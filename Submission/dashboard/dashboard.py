import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =============================================
# KONFIGURASI DATA
# =============================================
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

season_order = ['Spring', 'Summer', 'Fall', 'Winter']

# =============================================
# FUNGSI UTAMA
# =============================================
@st.cache_data
def load_data():
    try:
        day_df = pd.read_csv("cleaned-day.csv")
        hour_df = pd.read_csv("cleaned-hour.csv")
        
        for df in [day_df, hour_df]:
            df['dteday'] = pd.to_datetime(df['dteday'])
            df['weather'] = df['weathersit'].map(weather_map)
            df['season'] = df['season'].map({1: 'Spring', 2: 'Summer', 3: 'Fall', 4: 'Winter'})
            df['month'] = df['mnth'].map(month_map)
            
        return day_df, hour_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

# =============================================
# ANTARMUKA PENGGUNA
# =============================================
st.set_page_config(page_title="Analisis Penyewaan Sepeda", layout="wide", page_icon="🚲")
day_df, hour_df = load_data()

if day_df is None or hour_df is None:
    st.stop()

# =============================================
# FILTER SIDEBAR
# =============================================
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
    
    # Validasi tanggal
    if len(selected_dates) != 2:
        st.error("Harap pilih rentang tanggal yang valid (start dan end date)")
        st.stop()
    
    start_date = pd.to_datetime(selected_dates[0])
    end_date = pd.to_datetime(selected_dates[1])

    # Auto-Season Filter
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    unique_months = date_range.month.unique()
    
    season_mapping = {
        **{m: 'Winter' for m in [12, 1, 2]},
        **{m: 'Spring' for m in [3, 4, 5]},
        **{m: 'Summer' for m in [6, 7, 8]},
        **{m: 'Fall' for m in [9, 10, 11]}
    }
    
    possible_seasons = list({season_mapping[month] for month in unique_months})
    possible_seasons = [s for s in season_order if s in possible_seasons]

    selected_seasons = st.multiselect(
        "Musim",
        options=possible_seasons,
        default=possible_seasons,
        help="Musim otomatis terpilih berdasarkan rentang tanggal"
    )
    
    selected_weather = st.multiselect(
        "Kondisi Cuaca",
        options=list(weather_map.values()),
        default=list(weather_map.values())
    )

# =============================================
# FILTER DATA UTAMA
# =============================================
try:
    filtered_day = day_df[
        (day_df['dteday'].dt.date >= selected_dates[0]) &
        (day_df['dteday'].dt.date <= selected_dates[1]) &
        (day_df['season'].isin(selected_seasons)) &
        (day_df['weather'].isin(selected_weather))
    ]
    
    filtered_hour = hour_df[
        (hour_df['dteday'].dt.date >= selected_dates[0]) &
        (hour_df['dteday'].dt.date <= selected_dates[1]) &
        (hour_df['season'].isin(selected_seasons)) &
        (hour_df['weather'].isin(selected_weather))
    ]
    
except Exception as e:
    st.error(f"Error filtering data: {str(e)}")
    st.stop()

if filtered_day.empty or filtered_hour.empty:
    st.warning("📭 Tidak ada data yang sesuai dengan filter")
    st.stop()

# =============================================
# TAMPILAN UTAMA
# =============================================
st.title("🚲 Analisis Penyewaan Sepeda - Jawaban Pertanyaan Bisnis")

with st.expander("🔍 Pertanyaan Bisnis", expanded=True):
    st.markdown("""
    1. **Faktor apa yang mempengaruhi jumlah total penyewaan sepeda (cnt) pada tingkat per jam dan per hari?**
    2. **Bagaimana pengaruh cuaca terhadap penggunaan sepeda oleh pengguna terdaftar vs pengguna kasual?**
    """)
    
# =============================================
# METRIK UTAMA
# =============================================
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

# Tambahkan penjelasan singkat
with st.expander("ℹ️ Penjelasan Metrik"):
    st.write("""
    - **Pengguna Terdaftar**: Penyewa yang memiliki keanggotaan/kartu langganan
    - **Pengguna Kasual**: Penyewa harian tanpa keanggotaan
    - **Rata-rata Harian**: Nilai rata-rata per hari dalam rentang filter
    """)

# =============================================
# VISUALISASI 1: FAKTOR PENGARUH
# =============================================
st.header("1. Faktor yang Mempengaruhi Total Penyewaan Sepeda")

# Analisis Korelasi
st.subheader("Analisis Korelasi Faktor Utama")
col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(10,6))
    sns.heatmap(filtered_day[['temp', 'atemp', 'hum', 'windspeed', 'cnt']].corr(),
                annot=True, cmap="coolwarm", ax=ax)
    ax.set_title("Korelasi Harian")
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(10,6))
    sns.heatmap(filtered_hour[['temp', 'atemp', 'hum', 'windspeed', 'cnt']].corr(),
                annot=True, cmap="coolwarm", ax=ax)
    ax.set_title("Korelasi Per Jam")
    st.pyplot(fig)

# Analisis Temporal
st.subheader("Pola Temporal Penyewaan Sepeda")
tab1, tab2, tab3 = st.tabs(["Harian", "Bulanan", "Per Jam"])

with tab1:
    fig, ax = plt.subplots(figsize=(12,4))
    sns.lineplot(data=filtered_day, x='dteday', y='cnt')
    ax.set(xlabel="Tanggal", ylabel="Total Penyewaan", title="Trend Harian")
    st.pyplot(fig)

with tab2:
    fig, ax = plt.subplots(figsize=(10,5))
    monthly = filtered_day.groupby('month')['cnt'].mean().reset_index()
    sns.barplot(data=monthly, x='month', y='cnt', order=list(month_map.values()))
    ax.set_title("Rata-rata Bulanan")
    plt.xticks(rotation=45)
    st.pyplot(fig)

with tab3:
    fig, ax = plt.subplots(figsize=(10,5))
    hourly = filtered_hour.groupby('hr')['cnt'].mean()
    sns.lineplot(x=hourly.index, y=hourly.values, marker='o')
    ax.set(xlabel="Jam", ylabel="Rata-rata", title="Pola Harian")
    st.pyplot(fig)

# =============================================
# VISUALISASI 2: PENGARUH CUACA
# =============================================
st.header("2. Pengaruh Cuaca Terhadap Pengguna")

# Perbandingan Pengguna
st.subheader("Perbandingan Pengguna Berdasarkan Cuaca")
col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(8,5))
    sns.barplot(data=filtered_day, x='weather', y='registered', 
                order=weather_map.values(), palette="Blues")
    ax.set_title("Pengguna Terdaftar")
    plt.xticks(rotation=45)
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(8,5))
    sns.barplot(data=filtered_day, x='weather', y='casual', 
                order=weather_map.values(), palette="Oranges")
    ax.set_title("Pengguna Kasual")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Pola Jam dengan Cuaca
st.subheader("Pola Penyewaan Per Jam Berdasarkan Cuaca")
fig, ax = plt.subplots(figsize=(12,6))
for weather in weather_map.values():
    subset = filtered_hour[filtered_hour['weather'] == weather]
    if not subset.empty:
        sns.lineplot(data=subset, x='hr', y='cnt', label=weather, estimator='mean')
ax.set(xlabel="Jam", ylabel="Rata-rata Penyewaan")
ax.legend(title="Kondisi Cuaca")
st.pyplot(fig)

st.markdown("---")
st.caption("Dashboard oleh Septbyu | Analisis Data Bike Sharing")
