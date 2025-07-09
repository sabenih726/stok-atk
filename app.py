# streamlit_inventory_app_modern.py
"""
Modern Streamlit implementation of "Stok ATK Kantor" dengan tampilan yang lebih
menarik, full page, dan user experience yang lebih baik.

Dependencies
------------
    pip install streamlit pandas plotly
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, date, timedelta
from typing import List
import json

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB = "inventory.db"

# ------------------ Custom CSS untuk tampilan modern ------------------
def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Global Styling */
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Main container - full width */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    /* Custom buttons */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: 2px solid #e9ecef;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-color: #667eea;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        border-radius: 8px;
        padding: 1rem;
        font-weight: 500;
    }
    
    .stError {
        background: linear-gradient(45deg, #dc3545, #e74c3c);
        color: white;
        border-radius: 8px;
        padding: 1rem;
        font-weight: 500;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e9ecef;
        padding: 0.5rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Chart containers */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        text-align: center;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .status-high {
        background: #d4edda;
        color: #155724;
    }
    
    .status-medium {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-low {
        background: #f8d7da;
        color: #721c24;
    }
    
    .status-empty {
        background: #f5c6cb;
        color: #721c24;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# ------------------ DB helpers ------------------
def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)

def init_db() -> None:
    """Create tables if not exist."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id TEXT UNIQUE,
                name TEXT,
                category TEXT,
                stock INTEGER,
                min_stock INTEGER DEFAULT 10,
                price REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                qty INTEGER,
                action TEXT,
                tdate DATE,
                note TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
            """
        )
        conn.commit()

# ------------- Enhanced CRUD operations -------------
def fetch_items(search: str = "") -> pd.DataFrame:
    with get_conn() as conn:
        if search:
            return pd.read_sql(
                """SELECT *, 
                   CASE 
                       WHEN stock = 0 THEN 'Habis'
                       WHEN stock <= min_stock THEN 'Rendah'
                       WHEN stock <= min_stock * 2 THEN 'Sedang'
                       ELSE 'Tinggi'
                   END as status
                   FROM items 
                   WHERE name LIKE ? OR material_id LIKE ?
                   ORDER BY name""",
                conn,
                params=(f"%{search}%", f"%{search}%", f"%{search}%"),
            )
        return pd.read_sql(
            """SELECT *, 
               CASE 
                   WHEN stock = 0 THEN 'Habis'
                   WHEN stock <= min_stock THEN 'Rendah'
                   WHEN stock <= min_stock * 2 THEN 'Sedang'
                   ELSE 'Tinggi'
               END as status
               FROM items 
               ORDER BY name""", 
            conn
        )

def upsert_item(material_id: str, name: str, category: str, stock: int, min_stock: int = 10, price: float = 0):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM items WHERE material_id = ?", (material_id,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE items SET name=?, category=?, stock=?, min_stock=?, price=? WHERE material_id=?",
                (name, category, stock, min_stock, price, material_id),
            )
        else:
            cur.execute(
                "INSERT INTO items (material_id,name,category,stock,min_stock,price) VALUES (?,?,?,?,?,?,?)",
                (material_id, name, category, stock, min_stock, price),
            )
        conn.commit()

def delete_item(material_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM transactions WHERE item_id = (SELECT id FROM items WHERE material_id=?)", (material_id,))
        conn.execute("DELETE FROM items WHERE material_id = ?", (material_id,))
        conn.commit()

def add_transaction(material_id: str, qty: int, action: str, note: str = ""):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, stock FROM items WHERE material_id = ?", (material_id,))
        row = cur.fetchone()
        if not row:
            st.error("❌ Barang tidak ditemukan.")
            return False
        item_id, curr_stock = row
        new_stock = curr_stock + qty if action == "masuk" else curr_stock - qty
        if new_stock < 0:
            st.error("❌ Stok tidak mencukupi!")
            return False
        cur.execute(
            "INSERT INTO transactions (item_id, qty, action, tdate, note) VALUES (?,?,?,?,?)",
            (item_id, qty, action, date.today(), note),
        )
        cur.execute("UPDATE items SET stock = ? WHERE id = ?", (new_stock, item_id))
        conn.commit()
        return True

def fetch_transactions(limit: int | None = None) -> pd.DataFrame:
    with get_conn() as conn:
        query = """SELECT t.id, i.material_id, i.name, t.qty, t.action, t.tdate, t.note
                   FROM transactions t JOIN items i ON t.item_id = i.id
                   ORDER BY t.id DESC"""
        if limit:
            query += f" LIMIT {limit}"
        return pd.read_sql(query, conn)

def get_dashboard_stats():
    with get_conn() as conn:
        # Total items
        total_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        
        # Low stock items
        low_stock = conn.execute("SELECT COUNT(*) FROM items WHERE stock <= min_stock").fetchone()[0]
        
        # Total value
        total_value = conn.execute("SELECT SUM(stock * price) FROM items").fetchone()[0] or 0
        
        # Monthly transactions
        monthly_trans = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE tdate >= ?", 
            (date.today().replace(day=1),)
        ).fetchone()[0]
        
        return {
            'total_items': total_items,
            'low_stock': low_stock,
            'total_value': total_value,
            'monthly_trans': monthly_trans
        }

def get_category_stats():
    with get_conn() as conn:
        return pd.read_sql(
            "SELECT category, COUNT(*) as count, SUM(stock) as total_stock FROM items GROUP BY category",
            conn
        )

def get_stock_trend():
    with get_conn() as conn:
        return pd.read_sql(
            """SELECT DATE(tdate) as date, 
                      SUM(CASE WHEN action = 'masuk' THEN qty ELSE -qty END) as net_change
               FROM transactions 
               WHERE tdate >= ? 
               GROUP BY DATE(tdate) 
               ORDER BY date""",
            conn,
            params=(date.today() - timedelta(days=30),)
        )

# ----------------- Enhanced UI -----------------
def main():
    try:
        st.set_page_config(
            page_title="Stok ATK Kantor",
            page_icon="📦",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        load_custom_css()
        init_db()
        
        # Show notifications
        show_notifications()
        
        # Header
        st.markdown("""
        <div class="main-header">
            <h1>📦 Sistem Manajemen Stok ATK</h1>
            <p>Kelola inventaris alat tulis kantor dengan mudah dan efisien</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar
        with st.sidebar:
            st.markdown("### 🎯 Menu Navigasi")
            MENU = st.radio(
                "Pilih Menu:",
                ["📊 Dashboard", "🛒 Transaksi", "📦 Data Barang", "📜 Riwayat", "⚙️ Pengaturan"],
                index=0
            )
            
            st.markdown("---")
            
            # Quick stats in sidebar
            stats = get_dashboard_stats()
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>📊 Ringkasan</h4>
                <p><strong>Total Item:</strong> {stats['total_items']}</p>
                <p><strong>Stok Rendah:</strong> {stats['low_stock']}</p>
                <p><strong>Nilai Total:</strong> Rp {stats['total_value']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Template download
            add_template_download()
            
            st.markdown("---")
            
            # Import Excel - PERBAIKAN UTAMA
            st.markdown("### 📁 Import Data")
            excel_file = st.file_uploader(
                "Upload file Excel (.xlsx/.xls)",
                type=["xlsx", "xls"],
                help="File harus memiliki kolom: material_id, name, category, stock"
            )
            
            if excel_file and st.button("🚀 Import ke Database"):
                try:
                    # Baca file Excel
                    df_xl = pd.read_excel(excel_file)
                    
                    # Debug: tampilkan informasi file
                    st.info(f"📋 File memiliki {len(df_xl.columns)} kolom dan {len(df_xl)} baris")
                    st.info(f"📋 Kolom yang ditemukan: {', '.join(df_xl.columns.tolist())}")
                    
                    # Normalisasi nama kolom (lowercase, strip spaces)
                    df_xl.columns = df_xl.columns.str.lower().str.strip()
                    
                    # Kolom yang diperlukan
                    required_cols = {"material_id", "name", "category", "stock"}
                    available_cols = set(df_xl.columns)
                    
                    # Cek kolom yang diperlukan
                    missing_cols = required_cols - available_cols
                    if missing_cols:
                        st.error(f"❌ Kolom yang hilang: {', '.join(missing_cols)}")
                        st.error(f"❌ Kolom yang tersedia: {', '.join(available_cols)}")
                        return
                    
                    # Hapus baris yang kosong
                    df_xl = df_xl.dropna(subset=['material_id', 'name'], how='any')
                    
                    if df_xl.empty:
                        st.error("❌ Tidak ada data valid untuk diimport")
                        return
                    
                    # Proses import
                    imported = 0
                    errors = []
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    total_rows = len(df_xl)
                    
                    for idx, row in df_xl.iterrows():
                        try:
                            # Ambil data dengan default values
                            material_id = str(row.get("material_id", "")).strip()
                            name = str(row.get("name", "")).strip()
                            category = str(row.get("category", "")).strip()
                            
                            # Validasi data wajib
                            if not material_id or not name or not category:
                                raise ValueError("material_id, name, dan category tidak boleh kosong")
                            
                            # Konversi numerik dengan validasi
                            try:
                                stock = int(float(row.get("stock", 0)))
                            except (ValueError, TypeError):
                                stock = 0
                            
                            try:
                                min_stock = int(float(row.get("min_stock", 10)))
                            except (ValueError, TypeError):
                                min_stock = 10
                            
                            try:
                                price = float(row.get("price", 0))
                            except (ValueError, TypeError):
                                price = 0.0
                            
                            # Validasi nilai
                            if stock < 0:
                                stock = 0
                            if min_stock < 0:
                                min_stock = 10
                            if price < 0:
                                price = 0.0
                            
                            # Import ke database
                            upsert_item(
                                material_id=material_id,
                                name=name,
                                category=category,
                                stock=stock,
                                min_stock=min_stock,
                                price=price
                            )
                            
                            imported += 1
                            
                        except Exception as e:
                            error_msg = f"Baris {idx+2}: {str(e)}"
                            errors.append(error_msg)
                            log_error(error_msg, "import_excel")
                        
                        # Update progress
                        progress_bar.progress((idx + 1) / total_rows)
                    
                    # Hasil import
                    if imported > 0:
                        st.success(f"✅ Berhasil import {imported} item dari {total_rows} baris!")
                    
                    if errors:
                        st.warning(f"⚠️ {len(errors)} item gagal diimport:")
                        # Tampilkan detail error dalam expander
                        with st.expander("📋 Detail Error"):
                            for error in errors[:10]:  # Tampilkan 10 error pertama
                                st.caption(f"• {error}")
                            if len(errors) > 10:
                                st.caption(f"... dan {len(errors) - 10} error lainnya")
                    
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Gagal membaca file Excel: {str(e)}"
                    st.error(f"❌ {error_msg}")
                    log_error(error_msg, "import_excel_main")
                    
                    # Saran perbaikan
                    st.markdown("""
                    **💡 Saran Perbaikan:**
                    - Pastikan file Excel tidak corrupt
                    - Periksa format kolom (tidak ada merge cell)
                    - Download template Excel dan ikuti formatnya
                    - Pastikan tidak ada karakter khusus pada nama kolom
                    """)
        
        # Main content based on menu selection
        if MENU == "📊 Dashboard":
            show_dashboard()
        elif MENU == "🛒 Transaksi":
            show_transaction_page()
        elif MENU == "📦 Data Barang":
            show_items_page()
        elif MENU == "📜 Riwayat":
            show_history_page()
        elif MENU == "⚙️ Pengaturan":
            show_settings_page()
            
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan sistem: {str(e)}")
        log_error(str(e), "main_function")

# Fungsi tambahan untuk validasi data Excel
def validate_excel_data(df):
    """Validasi data Excel sebelum import"""
    errors = []
    
    # Cek duplikasi material_id
    if 'material_id' in df.columns:
        duplicates = df[df['material_id'].duplicated(keep=False)]
        if not duplicates.empty:
            for idx in duplicates.index:
                errors.append(f"Baris {idx+2}: Material ID '{duplicates.loc[idx, 'material_id']}' sudah ada")
    
    # Cek format data
    for idx, row in df.iterrows():
        row_errors = []
        
        # Cek material_id
        if pd.isna(row.get('material_id')) or str(row.get('material_id')).strip() == '':
            row_errors.append("Material ID kosong")
        
        # Cek name
        if pd.isna(row.get('name')) or str(row.get('name')).strip() == '':
            row_errors.append("Nama barang kosong")
        
        # Cek category
        if pd.isna(row.get('category')) or str(row.get('category')).strip() == '':
            row_errors.append("Kategori kosong")
        
        # Cek stock format
        try:
            stock = row.get('stock', 0)
            if pd.isna(stock):
                row_errors.append("Stok kosong")
            else:
                stock_val = float(stock)
                if stock_val < 0:
                    row_errors.append("Stok tidak boleh negatif")
        except (ValueError, TypeError):
            row_errors.append("Format stok tidak valid")
        
        if row_errors:
            errors.append(f"Baris {idx+2}: {', '.join(row_errors)}")
    
    return errors

# Perbaikan fungsi upsert_item untuk handle error yang lebih baik
def upsert_item(material_id, name, category, stock, min_stock=10, price=0.0):
    """Insert or update item dengan error handling yang lebih baik"""
    try:
        # Validasi input
        if not material_id or not name or not category:
            raise ValueError("material_id, name, dan category tidak boleh kosong")
        
        # Sanitasi input
        material_id = str(material_id).strip()
        name = str(name).strip()
        category = str(category).strip()
        stock = int(stock)
        min_stock = int(min_stock)
        price = float(price)
        
        # Validasi range
        if stock < 0:
            raise ValueError("Stok tidak boleh negatif")
        if min_stock < 0:
            raise ValueError("Minimum stok tidak boleh negatif")
        if price < 0:
            raise ValueError("Harga tidak boleh negatif")
        
        # Hitung status
        if stock == 0:
            status = "Habis"
        elif stock <= min_stock:
            status = "Rendah"
        elif stock <= min_stock * 2:
            status = "Sedang"
        else:
            status = "Aman"
        
        # Database operation
        with get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO items 
                (material_id, name, category, stock, min_stock, price, status, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (material_id, name, category, stock, min_stock, price, status))
            conn.commit()
        
        return True
        
    except Exception as e:
        log_error(f"Error in upsert_item: {str(e)}", "upsert_item")
        raise e

# Fungsi untuk membersihkan data Excel
def clean_excel_data(df):
    """Membersihkan data Excel dari karakter yang tidak diinginkan"""
    # Hapus baris yang semuanya kosong
    df = df.dropna(how='all')
    
    # Bersihkan kolom string
    string_cols = ['material_id', 'name', 'category']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', '')
    
    # Bersihkan kolom numerik
    numeric_cols = ['stock', 'min_stock', 'price']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# Perbaikan fungsi export_to_template
def export_to_template():
    """Create Excel template dengan instruksi yang lebih jelas"""
    template_data = {
        'material_id': ['ATK001', 'ATK002', 'ATK003', 'ATK004', 'ATK005'],
        'name': ['Pulpen Pilot Hitam', 'Kertas A4 70gsm', 'Stapler Joyko HD-10', 'Penghapus Steadtler', 'Spidol Snowman'],
        'category': ['Alat Tulis', 'Kertas', 'Alat Kantor', 'Alat Tulis', 'Alat Tulis'],
        'stock': [50, 100, 10, 25, 30],
        'min_stock': [10, 20, 5, 5, 10],
        'price': [5000, 50000, 75000, 3000, 8000]
    }
    
    df_template = pd.DataFrame(template_data)
    
    from io import BytesIO
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet template
        df_template.to_excel(writer, sheet_name='Template', index=False)
        
        # Sheet instruksi
        instructions = pd.DataFrame({
            'No': [1, 2, 3, 4, 5, 6],
            'Kolom': ['material_id', 'name', 'category', 'stock', 'min_stock', 'price'],
            'Deskripsi': [
                'ID unik untuk setiap barang (contoh: ATK001, KRT001)',
                'Nama lengkap barang',
                'Kategori: Alat Tulis, Kertas, atau Alat Kantor',
                'Jumlah stok saat ini (angka)',
                'Batas minimum stok untuk alert (angka)',
                'Harga per unit dalam rupiah (angka)'
            ],
            'Wajib': ['Ya', 'Ya', 'Ya', 'Ya', 'Tidak', 'Tidak'],
            'Contoh': ['ATK001', 'Pulpen Pilot Hitam', 'Alat Tulis', '50', '10', '5000']
        })
        instructions.to_excel(writer, sheet_name='Instruksi', index=False)
        
        # Sheet validasi
        validation_rules = pd.DataFrame({
            'Aturan': [
                'Material ID harus unik',
                'Nama barang tidak boleh kosong',
                'Kategori harus salah satu: Alat Tulis, Kertas, Alat Kantor',
                'Stok harus angka positif atau 0',
                'Min stock harus angka positif',
                'Harga harus angka positif atau 0'
            ],
            'Contoh_Benar': [
                'ATK001, KRT001, ALK001',
                'Pulpen Pilot Hitam',
                'Alat Tulis',
                '50',
                '10',
                '5000'
            ],
            'Contoh_Salah': [
                'Duplikat: ATK001, ATK001',
                'Kosong atau hanya spasi',
                'Tulis Alat (salah kategori)',
                '-5 (negatif)',
                '-10 (negatif)',
                '-1000 (negatif)'
            ]
        })
        validation_rules.to_excel(writer, sheet_name='Validasi', index=False)
    
    return output.getvalue()

# Enhanced error handling dan logging
def log_error(error_msg, function_name):
    """Enhanced error logging dengan timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_log = f"[{timestamp}] ERROR in {function_name}: {error_msg}\n"
        
        # Write to error log file
        with open("error_log.txt", "a", encoding='utf-8') as f:
            f.write(error_log)
    except Exception:
        pass  # Jangan sampai error logging mengganggu proses utama

# Fungsi untuk membersihkan log error
def clear_error_log():
    """Membersihkan file log error"""
    try:
        if os.path.exists("error_log.txt"):
            os.remove("error_log.txt")
        return True
    except Exception:
        return False

# Add notification system
def show_notifications():
    """Show system notifications"""
    stats = get_dashboard_stats()
    
    if stats['low_stock'] > 0:
        st.warning(f"⚠️ {stats['low_stock']} item memiliki stok rendah!")
    
    # Check for items with zero stock
    with get_conn() as conn:
        zero_stock = conn.execute("SELECT COUNT(*) FROM items WHERE stock = 0").fetchone()[0]
        if zero_stock > 0:
            st.error(f"❌ {zero_stock} item habis stok!")

# Enhanced main function with error handling
def main():
    try:
        st.set_page_config(
            page_title="Stok ATK Kantor",
            page_icon="📦",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        load_custom_css()
        init_db()
        
        # Show notifications
        show_notifications()
        
        # Header
        st.markdown("""
        <div class="main-header">
            <h1>Manajemen Stok ATK</h1>
            <p>Sistem Automation Keluar Masuk ATK</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar
        with st.sidebar:
            st.markdown("### 🎯 Menu Navigasi")
            MENU = st.radio(
                "Pilih Menu:",
                ["📊 Dashboard", "🛒 Transaksi", "📦 Data Barang", "📜 Riwayat", "⚙️ Pengaturan"],
                index=0
            )
            
            st.markdown("---")
            
            # Quick stats in sidebar
            stats = get_dashboard_stats()
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>📊 Ringkasan</h4>
                <p><strong>Total Item:</strong> {stats['total_items']}</p>
                <p><strong>Stok Rendah:</strong> {stats['low_stock']}</p>
                <p><strong>Nilai Total:</strong> Rp {stats['total_value']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Template download
            add_template_download()
            
            st.markdown("---")
            
            # Import Excel
            st.markdown("### 📁 Import Data")
            excel_file = st.file_uploader(
                "Upload file Excel (.xlsx/.xls)",
                type=["xlsx", "xls"],
                help="File harus memiliki kolom: material_id, name, category, stock"
            )
            
            if excel_file and st.button("🚀 Import ke Database"):
                try:
                    df_xl = pd.read_excel(excel_file)
                    required = {"material_id", "name", "category", "stock"}
                    
                    if not required.issubset({c.lower() for c in df_xl.columns}):
                        st.error(f"❌ Header Excel harus memuat: {', '.join(required)}")
                    else:
                        imported = 0
                        errors = []
                        
                        for idx, row in df_xl.iterrows():
                            try:
                                upsert_item(
                                    material_id = str(row.get("material_id", "")).strip(),
                                    name = str(row.get("name", "")).strip(),
                                    category = str(row.get("category", "")).strip(),
                                    stock = int(row["stock"]),
                                    min_stock = int(row.get("min_stock", 10)),
                                    price = float(row.get("price", 0))
                                )
                                imported += 1
                            except Exception as e:
                                error_msg = f"Baris {idx+2}: {str(e)}"
                                errors.append(error_msg)
                                log_error(error_msg, "import_excel")
                        
                        if imported > 0:
                            st.success(f"✅ Berhasil import {imported} item!")
                        
                        if errors:
                            st.warning(f"⚠️ {len(errors)} item gagal diimport:")
                            for error in errors[:5]:  # Show first 5 errors
                                st.caption(error)
                        
                        st.rerun()
                        
                except Exception as e:
                    error_msg = f"Gagal import: {str(e)}"
                    st.error(f"❌ {error_msg}")
                    log_error(error_msg, "import_excel")
        
        # Main content based on menu selection
        if MENU == "📊 Dashboard":
            show_dashboard()
        elif MENU == "🛒 Transaksi":
            show_transaction_page()
        elif MENU == "📦 Data Barang":
            show_items_page()
        elif MENU == "📜 Riwayat":
            show_history_page()
        elif MENU == "⚙️ Pengaturan":
            show_settings_page()
            
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan sistem: {str(e)}")
        log_error(str(e), "main")

if __name__ == "__main__":
    main()
