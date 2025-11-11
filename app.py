import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Konfigurasi halaman
st.set_page_config(page_title="📦 Aplikasi Data Komoditas Ekspor", layout="wide")

# --- Judul Utama ---
st.title("📦 Aplikasi Pencarian Data Komoditas Ekspor")

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
        # Menggunakan kolom 0 dan 1 (A dan B) untuk memastikan data yang diambil benar
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

            # --- Sidebar Pilihan Komoditas ---
            st.sidebar.header("🔍 Pilih Komoditas")
            komoditas_list = sorted(df["komoditas"].dropna().unique())
            selected_komoditas = st.sidebar.selectbox("Pilih komoditas:", komoditas_list)

            # --- Filter data sesuai komoditas ---
            filtered_df = df[df["komoditas"] == selected_komoditas]

            # --- Hapus duplikasi data asal–tujuan ---
            filtered_df = filtered_df.drop_duplicates(
                subset=["provinsi asal", "daerah asal", "daerah tujuan", "klasifikasi", "komoditas", "nama tercetak", "kode hs", "satuan"]
            )

            # --- Status Pemeriksaan Komoditas (per komoditas) ---
            if "checked_items" not in st.session_state:
                st.session_state.checked_items = {}

            # ambil status sebelumnya (default False)
            is_checked = st.session_state.checked_items.get(selected_komoditas, False)

            # tampilkan checkbox dengan status sesuai komoditas
            new_checked = st.checkbox(
                f"✅ Tandai komoditas **{selected_komoditas}** telah diperiksa",
                value=is_checked,
                key=f"check_{selected_komoditas}"
            )

            # update session state hanya untuk komoditas ini
            st.session_state.checked_items[selected_komoditas] = new_checked

            # tampilkan notifikasi berdasarkan status
            if new_checked:
                st.success(f"✅ Komoditas **{selected_komoditas}** telah diperiksa.")
            else:
                st.info(f"🔎 Komoditas **{selected_komoditas}** belum diperiksa.")

            # --- Tampilkan Data Secara Vertikal (Perubahan Utama) ---
            if not filtered_df.empty:
                st.subheader(f"📊 Informasi Komoditas: {selected_komoditas}")

                # List Kolom yang ingin ditampilkan
                display_cols = {
                    "provinsi asal": "Provinsi Asal",
                    "daerah asal": "Daerah Asal",
                    "daerah tujuan": "Daerah Tujuan",
                    "klasifikasi": "Klasifikasi",
                    "komoditas": "Komoditas",
                    "nama tercetak": "Nama Tercetak",
                    "kode hs": "Kode HS",
                    "satuan": "Satuan"
                }

                # Ganti st.dataframe dengan loop vertikal
                for index, row in filtered_df.iterrows():
                    with st.container(border=True):
                        # Judul kecil untuk entri ini
                        st.markdown(f"**Entri Data #{index + 1}**", unsafe_allow_html=True)
                        st.markdown("---")

                        # Tampilkan setiap kolom dalam baris vertikal
                        for col_name, display_name in display_cols.items():
                            st.markdown(f"**{display_name}:** {row[col_name]}")
                    
                    # Tambahkan spasi antar container
                    st.write("") 

            else:
                st.warning("Tidak ada data untuk komoditas ini.")

            # --- Unduh hasil ---
            @st.cache_data
            def convert_to_excel(df_export):
                buffer = BytesIO()
                # Pastikan hanya kolom yang relevan yang diekspor
                cols_to_export = list(display_cols.keys())
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
st.caption("Dibuat dengan ❤️ menggunakan Streamlit")