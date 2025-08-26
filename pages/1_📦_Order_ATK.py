import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from utils.db_manager import DatabaseManager
from utils.inventory import InventoryManager

st.set_page_config(page_title="Order ATK", page_icon="📦", layout="wide")

# Initialize managers
data_manager = DatabaseManager()
inventory_manager = InventoryManager()

st.title("📦 Order ATK")
st.markdown("Buat permintaan ATK baru dengan mengisi form di bawah ini.")

# Load inventory data
inventory_df = data_manager.load_inventory()

if inventory_df.empty:
    st.error("Inventory kosong. Silakan hubungi admin untuk menambah item ATK.")
    st.stop()

# Order form
with st.form("order_form"):
    st.subheader("Form Permintaan ATK")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Requester information
        requester_name = st.text_input("Nama Pemohon *", placeholder="Masukkan nama lengkap")
        department = st.selectbox("Departemen *", [
            "IT", "HR", "Finance", "Marketing", "Operations", "Management", "Other"
        ])
        
        # Filter available items (stock > 0)
        available_items = inventory_df[inventory_df['current_stock'] > 0]
        
        if available_items.empty:
            st.error("Tidak ada item ATK yang tersedia saat ini.")
            st.stop()
        
        # Group items by category for better organization
        categories = available_items['category'].unique()
        selected_category = st.selectbox("Kategori ATK *", ["Semua"] + list(categories))
        
        # Filter items based on category
        if selected_category != "Semua":
            filtered_items = available_items[available_items['category'] == selected_category]
        else:
            filtered_items = available_items
        
        item_options = {}
        for _, item in filtered_items.iterrows():
            item_options[f"{item['item_name']} (Stok: {item['current_stock']} {item['unit']})"] = item['item_id']
        
        selected_item_display = st.selectbox("Pilih Item ATK *", list(item_options.keys()))
        selected_item_id = item_options[selected_item_display]
        
        # Get selected item details
        selected_item = inventory_df[inventory_df['item_id'] == selected_item_id].iloc[0]
        
    with col2:
        # Display item details
        st.subheader("Detail Item")
        st.write(f"**Nama**: {selected_item['item_name']}")
        st.write(f"**Kategori**: {selected_item['category']}")
        st.write(f"**Stok Tersedia**: {selected_item['current_stock']} {selected_item['unit']}")
        st.write(f"**Deskripsi**: {selected_item.get('description', 'Tidak ada deskripsi')}")
        
        # Quantity input with validation
        max_quantity = min(selected_item['current_stock'], 20)  # Limit max order to 20 or available stock
        quantity = st.number_input(
            f"Jumlah yang Diminta (Max: {max_quantity}) *", 
            min_value=1, 
            max_value=max_quantity, 
            value=1
        )
        
        # Purpose/reason
        purpose = st.text_area("Keperluan/Alasan Permintaan", placeholder="Jelaskan untuk keperluan apa ATK ini digunakan")
        
        # Priority level
        priority = st.selectbox("Tingkat Prioritas", ["Normal", "Urgent", "Very Urgent"])
    
    # Submit button
    submitted = st.form_submit_button("🚀 Submit Order", use_container_width=True)
    
    if submitted:
        # Validation
        if not requester_name.strip():
            st.error("Nama pemohon harus diisi!")
        elif not purpose.strip():
            st.error("Keperluan/alasan permintaan harus diisi!")
        else:
            # Create order
            order_data = {
                'order_id': str(uuid.uuid4())[:8],
                'item_id': selected_item_id,
                'item_name': selected_item['item_name'],
                'category': selected_item['category'],
                'quantity': quantity,
                'unit': selected_item['unit'],
                'requester_name': requester_name,
                'department': department,
                'purpose': purpose,
                'priority': priority,
                'status': 'Pending',
                'order_date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'approved_by': '',
                'approved_date': '',
                'notes': ''
            }
            
            # Add order to data
            success = data_manager.add_order(order_data)
            
            if success:
                st.success(f"✅ Order berhasil dibuat dengan ID: **{order_data['order_id']}**")
                st.balloons()
                
                # Show order summary
                with st.expander("📋 Detail Order", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Order ID**: {order_data['order_id']}")
                        st.write(f"**Item**: {order_data['item_name']}")
                        st.write(f"**Jumlah**: {order_data['quantity']} {order_data['unit']}")
                        st.write(f"**Prioritas**: {order_data['priority']}")
                    with col2:
                        st.write(f"**Pemohon**: {order_data['requester_name']}")
                        st.write(f"**Departemen**: {order_data['department']}")
                        st.write(f"**Tanggal**: {order_data['order_date']}")
                        st.write(f"**Status**: {order_data['status']}")
                
                st.info("💡 Order Anda sedang menunggu persetujuan admin. Anda akan diberitahu jika status berubah.")
                
                # Option to create another order
                if st.button("➕ Buat Order Baru"):
                    st.rerun()
            else:
                st.error("❌ Gagal membuat order. Silakan coba lagi.")

# Order tracking section
st.markdown("---")
st.subheader("🔍 Lacak Order Anda")

with st.expander("Cari Order Berdasarkan ID atau Nama"):
    col1, col2 = st.columns(2)
    with col1:
        search_id = st.text_input("Order ID", placeholder="Masukkan Order ID")
    with col2:
        search_name = st.text_input("Nama Pemohon", placeholder="Masukkan nama pemohon")
    
    if st.button("🔍 Cari Order"):
        orders_df = data_manager.load_orders()
        
        if not orders_df.empty:
            # Filter orders
            filtered_orders = orders_df.copy()
            
            if search_id:
                filtered_orders = filtered_orders[filtered_orders['order_id'].str.contains(search_id, case=False, na=False)]
            
            if search_name:
                filtered_orders = filtered_orders[filtered_orders['requester_name'].str.contains(search_name, case=False, na=False)]
            
            if not filtered_orders.empty:
                st.subheader("📋 Hasil Pencarian")
                for _, order in filtered_orders.iterrows():
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                        with col1:
                            st.write(f"**{order['order_id']}**")
                            st.write(f"{order['item_name']}")
                        with col2:
                            st.write(f"Pemohon: {order['requester_name']}")
                            st.write(f"Tanggal: {order['order_date']}")
                        with col3:
                            st.write(f"Qty: {order['quantity']} {order['unit']}")
                            st.write(f"Prioritas: {order['priority']}")
                        with col4:
                            status_color = {
                                'Pending': '🟡',
                                'Approved': '🟢',
                                'Rejected': '🔴'
                            }
                            st.write(f"{status_color.get(order['status'], '⚪')} {order['status']}")
                        
                        if order['notes']:
                            st.write(f"📝 Catatan: {order['notes']}")
                        
                        st.markdown("---")
            else:
                st.info("Tidak ada order yang ditemukan dengan kriteria pencarian tersebut.")
        else:
            st.info("Belum ada data order.")

# Quick tips
st.markdown("---")
st.markdown("""
### 💡 Tips Order ATK
- Pastikan mengisi keperluan dengan jelas untuk mempercepat persetujuan
- Periksa stok tersedia sebelum membuat order
- Order dengan prioritas "Urgent" akan diproses lebih cepat
- Simpan Order ID untuk tracking status order
""")
