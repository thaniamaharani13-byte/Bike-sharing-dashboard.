"""Dashboard Bike Sharing berdasarkan notebook analisis data Dicoding."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")

DATA_DIR = Path(__file__).resolve().parent


@st.cache_data
def load_data():
    harian = pd.read_csv(DATA_DIR / "day_data.csv", parse_dates=["dteday"])
    per_jam = pd.read_csv(DATA_DIR / "main_data.csv", parse_dates=["dteday"])
    harian["nama_musim"] = harian["season"].map({
        1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"
    })
    harian["kondisi_cuaca"] = harian["weathersit"].map({
        1: "Cerah", 2: "Berkabut/Berawan",
        3: "Hujan/Salju Ringan", 4: "Cuaca Buruk"
    })
    return harian, per_jam


day_df, hour_df = load_data()
awal = day_df["dteday"].min().date()
akhir = day_df["dteday"].max().date()

st.title("🚲 Bike Sharing Dashboard")
st.write(
    "Analisis penyewaan sepeda berdasarkan jam dan jenis hari, "
    "serta rata-rata penyewaan harian menurut musim dan cuaca (2011–2012)."
)

st.sidebar.header("Filter Data")
pilihan_tanggal = st.sidebar.date_input(
    "Rentang tanggal", value=(awal, akhir), min_value=awal, max_value=akhir
)
jenis_hari = st.sidebar.selectbox(
    "Jenis hari", ["Semua", "Hari Kerja", "Hari Nonkerja"]
)

if not isinstance(pilihan_tanggal, (tuple, list)) or len(pilihan_tanggal) != 2:
    st.info("Pilih tanggal awal dan tanggal akhir untuk menampilkan dashboard.")
    st.stop()

tgl_awal, tgl_akhir = pilihan_tanggal
if tgl_awal > tgl_akhir:
    st.warning("Tanggal awal tidak boleh melebihi tanggal akhir.")
    st.stop()

mask_harian = day_df["dteday"].dt.date.between(tgl_awal, tgl_akhir)
mask_per_jam = hour_df["dteday"].dt.date.between(tgl_awal, tgl_akhir)
if jenis_hari != "Semua":
    target = 1 if jenis_hari == "Hari Kerja" else 0
    mask_harian &= day_df["workingday"] == target
    mask_per_jam &= hour_df["workingday"] == target

harian = day_df.loc[mask_harian].copy()
per_jam = hour_df.loc[mask_per_jam].copy()

if harian.empty or per_jam.empty:
    st.warning("Belum ada data untuk kombinasi filter ini. Coba rentang tanggal lain.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Total Penyewaan", f"{harian['cnt'].sum():,}")
col2.metric("Rata-rata per Hari", f"{harian['cnt'].mean():,.0f}")
col3.metric("Jumlah Hari", f"{len(harian):,}")

st.divider()
st.subheader("Pertanyaan 1 — Pola Penyewaan per Jam")

rata_jam = (per_jam.groupby(["workingday", "hr"])["cnt"]
            .mean().reset_index())

fig_jam, ax_jam = plt.subplots(figsize=(11, 4.5))
for kerja, nama in [(0, "Hari Nonkerja"), (1, "Hari Kerja")]:
    data_garis = rata_jam[rata_jam["workingday"] == kerja]
    if not data_garis.empty:
        ax_jam.plot(data_garis["hr"], data_garis["cnt"], marker="o", label=nama)
ax_jam.set_title("Rata-rata Penyewaan Sepeda Berdasarkan Jam dan Jenis Hari")
ax_jam.set_xlabel("Jam")
ax_jam.set_ylabel("Rata-rata Penyewaan per Jam")
ax_jam.set_xticks(range(24))
ax_jam.set_ylim(bottom=0)
ax_jam.grid(alpha=0.25)
ax_jam.legend()
fig_jam.tight_layout()
st.pyplot(fig_jam)
plt.close(fig_jam)

puncak = rata_jam.loc[rata_jam.groupby("workingday")["cnt"].idxmax()]
for _, baris in puncak.iterrows():
    nama = "Hari Kerja" if baris["workingday"] == 1 else "Hari Nonkerja"
    st.write(f"**{nama}:** jam puncak pukul {int(baris['hr']):02d}.00, "
             f"rata-rata {baris['cnt']:,.2f} penyewaan per jam.")

st.divider()
st.subheader("Pertanyaan 2 — Penyewaan Berdasarkan Musim dan Cuaca")

rata_musim = (harian.groupby("nama_musim")["cnt"]
              .mean().sort_values(ascending=False))
rata_cuaca = (harian.groupby("kondisi_cuaca")["cnt"]
             .mean().sort_values(ascending=False))

fig_kategori, (ax_musim, ax_cuaca) = plt.subplots(1, 2, figsize=(13, 4.8))
bar_musim = ax_musim.bar(rata_musim.index, rata_musim.values)
ax_musim.set_title("Rata-rata per Hari: Musim")
ax_musim.set_ylabel("Rata-rata Penyewaan per Hari")
ax_musim.set_ylim(0, max(rata_musim.max() * 1.2, 1))
ax_musim.bar_label(bar_musim, fmt="%.0f", padding=3)

bar_cuaca = ax_cuaca.bar(rata_cuaca.index, rata_cuaca.values)
ax_cuaca.set_title("Rata-rata per Hari: Cuaca")
ax_cuaca.set_ylabel("Rata-rata Penyewaan per Hari")
ax_cuaca.set_ylim(0, max(rata_cuaca.max() * 1.2, 1))
ax_cuaca.tick_params(axis="x", rotation=15)
ax_cuaca.bar_label(bar_cuaca, fmt="%.0f", padding=3)

fig_kategori.tight_layout()
st.pyplot(fig_kategori)
plt.close(fig_kategori)

st.write(
    f"**Musim:** tertinggi {rata_musim.idxmax()} ({rata_musim.max():,.2f} per hari), "
    f"terendah {rata_musim.idxmin()} ({rata_musim.min():,.2f} per hari)."
)
st.write(
    f"**Cuaca:** tertinggi {rata_cuaca.idxmax()} ({rata_cuaca.max():,.2f} per hari), "
    f"terendah {rata_cuaca.idxmin()} ({rata_cuaca.min():,.2f} per hari)."
)

with st.expander("Tentang data dan cara membaca grafik"):
    st.write(
        "Data berasal dari Bike Sharing Dataset tahun 2011–2012. "
        "Rata-rata pada grafik jam dihitung per catatan penyewaan per jam, "
        "sedangkan grafik musim dan cuaca dihitung per hari. "
        "Perbandingan ini menunjukkan pola, bukan hubungan sebab-akibat. "
        "Nilai kelembapan nol yang mencurigakan ditangani pada notebook menggunakan median."
    )
