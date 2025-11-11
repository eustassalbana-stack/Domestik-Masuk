import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="📦 Aplikasi Data Komoditas Ekspor", layout="wide")

# --- Judul Utama ---
st.title("📦 Aplikasi Pencarian Data Komoditas Ekspor")

# --- Nama file lokal ---
excel_file = "Pembebasan domas.xlsx"
mapping_file = "kabupaten_kota.csv"

# --- Periksa keberadaan file ---
if not os.path.exists(excel_file):
    st.error(f"❌ File {excel_file} tidak ditemukan di folder aplikasi. Pastikan file ini berada di lokasi yang sama dengan app.py.")
elif not os.path.exists(mapping_file):
    st.error(f"❌ File {mapping_file} tidak ditemukan di folder aplikasi. Pastikan file ini berada di lokasi yang sama dengan app.py.")
else:
    # --- Baca data utama ---
    df = pd.read_excel(excel_file)
    df.columns = df.columns.str.strip().str.lower()

    # --- Baca data mapping kabupaten–provinsi ---
    map_df = pd.read_csv(mapping_file)
    map_df.columns = map_df.columns.str.lower().str.strip()

    # Pastikan ada kolom yang diperlukan
    required_cols = [
        "daerah asal", "daerah tujuan", "klasifikasi",
        "komoditas", "nama tercetak", "kode hs", "satuan"
    ]

    if not all(col in df.columns for col in required_cols):
        st.error(f"❌ Kolom wajib tidak lengkap. Pastikan file Excel memiliki kolom berikut:\n{', '.join(required_cols)}")
    elif not all(col in map_df.columns for col in ["kabupaten_kota", "provinsi"]):
        st.error("❌ File kabupaten_kota.csv harus memiliki kolom: kabupaten_kota dan provinsi.")
    else:
        # --- Standarisasi lowercase dan merge provinsi ---
        df["daerah_asal_clean"] = df["daerah asal"].str.lower().str.strip()
        map_df["kabupaten_kota_clean"] =_
