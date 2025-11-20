
# app.py - Corporate ANTAM Theme (Gold–Teal) Full Version
# KPI / KRI / KCI Flexible + Export Excel + Sidebar Summary + Styling

import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from openpyxl import Workbook
from openpyxl.styles import PatternFill
import io

# ---------------------------------------------------
# THEME COLORS (ANTAM Corporate)
# ---------------------------------------------------
COLOR_GREEN = "#C8F7C5"
COLOR_RED = "#F7C5C5"
COLOR_GREY = "#E0E0E0"
COLOR_GOLD = "#C8A951"
COLOR_TEAL = "#007E6D"

FILE_NAME = "kpi_kri_kci_data.csv"

# ---------------------------------------------------
# STREAMLIT CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Dashboard KPI/KRI/KCI", layout="wide")
st.markdown(
    f'''
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
    ''',
    unsafe_allow_html=True
)

st.markdown(f"<h1 class='main-title'>📊 Dashboard KPI / KRI / KCI</h1>", unsafe_allow_html=True)

# ---------------------------------------------------
# GOOGLE DRIVE CONNECTION
# ---------------------------------------------------
@st.cache_resource
def get_drive_service():
    creds_info = st.secrets["gcp_service_account"]
    folder_id = creds_info.get("drive_folder_id")
    scopes = ["https://www.googleapis.com/auth/drive.file"]
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
    return build("drive","v3",credentials=creds), folder_id

def drive_find_file(service,folder_id,name):
    q=f"name='{name}' and '{folder_id}' in parents and trashed=false"
    r=service.files().list(q=q,fields="files(id)").execute()
    f=r.get("files",[])
    return f[0] if f else None

def drive_download_df(service,folder_id,name):
    meta=drive_find_file(service,folder_id,name)
    if not meta: return None
    req=service.files().get_media(fileId=meta["id"])
    fh=io.BytesIO()
    dl=MediaIoBaseDownload(fh,req)
    done=False
    while not done:
        _,done=dl.next_chunk()
    fh.seek(0)
    return pd.read_csv(fh)

def drive_upload_df(service,folder_id,name,df):
    data=df.to_csv(index=False).encode()
    media=MediaIoBaseUpload(io.BytesIO(data),"text/csv")
    meta=drive_find_file(service,folder_id,name)
    if meta:
        service.files().update(fileId=meta["id"],media_body=media).execute()
    else:
        body={"name":name,"parents":[folder_id],"mimeType":"text/csv"}
        service.files().create(body=body,media_body=media).execute()

# ---------------------------------------------------
# INITIAL DATA
# ---------------------------------------------------
def init_data():
    return pd.DataFrame(columns=[
        "Jenis","Nama_Indikator","Kategori","Unit","Pemilik","Tanggal",
        "Target","Realisasi","Satuan","Keterangan","Arah","Target_Min","Target_Max"
    ])

# ---------------------------------------------------
# LOGIC FLEXIBLE
# ---------------------------------------------------
def hitung_status(row):
    arah=row.get("Arah","Higher is Better")
    try: real=float(row["Realisasi"])
    except: return "N/A"

    if arah=="Higher is Better":
        return "Hijau" if real>=float(row["Target"]) else "Merah"

    if arah=="Lower is Better":
        return "Hijau" if real<=float(row["Target"]) else "Merah"

    if arah=="Range":
        try:
            mn=float(row["Target_Min"]); mx=float(row["Target_Max"])
            return "Hijau" if mn<=real<=mx else "Merah"
        except: return "N/A"

    return "N/A"

# ---------------------------------------------------
# EXPORT EXCEL
# ---------------------------------------------------
def export_excel(df):
    import pandas as pd
    import xlsxwriter
    from io import BytesIO

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dashboard")
        workbook = writer.book
        worksheet = writer.sheets["Dashboard"]

        # Define formats
        fmt_hijau = workbook.add_format({"bg_color": "#C8F7C5"})
        fmt_merah = workbook.add_format({"bg_color": "#F7C5C5"})
        fmt_grey  = workbook.add_format({"bg_color": "#E0E0E0"})

        # Apply color row by row
        for row_idx, status in enumerate(df["Status"], start=1):
            if status == "Hijau":
                fmt = fmt_hijau
            elif status == "Merah":
                fmt = fmt_merah
            else:
                fmt = fmt_grey

            worksheet.set_row(row_idx, None, fmt)

    output.seek(0)
    return output

# ---------------------------------------------------
# LOAD SESSION DATA
# ---------------------------------------------------
if "df" not in st.session_state:
    try:
        service, folder = get_drive_service()
        df_drive = drive_download_df(service, folder, FILE_NAME)
        st.session_state.df = df_drive if df_drive is not None else init_data()
    except:
        st.session_state.df = init_data()

df = st.session_state.df.copy()

# ---------------------------------------------------
# INPUT FORM
# ---------------------------------------------------
st.subheader("🧾 Input Indikator Baru")

with st.form("form"):
    c1,c2,c3=st.columns(3)
    with c1:
        jenis=st.selectbox("Jenis",["KPI","KRI","KCI"])
        kategori=st.text_input("Kategori")
        unit=st.text_input("Unit")
    with c2:
        nama=st.text_input("Nama Indikator")
        pemilik=st.text_input("Pemilik")
        tanggal=st.date_input("Tanggal")
    with c3:
        target=st.number_input("Target",0.0)
        real=st.number_input("Realisasi",0.0)
        satuan=st.text_input("Satuan")

    arah=st.selectbox("Arah Penilaian",[
        "Higher is Better","Lower is Better","Range"
    ])
    tmin=tmax=None
    if arah=="Range":
        tmin=st.number_input("Range Min",0.0)
        tmax=st.number_input("Range Max",0.0)

    ket=st.text_area("Keterangan")
    submit=st.form_submit_button("Tambah")

if submit:
    new = pd.DataFrame([{
        "Jenis":jenis,"Nama_Indikator":nama,"Kategori":kategori,"Unit":unit,
        "Pemilik":pemilik,"Tanggal":tanggal.strftime("%Y-%m-%d"),
        "Target":target,"Realisasi":real,"Satuan":satuan,"Keterangan":ket,
        "Arah":arah,"Target_Min":tmin,"Target_Max":tmax
    }])
    st.session_state.df=pd.concat([st.session_state.df,new],ignore_index=True)
    df=st.session_state.df.copy()
    st.success("Indikator ditambahkan!")

# ---------------------------------------------------
# DELETE / CLEAR
# ---------------------------------------------------
st.subheader("🗑️ Hapus / Clear Data")
c1,c2=st.columns(2)
with c1:
    if len(df)>0:
        pilih=st.selectbox("Pilih indikator",df["Nama_Indikator"])
        if st.button("Hapus"):
            st.session_state.df=df[df["Nama_Indikator"]!=pilih]
            df=st.session_state.df.copy()
            st.success("Dihapus")
with c2:
    if st.button("Clear Semua"):
        st.session_state.df=init_data()
        df=st.session_state.df.copy()
        st.warning("Semua data dihapus")

# ---------------------------------------------------
# SAVE / RELOAD
# ---------------------------------------------------
st.subheader("💾 Sinkronisasi Drive")
cs,cr=st.columns(2)
with cs:
    if st.button("Save ke Drive"):
        service,folder=get_drive_service()
        drive_upload_df(service,folder,FILE_NAME,df)
        st.success("Tersimpan")
with cr:
    if st.button("Reload dari Drive"):
        service,folder=get_drive_service()
        df_drive=drive_download_df(service,folder,FILE_NAME)
        st.session_state.df=df_drive if df_drive is not None else init_data()
        df=st.session_state.df.copy()
        st.success("Reloaded")

# ---------------------------------------------------
# ADD STATUS
# ---------------------------------------------------
if len(df)>0:
    df["Tanggal"]=pd.to_datetime(df["Tanggal"],errors="coerce")
    df["Status"]=df.apply(hitung_status,axis=1)

# ---------------------------------------------------
# SIDEBAR FILTER
# ---------------------------------------------------
st.sidebar.header("🔍 Filter Dashboard")

if len(df)>0:
    jenis_f=st.sidebar.multiselect("Jenis",
        ["All"]+df["Jenis"].unique().tolist(),["All"])
    unit_f=st.sidebar.multiselect("Unit",
        ["All"]+df["Unit"].unique().tolist(),["All"])
    kat_f=st.sidebar.multiselect("Kategori",
        ["All"]+df["Kategori"].unique().tolist(),["All"])
    min_d,max_d=df["Tanggal"].min(),df["Tanggal"].max()
    d_rng=st.sidebar.date_input("Tanggal",value=(min_d,max_d))

    f=df.copy()
    if "All" not in jenis_f: f=f[f["Jenis"].isin(jenis_f)]
    if "All" not in unit_f: f=f[f["Unit"].isin(unit_f)]
    if "All" not in kat_f: f=f[f["Kategori"].isin(kat_f)]
    f=f[(f["Tanggal"]>=pd.to_datetime(d_rng[0]))&(f["Tanggal"]<=pd.to_datetime(d_rng[1]))]
else:
    f=df.copy()

# ---------------------------------------------------
# SIDEBAR SUMMARY MINI
# ---------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📊 Ringkasan")
if len(df)>0:
    total=len(df)
    hijau=(df["Status"]=="Hijau").sum()
    merah=(df["Status"]=="Merah").sum()
    na=(df["Status"]=="N/A").sum()
    kpi=(df["Jenis"]=="KPI").sum()
    kri=(df["Jenis"]=="KRI").sum()
    kci=(df["Jenis"]=="KCI").sum()

    pct=hijau/total*100 if total>0 else 0

    st.sidebar.metric("Total",total)
    st.sidebar.metric("Hijau",hijau)
    st.sidebar.metric("Merah",merah)
    st.sidebar.metric("N/A",na)
    st.sidebar.markdown("---")
    st.sidebar.metric("KPI",kpi)
    st.sidebar.metric("KRI",kri)
    st.sidebar.metric("KCI",kci)
    st.sidebar.markdown("---")
    st.sidebar.metric("Capaian Hijau",f"{pct:.1f}%")
else:
    st.sidebar.info("Belum ada data")

# ---------------------------------------------------
# TABLE COLORED
# ---------------------------------------------------
st.subheader("📋 Data (Colored)")

def highlight(s):
    c=[]
    for v in s["Status"]:
        if v=="Hijau": c.append(f"background-color:{COLOR_GREEN}")
        elif v=="Merah": c.append(f"background-color:{COLOR_RED}")
        else: c.append(f"background-color:{COLOR_GREY}")
    return c

if len(df)>0:
    styled=df.style.apply(highlight,axis=1)
    st.table(styled)
else:
    st.info("Belum ada data")

# ---------------------------------------------------
# EXPORT BUTTON
# ---------------------------------------------------
st.subheader("📤 Export Excel")
if len(f)>0:
    excel_file=export_excel(f)
    st.download_button(
        label="📥 Download Excel",
        data=excel_file,
        file_name="kpi_kri_kci_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Tidak ada data untuk diexport")

# ---------------------------------------------------
# CHARTS
# ---------------------------------------------------
if len(f)>0:
    st.subheader("📊 Status per Jenis")
    g=f.groupby(["Jenis","Status"]).size().reset_index(name="Jumlah")
    st.plotly_chart(px.bar(g,x="Jenis",y="Jumlah",color="Status",
        text="Jumlah",color_discrete_map={
            "Hijau":COLOR_TEAL,"Merah":COLOR_RED}),use_container_width=True)

    st.subheader("📈 Tren Per Indikator")
    ind=st.selectbox("Pilih indikator",f["Nama_Indikator"].unique())
    d2=f[f["Nama_Indikator"]==ind].sort_values("Tanggal")
    long=d2.melt(id_vars=["Tanggal"],value_vars=["Target","Realisasi"],
        var_name="Jenis_Nilai",value_name="Nilai")
    st.plotly_chart(px.line(long,x="Tanggal",y="Nilai",color="Jenis_Nilai",
        markers=True,color_discrete_map={
            "Target":COLOR_GOLD,"Realisasi":COLOR_TEAL}),use_container_width=True)

    st.subheader("🗺️ Heatmap Unit vs Kategori")
    stat_map={"Hijau":1,"Merah":0,"N/A":0.5}
    f["Score"]=f["Status"].map(stat_map)
    pv=f.pivot_table(index="Unit",columns="Kategori",values="Score",aggfunc="mean")
    st.plotly_chart(px.imshow(pv,text_auto=True,aspect="auto",
        color_continuous_scale=[COLOR_RED,COLOR_GREY,COLOR_GREEN]),
        use_container_width=True)


