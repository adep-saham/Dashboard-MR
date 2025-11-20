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
    try:
        real = float(row["Realisasi"])
        target = float(row["Target"])
    except:
        return "N/A"

    # normalisasi
    arah = str(row.get("Arah", "")).strip().lower()

    if arah == "higher is better":
        return "Hijau" if real >= target else "Merah"

    if arah == "lower is better":
        return "Hijau" if real <= target else "Merah"

    if arah == "range":
        try:
            tmin = float(row["Target_Min"])
            tmax = float(row["Target_Max"])
            return "Hijau" if tmin <= real <= tmax else "Merah"
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

# Hapus baris-baris sampah / kosong
df = df[df["Nama_Indikator"].notna()]
df = df[df["Nama_Indikator"] != "nan"]
df = df[df["Nama_Indikator"] != ""]
df = df[df["Nama_Indikator"].str.strip() != ""]

# ====================================================
# HITUNG ULANG STATUS SETELAH LOAD CSV
# ====================================================
if len(df) > 0:
    df["Status"] = df.apply(hitung_status, axis=1)

# ------------------------------------------------------------
#  INPUT FORM (VERSION FIXED)
# ------------------------------------------------------------
st.subheader("🧾 Input Indikator Baru")

c1, c2, c3 = st.columns(3)

with c1:
    jenis    = st.selectbox("Jenis", ["KPI", "KRI", "KCI"])
    kategori = st.text_input("Kategori")
    unit     = st.text_input("Unit")

with c2:
    nama     = st.text_input("Nama Indikator")
    pemilik  = st.text_input("Pemilik")
    tanggal  = st.date_input("Tanggal")

with c3:
    target    = st.number_input("Target", 0.0)
    realisasi = st.number_input("Realisasi", 0.0)
    satuan    = st.text_input("Satuan")

arah = st.selectbox(
    "Arah Penilaian",
    ["Higher is Better", "Lower is Better", "Range"]
)

tmin, tmax = None, None

# ----- DYNAMIC RANGE UI -----
if arah == "Range":
    st.markdown("### 🎯 Pengaturan Range Target")

    colr1, colr2 = st.columns(2)
    with colr1:
        tmin = st.number_input("Target Minimal", value=0.0)
    with colr2:
        tmax = st.number_input("Target Maksimal", value=0.0)

ket = st.text_area("Keterangan")

# ---- SUBMIT BUTTON ----
if st.button("➕ Tambah Indikator"):

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

    st.rerun()  # << FIX PENTING

# ============================================================
#  DELETE & CLEAR DATA TAHUN INI (POSITION FIXED)
# ============================================================
st.subheader("🗑️ Hapus / Clear Data Tahun Ini")

if len(df) == 0:
    st.info("Belum ada data untuk tahun ini.")
else:

    # Buat kolom: 75% untuk dropdown + delete, 25% untuk clear
    col_del_left, col_del_right = st.columns([6, 2])

    # ---------------- LEFT SIDE (Dropdown + Hapus) ----------------
    with col_del_left:
        pilih_hapus = st.selectbox(
            "Pilih indikator untuk dihapus:",
            df["Nama_Indikator"].unique(),
            key="hapus_indikator"
        )

        if st.button("Hapus Indikator Ini"):
            df_new = df[df["Nama_Indikator"] != pilih_hapus]
            df_new.to_csv(FILE_NAME, index=False)
            st.success(f"Indikator '{pilih_hapus}' berhasil dihapus.")
            st.rerun()

    # ---------------- RIGHT SIDE (CLEAR BUTTON) ----------------
    with col_del_right:
        st.write("")  # memberi jarak vertikal agar tombol pas di baris yang sama
        st.write("")  # tambahan jarak
        if st.button("🧹 Clear Semua Data Tahun Ini"):
            kosong = init_data()
            kosong.to_csv(FILE_NAME, index=False)
            st.warning("SEMUA data tahun ini telah dihapus!")
            st.rerun()


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

# ============================================================
#  EDIT INDIKATOR (FORM EDIT TERPISAH)
# ============================================================
st.subheader("✏️ Edit Indikator")

if len(df) == 0:
    st.info("Belum ada data untuk diedit.")
else:

    # ===========================
    # PILIH DATA YANG AKAN DIEDIT
    # ===========================
    pilih_edit = st.selectbox(
        "Pilih indikator untuk diedit:",
        df["Nama_Indikator"].unique(),
        key="edit_picker"
    )

    data_edit = df[df["Nama_Indikator"] == pilih_edit].iloc[0]

    st.markdown("### 🔧 Edit Data:")

    c1, c2, c3 = st.columns(3)

    with c1:
        e_jenis = st.selectbox("Jenis", ["KPI", "KRI", "KCI"], index=["KPI","KRI","KCI"].index(data_edit["Jenis"]))
        e_kategori = st.text_input("Kategori", data_edit["Kategori"])
        e_unit = st.text_input("Unit", data_edit["Unit"])

    with c2:
        e_nama = st.text_input("Nama Indikator", data_edit["Nama_Indikator"])
        e_pemilik = st.text_input("Pemilik", data_edit["Pemilik"])
        e_tanggal = st.date_input("Tanggal", pd.to_datetime(data_edit["Tanggal"]))

    with c3:
        e_target = st.number_input("Target", value=float(data_edit["Target"]))
        e_realisasi = st.number_input("Realisasi", value=float(data_edit["Realisasi"]))
        e_satuan = st.text_input("Satuan", data_edit["Satuan"])

    # -------------------------------------------------------
    # ARAH PENILAIAN (EDIT)
    # -------------------------------------------------------
    e_arah = st.selectbox(
        "Arah Penilaian",
        ["Higher is Better", "Lower is Better", "Range"],
        index=["Higher is Better", "Lower is Better", "Range"].index(data_edit["Arah"])
    )

    e_min, e_max = None, None

    if e_arah == "Range":
        r1, r2 = st.columns(2)
        with r1:
            e_min = st.number_input("Target Minimal", value=float(data_edit["Target_Min"]) if pd.notna(data_edit["Target_Min"]) else 0.0)
        with r2:
            e_max = st.number_input("Target Maksimal", value=float(data_edit["Target_Max"]) if pd.notna(data_edit["Target_Max"]) else 0.0)

    e_ket = st.text_area("Keterangan", data_edit["Keterangan"])

    # =======================
    #  SIMPAN PERUBAHAN
    # =======================
    if st.button("💾 Simpan Perubahan"):

        # Update baris pada dataframe
        idx = df.index[df["Nama_Indikator"] == pilih_edit][0]

        df.loc[idx, "Jenis"] = e_jenis
        df.loc[idx, "Nama_Indikator"] = e_nama
        df.loc[idx, "Kategori"] = e_kategori
        df.loc[idx, "Unit"] = e_unit
        df.loc[idx, "Pemilik"] = e_pemilik
        df.loc[idx, "Tanggal"] = e_tanggal.strftime("%Y-%m-%d")
        df.loc[idx, "Target"] = e_target
        df.loc[idx, "Realisasi"] = e_realisasi
        df.loc[idx, "Satuan"] = e_satuan
        df.loc[idx, "Keterangan"] = e_ket
        df.loc[idx, "Arah"] = e_arah
        df.loc[idx, "Target_Min"] = e_min
        df.loc[idx, "Target_Max"] = e_max

        df.to_csv(FILE_NAME, index=False)

        st.success(f"Perubahan pada indikator '{pilih_edit}' telah disimpan!")
        st.rerun()


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












