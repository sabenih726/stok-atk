import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- Inisialisasi database sqlite ---
conn = sqlite3.connect("office_supplies.db", check_same_thread=False)
c = conn.cursor()

# Buat tabel jika belum ada
c.execute("""CREATE TABLE IF NOT EXISTS stok (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mm TEXT,
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
c.execute("""CREATE TABLE IF NOT EXISTS stok_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_barang TEXT,
    jumlah INTEGER,
    tipe TEXT, -- 'masuk' atau 'keluar'
    tanggal TEXT
)""")
conn.commit()

# --- Seed data stok kalau masih kosong ---
c.execute("SELECT COUNT(*) FROM stok")
if c.fetchone()[0] == 0:
    default_items = [
        ("MM001", "Pulpen", 50),
        ("MM002", "Buku Tulis", 30),
        ("MM003", "Stapler", 10),
        ("MM004", "Kertas A4", 100),
        ("MM005", "Spidol", 20)
    ]
    c.executemany("INSERT INTO stok (mm, nama_barang, stok) VALUES (?,?,?)", default_items)
    for mm, nama, qty in default_items:
        c.execute("INSERT INTO stok_log (nama_barang, jumlah, tipe, tanggal) VALUES (?,?,?,?)",
                  (nama, qty, 'masuk', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

# --- Fungsi pembantu database ---
def get_stok():
    return pd.read_sql("SELECT id, mm, nama_barang, stok FROM stok", conn)

def add_stok(nama_barang, qty, mm=None):
    existing = c.execute("SELECT id FROM stok WHERE nama_barang=?", (nama_barang,)).fetchone()
    if existing:
        c.execute("UPDATE stok SET stok = stok + ? WHERE nama_barang=?", (qty, nama_barang))
    else:
        c.execute("INSERT INTO stok (mm, nama_barang, stok) VALUES (?,?,?)", (mm, nama_barang, qty))
    # log stok masuk
    c.execute("INSERT INTO stok_log (nama_barang, jumlah, tipe, tanggal) VALUES (?,?,?,?)",
              (nama_barang, qty, 'masuk', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def reduce_stok(item, qty):
    c.execute("UPDATE stok SET stok = stok - ? WHERE nama_barang = ?", (qty, item))
    # log stok keluar
    c.execute("INSERT INTO stok_log (nama_barang, jumlah, tipe, tanggal) VALUES (?,?,?,?)",
              (item, qty, 'keluar', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def add_request(nama, departemen, barang_list):
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO requests (nama, departemen, status, tanggal) VALUES (?,?,?,?)",
        (nama, departemen, "Menunggu Konfirmasi", tanggal),
    )
    request_id = c.lastrowid
    for item, jumlah in barang_list:
        c.execute(
            "INSERT INTO request_items (request_id, barang, jumlah) VALUES (?,?,?)",
            (request_id, item, jumlah),
        )
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

def delete_history_all():
    c.execute("DELETE FROM history")
    conn.commit()

def delete_item_barang(nama_barang):
    c.execute("DELETE FROM stok WHERE nama_barang=?", (nama_barang,))
    conn.commit()

# --- Rekap stok masuk / keluar ---
def get_rekap_stok():
    stok_df = get_stok()[["mm", "nama_barang", "stok"]]
    masuk = pd.read_sql("SELECT nama_barang, SUM(jumlah) as masuk FROM stok_log WHERE tipe='masuk' GROUP BY nama_barang", conn)
    keluar = pd.read_sql("SELECT nama_barang, SUM(jumlah) as keluar FROM stok_log WHERE tipe='keluar' GROUP BY nama_barang", conn)

    df = pd.merge(stok_df, masuk, on="nama_barang", how="left")
    df = pd.merge(df, keluar, on="nama_barang", how="left")
    df = df.fillna(0)
    df = df.rename(columns={"stok": "stok_tersedia"})
    return df[["mm", "nama_barang", "masuk", "keluar", "stok_tersedia"]]

# --- Export & Import Functions ---
def export_stok_to_excel():
    df = get_rekap_stok()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="RekapStok")
    buffer.seek(0)
    return buffer

def import_stok_from_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    required_cols = {"mm", "nama_barang", "stok"}
    if not required_cols.issubset(set(df.columns)):
        return False, "Format file salah! Harus ada kolom: 'mm', 'nama_barang', dan 'stok'"
    for _, row in df.iterrows():
        mm = str(row["mm"]).strip()
        nama = str(row["nama_barang"]).strip()
        try:
            qty = int(row["stok"])
        except:
            return False, f"Stok untuk {nama} tidak valid (harus angka)"
        if nama != "" and qty >= 0:
            add_stok(nama, qty, mm)
    return True, "Import stok berhasil!"

def generate_template():
    df = pd.DataFrame({"mm": [], "nama_barang": [], "stok": []})
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Template")
    buffer.seek(0)
    return buffer

# --- UI Streamlit ---
st.set_page_config(page_title="General Office Supplies", layout="wide")
st.markdown("""
<div style="display:flex; justify-content:center; align-items:center;">
    <img src="logo.png" style="height:60px; margin-right:10px;">
    <h1 style="color:#2C3E50; margin:0;">General Office Supplies</h1>
</div>
""", unsafe_allow_html=True)

# Session state
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "jumlah_item" not in st.session_state:
    st.session_state.jumlah_item = 1

tabs = ["Form Request", "Stok Barang", "History Transaksi", "Admin Panel"]
active_tab = st.tabs(tabs)

# --- TAB FORM REQUEST ---
with active_tab[0]:
    st.subheader("Form Request Karyawan")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Tambah Barang"):
            st.session_state.jumlah_item += 1
    with col_btn2:
        if st.button("Kurangi Barang") and st.session_state.jumlah_item > 1:
            st.session_state.jumlah_item -= 1

    with st.form("form_request"):
        nama = st.text_input("Nama", "")
        departemen = st.text_input("Departemen", "")
        barang_df = get_stok()
        barang_list = []

        for i in range(st.session_state.jumlah_item):
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
                st.session_state.jumlah_item = 1
            else:
                st.error("Mohon isi semua data dengan benar.")

# --- TAB STOK BARANG ---
with active_tab[1]:
    st.subheader("Rekap Stok Barang")
    rekap_df = get_rekap_stok()
    st.dataframe(rekap_df, width="stretch")

# --- TAB HISTORY TRANSAKSI ---
with active_tab[2]:
    st.subheader("History Transaksi (Barang Keluar)")
    history = get_history()
    if history.empty:
        st.info("Belum ada transaksi.")
    else:
        st.dataframe(history, width="stretch")

# --- TAB ADMIN PANEL ---
with active_tab[3]:
    if not st.session_state.is_admin:
        st.subheader("Login Admin")
        with st.form("login_form"):
            password = st.text_input("Password Admin", type="password")
            login_btn = st.form_submit_button("Login")
            if login_btn:
                if password == "743759":
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Password salah!")
    else:
        st.success("Anda login sebagai Admin")
        if st.button("Logout Admin"):
            st.session_state.is_admin = False
            st.rerun()

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

        st.markdown("---")
        st.markdown("### Tambah Barang / Update Stok")
        with st.form("form_barang"):
            mm = st.text_input("Kode MM")
            new_item = st.text_input("Nama Barang")
            qty = st.number_input("Jumlah", min_value=1, step=1)
            add_btn = st.form_submit_button("Tambah / Update Barang")
            if add_btn and new_item:
                add_stok(new_item, qty, mm)
                st.success(f"Barang {new_item} ({mm}) berhasil ditambahkan / stok ditambah {qty}!")

        st.markdown("---")
        st.markdown("### Export & Import Data Stok")
        excel_data = export_stok_to_excel()
        st.download_button(
            label="Export Stok ke Excel",
            data=excel_data,
            file_name="rekap_stok.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        template_file = generate_template()
        st.download_button(
            label="Download Template Import",
            data=template_file,
            file_name="template_import_stok.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        uploaded_file = st.file_uploader("Upload file stok (Excel)", type=["xlsx"])
        if uploaded_file:
            success, msg = import_stok_from_excel(uploaded_file)
            if success:
                st.success(msg)
            else:
                st.error(msg)

        st.markdown("---")
        st.markdown("### Manajemen Data")
        if st.button("Hapus Semua History Transaksi"):
            delete_history_all()
            st.success("Semua history transaksi berhasil dihapus!")

        stok_df = get_stok()
        if not stok_df.empty:
            barang_pilihan = st.selectbox("Pilih Barang untuk Dihapus", stok_df["nama_barang"].tolist())
            if st.button(f"Hapus Barang: {barang_pilihan}"):
                delete_item_barang(barang_pilihan)
                st.success(f"Barang '{barang_pilihan}' berhasil dihapus dari stok!")

st.markdown("""
---
<div style='text-align:center; color:grey; font-size:13px;'>
    Created by <b>Facility Maintenance</b>
</div>
""", unsafe_allow_html=True)
