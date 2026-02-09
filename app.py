import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.title("Bitcoin Price Chart — With Moving Averages (20 & 50)")

# Sidebar controls
st.sidebar.header("Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ["Daily", "4 Hour"])
start_date = st.sidebar.date_input("Start Date", datetime.today().date() - pd.Timedelta(days=365))
end_date = st.sidebar.date_input("End Date", datetime.today().date())

if start_date > end_date:
    st.sidebar.error("Start date must be before end date")

def to_ms(dt):
    return int(datetime(dt.year, dt.month, dt.day).timestamp() * 1000)

@st.cache_data
def fetch_binance_data(start, end, interval):
    start_ms = to_ms(start)
    end_ms = to_ms(end) + (24 * 60 * 60 * 1000) - 1
    url = "https://data.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": interval,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": 1000
    }
    all_data = []
    while True:
        response = requests.get(url, params=params).json()
        if not response or "code" in response:
            break
        all_data.extend(response)
        last_open_time = response[-1][0]
        if last_open_time >= end_ms or len(response) < params["limit"]:
            break
        params["startTime"] = last_open_time + 1

    df = pd.DataFrame(all_data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["date"] = pd.to_datetime(df["open_time"], unit="ms")
    df["price"] = pd.to_numeric(df["close"])
    return df

interval = "1d" if timeframe == "Daily" else "4h"
df = fetch_binance_data(start_date, end_date, interval)

if df.empty:
    st.write("No data available for this range/timeframe.")
else:
    # Compute Moving Averages
    df = df.sort_values("date")
    df["MA20"] = df["price"].rolling(window=20).mean()  # 20‑period SMA
    df["MA50"] = df["price"].rolling(window=50).mean()  # 50‑period SMA

    st.subheader(f"BTC Price ({timeframe}) with Moving Averages from {start_date} to {end_date}")

    fig = go.Figure()

    # Price line
    fig.add_trace(go.Scatter(x=df["date"], y=df["price"], mode="lines", name="Price", line=dict(color="blue")))

    # Moving averages
    fig.add_trace(go.Scatter(x=df["date"], y=df["MA20"], mode="lines", name="20‑Period MA", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df["date"], y=df["MA50"], mode="lines", name="50‑Period MA", line=dict(color="green")))

    fig.update_layout(
        title=f"BTC {timeframe} Price with 20 & 50 Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        legend_title="Legend"
    )

    st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("Show Raw Data"):
        st.dataframe(df[["date", "price", "MA20", "MA50"]])