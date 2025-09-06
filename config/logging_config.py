import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging(debug_mode=False):
    """پیکربندی پیشرفته سیستم لاگینگ"""
    
    # ایجاد دایرکتوری لاگ‌ها
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # فرمت لاگ
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # سطح لاگینگ
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # تنظیم root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # حذف handlers موجود
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File Handler با rotation
    file_handler = RotatingFileHandler(
        filename=f'{log_dir}/signal_bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # اضافه کردن handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # لاگ شروع
    root_logger.info("=" * 50)
    root_logger.info("Logging system initialized")
    root_logger.info(f"Debug mode: {debug_mode}")
    root_logger.info("=" * 50)
    
    return root_logger

def get_logger(name):
    """دریافت logger با نام مشخص"""
    return logging.getLogger(name)
