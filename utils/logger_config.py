# utils/logger_config.py
import logging
import os
from datetime import datetime

def setup_logger():
    """
    یک logger مرکزی با خروجی فایل و کنسول ایجاد می‌کند.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir,
        f"divergence_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler: فایل
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Handler: کنسول
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Logger اصلی
    logger = logging.getLogger("DivergenceBot")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # جلوگیری از لاگ تکراری در کنسول
    logger.propagate = False

    return logger

# ایجاد یک نمونه از logger برای استفاده در تمام ماژول‌ها
logger = setup_logger()
