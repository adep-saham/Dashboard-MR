import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io

# ============================================================
#   STREAMLIT PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Dashboard KPI - KRI - KCI",
    layout="wide",
)

st.title("📊 Dashboard KPI, KRI, dan KCI")
st.caption("Data disimpan otomatis di Google Drive (CSV). Input lewat FORM, bukan tabel.")

# ============================================================
#   GOOGLE DRIVE CONFIG
# ============================================================
FILE_NAME = "kpi_kri_kci_data.csv"

@st.cache_resource
def get_drive_service():
    """Init Google Drive API via secrets."""
    creds_info = st.secrets["gcp_service_account"]
    folder_id = creds_info.get("drive_folder_id", None)
    scopes = ["https://www.googleapis.com/auth/drive.file"]

    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=scopes
    )
    service = build("drive", "v3", credentials=creds)
    return service, folder_id


# ============================================================
#   DATA INITIALIZER
# ============================================================
def init_data():
    return pd.DataFrame({
        "Jenis": ["KPI"],
        "Nama_Indikator": ["Contoh"],
        "Kategori": ["Keuangan"],
        "Unit": ["HO"],
        "Pemilik": ["Corporate Performance"],
        "Tanggal": ["2025-01-01"],
        "Target": [10],
        "Realisasi": [5],
        "Satuan": ["%"],
        "Keterangan": [""],
        "Arah_KRI": ["Higher is Better"],
        "Target_Min": [None],
        "Target_Max": [None],
    })

# ============================================================
#   DRIVE FUNCTIONS
# ============================================================
def drive_find_file(service, folder_id, name):
    query = f"name='{name}' and '{folder_id}' in parents and trashed=false"
    resp = service.files().list(q=query, fields="files(id, name)").execute()
    files = resp.get("files", [])
    return files[0] if files else None

def drive_download_df(service, folder_id, name):
    file_meta = drive_find_file(service, folder_id, name)
    if not file_meta:
        return None

    file_id = file_meta["id"]
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)
    return pd.read_csv(fh)

def drive_upload_df(service, folder_id, name, df):
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    fh = io.BytesIO(csv_bytes)
    media = MediaIoBaseUpload(fh, mimetype="text/csv", resumable=True)

    file_meta = drive_find_file(service, folder_id, name)

    if file_meta:
        return service.files().update(
            fileId=file_meta["id"],
            media_body=media
        ).execute()
    else:
        return service.files().create(
            body={"name": name, "parents": [folder_id], "mimeType": "text/csv"},
            media_body=media,
            fields="id"
        ).execute()


# ============================================================
#   LOGIKA KPI / KRI / KCI (Fleksibel)
# ============================================================
def hitung_status(row):
    jenis = str(row["Jenis"]).upper()
    real = float(row["Realisasi"])

    # KPI / KCI default: Real >= Target = Hijau
    if jenis in ["KPI", "KCI"]:
        target = float(row["Target"])
        return "Hijau" if real >= target else "Merah"

    # ------------- KRI FLEXIBLE -------------
    if jenis == "KRI":
        arah = row.get("Arah_KRI", "Higher is Better")

        # 1. HIGHER IS BETTER
        if arah == "Higher is Better":
            target = float(row["Target"])
            return "Hijau" if real >= target else "Merah"

        # 2. LOWER IS BETTER
        if arah == "Lower is Better":
            target = float(row["Target"])
            return "Hijau" if real <= target else "Merah"

        # 3. RANGE
        if arah == "Range":
            tmin = float(row["Target_Min"])
            tmax = float(row["Target_Max"])
            return "Hijau" if (real >= tmin and real <= tmax) else "Merah"

    return "N/A"


# ============================================================
#   LOAD DATA FROM GOOGLE DRIVE
# ============================================================
if "df" not in st.session_state:
    try:
        service, folder_id = get_drive_service()
        df_drive = drive_download_df(service, folder_id, FILE_NAME)
        if df_drive is not None:
            st.session_state.df = df_drive
            st.success("Data loaded from Google Drive.")
        else:
            st.session_state.df = init_data()
            st.info("Tidak ada file di Drive. Menggunakan data awal.")
    except Exception as e:
        st.session_state.df = init_data()
        st.error(f"Drive error: {e}")


df = st.session_state.df.copy()

# ============================================================
#   FORM INPUT (MENU)
# ============================================================
st.subheader("🧾 Tambah Indikator Baru")

with st.form("form_tambah"):

    colA, colB, colC = st.columns(3)

    # ============================
    # Kolom A
    # ============================
    with colA:
        jenis = st.selectbox("Jenis", ["KPI", "KRI", "KCI"])
        kategori = st.text_input("Kategori", "")
        unit = st.text_input("Unit", "")

    # ============================
    # Kolom B
    # ============================
    with colB:
        nama = st.text_input("Nama Indikator", "")
        pemilik = st.text_input("Pemilik", "")
        tanggal = st.date_input("Tanggal")

    # ============================
    # Kolom C
    # ============================
    with colC:
        target = st.number_input("Target", value=0.0)
        realisasi = st.number_input("Realisasi", value=0.0)
        satuan = st.text_input("Satuan", "")

    # ============================
    # KRI Flexible Logic
    # ============================
    arah_kri = st.selectbox(
        "Arah KRI (jika Jenis=KRI)",
        ["Higher is Better", "Lower is Better", "Range"]
    )

    tmin, tmax = None, None
    if arah_kri == "Range":
        tmin = st.number_input("Range Min", value=0.0)
        tmax = st.number_input("Range Max", value=0.0)

    keterangan = st.text_area("Keterangan", "")

    submitted = st.form_submit_button("➕ Tambah")

if submitted:
    new = {
        "Jenis": jenis,
        "Nama_Indikator": nama,
        "Kategori": kategori,
        "Unit": unit,
        "Pemilik": pemilik,
        "Tanggal": tanggal.strftime("%Y-%m-%d"),
        "Target": target,
        "Realisasi": realisasi,
        "Satuan": satuan,
        "Keterangan": keterangan,
        "Arah_KRI": arah_kri,
        "Target_Min": tmin,
        "Target_Max": tmax,
    }
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new])], ignore_index=True)
    st.success("Indikator berhasil ditambahkan.")
# ============================================================
#   DELETE SATU INDIKATOR & CLEAR SEMUA
# ============================================================
st.subheader("🗑️ Hapus Data")

col_del, col_clear = st.columns(2)

with col_del:
    if len(df) > 0:
        pilihan_delete = st.selectbox(
            "Pilih indikator untuk dihapus:",
            df["Nama_Indikator"] + " | " + df["Kategori"] + " | " + df["Unit"]
        )

        if st.button("❌ Hapus Indikator"):
            idx = df.index[
                (df["Nama_Indikator"] + " | " + df["Kategori"] + " | " + df["Unit"]) == pilihan_delete
            ][0]

            st.session_state.df = df.drop(idx).reset_index(drop=True)
            st.success(f"Berhasil menghapus: {pilihan_delete}. Jangan lupa klik Save ke Google Drive.")
    else:
        st.info("Tidak ada data untuk dihapus.")

with col_clear:
    if st.button("🗑️ Clear Semua Data"):
        st.session_state.df = df.iloc[0:0]
        st.warning("SELURUH data indikator telah dihapus! Klik Save ke Google Drive untuk menyimpan.")

df = st.session_state.df.copy()

# ============================================================
#   SAVE / RELOAD FROM GOOGLE DRIVE
# ============================================================
st.subheader("💾 Simpan / Reload Google Drive")

col_save, col_reload = st.columns(2)

with col_save:
    if st.button("📥 Save ke Google Drive"):
        try:
            service, folder_id = get_drive_service()
            drive_upload_df(service, folder_id, FILE_NAME, df)
            st.success("Data berhasil disimpan ke Google Drive.")
        except Exception as e:
            st.error(f"Gagal save ke Drive: {e}")

with col_reload:
    if st.button("🔄 Reload dari Google Drive"):
        try:
            service, folder_id = get_drive_service()
            df_drive = drive_download_df(service, folder_id, FILE_NAME)
            if df_drive is not None:
                st.session_state.df = df_drive
                st.success("Data berhasil di-load ulang dari Drive.")
            else:
                st.warning("File tidak ditemukan di Drive.")
        except Exception as e:
            st.error(f"Error reload Drive: {e}")

df = st.session_state.df.copy()

# ============================================================
#   TAMPILKAN TABEL DATA UTAMA
# ============================================================
st.subheader("📋 Data Indikator (Semua)")

if len(df) > 0:
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df["Status"] = df.apply(hitung_status, axis=1)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Belum ada data indikator.")

# ============================================================
#   FILTER FOR DASHBOARD
# ============================================================
st.sidebar.header("🔍 Filter Dashboard")

if len(df) > 0:
    jenis_opt = ["All"] + sorted(df["Jenis"].unique().tolist())
    unit_opt = ["All"] + sorted(df["Unit"].unique().tolist())
    kategori_opt = ["All"] + sorted(df["Kategori"].unique().tolist())

    f_jenis = st.sidebar.multiselect("Jenis", jenis_opt, default=["All"])
    f_unit = st.sidebar.multiselect("Unit", unit_opt, default=["All"])
    f_kat = st.sidebar.multiselect("Kategori", kategori_opt, default=["All"])

    min_date = df["Tanggal"].min()
    max_date = df["Tanggal"].max()

    f_date = st.sidebar.date_input("Tanggal", value=(min_date, max_date))
    start_d, end_d = pd.to_datetime(f_date[0]), pd.to_datetime(f_date[1])

    filtered = df.copy()

    if "All" not in f_jenis:
        filtered = filtered[filtered["Jenis"].isin(f_jenis)]
    if "All" not in f_unit:
        filtered = filtered[filtered["Unit"].isin(f_unit)]
    if "All" not in f_kat:
        filtered = filtered[filtered["Kategori"].isin(f_kat)]

    filtered = filtered[(filtered["Tanggal"] >= start_d) & (filtered["Tanggal"] <= end_d)]
else:
    filtered = df.copy()

# ============================================================
#   TABEL FILTERED
# ============================================================
st.subheader("📋 Tabel Indikator (Setelah Filter)")
st.dataframe(filtered, use_container_width=True)

# ============================================================
#   RINGKASAN KARTU
# ============================================================
st.subheader("📌 Ringkasan Status")

if len(filtered) > 0:
    total = len(filtered)
    hijau = (filtered["Status"] == "Hijau").sum()
    merah = (filtered["Status"] == "Merah").sum()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Total Indikator", total)
    with c2:
        st.metric("Hijau", hijau)
    with c3:
        st.metric("Merah", merah)
else:
    st.info("Tidak ada data dari filter.")

# ============================================================
#   GRAFIK STATUS PER JENIS
# ============================================================
st.subheader("📊 Grafik Status per Jenis")

if len(filtered) > 0:
    grp = filtered.groupby(["Jenis", "Status"]).size().reset_index(name="Jumlah")
    fig1 = px.bar(grp, x="Jenis", y="Jumlah", color="Status", text="Jumlah",
                  barmode="group", title="Status per Jenis")
    st.plotly_chart(fig1, use_container_width=True)

# ============================================================
#   TREN TARGET & REALISASI
# ============================================================
st.subheader("📈 Tren Realisasi vs Target")

if len(filtered) > 0:
    indikator_list = filtered["Nama_Indikator"].unique().tolist()

    pilih_ind = st.selectbox("Pilih indikator:", indikator_list)

    df_tren = filtered[filtered["Nama_Indikator"] == pilih_ind].sort_values("Tanggal")

    if len(df_tren) > 0:
        df_long = df_tren.melt(
            id_vars=["Tanggal"],
            value_vars=["Target", "Realisasi"],
            var_name="Jenis_Nilai",
            value_name="Nilai"
        )
        fig2 = px.line(df_long, x="Tanggal", y="Nilai", color="Jenis_Nilai",
                       markers=True, title=f"Tren - {pilih_ind}")
        st.plotly_chart(fig2, use_container_width=True)

# ============================================================
#   HEATMAP
# ============================================================
st.subheader("🗺️ Heatmap Status per Unit & Kategori")

if len(filtered) > 0:
    status_to_num = {"Hijau": 1, "Merah": 0, "N/A": 0.5}
    heat_df = filtered.copy()
    heat_df["Score"] = heat_df["Status"].map(status_to_num)

    pivot = heat_df.pivot_table(
        index="Unit", columns="Kategori", values="Score", aggfunc="mean"
    )

    fig3 = px.imshow(
        pivot,
        text_auto=True,
        aspect="auto",
        title="Heatmap Status"
    )

    st.plotly_chart(fig3, use_container_width=True)

# ============================================================
#   CATATAN
# ============================================================
st.markdown("""
---

### 🧠 Logika KRI Fleksibel:
- **Higher is Better** → Realisasi ≥ Target → Hijau  
- **Lower is Better** → Realisasi ≤ Target → Hijau  
- **Range (Min–Max)** → Realisasi di antara Range → Hijau  

### 💾 Penyimpanan:
Data disimpan ke Google Drive dalam file `kpi_kri_kci_data.csv`.

---
""")

