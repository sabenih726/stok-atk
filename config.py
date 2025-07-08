import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "stok_atk.db"

# App Config
APP_TITLE = "Manajemen Stok ATK Kantor"
APP_ICON = "📝"
LAYOUT = "wide"

# Database Config
DB_CONFIG = {
    "database": str(DB_PATH),
    "check_same_thread": False
}

# Categories
CATEGORIES = [
    "Alat Tulis",
    "Kertas", 
    "Perlengkapan Kantor",
    "Elektronik",
    "Lainnya"
]

# Units
UNITS = [
    "pcs", "box", "pak", 
    "rim", "roll", "set", "buah"
]
