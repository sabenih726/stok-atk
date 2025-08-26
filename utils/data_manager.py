import pandas as pd
import os
import json
from datetime import datetime
import shutil

class DataManager:
    def __init__(self):
        self.data_dir = "data"
        self.inventory_file = os.path.join(self.data_dir, "inventory.csv")
        self.orders_file = os.path.join(self.data_dir, "orders.csv")
        self.backup_dir = os.path.join(self.data_dir, "backups")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize empty CSV files if they don't exist"""
        if not os.path.exists(self.inventory_file):
            inventory_columns = [
                'item_id', 'item_name', 'category', 'initial_stock', 'current_stock',
                'minimum_stock', 'unit', 'unit_price', 'description', 'created_date', 'last_updated'
            ]
            pd.DataFrame(columns=inventory_columns).to_csv(self.inventory_file, index=False)
        
        if not os.path.exists(self.orders_file):
            orders_columns = [
                'order_id', 'item_id', 'item_name', 'category', 'quantity', 'unit',
                'requester_name', 'department', 'purpose', 'priority', 'status',
                'order_date', 'timestamp', 'approved_by', 'approved_date', 'notes'
            ]
            pd.DataFrame(columns=orders_columns).to_csv(self.orders_file, index=False)
    
    def load_inventory(self):
        """Load inventory data from CSV"""
        try:
            df = pd.read_csv(self.inventory_file)
            return df
        except Exception as e:
            print(f"Error loading inventory: {e}")
            return pd.DataFrame()
    
    def load_orders(self):
        """Load orders data from CSV"""
        try:
            df = pd.read_csv(self.orders_file)
            return df
        except Exception as e:
            print(f"Error loading orders: {e}")
            return pd.DataFrame()
    
    def save_inventory(self, df):
        """Save inventory data to CSV"""
        try:
            df.to_csv(self.inventory_file, index=False)
            return True
        except Exception as e:
            print(f"Error saving inventory: {e}")
            return False
    
    def save_orders(self, df):
        """Save orders data to CSV"""
        try:
            df.to_csv(self.orders_file, index=False)
            return True
        except Exception as e:
            print(f"Error saving orders: {e}")
            return False
    
    def add_inventory_item(self, item_data):
        """Add new inventory item"""
        try:
            df = self.load_inventory()
            new_row = pd.DataFrame([item_data])
            df = pd.concat([df, new_row], ignore_index=True)
            return self.save_inventory(df)
        except Exception as e:
            print(f"Error adding inventory item: {e}")
            return False
    
    def add_order(self, order_data):
        """Add new order"""
        try:
            df = self.load_orders()
            new_row = pd.DataFrame([order_data])
            df = pd.concat([df, new_row], ignore_index=True)
            return self.save_orders(df)
        except Exception as e:
            print(f"Error adding order: {e}")
            return False
    
    def update_inventory_item(self, item_id, updates):
        """Update inventory item"""
        try:
            df = self.load_inventory()
            mask = df['item_id'] == item_id
            
            if mask.any():
                for key, value in updates.items():
                    df.loc[mask, key] = value
                return self.save_inventory(df)
            else:
                print(f"Item ID {item_id} not found")
                return False
        except Exception as e:
            print(f"Error updating inventory item: {e}")
            return False
    
    def update_order(self, order_id, updates):
        """Update order"""
        try:
            df = self.load_orders()
            mask = df['order_id'] == order_id
            
            if mask.any():
                for key, value in updates.items():
                    df.loc[mask, key] = value
                return self.save_orders(df)
            else:
                print(f"Order ID {order_id} not found")
                return False
        except Exception as e:
            print(f"Error updating order: {e}")
            return False
    
    def delete_inventory_item(self, item_id):
        """Delete inventory item"""
        try:
            df = self.load_inventory()
            df = df[df['item_id'] != item_id]
            return self.save_inventory(df)
        except Exception as e:
            print(f"Error deleting inventory item: {e}")
            return False
    
    def delete_order(self, order_id):
        """Delete order"""
        try:
            df = self.load_orders()
            df = df[df['order_id'] != order_id]
            return self.save_orders(df)
        except Exception as e:
            print(f"Error deleting order: {e}")
            return False
    
    def get_item_by_id(self, item_id):
        """Get inventory item by ID"""
        try:
            df = self.load_inventory()
            item = df[df['item_id'] == item_id]
            return item.iloc[0] if not item.empty else None
        except Exception as e:
            print(f"Error getting item by ID: {e}")
            return None
    
    def get_order_by_id(self, order_id):
        """Get order by ID"""
        try:
            df = self.load_orders()
            order = df[df['order_id'] == order_id]
            return order.iloc[0] if not order.empty else None
        except Exception as e:
            print(f"Error getting order by ID: {e}")
            return None
    
    def backup_data(self, backup_name=None):
        """Create backup of all data"""
        try:
            if backup_name is None:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy files to backup directory
            if os.path.exists(self.inventory_file):
                shutil.copy2(self.inventory_file, backup_path)
            if os.path.exists(self.orders_file):
                shutil.copy2(self.orders_file, backup_path)
            
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_data(self, backup_name):
        """Restore data from backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if os.path.exists(backup_path):
                backup_inventory = os.path.join(backup_path, "inventory.csv")
                backup_orders = os.path.join(backup_path, "orders.csv")
                
                if os.path.exists(backup_inventory):
                    shutil.copy2(backup_inventory, self.inventory_file)
                if os.path.exists(backup_orders):
                    shutil.copy2(backup_orders, self.orders_file)
                
                return True
            else:
                print(f"Backup {backup_name} not found")
                return False
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self):
        """List available backups"""
        try:
            if os.path.exists(self.backup_dir):
                backups = [d for d in os.listdir(self.backup_dir) 
                          if os.path.isdir(os.path.join(self.backup_dir, d))]
                return sorted(backups, reverse=True)
            return []
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []
    
    def reset_orders(self):
        """Reset all orders data"""
        try:
            orders_columns = [
                'order_id', 'item_id', 'item_name', 'category', 'quantity', 'unit',
                'requester_name', 'department', 'purpose', 'priority', 'status',
                'order_date', 'timestamp', 'approved_by', 'approved_date', 'notes'
            ]
            empty_df = pd.DataFrame(columns=orders_columns)
            return self.save_orders(empty_df)
        except Exception as e:
            print(f"Error resetting orders: {e}")
            return False
    
    def reset_inventory(self):
        """Reset all inventory data"""
        try:
            inventory_columns = [
                'item_id', 'item_name', 'category', 'initial_stock', 'current_stock',
                'minimum_stock', 'unit', 'unit_price', 'description', 'created_date', 'last_updated'
            ]
            empty_df = pd.DataFrame(columns=inventory_columns)
            return self.save_inventory(empty_df)
        except Exception as e:
            print(f"Error resetting inventory: {e}")
            return False
    
    def export_all_data(self):
        """Export all data as JSON"""
        try:
            export_data = {
                'inventory': self.load_inventory().to_dict('records'),
                'orders': self.load_orders().to_dict('records'),
                'export_timestamp': datetime.now().isoformat()
            }
            
            export_file = os.path.join(self.data_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False
    
    def import_data(self, json_file_path):
        """Import data from JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'inventory' in data:
                inventory_df = pd.DataFrame(data['inventory'])
                self.save_inventory(inventory_df)
            
            if 'orders' in data:
                orders_df = pd.DataFrame(data['orders'])
                self.save_orders(orders_df)
            
            return True
        except Exception as e:
            print(f"Error importing data: {e}")
            return False
    
    def get_low_stock_items(self):
        """Get items with low stock"""
        try:
            df = self.load_inventory()
            low_stock = df[df['current_stock'] <= df['minimum_stock']]
            return low_stock
        except Exception as e:
            print(f"Error getting low stock items: {e}")
            return pd.DataFrame()
    
    def get_statistics(self):
        """Get basic statistics"""
        try:
            inventory_df = self.load_inventory()
            orders_df = self.load_orders()
            
            stats = {
                'total_items': len(inventory_df),
                'total_orders': len(orders_df),
                'pending_orders': len(orders_df[orders_df['status'] == 'Pending']) if not orders_df.empty else 0,
                'approved_orders': len(orders_df[orders_df['status'] == 'Approved']) if not orders_df.empty else 0,
                'low_stock_items': len(self.get_low_stock_items()),
                'total_inventory_value': (inventory_df['current_stock'] * inventory_df['unit_price']).sum() if not inventory_df.empty else 0
            }
            
            return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
