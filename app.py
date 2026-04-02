import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import plotly.graph_objects as go

# Cek library Utide
try:
    import utide
except ImportError:
    st.sidebar.error("Library 'utide' belum terinstall. Jalankan 'pip install utide openpyxl' di terminal.")

st.set_page_config(page_title="Oceanography Analysis Dashboard", layout="wide")
st.title("🌊 Oceanography Data Processing Dashboard")

# --- FUNGSI MATEMATIKA ---

@st.cache_data
def get_cleaned_data(series, z_thresh):
    interp = series.interpolate(method='linear').values
    m, std = np.nanmean(interp), np.nanstd(interp)
    clean = np.where(np.abs((interp - m) / std) > z_thresh, m, interp) if std > 0 else interp
    return pd.Series(clean)

@st.cache_data
def apply_averaging(series, window_hours):
    return series.rolling(window=window_hours).mean()

@st.cache_data
def apply_ma(series, window_hours):
    return series.rolling(window=window_hours, center=True).mean()

@st.cache_data
def apply_lp(series, window_hours):
    cutoff = 1 / (window_hours if window_hours > 0 else 1)
    filled = series.ffill().bfill().values
    if len(filled) > 10 and 0 < cutoff < 0.5:
        b, a = butter(3, cutoff, btype='low')
        return filtfilt(b, a, filled)
    return filled

@st.cache_data
def run_utide_analysis(time_series, elevation_series, lat):
    from matplotlib.dates import date2num
    import numpy as np
    
    # 1. PAKSA format waktu jadi datetime yang bener
    # Kalau kolom 'timestamp' kamu aneh, ini bakal benerin
    t_raw = pd.to_datetime(time_series, errors='coerce')
    temp_df = pd.DataFrame({'t': t_raw, 'v': elevation_series}).dropna()
    
    if len(temp_df) < 24:
        return None, None, 0
    
    # 2. Konversi ke angka yang dimengerti Utide
    t_num = date2num(temp_df['t'])
    vals = temp_df['v'].values
    msl_val = np.nanmean(vals)
    
    try:
        # 3. SOLVE - Kita paksa cari 4 komponen utama dulu
        # Jangan pakai 'auto' dulu karena 'auto' sering bikin F=0 kalau durasi gak sinkron
        coef = utide.solve(t_num, vals - msl_val, lat=lat, 
                           method='ols', conf_int='none', 
                           constit=['M2', 'S2', 'K1', 'O1'], 
                           verbose=False)
        
        # 4. Rekonstruksi
        tide_recon = utide.reconstruct(t_num, coef)
        prediction_final = tide_recon.h + msl_val
            
        return coef, prediction_final, msl_val
    except Exception as e:
        st.error(f"Utide Error: {e}")
        return None, None, msl_val

# --- STEP 1: UPLOAD & PREVIEW ---

st.sidebar.header("1. Upload File")
up = st.sidebar.file_uploader("Upload CSV atau Excel", type=["csv", "xlsx"])

if up:
    @st.cache_data
    def load_df(file):
        try:
            return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
            return None
    
    df = load_df(up)
    
    if df is not None:
        st.subheader("📄 Pratinjau Data Asli (Raw)")
        st.dataframe(df.head(100), use_container_width=True)
        st.divider()

        cols = list(df.columns)
        x_col = st.sidebar.selectbox("Pilih Kolom X:", [None] + cols)
        y_col = st.sidebar.selectbox("Pilih Kolom Y:", [None] + cols)

        if x_col and y_col:
            # --- STEP 2: KONFIGURASI ---
            st.sidebar.divider()
            st.sidebar.header("2. Konfigurasi Pengolahan")
            skip_cleaning = st.sidebar.checkbox("Data Sudah Bersih (Lewati Cleaning)")
            z_val = st.sidebar.slider("Spike Threshold (Z-Score)", 1.0, 10.0, 3.0) if not skip_cleaning else 3.0
            windows = st.sidebar.multiselect("Pilih Window Filter (Jam):", [1, 3, 12, 24, 25], default=[1, 3, 12, 25])

            # --- STEP 3: ANALISIS PASUT ---
            st.sidebar.divider()
            st.sidebar.header("3. Analisis Pasut (Opsional)")
            run_tide = st.sidebar.checkbox("Aktifkan Analisis Pasut Utide")
            lat_val = st.sidebar.number_input("Latitude Lokasi:", value=-6.90, step=0.01) if run_tide else -6.90

            # PROSES DATA INTI
            y_raw = pd.to_numeric(df[y_col], errors='coerce')
            data_clean = y_raw.interpolate().fillna(method='ffill').fillna(method='bfill') if skip_cleaning else get_cleaned_data(y_raw, z_val)

            # --- VISUALISASI UTAMA (TABS) ---
            tabs = st.tabs(["0. Overlay", "1. Clean Data", "2. Averaging", "3. MA", "4. LP"])

            with tabs[0]:
                c1, c2, c3 = st.columns(3)
                with c1:
                    show_raw, show_clean = st.checkbox("Garis Raw", True), st.checkbox("Garis Clean", True)
                with c2:
                    show_avg, show_ma = st.checkbox("Garis Avg"), st.checkbox("Garis MA")
                with c3:
                    show_lp = st.checkbox("Garis LP", True)
                    sel_w = st.selectbox("Window (Jam):", windows if windows else [24])

                fig0 = go.Figure()
                if show_raw: fig0.add_trace(go.Scattergl(x=df[x_col], y=y_raw, name="Raw", line=dict(color='rgba(200,200,200,0.5)')))
                if show_clean: fig0.add_trace(go.Scattergl(x=df[x_col], y=data_clean, name="Clean", line=dict(color='blue')))
                if show_avg: fig0.add_trace(go.Scattergl(x=df[x_col], y=apply_averaging(data_clean, sel_w), name="Avg", line=dict(color='green')))
                if show_ma: fig0.add_trace(go.Scattergl(x=df[x_col], y=apply_ma(data_clean, sel_w), name="MA", line=dict(color='orange')))
                if show_lp: fig0.add_trace(go.Scattergl(x=df[x_col], y=apply_lp(data_clean, sel_w), name="LP", line=dict(color='red')))
                st.plotly_chart(fig0, use_container_width=True)

            with tabs[1]: st.plotly_chart(go.Figure(go.Scattergl(x=df[x_col], y=data_clean, name="Clean")), use_container_width=True)
            with tabs[2]:
                fig2 = go.Figure()
                for w in windows: fig2.add_trace(go.Scattergl(x=df[x_col], y=apply_averaging(data_clean, w), name=f"Avg {w}h"))
                st.plotly_chart(fig2, use_container_width=True)
            with tabs[3]:
                fig3 = go.Figure()
                for w in windows: fig3.add_trace(go.Scattergl(x=df[x_col], y=apply_ma(data_clean, w), name=f"MA {w}h"))
                st.plotly_chart(fig3, use_container_width=True)
            with tabs[4]:
                fig4 = go.Figure()
                for w in windows: fig4.add_trace(go.Scattergl(x=df[x_col], y=apply_lp(data_clean, w), name=f"LP {w}h"))
                st.plotly_chart(fig4, use_container_width=True)

            # --- ANALISIS PASUT (UTIDE) ---
            if run_tide:
                st.divider()
                st.header("📉 Hasil Analisis Pasut")
                try:
                    coef, tide_pred, msl_val = run_utide_analysis(df[x_col], data_clean, lat_val)
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        fig_t = go.Figure()
                        fig_t.add_trace(go.Scattergl(x=df[x_col], y=data_clean, name="Obs"))
                        fig_t.add_trace(go.Scattergl(x=df[x_col], y=tide_pred, name="Prediksi", line=dict(color='red', dash='dot')))
                        st.plotly_chart(fig_t, use_container_width=True)
                    with c2:
                        amp = dict(zip(coef.name, coef.A))
                        F = (amp.get('K1', 0) + amp.get('O1', 0)) / (amp.get('M2', 0) + amp.get('S2', 1e-6))
                        st.metric("Formzahl (F)", f"{F:.3f}")
                        if F <= 0.25: t, w = "Ganda", "blue"
                        elif F <= 1.50: t, w = "Campuran Ganda", "green"
                        elif F <= 3.00: t, w = "Campuran Tunggal", "orange"
                        else: t, w = "Tunggal", "red"
                        st.markdown(f"Tipe: **:{w}[{t}]**")
                        st.write(f"**MSL:** {msl_val:.2f}")
                        st.dataframe(pd.DataFrame({'Komponen': coef.name, 'Amplitudo': coef.A}).sort_values('Amplitudo', ascending=False).head(6))
                except: st.error("Gagal analisis pasut.")

            # --- BAGIAN BARU: TABEL HASIL PENGOLAHAN ---
            st.divider()
            st.subheader("✅ Pratinjau Data Hasil Pengolahan")
            st.write("Data di bawah ini adalah hasil pengolahan (Spike Removal + Interpolasi).")
            
            # Buat DataFrame untuk ditampilkan & download
            df_final = pd.DataFrame({
                'timestamp': df[x_col].astype(str), 
                'Water_Level_Raw': y_raw,
                'Water_Level_Cleaned': data_clean.fillna(0)
            })
            
            st.dataframe(df_final, use_container_width=True, height=500)

            # DOWNLOAD BUTTON
            st.download_button(
                label="💾 Download Hasil Olahan (.csv)", 
                data=df_final.to_csv(index=False).encode('utf-8'), 
                file_name="hasil_oseanografi_final.csv"
            )