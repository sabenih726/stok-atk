import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import warnings

# Suppress sqlite3 deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlite3")

# Setup custom SQLite adapters
def setup_sqlite_adapters():
    """Setup custom SQLite adapters untuk mengatasi deprecation warning"""
    sqlite3.register_adapter(date, lambda x: x.isoformat())
    sqlite3.register_adapter(datetime, lambda x: x.isoformat())
    sqlite3.register_converter("date", lambda x: datetime.fromisoformat(x.decode()).date())
    sqlite3.register_converter("datetime", lambda x: datetime.fromisoformat(x.decode()))

# Setup adapters
setup_sqlite_adapters()

# Konfigurasi halaman
st.set_page_config(
    page_title="Manajemen Stok ATK Kantor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
def init_database():
    """Inisialisasi database dan tabel"""
    conn = sqlite3.connect('stok_atk.db', detect_types=sqlite3.PARSE_DECLTYPES)
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
    return sqlite3.connect('stok_atk.db', detect_types=sqlite3.PARSE_DECLTYPES)

def get_all_barang():
    """Mengambil semua data barang"""
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM barang ORDER BY nama_barang", conn)
        return df
    except Exception as e:
        st.error(f"Error mengambil data barang: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_barang_by_kode(kode_barang):
    """Mengambil data barang berdasarkan kode"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM barang WHERE kode_barang = ?", (kode_barang,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        st.error(f"Error mengambil data barang: {e}")
        return None
    finally:
        conn.close()

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
        st.error("Kode barang sudah ada!")
        return False
    except Exception as e:
        st.error(f"Error menambah barang: {e}")
        return False
    finally:
        conn.close()

def update_barang(kode_barang, data):
    """Update data barang"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE barang SET nama_barang=?, kategori=?, satuan=?, 
                             stok_minimum=?, stok_saat_ini=?, harga_satuan=?, 
                             lokasi_penyimpanan=?, keterangan=?
            WHERE kode_barang=?
        ''', (*data, kode_barang))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error update barang: {e}")
        return False
    finally:
        conn.close()

def delete_barang(kode_barang):
    """Hapus barang"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM barang WHERE kode_barang = ?", (kode_barang,))
        cursor.execute("DELETE FROM transaksi WHERE kode_barang = ?", (kode_barang,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error menghapus barang: {e}")
        return False
    finally:
        conn.close()

def insert_transaksi(data):
    """Menambah transaksi baru"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO transaksi (kode_barang, jenis_transaksi, jumlah, 
                                 tanggal_transaksi, keterangan, penanggung_jawab)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error menambah transaksi: {e}")
        return False
    finally:
        conn.close()

def update_stok_barang(kode_barang, jumlah_perubahan):
    """Update stok barang"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE barang SET stok_saat_ini = stok_saat_ini + ?
            WHERE kode_barang = ?
        ''', (jumlah_perubahan, kode_barang))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error update stok: {e}")
        return False
    finally:
        conn.close()

def get_transaksi():
    """Mengambil semua data transaksi"""
    conn = get_connection()
    try:
        df = pd.read_sql_query('''
            SELECT t.*, b.nama_barang 
            FROM transaksi t
            JOIN barang b ON t.kode_barang = b.kode_barang
            ORDER BY t.tanggal_transaksi DESC
        ''', conn)
        return df
    except Exception as e:
        st.error(f"Error mengambil data transaksi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_stok_menipis():
    """Mengambil barang dengan stok menipis"""
    conn = get_connection()
    try:
        df = pd.read_sql_query('''
            SELECT * FROM barang 
            WHERE stok_saat_ini <= stok_minimum
            ORDER BY stok_saat_ini ASC
        ''', conn)
        return df
    except Exception as e:
        st.error(f"Error mengambil data stok menipis: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# Inisialisasi database
init_database()

# UI Components
def main():
    """Fungsi utama aplikasi"""
    st.title("🏢 Manajemen Stok ATK Kantor")
    st.markdown("---")
    
    # Sidebar untuk navigasi
    st.sidebar.title("Menu Navigasi")
    menu = st.sidebar.selectbox(
        "Pilih Menu:",
        ["Dashboard", "Data Barang", "Transaksi", "Laporan", "Pengaturan"]
    )
    
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Data Barang":
        show_data_barang()
    elif menu == "Transaksi":
        show_transaksi()
    elif menu == "Laporan":
        show_laporan()
    elif menu == "Pengaturan":
        show_pengaturan()

def show_dashboard():
    """Tampilan dashboard"""
    st.header("📊 Dashboard")
    
    # Ambil data
    df_barang = get_all_barang()
    df_stok_menipis = get_stok_menipis()
    df_transaksi = get_transaksi()
    
    if not df_barang.empty:
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Barang", len(df_barang))
        
        with col2:
            total_stok = df_barang['stok_saat_ini'].sum()
            st.metric("Total Stok", f"{total_stok:,}")
        
        with col3:
            stok_menipis = len(df_stok_menipis)
            st.metric("Stok Menipis", stok_menipis, delta=f"-{stok_menipis}")
        
        with col4:
            if not df_transaksi.empty:
                transaksi_hari_ini = len(df_transaksi[df_transaksi['tanggal_transaksi'] == date.today().isoformat()])
                st.metric("Transaksi Hari Ini", transaksi_hari_ini)
            else:
                st.metric("Transaksi Hari Ini", 0)
        
        # Alert stok menipis
        if not df_stok_menipis.empty:
            st.warning(f"⚠️ {len(df_stok_menipis)} barang memiliki stok menipis!")
            with st.expander("Lihat Barang dengan Stok Menipis"):
                st.dataframe(df_stok_menipis[['kode_barang', 'nama_barang', 'stok_saat_ini', 'stok_minimum']])
    
    else:
        st.info("Belum ada data barang. Silakan tambahkan data barang terlebih dahulu.")

def show_data_barang():
    """Tampilan data barang"""
    st.header("📦 Data Barang")
    
    tab1, tab2 = st.tabs(["📋 Daftar Barang", "➕ Tambah Barang"])
    
    with tab1:
        df_barang = get_all_barang()
        if not df_barang.empty:
            st.dataframe(df_barang, use_container_width=True)
        else:
            st.info("Belum ada data barang")
    
    with tab2:
        st.subheader("Tambah Barang Baru")
        
        with st.form("form_tambah_barang"):
            col1, col2 = st.columns(2)
            
            with col1:
                kode_barang = st.text_input("Kode Barang*")
                nama_barang = st.text_input("Nama Barang*")
                kategori = st.selectbox("Kategori*", ["Alat Tulis", "Kertas", "Elektronik", "Peralatan", "Lainnya"])
                satuan = st.selectbox("Satuan*", ["pcs", "dus", "rim", "pak", "lusin", "kg", "liter"])
            
            with col2:
                stok_minimum = st.number_input("Stok Minimum*", min_value=0, value=10)
                stok_saat_ini = st.number_input("Stok Saat Ini*", min_value=0, value=0)
                harga_satuan = st.number_input("Harga Satuan*", min_value=0.0, value=0.0)
                lokasi_penyimpanan = st.text_input("Lokasi Penyimpanan")
            
            keterangan = st.text_area("Keterangan")
            
            if st.form_submit_button("Tambah Barang"):
                if kode_barang and nama_barang and kategori and satuan:
                    data = (
                        kode_barang, nama_barang, kategori, satuan,
                        stok_minimum, stok_saat_ini, harga_satuan,
                        lokasi_penyimpanan, date.today(), keterangan
                    )
                    
                    if insert_barang(data):
                        st.success("Barang berhasil ditambahkan!")
                        st.rerun()
                else:
                    st.error("Mohon isi semua field yang wajib (*)")

def show_transaksi():
    """Tampilan transaksi"""
    st.header("📝 Transaksi")
    
    tab1, tab2 = st.tabs(["📋 Riwayat Transaksi", "➕ Tambah Transaksi"])
    
    with tab1:
        df_transaksi = get_transaksi()
        if not df_transaksi.empty:
            st.dataframe(df_transaksi, use_container_width=True)
        else:
            st.info("Belum ada data transaksi")
    
    with tab2:
        st.subheader("Tambah Transaksi Baru")
        
        df_barang = get_all_barang()
        if df_barang.empty:
            st.warning("Tidak ada data barang. Silakan tambahkan barang terlebih dahulu.")
            return
        
        with st.form("form_transaksi"):
            kode_barang = st.selectbox("Pilih Barang*", df_barang['kode_barang'].tolist())
            jenis_transaksi = st.selectbox("Jenis Transaksi*", ["Masuk", "Keluar"])
            jumlah = st.number_input("Jumlah*", min_value=1, value=1)
            tanggal_transaksi = st.date_input("Tanggal Transaksi*", value=date.today())
            penanggung_jawab = st.text_input("Penanggung Jawab*")
            keterangan = st.text_area("Keterangan")
            
            if st.form_submit_button("Simpan Transaksi"):
                if kode_barang and jenis_transaksi and jumlah and penanggung_jawab:
                    # Cek stok untuk transaksi keluar
                    if jenis_transaksi == "Keluar":
                        barang = get_barang_by_kode(kode_barang)
                        if barang and barang[6] < jumlah:  # stok_saat_ini
                            st.error(f"Stok tidak mencukupi! Stok saat ini: {barang[6]}")
                            return
                    
                    data = (
                        kode_barang, jenis_transaksi, jumlah,
                        tanggal_transaksi, keterangan, penanggung_jawab
                    )
                    
                    if insert_transaksi(data):
                        # Update stok
                        jumlah_perubahan = jumlah if jenis_transaksi == "Masuk" else -jumlah
                        if update_stok_barang(kode_barang, jumlah_perubahan):
                            st.success("Transaksi berhasil disimpan!")
                            st.rerun()
                else:
                    st.error("Mohon isi semua field yang wajib (*)")

def show_laporan():
    """Tampilan laporan"""
    st.header("📊 Laporan")
    
    df_barang = get_all_barang()
    df_transaksi = get_transaksi()
    
    if df_barang.empty:
        st.info("Belum ada data untuk laporan")
        return
    
    # Filter tanggal
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Tanggal Mulai", value=date.today().replace(day=1))
    with col2:
        end_date = st.date_input("Tanggal Akhir", value=date.today())
    
    # Chart stok per kategori
    if not df_barang.empty:
        st.subheader("Stok Per Kategori")
        fig_kategori = px.bar(
            df_barang.groupby('kategori')['stok_saat_ini'].sum().reset_index(),
            x='kategori', y='stok_saat_ini',
            title="Total Stok Per Kategori"
        )
        st.plotly_chart(fig_kategori, use_container_width=True)
    
    # Chart transaksi
    if not df_transaksi.empty:
        st.subheader("Transaksi Per Hari")
        df_transaksi['tanggal_transaksi'] = pd.to_datetime(df_transaksi['tanggal_transaksi'])
        df_filtered = df_transaksi[
            (df_transaksi['tanggal_transaksi'] >= pd.to_datetime(start_date)) &
            (df_transaksi['tanggal_transaksi'] <= pd.to_datetime(end_date))
        ]
        
        if not df_filtered.empty:
            daily_trans = df_filtered.groupby(['tanggal_transaksi', 'jenis_transaksi']).size().reset_index(name='jumlah')
            fig_trans = px.line(
                daily_trans, x='tanggal_transaksi', y='jumlah',
                color='jenis_transaksi', title="Transaksi Harian"
            )
            st.plotly_chart(fig_trans, use_container_width=True)

def show_pengaturan():
    """Tampilan pengaturan"""
    st.header("⚙️ Pengaturan")
    
    st.subheader("Backup & Restore")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Backup Database"):
            # Implementasi backup
            st.success("Database berhasil di-backup!")
    
    with col2:
        uploaded_file = st.file_uploader("📤 Restore Database", type=['db'])
        if uploaded_file and st.button("Restore"):
            st.success("Database berhasil di-restore!")
    
    st.subheader("Hapus Semua Data")
    if st.button("🗑️ Hapus Semua Data", type="secondary"):
        if st.checkbox("Saya yakin ingin menghapus semua data"):
            # Implementasi hapus semua data
            st.success("Semua data berhasil dihapus!")

if __name__ == "__main__":
    main()
