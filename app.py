import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io

# -------------------- CONFIG HALAMAN --------------------
st.set_page_config(
    page_title="Dashboard KPI - KRI - KCI",
    layout="wide",
)

st.title("📊 Dashboard KPI, KRI, dan KCI")
st.caption("Data indikator tersimpan sebagai CSV di Google Drive melalui Service Account.")

# -------------------- KONFIGURASI GOOGLE DRIVE --------------------
FILE_NAME = "kpi_kri_kci_data.csv"

@st.cache_resource
def get_drive_service():
    """
    Inisialisasi Drive API dari st.secrets["gcp_service_account"].
    Pastikan secrets sudah diisi di Streamlit Cloud.
    """
    creds_info = st.secrets["gcp_service_account"]
    folder_id = creds_info.get("drive_folder_id", None)
    if folder_id is None:
        raise RuntimeError("drive_folder_id belum di-set di secrets.")
    scopes = ["https://www.googleapis.com/auth/drive.file"]
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=scopes
    )
    service = build("drive", "v3", credentials=creds)
    return service, folder_id

def init_data():
    """Data awal kalau belum ada file di Drive."""
    data = {
        "Jenis": ["KPI", "KRI", "KCI"],
        "Nama_Indikator": [
            "ROIC",
            "Kecelakaan Kerja",
            "% SOP Kritikal Di-review",
        ],
        "Kategori": ["Keuangan", "HSSE", "Kepatuhan"],
        "Unit": ["HO", "UBPP", "HO"],
        "Pemilik": [
            "Corporate Performance",
            "HSSE UBPP",
            "GCG & Compliance",
        ],
        "Tanggal": [
            "2025-09-30",
            "2025-09-30",
            "2025-09-30",
        ],
        "Target": [12.0, 2.0, 90.0],
        "Realisasi": [13.5, 3.0, 80.0],
        "Satuan": ["%", "kasus", "%"],
        "Keterangan": ["", "", ""],
    }
    return pd.DataFrame(data)

def drive_find_file(service, folder_id, name):
    """Cari file berdasarkan nama di folder Drive."""
    query = f"name='{name}' and '{folder_id}' in parents and trashed=false"
    resp = service.files().list(q=query, fields="files(id, name)").execute()
    files = resp.get("files", [])
    return files[0] if files else None

def drive_download_df(service, folder_id, name):
    """Download CSV dari Drive jadi DataFrame. Kalau tidak ada, return None."""
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
    df = pd.read_csv(fh)
    return df

def drive_upload_df(service, folder_id, name, df):
    """Upload / update DataFrame ke Drive sebagai CSV."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    fh = io.BytesIO(csv_bytes)
    media = MediaIoBaseUpload(fh, mimetype="text/csv", resumable=True)

    file_meta = drive_find_file(service, folder_id, name)

    if file_meta:
        # Update file
        file_id = file_meta["id"]
        updated = service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        return updated.get("id")
    else:
        # Create file baru
        file_metadata = {
            "name": name,
            "parents": [folder_id],
            "mimeType": "text/csv"
        }
        created = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        return created.get("id")

# -------------------- LOGIKA KPI/KRI/KCI --------------------
def hitung_status(row):
    """Hitung status Hijau/Merah/N/A berdasarkan jenis indikator."""
    try:
        target = float(row["Target"])
        real = float(row["Realisasi"])
    except (TypeError, ValueError):
        return "N/A"

    jenis = str(row["Jenis"]).upper()

    if jenis in ["KPI", "KCI"]:
        # KPI/KCI: makin tinggi makin baik
        return "Hijau" if real >= target else "Merah"
    elif jenis == "KRI":
        # KRI: makin rendah makin baik
        return "Hijau" if real <= target else "Merah"
    else:
        return "N/A"

def safe_pct(part, whole):
    return 0 if whole == 0 else round(part / whole * 100, 1)

# -------------------- LOAD DATA DARI DRIVE (PERTAMA KALI) --------------------
if "df_indikator" not in st.session_state:
    try:
        drive_service, DRIVE_FOLDER_ID = get_drive_service()
        df_drive = drive_download_df(drive_service, DRIVE_FOLDER_ID, FILE_NAME)
        if df_drive is not None:
            st.session_state.df_indikator = df_drive
            st.success("✅ Data indikator di-load dari Google Drive.")
        else:
            st.session_state.df_indikator = init_data()
            st.info("ℹ️ Belum ada file di Google Drive. Menggunakan data contoh awal.")
    except Exception as e:
        st.session_state.df_indikator = init_data()
        st.error(f"Gagal akses Google Drive, menggunakan data contoh. Detail: {e}")

# -------------------- INFO STRUKTUR DATA DI SIDEBAR --------------------
st.sidebar.header("⚙️ Struktur Data")

st.sidebar.markdown(
    """
**Kolom yang digunakan:**

- `Jenis` → KPI / KRI / KCI  
- `Nama_Indikator`  
- `Kategori` (Keuangan, HSSE, Kepatuhan, Operasi, dll.)  
- `Unit` (HO, UBPP, UBPN, dsb.)  
- `Pemilik` (PIC indikator)  
- `Tanggal` → format YYYY-MM-DD  
- `Target` → angka  
- `Realisasi` → angka  
- `Satuan` → %, kasus, unit, dll.  
- `Keterangan` → catatan bebas
"""
)

# -------------------- FORM INPUT / MENU TAMBAH DATA --------------------
st.subheader("🧾 Tambah Indikator (Form)")

with st.form("form_tambah_indikator"):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        jenis = st.selectbox("Jenis Indikator", ["KPI", "KRI", "KCI"])
        kategori = st.text_input("Kategori", "Keuangan")
        unit = st.text_input("Unit", "HO")
    with col_b:
        nama = st.text_input("Nama Indikator", "ROIC")
        pemilik = st.text_input("Pemilik / PIC", "Corporate Performance")
        tanggal = st.date_input("Tanggal")
    with col_c:
        target = st.number_input("Target", value=0.0, step=0.1)
        realisasi = st.number_input("Realisasi", value=0.0, step=0.1)
        satuan = st.text_input("Satuan", "%")

    keterangan = st.text_area("Keterangan (opsional)", "")

    submitted = st.form_submit_button("➕ Tambah ke Data")

if submitted:
    # Tambah baris baru ke DataFrame di session_state
    new_row = {
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
    }
    st.session_state.df_indikator = pd.concat(
        [st.session_state.df_indikator, pd.DataFrame([new_row])],
        ignore_index=True
    )
    st.success(f"Indikator '{nama}' berhasil ditambahkan.")

df = st.session_state.df_indikator.copy()

# -------------------- TOMBOL SIMPAN / RELOAD DARI DRIVE --------------------
col_save, col_reload = st.columns(2)

with col_save:
    if st.button("💾 Save ke Google Drive"):
        try:
            drive_service, DRIVE_FOLDER_ID = get_drive_service()
            drive_upload_df(drive_service, DRIVE_FOLDER_ID, FILE_NAME, df)
            st.success("✅ Data berhasil disimpan / di-update di Google Drive.")
        except Exception as e:
            st.error(f"Gagal menyimpan ke Google Drive: {e}")

with col_reload:
    if st.button("⟳ Reload dari Google Drive"):
        try:
            drive_service, DRIVE_FOLDER_ID = get_drive_service()
            df_drive = drive_download_df(drive_service, DRIVE_FOLDER_ID, FILE_NAME)
            if df_drive is not None:
                st.session_state.df_indikator = df_drive
                df = df_drive.copy()
                st.success("✅ Data berhasil di-load ulang dari Google Drive.")
            else:
                st.warning("File di Google Drive belum ada.")
        except Exception as e:
            st.error(f"Gagal load dari Google Drive: {e}")

# -------------------- PRE-PROSES DATA UNTUK DASHBOARD --------------------
if df.empty:
    st.warning("Belum ada data indikator. Tambahkan minimal satu baris lewat form di atas.")
    st.stop()

# Nama kolom jadi konsisten (tanpa spasi)
df.columns = [c.strip().replace(" ", "_") for c in df.columns]

required_cols = ["Jenis", "Nama_Indikator", "Kategori", "Unit",
                 "Pemilik", "Tanggal", "Target", "Realisasi"]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Kolom wajib berikut belum ada di data: {', '.join(missing)}")
    st.stop()

df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
df["Status"] = df.apply(hitung_status, axis=1).fillna("N/A")

# -------------------- TAMPILKAN DATA EXISTING --------------------
st.subheader("📋 Data Indikator (Semua)")

st.dataframe(
    df.sort_values(["Jenis", "Kategori", "Unit", "Nama_Indikator"]),
    use_container_width=True,
)

# -------------------- FUNGSI DELETE & CLEAR --------------------

st.subheader("🧹 Hapus / Bersihkan Data")

col_del, col_clear = st.columns(2)

with col_del:
    # Pilih baris untuk dihapus
    if len(df) > 0:
        row_to_delete = st.selectbox(
            "Pilih indikator yang ingin dihapus:",
            df["Nama_Indikator"] + " | " + df["Kategori"] + " | " + df["Unit"]
        )

        if st.button("❌ Hapus Indikator Ini"):
            # Cari index berdasarkan pilihan
            idx = df.index[
                (df["Nama_Indikator"] + " | " + df["Kategori"] + " | " + df["Unit"]) == row_to_delete
            ][0]

            st.session_state.df_indikator = df.drop(idx).reset_index(drop=True)
            st.success(f"Indikator '{row_to_delete}' berhasil dihapus. Klik Save ke Google Drive untuk menyimpan.")
    else:
        st.info("Tidak ada data untuk dihapus.")

with col_clear:
    if st.button("🗑️ Clear Semua Data"):
        st.session_state.df_indikator = df.iloc[0:0]  # membuat dataframe kosong
        st.warning("Semua indikator telah DIHAPUS. Klik Save ke Google Drive untuk menyimpan.")

# -------------------- FILTER DI SIDEBAR UNTUK DASHBOARD --------------------
st.sidebar.header("🔍 Filter Dashboard")

jenis_options = ["All"] + sorted(df["Jenis"].dropna().unique().tolist())
unit_options = ["All"] + sorted(df["Unit"].dropna().unique().tolist())
kategori_options = ["All"] + sorted(df["Kategori"].dropna().unique().tolist())

selected_jenis = st.sidebar.multiselect(
    "Jenis Indikator",
    options=jenis_options,
    default=["All"]
)

selected_unit = st.sidebar.multiselect(
    "Unit",
    options=unit_options,
    default=["All"]
)

selected_kat = st.sidebar.multiselect(
    "Kategori",
    options=kategori_options,
    default=["All"]
)

min_date = df["Tanggal"].min()
max_date = df["Tanggal"].max()
start_date, end_date = st.sidebar.date_input(
    "Periode Tanggal",
    value=(min_date, max_date)
)

filtered = df.copy()

if "All" not in selected_jenis:
    filtered = filtered[filtered["Jenis"].isin(selected_jenis)]

if "All" not in selected_unit:
    filtered = filtered[filtered["Unit"].isin(selected_unit)]

if "All" not in selected_kat:
    filtered = filtered[filtered["Kategori"].isin(selected_kat)]

filtered = filtered[
    (filtered["Tanggal"] >= pd.to_datetime(start_date)) &
    (filtered["Tanggal"] <= pd.to_datetime(end_date))
]

# -------------------- RINGKASAN --------------------
st.subheader("📌 Ringkasan Utama (Setelah Filter)")

total_ind = len(filtered)
total_hijau = (filtered["Status"] == "Hijau").sum()
total_merah = (filtered["Status"] == "Merah").sum()

pct_hijau = safe_pct(total_hijau, total_ind)
pct_merah = safe_pct(total_merah, total_ind)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total Indikator", total_ind)

with c2:
    st.metric("Indikator Hijau", f"{total_hijau} ({pct_hijau}%)")

with c3:
    st.metric("Indikator Merah", f"{total_merah} ({pct_merah}%)")

# -------------------- TABEL DETAIL FILTERED --------------------
st.subheader("📋 Tabel Indikator (Setelah Filter)")

st.dataframe(
    filtered.sort_values(["Jenis", "Kategori", "Unit", "Nama_Indikator"]),
    use_container_width=True,
)

# -------------------- GRAFIK STATUS PER JENIS --------------------
st.subheader("📊 Distribusi Status per Jenis Indikator")

if len(filtered) > 0:
    status_agg = (
        filtered.groupby(["Jenis", "Status"])
        .size()
        .reset_index(name="Jumlah")
    )

    fig1 = px.bar(
        status_agg,
        x="Jenis",
        y="Jumlah",
        color="Status",
        barmode="group",
        text="Jumlah",
        title="Jumlah Indikator Hijau/Merah per Jenis",
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(xaxis_title="", yaxis_title="Jumlah Indikator")
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Tidak ada data sesuai filter.")

# -------------------- TREN TARGET vs REALISASI --------------------
st.subheader("📈 Tren Realisasi vs Target")

if len(filtered) > 0:
    indikator_pilihan = st.selectbox(
        "Pilih indikator",
        options=sorted(filtered["Nama_Indikator"].unique().tolist())
    )
else:
    indikator_pilihan = None

if indikator_pilihan:
    df_tren = filtered[filtered["Nama_Indikator"] == indikator_pilihan].copy()
    df_tren = df_tren.sort_values("Tanggal")

    if not df_tren.empty:
        df_long = df_tren.melt(
            id_vars=["Tanggal"],
            value_vars=["Target", "Realisasi"],
            var_name="Jenis_Nilai",
            value_name="Nilai"
        )

        fig2 = px.line(
            df_long,
            x="Tanggal",
            y="Nilai",
            color="Jenis_Nilai",
            markers=True,
            title=f"Tren Target vs Realisasi - {indikator_pilihan}",
        )
        st.plotly_chart(fig2, use_container_width=True)

# -------------------- HEATMAP UNIT vs KATEGORI --------------------
st.subheader("🗺️ Heatmap Status per Unit & Kategori")

if len(filtered) > 0:
    status_map = {"Hijau": 1, "Merah": 0, "N/A": 0.5}
    heat_df = filtered.copy()
    heat_df["Skor_Status"] = heat_df["Status"].map(status_map).fillna(0.5)

    pivot = heat_df.pivot_table(
        index="Unit",
        columns="Kategori",
        values="Skor_Status",
        aggfunc="mean"
    )

    fig3 = px.imshow(
        pivot,
        labels=dict(x="Kategori", y="Unit", color="Skor Status (0=Merah; 1=Hijau)"),
        aspect="auto",
        title="Heatmap Rata-rata Status per Unit & Kategori"
    )

    st.plotly_chart(fig3, use_container_width=True)

# -------------------- CATATAN --------------------
st.markdown(
    """
---
ℹ️ **Logika warna:**
- **KPI & KCI** → Hijau kalau `Realisasi ≥ Target`  
- **KRI** → Hijau kalau `Realisasi ≤ Target`  

Data disimpan sebagai `kpi_kri_kci_data.csv` di folder Google Drive
yang ID-nya diisi di `drive_folder_id` pada secrets Streamlit Cloud.
"""
)


