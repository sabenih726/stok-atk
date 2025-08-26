import pandas as pd
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from utils.database import engine, InventoryItem, Order, get_db, init_database
import uuid

class DatabaseManager:
    def __init__(self):
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        # Initialize database tables
        init_database()
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def load_inventory(self):
        """Load inventory data from PostgreSQL"""
        try:
            session = self.get_session()
            items = session.query(InventoryItem).all()
            session.close()
            
            data = []
            for item in items:
                data.append({
                    'item_id': item.item_id,
                    'item_name': item.item_name,
                    'category': item.category,
                    'initial_stock': item.initial_stock,
                    'current_stock': item.current_stock,
                    'minimum_stock': item.minimum_stock,
                    'unit': item.unit,
                    'unit_price': item.unit_price,
                    'description': item.description,
                    'created_date': item.created_date.strftime('%Y-%m-%d') if item.created_date else '',
                    'last_updated': item.last_updated.strftime('%Y-%m-%d %H:%M:%S') if item.last_updated else ''
                })
            
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error loading inventory: {e}")
            return pd.DataFrame()
    
    def load_orders(self):
        """Load orders data from PostgreSQL"""
        try:
            session = self.get_session()
            orders = session.query(Order).order_by(Order.timestamp.desc()).all()
            session.close()
            
            data = []
            for order in orders:
                data.append({
                    'order_id': order.order_id,
                    'item_id': order.item_id,
                    'item_name': order.item_name,
                    'category': order.category,
                    'quantity': order.quantity,
                    'unit': order.unit,
                    'requester_name': order.requester_name,
                    'department': order.department,
                    'purpose': order.purpose,
                    'priority': order.priority,
                    'status': order.status,
                    'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else '',
                    'timestamp': order.timestamp.strftime('%Y-%m-%d %H:%M:%S') if order.timestamp else '',
                    'approved_by': order.approved_by or '',
                    'approved_date': order.approved_date.strftime('%Y-%m-%d %H:%M:%S') if order.approved_date else '',
                    'notes': order.notes or ''
                })
            
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error loading orders: {e}")
            return pd.DataFrame()
    
    def add_inventory_item(self, item_data):
        """Add new inventory item to PostgreSQL"""
        try:
            session = self.get_session()
            
            new_item = InventoryItem(
                item_id=item_data['item_id'],
                item_name=item_data['item_name'],
                category=item_data['category'],
                initial_stock=item_data.get('initial_stock', 0),
                current_stock=item_data.get('current_stock', 0),
                minimum_stock=item_data.get('minimum_stock', 0),
                unit=item_data['unit'],
                unit_price=item_data.get('unit_price', 0.0),
                description=item_data.get('description', ''),
                created_date=datetime.now(),
                last_updated=datetime.now()
            )
            
            session.add(new_item)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error adding inventory item: {e}")
            return False
    
    def add_order(self, order_data):
        """Add new order to PostgreSQL"""
        try:
            session = self.get_session()
            
            new_order = Order(
                order_id=order_data['order_id'],
                item_id=order_data['item_id'],
                item_name=order_data['item_name'],
                category=order_data['category'],
                quantity=order_data['quantity'],
                unit=order_data['unit'],
                requester_name=order_data['requester_name'],
                department=order_data['department'],
                purpose=order_data.get('purpose', ''),
                priority=order_data.get('priority', 'Normal'),
                status=order_data.get('status', 'Pending'),
                order_date=datetime.now(),
                timestamp=datetime.now(),
                approved_by=order_data.get('approved_by', ''),
                approved_date=datetime.strptime(order_data['approved_date'], '%Y-%m-%d %H:%M:%S') if order_data.get('approved_date') else None,
                notes=order_data.get('notes', '')
            )
            
            session.add(new_order)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error adding order: {e}")
            return False
    
    def update_inventory_item(self, item_id, updates):
        """Update inventory item in PostgreSQL"""
        try:
            session = self.get_session()
            item = session.query(InventoryItem).filter(InventoryItem.item_id == item_id).first()
            
            if item:
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                
                item.last_updated = datetime.now()
                session.commit()
                session.close()
                return True
            else:
                session.close()
                return False
        except Exception as e:
            print(f"Error updating inventory item: {e}")
            return False
    
    def update_order(self, order_id, updates):
        """Update order in PostgreSQL"""
        try:
            session = self.get_session()
            order = session.query(Order).filter(Order.order_id == order_id).first()
            
            if order:
                for key, value in updates.items():
                    if hasattr(order, key):
                        if key == 'approved_date' and value:
                            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                        setattr(order, key, value)
                
                session.commit()
                session.close()
                return True
            else:
                session.close()
                return False
        except Exception as e:
            print(f"Error updating order: {e}")
            return False
    
    def delete_inventory_item(self, item_id):
        """Delete inventory item from PostgreSQL"""
        try:
            session = self.get_session()
            item = session.query(InventoryItem).filter(InventoryItem.item_id == item_id).first()
            
            if item:
                session.delete(item)
                session.commit()
                session.close()
                return True
            else:
                session.close()
                return False
        except Exception as e:
            print(f"Error deleting inventory item: {e}")
            return False
    
    def delete_order(self, order_id):
        """Delete order from PostgreSQL"""
        try:
            session = self.get_session()
            order = session.query(Order).filter(Order.order_id == order_id).first()
            
            if order:
                session.delete(order)
                session.commit()
                session.close()
                return True
            else:
                session.close()
                return False
        except Exception as e:
            print(f"Error deleting order: {e}")
            return False
    
    def get_item_by_id(self, item_id):
        """Get inventory item by ID from PostgreSQL"""
        try:
            session = self.get_session()
            item = session.query(InventoryItem).filter(InventoryItem.item_id == item_id).first()
            session.close()
            
            if item:
                return {
                    'item_id': item.item_id,
                    'item_name': item.item_name,
                    'category': item.category,
                    'initial_stock': item.initial_stock,
                    'current_stock': item.current_stock,
                    'minimum_stock': item.minimum_stock,
                    'unit': item.unit,
                    'unit_price': item.unit_price,
                    'description': item.description,
                    'created_date': item.created_date.strftime('%Y-%m-%d') if item.created_date else '',
                    'last_updated': item.last_updated.strftime('%Y-%m-%d %H:%M:%S') if item.last_updated else ''
                }
            return None
        except Exception as e:
            print(f"Error getting item by ID: {e}")
            return None
    
    def get_order_by_id(self, order_id):
        """Get order by ID from PostgreSQL"""
        try:
            session = self.get_session()
            order = session.query(Order).filter(Order.order_id == order_id).first()
            session.close()
            
            if order:
                return {
                    'order_id': order.order_id,
                    'item_id': order.item_id,
                    'item_name': order.item_name,
                    'category': order.category,
                    'quantity': order.quantity,
                    'unit': order.unit,
                    'requester_name': order.requester_name,
                    'department': order.department,
                    'purpose': order.purpose,
                    'priority': order.priority,
                    'status': order.status,
                    'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else '',
                    'timestamp': order.timestamp.strftime('%Y-%m-%d %H:%M:%S') if order.timestamp else '',
                    'approved_by': order.approved_by or '',
                    'approved_date': order.approved_date.strftime('%Y-%m-%d %H:%M:%S') if order.approved_date else '',
                    'notes': order.notes or ''
                }
            return None
        except Exception as e:
            print(f"Error getting order by ID: {e}")
            return None
    
    def get_statistics(self):
        """Get basic statistics from PostgreSQL"""
        try:
            session = self.get_session()
            
            total_items = session.query(InventoryItem).count()
            total_orders = session.query(Order).count()
            pending_orders = session.query(Order).filter(Order.status == 'Pending').count()
            approved_orders = session.query(Order).filter(Order.status == 'Approved').count()
            
            # Get low stock items
            low_stock_items = session.query(InventoryItem).filter(
                InventoryItem.current_stock <= InventoryItem.minimum_stock
            ).count()
            
            # Calculate total inventory value
            total_value_result = session.query(
                func.sum(InventoryItem.current_stock * InventoryItem.unit_price)
            ).scalar()
            total_inventory_value = total_value_result or 0
            
            session.close()
            
            return {
                'total_items': total_items,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'approved_orders': approved_orders,
                'low_stock_items': low_stock_items,
                'total_inventory_value': total_inventory_value
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def reset_orders(self):
        """Reset all orders data in PostgreSQL"""
        try:
            session = self.get_session()
            session.query(Order).delete()
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error resetting orders: {e}")
            return False
    
    def reset_inventory(self):
        """Reset all inventory data in PostgreSQL"""
        try:
            session = self.get_session()
            session.query(InventoryItem).delete()
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error resetting inventory: {e}")
            return False
    
    def backup_data(self, backup_name=None):
        """Create backup by exporting to CSV"""
        try:
            inventory_df = self.load_inventory()
            orders_df = self.load_orders()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = f"backups/{backup_name or f'backup_{timestamp}'}"
            
            import os
            os.makedirs(backup_dir, exist_ok=True)
            
            inventory_df.to_csv(f"{backup_dir}/inventory_backup.csv", index=False)
            orders_df.to_csv(f"{backup_dir}/orders_backup.csv", index=False)
            
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def export_all_data(self):
        """Export all data to CSV files"""
        try:
            inventory_df = self.load_inventory()
            orders_df = self.load_orders()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            inventory_df.to_csv(f"inventory_export_{timestamp}.csv", index=False)
            orders_df.to_csv(f"orders_export_{timestamp}.csv", index=False)
            
            return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False
    
    def get_low_stock_items(self):
        """Get items with low stock from PostgreSQL"""
        try:
            session = self.get_session()
            items = session.query(InventoryItem).filter(
                InventoryItem.current_stock <= InventoryItem.minimum_stock
            ).all()
            session.close()
            
            low_stock_data = []
            for item in items:
                low_stock_data.append({
                    'item_id': item.item_id,
                    'item_name': item.item_name,
                    'category': item.category,
                    'current_stock': item.current_stock,
                    'minimum_stock': item.minimum_stock,
                    'unit': item.unit
                })
            
            return pd.DataFrame(low_stock_data)
        except Exception as e:
            print(f"Error getting low stock items: {e}")
            return pd.DataFrame()

    # Compatibility methods for existing code
    def save_inventory(self, df):
        """Legacy method - not used with PostgreSQL"""
        return True
    
    def save_orders(self, df):
        """Legacy method - not used with PostgreSQL"""
        return True