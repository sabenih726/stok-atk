# app.py
import streamlit as st
from streamlit_option_menu import option_menu
from auth import login_admin, logout_user
from dashboards.admin import show_admin_dashboard

# --- Page Config
st.set_page_config(
    page_title="Office Supplies System",
    page_icon="📦",
    layout="wide"
)

# --- Init session
for k,v in {"logged_in":False,"user_type":None,"user_name":None}.items():
    st.session_state.setdefault(k,v)

# --- Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/external-flaticons-lineal-color-flat-icons/512/external-office-supplies-human-resources-flaticons-lineal-color-flat-icons.png", width=80)
    st.title("Office Supplies")

    if not st.session_state.logged_in:
        st.subheader("Login sebagai Admin")
        user = st.text_input("Username")
        pw   = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if login_admin(user,pw): st.rerun()
            else: st.error("Username / password salah!")
    else:
        st.success(f"👋 Halo, {st.session_state.user_name}")
        if st.button("Logout", use_container_width=True):
            logout_user(); st.rerun()

# --- Main Content
if not st.session_state.logged_in:
    st.title("📦 Selamat Datang")
    st.write("Silakan login Admin di sidebar untuk mulai.")
else:
    # Modern nav bar (option menu)
    choice = option_menu(
        None, ["Dashboard"],  # bisa ditambah menu lain
        icons=["bar-chart"], orientation="horizontal"
    )
    if choice=="Dashboard":
        show_admin_dashboard()

# --- Footer
st.markdown("<hr><center>Office Supplies Management System © 2024</center>",unsafe_allow_html=True)
