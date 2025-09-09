
import streamlit as st
from database import Database

db = Database()

def login_admin(username, password):
    # ⚠️ sementara hardcode akun admin
    if username == "admin" and password == "admin123":
        st.session_state.logged_in = True
        st.session_state.user_type = 'admin'
        st.session_state.user_name = 'Administrator'
        return True
    return False

def logout_user():
    for key in ["logged_in", "user_type", "user_name", "user_id", "department"]:
        st.session_state[key] = None
