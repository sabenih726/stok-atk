import sqlite3   # <— ini dia yang wajib ada
import pandas as pd
from datetime import datetime
import streamlit as st

class Database:
    def __init__(self, db_name='office_supplies.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ===== Tabel Karyawan
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ===== Tabel Barang/Inventaris
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL DEFAULT 0,
                unit TEXT DEFAULT 'pcs',
                min_stock INTEGER DEFAULT 10,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ===== Tabel Permintaan
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requisitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                employee_name TEXT NOT NULL,
                department TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        ''')
        
        # ===== Detail Permintaan
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requisition_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requisition_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (requisition_id) REFERENCES requisitions(id),
                FOREIGN KEY (item_id) REFERENCES inventory(id)
            )
        ''')
        
        # ===== Riwayat Transaksi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                employee_name TEXT NOT NULL,
                department TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                requisition_id INTEGER,
                FOREIGN KEY (requisition_id) REFERENCES requisitions(id)
            )
        ''')
        
        conn.commit()
        
        # ===== Sample Data Inventory
        cursor.execute('SELECT COUNT(*) FROM inventory')
        if cursor.fetchone()[0] == 0:
            sample_items = [
                ('Pulpen', 100, 'pcs', 20),
                ('Pensil', 150, 'pcs', 30),
                ('Kertas A4', 50, 'rim', 10),
                ('Stapler', 20, 'pcs', 5),
                ('Penghapus', 80, 'pcs', 20),
                ('Spidol', 60, 'pcs', 15),
                ('Binder Clip', 200, 'pcs', 50),
                ('Post-it Notes', 100, 'pack', 20),
                ('Amplop', 500, 'pcs', 100),
                ('Map Folder', 75, 'pcs', 15)
            ]
            cursor.executemany('''
                INSERT INTO inventory (item_name, quantity, unit, min_stock)
                VALUES (?, ?, ?, ?)
            ''', sample_items)
            conn.commit()
        
        # ===== Sample Data Employees
        cursor.execute('SELECT COUNT(*) FROM employees')
        if cursor.fetchone()[0] == 0:
            sample_employees = [
                ('John Doe', 'IT', 'john@company.com'),
                ('Jane Smith', 'HR', 'jane@company.com'),
                ('Bob Johnson', 'Finance', 'bob@company.com'),
                ('Alice Brown', 'Marketing', 'alice@company.com')
            ]
            cursor.executemany('''
                INSERT INTO employees (name, department, email)
                VALUES (?, ?, ?)
            ''', sample_employees)
            conn.commit()
        
        conn.close()

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            conn.close()
            return results
        else:
            conn.commit()
            lastrowid = cursor.lastrowid
            conn.close()
            return lastrowid
