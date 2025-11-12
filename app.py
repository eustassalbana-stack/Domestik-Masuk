import streamlit as st
import pandas as pd
import os
import json # Diperlukan untuk penyimpanan status
from io import BytesIO

# --- Konfigurasi Persistensi Checklist ---
STATUS_FILE = "status_checklist.json"

def load_checklist_status():
    """Memuat status checklist dari file JSON."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            # Jika file rusak atau kosong, kembalikan status kosong
            return {}
    return {}

def save_checklist_status(data):
    """Menyimpan status checklist ke file JSON."""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Gagal menyimpan status checklist: {e}")

# Konfigurasi halaman
st.set_page_config(page_title="📦 Aplikasi Data Komoditas Domestik Masuk", layout="wide")

# --- Judul Utama ---
st.title("📦 Aplikasi Pencarian Data Komoditas Domestik Masuk")

# --- Nama file lokal ---
excel_file = "Pembebasan domas.xlsx"
mapping_file = "kabupaten_kota.xlsx"

# --- Periksa keberadaan file ---
if not os.path.exists(excel_file):
    st.error(f"❌ File {excel_file} tidak ditemukan di folder aplikasi. Pastikan file ini berada di lokasi yang sama dengan app.py.")
elif not os.path.exists(mapping_file):
    st.error(f"❌ File {mapping_file} tidak ditemukan di folder aplikasi. Pastikan file ini berada di lokasi yang sama dengan app.py.")
else:
    try:
        # --- Baca data utama ---
        df = pd.read_excel(excel_file)
        df.columns = df.columns.str.strip().str.lower()

        # --- Baca data mapping kabupaten–provinsi (Excel) ---
        map_df = pd.read_excel(mapping_file)
        map_df.columns = map_df.columns.str.lower().str.strip()

        # Pastikan ada kolom yang diperlukan
        required_cols_main = [
            "daerah asal", "daerah tujuan", "klasifikasi",
            "komoditas", "nama tercetak", "kode hs", "satuan"
        ]
        required_cols_map = ["kabupaten_kota", "provinsi"]

        if not all(col in df.columns for col in required_cols_main):
            st.error(f"❌ Kolom wajib file data utama tidak lengkap. Pastikan file Excel memiliki kolom berikut:\n{', '.join(required_cols_main)}")
        elif not all(col in map_df.columns for col in required_cols_map):
            st.error(f"❌ File {mapping_file} harus memiliki kolom: kabupaten_kota dan provinsi.")
        else:
            # --- Standarisasi lowercase dan merge provinsi ---
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

            # --- Status Pemeriksaan Komoditas (INISIALISASI DENGAN PERSISTENSI) ---
            if "checked_items" not in st.session_state:
                # Muat status dari file saat pertama kali dijalankan
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
            selected_komoditas = selected_option_with_icon[3:].strip() # Ambil string dari indeks ke-3 (setelah '✅ ' atau '🔎 ')
            st.session_state.selected_komoditas_raw = selected_komoditas # Simpan nama asli

            # --- Filter data sesuai komoditas ---
            filtered_df = df[df["komoditas"] == selected_komoditas]

            # --- Hapus duplikasi data asal–tujuan ---
            filtered_df = filtered_df.drop_duplicates(
                subset=["provinsi asal", "daerah asal", "daerah tujuan", "klasifikasi", "komoditas", "nama tercetak", "kode hs", "satuan"]
            )

            # --- Checkbox Pemeriksaan Komoditas ---
            # Ambil status sebelumnya (default False)
            is_checked = st.session_state.checked_items.get(selected_komoditas, False)

            # Callback function untuk memperbarui status dan menyimpannya ke disk
            def update_sidebar_on_check():
                # 1. Update status di session state
                st.session_state.checked_items[selected_komoditas] = st.session_state[f"check_{selected_komoditas}"]
                
                # 2. SIMPAN STATUS BARU KE FILE (PERSISTENSI)
                save_checklist_status(st.session_state.checked_items)
                
                # PENTING: Panggil st.rerun() untuk memaksa Streamlit memuat ulang,
                # ini akan memperbarui ikon di st.radio di sidebar
                st.rerun() 

            # Tampilkan checkbox
            new_checked = st.checkbox(
                f"✅ Tandai komoditas **{selected_komoditas}** telah diperiksa",
                value=is_checked,
                key=f"check_{selected_komoditas}",
                on_change=update_sidebar_on_check # Panggil fungsi callback
            )
            
            # --- Tampilkan notifikasi berdasarkan status (tetap sama) ---
            if new_checked:
                st.success(f"✅ Komoditas **{selected_komoditas}** telah diperiksa.")
            else:
                st.info(f"🔎 Komoditas **{selected_komoditas}** belum diperiksa.")

            # --- Tampilkan Data Secara Vertikal (Berfokus pada Provinsi dengan Expander) ---
            if not filtered_df.empty:
                st.subheader(f"📊 Informasi Komoditas: {selected_komoditas}")

                # 1. Kelompokkan data berdasarkan 'provinsi asal'
                grouped_by_provinsi = filtered_df.groupby("provinsi asal")

                for provinsi, group_df in grouped_by_provinsi:
                    # Ambil SEMUA Kode HS unik dalam kelompok provinsi ini
                    unique_kode_hs = group_df["kode hs"].unique()
                    
                    # Gabungkan semua Kode HS unik menjadi satu string, dipisahkan koma
                    kode_hs_display = ", ".join(unique_kode_hs.astype(str))
                    
                    # 2. Gunakan st.expander dengan nama provinsi dan Kode HS unik sebagai judul
                    with st.expander(f"📦 **{provinsi}** - Kode HS: **{kode_hs_display}** (Total {len(group_df)} Entri Unik)"):
                        
                        # 3. Kumpulkan informasi unik di provinsi tersebut
                        daerah_asal_unik = sorted(group_df["daerah asal"].unique())
                        daerah_tujuan_unik = sorted(group_df["daerah tujuan"].unique())
                        klasifikasi_unik = sorted(group_df["klasifikasi"].unique())

                        st.markdown("---")
                        
                        # Tampilkan Daftar Daerah Asal
                        st.markdown(f"**Daerah Asal di {provinsi} ({len(daerah_asal_unik)} Unik):**")
                        st.write(", ".join(daerah_asal_unik)) # Tampilan datar (lebih baik untuk list)

                        # Tampilkan Daftar Daerah Tujuan
                        st.markdown(f"**Daerah Tujuan ({len(daerah_tujuan_unik)} Unik):**")
                        st.write(", ".join(daerah_tujuan_unik))

                        # Tampilkan Daftar Klasifikasi
                        st.markdown(f"**Klasifikasi ({len(klasifikasi_unik)} Unik):**")
                        st.write(", ".join(klasifikasi_unik))

                        st.markdown("---")
                        # Tampilkan detail lainnya (Nama Tercetak, Satuan)
                        st.markdown(f"**Nama Tercetak:** {group_df['nama tercetak'].iloc[0]}")
                        st.markdown(f"**Satuan:** {group_df['satuan'].iloc[0]}")

            else:
                st.warning("Tidak ada data untuk komoditas ini.")

            # --- Unduh hasil ---
            @st.cache_data
            def convert_to_excel(df_export):
                buffer = BytesIO()
                # List kolom yang ingin ditampilkan di Excel (sama dengan required_cols_main)
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

    except Exception as e:
        # Menampilkan pesan error jika ada masalah saat membaca file atau merge
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
        st.warning("Pastikan nama kolom di file Excel Anda (Pembebasan domas.xlsx dan kabupaten_kota.xlsx) sudah benar dan konsisten.")


st.markdown("---")
st.caption("TETAP KERJA WALAUPUN TUKIN BELUM CAIR")