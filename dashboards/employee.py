import streamlit as st
import pandas as pd
from database import Database

db = Database()

def show_employee_dashboard():
    tab1, tab2, tab3 = st.tabs(["📝 Buat Permintaan", "📋 Riwayat Permintaan", "📊 Stok Barang"])
    
    from dashboards.employee_requisition import requisition_tab
    from dashboards.employee_history import history_tab
    from dashboards.employee_inventory import inventory_tab

    with tab1: requisition_tab()
    with tab2: history_tab()
    with tab3: inventory_tab()
