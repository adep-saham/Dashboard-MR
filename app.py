###############################################################
#  app.py – FINAL CLEAN VERSION (Year System + Range Logic FIX)
###############################################################

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import altair as alt


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

# =====================================================
# NORMALISASI REALISASI TERHADAP TARGET (DALAM %)
# =====================================================
df["Skor_Normal"] = (df["Realisasi"].astype(float) / df["Target"].astype(float)) * 100
df["Skor_Normal"] = df["Skor_Normal"].round(2)

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

# ================================
# TABEL NORMALISASI
# ================================

st.markdown("### 📊 Tabel Normalisasi Indikator")

if "Skor_Normal" in df.columns:

    # Tabel khusus normalisasi
    df_norm = df[[
        "Nama_Indikator",
        "Kategori",
        "Unit",
        "Target",
        "Realisasi",
        "Skor_Normal",
        "Status"
    ]].copy()

    # Format agar terlihat rapi
    df_norm["Target"] = df_norm["Target"].astype(float).round(2)
    df_norm["Realisasi"] = df_norm["Realisasi"].astype(float).round(2)
    df_norm["Skor_Normal"] = df_norm["Skor_Normal"].astype(float).round(2)

    # Warna berdasarkan status
    def color_status(row):
        if row["Status"] == "Hijau":
            return ["background-color: #d4edda; color: #155724"] * len(row)
        elif row["Status"] == "Merah":
            return ["background-color: #f8d7da; color: #721c24"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_norm.style.apply(color_status, axis=1)
                      .format({
                          "Target": "{:,.2f}",
                          "Realisasi": "{:,.2f}",
                          "Skor_Normal": "{:.2f}%"
                      }),
        use_container_width=True
    )

else:
    st.info("Normalisasi belum dihitung. Pastikan df['Skor_Normal'] sudah dibuat.")

# ============================================================
#  📈 Combo Chart Profesional — Target vs Realisasi
# ============================================================
st.markdown("## 📊 Bar Chart — Target vs Realisasi + % Capaian (Auto-Color)")

# Hanya kolom yang diperlukan
df_bar = df.copy()
df_bar["Skor_Normal"] = (df_bar["Realisasi"] / df_bar["Target"]) * 100
df_bar["Skor_Normal"] = df_bar["Skor_Normal"].round(2)

# Tentukan warna otomatis berdasarkan capaian
def get_color(score):
    if score >= 100:
        return "Hijau"
    elif score >= 90:
        return "Kuning"
    else:
        return "Merah"

df_bar["Warna"] = df_bar["Skor_Normal"].apply(get_color)

# Pilih indikator
indikator_list = df_bar["Nama_Indikator"].unique()
pilihan = st.multiselect("Pilih indikator:", indikator_list, default=indikator_list)

df_plot = df_bar[df_bar["Nama_Indikator"].isin(pilihan)]

if df_plot.empty:
    st.info("Tidak ada indikator dipilih.")
else:
    # Long dataframe (target & realisasi)
    df_long = df_plot.melt(
        id_vars=["Nama_Indikator", "Skor_Normal", "Warna"],
        value_vars=["Target", "Realisasi"],
        var_name="Jenis",
        value_name="Nilai"
    )

    # Mapping warna dinamis
    color_scale = alt.Scale(
        domain=["Hijau", "Kuning", "Merah", "Target"],
        range=["#27AE60", "#F1C40F", "#E74C3C", "#7F8C8D"]  # hijau, kuning, merah, abu gelap
    )

    # Tentukan warna: Target = abu gelap, Realisasi = warna otomatis
    df_long["Warna_Final"] = df_long.apply(
        lambda r: "Target" if r["Jenis"] == "Target" else r["Warna"],
        axis=1
    )

    chart = alt.Chart(df_long).mark_bar().encode(
        x=alt.X("Nama_Indikator:N", title="Indikator", sort="-y"),
        y=alt.Y("Nilai:Q", title="Nilai"),
        color=alt.Color("Warna_Final:N", scale=color_scale, title=""),
        tooltip=[
            "Nama_Indikator",
            "Jenis",
            "Nilai",
            alt.Tooltip("Skor_Normal", title="Capaian (%)"),
            alt.Tooltip("Warna_Final", title="Status Warna")
        ]
    ).properties(height=450)

    # Label % capaian di atas bar realisasi
    label = alt.Chart(df_plot).mark_text(
        align="center",
        baseline="bottom",
        dy=-5,
        fontSize=11,
        fontWeight="bold",
    ).encode(
        x="Nama_Indikator:N",
        y="Realisasi:Q",
        text=alt.Text("Skor_Normal:Q", format=".1f")
    )

    st.altair_chart(chart + label, use_container_width=True)






































