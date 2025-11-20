###############################################################
#  app.py – FINAL CLEAN VERSION (Year System + Range Logic FIX)
###############################################################

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ------------------------------------------------------------
#  THEME COLORS
# ------------------------------------------------------------
COLOR_GREEN = "#C8F7C5"
COLOR_RED   = "#F7C5C5"
COLOR_GREY  = "#E0E0E0"
COLOR_GOLD  = "#C8A951"
COLOR_TEAL  = "#007E6D"

st.set_page_config(page_title="Dashboard KPI/KRI/KCI", layout="wide")

st.markdown(f"""
<style>
.main-title {{
    font-size: 36px;
    font-weight: bold;
    color: {COLOR_TEAL};
}}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>📊 Dashboard KPI / KRI / KCI</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
#  DATA FOLDER
# ------------------------------------------------------------
DATA_FOLDER = "data_tahun"
os.makedirs(DATA_FOLDER, exist_ok=True)

def get_file_path(tahun):
    return os.path.join(DATA_FOLDER, f"data_{tahun}.csv")

# ------------------------------------------------------------
#  INITIAL EMPTY DATA
# ------------------------------------------------------------
def init_data():
    return pd.DataFrame(columns=[
        "Jenis","Nama_Indikator","Kategori","Unit","Pemilik","Tanggal",
        "Target","Realisasi","Satuan","Keterangan",
        "Arah","Target_Min","Target_Max","Tahun"
    ])

# ------------------------------------------------------------
#  STATUS LOGIC
# ------------------------------------------------------------
def hitung_status(row):
    arah = row.get("Arah", "Higher is Better")
    try: real = float(row["Realisasi"])
    except: return "N/A"

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


# ------------------------------------------------------------
#  SIDEBAR SELECT YEAR
# ------------------------------------------------------------
tahun_list = list(range(2024, 2032))
tahun_pilih = st.sidebar.selectbox("📅 Pilih Tahun Dataset", tahun_list, index=tahun_list.index(2025))

FILE_NAME = get_file_path(tahun_pilih)

# ------------------------------------------------------------
#  LOAD DATA
# ------------------------------------------------------------
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = init_data()

# ------------------------------------------------------------
#  INPUT FORM (VERSION FIXED)
# ------------------------------------------------------------
st.subheader("🧾 Input Indikator Baru")

with st.form("form_input", clear_on_submit=False):

    col1, col2, col3 = st.columns(3)

    with col1:
        jenis    = st.selectbox("Jenis", ["KPI", "KRI", "KCI"], key="jenis")
        kategori = st.text_input("Kategori", key="kategori")
        unit     = st.text_input("Unit", key="unit")

    with col2:
        nama     = st.text_input("Nama Indikator", key="nama")
        pemilik  = st.text_input("Pemilik", key="pemilik")
        tanggal  = st.date_input("Tanggal", key="tanggal")

    with col3:
        target    = st.number_input("Target", 0.0, key="target")
        realisasi = st.number_input("Realisasi", 0.0, key="realisasi")
        satuan    = st.text_input("Satuan", key="satuan")

    # -------- ARAH PENILAIAN (TRIGGER RANGE) --------
    arah = st.selectbox(
        "Arah Penilaian",
        ["Higher is Better", "Lower is Better", "Range"],
        key="arah"
    )

    tmin, tmax = None, None

    # -------- RANGE INPUT (ONLY SHOW IF RANGE) --------
    show_range = (arah == "Range")

    if show_range:
        st.markdown("### 🎯 Pengaturan Range Target")

        r1, r2 = st.columns(2)
        with r1:
            tmin = st.number_input("Target Minimal", value=0.0, step=1.0, key="tmin")
        with r2:
            tmax = st.number_input("Target Maksimal", value=0.0, step=1.0, key="tmax")

    ket = st.text_area("Keterangan", key="ket")

    submit = st.form_submit_button("➕ Tambah Indikator")


# ------------------------------------------------------------
#  SAVE SUBMISSION
# ------------------------------------------------------------
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

    if os.path.exists(file_input):
        old = pd.read_csv(file_input)
        saved = pd.concat([old, new], ignore_index=True)
    else:
        saved = new

    saved.to_csv(file_input, index=False)

    st.success(f"Indikator berhasil ditambahkan ke tahun {tahun_input}!")
    st.experimental_rerun()


# ------------------------------------------------------------
#  RELOAD DATA
# ------------------------------------------------------------
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = init_data()


# ------------------------------------------------------------
#  STATUS COLUMN
# ------------------------------------------------------------
if len(df) > 0:
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df["Status"]  = df.apply(hitung_status, axis=1)


# ------------------------------------------------------------
#  DELETE / CLEAR
# ------------------------------------------------------------
st.subheader("🗑️ Hapus / Clear Data Tahun Ini")

del1, del2 = st.columns(2)

with del1:
    if len(df) > 0:
        pilih = st.selectbox("Pilih indikator", df["Nama_Indikator"])
        if st.button("Hapus"):
            df2 = df[df["Nama_Indikator"] != pilih]
            df2.to_csv(FILE_NAME, index=False)
            st.success("Data terhapus.")
            st.experimental_rerun()

with del2:
    if st.button("Clear Semua Data"):
        empty = init_data()
        empty.to_csv(FILE_NAME, index=False)
        st.warning("Data tahun ini telah dikosongkan.")
        st.experimental_rerun()


# ------------------------------------------------------------
#  SIDEBAR SUMMARY
# ------------------------------------------------------------
st.sidebar.header("📊 Ringkasan Tahun Ini")

if len(df) > 0:
    total = len(df)
    hijau = (df["Status"] == "Hijau").sum()
    merah = (df["Status"] == "Merah").sum()
    na    = (df["Status"] == "N/A").sum()

    st.sidebar.metric("Total", total)
    st.sidebar.metric("Hijau", hijau)
    st.sidebar.metric("Merah", merah)
    st.sidebar.metric("N/A", na)


# ------------------------------------------------------------
#  HTML TABLE (COLORED)
# ------------------------------------------------------------
st.subheader("📋 Data (Colored)")

if len(df) > 0:

    html = "<table style='width:100%;border-collapse:collapse;'>"

    # header
    html += "<thead><tr>"
    for col in df.columns:
        html += f"<th style='border:1px solid #ccc;padding:6px;background:#eee;'>{col}</th>"
    html += "</tr></thead><tbody>"

    # rows
    for _, row in df.iterrows():
        status = row["Status"]
        if status == "Hijau": bg = COLOR_GREEN
        elif status == "Merah": bg = COLOR_RED
        else: bg = COLOR_GREY

        html += f"<tr style='background:{bg};'>"
        for col in df.columns:
            html += f"<td style='border:1px solid #ccc;padding:6px;'>{row[col]}</td>"
        html += "</tr>"

    html += "</tbody></table>"

    st.markdown(html, unsafe_allow_html=True)


# ------------------------------------------------------------
#  EXPORT CSV
# ------------------------------------------------------------
st.subheader("📤 Export CSV Tahun Ini")

if len(df) > 0:
    csv = df.to_csv(index=False).encode()
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"export_{tahun_pilih}.csv",
        mime="text/csv"
    )


# ------------------------------------------------------------
#  CHARTS
# ------------------------------------------------------------
if len(df) > 0:

    # Status bar chart
    st.subheader("📊 Status per Jenis")
    g = df.groupby(["Jenis", "Status"]).size().reset_index(name="Jumlah")
    fig = px.bar(g, x="Jenis", y="Jumlah", color="Status",
                  color_discrete_map={"Hijau": COLOR_TEAL, "Merah": COLOR_RED})
    st.plotly_chart(fig, use_container_width=True)

    # Trend chart
    st.subheader("📈 Tren Target vs Realisasi")
    indikator_list = df["Nama_Indikator"].unique()
    pick = st.selectbox("Pilih Indikator", indikator_list, key="trend_pick")

    d2 = df[df["Nama_Indikator"] == pick].sort_values("Tanggal")
    melt = d2.melt(id_vars=["Tanggal"], value_vars=["Target","Realisasi"],
                   var_name="Jenis", value_name="Nilai")

    fig2 = px.line(melt, x="Tanggal", y="Nilai", color="Jenis",
                    markers=True,
                    color_discrete_map={"Target": COLOR_GOLD, "Realisasi": COLOR_TEAL})
    st.plotly_chart(fig2, use_container_width=True)
