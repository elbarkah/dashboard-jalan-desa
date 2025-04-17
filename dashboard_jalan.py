import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Jalan Desa Jawa Barat",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== LOAD DATA ==========
@st.cache_data
def load_data():
    df = pd.read_excel("DATA JALAN DESA.xlsx", sheet_name='02  DATA JALAN DESA')
    cols = ['BAIK (meter)', 'RUSAK RINGAN (meter)', 'RUSAK SEDANG (meter)', 'RUSAK BERAT (meter)']
    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
    return df

df = load_data()

# ========== HEADER ==========
st.markdown("<h1 style='text-align: center;'>🛣️ Dashboard Kondisi Jalan Desa<br>Provinsi Jawa Barat</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Analisis visual interaktif kondisi jalan desa berdasarkan kategori: Baik, Rusak Ringan, Rusak Sedang, dan Rusak Berat.</p>", unsafe_allow_html=True)
st.markdown("---")

# ========== FILTER ==========
with st.sidebar:
    st.header("🔍 Filter Data")
    selected_kab = st.selectbox("Pilih Kabupaten", ["Semua"] + sorted(df['KABUPATEN'].dropna().unique()))
    df_kab = df[df['KABUPATEN'] == selected_kab] if selected_kab != "Semua" else df.copy()

    selected_kec = st.selectbox("Pilih Kecamatan", ["Semua"] + sorted(df_kab['KECAMATAN'].dropna().unique()))
    df_kec = df_kab[df_kab['KECAMATAN'] == selected_kec] if selected_kec != "Semua" else df_kab

    selected_desa = st.selectbox("Pilih Desa", ["Semua"] + sorted(df_kec['DESA'].dropna().unique()))
    df_filtered = df_kec[df_kec['DESA'] == selected_desa] if selected_desa != "Semua" else df_kec

    if 'JENIS PERKERASAN' in df.columns:
        jenis_list = sorted(df_filtered['JENIS PERKERASAN'].dropna().unique())
        selected_jenis = st.multiselect("Pilih Jenis Perkerasan", jenis_list, default=jenis_list)
        df_filtered = df_filtered[df_filtered['JENIS PERKERASAN'].isin(selected_jenis)]

# ========== TABS ==========
tab1, tab2, tab3, tab4 = st.tabs(["📊 Ringkasan", "📈 Grafik", "🗺️ Peta", "📄 Data"])

# ========== TAB RINGKASAN ==========
with tab1:
    st.subheader("📊 Statistik Kondisi Jalan")

    total_baik = int(df_filtered['BAIK (meter)'].sum())
    rusak_ringan = int(df_filtered['RUSAK RINGAN (meter)'].sum())
    rusak_sedang = int(df_filtered['RUSAK SEDANG (meter)'].sum())
    rusak_berat = int(df_filtered['RUSAK BERAT (meter)'].sum())
    total_ruas = int(df_filtered['NAMA RUAS JALAN DESA'].count())

    total_rusak = rusak_ringan + rusak_sedang + rusak_berat
    total_jalan = total_baik + total_rusak

    # Hitung persentase
    def get_persen(val):
        return (val / total_jalan * 100) if total_jalan else 0

    persen_baik = get_persen(total_baik)
    persen_ringan = get_persen(rusak_ringan)
    persen_sedang = get_persen(rusak_sedang)
    persen_berat = get_persen(rusak_berat)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Baik", f"{total_baik:,} m", f"{persen_baik:.1f}%")
    col2.metric("⚠️ Rusak Ringan", f"{rusak_ringan:,} m", f"{persen_ringan:.1f}%")
    col3.metric("⚠️ Rusak Sedang", f"{rusak_sedang:,} m", f"{persen_sedang:.1f}%")
    col4.metric("❌ Rusak Berat", f"{rusak_berat:,} m", f"{persen_berat:.1f}%")

    st.markdown(f"""
    **DESKRIPSI UMUM:**
    - **Total ruas jalan keseluruhan**: `{total_ruas:,} ruas jalan`
    - **Total panjang jalan keseluruhan**: `{total_jalan:,} meter`
    - Total panjang jalan dalam kondisi **baik**: `{total_baik:,} meter` ({persen_baik:.1f}%)
    - Total panjang jalan yang mengalami **kerusakan**: `{total_rusak:,} meter` ({100 - persen_baik:.1f}%)
    """)


with tab2:
    st.subheader("📈 Grafik Kondisi Jalan")

    agg_cols = ['BAIK (meter)', 'RUSAK RINGAN (meter)', 'RUSAK SEDANG (meter)', 'RUSAK BERAT (meter)']

    if selected_desa != "Semua":
        grouping = 'NAMA RUAS JALAN DESA'
    elif selected_kec != "Semua":
        grouping = 'DESA'
    elif selected_kab != "Semua":
        grouping = 'KECAMATAN'
    else:
        grouping = 'KABUPATEN'

    if grouping in df_filtered.columns:
        summary = df_filtered.groupby(grouping)[agg_cols].sum()
        fig_meter = px.bar(
            summary,
            x=summary.index,
            y=agg_cols,
            title=f"Panjang Jalan Berdasarkan Kondisi per {grouping}",
            labels={"value": "Panjang Jalan (m)", grouping: grouping},
            barmode='stack',
            template='simple_white',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_meter.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_meter, use_container_width=True)

        percent_df = summary.div(summary.sum(axis=1), axis=0) * 100
        fig_percent = px.bar(
            percent_df,
            x=percent_df.index,
            y=agg_cols,
            title=f"Persentase Kondisi Jalan per {grouping}",
            labels={"value": "Persentase (%)", grouping: grouping},
            barmode='stack',
            template='simple_white',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_percent.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_percent, use_container_width=True)
    else:
        st.info("Data tidak mencukupi untuk membuat grafik.")

with tab3:
    st.subheader("🗺️ Peta Jalan Desa (Highlight Jalur Jalan)")

    if {'LAT AWAL', 'LNG AWAL', 'LAT AKHIR', 'LNG AKHIR'}.issubset(df_filtered.columns):
        df_map = df_filtered.dropna(subset=['LAT AWAL', 'LNG AWAL', 'LAT AKHIR', 'LNG AKHIR'])

        if not df_map.empty:
            m = folium.Map(
                location=[df_map['LAT AWAL'].mean(), df_map['LNG AWAL'].mean()],
                zoom_start=11,
                control_scale=True,
                tiles='CartoDB positron'
            )

            for _, row in df_map.iterrows():
                lat_awal = row['LAT AWAL']
                lng_awal = row['LNG AWAL']
                lat_akhir = row['LAT AKHIR']
                lng_akhir = row['LNG AKHIR']
                google_maps_directions = f"https://www.google.com/maps/dir/{lat_awal},{lng_awal}/{lat_akhir},{lng_akhir}"

                popup_html = f"""
                <b>Desa:</b> {row.get('DESA', '')}<br>
                <b>Ruas Jalan:</b> {row.get('NAMA RUAS JALAN DESA', '')}<br>
                <b>Jenis Perkerasan:</b> {row.get('JENIS PERKERASAN', '')}<br>
                <b>Total Panjang:</b> {row.get('TOTAL PANJANG JALAN (meter)', '')} m<br>
                <a href="{google_maps_directions}" target="_blank">🛣️ Lihat Rute di Google Maps</a>
                """

                folium.PolyLine(
                    locations=[(lat_awal, lng_awal), (lat_akhir, lng_akhir)],
                    color='red',
                    weight=4,
                    popup=folium.Popup(folium.IFrame(popup_html, width=300, height=150), max_width=300)
                ).add_to(m)

            st_folium(m, use_container_width=True)
        else:
            st.info("Tidak ada data jalan dengan koordinat untuk ditampilkan.")
    else:
        st.warning("Data tidak memiliki kolom koordinat awal dan akhir.")

with tab4:
    st.subheader("📄 Data Mentah")
    st.dataframe(df_filtered)

st.caption("📌 Sumber data: DATA JALAN DESA.xlsx")
