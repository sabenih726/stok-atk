from __future__ import annotations

import warnings
from datetime import date, datetime
from typing import Optional

import pandas as pd
import plotly.express as px
import sqlite3
import streamlit as st

# ---------------- SQLite setup ----------------
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlite3")

def setup_sqlite_adapters():
    sqlite3.register_adapter(date, lambda x: x.isoformat())
    sqlite3.register_adapter(datetime, lambda x: x.isoformat())
    sqlite3.register_converter("date", lambda x: datetime.fromisoformat(x.decode()).date())
    sqlite3.register_converter("datetime", lambda x: datetime.fromisoformat(x.decode()))

setup_sqlite_adapters()

# Enable foreign‑key constraints
sqlite3.connect("stok_atk.db").execute("PRAGMA foreign_keys = ON").close()

# ---------------- Database helpers ----------------
DB_PATH = "stok_atk.db"

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)


def init_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS barang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_barang TEXT UNIQUE NOT NULL,
            nama_barang TEXT NOT NULL,
            kategori TEXT NOT NULL,
            satuan TEXT NOT NULL,
            stok_minimum INTEGER NOT NULL,
            stok_saat_ini INTEGER NOT NULL,
            harga_satuan REAL NOT NULL,
            lokasi_penyimpanan TEXT,
            tanggal_input DATE NOT NULL,
            keterangan TEXT
        )
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_barang TEXT NOT NULL,
            jenis_transaksi TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            tanggal_transaksi DATE NOT NULL,
            keterangan TEXT,
            penanggung_jawab TEXT,
            FOREIGN KEY (kode_barang) REFERENCES barang (kode_barang) ON DELETE CASCADE
        )
    """
    )
    conn.commit()
    conn.close()

# CRUD utilities (unchanged except delete_barang) ----------------

def get_all_barang() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM barang ORDER BY nama_barang", conn)


def get_barang_by_kode(kode: str) -> Optional[tuple]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM barang WHERE kode_barang = ?", (kode,))
        return cur.fetchone()


def insert_barang(data: tuple) -> bool:
    with get_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO barang (kode_barang,nama_barang,kategori,satuan,stok_minimum,
                                    stok_saat_ini,harga_satuan,lokasi_penyimpanan,
                                    tanggal_input,keterangan)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
                data,
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            st.error("Kode barang sudah ada!")
            return False


def update_barang(kode: str, data: tuple) -> bool:
    with get_connection() as conn:
        try:
            conn.execute(
                """
                UPDATE barang SET nama_barang=?, kategori=?, satuan=?, stok_minimum=?,
                                   stok_saat_ini=?, harga_satuan=?, lokasi_penyimpanan=?,
                                   keterangan=? WHERE kode_barang=?
            """,
                (*data, kode),
            )
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Update gagal: {e}")
            return False


def delete_barang(kode: str) -> bool:
    """Hapus barang + transaksi; menggunakan ON DELETE CASCADE di schema."""
    with get_connection() as conn:
        try:
            conn.execute("DELETE FROM barang WHERE kode_barang = ?", (kode,))
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Gagal menghapus: {e}")
            return False

# (insert_transaksi, update_stok_barang, get_transaksi, get_stok_menipis) –
#       tetap sama seperti versi pengguna, tidak di‑paste ulang di sini demi ringkas.
#       ↳ Pastikan Anda menyalin fungsi lengkap kalau file ini berdiri sendiri.

# ---------------- Streamlit UI ----------------
st.set_page_config("Manajemen Stok ATK", "📝", layout="wide", initial_sidebar_state="expanded")

init_database()

KATEGORI_LIST = [
    "Alat Tulis",
    "Kertas",
    "Elektronik",
    "Peralatan",
    "Lainnya",
]
SATUAN_LIST = ["pcs", "dus", "rim", "pak", "lusin", "kg", "liter"]


def main():
    st.title("🏢 Manajemen Stok ATK Kantor")
    st.sidebar.selectbox(
        "Pilih Menu:",
        ["Dashboard", "Data Barang", "Transaksi", "Laporan", "Pengaturan"],
        key="menu",
    )

    menu = st.session_state.menu
    if menu == "Data Barang":
        show_data_barang()
    # Dashboard, Transaksi, Laporan, Pengaturan → gunakan fungsi lama.


# -------- EDIT / HAPUS BARANG TAB --------

def show_data_barang():
    st.header("📦 Data Barang")
    tab1, tab2, tab3 = st.tabs(["📋 Daftar", "➕ Tambah", "✏️ Edit/Hapus"])

    # ——— Tab 1: List
    with tab1:
        df = get_all_barang()
        st.dataframe(df, use_container_width=True) if not df.empty else st.info("Belum ada data")

    # ——— Tab 2: Tambah (menggunakan kode asli pengguna, ringkas di sini)
    with tab2:
        st.subheader("Tambah Barang Baru")
        with st.form("add_barang"):
            col1, col2 = st.columns(2)
            with col1:
                kode_barang = st.text_input("Kode Barang*")
                nama_barang = st.text_input("Nama Barang*")
                kategori = st.selectbox("Kategori*", KATEGORI_LIST)
                satuan = st.selectbox("Satuan*", SATUAN_LIST)
            with col2:
                stok_min = st.number_input("Stok Minimum*", 0, value=10)
                stok_curr = st.number_input("Stok Saat Ini*", 0, value=0)
                harga = st.number_input("Harga Satuan*", 0.0)
                lokasi = st.text_input("Lokasi Penyimpanan")
            keterangan = st.text_area("Keterangan")
            if st.form_submit_button("Tambah Barang"):
                if kode_barang and nama_barang:
                    data = (
                        kode_barang,
                        nama_barang,
                        kategori,
                        satuan,
                        stok_min,
                        stok_curr,
                        harga,
                        lokasi,
                        date.today(),
                        keterangan,
                    )
                    if insert_barang(data):
                        st.success("Barang ditambahkan!")
                        st.rerun()
                else:
                    st.error("Field bertanda * wajib diisi")

    # ——— Tab 3: Edit/Hapus
    with tab3:
        st.subheader("Edit atau Hapus Barang")
        df = get_all_barang()
        if df.empty:
            st.info("Belum ada data barang")
            return

        kode_selected = st.selectbox("Pilih Kode Barang", df["kode_barang"], key="sel_kode")
        record = get_barang_by_kode(kode_selected)
        if record is None:
            st.error("Barang tidak ditemukan")
            return

        (
            _id,
            kode,
            nama,
            kategori,
            satuan,
            stok_min,
            stok_curr,
            harga,
            lokasi,
            tanggal_input,
            ket,
        ) = record

        with st.form("edit_barang"):
            col1, col2 = st.columns(2)
            with col1:
                nama_new = st.text_input("Nama Barang*", value=nama)
                kategori_new = st.selectbox("Kategori*", KATEGORI_LIST, index=KATEGORI_LIST.index(categoria) if (categoria:=kategori) in KATEGORI_LIST else 0)
                satuan_new = st.selectbox("Satuan*", SATUAN_LIST, index=SATUAN_LIST.index(satuan) if satuan in SATUAN_LIST else 0)
            with col2:
                stok_min_new = st.number_input("Stok Minimum*", 0, value=stok_min)
                stok_curr_new = st.number_input("Stok Saat Ini*", 0, value=stok_curr)
                harga_new = st.number_input("Harga Satuan*", 0.0, value=harga)
            lokasi_new = st.text_input("Lokasi Penyimpanan", value=lokasi or "")
            ket_new = st.text_area("Keterangan", value=ket or "")

            col_save, col_del = st.columns([3, 1])
            with col_save:
                if st.form_submit_button("💾 Simpan Perubahan"):
                    if update_barang(
                        kode,
                        (
                            nama_new,
                            kategori_new,
                            satuan_new,
                            stok_min_new,
                            stok_curr_new,
                            harga_new,
                            lokasi_new,
                            ket_new,
                        ),
                    ):
                        st.success("Perubahan disimpan")
                        st.rerun()
            with col_del:
                if st.form_submit_button("🗑️ Hapus Barang", help="Hapus barang & seluruh transaksi terkait"):
                    if st.checkbox("Konfirmasi hapus barang dan TRANSAKSI terkait", key="confirm_del"):
                        if delete_barang(kode):
                            st.success("Barang & transaksi dihapus")
                            st.rerun()
                    else:
                        st.warning("Centang konfirmasi untuk menghapus.")

# ---------------------------------------------------
if __name__ == "__main__":
    main()
