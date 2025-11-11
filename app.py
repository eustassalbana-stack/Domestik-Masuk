import streamlit as st
import pandas as pd
from io import BytesIO

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="📦 Aplikasi Data Komoditas Ekspor", layout="wide")
st.title("📦 Aplikasi Pencarian Data Komoditas Ekspor")

# --- Baca Data Lokal ---
try:
    df = pd.read_excel("Pembebasan domas.xlsx")
    map_df = pd.read_excel("kabupaten_kota.xlsx")
except FileNotFoundError:
    st.error("❌ File 'Pembebasan domas.xlsx' atau 'kabupaten_kota.xlsx' tidak ditemukan di folder aplikasi.")
    st.stop()

# --- Bersihkan nama kolom ---
df.columns = df.columns.str.lower().str.strip()
map_df.columns = map_df.columns.str.lower().str.strip()

# --- Kolom wajib ---
required_cols = [
    "daerah asal", "daerah tujuan", "klasifikasi",
    "komoditas", "nama tercetak", "kode hs", "satuan"
]
if not all(col in df.columns for col in required_cols):
    st.error(f"❌ Kolom wajib tidak lengkap. Pastikan file memiliki kolom berikut:\n{', '.join(required_cols)}")
    st.stop()

# --- Standarisasi nama untuk pencocokan ---
df["daerah_asal_clean"] = df["daerah asal"].str.lower().str.strip()
df["daerah_tujuan_clean"] = df["daerah tujuan"].str.lower().str.strip()
map_df["kabupaten_kota_clean"] = map_df["kabupaten_kota"].str.lower().str.strip()

# --- Merge untuk dapatkan provinsi asal dan tujuan ---
df = df.merge(
    map_df[["kabupaten_kota_clean", "provinsi"]],
    left_on="daerah_asal_clean",
    right_on="kabupaten_kota_clean",
    how="left"
).rename(columns={"provinsi": "provinsi asal"})

df = df.merge(
    map_df[["kabupaten_kota_clean", "provinsi"]],
    left_on="daerah_tujuan_clean",
    right_on="kabupaten_kota_clean",
    how="left"
).rename(columns={"provinsi": "provinsi tujuan"})

df["provinsi asal"] = df["provinsi asal"].fillna("Provinsi tidak diketahui")
df["provinsi tujuan"] = df["provinsi tujuan"].fillna("Provinsi tidak diketahui")

# --- Hilangkan duplikat (asal, tujuan, komoditas sama) ---
df = df.drop_duplicates(subset=["daerah asal", "daerah tujuan", "komoditas"])

# --- Sidebar Pilihan Komoditas ---
st.sidebar.header("🔍 Pilih Komoditas")
komoditas_list = sorted(df["komoditas"].dropna().unique())
selected_komoditas = st.sidebar.selectbox("Pilih komoditas:", komoditas_list)

filtered_data = df[df["komoditas"] == selected_komoditas]

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

# --- Tampilkan notifikasi status ---
if new_checked:
    st.success(f"✅ Komoditas **{selected_komoditas}** telah diperiksa.")
else:
    st.info(f"🔎 Komoditas **{selected_komoditas}** belum diperiksa.")

# --- Tampilkan Data dalam format vertikal ---
st.markdown("---")
st.subheader(f"📋 Detail Komoditas: {selected_komoditas}")

if not filtered_data.empty:
    for _, row in filtered_data.iterrows():
        st.markdown(
            f"""
            <div style='padding:15px; border-radius:12px; background-color:#f7f7f9; margin-bottom:10px;'>
                <h4 style='margin-bottom:5px; color:#2E86C1;'>🌾 {row['komoditas']}</h4>
                <p><b>Kode HS:</b> {row['kode hs']}</p>
                <p><b>Klasifikasi:</b> {row['klasifikasi']}</p>
                <p><b>Provinsi Asal:</b> {row['provinsi asal']}</p>
                <p><b>Daerah Asal:</b> {row['daerah asal']}</p>
                <p><b>Provinsi Tujuan:</b> {row['provinsi tujuan']}</p>
                <p><b>Daerah Tujuan:</b> {row['daerah tujuan']}</p>
                <p><b>Satuan:</b> {row['satuan']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.warning("Tidak ada data untuk komoditas ini.")

# --- Fungsi untuk unduh hasil ---
@st.cache_data
def convert_to_excel(df_export):
    buffer = BytesIO()
    df_export.to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()

# --- Tombol unduh ---
st.download_button(
    label="💾 Unduh Hasil (Excel)",
    data=convert_to_excel(filtered_data),
    file_name=f"hasil_{selected_komoditas}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("---")
st.caption("Dibuat dengan ❤️ menggunakan Streamlit")
