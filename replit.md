# ATK Inventory Management System

## Overview

This is a comprehensive office supply (ATK - Alat Tulis Kantor) inventory management system built with Streamlit. The application provides a complete solution for managing office supplies, including inventory tracking, order processing, administrative controls, and reporting capabilities. The system is designed for small to medium organizations to efficiently manage their office supply resources with real-time stock monitoring and automated order processing.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses **Streamlit** as the web framework, providing a multi-page application structure:
- **Main Dashboard** (`app.py`) - Overview metrics and system status
- **Order Management** (`pages/1_📦_Order_ATK.py`) - User interface for creating supply requests
- **Analytics Dashboard** (`pages/2_📊_Dashboard.py`) - Visual analytics and metrics
- **Admin Panel** (`pages/3_⚙️_Admin_Panel.py`) - Administrative controls with authentication
- **Reports** (`pages/4_📋_Reports.py`) - Comprehensive reporting and data export

### Data Management Layer
The system implements a **PostgreSQL database** approach for enterprise-grade data storage:
- **DatabaseManager** (`utils/db_manager.py`) - Handles all database operations using SQLAlchemy ORM
- **InventoryManager** (`utils/inventory.py`) - Manages stock operations and business logic
- **Database Schema** (`utils/database.py`) - Defines database models and connection management
- Data is stored in PostgreSQL for scalability, ACID compliance, and enterprise features
- Built-in backup functionality and data export capabilities

### Key Design Patterns
- **Separation of Concerns** - Business logic separated from presentation layer
- **Manager Pattern** - Dedicated managers for data and inventory operations
- **Session State Management** - Streamlit session state for user authentication
- **Caching Strategy** - `@st.cache_resource` for performance optimization

### Authentication & Authorization
Simple password-based authentication for admin access:
- Session-based authentication using Streamlit's session state
- Basic password protection for administrative functions
- Default credentials system (admin123) for demo purposes

### Data Flow Architecture
1. **User Requests** → Streamlit UI → Business Logic Managers
2. **Data Operations** → DataManager → CSV File Storage
3. **Stock Management** → InventoryManager → Automated stock calculations
4. **Reporting** → Data aggregation → Plotly visualizations

## External Dependencies

### Core Framework
- **Streamlit** - Web application framework and UI components
- **Pandas** - Data manipulation and analysis operations
- **Plotly** - Interactive charts and data visualization (plotly.express and plotly.graph_objects)
- **PostgreSQL** - Enterprise-grade relational database system
- **SQLAlchemy** - Object-Relational Mapping (ORM) for database operations
- **psycopg2** - PostgreSQL adapter for Python database connectivity

### Python Standard Library
- **datetime** - Date and time operations for timestamps and filtering
- **uuid** - Unique identifier generation for orders and items
- **os** - File system operations and directory management
- **io** - Input/output operations for data export functionality
- **json** - Data serialization (prepared for future enhancements)
- **shutil** - File operations for backup functionality

### Data Storage
- **PostgreSQL Database** - Enterprise-grade relational database
  - `inventory_items` table - Inventory items and stock levels with full ACID compliance
  - `orders` table - Order history and status tracking with referential integrity
  - Built-in connection pooling and transaction management
  - Automated backup and export functionality
  - Full-text search capabilities and advanced indexing

### Visualization Dependencies
- **Plotly Express** - High-level plotting interface for quick visualizations
- **Plotly Graph Objects** - Low-level plotting for custom chart configurations

## Database Architecture

### PostgreSQL Integration
The system now uses **PostgreSQL** as the primary data storage solution, providing:

#### Database Tables
- **inventory_items**: Stores all ATK inventory data with proper indexing
- **orders**: Manages order requests with full audit trail and status tracking

#### Key Features
- **ACID Compliance**: Ensures data integrity and consistency
- **Scalability**: Handles enterprise-level data volumes efficiently
- **Backup & Recovery**: Automated database backups and point-in-time recovery
- **Security**: Role-based access control and encrypted connections
- **Performance**: Optimized queries with proper indexing strategies

#### Environment Configuration
The system automatically connects to PostgreSQL using these environment variables:
- `DATABASE_URL` - Complete connection string
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` - Individual connection parameters

#### Initialization
Run `python init_sample_data.py` to initialize the database with sample ATK data for testing and development.