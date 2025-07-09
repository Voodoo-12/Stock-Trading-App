import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class StockTradingAdvisor:
    def __init__(self, symbol: str, start: str, end: str):
        self.symbol = symbol
        self.start = start
        self.end = end
        self.data = self.download_data()
        self.signals = self.generate_signals()

    def download_data(self):
        df = yf.download(self.symbol, start=self.start, end=self.end)
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        return df

    def generate_signals(self):
        df = self.data.copy()
        df['Signal'] = 0
        df['Reason'] = ''
        df.loc[(df['SMA50'] > df['SMA200']) & (df['SMA50'].shift(1) <= df['SMA200'].shift(1)), 'Signal'] = 1
        df.loc[(df['SMA50'] < df['SMA200']) & (df['SMA50'].shift(1) >= df['SMA200'].shift(1)), 'Signal'] = -1
        df.loc[df['Signal'] == 1, 'Reason'] = 'Golden Cross: SMA50 crossed above SMA200 (Buy Signal)'
        df.loc[df['Signal'] == -1, 'Reason'] = 'Death Cross: SMA50 crossed below SMA200 (Sell Signal)'
        return df.dropna()

    def simulate_trades(self, initial_balance=10000):
        df = self.signals.copy()
        balance = initial_balance
        position = 0
        trade_log = []

        for i, row in df.iterrows():
            price = row['Close']
            if row['Signal'] == 1 and position == 0:
                position = balance / price
                balance = 0
                trade_log.append((i, 'BUY', price, row['Reason']))
            elif row['Signal'] == -1 and position > 0:
                balance = position * price
                position = 0
                trade_log.append((i, 'SELL', price, row['Reason']))

        final_balance = balance + (position * df['Close'].iloc[-1])
        return trade_log, final_balance

    def plot(self):
        df = self.signals
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(df['Close'], label='Close Price')
        ax.plot(df['SMA50'], label='SMA50')
        ax.plot(df['SMA200'], label='SMA200')

        buys = df[df['Signal'] == 1]
        sells = df[df['Signal'] == -1]

        ax.scatter(buys.index, buys['Close'], marker='^', color='g', label='Buy Signal')
        ax.scatter(sells.index, sells['Close'], marker='v', color='r', label='Sell Signal')

        ax.set_title(f'{self.symbol} Buy/Sell Signals')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend()
        ax.grid()
        return fig

# Streamlit UI
st.title("Stock Trading Advisor")
symbol = st.text_input("Enter Stock Symbol (e.g., AAPL)", "AAPL")
start_date = st.date_input("Start Date", pd.to_datetime("2020-01-01"))
end_date = st.date_input("End Date", pd.to_datetime("2023-01-01"))
initial_balance = st.number_input("Initial Balance ($)", min_value=1000, value=10000, step=500)

if st.button("Run Analysis"):
    advisor = StockTradingAdvisor(symbol, str(start_date), str(end_date))
    trades, final_balance = advisor.simulate_trades(initial_balance)

    st.subheader("Trade Log")
    trade_df = pd.DataFrame(trades, columns=['Date', 'Action', 'Price', 'Reason'])
    st.dataframe(trade_df)

    st.subheader(f"Final Balance: ${final_balance:.2f}")

    st.subheader("Signal Chart")
    fig = advisor.plot()
    st.pyplot(fig)
