import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.hybrid_manager import HybridDataManager
from utils.inventory import InventoryManager

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Initialize managers
data_manager = HybridDataManager()
inventory_manager = InventoryManager()

st.title("📊 Dashboard Inventory ATK")

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

# Charts section
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Distribusi Stok per Kategori")
    if not inventory_df.empty:
        category_stock = inventory_df.groupby('category').agg({
            'current_stock': 'sum',
            'item_name': 'count'
        }).reset_index()
        category_stock.columns = ['Category', 'Total Stock', 'Item Count']
        
        fig_bar = px.bar(
            category_stock, 
            x='Category', 
            y='Total Stock',
            title="Total Stok per Kategori",
            color='Total Stock',
            color_continuous_scale='Viridis'
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Show category details
        with st.expander("Detail per Kategori"):
            st.dataframe(category_stock, use_container_width=True)
    else:
        st.info("Belum ada data inventory untuk ditampilkan.")

with col2:
    st.subheader("⚠️ Status Stok Item")
    if not inventory_df.empty:
        # Create stock status
        inventory_df_copy = inventory_df.copy()
        inventory_df_copy['stock_status'] = inventory_df_copy.apply(
            lambda row: 'Habis' if row['current_stock'] == 0 
            else 'Stok Rendah' if row['current_stock'] <= row['minimum_stock'] 
            else 'Stok Normal', axis=1
        )
        
        status_counts = inventory_df_copy['stock_status'].value_counts()
        
        fig_donut = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Status Stok",
            hole=0.4,
            color_discrete_map={
                'Habis': '#FF4B4B',
                'Stok Rendah': '#FFA500',
                'Stok Normal': '#00C851'
            }
        )
        fig_donut.update_layout(height=400)
        st.plotly_chart(fig_donut, use_container_width=True)
        
        # Alert for low stock items
        low_stock_items = inventory_df_copy[inventory_df_copy['stock_status'].isin(['Habis', 'Stok Rendah'])]
        if not low_stock_items.empty:
            with st.expander(f"⚠️ {len(low_stock_items)} Item Perlu Perhatian"):
                for _, item in low_stock_items.iterrows():
                    status_icon = "🔴" if item['stock_status'] == 'Habis' else "🟡"
                    st.write(f"{status_icon} **{item['item_name']}** - Stok: {item['current_stock']} {item['unit']} (Min: {item['minimum_stock']})")
    else:
        st.info("Belum ada data inventory untuk ditampilkan.")

# Order trends
st.subheader("📈 Trend Order ATK")
if not orders_df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Order dalam 30 hari terakhir**")
        # Last 30 days trend
        orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
        last_30_days = pd.date_range(end=datetime.now().date(), periods=30)
        daily_orders = orders_df.groupby(orders_df['order_date'].dt.date).size().reindex(last_30_days.date, fill_value=0)
        
        fig_trend = px.line(
            x=daily_orders.index,
            y=daily_orders.values,
            title="Trend Order Harian"
        )
        fig_trend.update_layout(height=300, xaxis_title="Tanggal", yaxis_title="Jumlah Order")
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        st.write("**Order berdasarkan Status**")
        status_counts = orders_df['status'].value_counts()
        
        fig_status = px.bar(
            x=status_counts.index,
            y=status_counts.values,
            title="Order per Status",
            color=status_counts.values,
            color_continuous_scale='RdYlGn'
        )
        fig_status.update_layout(height=300, xaxis_title="Status", yaxis_title="Jumlah")
        st.plotly_chart(fig_status, use_container_width=True)
else:
    st.info("Belum ada data order untuk ditampilkan.")

# Top requested items
st.subheader("🔥 Item Paling Sering Diminta")
if not orders_df.empty:
    top_items = orders_df.groupby('item_name').agg({
        'quantity': 'sum',
        'order_id': 'count'
    }).reset_index()
    top_items.columns = ['Item', 'Total Quantity', 'Order Count']
    top_items = top_items.sort_values('Order Count', ascending=False).head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_top = px.bar(
            top_items.head(5),
            x='Order Count',
            y='Item',
            orientation='h',
            title="Top 5 Item Paling Sering Diminta",
            color='Order Count',
            color_continuous_scale='Blues'
        )
        fig_top.update_layout(height=300)
        st.plotly_chart(fig_top, use_container_width=True)
    
    with col2:
        st.write("**Top 10 Item yang Diminta**")
        st.dataframe(top_items, use_container_width=True, hide_index=True)
else:
    st.info("Belum ada data order untuk analysis.")

# Department usage
st.subheader("🏢 Penggunaan per Departemen")
if not orders_df.empty:
    dept_usage = orders_df.groupby('department').agg({
        'quantity': 'sum',
        'order_id': 'count'
    }).reset_index()
    dept_usage.columns = ['Department', 'Total Quantity', 'Total Orders']
    
    fig_dept = px.sunburst(
        orders_df,
        path=['department', 'category'],
        title="Penggunaan ATK per Departemen dan Kategori"
    )
    fig_dept.update_layout(height=400)
    st.plotly_chart(fig_dept, use_container_width=True)
    
    with st.expander("Detail Penggunaan per Departemen"):
        st.dataframe(dept_usage.sort_values('Total Orders', ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Belum ada data untuk analysis departemen.")

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
