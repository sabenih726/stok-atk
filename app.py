# streamlit_inventory_app.py
"""
Streamlit implementation of "Stok ATK Kantor" inspired by the Next.js demo
repo https://github.com/sabenih726/Stok-ATK-Kantor (simple sales / inventory
app).  Re‑creates the same flow:
  • Barang masuk / keluar via quick search
  • Tabel stok + status warna
  • Tambah / edit / hapus material
  • Riwayat transaksi & export CSV

Dependencies
------------
    pip install streamlit pandas
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, date
from typing import List

import pandas as pd
import streamlit as st

DB = "inventory.db"

# ------------------ DB helpers ------------------

def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)


def init_db() -> None:
    """Create tables if not exist."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id TEXT UNIQUE,
                name TEXT,
                brand TEXT,
                category TEXT,
                stock INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                qty INTEGER,
                action TEXT,
                tdate DATE,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
            """
        )
        conn.commit()


# ------------- CRUD operations -------------

def fetch_items(search: str = "") -> pd.DataFrame:
    with get_conn() as conn:
        if search:
            return pd.read_sql(
                "SELECT * FROM items WHERE name LIKE ? OR brand LIKE ? ORDER BY name",
                conn,
                params=(f"%{search}%", f"%{search}%"),
            )
        return pd.read_sql("SELECT * FROM items ORDER BY name", conn)


def upsert_item(material_id: str, name: str, brand: str, category: str, stock: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM items WHERE material_id = ?", (material_id,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE items SET name=?, brand=?, category=?, stock=? WHERE material_id=?",
                (name, brand, category, stock, material_id),
            )
        else:
            cur.execute(
                "INSERT INTO items (material_id,name,brand,category,stock) VALUES (?,?,?,?,?)",
                (material_id, name, brand, category, stock),
            )
        conn.commit()


def delete_item(material_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM transactions WHERE item_id = (SELECT id FROM items WHERE material_id=?)", (material_id,))
        conn.execute("DELETE FROM items WHERE material_id = ?", (material_id,))
        conn.commit()


def add_transaction(material_id: str, qty: int, action: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, stock FROM items WHERE material_id = ?", (material_id,))
        row = cur.fetchone()
        if not row:
            st.error("Barang tidak ditemukan.")
            return False
        item_id, curr_stock = row
        new_stock = curr_stock + qty if action == "masuk" else curr_stock - qty
        if new_stock < 0:
            st.error("Stok tidak mencukupi!")
            return False
        cur.execute(
            "INSERT INTO transactions (item_id, qty, action, tdate) VALUES (?,?,?,?)",
            (item_id, qty, action, date.today()),
        )
        cur.execute("UPDATE items SET stock = ? WHERE id = ?", (new_stock, item_id))
        conn.commit()
        return True


def fetch_transactions(limit: int | None = None) -> pd.DataFrame:
    with get_conn() as conn:
        query = """SELECT t.id, i.material_id, i.name, i.brand, t.qty, t.action, t.tdate
                   FROM transactions t JOIN items i ON t.item_id = i.id
                   ORDER BY t.id DESC"""
        if limit:
            query += f" LIMIT {limit}"
        return pd.read_sql(query, conn)


# ----------------- UI -----------------

st.set_page_config("Stok ATK Kantor", "📦", layout="wide")
init_db()

MENU = st.sidebar.radio("Menu", ["Transaksi", "Data Barang", "Riwayat"])

# === Import stok awal dari Excel ==========================================
# === Import stok awal dari Excel ==========================================
st.sidebar.header("🗂️ Import Stok dari Excel")
excel_file = st.sidebar.file_uploader(
    "Pilih file .xlsx / .xls", type=["xlsx", "xls"]
)

if excel_file and st.sidebar.button("🚀 Import ke Database"):
    try:
        import pandas as pd
        from io import BytesIO

        df_xl = pd.read_excel(BytesIO(excel_file.read()))

        # ↳ sesuaikan header kolom jika berbeda
        required = {"material_id", "name", "brand", "category", "stock"}
        if not required.issubset({c.lower() for c in df_xl.columns}):
            st.sidebar.error(
                f"Header Excel harus memuat kolom: {', '.join(required)}"
            )
        else:
            for _, row in df_xl.iterrows():
                upsert_item(
                    str(row["material_id"]).strip(),
                    str(row["name"]).strip(),
                    str(row["brand"]).strip(),
                    str(row["category"]).strip(),
                    int(row["stock"]),
                )
            st.sidebar.success(f"Berhasil import {len(df_xl)} baris! ✅")
            st.rerun()  # refresh tampilan tabel
    except Exception as e:
        st.sidebar.error(f"Gagal import: {e}")
      
# ---------- Transaksi ----------
if MENU == "Transaksi":
    st.header("🛒 Transaksi Barang Masuk/Keluar")
    # Autocomplete via text_input + suggestions table
    search = st.text_input("Cari barang (nama / merk)")
    df_items = fetch_items(search)
    if not df_items.empty and search:
        st.dataframe(df_items[["material_id", "name", "brand", "stock"]], height=150)
    material_id = st.text_input("Material ID (mis. PEN-001)")
    qty = st.number_input("Jumlah", min_value=1, step=1)
    action = st.selectbox("Aksi", ["masuk", "keluar"])
    if st.button("Submit"):
        if add_transaction(material_id, int(qty), action):
            st.success("Transaksi berhasil!")

    st.subheader("Riwayat Terbaru")
    st.dataframe(fetch_transactions(20))

# ---------- Data Barang ----------
elif MENU == "Data Barang":
    st.header("📦 Data Barang")
    tab1, tab2 = st.tabs(["Daftar", "Tambah / Edit"])

    with tab1:
        st.dataframe(fetch_items())

    with tab2:
        st.subheader("Form Tambah / Edit Barang")
        col1, col2 = st.columns(2)
        with col1:
            material_id = st.text_input("Material ID* (unik)")
            name = st.text_input("Nama Barang*")
            brand = st.text_input("Merk*")
        with col2:
            category = st.selectbox("Kategori", ["Alat Tulis", "Kertas", "Alat Kantor", "Elektronik", "Lainnya"])
            stock = st.number_input("Stok", min_value=0, step=1)
        if st.button("Simpan / Perbarui"):
            if material_id and name and brand:
                upsert_item(material_id, name, brand, category, int(stock))
                st.success("Data disimpan.")
            else:
                st.error("Material ID, Nama, Merk wajib diisi!")
        st.divider()
        st.subheader("Hapus Barang")
        del_material = st.text_input("Material ID untuk dihapus")
        if st.button("Hapus Barang"):
            if del_material:
                delete_item(del_material)
                st.success("Barang dihapus.")

# ---------- Riwayat ----------
else:
    st.header("📜 Riwayat Transaksi")
    df = fetch_transactions()
    st.dataframe(df)
    if st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode(),
        file_name=f"riwayat_{date.today()}.csv",
        mime="text/csv",
    ):
        st.success("Berhasil diunduh.")
