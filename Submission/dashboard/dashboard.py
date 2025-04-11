import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================
# KONFIGURASI PAGE
# ==============================================
st.set_page_config(page_title="Analisis Penyewaan Sepeda", layout="wide", page_icon="🚲")

# ==============================================
# KONFIGURASI DATA
# ==============================================
month_map = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

weather_map = {
    1: 'Clear/Partly Cloudy',
    2: 'Mist/Cloudy',
    3: 'Light Rain/Snow/Thunderstorm',
    4: 'Heavy Rain/Snow/Fog'
}

season_map = {
    1: 'Winter', 2: 'Spring', 3: 'Summer', 4: 'Fall'
}

# ==============================================
# FUNGSI UTAMA
# ==============================================
@st.cache_data
def load_data():
    try:
        day_df = pd.read_csv("cleaned-day.csv")
        hour_df = pd.read_csv("cleaned-hour.csv")
        
        # Proses data sesuai notebook
        for df in [day_df, hour_df]:
            df['dteday'] = pd.to_datetime(df['dteday'])
            df['mnth_name'] = df['mnth'].map(month_map)
            df['season_name'] = df['season'].map(season_map)
            df['weather_desc'] = df['weathersit'].map(weather_map)
            
        return day_df, hour_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

# ==============================================
# KONFIGURASI STREAMLIT
# ==============================================
day_df, hour_df = load_data()

if day_df is None or hour_df is None:
    st.stop()

# ==============================================
# FILTER SIDEBAR
# ==============================================
with st.sidebar:
    st.header("⚙️ Filter Data")
    
    # Date Filter
    min_date = day_df['dteday'].min().date()
    max_date = day_df['dteday'].max().date()
    selected_dates = st.date_input(
        "Rentang Tanggal",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # Season Filter
    seasons = ['Winter', 'Spring', 'Summer', 'Fall']
    selected_seasons = st.multiselect(
        "Musim",
        options=seasons,
        default=seasons
    )
    
    # Weather Filter
    selected_weather = st.multiselect(
        "Kondisi Cuaca",
        options=list(weather_map.values()),
        default=list(weather_map.values())
    )

# ==============================================
# FILTER DATA
# ==============================================
filtered_day = day_df[
    (day_df['dteday'].dt.date >= selected_dates[0]) &
    (day_df['dteday'].dt.date <= selected_dates[1]) &
    (day_df['season_name'].isin(selected_seasons)) &
    (day_df['weather_desc'].isin(selected_weather))
]
filtered_hour = hour_df[
    (hour_df['dteday'].dt.date >= selected_dates[0]) &
    (hour_df['dteday'].dt.date <= selected_dates[1]) &
    (hour_df['season_name'].isin(selected_seasons)) &
    (hour_df['weather_desc'].isin(selected_weather))
]

if filtered_day.empty or filtered_hour.empty:
    st.warning("📭 Tidak ada data yang sesuai dengan filter")
    st.stop()

# ==============================================
# TAMPILAN UTAMA
# ==============================================
st.title("🚲 Analisis Penyewaan Sepeda - Jawaban Pertanyaan Bisnis")

with st.expander("🔍 Pertanyaan Bisnis", expanded=True):
    st.markdown(""" 
    1. **Bagaimana faktor-faktor lingkungan (suhu, kelembaban, kecepatan angin) dan temporal (musim, jam, hari) memengaruhi pola penyewaan sepeda harian dan per jam?**
    2. **Bagaimana pengaruh cuaca terhadap penggunaan sepeda oleh pengguna terdaftar vs pengguna kasual?**
    """)

# ==============================================
# METRIK UTAMA
# ==============================================
st.subheader("📊 Total Penyewaan Berdasarkan Jenis Pengguna")
col1, col2 = st.columns(2)

with col1:
    total_reg = filtered_day['registered'].sum()
    avg_reg = filtered_day['registered'].mean()
    st.metric(
        label="Pengguna Terdaftar",
        value=f"{total_reg:,}",
        help="Total penyewaan oleh pengguna terdaftar",
        delta=f"Rata-rata harian: {avg_reg:,.1f}"
    )

with col2:
    total_cas = filtered_day['casual'].sum()
    avg_cas = filtered_day['casual'].mean()
    st.metric(
        label="Pengguna Kasual", 
        value=f"{total_cas:,}",
        help="Total penyewaan oleh pengguna kasual",
        delta=f"Rata-rata harian: {avg_cas:,.1f}"
    )

# Tambahan penjelasan singkat
with st.expander("ℹ️ Penjelasan Metrik"):
    st.write("""
    - **Pengguna Terdaftar**: Penyewa yang memiliki keanggotaan/kartu langganan
    - **Pengguna Kasual**: Penyewa harian tanpa keanggotaan
    - **Rata-rata Harian**: Nilai rata-rata per hari dalam rentang filter
    """)

# ==============================================
# VISUALISASI 1: KORELASI
# ==============================================
st.header("1. Analisis Korelasi")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(10,6))
    sns.heatmap(
        filtered_day[['temp', 'hum', 'windspeed', 'casual', 'registered', 'cnt']].corr(),
        annot=True, 
        cmap="coolwarm",
        fmt=".2f",
        linewidths=0.5
    )
    plt.title("Korelasi Antar Variabel dalam Dataset Day")
    st.pyplot(fig)

# ==============================================
# VISUALISASI 2: POLA TEMPORAL
# ==============================================
st.header("2. Analisis Temporal")

# Panel 2.1: Bulanan
fig, ax = plt.subplots(figsize=(8,6))
monthly = filtered_day.groupby('mnth_name')['cnt'].mean().reset_index()
sns.barplot(
    x='mnth_name',
    y='cnt',
    data=monthly,
    order=list(month_map.values()),
    palette="Set2"
)
plt.title("Rata-rata Penyewaan Berdasarkan Bulan")
plt.xlabel("Bulan")
plt.ylabel("Rata-rata Penyewaan Sepeda")
plt.xticks(rotation=45)
st.pyplot(fig)

# Panel 2.2: Musiman
fig, ax = plt.subplots(figsize=(8,6))
seasonal = filtered_day.groupby('season_name')['cnt'].mean().reset_index()
sns.barplot(
    x='season_name',
    y='cnt',
    data=seasonal,
    order=['Winter', 'Spring', 'Summer', 'Fall'],
    palette="Set2"
)
plt.title("Rata-rata Penyewaan Berdasarkan Musim")
plt.xlabel("Musim")
plt.ylabel("Rata-rata Penyewaan Sepeda")
st.pyplot(fig)

# Panel 2.3: Per Jam dan harian
fig, ax = plt.subplots(figsize=(12,6))
daily_rentals = filtered_day.groupby('dteday')['cnt'].sum()

ax.plot(
    daily_rentals.index,
    daily_rentals.values,
    color='green',
    linewidth=2,
    marker='o'
)

ax.set_title("Trend Penyewaan Harian", fontsize=16)
ax.set_xlabel("Tanggal", fontsize=12)
ax.set_ylabel("Total Penyewaan Sepeda", fontsize=12)
ax.grid(True, linestyle='--', alpha=0.6)
plt.xticks(rotation=45)
st.pyplot(fig)

fig, ax = plt.subplots(figsize=(8,6))
hourly = filtered_hour.groupby('hr')['cnt'].mean()
plt.plot(
    hourly.index,
    hourly.values,
    marker='o',
    color='orange',
    linewidth=2
)
plt.title("Penyewaan Sepeda Per Jam")
plt.xlabel("Jam")
plt.ylabel("Rata-rata Penyewaan Sepeda")
plt.grid(True, linestyle='--', alpha=0.6)
st.pyplot(fig)

# ==============================================
# VISUALISASI 3: PENGARUH CUACA
# ==============================================
st.header("3. Pengaruh Kondisi Cuaca")

fig, axes = plt.subplots(1, 2, figsize=(18,6))

# Panel 3.1: Pengguna Terdaftar
sns.barplot(
    x='weather_desc',
    y='registered',
    data=filtered_hour,
    palette="Set2",
    ax=axes[0]
)
axes[0].set_title("Pengaruh Cuaca terhadap Pengguna Terdaftar")
axes[0].set_xlabel("Deskripsi Cuaca")
axes[0].set_ylabel("Rata-rata Penyewaan Sepeda (Terdaftar)")
axes[0].tick_params(axis='x', rotation=45)

# Panel 3.2: Pengguna Kasual
sns.barplot(
    x='weather_desc',
    y='casual',
    data=filtered_hour,
    palette="Set2",
    ax=axes[1]
)
axes[1].set_title("Pengaruh Cuaca terhadap Pengguna Kasual")
axes[1].set_xlabel("Deskripsi Cuaca")
axes[1].set_ylabel("Rata-rata Penyewaan Sepeda (Kasual)")
axes[1].tick_params(axis='x', rotation=45)
st.pyplot(fig)

st.markdown("---")
st.caption("Dashboard oleh Septbyu | Analisis Data Bike Sharing")

