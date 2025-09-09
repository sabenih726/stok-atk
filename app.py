# app.py
import streamlit as st
from auth import login_user, login_admin, logout_user
from dashboards.employee import show_employee_dashboard
from dashboards.admin import show_admin_dashboard
from database import Database

st.set_page_config(
    page_title="Office Supplies Management System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Buat session state default
for key, val in {
    'logged_in': False,
    'user_type': None,
    'user_id': None,
    'user_name': None,
    'department': None
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Sidebar login/logout
with st.sidebar:
    st.title("📦 Office Supplies System")
    if not st.session_state.logged_in:
        st.subheader("Login")
        login_type = st.radio("Login sebagai:", ["Karyawan", "Admin"])
        if login_type == "Karyawan":
            email = st.text_input("Email")
            if st.button("Login"):
                if login_user(email): st.rerun()
                else: st.error("Email tidak terdaftar")
        else:
            username = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.button("Login"):
                if login_admin(username, pw): st.rerun()
                else: st.error("Username atau password salah")
    else:
        st.write(f"👤 {st.session_state.user_name}")
        st.write("🏢 " + st.session_state.department if st.session_state.user_type == 'employee' else "🔐 Administrator")
        if st.button("Logout"):
            logout_user()
            st.rerun()

# Konten utama
if not st.session_state.logged_in:
    st.title("Selamat Datang")
    st.write("Silakan login melalui sidebar untuk melanjutkan")
else:
    if st.session_state.user_type == 'employee':
        show_employee_dashboard()
    else:
        show_admin_dashboard()

# Footer
st.markdown("---")
st.caption("Office Supplies Management System © 2024")
