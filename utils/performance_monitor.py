import time
import psutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """مانیتورینگ عملکرد سیستم"""
    
    def __init__(self):
        self.start_time = None
        self.operation_times = {}
        self.memory_usage = []
        
    def start_monitoring(self):
        """شروع مانیتورینگ"""
        self.start_time = time.time()
        self.operation_times = {}
        self.memory_usage = []
        logger.info("Performance monitoring started")
    
    def track_operation(self, operation_name):
        """ردیابی زمان عملیات"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                duration = end_time - start_time
                self.operation_times[operation_name] = duration
                
                # ثبت استفاده از memory
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                self.memory_usage.append({
                    "timestamp": datetime.now(),
                    "operation": operation_name,
                    "memory_mb": round(memory_usage, 2),
                    "duration_seconds": round(duration, 4)
                })
                
                logger.debug(f"Operation '{operation_name}' took {duration:.4f} seconds")
                return result
            return wrapper
        return decorator
    
    def get_performance_report(self):
        """دریافت گزارش عملکرد"""
        if not self.start_time:
            return {"error": "Monitoring not started"}
        
        total_time = time.time() - self.start_time
        process = psutil.Process()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration_seconds": round(total_time, 2),
            "operation_times": self.operation_times,
            "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(),
            "detailed_metrics": self.memory_usage
        }
        
        return report
    
    def log_performance_report(self):
        """ثبت گزارش عملکرد"""
        report = self.get_performance_report()
        logger.info("Performance Report:")
        logger.info(f"Total Duration: {report['total_duration_seconds']}s")
        logger.info(f"Memory Usage: {report['memory_usage_mb']}MB")
        logger.info(f"CPU Usage: {report['cpu_percent']}%")
        
        for op, duration in report['operation_times'].items():
            logger.info(f"  {op}: {duration:.4f}s")
        
        # ذخیره گزارش کامل
        with open("logs/performance_report.json", "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

# ایجاد instance全局
performance_monitor = PerformanceMonitor()
