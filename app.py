# --- Tampilkan Data dalam format vertikal ---
st.markdown("---")
st.subheader(f"📋 Detail Komoditas: {selected_komoditas}")

if not filtered_data.empty:
    for _, row in filtered_data.iterrows():
        st.markdown(
            f"""
            <div style='padding:15px; border-radius:12px; background-color:#f7f7f9; margin-bottom:10px;'>
                <h4 style='margin-bottom:5px; color:#2E86C1;'>🌾 {row['Komoditas']}</h4>
                <p><b>Kode HS:</b> {row['Kode HS']}</p>
                <p><b>Klasifikasi:</b> {row['Klasifikasi']}</p>
                <p><b>Provinsi Asal:</b> {row['Provinsi Asal']}</p>
                <p><b>Daerah Asal:</b> {row['Daerah Asal']}</p>
                <p><b>Provinsi Tujuan:</b> {row['Provinsi Tujuan']}</p>
                <p><b>Daerah Tujuan:</b> {row['Daerah Tujuan']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.warning("Tidak ada data untuk komoditas ini.")
