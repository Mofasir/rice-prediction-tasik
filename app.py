import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_connection():
    try:
        st.write(f"Attempting to connect to {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'rice_db'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        if connection.is_connected():
            st.success("Successfully connected to the database")
            return connection
    except Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        st.write(f"Connection parameters: host={os.getenv('DB_HOST')}, database={os.getenv('DB_NAME')}, user={os.getenv('DB_USER')}, port={os.getenv('DB_PORT')}")
        return None

# Fungsi untuk mengambil data
def get_data():
    conn = create_connection()
    if conn is not None:
        query = "SELECT * FROM rice_factors ORDER BY date"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()

# Fungsi untuk menghitung rata-rata harga beras
def calculate_rice_price_average(df):
    df['rice_price_avg'] = df[['rice_price_kb_I', 'rice_price_kb_II', 'rice_price_km_I', 
                               'rice_price_km_II', 'rice_price_ks_I', 'rice_price_ks_II']].mean(axis=1)
    return df

# Fungsi untuk membuat grafik garis
def create_line_chart(df):
    fig = px.line(df, x='date', y=['rice_price_avg', 'weather', 'fuel_price', 'exchange_rate', 'fertilizer_price'],
                  title='Tren Harga Beras dan Faktor-faktor Terkait')
    return fig

# Fungsi untuk membuat grafik korelasi
def create_correlation_chart(df):
    corr = df[['rice_price_avg', 'weather', 'fuel_price', 'exchange_rate', 'fertilizer_price']].corr()
    fig = px.imshow(corr, text_auto=True, aspect="auto",
                    title='Korelasi antara Harga Beras dan Faktor-faktor Terkait')
    return fig

# Main function untuk Streamlit app
def main():
    st.title('Analisis Harga Beras dan Faktor-faktor Terkait di Tasikmalaya')

    # Load data
    df = get_data()
    if df.empty:
        st.error("Tidak dapat mengambil data. Silakan periksa koneksi database.")
        return

    df = calculate_rice_price_average(df)

    # Sidebar untuk filter tanggal
    st.sidebar.header('Filter Data')
    start_date = st.sidebar.date_input('Tanggal Mulai', df['date'].min())
    end_date = st.sidebar.date_input('Tanggal Akhir', df['date'].max())

    # Filter data berdasarkan tanggal
    mask = (df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))
    filtered_df = df.loc[mask]

    # Menampilkan grafik garis
    st.plotly_chart(create_line_chart(filtered_df))

    # Menampilkan grafik korelasi
    st.plotly_chart(create_correlation_chart(filtered_df))

    # Menampilkan ringkasan data terkini
    st.header('Ringkasan Data Terkini')
    latest_data = filtered_df.iloc[-1]
    prev_data = filtered_df.iloc[-2] if len(filtered_df) > 1 else None

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Harga Beras Rata-rata Hari Ini", f"Rp {latest_data['rice_price_avg']:,.2f}")
    with col2:
        if prev_data is not None:
            st.metric("Harga Beras Rata-rata Kemarin", f"Rp {prev_data['rice_price_avg']:,.2f}")
    with col3:
        if prev_data is not None:
            change = (latest_data['rice_price_avg'] - prev_data['rice_price_avg']) / prev_data['rice_price_avg'] * 100
            st.metric("Perubahan Harga", f"{change:.2f}%")

    # Menampilkan data mentah
    if st.checkbox('Tampilkan Data Mentah'):
        st.subheader('Data Mentah')
        st.write(filtered_df)

if __name__ == '__main__':
    main()
