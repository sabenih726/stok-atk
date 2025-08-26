import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.hybrid_manager import HybridDataManager
from utils.inventory import InventoryManager

st.set_page_config(page_title="Dashboard", layout="wide")

# Initialize managers
data_manager = HybridDataManager()
inventory_manager = InventoryManager()

st.title("Dashboard Inventory ATK")

# Load data
inventory_df = data_manager.load_inventory()
orders_df = data_manager.load_orders()

# Refresh button
if st.button("🔄 Refresh Data"):
    st.rerun()

# Main metrics
st.subheader("📈 Metrics Overview")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_items = len(inventory_df)
    st.metric("Total Item", total_items)

with col2:
    if not inventory_df.empty:
        total_stock_value = (inventory_df['current_stock'] * inventory_df['unit_price']).sum()
        st.metric("Nilai Total Stok", f"Rp {total_stock_value:,.0f}")
    else:
        st.metric("Nilai Total Stok", "Rp 0")

with col3:
    if not inventory_df.empty:
        low_stock = len(inventory_df[inventory_df['current_stock'] <= inventory_df['minimum_stock']])
        st.metric("Item Stok Rendah", low_stock, delta=f"-{low_stock}" if low_stock > 0 else "✅")
    else:
        st.metric("Item Stok Rendah", 0)

with col4:
    if not orders_df.empty:
        total_orders = len(orders_df)
        today_orders = len(orders_df[orders_df['order_date'] == datetime.now().strftime('%Y-%m-%d')])
        st.metric("Total Orders", total_orders, delta=f"+{today_orders} hari ini")
    else:
        st.metric("Total Orders", 0)

with col5:
    if not orders_df.empty:
        pending_orders = len(orders_df[orders_df['status'] == 'Pending'])
        st.metric("Order Pending", pending_orders)
    else:
        st.metric("Order Pending", 0)

st.markdown("---")

# Real-time inventory table
st.subheader("📋 Inventory Real-time")
if not inventory_df.empty:
    # Add search and filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("🔍 Cari item", placeholder="Nama item atau kategori")
    with col2:
        category_filter = st.selectbox("Filter Kategori", ["Semua"] + list(inventory_df['category'].unique()))
    with col3:
        stock_filter = st.selectbox("Filter Stok", ["Semua", "Stok Normal", "Stok Rendah", "Habis"])
    
    # Apply filters
    filtered_df = inventory_df.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['item_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['category'].str.contains(search_term, case=False, na=False)
        ]
    
    if category_filter != "Semua":
        filtered_df = filtered_df[filtered_df['category'] == category_filter]
    
    if stock_filter != "Semua":
        if stock_filter == "Habis":
            filtered_df = filtered_df[filtered_df['current_stock'] == 0]
        elif stock_filter == "Stok Rendah":
            filtered_df = filtered_df[
                (filtered_df['current_stock'] > 0) & 
                (filtered_df['current_stock'] <= filtered_df['minimum_stock'])
            ]
        elif stock_filter == "Stok Normal":
            filtered_df = filtered_df[filtered_df['current_stock'] > filtered_df['minimum_stock']]
    
    # Add stock status column for display
    filtered_df['Status'] = filtered_df.apply(
        lambda row: '🔴 Habis' if row['current_stock'] == 0 
        else '🟡 Rendah' if row['current_stock'] <= row['minimum_stock'] 
        else '🟢 Normal', axis=1
    )
    
    # Display table
    display_columns = ['item_name', 'category', 'current_stock', 'minimum_stock', 'unit', 'unit_price', 'Status']
    column_config = {
        'item_name': 'Nama Item',
        'category': 'Kategori',
        'current_stock': 'Stok Saat Ini',
        'minimum_stock': 'Stok Minimum',
        'unit': 'Satuan',
        'unit_price': st.column_config.NumberColumn('Harga Satuan', format="Rp %.0f"),
        'Status': 'Status'
    }
    
    st.dataframe(
        filtered_df[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
    
    st.caption(f"Menampilkan {len(filtered_df)} dari {len(inventory_df)} item")
else:
    st.info("Belum ada data inventory.")

# Auto-refresh option
st.markdown("---")
if st.checkbox("🔄 Auto-refresh setiap 30 detik"):
    import time
    time.sleep(30)
    st.rerun()
