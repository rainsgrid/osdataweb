# 🌊 Oceanography Data Processing Dashboard

Dashboard berbasis Web (Streamlit) yang dirancang untuk mempermudah pengolahan data oseanografi, mulai dari pembersihan data (*spike removal*) hingga analisis pasang surut menggunakan metode *least-squares* (Utide).

## 🚀 Fitur Utama
* **Data Cleaning:** Pembersihan *spike* otomatis menggunakan metode Z-Score dan interpolasi linear.
* **Filter Digital:** Implementasi *Averaging*, *Moving Average* (MA), dan *Low-pass Filter* (Butterworth) dengan jendela waktu yang dapat disesuaikan.
* **Analisis Pasang Surut (Utide):** * Ekstraksi komponen harmonik (M2, S2, K1, O1).
    * Perhitungan **Formzahl (F)** untuk penentuan tipe pasut.
    * Rekonstruksi dan prediksi pasut.
* **Visualisasi Interaktif:** Grafik dinamis menggunakan Plotly yang mendukung *overlay* berbagai hasil filter.
* **Export Data:** Unduh hasil pengolahan dalam format `.csv`.

## 🛠️ Teknologi yang Digunakan
* **Bahasa Pemrograman:** Python 3.x
* **Framework:** Streamlit
* **Library Utama:** * `utide` (Analisis Harmonik)
    * `pandas` & `numpy` (Manajemen Data)
    * `scipy` (Signal Processing)
    * `plotly` (Visualisasi)

## 📦 Cara Instalasi Lokal
Jika ingin menjalankan dashboard ini di perangkat lokal:

1. Clone repository ini:
   ```bash
   git clone [https://github.com/rainsgrid/osdataweb.git](https://github.com/rainsgrid/osdataweb.git)
