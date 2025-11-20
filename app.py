###############################################################
#  app.py – Final Deploy Version (CSV Export, No Excel Engine)
#  KPI / KRI / KCI Flexible • Corporate ANTAM Theme • No Errors
###############################################################

import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io

# ============================================================
#  THEME COLORS (Corporate ANTAM)
# ============================================================
COLOR_GREEN = "#C8F7C5"
COLOR_RED   = "#F7C5C5"
COLOR_GREY  = "#E0E0E0"
COLOR_GOLD  = "#C8A951"
COLOR_TEAL  = "#007E6D"

FILE_NAME = "kpi_kri_kci_data.csv"

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
#  GOOGLE DRIVE CONNECTION
# ============================================================
@st.cache_resource
def get_drive_service():
    creds_info = st.secrets["gcp_service_account"]
    folder_id = creds_info.get("drive_folder_id")

    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build("drive", "v3", credentials=creds)
    return service, folder_id

def drive_find(service, folder_id, name):
    query = f"name='{name}' and '{folder_id}' in parents and trashed=false"
    resp = service.files().list(q=query, fields="files(id)").execute()
    files = resp.get("files", [])
    return files[0] if files else None

def drive_load(service, folder_id, name):
    meta = drive_find(service, folder_id, name)
    if not meta:
        return None

    req = service.files().get_media(fileId=meta["id"])
    fh  = io.BytesIO()
    dl  = MediaIoBaseDownload(fh, req)

    done = False
    while not done:
        _, done = dl.next_chunk()

    fh.seek(0)
    return pd.read_csv(fh)

def drive_save(service, folder_id, name, df):
    data = df.to_csv(index=False).encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(data), "text/csv")

    meta = drive_find(service, folder_id, name)
    if meta:
        service.files().update(fileId=meta["id"], media_body=media).execute()
    else:
        service.files().create(
            body={
                "name": name,
                "parents": [folder_id],
                "mimeType": "text/csv"
            },
            media_body=media
        ).execute()


# ============================================================
#  INITIAL DATA
# ============================================================
def init_data():
    return pd.DataFrame(columns=[
        "Jenis", "Nama_Indikator", "Kategori", "Unit", "Pemilik", "Tanggal",
        "Target", "Realisasi", "Satuan", "Keterangan",
        "Arah", "Target_Min", "Target_Max"
    ])


# ============================================================
#  FLEXIBLE LOGIC FOR KPI / KRI / KCI
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
            tmin = float(row["Target_Min"])
            tmax = float(row["Target_Max"])
            return "Hijau" if tmin <= real <= tmax else "Merah"
        except:
            return "N/A"

    return "N/A"


# ============================================================
#  LOAD SESSION DATA
# ============================================================
if "df" not in st.session_state:
    try:
        service, folder_id = get_drive_service()
        df_drive = drive_load(service, folder_id, FILE_NAME)
        st.session_state.df = df_drive if df_drive is not None else init_data()
    except:
        st.session_state.df = init_data()

df = st.session_state.df.copy()


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
        "Higher is Better",
        "Lower is Better",
        "Range"
    ])

    tmin = tmax = None
    if arah == "Range":
        tmin = st.number_input("Range Min", 0.0)
        tmax = st.number_input("Range Max", 0.0)

    ket = st.text_area("Keterangan")

    submit = st.form_submit_button("Tambah")


if submit:
    new = pd.DataFrame([{
        "Jenis": jenis, "Nama_Indikator": nama, "Kategori": kategori,
        "Unit": unit, "Pemilik": pemilik, "Tanggal": tanggal.strftime("%Y-%m-%d"),
        "Target": target, "Realisasi": realisasi, "Satuan": satuan,
        "Keterangan": ket, "Arah": arah, "Target_Min": tmin, "Target_Max": tmax
    }])

    st.session_state.df = pd.concat([df, new], ignore_index=True)
    df = st.session_state.df.copy()
    st.success("Indikator berhasil ditambahkan!")


# ============================================================
#  DELETE & CLEAR
# ============================================================
st.subheader("🗑️ Hapus / Clear")

c1, c2 = st.columns(2)

with c1:
    if len(df) > 0:
        pilih = st.selectbox("Pilih indikator", df["Nama_Indikator"])
        if st.button("Hapus"):
            st.session_state.df = df[df["Nama_Indikator"] != pilih]
            df = st.session_state.df.copy()
            st.success("Data berhasil dihapus.")

with c2:
    if st.button("Clear Semua"):
        st.session_state.df = init_data()
        df = st.session_state.df.copy()
        st.warning("Semua data dihapus.")


# ============================================================
#  SAVE / RELOAD
# ============================================================
st.subheader("💾 Sinkronisasi")

c1, c2 = st.columns(2)

with c1:
    if st.button("Save ke Google Drive"):
        service, folder_id = get_drive_service()
        drive_save(service, folder_id, FILE_NAME, df)
        st.success("Data tersimpan ke Google Drive.")

with c2:
    if st.button("Reload dari Google Drive"):
        service, folder_id = get_drive_service()
        df_drive = drive_load(service, folder_id, FILE_NAME)
        st.session_state.df = df_drive if df_drive is not None else init_data()
        df = st.session_state.df.copy()
        st.success("Reload berhasil.")


# ============================================================
#  ADD STATUS COLUMN
# ============================================================
if len(df) > 0:
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df["Status"]  = df.apply(hitung_status, axis=1)


# ============================================================
#  SIDEBAR FILTER
# ============================================================
st.sidebar.header("🔍 Filter Dashboard")

if len(df) > 0:

    jenis_f = st.sidebar.multiselect("Jenis",
                 ["All"] + df["Jenis"].unique().tolist(), ["All"])

    unit_f  = st.sidebar.multiselect("Unit",
                 ["All"] + df["Unit"].unique().tolist(), ["All"])

    kat_f   = st.sidebar.multiselect("Kategori",
                 ["All"] + df["Kategori"].unique().tolist(), ["All"])

    min_d, max_d = df["Tanggal"].min(), df["Tanggal"].max()

    d_rng = st.sidebar.date_input("Tanggal", value=(min_d, max_d))

    f = df.copy()

    if "All" not in jenis_f:
        f = f[f["Jenis"].isin(jenis_f)]

    if "All" not in unit_f:
        f = f[f["Unit"].isin(unit_f)]

    if "All" not in kat_f:
        f = f[f["Kategori"].isin(kat_f)]

    f = f[(f["Tanggal"] >= pd.to_datetime(d_rng[0])) &
          (f["Tanggal"] <= pd.to_datetime(d_rng[1]))]

else:
    f = df.copy()


# ============================================================
#  SIDEBAR SUMMARY MINI
# ============================================================
st.sidebar.markdown("---")
st.sidebar.header("📊 Ringkasan")

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
#  TABLE (COLORED)
# ============================================================
st.subheader("📋 Data (Colored)")

def highlight(s):
    c = []
    for v in s["Status"]:
        if v == "Hijau":
            c.append(f"background-color:{COLOR_GREEN}")
        elif v == "Merah":
            c.append(f"background-color:{COLOR_RED}")
        else:
            c.append(f"background-color:{COLOR_GREY}")
    return c

st.subheader("📋 Data (Colored)")

if len(df) > 0:
    styled = df.style.apply(highlight, axis=1)
    st.markdown(styled.to_html(), unsafe_allow_html=True)
else:
    st.info("Belum ada data.")


# ============================================================
#  EXPORT CSV
# ============================================================
st.subheader("📤 Export CSV")

if len(f) > 0:
    csv_data = f.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name="kpi_kri_kci_export.csv",
        mime="text/csv"
    )
else:
    st.info("Tidak ada data untuk diexport.")


# ============================================================
#  CHARTS & HEATMAP
# ============================================================
if len(f) > 0:

    st.subheader("📊 Status per Jenis")
    g = f.groupby(["Jenis", "Status"]).size().reset_index(name="Jumlah")

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
    pick = st.selectbox("Pilih indikator", f["Nama_Indikator"].unique())

    d2 = f[f["Nama_Indikator"] == pick].sort_values("Tanggal")
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
        color="Jenis_Nilai",
        markers=True,
        color_discrete_map={"Target": COLOR_GOLD, "Realisasi": COLOR_TEAL}
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🗺️ Heatmap Unit vs Kategori")
    score = {"Hijau": 1, "Merah": 0, "N/A": 0.5}

    f["Score"] = f["Status"].map(score)

    pv = f.pivot_table(
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

