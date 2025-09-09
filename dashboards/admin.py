import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
from database import Database

db = Database()

def show_admin_dashboard():
    st.title("🔐 Dashboard Admin")
    st.markdown("Kelola stok, karyawan, dan lihat laporan secara interaktif.")

    # ---- METRICS CARDS ----------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    low_stock = db.execute_query("SELECT COUNT(*) as c FROM inventory WHERE quantity <= min_stock")[0]['c']
    pending    = db.execute_query("SELECT COUNT(*) as c FROM requisitions WHERE status='pending'")[0]['c']
    items      = db.execute_query("SELECT COUNT(*) as c FROM inventory")[0]['c']
    employees  = db.execute_query("SELECT COUNT(*) as c FROM employees")[0]['c']
    
    with c1: st.metric("Stok Rendah", low_stock, delta_color="inverse")
    with c2: st.metric("Pending Request", pending)
    with c3: st.metric("Total Jenis Barang", items)
    with c4: st.metric("Karyawan", employees)
    st.write("---")

    # ---- INVENTORY TABLE --------------------------------------
    st.subheader("📦 Inventaris Barang")
    inventory = db.execute_query("SELECT * FROM inventory ORDER BY item_name")
    if inventory:
        df = pd.DataFrame([dict(row) for row in inventory])
        df['status'] = df.apply(lambda x: '⚠️ Rendah' if x['quantity'] <= x['min_stock'] else '✅ Aman', axis=1)
        
        gb = GridOptionsBuilder.from_dataframe(df[["item_name","quantity","unit","min_stock","status"]])
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(resizable=True, filterable=True, sortable=True)
        grid_options = gb.build()
        AgGrid(df, gridOptions=grid_options, theme="balham", height=250)
    else:
        st.info("Inventaris kosong")

    st.write("---")

    # ---- TRANSAKSI TOP ITEMS ---------------------------------
    st.subheader("📊 Barang Paling Banyak Diminta (30 Hari)")
    top_items = db.execute_query("""
        SELECT item_name, SUM(quantity) as total_requested
        FROM transaction_history
        WHERE status='approved' AND date >= date('now','-30 days')
        GROUP BY item_name
        ORDER BY total_requested DESC LIMIT 10
    """)
    if top_items:
        df = pd.DataFrame([dict(r) for r in top_items])
        fig = px.bar(df, x="item_name", y="total_requested",
                     labels={"item_name":"Barang","total_requested":"Total Diminta"},
                     color="total_requested", color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada transaksi")

    st.toast("Dashboard berhasil dimuat 🚀")
