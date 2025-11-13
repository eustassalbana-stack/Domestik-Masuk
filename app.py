import streamlit as st
import pandas as pd
import os
import json 
from io import BytesIO

# --- KONFIGURASI PERSISTENSI CHECKLIST (File Lokal) ---
# CATATAN PENTING: Pendekatan file lokal ini HANYA akan berfungsi jika aplikasi 
# dijalankan di lingkungan lokal. Di lingkungan cloud (seperti Streamlit Cloud), 
# file ini akan HILANG/RESET saat container server mati karena idle.
# Untuk persistensi sejati di cloud, gunakan database seperti Firestore/Supabase.
STATUS_FILE = "status_checklist.json"

def load_checklist_status():
    """Memuat status checklist dari file JSON. Lebih robust terhadap error."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                # Memastikan file tidak kosong sebelum mencoba memuat JSON
                content = f.read()
                if content:
                    return json.loads(content)
                else:
                    return {}
        except json.JSONDecodeError:
            st.warning("File status_checklist.json rusak atau tidak valid, memulai status kosong.")
            return {}
        except Exception as e:
            st.error(f"Error saat memuat status: {e}")
            return {}
    return {}

def save_checklist_status(data):
    """Menyimpan status checklist ke file JSON."""
    try:
        # Gunakan mode 'w' untuk menimpa file dengan status terbaru
        with open(STATUS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Gagal menyimpan status checklist ke disk: {e}")

# Konfigurasi halaman
st.set_page_config(page_title="📦 Aplikasi Data Komoditas Domestik Masuk", layout="wide")

# --- Judul Utama ---
st.title("📦 Aplikasi Pencarian Data Komoditas Domestik Masuk")

# --- Nama file lokal ---
# NOTE: Asumsikan file-file ini ada untuk tujuan demo
excel_file = "Pembebasan domas.xlsx"
mapping_file = "kabupaten_kota.xlsx"

# --- Kode Simulasi Data (Ganti dengan data asli Anda) ---
# Jika Anda menjalankan ini tanpa file Excel, gunakan simulasi data ini
if not os.path.exists(excel_file) or not os.path.exists(mapping_file):
    st.warning("File Excel tidak ditemukan. Menggunakan data dummy untuk demonstrasi fitur persistensi.")
    
    data = {
        "daerah asal": ["Jakarta", "Bandung", "Surabaya", "Medan"],
        "daerah tujuan": ["Denpasar", "Makassar", "Jakarta", "Bandung"],
        "klasifikasi": ["Sayuran", "Buah-buahan", "Biji-bijian", "Sayuran"],
        "komoditas": ["Benih Anggrek", "Bawang Merah", "Padi", "Benih Anggrek"],
        "nama tercetak": ["Anggrek A", "BM Kering", "Padi Unggul", "Anggrek B"],
        "kode hs": ["06021090", "07031000", "10063000", "06021090"],
        "satuan": ["Kg", "Ton", "Kg", "Kg"]
    }
    df = pd.DataFrame(data)
    
    map_data = {
        "kabupaten_kota": ["Jakarta", "Bandung", "Surabaya", "Medan"],
        "provinsi": ["DKI Jakarta", "Jawa Barat", "Jawa Timur", "Sumatera Utara"]
    }
    map_df = pd.DataFrame(map_data)
    
    # Lakukan standarisasi dan merge dummy data
    df.columns = df.columns.str.strip().str.lower()
    map_df.columns = map_df.columns.str.lower().str.strip()
    df["daerah_asal_clean"] = df["daerah asal"].str.lower().str.strip()
    map_df["kabupaten_kota_clean"] = map_df["kabupaten_kota"].str.lower().str.strip()
    
    df = df.merge(
        map_df[["kabupaten_kota_clean", "provinsi"]],
        left_on="daerah_asal_clean",
        right_on="kabupaten_kota_clean",
        how="left"
    )
    df = df.rename(columns={"provinsi": "provinsi asal"})
    df["provinsi asal"] = df["provinsi asal"].fillna("Provinsi tidak diketahui")

    # Filter keluar jika data dummy digunakan
    st.sidebar.markdown("*Pilihan berdasarkan data dummy.*")

else:
    # --- Kode Asli Anda untuk Membaca File Excel ---
    try:
        df = pd.read_excel(excel_file)
        df.columns = df.columns.str.strip().str.lower()
        map_df = pd.read_excel(mapping_file)
        map_df.columns = map_df.columns.str.lower().str.strip()
        
        # (Sisa kode pembacaan, validasi, dan merge data Anda yang asli)
        # ... [Kode validasi dan merge data Anda yang asli ada di sini] ...
        required_cols_main = [
            "daerah asal", "daerah tujuan", "klasifikasi",
            "komoditas", "nama tercetak", "kode hs", "satuan"
        ]
        required_cols_map = ["kabupaten_kota", "provinsi"]

        if not all(col in df.columns for col in required_cols_main) or \
           not all(col in map_df.columns for col in required_cols_map):
             st.error("❌ Kolom wajib file Excel tidak lengkap.")
             st.stop()
        
        df["daerah_asal_clean"] = df["daerah asal"].str.lower().str.strip()
        map_df["kabupaten_kota_clean"] = map_df["kabupaten_kota"].str.lower().str.strip()

        df = df.merge(
            map_df[["kabupaten_kota_clean", "provinsi"]],
            left_on="daerah_asal_clean",
            right_on="kabupaten_kota_clean",
            how="left"
        )

        df = df.rename(columns={"provinsi": "provinsi asal"})
        df["provinsi asal"] = df["provinsi asal"].fillna("Provinsi tidak diketahui")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
        st.stop()


# --- Status Pemeriksaan Komoditas (LOAD PERSISTENSI) ---
if "checked_items" not in st.session_state:
    st.session_state.checked_items = load_checklist_status()
    
# --- Sidebar Pilihan Komoditas ---
st.sidebar.header("🔍 Pilih Komoditas")
komoditas_list_raw = sorted(df["komoditas"].dropna().unique())
    
# 1. Buat daftar opsi yang sudah dihias dengan tanda centang/kaca pembesar
komoditas_options = []
default_index = 0
    
for i, komoditas in enumerate(komoditas_list_raw):
    # Cek status pemeriksaan
    is_checked = st.session_state.checked_items.get(komoditas, False)
    # Tambahkan tanda ke nama komoditas
    status_icon = "✅ " if is_checked else "🔎 "
    komoditas_options.append(f"{status_icon} {komoditas}")
        
    # Jika komoditas saat ini adalah yang terpilih sebelumnya, simpan index-nya
    if 'selected_komoditas_raw' in st.session_state and st.session_state.selected_komoditas_raw == komoditas:
        default_index = i

# 2. Ganti st.selectbox dengan st.radio
selected_option_with_icon = st.sidebar.radio(
    "Pilih komoditas:", 
    komoditas_options,
    index=default_index,
    key='radio_komoditas'
)
    
# 3. Ekstrak nama komoditas asli (tanpa ikon) untuk filtering DataFrame
selected_komoditas = selected_option_with_icon[3:].strip()
st.session_state.selected_komoditas_raw = selected_komoditas # Simpan nama asli

# --- Filter data sesuai komoditas ---
filtered_df = df[df["komoditas"] == selected_komoditas]

# --- Checkbox Pemeriksaan Komoditas ---
# Ambil status sebelumnya (default False)
is_checked = st.session_state.checked_items.get(selected_komoditas, False)

# Callback function untuk memperbarui status dan menyimpannya ke disk
def update_checklist_and_save():
    # 1. Update status di session state
    st.session_state.checked_items[selected_komoditas] = st.session_state[f"check_{selected_komoditas}"]
        
    # 2. SIMPAN STATUS BARU KE FILE (PERSISTENSI LOKAL)
    save_checklist_status(st.session_state.checked_items)
        
    # PENTING: Panggil st.rerun() untuk memaksa Streamlit memuat ulang,
    # ini akan memperbarui ikon di st.radio di sidebar
    st.rerun() 

# Tampilkan checkbox
new_checked = st.checkbox(
    f"✅ Tandai komoditas **{selected_komoditas}** telah diperiksa",
    value=is_checked,
    key=f"check_{selected_komoditas}",
    on_change=update_checklist_and_save # Panggil fungsi callback
)
    
# --- Tampilkan notifikasi berdasarkan status ---
if new_checked:
    st.success(f"✅ Komoditas **{selected_komoditas}** telah diperiksa.")
else:
    st.info(f"🔎 Komoditas **{selected_komoditas}** belum diperiksa.")

# --- Tampilkan Data Secara Vertikal (Berfokus pada Provinsi dengan Expander) ---
if not filtered_df.empty:
    st.subheader(f"📊 Informasi Komoditas: {selected_komoditas}")

    grouped_by_provinsi = filtered_df.groupby("provinsi asal")

    for provinsi, group_df in grouped_by_provinsi:
        unique_kode_hs = group_df["kode hs"].unique()
        kode_hs_display = ", ".join(unique_kode_hs.astype(str))
            
        with st.expander(f"📦 **{provinsi}** - Kode HS: **{kode_hs_display}** (Total {len(group_df)} Entri Unik)"):
            
            daerah_asal_unik = sorted(group_df["daerah asal"].unique())
            daerah_tujuan_unik = sorted(group_df["daerah tujuan"].unique())
            klasifikasi_unik = sorted(group_df["klasifikasi"].unique())

            st.markdown("---")
                
            st.markdown(f"**Daerah Asal di {provinsi} ({len(daerah_asal_unik)} Unik):**")
            st.write(", ".join(daerah_asal_unik))

            st.markdown(f"**Daerah Tujuan ({len(daerah_tujuan_unik)} Unik):**")
            st.write(", ".join(daerah_tujuan_unik))

            st.markdown(f"**Klasifikasi ({len(klasifikasi_unik)} Unik):**")
            st.write(", ".join(klasifikasi_unik))

            st.markdown("---")
            st.markdown(f"**Nama Tercetak:** {group_df['nama tercetak'].iloc[0]}")
            st.markdown(f"**Satuan:** {group_df['satuan'].iloc[0]}")

else:
    st.warning("Tidak ada data untuk komoditas ini.")

# --- Unduh hasil ---
@st.cache_data
def convert_to_excel(df_export):
    buffer = BytesIO()
    cols_to_export = [
        "provinsi asal", "daerah asal", "daerah tujuan", "klasifikasi",
        "komoditas", "nama tercetak", "kode hs", "satuan"
    ]
    df_export[cols_to_export].to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()

st.download_button(
    label="💾 Unduh Hasil (Excel)",
    data=convert_to_excel(filtered_df),
    file_name=f"hasil_{selected_komoditas}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("---")
st.caption("TETAP KERJA WALAUPUN TUKIN BELUM CAIR")