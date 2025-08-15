# src/backtester.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Trade:
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_type: str  # 'long'
    pnl: float
    return_pct: float
    holding_period: timedelta
    stop_loss: float
    take_profit: float
    exit_reason: str  # 'stop_loss', 'take_profit', 'time_exit', 'manual'

class Backtester:
    def __init__(self, initial_balance: float = 10000, commission: float = 0.001):
        """
        موتور بک‌تست حرفه‌ای برای سیستم معاملاتی نهادی
        """
        self.initial_balance = initial_balance
        self.commission = commission
        self.trades: List[Trade] = []
        self.equity_curve = []

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy_func,
        risk_per_trade: float = 0.01,
        max_holding_period: int = 24  # ساعت
    ) -> Dict:
        """
        اجرای بک‌تست کامل روی داده‌های تاریخی
        
        Args:
            data: DataFrame با ستون‌های ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            strategy_func: تابع استراتژی که سیگنال تولید می‌کند
            risk_per_trade: درصد ریسک در هر معامله (پیش‌فرض 1%)
            max_holding_period: حداکثر مدت نگهداری معامله (ساعت)
            
        Returns:
            دیکشنری شامل نتایج و آمارهای بک‌تست
        """
        # اعمال استراتژی
        df = strategy_func(data.copy())
        if df.empty or 'signal' not in df.columns:
            raise ValueError("داده ورودی نامعتبر یا استراتژی خطا دارد")

        # متغیرهای مدیریت معامله
        balance = self.initial_balance
        position = None
        entry_price = None
        entry_time = None
        stop_loss = None
        take_profit = None

        for i, row in df.iterrows():
            current_time = row['timestamp']
            current_price = row['close']

            # مدیریت معامله باز
            if position:
                exit_price, exit_reason = None, None

                # بررسی حد ضرر و سود
                if current_price <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'stop_loss'
                elif current_price >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'take_profit'

                # بررسی زمان خروج
                if (current_time - entry_time) >= timedelta(hours=max_holding_period):
                    exit_price = current_price
                    exit_reason = 'time_exit'

                # اگر شرط خروج فعال شد
                if exit_price:
                    pnl = (exit_price - entry_price) * position
                    # کارمزد رفت و برگشت
                    fees = self.commission * (entry_price + exit_price) * position
                    pnl -= fees
                    balance += pnl

                    trade = Trade(
                        entry_time=entry_time,
                        exit_time=current_time,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position_type='long',
                        pnl=pnl,
                        return_pct=(pnl / (entry_price * position)) * 100,
                        holding_period=current_time - entry_time,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        exit_reason=exit_reason
                    )
                    self.trades.append(trade)

                    # ریست وضعیت
                    position = None
                    entry_price = None
                    entry_time = None
                    stop_loss = None
                    take_profit = None

            # باز کردن معامله جدید
            if not position and row['signal'] == 1:
                entry_price = current_price
                entry_time = current_time
                stop_loss = row['stop_loss']
                take_profit = row['take_profit']

                # محاسبه حجم بر اساس ریسک
                risk_amount = balance * risk_per_trade
                position_size = risk_amount / (entry_price - stop_loss)
                position = position_size

            # به‌روزرسانی منحنی سرمایه
            current_value = balance + (current_price - entry_price) * position if position else balance
            self.equity_curve.append({
                'timestamp': current_time,
                'balance': current_value
            })

        # محاسبه آمار
        return self.calculate_stats()

    def calculate_stats(self) -> Dict:
        """محاسبه آمار عملکرد بک‌تست"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'final_balance': self.initial_balance,
                'return_pct': 0,
                'annualized_return': 0,
                'trades': [],
                'equity_curve': []
            }

        trades_df = pd.DataFrame([t.__dict__ for t in self.trades])
        equity_df = pd.DataFrame(self.equity_curve)

        # محاسبات پایه
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        win_rate = (winning_trades / total_trades) * 100

        total_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        total_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')

        # حداکثر افت سرمایه (Max Drawdown)
        equity_df['peak'] = equity_df['balance'].cummax()
        equity_df['drawdown'] = (equity_df['balance'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min() * 100

        # بازده
        final_balance = equity_df.iloc[-1]['balance']
        total_return = ((final_balance - self.initial_balance) / self.initial_balance) * 100

        # بازده سالانه
        first_date = equity_df.iloc[0]['timestamp']
        last_date = equity_df.iloc[-1]['timestamp']
        years = (last_date - first_date).days / 365.25
        annualized_return = ((final_balance / self.initial_balance) ** (1/years) - 1) * 100 if years > 0 else 0

        # نسبت شارپ
        returns = equity_df['balance'].pct_change().dropna()
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 1 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'final_balance': final_balance,
            'return_pct': total_return,
            'annualized_return': annualized_return,
            'trades': trades_df.to_dict('records'),
            'equity_curve': equity_df.to_dict('records')
        }

    def generate_report(self, output_dir: str = 'results/backtest'):
        """تولید گزارش کامل بک‌تست"""
        os.makedirs(output_dir, exist_ok=True)

        # ذخیره داده‌ها
        trades_df = pd.DataFrame([t.__dict__ for t in self.trades])
        equity_df = pd.DataFrame(self.equity_curve)

        trades_df.to_csv(f'{output_dir}/trades.csv', index=False)
        equity_df.to_csv(f'{output_dir}/equity_curve.csv', index=False)

        # نمودار منحنی سرمایه
        plt.figure(figsize=(12, 6))
        plt.plot(equity_df['timestamp'], equity_df['balance'])
        plt.title('Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Balance ($)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/equity_curve.png')
        plt.close()

        # نمودار توزیع سود/زیان
        if not trades_df.empty:
            plt.figure(figsize=(10, 6))
            sns.histplot(data=trades_df, x='pnl', hue='exit_reason', multiple='stack', bins=20)
            plt.axvline(0, color='red', linestyle='--', label='Break-even')
            plt.title('Profit/Loss Distribution by Exit Reason')
            plt.xlabel('P&L ($)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(f'{output_dir}/pnl_distribution.png')
            plt.close()

        # خلاصه گزارش
        stats = self.calculate_stats()
        report_text = f"""
📊 گزارش بک‌تست
{'='*50}
• موجودی اولیه: ${self.initial_balance:,.2f}
• موجودی نهایی: ${stats['final_balance']:,.2f}
• بازده کلی: {stats['return_pct']:.2f}%
• بازده سالانه: {stats['annualized_return']:.2f}%
• تعداد معاملات: {stats['total_trades']}
• نرخ برد: {stats['win_rate']:.2f}%
• فاکتور سود: {stats['profit_factor']:.2f}
• حداکثر افت سرمایه: {stats['max_drawdown']:.2f}%
• نسبت شارپ: {stats['sharpe_ratio']:.2f}
        """.strip()

        with open(f'{output_dir}/summary.txt', 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"✅ گزارش بک‌تست در '{output_dir}' ذخیره شد")

if __name__ == "__main__":
    # نمونه استفاده
    from strategy_engine import InstitutionalStrategy
    import config

    # بارگیری داده (نمونه)
    try:
        data = pd.read_csv('historical_data.csv', parse_dates=['timestamp'])
    except:
        # داده نمونه
        dates = pd.date_range('2023-01-01', periods=1000, freq='15min')
        np.random.seed(42)
        close = 60000 + np.random.randn(1000).cumsum() * 100
        data = pd.DataFrame({
            'timestamp': dates,
            'open': close * 0.99,
            'high': close * 1.01,
            'low': close * 0.98,
            'close': close,
            'volume': np.random.randint(100, 1000, 1000)
        })

    # اجرای بک‌تست
    backtester = Backtester(initial_balance=10000, commission=0.001)
    strategy = InstitutionalStrategy()
    results = backtester.run_backtest(
        data=data,
        strategy_func=strategy.calculate,
        risk_per_trade=0.01,
        max_holding_period=24
    )

    # نمایش نتایج
    print("\n📈 نتایج بک‌تست:")
    print(f"• تعداد معاملات: {results['total_trades']}")
    print(f"• نرخ برد: {results['win_rate']:.2f}%")
    print(f"• فاکتور سود: {results['profit_factor']:.2f}")
    print(f"• بازده نهایی: {results['return_pct']:.2f}%")
    print(f"• موجودی نهایی: ${results['final_balance']:,.2f}")

    # تولید گزارش
    backtester.generate_report()
