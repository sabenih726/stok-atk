# dashboards/admin.py
import streamlit as st

def show_admin_dashboard():
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔔 Persetujuan", 
        "📦 Kelola Stok", 
        "📊 Laporan", 
        "👥 Kelola Karyawan",
        "📈 Dashboard"
    ])

    from dashboards.admin_requests import approval_tab
    from dashboards.admin_inventory import stock_tab
    from dashboards.admin_reports import report_tab
    from dashboards.admin_employees import employees_tab
    from dashboards.admin_analytics import analytics_tab

    with tab1: approval_tab()
    with tab2: stock_tab()
    with tab3: report_tab()
    with tab4: employees_tab()
    with tab5: analytics_tab()
