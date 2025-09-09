# auth.py
import streamlit as st
from database import Database

db = Database()

def login_user(email):
    query = "SELECT * FROM employees WHERE email = ?"
    result = db.execute_query(query, (email,))
    if result:
        user = result[0]
        st.session_state.logged_in = True
        st.session_state.user_type = 'employee'
        st.session_state.user_id = user['id']
        st.session_state.user_name = user['name']
        st.session_state.department = user['department']
        return True
    return False

def login_admin(username, password):
    if username == "admin" and password == "admin123":  # sementara
        st.session_state.logged_in = True
        st.session_state.user_type = 'admin'
        st.session_state.user_name = 'Administrator'
        return True
    return False

def logout_user():
    """Reset session state"""
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.department = None
