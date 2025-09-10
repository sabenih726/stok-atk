import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- Inisialisasi database sqlite ---
conn = sqlite3.connect("office_supplies.db", check_same_thread=False)
c = conn.cursor()

# Buat tabel jika belum ada
c.execute("""CREATE TABLE IF NOT EXISTS stok (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_barang TEXT UNIQUE,
    stok INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    departemen TEXT,
    status TEXT,
    tanggal TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS request_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER,
    barang TEXT,
    jumlah INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    departemen TEXT,
    barang TEXT,
    jumlah INTEGER,
    tanggal TEXT
)""")

conn.commit()

# --- Fungsi pembantu ---
def get_stok():
    return pd.read_sql("SELECT * FROM stok", conn)

def add_stok(nama_barang, qty):
    try:
        c.execute("INSERT INTO stok (nama_barang, stok) VALUES (?,?)", (nama_barang, qty))
    except sqlite3.IntegrityError:  # jika sudah ada, update stok
        c.execute("UPDATE stok SET stok = stok + ? WHERE nama_barang = ?", (qty, nama_barang))
    conn.commit()

def reduce_stok(item, qty):
    c.execute("UPDATE stok SET stok = stok - ? WHERE nama_barang = ?", (qty, item))
    conn.commit()

def add_request(nama, departemen, barang_list):
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO requests (nama, departemen, status, tanggal) VALUES (?,?,?,?)",
              (nama, departemen, "Menunggu Konfirmasi", tanggal))
    request_id = c.lastrowid
    for item, jumlah in barang_list:
        c.execute("INSERT INTO request_items (request_id, barang, jumlah) VALUES (?,?,?)",
                  (request_id, item, jumlah))
    conn.commit()

def get_requests(status_filter=None):
    if status_filter:
        return pd.read_sql("SELECT * FROM requests WHERE status=?", conn, params=(status_filter,))
    else:
        return pd.read_sql("SELECT * FROM requests", conn)

def get_request_items(request_id):
    return pd.read_sql("SELECT * FROM request_items WHERE request_id=?", conn, params=(request_id,))

def confirm_request(request_id):
    req = c.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
    items = c.execute("SELECT barang, jumlah FROM request_items WHERE request_id=?", (request_id,)).fetchall()

    # cek stok
    for item, qty in items:
        stok = c.execute("SELECT stok FROM stok WHERE nama_barang=?", (item,)).fetchone()[0]
        if qty > stok:
            return False, f"Stok {item} tidak cukup"

    # update stok & buat history
    for item, qty in items:
        reduce_stok(item, qty)
        c.execute("INSERT INTO history (nama, departemen, barang, jumlah, tanggal) VALUES (?,?,?,?,?)",
                  (req[1], req[2], item, qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    c.execute("UPDATE requests SET status=? WHERE id=?", ("Dikonfirmasi", request_id))
    conn.commit()
    return True, "Request berhasil dikonfirmasi"

def get_history():
    return pd.read_sql("SELECT * FROM history ORDER BY tanggal DESC", conn)

# --- UI Streamlit ---
st.set_page_config(page_title="Office Supplies Manager", page_icon="📦", layout="wide")
st.markdown("<h1 style='color:#2C3E50; text-align:center;'>📦 Office Supplies Manager</h1>", unsafe_allow_html=True)

# Session autentikasi admin
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

tabs = ["📝 Form Request", "📊 Stok Barang", "📚 History Transaksi", "🔒 Admin Panel"]
active_tab = st.tabs(tabs)

# --- TAB FORM REQUEST ---
with active_tab[0]:
    st.subheader("Form Request Karyawan")
    with st.form("form_request"):
        nama = st.text_input("Nama", "")
        departemen = st.text_input("Departemen", "")

        barang_df = get_stok()
        barang_list = []
        st.write("Pilih Barang:")
        jumlah_item = st.number_input("Jumlah item berbeda", min_value=1, max_value=10, value=1)
        for i in range(jumlah_item):
            col1, col2 = st.columns([2,1])
            with col1:
                item = st.selectbox(f"Barang {i+1}", ["-"] + barang_df["nama_barang"].tolist(), key=f"item_{i}")
            with col2:
                qty = st.number_input(f"Jumlah {i+1}", min_value=0, step=1, key=f"jumlah_{i}")
            if item != "-" and qty > 0:
                barang_list.append((item, qty))

        submitted = st.form_submit_button("Kirim Request")
        if submitted:
            if nama and departemen and barang_list:
                add_request(nama, departemen, barang_list)
                st.success("Request berhasil dikirim!")
            else:
                st.error("Mohon isi semua data dengan benar.")

# --- TAB STOK BARANG ---
with active_tab[1]:
    st.subheader("Stok Barang Tersedia")
    stok_df = get_stok()
    st.dataframe(stok_df, use_container_width=True)

# --- TAB HISTORY TRANSAKSI ---
with active_tab[2]:
    st.subheader("History Transaksi (Barang Keluar)")
    history = get_history()
    if history.empty:
        st.info("Belum ada transaksi.")
    else:
        st.dataframe(history, use_container_width=True)

# --- TAB ADMIN PANEL ---
with active_tab[3]:
    if not st.session_state.is_admin:
        password = st.text_input("Masukkan Password Admin", type="password")
        if password == "admin123":  # <-- ganti sesuai selera
            st.session_state.is_admin = True
            st.success("Berhasil masuk sebagai Admin!")
        else:
            st.warning("Tab ini khusus Admin. Silakan login.")
    else:
        st.subheader("Admin Panel")
        
        st.markdown("### Request Masuk")
        req_df = get_requests("Menunggu Konfirmasi")
        if req_df.empty:
            st.info("Belum ada request menunggu.")
        else:
            for i, row in req_df.iterrows():
                with st.expander(f"{row['nama']} ({row['departemen']}) [{row['tanggal']}]"):
                    items = get_request_items(row['id'])
                    st.table(items[["barang", "jumlah"]])
                    if st.button("Konfirmasi", key=f"confirm_{row['id']}"):
                        ok, msg = confirm_request(row['id'])
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

        st.markdown("### Tambah Barang Stok")
        with st.form("form_barang"):
            new_item = st.text_input("Nama Barang")
            qty = st.number_input("Jumlah Awal", min_value=1, step=1)
            add_btn = st.form_submit_button("Tambah / Update Barang")
            if add_btn and new_item:
                add_stok(new_item, qty)
                st.success(f"Barang {new_item} ditambahkan / update stok!")
