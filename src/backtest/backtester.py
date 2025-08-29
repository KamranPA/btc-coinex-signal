import pandas as pd

class Backtester:
    def __init__(self, df):
        self.df = df
        self.trades = []

    def run(self):
        position = None
        entry_idx = None

        for i in range(len(self.df)):
            if self.df['signal'].iloc[i] == 1 and not position:
                entry_price = self.df['close'].iloc[i]
                stop_loss = self.df['low'].iloc[i] * 0.99  # 1%
                take_profit = entry_price * 1.03  # 3%
                entry_idx = i
                position = 'long'

            elif position == 'long':
                high = self.df['high'].iloc[i]
                low = self.df['low'].iloc[i]

                if low <= stop_loss:
                    self.trades.append({
                        'entry': entry_price,
                        'exit': stop_loss,
                        'tp': take_profit,
                        'sl': stop_loss,
                        'success': False,
                        'type': 'long'
                    })
                    position = None
                elif high >= take_profit:
                    self.trades.append({
                        'entry': entry_price,
                        'exit': take_profit,
                        'tp': take_profit,
                        'sl': stop_loss,
                        'success': True,
                        'type': 'long'
                    })
                    position = None

        self._analyze_results()
        return self.summary

    def _analyze_results(self):
        df_trades = pd.DataFrame(self.trades)
        total = len(df_trades)
        wins = df_trades['success'].sum()
        win_rate = wins / total if total > 0 else 0
        drawdown = self._calculate_max_drawdown()

        self.summary = {
            'total_trades': total,
            'successful_trades': wins,
            'failed_trades': total - wins,
            'win_rate': round(win_rate * 100, 2),
            'max_drawdown': round(drawdown * 100, 2),
            'trades': self.trades
        }
