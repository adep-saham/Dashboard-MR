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

# GANTI DENGAN ID GOOGLE SHEETS KAMU
SPREADSHEET_ID = "1Ro8FWl9HTCxdiqpAuFbqA4St7NNFuzHyJHKXQ4fEwps"
SHEET_NAME = "Sheet1"

sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# ============================================================
# 🔧 CRUD FUNCTIONS UNTUK GOOGLE SHEETS
# ============================================================

HEADER = [
    "Jenis","Nama_Indikator","Kategori","Unit","Pemilik","Tanggal",
    "Target","Realisasi","Satuan","Keterangan","Arah",
    "Target_Min","Target_Max","Tahun"
]

def load_data():
    """Load data dari Google Sheets → DataFrame"""
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df


def save_data(df):
    """Simpan DataFrame → Google Sheets"""
    sheet.clear()
    sheet.append_row(HEADER)
    rows = df.values.tolist()
    for r in rows:
        sheet.append_row(r)


def delete_row(index):
    """Menghapus 1 baris berdasarkan index (0-based DataFrame)"""
    # +2 karena:
    # baris 1 = HEADER
    # baris 2 = index 0 df
    sheet.delete_rows(index + 2)


def clear_all():
    """Hapus seluruh data → hanya header yang ditinggal"""
    sheet.clear()
    sheet.append_row(HEADER)



# ======================================================
# 🎨 UI SETUP
# ======================================================

st.set_page_config(page_title="Dashboard KPI/KRI/KCI", layout="wide")
st.title("📊 Dashboard KPI / KRI / KCI – Google Sheets Version")

# ======================================================
# 📥 LOAD DATA
# ======================================================

df = load_data()

# =====================================================
# TAMBAHKAN KOLOM STATUS & SKOR NORMAL SETELAH LOAD DATA
# =====================================================

if len(df) > 0:

    # pastikan numeric
    df["Target"] = pd.to_numeric(df["Target"], errors="coerce")
    df["Realisasi"] = pd.to_numeric(df["Realisasi"], errors="coerce")
    df["Target_Min"] = pd.to_numeric(df.get("Target_Min"), errors="coerce")
    df["Target_Max"] = pd.to_numeric(df.get("Target_Max"), errors="coerce")

    # status
    df["Status"] = df.apply(hitung_status, axis=1)

    # skor normal (%)
    df["Skor_Normal"] = (df["Realisasi"] / df["Target"]) * 100
    df["Skor_Normal"] = df["Skor_Normal"].fillna(0).round(2)


# ===========================
#  Tambah kolom STATUS
# ===========================
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

# jika kosong → buat header
if df.empty:
    df = pd.DataFrame(columns=HEADER)
    save_data(df)

# ======================================================
# 🧮 STATUS LOGIC
# ======================================================

def hitung_status(row):
    try:
        real = float(row["Realisasi"])
        target = float(row["Target"])
    except:
        return "N/A"

    arah = str(row.get("Arah","")).lower()

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

if len(df) > 0:
    df["Status"] = df.apply(hitung_status, axis=1)

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
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        tmin = st.number_input("Target Min", 0.0)
    with col_r2:
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
# 📋 TABEL DATA
# ======================================================

st.subheader("📋 Data Indikator")

st.dataframe(df, use_container_width=True)

# ======================================================
# ✏️ INLINE EDIT (EDIT LANGSUNG)
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
# 🔥 DASHBOARD UNTUK STATUS MERAH
# ======================================================

st.subheader("🚨 Indikator Status Merah")

df_merah = df[df["Status"] == "Merah"]

def mini_chart(row):
    st.markdown(
        f"<b>{row['Nama_Indikator']}</b>",
        unsafe_allow_html=True
    )

    target = float(row["Target"])
    real = float(row["Realisasi"])

    fig = go.Figure()
    fig.add_trace(go.Bar(x=[real], y=["Realisasi"], orientation="h",
                         marker=dict(color="#ff6b6b")))
    fig.add_trace(go.Bar(x=[target], y=["Target"], orientation="h",
                         marker=dict(color="#9aa0a6")))

    fig.update_layout(height=120, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def tampil_section(title, data):
    st.markdown(f"### {title}")
    if len(data) == 0:
        st.success("Tidak ada yang merah.")
        return
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for i, (_, r) in enumerate(data.iterrows()):
        with cols[i % 4]:
            mini_chart(r)

tampil_section("🔥 KPI Merah", df_merah[df_merah["Jenis"] == "KPI"])
tampil_section("⚠ KRI Merah", df_merah[df_merah["Jenis"] == "KRI"])
tampil_section("🔐 KCI Merah", df_merah[df_merah["Jenis"] == "KCI"])




