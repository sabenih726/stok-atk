import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import Database
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Office Supplies Management System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db = Database()

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'department' not in st.session_state:
    st.session_state.department = None

# Helper Functions
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

def logout_user():
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.department = None

# Sidebar
with st.sidebar:
    st.title("📦 Office Supplies System")
    
    if not st.session_state.logged_in:
        st.subheader("Login")
        login_type = st.radio("Login sebagai:", ["Karyawan", "Admin"])
        
        if login_type == "Karyawan":
            email = st.text_input("Email")
            if st.button("Login"):
                if login_user(email):
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Email tidak terdaftar")
        else:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.user_type = 'admin'
                    st.session_state.user_name = 'Administrator'
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau password salah")
    else:
        st.write(f"👤 {st.session_state.user_name}")
        if st.session_state.user_type == 'employee':
            st.write(f"🏢 {st.session_state.department}")
        else:
            st.write("🔐 Administrator")
        
        if st.button("Logout"):
            logout_user()
            st.rerun()

# Main content =====================================================================================
if not st.session_state.logged_in:
    st.title("Selamat Datang di Office Supplies Management System")
    st.write("Silakan login melalui sidebar untuk melanjutkan")
    
    # Some stats
    col1, col2, col3 = st.columns(3)
    with col1:
        total_items = db.execute_query("SELECT COUNT(*) as count FROM inventory")[0]['count']
        st.metric("Total Jenis Barang", total_items)
    with col2:
        total_employees = db.execute_query("SELECT COUNT(*) as count FROM employees")[0]['count']
        st.metric("Total Karyawan", total_employees)
    with col3:
        pending_reqs = db.execute_query("SELECT COUNT(*) as count FROM requisitions WHERE status='pending'")[0]['count']
        st.metric("Permintaan Pending", pending_reqs)

elif st.session_state.user_type == 'employee':
    # Employee Dashboard
    tab1, tab2, tab3 = st.tabs(["📝 Buat Permintaan", "📋 Riwayat Permintaan", "📊 Stok Barang"])
    
    # ----------------- TAB 1 : Buat Permintaan
    with tab1:
        st.header("Formulir Permintaan Barang")
        items_data = db.execute_query("SELECT * FROM inventory WHERE quantity > 0 ORDER BY item_name")
        if items_data:
            with st.form("requisition_form"):
                st.write("**Informasi Pemohon:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Nama", value=st.session_state.user_name, disabled=True)
                with col2:
                    st.text_input("Departemen", value=st.session_state.department, disabled=True)
                
                st.write("**Daftar Barang yang Diminta:**")
                num_items = st.number_input("Jumlah jenis barang", min_value=1, max_value=10, value=1)
                
                selected_items = []
                for i in range(num_items):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        item_names = [item['item_name'] for item in items_data]
                        selected_item = st.selectbox(f"Barang {i+1}", options=item_names, key=f"item_{i}")
                    with col2:
                        max_qty = next(item['quantity'] for item in items_data if item['item_name'] == selected_item)
                        quantity = st.number_input("Jumlah", min_value=1, max_value=max_qty, value=1, key=f"qty_{i}")
                    
                    selected_items.append({'item_name': selected_item, 'quantity': quantity})
                
                submitted = st.form_submit_button("Ajukan Permintaan")
                if submitted:
                    req_id = db.execute_query('''
                        INSERT INTO requisitions (employee_id, employee_name, department)
                        VALUES (?, ?, ?)
                    ''', (st.session_state.user_id, st.session_state.user_name, st.session_state.department))
                    
                    for item in selected_items:
                        item_data = next(i for i in items_data if i['item_name'] == item['item_name'])
                        db.execute_query('''
                            INSERT INTO requisition_items (requisition_id, item_id, item_name, quantity)
                            VALUES (?, ?, ?, ?)
                        ''', (req_id, item_data['id'], item['item_name'], item['quantity']))
                    
                    st.success("Permintaan berhasil diajukan!")
                    st.balloons()
    
    # ----------------- TAB 2 : Riwayat Permintaan
    with tab2:
        st.header("Riwayat Permintaan Saya")
        reqs = db.execute_query('''
            SELECT * FROM requisitions 
            WHERE employee_id = ? 
            ORDER BY created_at DESC
        ''', (st.session_state.user_id,))
        
        if reqs:
            for req in reqs:
                with st.expander(f"Permintaan #{req['id']} - {req['created_at'][:10]} - Status: {req['status'].upper()}"):
                    items = db.execute_query('''
                        SELECT * FROM requisition_items
                        WHERE requisition_id = ?
                    ''', (req['id'],))
                    df = pd.DataFrame([dict(row) for row in items])
                    if not df.empty:
                        st.dataframe(df[['item_name', 'quantity']], hide_index=True)
                    if req['admin_notes']:
                        st.info(f"Catatan Admin: {req['admin_notes']}")
        else:
            st.info("Belum ada riwayat permintaan")
    
    # ----------------- TAB 3 : Stok Barang
    with tab3:
        st.header("Stok Barang Tersedia")
        inventory = db.execute_query("SELECT * FROM inventory ORDER BY item_name")
        if inventory:
            df = pd.DataFrame([dict(row) for row in inventory])
            df['status'] = df.apply(lambda x: '⚠️ Stok Rendah' if x['quantity'] <= x['min_stock'] else '✅ Normal', axis=1)
            st.dataframe(
                df[['item_name', 'quantity', 'unit', 'min_stock', 'status']],
                column_config={
                    "item_name": "Nama Barang",
                    "quantity": "Stok Tersedia",
                    "unit": "Satuan",
                    "min_stock": "Stok Minimum",
                    "status": "Status"
                },
                hide_index=True
            )

elif st.session_state.user_type == 'admin':
    # Admin Dashboard
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔔 Persetujuan", 
        "📦 Kelola Stok", 
        "📊 Laporan", 
        "👥 Kelola Karyawan",
        "📈 Dashboard"
    ])
    
    # ----------------- TAB 1 : Persetujuan
    with tab1:
        st.header("Permintaan Menunggu Persetujuan")
        pending = db.execute_query('''
            SELECT * FROM requisitions 
            WHERE status = 'pending' 
            ORDER BY created_at DESC
        ''')
        
        if pending:
            for req in pending:
                with st.expander(f"Permintaan #{req['id']} - {req['employee_name']} ({req['department']}) - {req['created_at'][:10]}"):
                    items = db.execute_query('''
                        SELECT * FROM requisition_items
                        WHERE requisition_id = ?
                    ''', (req['id'],))
                    
                    st.write("**Barang yang diminta:**")
                    for item in items:
                        current_stock = db.execute_query(
                            "SELECT quantity FROM inventory WHERE id = ?", 
                            (item['item_id'],)
                        )[0]['quantity']
                        if current_stock >= item['quantity']:
                            st.write(f"✅ {item['item_name']}: {item['quantity']} (Stok: {current_stock})")
                        else:
                            st.write(f"❌ {item['item_name']}: {item['quantity']} (Stok: {current_stock}) - **STOK TIDAK CUKUP**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        admin_notes = st.text_area(f"Catatan (Opsional)", key=f"notes_{req['id']}")
                    
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        if st.button("✅ Setujui", key=f"approve_{req['id']}", type="primary"):
                            can_approve = True
                            for item in items:
                                current_stock = db.execute_query(
                                    "SELECT quantity FROM inventory WHERE id = ?", 
                                    (item['item_id'],)
                                )[0]['quantity']
                                if current_stock < item['quantity']:
                                    can_approve = False
                                    break
                            if can_approve:
                                db.execute_query('''
                                    UPDATE requisitions 
                                    SET status = 'approved', admin_notes = ?, processed_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                ''', (admin_notes, req['id']))
                                
                                for item in items:
                                    db.execute_query('''
                                        UPDATE inventory 
                                        SET quantity = quantity - ?, last_updated = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    ''', (item['quantity'], item['item_id']))
                                    db.execute_query('''
                                        INSERT INTO transaction_history 
                                        (employee_name, department, item_name, quantity, status, requisition_id)
                                        VALUES (?, ?, ?, ?, 'approved', ?)
                                    ''', (req['employee_name'], req['department'], item['item_name'], item['quantity'], req['id']))
                                st.success("Permintaan disetujui!")
                                st.rerun()
                            else:
                                st.error("Tidak dapat menyetujui: Stok tidak mencukupi!")
                    
                    with col4:
                        if st.button("❌ Tolak", key=f"reject_{req['id']}"):
                            db.execute_query('''
                                UPDATE requisitions 
                                SET status = 'rejected', admin_notes = ?, processed_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            ''', (admin_notes, req['id']))
                            for item in items:
                                db.execute_query('''
                                    INSERT INTO transaction_history 
                                    (employee_name, department, item_name, quantity, status, requisition_id)
                                    VALUES (?, ?, ?, ?, 'rejected', ?)
                                ''', (req['employee_name'], req['department'], item['item_name'], item['quantity'], req['id']))
                            st.success("Permintaan ditolak!")
                            st.rerun()
        else:
            st.info("Tidak ada permintaan yang menunggu persetujuan")

    # ----------------- TAB 2 : Kelola Stok Barang
    with tab2:
        st.header("Kelola Stok Barang")
        col1, col2 = st.columns([2, 1])
        with col1:
            inventory = db.execute_query("SELECT * FROM inventory ORDER BY item_name")
            if inventory:
                df = pd.DataFrame([dict(row) for row in inventory])
                df['status'] = df.apply(lambda x: '⚠️ Stok Rendah' if x['quantity'] <= x['min_stock'] else '✅ Normal', axis=1)
                st.dataframe(
                    df[['item_name', 'quantity', 'unit', 'min_stock', 'status', 'last_updated']],
                    column_config={
                        "item_name": "Nama Barang",
                        "quantity": "Stok Saat Ini",
                        "unit": "Satuan",
                        "min_stock": "Stok Minimum",
                        "status": "Status",
                        "last_updated": "Update Terakhir"
                    },
                    hide_index=True,
                    width="stretch"
                )
        with col2:
            st.subheader("Tambah Barang Baru")
            with st.form("add_item_form"):
                item_name = st.text_input("Nama Barang")
                quantity = st.number_input("Jumlah Awal", min_value=0, value=0)
                unit = st.text_input("Satuan", value="pcs")
                min_stock = st.number_input("Stok Minimum", min_value=0, value=10)
                if st.form_submit_button("Tambah Barang"):
                    try:
                        db.execute_query('''
                            INSERT INTO inventory (item_name, quantity, unit, min_stock)
                            VALUES (?, ?, ?, ?)
                        ''', (item_name, quantity, unit, min_stock))
                        st.success(f"Barang {item_name} berhasil ditambahkan!")
                        st.rerun()
                    except:
                        st.error("Barang sudah ada dalam database!")
            
            st.subheader("Update Stok")
            with st.form("update_stock_form"):
                items_list = [item['item_name'] for item in inventory]
                selected_item = st.selectbox("Pilih Barang", items_list)
                stock_change = st.number_input("Tambah/Kurangi Stok", value=0)
                if st.form_submit_button("Update Stok"):
                    if stock_change != 0:
                        item_id = next(item['id'] for item in inventory if item['item_name'] == selected_item)
                        db.execute_query('''
                            UPDATE inventory 
                            SET quantity = quantity + ?, last_updated = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (stock_change, item_id))
                        st.success(f"Stok {selected_item} berhasil diupdate!")
                        st.rerun()
    
    # ----------------- TAB 3 : Laporan Transaksi
    with tab3:
        st.header("Laporan Transaksi")
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Dari Tanggal", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("Sampai Tanggal", value=datetime.now())
        with col3:
            departments = db.execute_query("SELECT DISTINCT department FROM employees")
            dept_list = ['Semua'] + [d['department'] for d in departments]
            selected_dept = st.selectbox("Departemen", dept_list)
        
        query = '''
            SELECT * FROM transaction_history 
            WHERE date BETWEEN ? AND ?
        '''
        params = [start_date, end_date]
        if selected_dept != 'Semua':
            query += ' AND department = ?'
            params.append(selected_dept)
        query += ' ORDER BY date DESC'
        transactions = db.execute_query(query, params)
        
        if transactions:
            df = pd.DataFrame([dict(row) for row in transactions])
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_trans = len(df)
                st.metric("Total Transaksi", total_trans)
            with col2:
                approved = len(df[df['status'] == 'approved'])
                st.metric("Disetujui", approved)
            with col3:
                rejected = len(df[df['status'] == 'rejected'])
                st.metric("Ditolak", rejected)
            with col4:
                approval_rate = (approved / total_trans * 100) if total_trans > 0 else 0
                st.metric("Tingkat Persetujuan", f"{approval_rate:.1f}%")
            
            st.subheader("Detail Transaksi")
            st.dataframe(
                df[['date', 'employee_name', 'department', 'item_name', 'quantity', 'status']],
                column_config={
                    "date": "Tanggal",
                    "employee_name": "Nama Pemohon",
                    "department": "Departemen",
                    "item_name": "Nama Barang",
                    "quantity": "Jumlah",
                    "status": st.column_config.TextColumn(
                        "Status",
                        help="Status permintaan"
                    )
                },
                hide_index=True,
                width="stretch"
            )
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"laporan_transaksi_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.info("Tidak ada transaksi dalam periode yang dipilih")
    
    # ----------------- TAB 4 : Kelola Karyawan
    with tab4:
        st.header("Kelola Karyawan")
        col1, col2 = st.columns([2, 1])
        with col1:
            employees = db.execute_query("SELECT * FROM employees ORDER BY name")
            if employees:
                df = pd.DataFrame([dict(row) for row in employees])
                st.dataframe(
                    df[['name', 'department', 'email']],
                    column_config={
                        "name": "Nama",
                        "department": "Departemen",
                        "email": "Email"
                    },
                    hide_index=True,
                    width="stretch"
                )
        with col2:
            st.subheader("Tambah Karyawan")
            with st.form("add_employee_form"):
                name = st.text_input("Nama Lengkap")
                department = st.text_input("Departemen")
                email = st.text_input("Email")
                if st.form_submit_button("Tambah Karyawan"):
                    try:
                        db.execute_query('''
                            INSERT INTO employees (name, department, email)
                            VALUES (?, ?, ?)
                        ''', (name, department, email))
                        st.success(f"Karyawan {name} berhasil ditambahkan!")
                        st.rerun()
                    except:
                        st.error("Email sudah terdaftar!")
    
    # ----------------- TAB 5 : Dashboard Analytics
    with tab5:
        st.header("Dashboard Analytics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            low_stock = db.execute_query("SELECT COUNT(*) as count FROM inventory WHERE quantity <= min_stock")[0]['count']
            st.metric("Barang Stok Rendah", low_stock, delta_color="inverse")
        with col2:
            pending_reqs = db.execute_query("SELECT COUNT(*) as count FROM requisitions WHERE status='pending'")[0]['count']
            st.metric("Permintaan Pending", pending_reqs)
        with col3:
            total_items = db.execute_query("SELECT COUNT(*) as count FROM inventory")[0]['count']
            st.metric("Total Jenis Barang", total_items)
        with col4:
            total_employees = db.execute_query("SELECT COUNT(*) as count FROM employees")[0]['count']
            st.metric("Total Karyawan", total_employees)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Barang Paling Banyak Diminta (30 Hari)")
            top_items = db.execute_query('''
                SELECT item_name, SUM(quantity) as total_requested
                FROM transaction_history
                WHERE status = 'approved' 
                AND date >= date('now', '-30 days')
                GROUP BY item_name
                ORDER BY total_requested DESC
                LIMIT 10
            ''')
            if top_items:
                df = pd.DataFrame([dict(row) for row in top_items])
                fig = px.bar(df, x='item_name', y='total_requested',
                            labels={'item_name': 'Nama Barang', 'total_requested': 'Jumlah Diminta'})
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Belum ada data transaksi")
        with col2:
            st.subheader("Permintaan per Departemen (30 Hari)")
            dept_requests = db.execute_query('''
                SELECT department, COUNT(*) as total_requests
                FROM requisitions
                WHERE created_at >= date('now', '-30 days')
                GROUP BY department
            ''')
            if dept_requests:
                df = pd.DataFrame([dict(row) for row in dept_requests])
                fig = px.pie(df, values='total_requests', names='department')
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Belum ada data permintaan")
        
        st.subheader("Status Stok Barang")
        inventory_status = db.execute_query('''
            SELECT 
                CASE 
                    WHEN quantity <= min_stock THEN 'Stok Rendah'
                    WHEN quantity <= min_stock * 2 THEN 'Stok Menengah'
                    ELSE 'Stok Aman'
                END as status,
                COUNT(*) as count
            FROM inventory
            GROUP BY status
        ''')
        if inventory_status:
            df = pd.DataFrame([dict(row) for row in inventory_status])
            fig = go.Figure(data=[go.Pie(labels=df['status'], values=df['count'], 
                                         marker_colors=['#ff4444', '#ffaa00', '#00aa00'])])
            fig.update_layout(title="Distribusi Status Stok")
            st.plotly_chart(fig, width="stretch")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Office Supplies Management System © 2024</p>
    </div>
    """,
    unsafe_allow_html=True
)
