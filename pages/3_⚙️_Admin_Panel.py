import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from utils.hybrid_manager import HybridDataManager
from utils.inventory import InventoryManager

st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

# Initialize managers
data_manager = HybridDataManager()
inventory_manager = InventoryManager()

# Simple admin authentication
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False

def authenticate_admin():
    st.title("🔐 Admin Login")
    st.markdown("Masukkan password admin untuk mengakses panel administrasi.")
    
    password = st.text_input("Password Admin", type="password")
    
    if st.button("Login"):
        # Simple password check (in production, use proper authentication)
        if password == "admin123":  # Change this to a secure password
            st.session_state.admin_authenticated = True
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Password salah!")
    
    st.markdown("---")
    st.caption("Default password: admin123")

if not st.session_state.admin_authenticated:
    authenticate_admin()
    st.stop()

# Admin panel content
st.title("⚙️ Admin Panel")

# Logout button
col1, col2, col3 = st.columns([1, 1, 1])
with col3:
    if st.button("🚪 Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()

# Admin tabs
tab1, tab2, tab3, tab4 = st.tabs(["📦 Kelola Inventory", "✅ Approve Orders", "📊 Analytics", "⚙️ Settings"])

with tab1:
    st.subheader("📦 Kelola Inventory")
    
    # Add new item form
    with st.expander("➕ Tambah Item Baru", expanded=False):
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                item_name = st.text_input("Nama Item *")
                category = st.selectbox("Kategori *", [
                    "Alat Tulis", "Kertas", "File & Folder", "Elektronik", 
                    "Perlengkapan Kantor", "Cleaning Supplies", "Other"
                ])
                unit = st.selectbox("Satuan *", ["pcs", "box", "pack", "rim", "roll", "set", "kg", "liter"])
                
            with col2:
                initial_stock = st.number_input("Stok Awal *", min_value=0, value=0)
                minimum_stock = st.number_input("Stok Minimum *", min_value=0, value=10)
                unit_price = st.number_input("Harga Satuan (Rp) *", min_value=0.0, value=0.0, format="%.2f")
            
            description = st.text_area("Deskripsi Item")
            
            if st.form_submit_button("➕ Tambah Item"):
                if item_name and category and unit:
                    new_item = {
                        'item_id': str(uuid.uuid4())[:8],
                        'item_name': item_name,
                        'category': category,
                        'initial_stock': initial_stock,
                        'current_stock': initial_stock,
                        'minimum_stock': minimum_stock,
                        'unit': unit,
                        'unit_price': unit_price,
                        'description': description,
                        'created_date': datetime.now().strftime('%Y-%m-%d'),
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    if data_manager.add_inventory_item(new_item):
                        st.success(f"✅ Item '{item_name}' berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.error("❌ Gagal menambahkan item!")
                else:
                    st.error("❌ Mohon lengkapi semua field yang wajib diisi!")
    
    # Existing inventory management
    inventory_df = data_manager.load_inventory()
    
    if not inventory_df.empty:
        st.subheader("📋 Inventory Existing")
        
        # Search and filter
        col1, col2 = st.columns(2)
        with col1:
            search_item = st.text_input("🔍 Cari Item", placeholder="Nama item atau kategori")
        with col2:
            filter_category = st.selectbox("Filter Kategori", ["Semua"] + list(inventory_df['category'].unique()))
        
        # Apply filters
        filtered_inventory = inventory_df.copy()
        if search_item:
            filtered_inventory = filtered_inventory[
                filtered_inventory['item_name'].str.contains(search_item, case=False, na=False) |
                filtered_inventory['category'].str.contains(search_item, case=False, na=False)
            ]
        if filter_category != "Semua":
            filtered_inventory = filtered_inventory[filtered_inventory['category'] == filter_category]
        
        # Inventory table with edit capabilities
        for idx, item in filtered_inventory.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 2])
                
                with col1:
                    st.write(f"**{item['item_name']}**")
                    st.caption(f"ID: {item['item_id']} | {item['category']}")
                
                with col2:
                    current_stock = item['current_stock']
                    min_stock = item['minimum_stock']
                    stock_status = "🔴 Habis" if current_stock == 0 else "🟡 Rendah" if current_stock <= min_stock else "🟢 Normal"
                    st.write(f"Stok: {current_stock} {item['unit']}")
                    st.write(stock_status)
                
                with col3:
                    st.write(f"Min: {min_stock}")
                    st.write(f"Rp {item['unit_price']:,.0f}")
                
                with col4:
                    # Stock adjustment
                    with st.popover("📝 Edit"):
                        new_stock = st.number_input(f"Stok Baru", value=int(current_stock), key=f"stock_{item['item_id']}")
                        new_min = st.number_input(f"Min Stok", value=int(min_stock), key=f"min_{item['item_id']}")
                        new_price = st.number_input(f"Harga", value=float(item['unit_price']), key=f"price_{item['item_id']}")
                        
                        if st.button("💾 Update", key=f"update_{item['item_id']}"):
                            updates = {
                                'current_stock': new_stock,
                                'minimum_stock': new_min,
                                'unit_price': new_price,
                                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            if data_manager.update_inventory_item(item['item_id'], updates):
                                st.success("✅ Item updated!")
                                st.rerun()
                
                with col5:
                    if st.button("🗑️ Delete", key=f"delete_{item['item_id']}", type="secondary"):
                        if data_manager.delete_inventory_item(item['item_id']):
                            st.success("✅ Item deleted!")
                            st.rerun()
                
                st.markdown("---")
    else:
        st.info("Belum ada inventory. Tambahkan item baru terlebih dahulu.")

with tab2:
    st.subheader("✅ Approve Orders")
    
    orders_df = data_manager.load_orders()
    
    if not orders_df.empty:
        # Filter orders
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter Status", ["Semua", "Pending", "Approved", "Rejected"])
        with col2:
            priority_filter = st.selectbox("Filter Prioritas", ["Semua", "Very Urgent", "Urgent", "Normal"])
        
        # Apply filters
        filtered_orders = orders_df.copy()
        if status_filter != "Semua":
            filtered_orders = filtered_orders[filtered_orders['status'] == status_filter]
        if priority_filter != "Semua":
            filtered_orders = filtered_orders[filtered_orders['priority'] == priority_filter]
        
        # Sort by priority and date
        priority_order = {'Very Urgent': 3, 'Urgent': 2, 'Normal': 1}
        filtered_orders['priority_num'] = filtered_orders['priority'].map(priority_order)
        filtered_orders = filtered_orders.sort_values(['priority_num', 'timestamp'], ascending=[False, True])
        
        st.write(f"📋 Menampilkan {len(filtered_orders)} order")
        
        # Order management
        for _, order in filtered_orders.iterrows():
            with st.container():
                # Priority indicator
                priority_color = {"Very Urgent": "🔴", "Urgent": "🟡", "Normal": "🟢"}
                priority_indicator = priority_color.get(order['priority'], "⚪")
                
                col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
                
                with col1:
                    st.write(f"{priority_indicator} **{order['order_id']}**")
                    st.write(f"**{order['item_name']}** ({order['quantity']} {order['unit']})")
                    st.caption(f"Kategori: {order['category']}")
                
                with col2:
                    st.write(f"**Pemohon:** {order['requester_name']}")
                    st.write(f"**Dept:** {order['department']}")
                    st.write(f"**Tanggal:** {order['order_date']}")
                
                with col3:
                    st.write(f"**Prioritas:** {order['priority']}")
                    st.write(f"**Status:** {order['status']}")
                    if order['purpose']:
                        st.write(f"**Keperluan:** {order['purpose']}")
                
                with col4:
                    if order['status'] == 'Pending':
                        col_approve, col_reject = st.columns(2)
                        
                        with col_approve:
                            if st.button("✅ Approve", key=f"approve_{order['order_id']}"):
                                # Check stock availability
                                inventory_df = data_manager.load_inventory()
                                item_stock = inventory_df[inventory_df['item_id'] == order['item_id']]
                                
                                if not item_stock.empty and item_stock.iloc[0]['current_stock'] >= order['quantity']:
                                    # Update order status
                                    order_updates = {
                                        'status': 'Approved',
                                        'approved_by': 'Admin',
                                        'approved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    }
                                    
                                    # Update stock
                                    new_stock = item_stock.iloc[0]['current_stock'] - order['quantity']
                                    stock_updates = {
                                        'current_stock': new_stock,
                                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    }
                                    
                                    if (data_manager.update_order(order['order_id'], order_updates) and 
                                        data_manager.update_inventory_item(order['item_id'], stock_updates)):
                                        st.success("✅ Order approved dan stok updated!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Gagal approve order!")
                                else:
                                    st.error("❌ Stok tidak mencukupi!")
                        
                        with col_reject:
                            with st.popover("❌ Reject"):
                                rejection_note = st.text_area("Alasan penolakan", key=f"reject_note_{order['order_id']}")
                                if st.button("Confirm Reject", key=f"confirm_reject_{order['order_id']}"):
                                    order_updates = {
                                        'status': 'Rejected',
                                        'approved_by': 'Admin',
                                        'approved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'notes': rejection_note
                                    }
                                    
                                    if data_manager.update_order(order['order_id'], order_updates):
                                        st.success("❌ Order rejected!")
                                        st.rerun()
                    else:
                        status_icon = {"Approved": "✅", "Rejected": "❌"}
                        st.write(f"{status_icon.get(order['status'], '⚪')} {order['status']}")
                        if order['approved_date']:
                            st.caption(f"Oleh: {order['approved_by']} pada {order['approved_date']}")
                        if order['notes']:
                            st.caption(f"Catatan: {order['notes']}")
                
                st.markdown("---")
    else:
        st.info("Belum ada order yang perlu di-review.")

with tab3:
    st.subheader("📊 Analytics")
    
    # Load data
    orders_df = data_manager.load_orders()
    inventory_df = data_manager.load_inventory()
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = len(orders_df) if not orders_df.empty else 0
        st.metric("Total Orders", total_orders)
    
    with col2:
        approved_orders = len(orders_df[orders_df['status'] == 'Approved']) if not orders_df.empty else 0
        approval_rate = (approved_orders / total_orders * 100) if total_orders > 0 else 0
        st.metric("Approval Rate", f"{approval_rate:.1f}%")
    
    with col3:
        low_stock_count = len(inventory_df[inventory_df['current_stock'] <= inventory_df['minimum_stock']]) if not inventory_df.empty else 0
        st.metric("Items Low Stock", low_stock_count)
    
    with col4:
        total_value = (inventory_df['current_stock'] * inventory_df['unit_price']).sum() if not inventory_df.empty else 0
        st.metric("Total Inventory Value", f"Rp {total_value:,.0f}")
    
    if not orders_df.empty:
        # Order analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Order per Departemen**")
            dept_orders = orders_df.groupby('department').size().sort_values(ascending=False)
            st.bar_chart(dept_orders)
        
        with col2:
            st.write("**Order per Status**")
            status_orders = orders_df.groupby('status').size()
            st.bar_chart(status_orders)
        
        # Recent activity summary
        st.subheader("📈 Recent Activity (Last 7 Days)")
        last_week = datetime.now() - timedelta(days=7)
        recent_orders = orders_df[pd.to_datetime(orders_df['order_date']) >= last_week]
        
        if not recent_orders.empty:
            col1, col2 = st.columns(2)
            with col1:
                daily_orders = recent_orders.groupby('order_date').size()
                st.line_chart(daily_orders)
            with col2:
                top_requested = recent_orders.groupby('item_name').size().sort_values(ascending=False).head(5)
                st.bar_chart(top_requested)
        else:
            st.info("Tidak ada aktivitas dalam 7 hari terakhir.")

with tab4:
    st.subheader("⚙️ Settings")
    
    # Data management
    st.write("**📁 Data Management**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Backup Data"):
            # Create backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_success = data_manager.backup_data(f"backup_{timestamp}")
            if backup_success:
                st.success("✅ Backup berhasil dibuat!")
            else:
                st.error("❌ Gagal membuat backup!")
    
    with col2:
        if st.button("🔄 Reset Orders"):
            if data_manager.reset_orders():
                st.success("✅ Data orders berhasil direset!")
                st.rerun()
            else:
                st.error("❌ Gagal reset orders!")
    
    with col3:
        if st.button("📊 Export Data"):
            export_success = data_manager.export_all_data()
            if export_success:
                st.success("✅ Data berhasil diekspor!")
            else:
                st.error("❌ Gagal ekspor data!")
    
    st.markdown("---")
    
    # System info
    st.write("**ℹ️ System Information**")
    
    inventory_count = len(data_manager.load_inventory())
    orders_count = len(data_manager.load_orders())
    
    st.write(f"- Total Inventory Items: {inventory_count}")
    st.write(f"- Total Orders: {orders_count}")
    st.write(f"- Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change admin password
    st.markdown("---")
    st.write("**🔐 Change Admin Password**")
    
    with st.form("change_password"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            if current_password == "admin123":  # Current default password
                if new_password == confirm_password and len(new_password) >= 6:
                    st.success("Password berhasil diubah! (Note: Dalam implementasi real, password akan disimpan dengan aman)")
                    st.info("⚠️ Fitur ini memerlukan implementasi keamanan tambahan untuk production")
                else:
                    st.error("Password baru tidak cocok atau terlalu pendek (min 6 karakter)")
            else:
                st.error("Password saat ini salah!")
