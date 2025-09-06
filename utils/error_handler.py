import logging
import traceback
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorHandler:
    """کلاس مدیریت خطاهای پیشرفته"""
    
    @staticmethod
    def handle_error(context="", raise_exception=False):
        """دکوراتور برای مدیریت خطاها"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = f"Error in {context}: {str(e)}"
                    logger.error(error_msg)
                    logger.debug(traceback.format_exc())
                    
                    # ذخیره خطا در فایل
                    ErrorHandler._log_error_to_file(context, e, traceback.format_exc())
                    
                    if raise_exception:
                        raise
                    return None
            return wrapper
        return decorator
    
    @staticmethod
    def _log_error_to_file(context, exception, traceback_str):
        """ذخیره خطا در فایل"""
        try:
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback_str
            }
            
            with open("logs/errors.jsonl", "a", encoding='utf-8') as f:
                f.write(json.dumps(error_data, ensure_ascii=False) + "\n")
                
        except Exception as e:
            print(f"Failed to log error: {str(e)}")
    
    @staticmethod
    def retry_operation(max_retries=3, delay=1, backoff=2):
        """دکوراتور برای تلاش مجدد"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        
                        if attempt < max_retries - 1:
                            time.sleep(current_delay)
                            current_delay *= backoff
                
                logger.error(f"All {max_retries} attempts failed")
                raise last_exception
            return wrapper
        return decorator

# ایجاد instance全局
error_handler = ErrorHandler()
