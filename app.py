import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Inventory ATK",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi session state
if 'inventory_data' not in st.session_state:
    st.session_state.inventory_data = pd.DataFrame({
        'kode_barang': ['ATK001', 'ATK002', 'ATK003', 'ATK004', 'ATK005', 'ATK006'],
        'nama_barang': ['Pulpen Pilot', 'Kertas A4 70gsm', 'Stapler Kenko', 'Penghapus Faber Castell', 'Spidol Snowman', 'Klip Kertas'],
        'kategori': ['Alat Tulis', 'Kertas', 'Alat Kantor', 'Alat Tulis', 'Alat Tulis', 'Alat Kantor'],
        'stok_tersedia': [25, 8, 5, 15, 12, 200],
        'minimum_stok': [10, 5, 3, 10, 8, 50],
        'harga_satuan': [3500, 45000, 85000, 2500, 8000, 15000],
        'supplier': ['PT ABC', 'PT XYZ', 'PT ABC', 'PT DEF', 'PT XYZ', 'PT ABC'],
        'lokasi_penyimpanan': ['Gudang A', 'Gudang B', 'Gudang A', 'Gudang A', 'Gudang A', 'Gudang B']
    })

if 'request_data' not in st.session_state:
    st.session_state.request_data = pd.DataFrame(columns=[
        'id_request', 'tanggal_request', 'nama_pemohon', 'divisi', 'kode_barang', 
        'nama_barang', 'qty_request', 'keterangan', 'status', 'tanggal_approve'
    ])

if 'transaction_history' not in st.session_state:
    st.session_state.transaction_history = pd.DataFrame(columns=[
        'tanggal', 'kode_barang', 'nama_barang', 'jenis_transaksi', 'qty', 'keterangan'
    ])

# CSS untuk styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .status-pending { background-color: #ffeaa7; padding: 4px 8px; border-radius: 4px; }
    .status-approved { background-color: #55a3ff; padding: 4px 8px; border-radius: 4px; color: white; }
    .status-rejected { background-color: #fd79a8; padding: 4px 8px; border-radius: 4px; color: white; }
    .low-stock { background-color: #ff7675; color: white; padding: 4px 8px; border-radius: 4px; }
    .normal-stock { background-color: #00b894; color: white; padding: 4px 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("📋 Sistem Inventory ATK")
menu = st.sidebar.radio("Menu Utama", [
    "🏠 Dashboard", 
    "📦 Data Inventori", 
    "📝 Form Request", 
    "✅ Approve Request", 
    "📊 Laporan & Analytics",
    "⚙️ Master Data"
])

# Fungsi helper
def generate_request_id():
    return f"REQ{datetime.now().strftime('%Y%m%d%H%M%S')}"

def add_transaction(kode_barang, nama_barang, jenis, qty, keterangan=""):
    new_transaction = pd.DataFrame({
        'tanggal': [datetime.now()],
        'kode_barang': [kode_barang],
        'nama_barang': [nama_barang],
        'jenis_transaksi': [jenis],
        'qty': [qty],
        'keterangan': [keterangan]
    })
    st.session_state.transaction_history = pd.concat([st.session_state.transaction_history, new_transaction], ignore_index=True)

def update_stock(kode_barang, qty_change):
    mask = st.session_state.inventory_data['kode_barang'] == kode_barang
    if mask.any():
        current_stock = st.session_state.inventory_data.loc[mask, 'stok_tersedia'].iloc[0]
        new_stock = current_stock + qty_change
        st.session_state.inventory_data.loc[mask, 'stok_tersedia'] = max(0, new_stock)

# DASHBOARD
if menu == "🏠 Dashboard":
    st.title("🏠 Dashboard Inventory ATK")
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    total_items = len(st.session_state.inventory_data)
    low_stock_items = len(st.session_state.inventory_data[
        st.session_state.inventory_data['stok_tersedia'] <= st.session_state.inventory_data['minimum_stok']
    ])
    pending_requests = len(st.session_state.request_data[st.session_state.request_data['status'] == 'Pending'])
    total_value = (st.session_state.inventory_data['stok_tersedia'] * st.session_state.inventory_data['harga_satuan']).sum()
    
    with col1:
        st.metric("Total Items", total_items)
    with col2:
        st.metric("Stock Menipis", low_stock_items, delta=f"-{low_stock_items}")
    with col3:
        st.metric("Pending Request", pending_requests)
    with col4:
        st.metric("Total Nilai Inventory", f"Rp {total_value:,.0f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribusi Stock per Kategori")
        category_stock = st.session_state.inventory_data.groupby('kategori')['stok_tersedia'].sum().reset_index()
        fig_pie = px.pie(category_stock, values='stok_tersedia', names='kategori', 
                        title="Stock per Kategori")
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("⚠️ Alert Stock Menipis")
        low_stock_df = st.session_state.inventory_data[
            st.session_state.inventory_data['stok_tersedia'] <= st.session_state.inventory_data['minimum_stok']
        ][['kode_barang', 'nama_barang', 'stok_tersedia', 'minimum_stok']]
        
        if len(low_stock_df) > 0:
            st.dataframe(low_stock_df, use_container_width=True)
        else:
            st.success("✅ Semua item dalam kondisi stock aman!")

    # Recent Activity
    st.subheader("📈 Aktivitas Transaksi Terakhir")
    if len(st.session_state.transaction_history) > 0:
        recent_transactions = st.session_state.transaction_history.sort_values('tanggal', ascending=False).head(10)
        st.dataframe(recent_transactions, use_container_width=True)
    else:
        st.info("Belum ada transaksi yang tercatat.")

# DATA INVENTORI
elif menu == "📦 Data Inventori":
    st.title("📦 Data Inventori ATK")
    
    # Filter dan Search
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("🔍 Cari Barang", placeholder="Masukkan nama atau kode barang...")
    with col2:
        filter_category = st.selectbox("Filter Kategori", 
                                     ['Semua'] + list(st.session_state.inventory_data['kategori'].unique()))
    with col3:
        filter_stock = st.selectbox("Filter Stock", ['Semua', 'Stock Menipis', 'Stock Aman'])
    
    # Apply filters
    filtered_data = st.session_state.inventory_data.copy()
    
    if search_term:
        filtered_data = filtered_data[
            (filtered_data['nama_barang'].str.contains(search_term, case=False)) |
            (filtered_data['kode_barang'].str.contains(search_term, case=False))
        ]
    
    if filter_category != 'Semua':
        filtered_data = filtered_data[filtered_data['kategori'] == filter_category]
    
    if filter_stock == 'Stock Menipis':
        filtered_data = filtered_data[filtered_data['stok_tersedia'] <= filtered_data['minimum_stok']]
    elif filter_stock == 'Stock Aman':
        filtered_data = filtered_data[filtered_data['stok_tersedia'] > filtered_data['minimum_stok']]
    
    # Display data dengan status stock
    def format_stock_status(row):
        if row['stok_tersedia'] <= row['minimum_stok']:
            return f'<span class="low-stock">{row["stok_tersedia"]} (Low)</span>'
        else:
            return f'<span class="normal-stock">{row["stok_tersedia"]} (OK)</span>'
    
    if len(filtered_data) > 0:
        # Tambah kolom status untuk display
        display_data = filtered_data.copy()
        display_data['Total Nilai'] = display_data['stok_tersedia'] * display_data['harga_satuan']
        
        st.dataframe(display_data.style.format({
            'harga_satuan': 'Rp {:,.0f}',
            'Total Nilai': 'Rp {:,.0f}'
        }), use_container_width=True)
    else:
        st.warning("Tidak ada data yang sesuai dengan filter.")

# FORM REQUEST
elif menu == "📝 Form Request":
    st.title("📝 Form Request ATK")
    
    with st.form("request_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nama_pemohon = st.text_input("Nama Pemohon", placeholder="Masukkan nama lengkap")
            divisi = st.selectbox("Divisi", ['IT', 'Finance', 'HR', 'Marketing', 'Operations', 'Admin'])
            
        with col2:
            selected_item = st.selectbox("Pilih Barang ATK", 
                                       options=st.session_state.inventory_data['kode_barang'] + " - " + 
                                              st.session_state.inventory_data['nama_barang'])
            qty_request = st.number_input("Jumlah Request", min_value=1, value=1)
        
        keterangan = st.text_area("Keterangan/Keperluan", placeholder="Jelaskan keperluan penggunaan...")
        
        submitted = st.form_submit_button("📤 Submit Request", use_container_width=True)
        
        if submitted:
            if nama_pemohon and selected_item:
                # Parse selected item
                kode_barang = selected_item.split(" - ")[0]
                nama_barang = selected_item.split(" - ")[1]
                
                # Check stock availability
                current_stock = st.session_state.inventory_data[
                    st.session_state.inventory_data['kode_barang'] == kode_barang
                ]['stok_tersedia'].iloc[0]
                
                if qty_request > current_stock:
                    st.error(f"❌ Stock tidak mencukupi! Stock tersedia: {current_stock}")
                else:
                    # Add to request data
                    new_request = pd.DataFrame({
                        'id_request': [generate_request_id()],
                        'tanggal_request': [datetime.now()],
                        'nama_pemohon': [nama_pemohon],
                        'divisi': [divisi],
                        'kode_barang': [kode_barang],
                        'nama_barang': [nama_barang],
                        'qty_request': [qty_request],
                        'keterangan': [keterangan],
                        'status': ['Pending'],
                        'tanggal_approve': [None]
                    })
                    
                    st.session_state.request_data = pd.concat([st.session_state.request_data, new_request], ignore_index=True)
                    st.success("✅ Request berhasil disubmit!")
                    st.rerun()
            else:
                st.error("❌ Mohon lengkapi semua field yang required!")
    
    # Display pending requests
    st.subheader("📋 Request Saya")
    if len(st.session_state.request_data) > 0:
        my_requests = st.session_state.request_data.copy()
        my_requests['tanggal_request'] = pd.to_datetime(my_requests['tanggal_request']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(my_requests, use_container_width=True)
    else:
        st.info("Belum ada request yang disubmit.")

# APPROVE REQUEST
elif menu == "✅ Approve Request":
    st.title("✅ Approval Request ATK")
    
    pending_requests = st.session_state.request_data[st.session_state.request_data['status'] == 'Pending'].copy()
    
    if len(pending_requests) > 0:
        for idx, request in pending_requests.iterrows():
            with st.expander(f"Request ID: {request['id_request']} - {request['nama_pemohon']} ({request['divisi']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Barang:** {request['nama_barang']}")
                    st.write(f"**Jumlah:** {request['qty_request']}")
                    st.write(f"**Tanggal Request:** {request['tanggal_request']}")
                    st.write(f"**Keterangan:** {request['keterangan']}")
                
                with col2:
                    current_stock = st.session_state.inventory_data[
                        st.session_state.inventory_data['kode_barang'] == request['kode_barang']
                    ]['stok_tersedia'].iloc[0]
                    st.write(f"**Stock Tersedia:** {current_stock}")
                    
                    col_approve, col_reject = st.columns(2)
                    
                    with col_approve:
                        if st.button(f"✅ Approve", key=f"approve_{idx}"):
                            if request['qty_request'] <= current_stock:
                                # Update request status
                                st.session_state.request_data.loc[idx, 'status'] = 'Approved'
                                st.session_state.request_data.loc[idx, 'tanggal_approve'] = datetime.now()
                                
                                # Update stock
                                update_stock(request['kode_barang'], -request['qty_request'])
                                
                                # Add transaction history
                                add_transaction(
                                    request['kode_barang'], 
                                    request['nama_barang'], 
                                    'Keluar', 
                                    request['qty_request'],
                                    f"Request approved untuk {request['nama_pemohon']} - {request['divisi']}"
                                )
                                
                                st.success("Request approved!")
                                st.rerun()
                            else:
                                st.error("Stock tidak mencukupi!")
                    
                    with col_reject:
                        if st.button(f"❌ Reject", key=f"reject_{idx}"):
                            st.session_state.request_data.loc[idx, 'status'] = 'Rejected'
                            st.session_state.request_data.loc[idx, 'tanggal_approve'] = datetime.now()
                            st.warning("Request rejected!")
                            st.rerun()
    else:
        st.info("🎉 Tidak ada request yang perlu di-approve.")

# LAPORAN & ANALYTICS
elif menu == "📊 Laporan & Analytics":
    st.title("📊 Laporan & Analytics")
    
    tab1, tab2, tab3 = st.tabs(["📈 Stock Analysis", "🔄 Transaction History", "👥 Request Analysis"])
    
    with tab1:
        st.subheader("Analisis Stock")
        
        # Stock value by category
        stock_value = st.session_state.inventory_data.copy()
        stock_value['total_value'] = stock_value['stok_tersedia'] * stock_value['harga_satuan']
        category_value = stock_value.groupby('kategori')['total_value'].sum().reset_index()
        
        fig_bar = px.bar(category_value, x='kategori', y='total_value', 
                        title="Nilai Stock per Kategori")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Stock turnover prediction
        st.subheader("Prediksi Kebutuhan Restok")
        st.session_state.inventory_data['days_to_empty'] = st.session_state.inventory_data['stok_tersedia'] / 2  # Asumsi konsumsi 2 unit/hari
        restock_needed = st.session_state.inventory_data[st.session_state.inventory_data['days_to_empty'] <= 30]
        
        if len(restock_needed) > 0:
            st.dataframe(restock_needed[['kode_barang', 'nama_barang', 'stok_tersedia', 'days_to_empty']], 
                        use_container_width=True)
        else:
            st.success("Semua item aman untuk 30 hari ke depan!")
    
    with tab2:
        st.subheader("Riwayat Transaksi")
        
        if len(st.session_state.transaction_history) > 0:
            # Transaction trend
            trans_df = st.session_state.transaction_history.copy()
            trans_df['tanggal'] = pd.to_datetime(trans_df['tanggal'])
            trans_df['date_only'] = trans_df['tanggal'].dt.date
            
            daily_trans = trans_df.groupby(['date_only', 'jenis_transaksi']).agg({
                'qty': 'sum'
            }).reset_index()
            
            fig_line = px.line(daily_trans, x='date_only', y='qty', color='jenis_transaksi',
                             title="Trend Transaksi Harian")
            st.plotly_chart(fig_line, use_container_width=True)
            
            # Detailed transaction table
            st.dataframe(trans_df.sort_values('tanggal', ascending=False), use_container_width=True)
        else:
            st.info("Belum ada riwayat transaksi.")
    
    with tab3:
        st.subheader("Analisis Request")
        
        if len(st.session_state.request_data) > 0:
            # Request by status
            status_count = st.session_state.request_data['status'].value_counts()
            fig_pie_status = px.pie(values=status_count.values, names=status_count.index,
                                   title="Distribusi Status Request")
            st.plotly_chart(fig_pie_status, use_container_width=True)
            
            # Request by division
            div_requests = st.session_state.request_data['divisi'].value_counts().reset_index()
            fig_bar_div = px.bar(div_requests, x='index', y='divisi',
                               title="Request per Divisi")
            st.plotly_chart(fig_bar_div, use_container_width=True)
        else:
            st.info("Belum ada data request.")

# MASTER DATA
elif menu == "⚙️ Master Data":
    st.title("⚙️ Master Data Management")
    
    tab1, tab2 = st.tabs(["➕ Tambah Barang", "📝 Edit Barang"])
    
    with tab1:
        st.subheader("Tambah Barang Baru")
        
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                kode_barang_new = st.text_input("Kode Barang", placeholder="ATK007")
                nama_barang_new = st.text_input("Nama Barang", placeholder="Nama barang ATK")
                kategori_new = st.selectbox("Kategori", ['Alat Tulis', 'Kertas', 'Alat Kantor', 'Lainnya'])
                lokasi_new = st.selectbox("Lokasi Penyimpanan", ['Gudang A', 'Gudang B', 'Gudang C'])
                
            with col2:
                stok_awal = st.number_input("Stok Awal", min_value=0, value=0)
                minimum_stok_new = st.number_input("Minimum Stok", min_value=1, value=5)
                harga_satuan_new = st.number_input("Harga Satuan (Rp)", min_value=0, value=1000)
                supplier_new = st.text_input("Supplier", placeholder="PT Supplier ABC")
            
            submitted_add = st.form_submit_button("💾 Tambah Barang", use_container_width=True)
            
            if submitted_add:
                if kode_barang_new and nama_barang_new:
                    # Check if kode already exists
                    if kode_barang_new in st.session_state.inventory_data['kode_barang'].values:
                        st.error("❌ Kode barang sudah ada!")
                    else:
                        # Add new item
                        new_item = pd.DataFrame({
                            'kode_barang': [kode_barang_new],
                            'nama_barang': [nama_barang_new],
                            'kategori': [kategori_new],
                            'stok_tersedia': [stok_awal],
                            'minimum_stok': [minimum_stok_new],
                            'harga_satuan': [harga_satuan_new],
                            'supplier': [supplier_new],
                            'lokasi_penyimpanan': [lokasi_new]
                        })
                        
                        st.session_state.inventory_data = pd.concat([st.session_state.inventory_data, new_item], ignore_index=True)
                        
                        # Add transaction if stock > 0
                        if stok_awal > 0:
                            add_transaction(kode_barang_new, nama_barang_new, 'Masuk', stok_awal, 'Stock awal')
                        
                        st.success("✅ Barang berhasil ditambahkan!")
                        st.rerun()
                else:
                    st.error("❌ Kode barang dan nama barang harus diisi!")
    
    with tab2:
        st.subheader("Edit Data Barang")
        
        if len(st.session_state.inventory_data) > 0:
            # Select item to edit
            edit_options = st.session_state.inventory_data['kode_barang'] + " - " + st.session_state.inventory_data['nama_barang']
            selected_edit = st.selectbox("Pilih Barang untuk Edit", edit_options)
            
            if selected_edit:
                kode_edit = selected_edit.split(" - ")[0]
                item_data = st.session_state.inventory_data[st.session_state.inventory_data['kode_barang'] == kode_edit].iloc[0]
                
                with st.form("edit_item_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nama_edit = st.text_input("Nama Barang", value=item_data['nama_barang'])
                        kategori_edit = st.selectbox("Kategori", 
                                                   ['Alat Tulis', 'Kertas', 'Alat Kantor', 'Lainnya'],
                                                   index=['Alat Tulis', 'Kertas', 'Alat Kantor', 'Lainnya'].index(item_data['kategori']))
                        minimum_edit = st.number_input("Minimum Stok", min_value=1, value=int(item_data['minimum_stok']))
                        lokasi_edit = st.selectbox("Lokasi", ['Gudang A', 'Gudang B', 'Gudang C'],
                                                 index=['Gudang A', 'Gudang B', 'Gudang C'].index(item_data['lokasi_penyimpanan']))
                    
                    with col2:
                        stock_adjustment = st.number_input("Adjustment Stok (+/-)", value=0, 
                                                         help="Positif untuk menambah, negatif untuk mengurangi")
                        harga_edit = st.number_input("Harga Satuan", min_value=0, value=int(item_data['harga_satuan']))
                        supplier_edit = st.text_input("Supplier", value=item_data['supplier'])
                        adjustment_reason = st.text_input("Alasan Adjustment", placeholder="Alasan perubahan stok...")
                    
                    submitted_edit = st.form_submit_button("💾 Update Barang", use_container_width=True)
                    
                    if submitted_edit:
                        # Update data
                        mask = st.session_state.inventory_data['kode_barang'] == kode_edit
                        st.session_state.inventory_data.loc[mask, 'nama_barang'] = nama_edit
                        st.session_state.inventory_data.loc[mask, 'kategori'] = kategori_edit
                        st.session_state.inventory_data.loc[mask, 'minimum_stok'] = minimum_edit
                        st.session_state.inventory_data.loc[mask, 'harga_satuan'] = harga_edit
                        st.session_state.inventory_data.loc[mask, 'supplier'] = supplier_edit
                        st.session_state.inventory_data.loc[mask, 'lokasi_penyimpanan'] = lokasi_edit
                        
                        # Handle stock adjustment
                        if stock_adjustment != 0:
                            current_stock = st.session_state.inventory_data.loc[mask, 'stok_tersedia'].iloc[0]
                            new_stock = current_stock + stock_adjustment
                            
                            if new_stock >= 0:
                                st.session_state.inventory_data.loc[mask, 'stok_tersedia'] = new_stock
                                
                                # Add transaction
                                trans_type = 'Masuk' if stock_adjustment > 0 else 'Keluar'
                                add_transaction(kode_edit, nama_edit, trans_type, abs(stock_adjustment), 
                                              f"Adjustment: {adjustment_reason}")
                                
                                st.success("✅ Data barang berhasil diupdate!")
                                st.rerun()
                            else:
                                st.error("❌ Stock tidak boleh negatif!")
                        else:
                            st.success("✅ Data barang berhasil diupdate!")
                            st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**📋 Sistem Inventory ATK v1.0**")
st.sidebar.markdown("Developed with ❤️ using Streamlit")
