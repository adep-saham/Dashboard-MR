import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go

# ======================================================
# 🔧 SETUP GOOGLE SHEETS
# ======================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPES
)

client = gspread.authorize(creds)

SPREADSHEET_ID = "1Ro8FWl9HTCxdiqpAuFbqA4St7NNFuzHyJHKXQ4fEwps"
SHEET_NAME = "Sheet1"
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# ======================================================
# 🔧 HEADER + SAFETY
# ======================================================

HEADER = [
    "Jenis","Nama_Indikator","Kategori","Unit","Pemilik","Tanggal",
    "Target","Realisasi","Satuan","Keterangan","Arah",
    "Target_Min","Target_Max","Tahun"
]

# ======================================================
# 🧮 STATUS LOGIC (DARI AWAL DIDEFINISIKAN)
# ======================================================

def hitung_status(row):
    try:
        real = float(row["Realisasi"])
        target = float(row["Target"])
    except:
        return "N/A"

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

# ======================================================
# 🔧 CRUD GOOGLE SHEETS
# ======================================================

def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # jika kosong → buat df kosong
    if df.empty:
        df = pd.DataFrame(columns=HEADER)
        save_data(df)

    # Tambahkan kolom yang hilang
    for col in HEADER:
        if col not in df.columns:
            df[col] = ""

    # Convert numerik
    df["Target"] = pd.to_numeric(df["Target"], errors="coerce").fillna(0)
    df["Realisasi"] = pd.to_numeric(df["Realisasi"], errors="coerce").fillna(0)
    df["Target_Min"] = pd.to_numeric(df["Target_Min"], errors="coerce").fillna(0)
    df["Target_Max"] = pd.to_numeric(df["Target_Max"], errors="coerce").fillna(0)

    # Hitung status
    df["Status"] = df.apply(hitung_status, axis=1)

    # Skor Normal
    df["Skor_Normal"] = ((df["Realisasi"] / df["Target"]) * 100).fillna(0).round(2)

    return df


def save_data(df):
    sheet.clear()
    sheet.append_row(HEADER)
    rows = df.values.tolist()
    for r in rows:
        sheet.append_row(r)


def add_row(row_dict):
    """Tambahkan data 1 baris ke Sheet"""
    sheet.append_row([row_dict[h] for h in HEADER])


def delete_row(idx):
    sheet.delete_rows(idx + 2)  # offset header


def clear_all():
    sheet.clear()
    sheet.append_row(HEADER)



# ======================================================
# 🎨 UI
# ======================================================

st.set_page_config(page_title="Dashboard KPI/KRI/KCI", layout="wide")
st.title("📊 Dashboard KPI / KRI / KCI – Google Sheets Version")

df = load_data()

# ======================================================
# ➕ INPUT INDIKATOR BARU
# ======================================================

st.subheader("➕ Tambah Indikator Baru")

c1, c2, c3 = st.columns(3)
with c1:
    jenis = st.selectbox("Jenis", ["KPI","KRI","KCI"])
    kategori = st.text_input("Kategori")
    unit = st.text_input("Unit")

with c2:
    nama = st.text_input("Nama Indikator")
    pemilik = st.text_input("Pemilik")
    tanggal = st.date_input("Tanggal")

with c3:
    target = st.number_input("Target", 0.0)
    real = st.number_input("Realisasi", 0.0)
    satuan = st.text_input("Satuan")

arah = st.selectbox("Arah Penilaian", ["Higher is Better", "Lower is Better", "Range"])

tmin, tmax = None, None
if arah == "Range":
    r1, r2 = st.columns(2)
    with r1:
        tmin = st.number_input("Target Min", 0.0)
    with r2:
        tmax = st.number_input("Target Max", 0.0)

ket = st.text_area("Keterangan")

if st.button("💾 Simpan Indikator"):
    new_row = {
        "Jenis": jenis,
        "Nama_Indikator": nama,
        "Kategori": kategori,
        "Unit": unit,
        "Pemilik": pemilik,
        "Tanggal": str(tanggal),
        "Target": target,
        "Realisasi": real,
        "Satuan": satuan,
        "Keterangan": ket,
        "Arah": arah,
        "Target_Min": tmin,
        "Target_Max": tmax,
        "Tahun": tanggal.year
    }
    add_row(new_row)
    st.success("✔ Indikator berhasil ditambahkan!")
    st.rerun()

# ======================================================
# 📋 DATA TABLE
# ======================================================

st.subheader("📋 Data Indikator")
st.dataframe(df, use_container_width=True)

# ======================================================
# ✏️ INLINE EDIT
# ======================================================

st.subheader("✏️ Edit Tabel")
edited = st.data_editor(df, num_rows="dynamic")

if st.button("💾 Simpan Perubahan Table"):
    save_data(edited)
    st.success("Perubahan tersimpan!")
    st.rerun()

# ======================================================
# 🗑 HAPUS INDIKATOR
# ======================================================

st.subheader("🗑 Hapus Indikator")

if len(df) > 0:
    pilih = st.selectbox("Pilih indikator:", df["Nama_Indikator"])
    if st.button("Hapus Sekarang"):
        idx = df.index[df["Nama_Indikator"] == pilih][0]
        delete_row(idx)
        st.success("✔ Berhasil dihapus.")
        st.rerun()
else:
    st.info("Tidak ada data untuk dihapus.")

# ======================================================
# ⚠ CLEAR SEMUA DATA
# ======================================================

with st.expander("⚠ Clear Semua Data"):
    if st.button("🧹 Hapus Semua Data"):
        clear_all()
        st.warning("SEMUA data telah dihapus!")
        st.rerun()

# ======================================================
# 🔥 DASHBOARD MERAH
# ======================================================

st.subheader("🚨 Indikator Status Merah")

df_merah = df[df["Status"] == "Merah"]

def mini_chart(row):

    # Judul kecil
    st.markdown(
        f"<div style='font-size:14px; font-weight:600;'>{row['Nama_Indikator']}</div>",
        unsafe_allow_html=True
    )

    # Unit & kategori
    st.caption(f"Unit: {row['Unit']} | Kategori: {row['Kategori']}")

    # Hitung capaian (%)
    target = float(row["Target"])
    real = float(row["Realisasi"])
    capai = (real / target * 100) if target > 0 else 0

    # Tampilkan capaian
    st.markdown(
        f"<span style='color:#d9534f; font-weight:bold;'>Capaian: {capai:.2f}%</span>",
        unsafe_allow_html=True
    )

    # --- MINI HORIZONTAL BAR ---
    fig = go.Figure()

    # Realisasi
    fig.add_trace(go.Bar(
        x=[real],
        y=["Realisasi"],
        orientation='h',
        marker=dict(color="#ff6b6b"),
        width=0.35
    ))

    # Target
    fig.add_trace(go.Bar(
        x=[target],
        y=["Target"],
        orientation='h',
        marker=dict(color="#9aa0a6"),
        width=0.35
    ))

    fig.update_layout(
        height=120,
        margin=dict(l=0, r=0, t=5, b=0),
        showlegend=False,
        xaxis=dict(showgrid=True, zeroline=False),
        yaxis=dict(showgrid=False)
    )

    st.plotly_chart(fig, use_container_width=True)


def tampil_section(title, data):
    st.markdown(f"### {title}")

    if len(data) == 0:
        st.success("✨ Semua indikator aman.")
        return

    col1, col2, col3, col4 = st.columns(4, gap="large")
    cols = [col1, col2, col3, col4]

    for idx, (_, row) in enumerate(data.iterrows()):
        with cols[idx % 4]:
            mini_chart(row)


tampil_section("🔥 KPI Merah", df_merah[df_merah["Jenis"] == "KPI"])
tampil_section("⚠ KRI Merah", df_merah[df_merah["Jenis"] == "KRI"])
tampil_section("🔐 KCI Merah", df_merah[df_merah["Jenis"] == "KCI"])

