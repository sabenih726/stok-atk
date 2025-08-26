#!/usr/bin/env python3
"""
Script untuk menginisialisasi database PostgreSQL dengan data sample ATK
"""

import uuid
from datetime import datetime, timedelta
from utils.db_manager import DatabaseManager

def create_sample_inventory():
    """Membuat data inventory sample"""
    sample_items = [
        {
            'item_id': str(uuid.uuid4())[:8],
            'item_name': 'Pulpen Pilot G2',
            'category': 'Alat Tulis',
            'initial_stock': 100,
            'current_stock': 85,
            'minimum_stock': 20,
            'unit': 'pcs',
            'unit_price': 5500.0,
            'description': 'Pulpen gel hitam Pilot G2 0.7mm'
        },
        {
            'item_id': str(uuid.uuid4())[:8],
            'item_name': 'Kertas A4 70gsm',
            'category': 'Kertas',
            'initial_stock': 50,
            'current_stock': 35,
            'minimum_stock': 10,
            'unit': 'rim',
            'unit_price': 65000.0,
            'description': 'Kertas A4 putih 70gsm, 500 lembar per rim'
        },
        {
            'item_id': str(uuid.uuid4())[:8],
            'item_name': 'Stapler Kenko HD-10',
            'category': 'Perlengkapan Kantor',
            'initial_stock': 20,
            'current_stock': 18,
            'minimum_stock': 5,
            'unit': 'pcs',
            'unit_price': 25000.0,
            'description': 'Stapler kecil untuk 10 lembar'
        },
        {
            'item_id': str(uuid.uuid4())[:8],
            'item_name': 'Folder L Plastik',
            'category': 'File & Folder',
            'initial_stock': 200,
            'current_stock': 150,
            'minimum_stock': 50,
            'unit': 'pcs',
            'unit_price': 2500.0,
            'description': 'Folder L plastik transparan A4'
        },
        {
            'item_id': str(uuid.uuid4())[:8],
            'item_name': 'Tinta Printer Canon Black',
            'category': 'Elektronik',
            'initial_stock': 30,
            'current_stock': 12,
            'minimum_stock': 8,
            'unit': 'pcs',
            'unit_price': 75000.0,
            'description': 'Cartridge tinta hitam Canon original'
        },
        {
            'item_id': str(uuid.uuid4())[:8],
            'item_name': 'Spidol Whiteboard Snowman',
            'category': 'Alat Tulis',
            'initial_stock': 50,
            'current_stock': 25,
            'minimum_stock': 15,
            'unit': 'pcs',
            'unit_price': 8500.0,
            'description': 'Spidol papan tulis warna hitam'
        },
        {
            'item_id': str(uuid.uuid4())[:8],
            'item_name': 'Tissue Paseo 250 Sheet',
            'category': 'Cleaning Supplies',
            'initial_stock': 40,
            'current_stock': 30,
            'minimum_stock': 10,
            'unit': 'box',
            'unit_price': 28000.0,
            'description': 'Tissue kotak 250 lembar'
        },
        {
            'item_id': str(uuid.uuid4())[:8],
            'item_name': 'Post-it Notes 3x3',
            'category': 'Alat Tulis',
            'initial_stock': 100,
            'current_stock': 45,
            'minimum_stock': 25,
            'unit': 'pack',
            'unit_price': 15000.0,
            'description': 'Sticky notes kuning 3x3 inch'
        }
    ]
    return sample_items

def create_sample_orders():
    """Membuat data order sample"""
    # Get some sample item IDs from inventory first
    db_manager = DatabaseManager()
    inventory_df = db_manager.load_inventory()
    
    if inventory_df.empty:
        print("No inventory items found. Please add inventory first.")
        return []
    
    sample_orders = []
    item_ids = inventory_df['item_id'].tolist()[:3]  # Take first 3 items
    
    for i, item_id in enumerate(item_ids):
        item = inventory_df[inventory_df['item_id'] == item_id].iloc[0]
        order = {
            'order_id': str(uuid.uuid4())[:8],
            'item_id': item_id,
            'item_name': item['item_name'],
            'category': item['category'],
            'quantity': 5 + i,
            'unit': item['unit'],
            'requester_name': ['Ahmad Budiman', 'Siti Rahayu', 'Budi Santoso'][i],
            'department': ['IT', 'HR', 'Finance'][i],
            'purpose': [
                'Untuk keperluan dokumentasi project',
                'Administrasi rekrutment karyawan baru',
                'Keperluan laporan keuangan bulanan'
            ][i],
            'priority': ['Normal', 'Urgent', 'Normal'][i],
            'status': ['Pending', 'Approved', 'Pending'][i],
            'approved_by': 'Admin' if i == 1 else '',
            'approved_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S') if i == 1 else '',
            'notes': 'Sudah disetujui untuk penggunaan' if i == 1 else ''
        }
        sample_orders.append(order)
    
    return sample_orders

def initialize_database():
    """Inisialisasi database dengan data sample"""
    print("🚀 Menginisialisasi database PostgreSQL dengan data sample...")
    
    try:
        db_manager = DatabaseManager()
        
        # Check if data already exists
        existing_inventory = db_manager.load_inventory()
        if not existing_inventory.empty:
            print("⚠️  Database sudah berisi data inventory. Skipping initialization.")
            return True
        
        # Add sample inventory
        print("📦 Menambahkan data inventory sample...")
        sample_items = create_sample_inventory()
        
        for item in sample_items:
            success = db_manager.add_inventory_item(item)
            if success:
                print(f"   ✅ {item['item_name']} - {item['current_stock']} {item['unit']}")
            else:
                print(f"   ❌ Gagal menambahkan {item['item_name']}")
        
        # Add sample orders
        print("📋 Menambahkan data order sample...")
        sample_orders = create_sample_orders()
        
        for order in sample_orders:
            success = db_manager.add_order(order)
            if success:
                print(f"   ✅ Order {order['order_id']} - {order['item_name']} ({order['status']})")
            else:
                print(f"   ❌ Gagal menambahkan order {order['order_id']}")
        
        print("\n🎉 Database berhasil diinisialisasi dengan data sample!")
        print("📊 Summary:")
        stats = db_manager.get_statistics()
        print(f"   - Total Items: {stats.get('total_items', 0)}")
        print(f"   - Total Orders: {stats.get('total_orders', 0)}")
        print(f"   - Pending Orders: {stats.get('pending_orders', 0)}")
        print(f"   - Low Stock Items: {stats.get('low_stock_items', 0)}")
        print(f"   - Total Inventory Value: Rp {stats.get('total_inventory_value', 0):,.0f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

if __name__ == "__main__":
    initialize_database()