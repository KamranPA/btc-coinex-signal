# logger_config.py
import logging
import os
from datetime import datetime

# ایجاد پوشه logs اگر وجود نداشته باشد
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/{datetime.now().strftime('%Y-%m-%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
