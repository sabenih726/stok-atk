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
    st.set_page_config(
        page_title="Stok ATK Kantor",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    load_custom_css()
    init_db()
    
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
        
        # Import Excel
        st.markdown("### 📁 Import Data")
        excel_file = st.file_uploader(
            "Upload file Excel (.xlsx/.xls)",
            type=["xlsx", "xls"],
            help="File harus memiliki kolom: material_id, name, brand, category, stock"
        )
        
        if excel_file and st.button("🚀 Import ke Database"):
            try:
                df_xl = pd.read_excel(excel_file)
                required = {"material_id", "name", "brand", "category", "stock"}
                
                if not required.issubset({c.lower() for c in df_xl.columns}):
                    st.error(f"❌ Header Excel harus memuat: {', '.join(required)}")
                else:
                    imported = 0
                    for _, row in df_xl.iterrows():
                        try:
                            upsert_item(
                                str(row["material_id"]).strip(),
                                str(row["name"]).strip(),
                                str(row["category"]).strip(),
                                int(row["stock"]),
                                int(row.get("min_stock", 10)),
                                float(row.get("price", 0))
                            )
                            imported += 1
                        except Exception as e:
                            st.warning(f"⚠️ Error pada baris {imported+1}: {e}")
                    
                    st.success(f"✅ Berhasil import {imported} item!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Gagal import: {e}")
    
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

def show_dashboard():
    st.markdown("## 📊 Dashboard Overview")
    
    # Key metrics
    stats = get_dashboard_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Item",
            value=stats['total_items'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="⚠️ Stok Rendah",
            value=stats['low_stock'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="💰 Total Nilai",
            value=f"Rp {stats['total_value']:,.0f}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="📈 Transaksi Bulan Ini",
            value=stats['monthly_trans'],
            delta=None
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Distribusi per Kategori")
        category_stats = get_category_stats()
        if not category_stats.empty:
            fig = px.pie(
                category_stats,
                values='count',
                names='category',
                title="Jumlah Item per Kategori"
            )
            fig.update_layout(
                showlegend=True,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📝 Belum ada data untuk ditampilkan")
    
    with col2:
        st.markdown("### 📈 Trend Stok (30 hari)")
        trend_data = get_stock_trend()
        if not trend_data.empty:
            fig = px.line(
                trend_data,
                x='date',
                y='net_change',
                title="Perubahan Stok Harian"
            )
            fig.update_layout(
                xaxis_title="Tanggal",
                yaxis_title="Perubahan Stok",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📝 Belum ada data transaksi")
    
    # Items with low stock
    st.markdown("### ⚠️ Item dengan Stok Rendah")
    df_items = fetch_items()
    if not df_items.empty:
        low_stock_items = df_items[df_items['stock'] <= df_items['min_stock']]
        if not low_stock_items.empty:
            st.dataframe(
                low_stock_items[['material_id', 'name', 'category', 'stock', 'min_stock', 'status']],
                use_container_width=True
            )
        else:
            st.success("✅ Semua item memiliki stok yang cukup!")
    else:
        st.info("📝 Belum ada data barang")

def show_transaction_page():
    st.markdown("## 🛒 Transaksi Barang Masuk/Keluar")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Transaction form
        with st.form("transaction_form"):
            st.markdown("### 📝 Form Transaksi")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                search = st.text_input("🔍 Cari barang (nama/merk/ID)")
                material_id = st.text_input("📋 Material ID")
                qty = st.number_input("📊 Jumlah", min_value=1, step=1)
            
            with col_b:
                action = st.selectbox("⚡ Aksi", ["masuk", "keluar"])
                note = st.text_area("📝 Catatan (opsional)", height=100)
            
            submitted = st.form_submit_button("✅ Submit Transaksi")
            
            if 'submitted_transaction' not in st.session_state:
                st.session_state.submitted_transaction = False
                            
            if submitted and not st.session_state.submitted_transaction:
                st.session_state.submitted_transaction = True  # Set flag agar tidak submit ulang
                
                if material_id and qty:
                    if add_transaction(material_id, int(qty), action, note):
                        st.success("✅ Transaksi berhasil dicatat!")
                        st.rerun()
                else:
                    st.error("❌ Material ID dan jumlah harus diisi!")
    
    with col2:
        # Quick search results
        if 'search' in locals() and search:
            st.markdown("### 🔍 Hasil Pencarian")
            df_search = fetch_items(search)
            if not df_search.empty:
                st.dataframe(
                    df_search[["material_id", "name", "stock", "status"]],
                    use_container_width=True,
                    height=200
                )
            else:
                st.info("📝 Tidak ada hasil yang ditemukan")
    
    # Recent transactions
    st.markdown("### 📜 Transaksi Terbaru")
    df_recent = fetch_transactions(10)
    if not df_recent.empty:
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("📝 Belum ada transaksi")

def show_items_page():
    st.markdown("## 📦 Data Barang")
    
    tab1, tab2 = st.tabs(["📋 Daftar Barang", "➕ Tambah/Edit Barang"])
    
    with tab1:
        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Cari barang...")
        with col2:
            category_filter = st.selectbox(
                "📂 Filter Kategori",
                ["Semua", "Alat Tulis", "Kertas", "Alat Kantor"]
            )
        
        # Fetch and display items
        df_items = fetch_items(search)
        
        if not df_items.empty:
            if category_filter != "Semua":
                df_items = df_items[df_items['category'] == category_filter]
            
            # Add status styling
            def style_status(val):
                if val == 'Habis':
                    return 'background-color: #f8d7da; color: #721c24;'
                elif val == 'Rendah':
                    return 'background-color: #fff3cd; color: #856404;'
                elif val == 'Sedang':
                    return 'background-color: #cce5ff; color: #004085;'
                else:
                    return 'background-color: #d4edda; color: #155724;'
            
            styled_df = df_items.style.applymap(style_status, subset=['status'])
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                height=400
            )
        else:
            st.info("📝 Belum ada data barang")
    
    with tab2:
        with st.form("item_form"):
            st.markdown("### 📝 Form Tambah/Edit Barang")
            
            col1, col2 = st.columns(2)
            
            with col1:
                material_id = st.text_input("📋 Material ID*", help="ID unik untuk barang")
                name = st.text_input("📝 Nama Barang*")
                brand = st.text_input("🏷️ Merk*")
                category = st.selectbox("📂 Kategori", 
                    ["Alat Tulis", "Kertas", "Alat Kantor"])
            
            with col2:
                stock = st.number_input("📊 Stok Awal", min_value=0, step=1)
                min_stock = st.number_input("⚠️ Stok Minimum", min_value=0, step=1, value=10)
                price = st.number_input("💰 Harga Satuan", min_value=0.0, step=1000.0)
            
            submitted = st.form_submit_button("💾 Simpan Barang")
            
            if submitted:
                if material_id and name and brand:
                    upsert_item(material_id, name, brand, category, int(stock), int(min_stock), float(price))
                    st.success("✅ Data barang berhasil disimpan!")
                    st.rerun()
                else:
                    st.error("❌ Material ID, Nama, dan Merk wajib diisi!")
        
        # Delete item
        st.markdown("---")
        st.markdown("### 🗑️ Hapus Barang")
        
        with st.form("delete_form"):
            del_material = st.text_input("📋 Material ID yang akan dihapus")
            delete_submitted = st.form_submit_button("🗑️ Hapus Barang", type="secondary")
            
            if delete_submitted and del_material:
                if st.button("⚠️ Konfirmasi Hapus"):
                    delete_item(del_material)
                    st.success("✅ Barang berhasil dihapus!")
                    st.rerun()

def show_history_page():
    st.markdown("## 📜 Riwayat Transaksi")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_from = st.date_input("📅 Dari Tanggal", value=date.today() - timedelta(days=30))
    
    with col2:
        date_to = st.date_input("📅 Sampai Tanggal", value=date.today())
    
    with col3:
        action_filter = st.selectbox("⚡ Filter Aksi", ["Semua", "masuk", "keluar"])
    
    # Fetch transactions
    df_trans = fetch_transactions()
    
    if not df_trans.empty:
        # Apply filters
        df_trans['tdate'] = pd.to_datetime(df_trans['tdate'])
        df_filtered = df_trans[
            (df_trans['tdate'] >= pd.to_datetime(date_from)) &
            (df_trans['tdate'] <= pd.to_datetime(date_to))
        ]
        
        if action_filter != "Semua":
            df_filtered = df_filtered[df_filtered['action'] == action_filter]
        
        # Display data
        st.dataframe(df_filtered, use_container_width=True)
        
        # Export button
        if not df_filtered.empty:
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"riwayat_transaksi_{date.today()}.csv",
                mime="text/csv"
            )
        
        # Transaction summary
        st.markdown("### 📊 Ringkasan Transaksi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            masuk_count = len(df_filtered[df_filtered['action'] == 'masuk'])
            keluar_count = len(df_filtered[df_filtered['action'] == 'keluar'])
            
            st.metric("📥 Transaksi Masuk", masuk_count)
            st.metric("📤 Transaksi Keluar", keluar_count)
        
        with col2:
            if not df_filtered.empty:
                summary_chart = px.bar(
                    df_filtered.groupby('action').size().reset_index(name='count'),
                    x='action',
                    y='count',
                    title="Jumlah Transaksi per Jenis"
                )
                st.plotly_chart(summary_chart, use_container_width=True)
    else:
        st.info("📝 Belum ada data transaksi")

def show_settings_page():
    st.markdown("## ⚙️ Pengaturan Sistem")
    
    tab1, tab2 = st.tabs(["🔧 Konfigurasi", "📊 Statistik Database"])
    
    with tab1:
        st.markdown("### 🔧 Pengaturan Umum")
        
        # Backup database
        st.markdown("#### 💾 Backup Database")
        if st.button("📥 Download Backup Database"):
            with open(DB, 'rb') as f:
                st.download_button(
                    label="📥 Download Database",
                    data=f.read(),
                    file_name=f"inventory_backup_{date.today()}.db",
                    mime="application/octet-stream"
                )
        
        # Reset data
        st.markdown("#### ⚠️ Reset Data")
        st.warning("⚠️ Tindakan ini akan menghapus semua data!")
        
        if st.button("🗑️ Reset Database", type="secondary"):
            if st.button("⚠️ Konfirmasi Reset"):
                os.remove(DB)
                init_db()
                st.success("✅ Database berhasil direset!")
                st.rerun()
        
        # Export data
        st.markdown("#### 📤 Export Data")
        export_format = st.selectbox("Format Export", ["CSV", "Excel", "JSON"])
        
        if st.button("📤 Export Data Barang"):
            df_items = fetch_items()
            if not df_items.empty:
                if export_format == "CSV":
                    csv = df_items.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"data_barang_{date.today()}.csv",
                        mime="text/csv"
                    )
                elif export_format == "Excel":
                    # Create Excel file in memory
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_items.to_excel(writer, sheet_name='Data Barang', index=False)
                        df_trans = fetch_transactions()
                        if not df_trans.empty:
                            df_trans.to_excel(writer, sheet_name='Transaksi', index=False)
                    
                    st.download_button(
                        label="📥 Download Excel",
                        data=output.getvalue(),
                        file_name=f"data_inventory_{date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                elif export_format == "JSON":
                    json_data = df_items.to_json(orient='records', indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name=f"data_barang_{date.today()}.json",
                        mime="application/json"
                    )
            else:
                st.warning("⚠️ Tidak ada data untuk diekspor")
    
    with tab2:
        st.markdown("### 📊 Statistik Database")
        
        # Database statistics
        stats = get_database_stats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📦 Total Items", stats['total_items'])
            st.metric("📊 Total Transaksi", stats['total_transactions'])
            st.metric("💰 Total Nilai Inventory", f"Rp {stats['total_value']:,.0f}")
        
        with col2:
            st.metric("📂 Jumlah Kategori", stats['total_categories'])
            st.metric("📈 Rata-rata Stok", f"{stats['avg_stock']:.1f}")
            st.metric("💾 Ukuran Database", f"{stats['db_size']:.2f} MB")
        
        # Top items by value
        st.markdown("### 💰 Top Items by Value")
        top_items = get_top_items_by_value()
        if not top_items.empty:
            fig = px.bar(
                top_items.head(10),
                x='total_value',
                y='name',
                orientation='h',
                title="Top 10 Items by Total Value"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Category distribution
        st.markdown("### 📊 Distribusi Stok per Kategori")
        category_stats = get_category_stats()
        if not category_stats.empty:
            fig = px.bar(
                category_stats,
                x='category',
                y='total_stock',
                title="Total Stok per Kategori"
            )
            st.plotly_chart(fig, use_container_width=True)

def get_database_stats():
    """Get comprehensive database statistics"""
    with get_conn() as conn:
        # Total items
        total_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        
        # Total transactions
        total_transactions = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        
        # Total value
        total_value = conn.execute("SELECT SUM(stock * price) FROM items").fetchone()[0] or 0
        
        # Total categories
        total_categories = conn.execute("SELECT COUNT(DISTINCT category) FROM items").fetchone()[0]
        
        # Average stock
        avg_stock = conn.execute("SELECT AVG(stock) FROM items").fetchone()[0] or 0
        
        # Database size
        db_size = os.path.getsize(DB) / (1024 * 1024)  # Convert to MB
        
        return {
            'total_items': total_items,
            'total_transactions': total_transactions,
            'total_value': total_value,
            'total_categories': total_categories,
            'avg_stock': avg_stock,
            'db_size': db_size
        }

def get_top_items_by_value():
    """Get top items by total value (stock * price)"""
    with get_conn() as conn:
        return pd.read_sql(
            """SELECT name, category, stock, price, 
                      (stock * price) as total_value
               FROM items 
               WHERE price > 0 
               ORDER BY total_value DESC""",
            conn
        )

def export_to_template():
    """Create Excel template for import"""
    template_data = {
        'material_id': ['ATK001', 'ATK002', 'ATK003'],
        'name': ['Pulpen Pilot', 'Kertas A4', 'Stapler Joyko'],
        'category': ['Alat Tulis', 'Kertas', 'Alat Kantor'],
        'stock': [50, 100, 10],
        'min_stock': [10, 20, 5],
        'price': [5000, 50000, 75000]
    }
    
    df_template = pd.DataFrame(template_data)
    
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, sheet_name='Template', index=False)
        
        # Add instructions sheet
        instructions = pd.DataFrame({
            'Field': ['material_id', 'name', 'category', 'stock', 'min_stock', 'price'],
            'Description': [
                'ID unik untuk setiap barang (wajib diisi)',
                'Nama barang (wajib diisi)',
                'Kategori barang (wajib diisi)',
                'Jumlah stok awal (wajib diisi)',
                'Stok minimum untuk alert (opsional, default: 10)',
                'Harga per unit (opsional, default: 0)'
            ],
            'Required': ['Ya', 'Ya', 'Ya', 'Ya', 'Ya', 'Tidak', 'Tidak']
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
    
    return output.getvalue()

# Add template download to sidebar
def add_template_download():
    """Add template download option to sidebar"""
    st.markdown("### 📋 Template Import")
    if st.button("📥 Download Template Excel"):
        template_data = export_to_template()
        st.download_button(
            label="📥 Download Template",
            data=template_data,
            file_name=f"template_import_inventory.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Enhanced error handling and logging
def log_error(error_msg, function_name):
    """Simple error logging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_log = f"[{timestamp}] ERROR in {function_name}: {error_msg}\n"
    
    # Write to error log file
    with open("error_log.txt", "a") as f:
        f.write(error_log)

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
                                    str(row["material_id"]).strip(),
                                    str(row["name"]).strip(),
                                    str(row["category"]).strip(),
                                    int(row["stock"]),
                                    int(row.get("min_stock", 10)),
                                    float(row.get("price", 0))
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
