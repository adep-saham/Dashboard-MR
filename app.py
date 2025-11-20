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

# ============================================================
#  MODAL STATE
# ============================================================
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "row_to_edit" not in st.session_state:
    st.session_state.row_to_edit = None


# ============================================================
#  FUNGSI MEMBUKA & MENUTUP MODAL
# ============================================================
def open_modal(row_index):
    st.session_state.edit_mode = True
    st.session_state.row_to_edit = row_index


def close_modal():
    st.session_state.edit_mode = False
    st.session_state.row_to_edit = None


# ============================================================
#  TABEL DENGAN TOMBOL EDIT
# ============================================================
st.subheader("📋 Data (Colored)")

for i, row in df.iterrows():
    c1, c2 = st.columns([10, 1])
    with c1:
        st.write(
            f"**{row['Nama_Indikator']}** — {row['Kategori']} — {row['Unit']} — Status: {row['Status']}"
        )
    with c2:
        if st.button("✏️ Edit", key=f"editbtn_{i}", use_container_width=True):
            open_modal(i)


# ============================================================
#  POPUP MODAL EDIT
# ============================================================
if st.session_state.edit_mode:

    # Ambil data
    idx = st.session_state.row_to_edit
    data = df.loc[idx]

    # ----------- MODAL LAYER -----------
    modal_css = """
    <style>
    .modal-overlay {
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(0,0,0,0.45);
        z-index: 99998;
    }
    .modal-box {
        position: fixed;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 25px;
        width: 60%;
        border-radius: 10px;
        z-index: 99999;
        box-shadow: 0px 0px 20px rgba(0,0,0,0.3);
    }
    </style>
    """

    st.markdown(modal_css, unsafe_allow_html=True)

    modal_html = """
    <div class="modal-overlay"></div>
    <div class="modal-box">
    """
    st.markdown(modal_html, unsafe_allow_html=True)

    st.subheader("✏️ Edit Data Indikator")

    # ----------- FORM EDIT DALAM MODAL -----------
    col1, col2, col3 = st.columns(3)

    with col1:
        e_jenis = st.selectbox("Jenis", ["KPI", "KRI", "KCI"],
                               index=["KPI","KRI","KCI"].index(data["Jenis"]),
                               key="modal_jenis")
        e_kategori = st.text_input("Kategori", data["Kategori"], key="modal_kategori")

    with col2:
        e_nama = st.text_input("Nama Indikator", data["Nama_Indikator"], key="modal_nama")
        e_pemilik = st.text_input("Pemilik", data["Pemilik"], key="modal_pemilik")

    with col3:
        e_target = st.number_input("Target", float(data["Target"]), key="modal_target")
        e_realisasi = st.number_input("Realisasi", float(data["Realisasi"]), key="modal_realisasi")

    e_satuan = st.text_input("Satuan", data["Satuan"], key="modal_satuan")
    e_arah = st.selectbox(
        "Arah Penilaian",
        ["Higher is Better", "Lower is Better", "Range"],
        index=["Higher is Better","Lower is Better","Range"].index(data["Arah"]),
        key="modal_arah"
    )
    e_ket = st.text_area("Keterangan", data["Keterangan"], height=120, key="modal_ket")

    # ----------- TOMBOL SAVE / CANCEL -----------
    csave, ccancel = st.columns(2)

    with csave:
        if st.button("💾 Simpan Perubahan", use_container_width=True):

            df.loc[idx, "Jenis"] = e_jenis
            df.loc[idx, "Nama_Indikator"] = e_nama
            df.loc[idx, "Kategori"] = e_kategori
            df.loc[idx, "Pemilik"] = e_pemilik
            df.loc[idx, "Target"] = e_target
            df.loc[idx, "Realisasi"] = e_realisasi
            df.loc[idx, "Satuan"] = e_satuan
            df.loc[idx, "Arah"] = e_arah
            df.loc[idx, "Keterangan"] = e_ket

            df.to_csv(FILE_NAME, index=False)
            st.success("Data berhasil diperbarui!")
            close_modal()
            st.rerun()

    with ccancel:
        if st.button("❌ Batal", use_container_width=True):
            close_modal()
            st.rerun()

    # Tutup modal div
    st.markdown("</div>", unsafe_allow_html=True)


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

# ============================================================
#   ✏️ EDIT LANGSUNG DI TABEL (INLINE EDIT)
# ============================================================

st.subheader("✏️ Edit Langsung di Tabel (Inline Edit)")

# Tampilkan editor
edited_df = st.data_editor(
    df,
    num_rows="dynamic",         # bisa tambah / delete row
    use_container_width=True,
    hide_index=False
)

# Tombol simpan perubahan
if st.button("💾 Simpan Perubahan Tabel"):
    edited_df.to_csv(FILE_NAME, index=False)
    st.success("Perubahan pada tabel berhasil disimpan!")
    st.rerun()


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























