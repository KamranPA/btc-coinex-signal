import pandas as pd
import matplotlib.pyplot as plt
import config
import os
from datetime import datetime

class DailyReporter:
    def __init__(self, trade_logger, filter_stats):
        self.logger = trade_logger
        self.filter_stats = filter_stats
        self.report_dir = "results"
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_report(self):
        today = datetime.now().strftime("%Y-%m-%d")
        df = self.logger.get_daily_trades()
        
‎        # محاسبه آمار
        report = {
            'date': today,
            'total_signals': len(df),
            'executed_signals': len(df[df['status'] == 'CLOSED']),
            'pending_signals': len(df[df['status'] == 'OPEN'])
        }
        
        closed_trades = df[df['status'] == 'CLOSED']
        if not closed_trades.empty:
            winning_trades = closed_trades[closed_trades['pnl'] > 0]
            losing_trades = closed_trades[closed_trades['pnl'] < 0]
            
            report.update({
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / len(closed_trades) * 100,
                'total_pnl': closed_trades['pnl'].sum(),
                'avg_win': winning_trades['pnl'].mean(),
                'avg_loss': losing_trades['pnl'].mean() if not losing_trades.empty else 0,
                'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if not losing_trades.empty else float('inf')
            })
        
‎        # تولید گزارش متنی
        report_text = self.create_report_text(report)
        print(report_text)
        
‎        # ذخیره گزارش در فایل
        with open(f"{self.report_dir}/daily_report_{today}.txt", "w") as f:
            f.write(report_text)
        
‎        # تولید و ذخیره نمودارها
        self.generate_charts(df, today)
        
        return report
    
    def create_report_text(self, report):
        text = f"📊 Daily Performance Report - {report['date']}\n"
        text += "="*50 + "\n"
        text += f"🔔 Total Signals: {report['total_signals']}\n"
        text += f"✅ Executed Signals: {report['executed_signals']}\n"
        text += f"⏳ Pending Signals: {report['pending_signals']}\n\n"
        
        if 'winning_trades' in report:
            text += "📈 Trading Performance:\n"
            text += f"• Winning Trades: {report['winning_trades']}\n"
            text += f"• Losing Trades: {report['losing_trades']}\n"
            text += f"• Win Rate: {report['win_rate']:.2f}%\n"
            text += f"• Total P&L: ${report['total_pnl']:.2f}\n"
            text += f"• Avg Win: ${report['avg_win']:.2f}\n"
            text += f"• Avg Loss: ${report['avg_loss']:.2f}\n"
            text += f"• Profit Factor: {report['profit_factor']:.2f}\n\n"
        
        text += "🔍 Filter Statistics:\n"
        for filter_name, count in self.filter_stats.items():
            text += f"• {filter_name}: {count} times\n"
        
        text += "\n💡 Conclusion:\n"
        if 'win_rate' in report and report['win_rate'] > 65:
            text += "Excellent day! Strategy performed exceptionally well. ✅"
        elif 'win_rate' in report and report['win_rate'] > 50:
            text += "Good day. Acceptable performance with room for improvement. ⚠️"
        else:
            text += "Needs strategy review and optimization. ❌"
        
        return text
    
    def generate_charts(self, df, today):
‎        # نمودار سود تجمعی
        if not df.empty and 'pnl' in df.columns:
            plt.figure(figsize=(12, 6))
            df['cumulative_pnl'] = df['pnl'].cumsum()
            plt.plot(df['entry_time'], df['cumulative_pnl'])
            plt.title(f"Cumulative P&L - {today}")
            plt.xlabel("Time")
            plt.ylabel("Profit (USD)")
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"{self.report_dir}/{today}_equity.png")
            plt.close()
        
‎        # نمودار فیلترها
        plt.figure(figsize=(10, 6))
        plt.bar(self.filter_stats.keys(), self.filter_stats.values())
        plt.title("Filter Activation Distribution")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{self.report_dir}/{today}_filters.png")
        plt.close()
