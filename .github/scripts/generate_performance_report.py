import json
import os
from datetime import datetime

def generate_performance_report():
    """تولید گزارش تحلیل عملکرد"""
    
    try:
        # خواندن فایل performance
        with open('logs/performance_report.json', 'r') as f:
            performance_data = json.load(f)
        
        # ایجاد گزارش Markdown
        report = f"""
# Performance Analysis Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Workflow Run:** #{os.getenv('GITHUB_RUN_ID', 'Unknown')}

## 📊 Summary
- **Total Duration:** {performance_data.get('total_duration_seconds', 0):.2f} seconds
- **Memory Usage:** {performance_data.get('memory_usage_mb', 0):.2f} MB
- **CPU Usage:** {performance_data.get('cpu_percent', 0):.2f}%

## ⚡ Operation Times
"""
        
        # اضافه کردن زمان‌های عملیات
        operation_times = performance_data.get('operation_times', {})
        for operation, duration in operation_times.items():
            report += f"- **{operation}:** {duration:.4f} seconds\n"
        
        # اضافه کردن متریک‌های دقیق
        report += "\n## 📈 Detailed Metrics\n"
        detailed_metrics = performance_data.get('detailed_metrics', [])
        for metric in detailed_metrics[-5:]:  # آخرین 5 متریک
            report += f"- {metric['timestamp']}: {metric['operation']} - {metric['duration_seconds']}s, {metric['memory_mb']}MB\n"
        
        # ذخیره گزارش
        with open('performance_analysis.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("Performance report generated successfully")
        
    except Exception as e:
        print(f"Error generating performance report: {e}")

if __name__ == "__main__":
    generate_performance_report()
