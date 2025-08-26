import pandas as pd
from datetime import datetime
import os

# Check if database is available
try:
    from utils.database import DATABASE_AVAILABLE
    if DATABASE_AVAILABLE:
        from utils.db_manager import DatabaseManager as PostgreSQLManager
    else:
        PostgreSQLManager = None
except ImportError:
    DATABASE_AVAILABLE = False
    PostgreSQLManager = None

# Always import CSV manager as fallback
from utils.data_manager import DataManager as CSVManager

class HybridDataManager:
    """
    Hybrid data manager that uses PostgreSQL when available, 
    falls back to CSV files otherwise
    """
    
    def __init__(self):
        self.use_postgresql = DATABASE_AVAILABLE and PostgreSQLManager is not None
        
        if self.use_postgresql:
            try:
                self.manager = PostgreSQLManager()
                self.storage_type = "PostgreSQL"
            except Exception as e:
                print(f"Failed to initialize PostgreSQL: {e}")
                print("Falling back to CSV storage...")
                self.manager = CSVManager()
                self.use_postgresql = False
                self.storage_type = "CSV"
        else:
            self.manager = CSVManager()
            self.storage_type = "CSV"
        
        print(f"✅ Using {self.storage_type} storage for data management")
    
    def get_storage_info(self):
        """Get information about current storage backend"""
        return {
            'type': self.storage_type,
            'postgresql_available': DATABASE_AVAILABLE,
            'using_postgresql': self.use_postgresql
        }
    
    # Delegate all methods to the underlying manager
    def load_inventory(self):
        return self.manager.load_inventory()
    
    def load_orders(self):
        return self.manager.load_orders()
    
    def save_inventory(self, df):
        return self.manager.save_inventory(df)
    
    def save_orders(self, df):
        return self.manager.save_orders(df)
    
    def add_inventory_item(self, item_data):
        return self.manager.add_inventory_item(item_data)
    
    def add_order(self, order_data):
        return self.manager.add_order(order_data)
    
    def update_inventory_item(self, item_id, updates):
        return self.manager.update_inventory_item(item_id, updates)
    
    def update_order(self, order_id, updates):
        return self.manager.update_order(order_id, updates)
    
    def delete_inventory_item(self, item_id):
        return self.manager.delete_inventory_item(item_id)
    
    def delete_order(self, order_id):
        return self.manager.delete_order(order_id)
    
    def get_item_by_id(self, item_id):
        return self.manager.get_item_by_id(item_id)
    
    def get_order_by_id(self, order_id):
        return self.manager.get_order_by_id(order_id)
    
    def backup_data(self, backup_name=None):
        return self.manager.backup_data(backup_name)
    
    def reset_orders(self):
        return self.manager.reset_orders()
    
    def reset_inventory(self):
        return self.manager.reset_inventory()
    
    def export_all_data(self):
        return self.manager.export_all_data()
    
    def get_low_stock_items(self):
        return self.manager.get_low_stock_items()
    
    def get_statistics(self):
        return self.manager.get_statistics()