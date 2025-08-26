import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
from utils.db_manager import DatabaseManager

st.set_page_config(page_title="Reports", page_icon="📋", layout="wide")

# Initialize data manager
data_manager = DatabaseManager()

st.title("📋 Reports & Analytics")

# Load data
inventory_df = data_manager.load_inventory()
orders_df = data_manager.load_orders()

# Report type selection
report_type = st.selectbox(
    "Pilih Jenis Report",
    ["Inventory Report", "Order Report", "Usage Analysis", "Stock Movement", "Department Report"]
)

st.markdown("---")

if report_type == "Inventory Report":
    st.subheader("📦 Inventory Report")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        category_filter = st.multiselect("Filter Kategori", inventory_df['category'].unique() if not inventory_df.empty else [])
    with col2:
        stock_status_filter = st.selectbox("Filter Status Stok", ["Semua", "Stok Normal", "Stok Rendah", "Habis"])
    with col3:
        value_threshold = st.number_input("Nilai Minimum (Rp)", min_value=0, value=0)
    
    if not inventory_df.empty:
        # Apply filters
        filtered_inventory = inventory_df.copy()
        
        if category_filter:
            filtered_inventory = filtered_inventory[filtered_inventory['category'].isin(category_filter)]
        
        if stock_status_filter != "Semua":
            if stock_status_filter == "Habis":
                filtered_inventory = filtered_inventory[filtered_inventory['current_stock'] == 0]
            elif stock_status_filter == "Stok Rendah":
                filtered_inventory = filtered_inventory[
                    (filtered_inventory['current_stock'] > 0) & 
                    (filtered_inventory['current_stock'] <= filtered_inventory['minimum_stock'])
                ]
            elif stock_status_filter == "Stok Normal":
                filtered_inventory = filtered_inventory[filtered_inventory['current_stock'] > filtered_inventory['minimum_stock']]
        
        # Value filter
        filtered_inventory['total_value'] = filtered_inventory['current_stock'] * filtered_inventory['unit_price']
        if value_threshold > 0:
            filtered_inventory = filtered_inventory[filtered_inventory['total_value'] >= value_threshold]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Items", len(filtered_inventory))
        with col2:
            total_stock = filtered_inventory['current_stock'].sum()
            st.metric("Total Stock Units", f"{total_stock:,.0f}")
        with col3:
            total_value = filtered_inventory['total_value'].sum()
            st.metric("Total Value", f"Rp {total_value:,.0f}")
        with col4:
            avg_value = filtered_inventory['total_value'].mean() if len(filtered_inventory) > 0 else 0
            st.metric("Avg Item Value", f"Rp {avg_value:,.0f}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Stock by category
            if not filtered_inventory.empty:
                category_stock = filtered_inventory.groupby('category')['current_stock'].sum().reset_index()
                fig_category = px.pie(
                    category_stock, 
                    values='current_stock', 
                    names='category',
                    title="Stock Distribution by Category"
                )
                st.plotly_chart(fig_category, use_container_width=True)
        
        with col2:
            # Value by category
            if not filtered_inventory.empty:
                category_value = filtered_inventory.groupby('category')['total_value'].sum().reset_index()
                fig_value = px.bar(
                    category_value, 
                    x='category', 
                    y='total_value',
                    title="Value Distribution by Category"
                )
                fig_value.update_layout(xaxis_title="Category", yaxis_title="Total Value (Rp)")
                st.plotly_chart(fig_value, use_container_width=True)
        
        # Detailed table
        st.subheader("📊 Detailed Inventory Report")
        
        # Add status column
        filtered_inventory['Status'] = filtered_inventory.apply(
            lambda row: 'Habis' if row['current_stock'] == 0 
            else 'Stok Rendah' if row['current_stock'] <= row['minimum_stock'] 
            else 'Stok Normal', axis=1
        )
        
        # Select columns for display
        display_columns = [
            'item_name', 'category', 'current_stock', 'minimum_stock', 
            'unit', 'unit_price', 'total_value', 'Status'
        ]
        
        # Format the dataframe for better display
        report_df = filtered_inventory[display_columns].copy()
        report_df['unit_price'] = report_df['unit_price'].apply(lambda x: f"Rp {x:,.0f}")
        report_df['total_value'] = report_df['total_value'].apply(lambda x: f"Rp {x:,.0f}")
        
        # Column configuration
        column_config = {
            'item_name': 'Item Name',
            'category': 'Category',
            'current_stock': 'Current Stock',
            'minimum_stock': 'Min Stock',
            'unit': 'Unit',
            'unit_price': 'Unit Price',
            'total_value': 'Total Value',
            'Status': 'Status'
        }
        
        st.dataframe(
            report_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
        
        # Export option
        if st.button("📥 Export Inventory Report"):
            csv_buffer = io.StringIO()
            filtered_inventory.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("Belum ada data inventory untuk membuat report.")

elif report_type == "Order Report":
    st.subheader("📋 Order Report")
    
    if not orders_df.empty:
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Tanggal Mulai", value=datetime.now().date() - timedelta(days=30))
        with col2:
            end_date = st.date_input("Tanggal Akhir", value=datetime.now().date())
        
        # Additional filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect("Filter Status", orders_df['status'].unique())
        with col2:
            dept_filter = st.multiselect("Filter Departemen", orders_df['department'].unique())
        with col3:
            priority_filter = st.multiselect("Filter Prioritas", orders_df['priority'].unique())
        
        # Apply filters
        filtered_orders = orders_df.copy()
        filtered_orders['order_date'] = pd.to_datetime(filtered_orders['order_date'])
        
        # Date filter
        filtered_orders = filtered_orders[
            (filtered_orders['order_date'].dt.date >= start_date) &
            (filtered_orders['order_date'].dt.date <= end_date)
        ]
        
        # Other filters
        if status_filter:
            filtered_orders = filtered_orders[filtered_orders['status'].isin(status_filter)]
        if dept_filter:
            filtered_orders = filtered_orders[filtered_orders['department'].isin(dept_filter)]
        if priority_filter:
            filtered_orders = filtered_orders[filtered_orders['priority'].isin(priority_filter)]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Orders", len(filtered_orders))
        with col2:
            approved_count = len(filtered_orders[filtered_orders['status'] == 'Approved'])
            approval_rate = (approved_count / len(filtered_orders) * 100) if len(filtered_orders) > 0 else 0
            st.metric("Approval Rate", f"{approval_rate:.1f}%")
        with col3:
            total_quantity = filtered_orders['quantity'].sum()
            st.metric("Total Quantity", f"{total_quantity:,.0f}")
        with col4:
            unique_requesters = filtered_orders['requester_name'].nunique()
            st.metric("Unique Requesters", unique_requesters)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Orders by status
            status_counts = filtered_orders['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Orders by Status"
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Orders by department
            dept_counts = filtered_orders['department'].value_counts()
            fig_dept = px.bar(
                x=dept_counts.index,
                y=dept_counts.values,
                title="Orders by Department"
            )
            fig_dept.update_layout(xaxis_title="Department", yaxis_title="Number of Orders")
            st.plotly_chart(fig_dept, use_container_width=True)
        
        # Daily order trend
        st.subheader("📈 Daily Order Trend")
        daily_orders = filtered_orders.groupby(filtered_orders['order_date'].dt.date).size().reset_index()
        daily_orders.columns = ['Date', 'Orders']
        
        fig_trend = px.line(
            daily_orders,
            x='Date',
            y='Orders',
            title="Daily Orders Trend"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Detailed table
        st.subheader("📊 Detailed Order Report")
        
        # Format for display
        display_orders = filtered_orders.copy()
        display_orders['order_date'] = display_orders['order_date'].dt.strftime('%Y-%m-%d')
        
        display_columns = [
            'order_id', 'order_date', 'item_name', 'category', 'quantity', 'unit',
            'requester_name', 'department', 'priority', 'status'
        ]
        
        st.dataframe(
            display_orders[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
        # Export option
        if st.button("📥 Export Order Report"):
            csv_buffer = io.StringIO()
            filtered_orders.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"order_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("Belum ada data order untuk membuat report.")

elif report_type == "Usage Analysis":
    st.subheader("📊 Usage Analysis")
    
    if not orders_df.empty:
        # Time period selection
        period = st.selectbox("Periode Analisis", ["Last 30 Days", "Last 3 Months", "Last 6 Months", "All Time"])
        
        # Filter by period
        filtered_orders = orders_df.copy()
        filtered_orders['order_date'] = pd.to_datetime(filtered_orders['order_date'])
        
        if period == "Last 30 Days":
            cutoff_date = datetime.now() - timedelta(days=30)
        elif period == "Last 3 Months":
            cutoff_date = datetime.now() - timedelta(days=90)
        elif period == "Last 6 Months":
            cutoff_date = datetime.now() - timedelta(days=180)
        else:
            cutoff_date = filtered_orders['order_date'].min()
        
        filtered_orders = filtered_orders[filtered_orders['order_date'] >= cutoff_date]
        
        # Top requested items
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🔥 Most Requested Items**")
            top_items = filtered_orders.groupby('item_name').agg({
                'quantity': 'sum',
                'order_id': 'count'
            }).reset_index()
            top_items.columns = ['Item', 'Total Quantity', 'Order Count']
            top_items = top_items.sort_values('Order Count', ascending=False).head(10)
            
            fig_top_items = px.bar(
                top_items.head(5),
                x='Order Count',
                y='Item',
                orientation='h',
                title="Top 5 Most Requested Items"
            )
            st.plotly_chart(fig_top_items, use_container_width=True)
            
            st.dataframe(top_items, use_container_width=True, hide_index=True)
        
        with col2:
            st.write("**🏢 Most Active Departments**")
            dept_activity = filtered_orders.groupby('department').agg({
                'quantity': 'sum',
                'order_id': 'count'
            }).reset_index()
            dept_activity.columns = ['Department', 'Total Quantity', 'Order Count']
            dept_activity = dept_activity.sort_values('Order Count', ascending=False)
            
            fig_dept_activity = px.pie(
                dept_activity,
                values='Order Count',
                names='Department',
                title="Orders by Department"
            )
            st.plotly_chart(fig_dept_activity, use_container_width=True)
            
            st.dataframe(dept_activity, use_container_width=True, hide_index=True)
        
        # Usage patterns
        st.subheader("📈 Usage Patterns")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Weekly pattern
            filtered_orders['day_of_week'] = filtered_orders['order_date'].dt.day_name()
            weekly_pattern = filtered_orders.groupby('day_of_week').size()
            
            # Reorder days
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_pattern = weekly_pattern.reindex(day_order, fill_value=0)
            
            fig_weekly = px.bar(
                x=weekly_pattern.index,
                y=weekly_pattern.values,
                title="Orders by Day of Week"
            )
            st.plotly_chart(fig_weekly, use_container_width=True)
        
        with col2:
            # Monthly trend
            monthly_trend = filtered_orders.groupby(filtered_orders['order_date'].dt.to_period('M')).size()
            
            fig_monthly = px.line(
                x=monthly_trend.index.astype(str),
                y=monthly_trend.values,
                title="Monthly Order Trend"
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Category analysis
        st.subheader("📦 Category Analysis")
        
        category_analysis = filtered_orders.groupby('category').agg({
            'quantity': ['sum', 'mean'],
            'order_id': 'count'
        }).round(2)
        
        category_analysis.columns = ['Total Quantity', 'Avg Quantity', 'Order Count']
        category_analysis = category_analysis.reset_index().sort_values('Order Count', ascending=False)
        
        # Category chart
        fig_category = px.treemap(
            category_analysis,
            path=['category'],
            values='Order Count',
            title="Order Count by Category"
        )
        st.plotly_chart(fig_category, use_container_width=True)
        
        st.dataframe(category_analysis, use_container_width=True, hide_index=True)
        
    else:
        st.info("Belum ada data order untuk analisis usage.")

elif report_type == "Stock Movement":
    st.subheader("📊 Stock Movement Analysis")
    
    if not orders_df.empty and not inventory_df.empty:
        # Stock movement simulation (since we don't have historical stock data)
        st.info("📌 Note: Stock movement dihitung berdasarkan approved orders dan current inventory")
        
        # Calculate stock movements from orders
        approved_orders = orders_df[orders_df['status'] == 'Approved'].copy()
        
        if not approved_orders.empty:
            # Stock out analysis
            stock_out = approved_orders.groupby('item_name').agg({
                'quantity': 'sum',
                'order_id': 'count'
            }).reset_index()
            stock_out.columns = ['Item', 'Total Quantity Out', 'Number of Transactions']
            
            # Merge with current inventory
            stock_movement = stock_out.merge(
                inventory_df[['item_name', 'current_stock', 'unit', 'category']],
                left_on='Item',
                right_on='item_name',
                how='left'
            )
            
            # Calculate estimated initial stock
            stock_movement['Estimated Initial Stock'] = stock_movement['current_stock'] + stock_movement['Total Quantity Out']
            stock_movement['Stock Turnover %'] = (stock_movement['Total Quantity Out'] / stock_movement['Estimated Initial Stock'] * 100).round(2)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_movement = stock_movement['Total Quantity Out'].sum()
                st.metric("Total Items Moved", f"{total_movement:,.0f}")
            with col2:
                avg_turnover = stock_movement['Stock Turnover %'].mean()
                st.metric("Avg Turnover Rate", f"{avg_turnover:.1f}%")
            with col3:
                high_movement = len(stock_movement[stock_movement['Stock Turnover %'] > 50])
                st.metric("High Movement Items", high_movement)
            with col4:
                active_items = len(stock_movement)
                st.metric("Active Items", active_items)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Top moving items
                top_moving = stock_movement.nlargest(10, 'Total Quantity Out')
                fig_moving = px.bar(
                    top_moving,
                    x='Total Quantity Out',
                    y='Item',
                    orientation='h',
                    title="Top 10 Items by Quantity Moved"
                )
                st.plotly_chart(fig_moving, use_container_width=True)
            
            with col2:
                # Turnover rate distribution
                fig_turnover = px.histogram(
                    stock_movement,
                    x='Stock Turnover %',
                    title="Stock Turnover Rate Distribution",
                    nbins=20
                )
                st.plotly_chart(fig_turnover, use_container_width=True)
            
            # Movement by category
            st.subheader("📦 Movement by Category")
            category_movement = stock_movement.groupby('category').agg({
                'Total Quantity Out': 'sum',
                'Number of Transactions': 'sum',
                'Stock Turnover %': 'mean'
            }).round(2).reset_index()
            
            fig_cat_movement = px.bar(
                category_movement,
                x='category',
                y='Total Quantity Out',
                title="Total Movement by Category"
            )
            st.plotly_chart(fig_cat_movement, use_container_width=True)
            
            # Detailed movement table
            st.subheader("📊 Detailed Movement Report")
            
            display_columns = [
                'Item', 'category', 'Total Quantity Out', 'Number of Transactions',
                'current_stock', 'Estimated Initial Stock', 'Stock Turnover %', 'unit'
            ]
            
            movement_display = stock_movement[display_columns].sort_values('Stock Turnover %', ascending=False)
            
            st.dataframe(
                movement_display,
                use_container_width=True,
                hide_index=True
            )
            
            # Export option
            if st.button("📥 Export Stock Movement Report"):
                csv_buffer = io.StringIO()
                stock_movement.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"stock_movement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("Belum ada approved orders untuk analisis stock movement.")
    else:
        st.info("Belum ada data yang cukup untuk analisis stock movement.")

elif report_type == "Department Report":
    st.subheader("🏢 Department Usage Report")
    
    if not orders_df.empty:
        # Department selection
        selected_dept = st.selectbox("Pilih Departemen", ["All Departments"] + list(orders_df['department'].unique()))
        
        # Filter data
        if selected_dept == "All Departments":
            dept_orders = orders_df.copy()
        else:
            dept_orders = orders_df[orders_df['department'] == selected_dept].copy()
        
        if not dept_orders.empty:
            # Summary for selected department(s)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_orders = len(dept_orders)
                st.metric("Total Orders", total_orders)
            with col2:
                total_quantity = dept_orders['quantity'].sum()
                st.metric("Total Quantity", f"{total_quantity:,.0f}")
            with col3:
                unique_items = dept_orders['item_name'].nunique()
                st.metric("Unique Items", unique_items)
            with col4:
                unique_requesters = dept_orders['requester_name'].nunique()
                st.metric("Unique Requesters", unique_requesters)
            
            # Department comparison (if all departments selected)
            if selected_dept == "All Departments":
                st.subheader("📊 Department Comparison")
                
                dept_summary = orders_df.groupby('department').agg({
                    'order_id': 'count',
                    'quantity': 'sum',
                    'item_name': 'nunique',
                    'requester_name': 'nunique'
                }).reset_index()
                dept_summary.columns = ['Department', 'Total Orders', 'Total Quantity', 'Unique Items', 'Unique Requesters']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_dept_orders = px.bar(
                        dept_summary,
                        x='Department',
                        y='Total Orders',
                        title="Total Orders by Department"
                    )
                    st.plotly_chart(fig_dept_orders, use_container_width=True)
                
                with col2:
                    fig_dept_qty = px.bar(
                        dept_summary,
                        x='Department',
                        y='Total Quantity',
                        title="Total Quantity by Department"
                    )
                    st.plotly_chart(fig_dept_qty, use_container_width=True)
                
                st.dataframe(dept_summary, use_container_width=True, hide_index=True)
            
            # Individual department analysis
            else:
                st.subheader(f"📈 {selected_dept} Department Analysis")
                
                # Top requesters in department
                col1, col2 = st.columns(2)
                
                with col1:
                    top_requesters = dept_orders.groupby('requester_name').agg({
                        'order_id': 'count',
                        'quantity': 'sum'
                    }).reset_index()
                    top_requesters.columns = ['Requester', 'Orders', 'Total Quantity']
                    top_requesters = top_requesters.sort_values('Orders', ascending=False).head(10)
                    
                    fig_requesters = px.bar(
                        top_requesters.head(5),
                        x='Orders',
                        y='Requester',
                        orientation='h',
                        title=f"Top Requesters in {selected_dept}"
                    )
                    st.plotly_chart(fig_requesters, use_container_width=True)
                    
                    st.dataframe(top_requesters, use_container_width=True, hide_index=True)
                
                with col2:
                    # Most requested items by department
                    dept_items = dept_orders.groupby('item_name').agg({
                        'order_id': 'count',
                        'quantity': 'sum'
                    }).reset_index()
                    dept_items.columns = ['Item', 'Orders', 'Total Quantity']
                    dept_items = dept_items.sort_values('Orders', ascending=False).head(10)
                    
                    fig_dept_items = px.pie(
                        dept_items.head(5),
                        values='Orders',
                        names='Item',
                        title=f"Top Items Requested by {selected_dept}"
                    )
                    st.plotly_chart(fig_dept_items, use_container_width=True)
                    
                    st.dataframe(dept_items, use_container_width=True, hide_index=True)
            
            # Timeline analysis
            st.subheader("📅 Timeline Analysis")
            
            dept_orders['order_date'] = pd.to_datetime(dept_orders['order_date'])
            monthly_trend = dept_orders.groupby(dept_orders['order_date'].dt.to_period('M')).size().reset_index()
            monthly_trend['order_date'] = monthly_trend['order_date'].astype(str)
            monthly_trend.columns = ['Month', 'Orders']
            
            fig_timeline = px.line(
                monthly_trend,
                x='Month',
                y='Orders',
                title=f"Monthly Order Trend - {selected_dept if selected_dept != 'All Departments' else 'All Departments'}"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Export option
            if st.button("📥 Export Department Report"):
                csv_buffer = io.StringIO()
                dept_orders.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                filename_dept = selected_dept.replace(" ", "_") if selected_dept != "All Departments" else "all_departments"
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"department_report_{filename_dept}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info(f"Tidak ada data order untuk departemen {selected_dept}.")
    else:
        st.info("Belum ada data order untuk membuat department report.")

# General export all data option
st.markdown("---")
st.subheader("📁 Export All Data")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Export All Inventory Data"):
        if not inventory_df.empty:
            csv_buffer = io.StringIO()
            inventory_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="Download Inventory CSV",
                data=csv_data,
                file_name=f"all_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.error("Tidak ada data inventory untuk diekspor.")

with col2:
    if st.button("📥 Export All Order Data"):
        if not orders_df.empty:
            csv_buffer = io.StringIO()
            orders_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="Download Orders CSV",
                data=csv_data,
                file_name=f"all_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.error("Tidak ada data order untuk diekspor.")

with col3:
    if st.button("📊 Generate Summary Report"):
        # Create a comprehensive summary
        summary_data = {
            'Report Generated': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'Total Inventory Items': [len(inventory_df)],
            'Total Orders': [len(orders_df)],
            'Total Approved Orders': [len(orders_df[orders_df['status'] == 'Approved']) if not orders_df.empty else 0],
            'Total Pending Orders': [len(orders_df[orders_df['status'] == 'Pending']) if not orders_df.empty else 0],
            'Low Stock Items': [len(inventory_df[inventory_df['current_stock'] <= inventory_df['minimum_stock']]) if not inventory_df.empty else 0],
            'Total Inventory Value': [f"Rp {(inventory_df['current_stock'] * inventory_df['unit_price']).sum():,.0f}" if not inventory_df.empty else "Rp 0"]
        }
        
        summary_df = pd.DataFrame(summary_data)
        csv_buffer = io.StringIO()
        summary_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="Download Summary Report",
            data=csv_data,
            file_name=f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
