import streamlit as st
import pandas as pd
import os

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
    # --- Baca data utama ---
    df = pd.read_excel(excel_file)
    df.columns = df.columns.str.strip().str.lower()

    # --- Baca data mapping kabupaten–provinsi (sekarang Excel) ---
    map_df = pd.read_excel(mapping_file)
    map_df.columns = map_df.columns.str.lower().str.strip()

    # Pastikan ada kolom yang diperlukan
    required_cols = [
        "daerah asal", "daerah tujuan", "klasifikasi",
        "komoditas", "nama tercetak", "kode hs", "satuan"
    ]

    if not all(col in df.columns for col in required_cols):
        st.error(f"❌ Kolom wajib tidak lengkap. Pastikan file Excel memiliki kolom berikut:\n{', '.join(required_cols)}")
    elif not all(col in map_df.columns for col in ["kabupaten_kota", "provinsi"]):
        st.error("❌ File kabupaten_kota.xlsx harus memiliki kolom: kabupaten_kota dan provinsi.")
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

        filtered_df = df[df["komoditas"] == selected_komoditas]

        # --- Hapus duplikasi data asal–tujuan ---
        filtered_df = filtered_df.drop_duplicates(
            subset=["provinsi asal", "daerah asal", "daerah tujuan", "klasifikasi", "komoditas", "nama tercetak", "kode hs", "satuan"]
        )

        # --- Status Pemeriksaan Komoditas ---
        if "checked_items" not in st.session_state:
            st.session_state.checked_items = {}

        checked = st.checkbox(
            "✅ Tandai komoditas ini sudah diperiksa",
            value=st.session_state.checked_items.get(selected_komoditas, False)
        )
        st.session_state.checked_items[selected_komoditas] = checked

        # --- Tampilkan Data ---
        if not filtered_df.empty:
            st.subheader(f"📊 Informasi Komoditas: {selected_komoditas}")
            st.dataframe(
                filtered_df[
                    [
                        "provinsi asal", "daerah asal", "daerah tujuan",
                        "klasifikasi", "komoditas", "nama tercetak",
                        "kode hs", "satuan"
                    ]
                ],
                use_container_width=True
            )

            if checked:
                st.success(f"✅ Komoditas **{selected_komoditas}** telah diperiksa.")
            else:
                st.info(f"🔎 Komoditas **{selected_komoditas}** belum diperiksa.")
        else:
            st.warning("Tidak ada data untuk komoditas ini.")

        # --- Unduh hasil ---
        @st.cache_data
        def convert_to_excel(df_export):
            from io import BytesIO
            buffer = BytesIO()
            df_export.to_excel(buffer, index=False, engine='openpyxl')
            return buffer.getvalue()

        st.download_button(
            label="💾 Unduh Hasil (Excel)",
            data=convert_to_excel(filtered_df),
            file_name=f"hasil_{selected_komoditas}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("---")
st.caption("Dibuat dengan ❤️ menggunakan Streamlit")
