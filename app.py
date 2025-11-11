import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="📦 Aplikasi Data Komoditas", layout="centered")

st.title("📦 Aplikasi Pencarian Data Komoditas")

# --- Baca file otomatis ---
domas_path = "Pembebasan domas.xlsx"
kabupaten_path = "kabupaten_kota.xlsx"

if not os.path.exists(domas_path):
    st.error(f"File {domas_path} tidak ditemukan. Pastikan file ada di folder yang sama dengan app.py.")
    st.stop()

if not os.path.exists(kabupaten_path):
    st.error(f"File {kabupaten_path} tidak ditemukan. Pastikan file ada di folder yang sama dengan app.py.")
    st.stop()

# --- Load Data ---
data = pd.read_excel(domas_path)
kabupaten = pd.read_excel(kabupaten_path)

# --- Pastikan kolom nama konsisten ---
kabupaten.columns = [c.strip().lower() for c in kabupaten.columns]

# --- Map kabupaten ke provinsi ---
def get_provinsi(nama_daerah):
    if pd.isna(nama_daerah):
        return ""
    row = kabupaten[kabupaten['kabupaten/kota'].str.lower() == nama_daerah.lower()]
    if not row.empty:
        return row.iloc[0]['provinsi']
    return ""

# --- Tambahkan kolom provinsi ---
data["Provinsi Asal"] = data["Daerah Asal"].apply(get_provinsi)
data["Provinsi Tujuan"] = data["Daerah Tujuan"].apply(get_provinsi)

# --- Hapus duplikat (asal & tujuan sama) ---
data_unique = data.drop_duplicates(subset=["Komoditas", "Daerah Asal", "Daerah Tujuan"])

# --- Pilih komoditas ---
komoditas_list = sorted(data_unique["Komoditas"].dropna().unique())
selected_komoditas = st.selectbox("Pilih Komoditas:", komoditas_list)

# --- Filter data sesuai komoditas ---
filtered_data = data_unique[data_unique["Komoditas"] == selected_komoditas]

# --- Status Pemeriksaan Komoditas ---
if "checked_items" not in st.session_state:
    st.session_state.checked_items = {}

is_checked = st.session_state.checked_items.get(selected_komoditas, False)

new_checked = st.checkbox(
    f"✅ Tandai komoditas **{selected_komoditas}** telah diperiksa",
    value=is_checked,
    key=f"check_{selected_komoditas}"
)

st.session_state.checked_items[selected_komoditas] = new_checked

if new_checked:
    st.success(f"✅ Komoditas **{selected_komoditas}** telah diperiksa.")
else:
    st.info(f"🔎 Komoditas **{selected_komoditas}** belum diperiksa.")

# --- Tampilkan Data dalam format vertikal ---
st.markdown("---")
st.subheader(f"📋 Detail Komoditas: {selected_komoditas}")

if not filtered_data.empty:
    for _, r_
