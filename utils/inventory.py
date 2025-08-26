import pandas as pd
from datetime import datetime
from utils.db_manager import DatabaseManager

class InventoryManager:
    def __init__(self):
        self.data_manager = DatabaseManager()
    
    def check_stock_availability(self, item_id, requested_quantity):
        """Check if requested quantity is available in stock"""
        try:
            item = self.data_manager.get_item_by_id(item_id)
            if item is not None:
                return item['current_stock'] >= requested_quantity
            return False
        except Exception as e:
            print(f"Error checking stock availability: {e}")
            return False
    
    def reduce_stock(self, item_id, quantity):
        """Reduce stock quantity for an item"""
        try:
            item = self.data_manager.get_item_by_id(item_id)
            if item is not None and item['current_stock'] >= quantity:
                new_stock = item['current_stock'] - quantity
                updates = {
                    'current_stock': new_stock,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                return self.data_manager.update_inventory_item(item_id, updates)
            return False
        except Exception as e:
            print(f"Error reducing stock: {e}")
            return False
    
    def increase_stock(self, item_id, quantity):
        """Increase stock quantity for an item (for restocking)"""
        try:
            item = self.data_manager.get_item_by_id(item_id)
            if item is not None:
                new_stock = item['current_stock'] + quantity
                updates = {
                    'current_stock': new_stock,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                return self.data_manager.update_inventory_item(item_id, updates)
            return False
        except Exception as e:
            print(f"Error increasing stock: {e}")
            return False
    
    def set_stock(self, item_id, new_quantity):
        """Set stock to a specific quantity"""
        try:
            updates = {
                'current_stock': new_quantity,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            return self.data_manager.update_inventory_item(item_id, updates)
        except Exception as e:
            print(f"Error setting stock: {e}")
            return False
    
    def get_low_stock_alerts(self):
        """Get items that are at or below minimum stock level"""
        try:
            inventory_df = self.data_manager.load_inventory()
            if not inventory_df.empty:
                low_stock = inventory_df[inventory_df['current_stock'] <= inventory_df['minimum_stock']]
                return low_stock.to_dict('records')
            return []
        except Exception as e:
            print(f"Error getting low stock alerts: {e}")
            return []
    
    def get_out_of_stock_items(self):
        """Get items that are completely out of stock"""
        try:
            inventory_df = self.data_manager.load_inventory()
            if not inventory_df.empty:
                out_of_stock = inventory_df[inventory_df['current_stock'] == 0]
                return out_of_stock.to_dict('records')
            return []
        except Exception as e:
            print(f"Error getting out of stock items: {e}")
            return []
    
    def calculate_stock_value(self, item_id=None):
        """Calculate total stock value for an item or all items"""
        try:
            inventory_df = self.data_manager.load_inventory()
            if not inventory_df.empty:
                if item_id:
                    item_df = inventory_df[inventory_df['item_id'] == item_id]
                    if not item_df.empty:
                        return (item_df['current_stock'] * item_df['unit_price']).sum()
                    return 0
                else:
                    return (inventory_df['current_stock'] * inventory_df['unit_price']).sum()
            return 0
        except Exception as e:
            print(f"Error calculating stock value: {e}")
            return 0
    
    def get_stock_status(self, item_id):
        """Get stock status for an item (Normal, Low, Out)"""
        try:
            item = self.data_manager.get_item_by_id(item_id)
            if item is not None:
                if item['current_stock'] == 0:
                    return 'Out of Stock'
                elif item['current_stock'] <= item['minimum_stock']:
                    return 'Low Stock'
                else:
                    return 'Normal'
            return 'Unknown'
        except Exception as e:
            print(f"Error getting stock status: {e}")
            return 'Error'
    
    def get_items_by_category(self, category):
        """Get all items in a specific category"""
        try:
            inventory_df = self.data_manager.load_inventory()
            if not inventory_df.empty:
                category_items = inventory_df[inventory_df['category'] == category]
                return category_items.to_dict('records')
            return []
        except Exception as e:
            print(f"Error getting items by category: {e}")
            return []
    
    def search_items(self, search_term):
        """Search items by name or description"""
        try:
            inventory_df = self.data_manager.load_inventory()
            if not inventory_df.empty:
                search_results = inventory_df[
                    inventory_df['item_name'].str.contains(search_term, case=False, na=False) |
                    inventory_df['description'].str.contains(search_term, case=False, na=False)
                ]
                return search_results.to_dict('records')
            return []
        except Exception as e:
            print(f"Error searching items: {e}")
            return []
    
    def validate_order_quantity(self, item_id, requested_quantity):
        """Validate if order quantity is reasonable and available"""
        try:
            item = self.data_manager.get_item_by_id(item_id)
            if item is None:
                return False, "Item not found"
            
            if requested_quantity <= 0:
                return False, "Quantity must be positive"
            
            if requested_quantity > item['current_stock']:
                return False, f"Insufficient stock. Available: {item['current_stock']} {item['unit']}"
            
            # Check if quantity is reasonable (not more than 50% of current stock for high-value items)
            if item['unit_price'] > 100000 and requested_quantity > (item['current_stock'] * 0.5):
                return False, "Quantity too high for high-value item. Please contact admin."
            
            return True, "Valid quantity"
        except Exception as e:
            print(f"Error validating order quantity: {e}")
            return False, "Validation error"
    
    def get_stock_movement_history(self, item_id, days=30):
        """Get stock movement history for an item (based on orders)"""
        try:
            orders_df = self.data_manager.load_orders()
            if not orders_df.empty:
                # Filter orders for the specific item and approved status
                item_orders = orders_df[
                    (orders_df['item_id'] == item_id) & 
                    (orders_df['status'] == 'Approved')
                ]
                
                # Convert order_date to datetime for filtering
                item_orders['order_date'] = pd.to_datetime(item_orders['order_date'])
                
                # Filter by days
                cutoff_date = datetime.now() - pd.Timedelta(days=days)
                recent_orders = item_orders[item_orders['order_date'] >= cutoff_date]
                
                return recent_orders.to_dict('records')
            return []
        except Exception as e:
            print(f"Error getting stock movement history: {e}")
            return []
    
    def calculate_reorder_recommendation(self, item_id):
        """Calculate reorder recommendation based on usage pattern"""
        try:
            item = self.data_manager.get_item_by_id(item_id)
            if item is None:
                return None
            
            # Get 30-day movement history
            movement_history = self.get_stock_movement_history(item_id, 30)
            
            if not movement_history:
                # No movement history, recommend minimum stock level
                recommendation = {
                    'item_id': item_id,
                    'item_name': item['item_name'],
                    'current_stock': item['current_stock'],
                    'minimum_stock': item['minimum_stock'],
                    'recommended_order': max(0, item['minimum_stock'] - item['current_stock']),
                    'reason': 'Maintain minimum stock level'
                }
            else:
                # Calculate average daily usage
                total_used = sum([order['quantity'] for order in movement_history])
                days_with_usage = len(set([order['order_date'][:10] for order in movement_history]))
                
                if days_with_usage > 0:
                    avg_daily_usage = total_used / days_with_usage
                    # Recommend 30 days worth of stock
                    recommended_stock = avg_daily_usage * 30
                    recommended_order = max(0, recommended_stock - item['current_stock'])
                    
                    recommendation = {
                        'item_id': item_id,
                        'item_name': item['item_name'],
                        'current_stock': item['current_stock'],
                        'minimum_stock': item['minimum_stock'],
                        'avg_daily_usage': avg_daily_usage,
                        'recommended_stock': recommended_stock,
                        'recommended_order': recommended_order,
                        'reason': f'Based on {days_with_usage} days usage pattern'
                    }
                else:
                    recommendation = {
                        'item_id': item_id,
                        'item_name': item['item_name'],
                        'current_stock': item['current_stock'],
                        'minimum_stock': item['minimum_stock'],
                        'recommended_order': max(0, item['minimum_stock'] - item['current_stock']),
                        'reason': 'Maintain minimum stock level'
                    }
            
            return recommendation
        except Exception as e:
            print(f"Error calculating reorder recommendation: {e}")
            return None
    
    def get_category_summary(self):
        """Get summary statistics by category"""
        try:
            inventory_df = self.data_manager.load_inventory()
            if not inventory_df.empty:
                category_summary = inventory_df.groupby('category').agg({
                    'item_name': 'count',
                    'current_stock': 'sum',
                    'unit_price': 'mean'
                }).reset_index()
                
                category_summary.columns = ['Category', 'Item Count', 'Total Stock', 'Avg Price']
                category_summary['Total Value'] = inventory_df.groupby('category').apply(
                    lambda x: (x['current_stock'] * x['unit_price']).sum()
                ).values
                
                return category_summary.to_dict('records')
            return []
        except Exception as e:
            print(f"Error getting category summary: {e}")
            return []
    
    def get_inventory_health_score(self):
        """Calculate overall inventory health score (0-100)"""
        try:
            inventory_df = self.data_manager.load_inventory()
            if inventory_df.empty:
                return 0
            
            total_items = len(inventory_df)
            out_of_stock = len(inventory_df[inventory_df['current_stock'] == 0])
            low_stock = len(inventory_df[
                (inventory_df['current_stock'] > 0) & 
                (inventory_df['current_stock'] <= inventory_df['minimum_stock'])
            ])
            normal_stock = total_items - out_of_stock - low_stock
            
            # Calculate score: Normal=100%, Low=50%, Out=0%
            health_score = (normal_stock * 100 + low_stock * 50) / total_items
            
            return round(health_score, 1)
        except Exception as e:
            print(f"Error calculating inventory health score: {e}")
            return 0
