###############################################################
#  app.py – Final Deploy Version (CSV Export, No Excel Engines)
#  KPI / KRI / KCI Flexible • Tahun Per Dataset • No Errors
###############################################################

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
from datetime import datetime

# ============================================================
#  THEME COLORS (Corporate ANTAM)
# ============================================================
COLOR_GREEN = "#C8F7C5"
COLOR_RED   = "#F7C5C5"
COLOR_GREY  = "#E0E0E0"
COLOR_GOLD  = "#C8A951"
COLOR_TEAL  = "#007E6D"

# ============================================================
#  STREAMLIT PAGE SETTINGS
# ============================================================
st.set_page_config(page_title="Dashboard KPI/KRI/KCI", layout="wide")

st.markdown(f"""
<style>
body {{
    background-color: #F4F4F4;
}}
.main-title {{
    color: {COLOR_TEAL};
    font-size: 40px;
    font-weight: 700;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>📊 Dashboard KPI / KRI / KCI</h1>", unsafe_allow_html=True)


# ============================================================
#  FOLDER DATA TAHUN
# ============================================================
DATA_FOLDER = "data_tahun"
os.makedirs(DATA_FOLDER, exist_ok=True)

def get_file_path(tahun):
    return os.path.join(DATA_FOLDER, f"data_{tahun}.csv")


# ============================================================
#  INITIAL EMPTY DATAFRAME
# ============================================================
def init_data():
    return pd.DataFrame(columns=[
        "Jenis","Nama_Indikator","Kategori","Unit","Pemilik","Tanggal",
        "Target","Realisasi","Satuan","Keterangan",
        "Arah","Target_Min","Target_Max","Tahun"
    ])


# ============================================================
#  FLEXIBLE LOGIC
# ============================================================
def hitung_status(row):
    arah = row.get("Arah", "Higher is Better")

    try:
        real = float(row["Realisasi"])
    except:
        return "N/A"

    if arah == "Higher is Better":
        return "Hijau" if real >= float(row["Target"]) else "Merah"

    if arah == "Lower is Better":
        return "Hijau" if real <= float(row["Target"]) else "Merah"

    if arah == "Range":
        try:
            mn = float(row["Target_Min"])
            mx = float(row["Target_Max"])
            return "Hijau" if mn <= real <= mx else "Merah"
        except:
            return "N/A"

    return "N/A"


# ============================================================
#  SIDEBAR PILIH TAHUN
# ============================================================
tahun_list = list(range(2024, 2031))
tahun_pilih = st.sidebar.selectbox("📅 Pilih Tahun Dataset", tahun_list, index=1)

FILE_NAME = get_file_path(tahun_pilih)

# ============================================================
#  LOAD DATA TAHUN
# ============================================================
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = init_data()


# ============================================================
#  INPUT FORM
# ============================================================
st.subheader("🧾 Input Indikator Baru")

with st.form("form_input"):
    c1, c2, c3 = st.columns(3)

    with c1:
        jenis    = st.selectbox("Jenis", ["KPI", "KRI", "KCI"])
        kategori = st.text_input("Kategori")
        unit     = st.text_input("Unit")

    with c2:
        nama    = st.text_input("Nama Indikator")
        pemilik = st.text_input("Pemilik")
        tanggal = st.date_input("Tanggal")

    with c3:
        target    = st.number_input("Target", 0.0)
        realisasi = st.number_input("Realisasi", 0.0)
        satuan    = st.text_input("Satuan")

    arah = st.selectbox("Arah Penilaian", [
        "Higher is Better", "Lower is Better", "Range"
    ])

    tmin = tmax = None
    if arah == "Range":
        tmin = st.number_input("Range Min", 0.0)
        tmax = st.number_input("Range Max", 0.0)

    ket = st.text_area("Keterangan")

    submit = st.form_submit_button("Tambah")

# Simpan jika submit
if submit:
    tahun_input = tanggal.year
    file_input  = get_file_path(tahun_input)

    new = pd.DataFrame([{
        "Jenis": jenis,
        "Nama_Indikator": nama,
        "Kategori": kategori,
        "Unit": unit,
        "Pemilik": pemilik,
        "Tanggal": tanggal.strftime("%Y-%m-%d"),
        "Target": target,
        "Realisasi": realisasi,
        "Satuan": satuan,
        "Keterangan": ket,
        "Arah": arah,
        "Target_Min": tmin,
        "Target_Max": tmax,
        "Tahun": tahun_input
    }])

    # append to file
    if os.path.exists(file_input):
        old = pd.read_csv(file_input)
        df_new = pd.concat([old, new], ignore_index=True)
    else:
        df_new = new

    df_new.to_csv(file_input, index=False)
    st.success(f"Indikator berhasil disimpan ke tahun {tahun_input}!")


# ============================================================
#  LOAD ULANG DF UNTUK TAHUN TERPILIH
# ============================================================
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = init_data()


# ============================================================
#  ADD STATUS COL
# ============================================================
if len(df) > 0:
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df["Status"]  = df.apply(hitung_status, axis=1)


# ============================================================
#  DELETE & CLEAR
# ============================================================
st.subheader("🗑️ Hapus / Clear Data Tahun Ini")

c1, c2 = st.columns(2)

with c1:
    if len(df) > 0:
        pilih = st.selectbox("Pilih indikator", df["Nama_Indikator"])
        if st.button("Hapus"):
            new_df = df[df["Nama_Indikator"] != pilih]
            new_df.to_csv(FILE_NAME, index=False)
            df = new_df.copy()
            st.success("Berhasil dihapus.")

with c2:
    if st.button("Clear Semua Data Tahun Ini"):
        empty = init_data()
        empty.to_csv(FILE_NAME, index=False)
        df = empty.copy()
        st.warning(f"Semua data tahun {tahun_pilih} telah dihapus.")


# ============================================================
#  SIDEBAR SUMMARY MINI
# ============================================================
st.sidebar.markdown("---")
st.sidebar.header("📊 Ringkasan Tahun Ini")

if len(df) > 0:
    total = len(df)
    hijau = (df["Status"] == "Hijau").sum()
    merah = (df["Status"] == "Merah").sum()
    na    = (df["Status"] == "N/A").sum()

    kpi = (df["Jenis"] == "KPI").sum()
    kri = (df["Jenis"] == "KRI").sum()
    kci = (df["Jenis"] == "KCI").sum()

    pct = hijau / total * 100 if total > 0 else 0

    st.sidebar.metric("Total", total)
    st.sidebar.metric("Hijau", hijau)
    st.sidebar.metric("Merah", merah)
    st.sidebar.metric("N/A", na)
    st.sidebar.markdown("---")
    st.sidebar.metric("KPI", kpi)
    st.sidebar.metric("KRI", kri)
    st.sidebar.metric("KCI", kci)
    st.sidebar.markdown("---")
    st.sidebar.metric("Capaian Hijau", f"{pct:.1f}%")

else:
    st.sidebar.info("Belum ada data.")


# ============================================================
#  TABEL COLORED (HTML)
# ============================================================
st.subheader("📋 Data (Colored)")

if len(df) > 0:
    html = """
    <table style='border-collapse:collapse;width:100%;'>
    <thead><tr>
    """

    # Header
    for col in df.columns:
        html += f"<th style='border:1px solid #ddd;padding:6px;background:#fafafa;'>{col}</th>"
    html += "</tr></thead><tbody>"

    # Rows
    for _, row in df.iterrows():
        status = row["Status"]
        if status == "Hijau": bg = COLOR_GREEN
        elif status == "Merah": bg = COLOR_RED
        else: bg = COLOR_GREY

        html += f"<tr style='background:{bg};'>"
        for col in df.columns:
            html += f"<td style='border:1px solid #ddd;padding:6px;'>{row[col]}</td>"
        html += "</tr>"

    html += "</tbody></table>"

    st.markdown(html, unsafe_allow_html=True)
else:
    st.info("Belum ada data.")


# ============================================================
#  EXPORT CSV
# ============================================================
st.subheader("📤 Export CSV Tahun Ini")

if len(df) > 0:
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name=f"export_{tahun_pilih}.csv",
        mime="text/csv"
    )
else:
    st.info("Tidak ada data untuk diexport.")


# ============================================================
#  CHARTS & HEATMAP
# ============================================================
if len(df) > 0:

    st.subheader("📊 Status per Jenis")
    g = df.groupby(["Jenis", "Status"]).size().reset_index(name="Jumlah")

    fig = px.bar(
        g,
        x="Jenis",
        y="Jumlah",
        color="Status",
        text="Jumlah",
        color_discrete_map={"Hijau": COLOR_TEAL, "Merah": COLOR_RED}
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Tren Target vs Realisasi")
    indicators = df["Nama_Indikator"].unique()

    pick = st.selectbox("Pilih indikator", indicators, key="trend_selector")

    d2 = df[df["Nama_Indikator"] == pick].sort_values("Tanggal")
    long = d2.melt(
        id_vars=["Tanggal"],
        value_vars=["Target", "Realisasi"],
        var_name="Jenis_Nilai",
        value_name="Nilai"
    )

    fig2 = px.line(
        long,
        x="Tanggal",
        y="Nilai",
        markers=True,
        color="Jenis_Nilai",
        color_discrete_map={"Target": COLOR_GOLD, "Realisasi": COLOR_TEAL}
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🗺️ Heatmap Unit vs Kategori")
    score_map = {"Hijau": 1, "Merah": 0, "N/A": 0.5}
    df["Score"] = df["Status"].map(score_map)

    pv = df.pivot_table(
        index="Unit",
        columns="Kategori",
        values="Score",
        aggfunc="mean"
    )

    fig3 = px.imshow(
        pv,
        text_auto=True,
        aspect="auto",
        color_continuous_scale=[COLOR_RED, COLOR_GREY, COLOR_GREEN]
    )
    st.plotly_chart(fig3, use_container_width=True)
