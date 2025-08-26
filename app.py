import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from utils.db_manager import DatabaseManager
from utils.inventory import InventoryManager

# Page configuration
st.set_page_config(
    page_title="Sistem Pengelolaan ATK",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize data managers
@st.cache_resource
def get_managers():
    return DatabaseManager(), InventoryManager()

data_manager, inventory_manager = get_managers()

# Main page content
st.title("🏢 Sistem Pengelolaan ATK")
st.markdown("---")

# Overview metrics
col1, col2, col3, col4 = st.columns(4)

# Load current data
inventory_df = data_manager.load_inventory()
orders_df = data_manager.load_orders()

with col1:
    total_items = len(inventory_df)
    st.metric("Total Item ATK", total_items)

with col2:
    low_stock_items = len(inventory_df[inventory_df['current_stock'] <= inventory_df['minimum_stock']])
    st.metric("Item Stok Rendah", low_stock_items, delta=f"-{low_stock_items}" if low_stock_items > 0 else None)

with col3:
    today_orders = len(orders_df[orders_df['order_date'] == datetime.now().strftime('%Y-%m-%d')])
    st.metric("Order Hari Ini", today_orders)

with col4:
    pending_orders = len(orders_df[orders_df['status'] == 'Pending'])
    st.metric("Order Pending", pending_orders)

st.markdown("---")

# Quick overview charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Status Stok ATK")
    if not inventory_df.empty:
        # Stock status pie chart
        stock_status = []
        for _, item in inventory_df.iterrows():
            if item['current_stock'] == 0:
                stock_status.append('Habis')
            elif item['current_stock'] <= item['minimum_stock']:
                stock_status.append('Stok Rendah')
            else:
                stock_status.append('Stok Normal')
        
        status_counts = pd.Series(stock_status).value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color_discrete_map={
                'Habis': '#FF4B4B',
                'Stok Rendah': '#FFA500',
                'Stok Normal': '#00C851'
            }
        )
        fig_pie.update_layout(height=300)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Belum ada data inventory.")

with col2:
    st.subheader("📈 Order Trend (7 Hari Terakhir)")
    if not orders_df.empty:
        # Last 7 days order trend
        orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
        last_7_days = pd.date_range(end=datetime.now().date(), periods=7)
        daily_orders = orders_df.groupby(orders_df['order_date'].dt.date).size().reindex(last_7_days.date, fill_value=0)
        
        fig_line = px.line(
            x=daily_orders.index,
            y=daily_orders.values,
            title="Jumlah Order per Hari"
        )
        fig_line.update_layout(height=300, xaxis_title="Tanggal", yaxis_title="Jumlah Order")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Belum ada data order.")

# Recent activity
st.subheader("🕐 Aktivitas Terbaru")
if not orders_df.empty:
    recent_orders = orders_df.sort_values('timestamp', ascending=False).head(5)
    for _, order in recent_orders.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.write(f"**{order['item_name']}**")
            with col2:
                st.write(f"Pemohon: {order['requester_name']}")
            with col3:
                st.write(f"Qty: {order['quantity']}")
            with col4:
                status_color = {
                    'Pending': '🟡',
                    'Approved': '🟢',
                    'Rejected': '🔴'
                }
                st.write(f"{status_color.get(order['status'], '⚪')} {order['status']}")
else:
    st.info("Belum ada aktivitas order.")

# Navigation help
st.markdown("---")
st.markdown("""
### 🚀 Panduan Penggunaan
- **📦 Order ATK**: Buat permintaan ATK baru
- **📊 Dashboard**: Lihat status inventory dan analisis
- **⚙️ Admin Panel**: Kelola inventory dan approve order (khusus admin)
- **📋 Reports**: Lihat laporan dan export data

Gunakan sidebar untuk navigasi antar halaman.
""")
