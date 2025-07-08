import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

# Konfigurasi halaman
st.set_page_config(
    page_title="Manajemen Stok ATK Kantor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
def init_database():
    """Inisialisasi database SQLite"""
    conn = sqlite3.connect('stok_atk.db')
    cursor = conn.cursor()
    
    # Tabel barang
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS barang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_barang TEXT UNIQUE NOT NULL,
            nama_barang TEXT NOT NULL,
            kategori TEXT NOT NULL,
            satuan TEXT NOT NULL,
            stok_minimum INTEGER NOT NULL,
            stok_saat_ini INTEGER NOT NULL,
            harga_satuan REAL NOT NULL,
            lokasi_penyimpanan TEXT,
            tanggal_input DATE NOT NULL,
            keterangan TEXT
        )
    ''')
    
    # Tabel transaksi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_barang TEXT NOT NULL,
            jenis_transaksi TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            tanggal_transaksi DATE NOT NULL,
            keterangan TEXT,
            penanggung_jawab TEXT,
            FOREIGN KEY (kode_barang) REFERENCES barang (kode_barang)
        )
    ''')
    
    conn.commit()
    conn.close()

# Fungsi database
def get_connection():
    """Mendapatkan koneksi database"""
    return sqlite3.connect('stok_atk.db')

def get_all_barang():
    """Mengambil semua data barang"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM barang ORDER BY nama_barang", conn)
    conn.close()
    return df

def get_barang_by_kode(kode_barang):
    """Mengambil data barang berdasarkan kode"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM barang WHERE kode_barang = ?", (kode_barang,))
    result = cursor.fetchone()
    conn.close()
    return result

def insert_barang(data):
    """Menambah barang baru"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO barang (kode_barang, nama_barang, kategori, satuan, 
                              stok_minimum, stok_saat_ini, harga_satuan, 
                              lokasi_penyimpanan, tanggal_input, keterangan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_barang(kode_barang, data):
    """Update data barang"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE barang SET nama_barang=?, kategori=?, satuan=?, 
                         stok_minimum=?, stok_saat_ini=?, harga_satuan=?, 
                         lokasi_penyimpanan=?, keterangan=?
        WHERE kode_barang=?
    ''', (*data, kode_barang))
    conn.commit()
    conn.close()

def delete_barang(kode_barang):
    """Hapus barang"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM barang WHERE kode_barang = ?", (kode_barang,))
    cursor.execute("DELETE FROM transaksi WHERE kode_barang = ?", (kode_barang,))
    conn.commit()
    conn.close()

def insert_transaksi(data):
    """Menambah transaksi baru"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transaksi (kode_barang, jenis_transaksi, jumlah, 
                             tanggal_transaksi, keterangan, penanggung_jawab)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()

def update_stok_barang(kode_barang, jumlah_perubahan):
    """Update stok barang"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE barang SET stok_saat_ini = stok_saat_ini + ?
        WHERE kode_barang = ?
    ''', (jumlah_perubahan, kode_barang))
    conn.commit()
    conn.close()

def get_transaksi():
    """Mengambil semua data transaksi"""
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT t.*, b.nama_barang 
        FROM transaksi t
        JOIN barang b ON t.kode_barang = b.kode_barang
        ORDER BY t.tanggal_transaksi DESC
    ''', conn)
    conn.close()
    return df

def get_stok_menipis():
    """Mengambil barang dengan stok menipis"""
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT * FROM barang 
        WHERE stok_saat_ini <= stok_minimum
        ORDER BY stok_saat_ini ASC
    ''', conn)
    conn.close()
    return df

# Fungsi UI
def sidebar_navigation():
    """Sidebar untuk navigasi"""
    st.sidebar.title("📝 Manajemen Stok ATK")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Pilih Menu:",
        ["🏠 Dashboard", "📦 Data Barang", "📊 Transaksi", "⚠️ Stok Menipis", "📈 Laporan"]
    )
    
    return menu

def dashboard():
    """Halaman dashboard"""
    st.title("🏠 Dashboard Manajemen Stok ATK")
    
    # Ambil data untuk statistik
    df_barang = get_all_barang()
    df_transaksi = get_transaksi()
    df_stok_menipis = get_stok_menipis()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_barang = len(df_barang)
        st.metric("Total Barang", total_barang)
    
    with col2:
        total_stok = df_barang['stok_saat_ini'].sum() if not df_barang.empty else 0
        st.metric("Total Stok", total_stok)
    
    with col3:
        barang_menipis = len(df_stok_menipis)
        st.metric("Stok Menipis", barang_menipis, delta=f"-{barang_menipis}")
    
    with col4:
        total_nilai = (df_barang['stok_saat_ini'] * df_barang['harga_satuan']).sum() if not df_barang.empty else 0
        st.metric("Total Nilai Stok", f"Rp {total_nilai:,.0f}")
    
    # Grafik
    if not df_barang.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribusi Stok per Kategori")
            kategori_count = df_barang.groupby('kategori')['stok_saat_ini'].sum().reset_index()
            fig_pie = px.pie(kategori_count, values='stok_saat_ini', names='kategori')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("Barang dengan Stok Terbanyak")
            top_stok = df_barang.nlargest(10, 'stok_saat_ini')
            fig_bar = px.bar(top_stok, x='stok_saat_ini', y='nama_barang', 
                           orientation='h', title="Top 10 Barang")
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Transaksi terakhir
    st.subheader("Transaksi Terakhir")
    if not df_transaksi.empty:
        recent_transactions = df_transaksi.head(10)
        st.dataframe(recent_transactions[['tanggal_transaksi', 'nama_barang', 'jenis_transaksi', 'jumlah', 'penanggung_jawab']])
    else:
        st.info("Belum ada transaksi")

def data_barang():
    """Halaman manajemen data barang"""
    st.title("📦 Data Barang ATK")
    
    # Tabs untuk berbagai fungsi
    tab1, tab2, tab3 = st.tabs(["Lihat Data", "Tambah Barang", "Edit/Hapus"])
    
    with tab1:
        st.subheader("Daftar Barang")
        df_barang = get_all_barang()
        
        if not df_barang.empty:
            # Filter
            col1, col2 = st.columns(2)
            with col1:
                kategori_filter = st.selectbox(
                    "Filter Kategori:",
                    ["Semua"] + list(df_barang['kategori'].unique())
                )
            
            with col2:
                search_term = st.text_input("Cari Barang:", placeholder="Masukkan nama barang...")
            
            # Apply filters
            filtered_df = df_barang.copy()
            if kategori_filter != "Semua":
                filtered_df = filtered_df[filtered_df['kategori'] == kategori_filter]
            
            if search_term:
                filtered_df = filtered_df[filtered_df['nama_barang'].str.contains(search_term, case=False, na=False)]
            
            # Styling untuk stok menipis
            def highlight_low_stock(row):
                if row['stok_saat_ini'] <= row['stok_minimum']:
                    return ['background-color: #ffcccc'] * len(row)
                return [''] * len(row)
            
            styled_df = filtered_df.style.apply(highlight_low_stock, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            st.info("💡 Baris berwarna merah menunjukkan barang dengan stok menipis")
        else:
            st.info("Belum ada data barang")
    
    with tab2:
        st.subheader("Tambah Barang Baru")
        
        with st.form("form_tambah_barang"):
            col1, col2 = st.columns(2)
            
            with col1:
                kode_barang = st.text_input("Kode Barang*", placeholder="Contoh: ATK001")
                nama_barang = st.text_input("Nama Barang*", placeholder="Contoh: Pulpen Biru")
                kategori = st.selectbox("Kategori*", 
                    ["Alat Tulis", "Kertas", "Perlengkapan Kantor", "Elektronik", "Lainnya"])
                satuan = st.selectbox("Satuan*", 
                    ["pcs", "box", "pak", "rim", "roll", "set", "buah"])
            
            with col2:
                stok_minimum = st.number_input("Stok Minimum*", min_value=0, value=10)
                stok_saat_ini = st.number_input("Stok Saat Ini*", min_value=0, value=0)
                harga_satuan = st.number_input("Harga Satuan*", min_value=0.0, value=0.0, step=0.01)
                lokasi_penyimpanan = st.text_input("Lokasi Penyimpanan", placeholder="Contoh: Gudang A")
            
            keterangan = st.text_area("Keterangan", placeholder="Keterangan tambahan...")
            
            if st.form_submit_button("Tambah Barang", type="primary"):
                if kode_barang and nama_barang and kategori and satuan:
                    data = (kode_barang, nama_barang, kategori, satuan, stok_minimum, 
                           stok_saat_ini, harga_satuan, lokasi_penyimpanan, 
                           date.today(), keterangan)
                    
                    if insert_barang(data):
                        st.success("Barang berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.error("Kode barang sudah ada!")
                else:
                    st.error("Harap isi semua field yang wajib (*)")
    
    with tab3:
        st.subheader("Edit/Hapus Barang")
        
        df_barang = get_all_barang()
        if not df_barang.empty:
            selected_kode = st.selectbox("Pilih Barang:", df_barang['kode_barang'].tolist())
            
            if selected_kode:
                barang_data = get_barang_by_kode(selected_kode)
                
                if barang_data:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        with st.form("form_edit_barang"):
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                nama_barang = st.text_input("Nama Barang", value=barang_data[2])
                                kategori = st.selectbox("Kategori", 
                                    ["Alat Tulis", "Kertas", "Perlengkapan Kantor", "Elektronik", "Lainnya"],
                                    index=["Alat Tulis", "Kertas", "Perlengkapan Kantor", "Elektronik", "Lainnya"].index(barang_data[3]))
                                satuan = st.selectbox("Satuan", 
                                    ["pcs", "box", "pak", "rim", "roll", "set", "buah"],
                                    index=["pcs", "box", "pak", "rim", "roll", "set", "buah"].index(barang_data[4]))
                            
                            with col_b:
                                stok_minimum = st.number_input("Stok Minimum", min_value=0, value=barang_data[5])
                                stok_saat_ini = st.number_input("Stok Saat Ini", min_value=0, value=barang_data[6])
                                harga_satuan = st.number_input("Harga Satuan", min_value=0.0, value=barang_data[7], step=0.01)
                            
                            lokasi_penyimpanan = st.text_input("Lokasi Penyimpanan", value=barang_data[8] or "")
                            keterangan = st.text_area("Keterangan", value=barang_data[10] or "")
                            
                            if st.form_submit_button("Update Barang", type="primary"):
                                update_data = (nama_barang, kategori, satuan, stok_minimum, 
                                             stok_saat_ini, harga_satuan, lokasi_penyimpanan, keterangan)
                                update_barang(selected_kode, update_data)
                                st.success("Barang berhasil diupdate!")
                                st.rerun()
                    
                    with col2:
                        st.write("**Aksi Lainnya:**")
                        if st.button("🗑️ Hapus Barang", type="secondary"):
                            delete_barang(selected_kode)
                            st.success("Barang berhasil dihapus!")
                            st.rerun()
        else:
            st.info("Belum ada data barang untuk diedit")

def transaksi():
    """Halaman transaksi"""
    st.title("📊 Transaksi Stok")
    
    tab1, tab2 = st.tabs(["Tambah Transaksi", "Riwayat Transaksi"])
    
    with tab1:
        st.subheader("Transaksi Barang")
        
        df_barang = get_all_barang()
        if not df_barang.empty:
            with st.form("form_transaksi"):
                col1, col2 = st.columns(2)
                
                with col1:
                    kode_barang = st.selectbox("Pilih Barang:", df_barang['kode_barang'].tolist())
                    jenis_transaksi = st.selectbox("Jenis Transaksi:", ["Masuk", "Keluar"])
                    jumlah = st.number_input("Jumlah:", min_value=1, value=1)
                
                with col2:
                    tanggal_transaksi = st.date_input("Tanggal Transaksi:", value=date.today())
                    penanggung_jawab = st.text_input("Penanggung Jawab:", placeholder="Nama penanggung jawab")
                
                keterangan = st.text_area("Keterangan:", placeholder="Keterangan transaksi...")
                
                # Tampilkan info stok saat ini
                if kode_barang:
                    current_stock = df_barang[df_barang['kode_barang'] == kode_barang]['stok_saat_ini'].iloc[0]
                    st.info(f"Stok saat ini: {current_stock}")
                    
                    if jenis_transaksi == "Keluar" and jumlah > current_stock:
                        st.error("Jumlah keluar melebihi stok yang tersedia!")
                
                if st.form_submit_button("Proses Transaksi", type="primary"):
                    if kode_barang and penanggung_jawab:
                        current_stock = df_barang[df_barang['kode_barang'] == kode_barang]['stok_saat_ini'].iloc[0]
                        
                        if jenis_transaksi == "Keluar" and jumlah > current_stock:
                            st.error("Stok tidak mencukupi!")
                        else:
                            # Insert transaksi
                            data_transaksi = (kode_barang, jenis_transaksi, jumlah, 
                                            tanggal_transaksi, keterangan, penanggung_jawab)
                            insert_transaksi(data_transaksi)
                            
                            # Update stok
                            perubahan_stok = jumlah if jenis_transaksi == "Masuk" else -jumlah
                            update_stok_barang(kode_barang, perubahan_stok)
                            
                            st.success(f"Transaksi {jenis_transaksi.lower()} berhasil!")
                            st.rerun()
                    else:
                        st.error("Harap isi semua field yang wajib!")
        else:
            st.info("Belum ada data barang. Silakan tambah barang terlebih dahulu.")
    
    with tab2:
        st.subheader("Riwayat Transaksi")
        
        df_transaksi = get_transaksi()
        if not df_transaksi.empty:
            # Filter
            col1, col2, col3 = st.columns(3)
            
            with col1:
                jenis_filter = st.selectbox("Filter Jenis:", ["Semua", "Masuk", "Keluar"])
            
            with col2:
                start_date = st.date_input("Dari Tanggal:", value=date.today().replace(day=1))
            
            with col3:
                end_date = st.date_input("Sampai Tanggal:", value=date.today())
            
            # Apply filters
            filtered_df = df_transaksi.copy()
            if jenis_filter != "Semua":
                filtered_df = filtered_df[filtered_df['jenis_transaksi'] == jenis_filter]
            
            filtered_df['tanggal_transaksi'] = pd.to_datetime(filtered_df['tanggal_transaksi'])
            filtered_df = filtered_df[
                (filtered_df['tanggal_transaksi'] >= pd.to_datetime(start_date)) &
                (filtered_df['tanggal_transaksi'] <= pd.to_datetime(end_date))
            ]
            
            st.dataframe(filtered_df[['tanggal_transaksi', 'kode_barang', 'nama_barang', 
                                    'jenis_transaksi', 'jumlah', 'penanggung_jawab', 'keterangan']], 
                        use_container_width=True)
        else:
            st.info("Belum ada transaksi")

def stok_menipis():
    """Halaman stok menipis"""
    st.title("⚠️ Stok Menipis")
    
    df_stok_menipis = get_stok_menipis()
    
    if not df_stok_menipis.empty:
        st.warning(f"Terdapat {len(df_stok_menipis)} barang dengan stok menipis!")
        
        # Tampilkan dalam format card
        for idx, row in df_stok_menipis.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{row['nama_barang']}**")
                    st.text(f"Kode: {row['kode_barang']}")
                
                with col2:
                    st.metric("Stok Saat Ini", row['stok_saat_ini'])
                
                with col3:
                    st.metric("Stok Minimum", row['stok_minimum'])
                
                with col4:
                    selisih = row['stok_minimum'] - row['stok_saat_ini']
                    st.metric("Perlu Tambah", selisih)
                
                st.markdown("---")
    else:
        st.success("Semua barang memiliki stok yang mencukupi!")

def laporan():
    """Halaman laporan"""
    st.title("📈 Laporan")
    
    tab1, tab2, tab3 = st.tabs(["Laporan Stok", "Laporan Transaksi", "Laporan Nilai"])
    
    with tab1:
        st.subheader("Laporan Stok Barang")
        
        df_barang = get_all_barang()
        if not df_barang.empty:
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Item", len(df_barang))
            
            with col2:
                st.metric("Total Stok", df_barang['stok_saat_ini'].sum())
            
            with col3:
                avg_stock = df_barang['stok_saat_ini'].mean()
                st.metric("Rata-rata Stok", f"{avg_stock:.1f}")
            
            # Grafik stok per kategori
            st.subheader("Stok per Kategori")
            kategori_stok = df_barang.groupby('kategori')['stok_saat_ini'].sum().reset_index()
            fig = px.bar(kategori_stok, x='kategori', y='stok_saat_ini', 
                        title="Total Stok per Kategori")
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabel detail
            st.subheader("Detail Stok")
            st.dataframe(df_barang[['kode_barang', 'nama_barang', 'kategori', 
                                   'stok_saat_ini', 'stok_minimum', 'satuan']], 
                        use_container_width=True)
    
    with tab2:
        st.subheader("Laporan Transaksi")
        
        df_transaksi = get_transaksi()
        if not df_transaksi.empty:
            # Filter periode
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Dari:", value=date.today().replace(day=1))
            with col2:
                end_date = st.date_input("Sampai:", value=date.today())
            
            # Filter data
            df_transaksi['tanggal_transaksi'] = pd.to_datetime(df_transaksi['tanggal_transaksi'])
            filtered_transaksi = df_transaksi[
                (df_transaksi['tanggal_transaksi'] >= pd.to_datetime(start_date)) &
                (df_transaksi['tanggal_transaksi'] <= pd.to_datetime(end_date))
            ]
            
            if not filtered_transaksi.empty:
                # Summary
                masuk = filtered_transaksi[filtered_transaksi['jenis_transaksi'] == 'Masuk']['jumlah'].sum()
                keluar = filtered_transaksi[filtered_transaksi['jenis_transaksi'] == 'Keluar']['jumlah'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Masuk", masuk)
                with col2:
                    st.metric("Total Keluar", keluar)
                with col3:
                    st.metric("Net Flow", masuk - keluar)
                
                # Grafik transaksi per hari
                daily_trans = filtered_transaksi.groupby(['tanggal_transaksi', 'jenis_transaksi'])['jumlah'].sum().reset_index()
                fig = px.line(daily_trans, x='tanggal_transaksi', y='jumlah', 
                             color='jenis_transaksi', title="Transaksi Harian")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Tidak ada transaksi pada periode ini")
        else:
            st.info("Belum ada data transaksi")
    
    with tab3:
        st.subheader("Laporan Nilai Stok")
        
        df_barang = get_all_barang()
        if not df_barang.empty:
            # Hitung nilai stok
            df_barang['nilai_stok'] = df_barang['stok_saat_ini'] * df_barang['harga_satuan']
            
            total_nilai = df_barang['nilai_stok'].sum()
            st.metric("Total Nilai Stok", f"Rp {total_nilai:,.0f}")
            
            # Nilai per kategori
            nilai_kategori = df_barang.groupby('kategori')['nilai_stok'].sum().reset_index()
            fig = px.pie(nilai_kategori, values='nilai_stok', names='kategori', 
                        title="Distribusi Nilai Stok per Kategori")
            st.plotly_chart(fig, use_container_width=True)
            
            # Top 10 barang dengan nilai tertinggi
            st.subheader("Top 10 Barang dengan Nilai Tertinggi")
            top_nilai = df_barang.nlargest(10, 'nilai_stok')
            st.dataframe(top_nilai[['nama_barang', 'stok_saat_ini', 'harga_satuan', 'nilai_stok']], 
                        use_container_width=True)

# Main application
def main():
    # Inisialisasi database
    init_database()
    
    # Navigation
    menu = sidebar_navigation()
    
    # Routing
    if menu == "🏠 Dashboard":
        dashboard()
    elif menu == "📦 Data Barang":
        data_barang()
    elif menu == "📊 Transaksi":
        transaksi()
    elif menu == "⚠️ Stok Menipis":
        stok_menipis()
    elif menu == "📈 Laporan":
        laporan()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Manajemen Stok ATK Kantor**")
    st.sidebar.markdown("Versi 1.0")

if __name__ == "__main__":
    main()
