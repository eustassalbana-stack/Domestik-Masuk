import streamlit as st
import pandas as pd
import os
import json
from io import BytesIO

# --- FIREBASE / FIRESTORE IMPORTS ---
# Asumsikan SDK Firebase sudah dimuat di lingkungan ini (seperti dalam React/HTML).
# Untuk Streamlit, kita harus menggunakan metode simulasi SDK JS/Web
# atau mengasumsikan paket Python resmi (firebase-admin atau firebase) tersedia.
# Kami akan mensimulasikan koneksi menggunakan variabel global yang disediakan (MANDATORY).

# Variabel Global yang Disediakan (JANGAN UBAH)
try:
    FIREBASE_CONFIG = json.loads(__firebase_config)
    APP_ID = __app_id
    INITIAL_AUTH_TOKEN = __initial_auth_token
    # Log Level disetel di bagian init
    
    # Impor modul Firebase untuk lingkungan Streamlit/Python (Simulasi)
    from firebase_admin import credentials, initialize_app, firestore
    import firebase_admin

    # Inisialisasi Firebase Admin SDK (hanya sekali)
    if not firebase_admin._apps:
        # Menggunakan kredensial dummy karena lingkungan ini akan menyediakan kredensial runtime
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": FIREBASE_CONFIG["projectId"],
            "private_key_id": "dummy",
            "private_key": "dummy",
            "client_email": "dummy@dummy.iam.gserviceaccount.com",
            "client_id": "dummy",
            "auth_uri": "dummy",
            "token_uri": "dummy",
            "auth_provider_x509_cert_url": "dummy",
            "client_x509_cert_url": "dummy",
            "universe_domain": "googleapis.com"
        })
        # Note: initialize_app akan menggunakan kredensial dummy, tetapi koneksi 
        # ke Firestore akan diautentikasi secara otomatis oleh Canvas
        firebase_admin.initialize_app(cred, FIREBASE_CONFIG, name=APP_ID)
    
    db = firestore.client(APP_ID)
    
    # Path dokumen publik yang akan menyimpan status checklist
    # Path: /artifacts/{appId}/public/data/checklist_status/master_status
    CHECKLIST_DOC_REF = db.collection("artifacts").document(APP_ID).collection("public").document("data").collection("checklist_status").document("master_status")

    ST_USE_FIRESTORE = True
except (NameError, ImportError, KeyError, AttributeError):
    # Fallback ke mode file lokal jika Firebase SDK tidak tersedia atau variabel global hilang
    st.warning("⚠️ Gagal menginisialisasi Firebase. Menggunakan persistensi file lokal (status_checklist.json) sebagai fallback.")
    ST_USE_FIRESTORE = False
    
    STATUS_FILE = "status_checklist.json"

    def load_checklist_status_local():
        """Memuat status checklist dari file JSON lokal (Fallback)."""
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, 'r') as f:
                    content = f.read()
                    if content:
                        return json.loads(content)
                    return {}
            except (json.JSONDecodeError, Exception) as e:
                st.error(f"Error memuat status lokal: {e}")
                return {}
        return {}

    def save_checklist_status_local(data):
        """Menyimpan status checklist ke file JSON lokal (Fallback)."""
        try:
            with open(STATUS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            st.toast("Status checklist berhasil disimpan secara permanen (Lokal)!")
        except Exception as e:
            st.error(f"Gagal menyimpan status checklist ke disk (Lokal): {e}")

# --- Fungsi Persistensi Firestore ---
def load_checklist_status_firestore():
    """Memuat status checklist dari Firestore (Hanya dipanggil saat init)."""
    try:
        doc = CHECKLIST_DOC_REF.get()
        if doc.exists:
            # Mengembalikan dictionary status_map (e.g., {"Benih Anggrek": True})
            return doc.to_dict().get("status_map", {})
        return {}
    except Exception as e:
        st.error(f"Error saat memuat status dari Firestore: {e}")
        return {}

# BARIS INI TELAH DIPERBAIKI (MENGHAPUS @st.experimental_fragment)
def save_checklist_status_firestore(data):
    """Menyimpan status checklist ke Firestore."""
    try:
        # Menyimpan seluruh map status dalam satu dokumen
        CHECKLIST_DOC_REF.set({"status_map": data}, merge=True)
        # Tidak perlu st.toast di fragment, bisa menyebabkan masalah
    except Exception as e:
        st.error(f"Gagal menyimpan status checklist ke Firestore: {e}")

# --- Callback function untuk memperbarui status dan menyimpannya ke disk/Firestore ---
def update_checklist_and_save(selected_komoditas):
    """Callback function yang dipanggil saat checkbox diubah."""
    key_name = f"check_{selected_komoditas}"
    new_status = st.session_state[key_name]
    
    st.session_state.checked_items[selected_komoditas] = new_status
        
    if ST_USE_FIRESTORE:
        # Menyimpan ke Firestore
        save_checklist_status_firestore(st.session_state.checked_items)
        st.toast("Status checklist diperbarui di Firestore!")
    else:
        # Menyimpan ke File Lokal (Fallback)
        save_checklist_status_local(st.session_state.checked_items)
        
    # PENTING: Panggil st.rerun() untuk memaksa Streamlit memuat ulang,
    # ini akan memperbarui ikon di st.radio di sidebar
    st.rerun()  

# Konfigurasi halaman
st.set_page_config(page_title="📦 Aplikasi Data Komoditas Domestik Masuk", layout="wide")

# --- Judul Utama ---
st.title("📦 Aplikasi Pencarian Data Komoditas Domestik Masuk")

# --- Inisialisasi status checklist dari database (load persistensi) ---
if "checked_items" not in st.session_state:
    if ST_USE_FIRESTORE:
        # Muat dari Firestore
        st.session_state.checked_items = load_checklist_status_firestore()
    else:
        # Muat dari File Lokal (Fallback)
        st.session_state.checked_items = load_checklist_status_local()
        
    st.session_state.initial_load_complete = True # Flag untuk menandai inisialisasi

# --- Nama file lokal ---
excel_file = "Pembebasan domas.xlsx"
mapping_file = "kabupaten_kota.xlsx"

# --- Kode Simulasi Data (Ganti dengan data asli Anda) ---
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

    st.sidebar.markdown("*Pilihan berdasarkan data dummy.*")

else:
    # --- Kode Asli Anda untuk Membaca File Excel ---
    try:
        df = pd.read_excel(excel_file)
        df.columns = df.columns.str.strip().str.lower()
        map_df = pd.read_excel(mapping_file)
        map_df.columns = map_df.columns.str.lower().str.strip()
        
        # (Sisa kode pembacaan, validasi, dan merge data Anda yang asli)
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


# --- Sidebar Pilihan Komoditas ---
st.sidebar.header("🔍 Pilih Komoditas")
komoditas_list_raw = sorted(df["komoditas"].dropna().unique())
    
# 1. Buat daftar opsi yang sudah dihias dengan tanda centang/kaca pembesar
komoditas_options = []
default_index = 0
    
# Tentukan komoditas yang sebelumnya dipilih (untuk mempertahankan pilihan st.radio)
previous_selected = st.session_state.get('selected_komoditas_raw', komoditas_list_raw[0] if komoditas_list_raw else None)
    
for i, komoditas in enumerate(komoditas_list_raw):
    # Cek status pemeriksaan dari st.session_state yang sudah dimuat dari Firestore/Lokal
    is_checked = st.session_state.checked_items.get(komoditas, False)
    # Tambahkan tanda ke nama komoditas
    status_icon = "✅ " if is_checked else "🔎 "
    komoditas_options.append(f"{status_icon} {komoditas}")
        
    # Jika komoditas saat ini adalah yang terpilih sebelumnya, simpan index-nya
    if komoditas == previous_selected:
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
# Ambil status sebelumnya (default False) dari session state yang persisten
is_checked_state = st.session_state.checked_items.get(selected_komoditas, False)

# Tampilkan checkbox
st.checkbox(
    f"✅ Tandai komoditas **{selected_komoditas}** telah diperiksa",
    value=is_checked_state, # Gunakan status yang dimuat dari file/Firestore
    key=f"check_{selected_komoditas}",
    # Panggil callback, berikan selected_komoditas sebagai argumen
    on_change=update_checklist_and_save, 
    args=(selected_komoditas,)
)
    
# --- Tampilkan notifikasi berdasarkan status ---
if is_checked_state:
    st.success(f"✅ Komoditas **{selected_komoditas}** telah diperiksa.")
else:
    st.info(f"🔎 Komoditas **{selected_komoditas}** belum diperiksa.")

# --- Tampilkan Data Secara Vertikal (Berfokus pada Provinsi dengan Expander) ---
if not filtered_df.empty:
    st.subheader(f"📊 Informasi Komoditas: {selected_komoditas}")

    grouped_by_provinsi = filtered_df.groupby("provinsi asal")

    for provinsi, group_df in grouped_by_provinsi:
        unique_kode_hs = group_df["kode hs"].unique()
        # Pastikan Kode HS ditampilkan sebagai string, untuk menghindari error jika ada NaN atau tipe data campuran
        kode_hs_display = ", ".join(unique_kode_hs.astype(str).tolist())
            
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
            # Ambil nilai pertama untuk "nama tercetak" dan "satuan" karena diasumsikan sama dalam satu komoditas
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
    # Filter kolom yang ada di DataFrame sebelum diekspor
    # NOTE: Fix bug di sini, variabel harusnya df_export
    export_cols = [col for col in cols_to_export if col in df_export.columns] 
    
    df_export[export_cols].to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()

st.download_button(
    label="💾 Unduh Hasil (Excel)",
    data=convert_to_excel(filtered_df),
    file_name=f"hasil_{selected_komoditas}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("---")
st.caption("TETAP KERJA WALAUPUN TUKIN BELUM CAIR")