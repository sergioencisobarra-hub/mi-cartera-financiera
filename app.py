import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Quinta columna = ticker
    df["Ticker_Original"] = df.iloc[:, 4].astype(str)

    def convertir_ticker(t):
        t = t.strip()
        if t.startswith("BME:"):
            return t.split(":")[1] + ".MC"
        if t.startswith("LON:"):
            return t.split(":")[1] + ".L"
        if t.startswith("ETR:") or t.startswith("etr:") or t.startswith("vie:"):
            return t.split(":")[1] + ".DE"
        if t.startswith("NYSE:") or t.startswith("nyse:"):
            return t.split(":")[1]
        if t.startswith("NASDAQ:"):
            return t.split(":")[1]
        if t.startswith("AMS:"):
            return t.split(":")[1] + ".AS"
        if t.startswith("epa:"):
            return t.split(":")[1] + ".PA"
        return t

    df["Ticker"] = df["Ticker_Original"].apply(convertir_ticker).str.upper()

    # Tipos de cambio
    eurusd = float(yf.download("EURUSD=X", period="1d", progress=False)["Close"].iloc[-1])
    gbpusd = float(yf.download("GBPUSD=X", period="1d", progress=False)["Close"].iloc[-1])

    precios_por_accion = []

    for t in df["Ticker"]:
        try:
            datos = yf.download(t, period="1d", progress=False)
            if datos.empty:
                raise Ex
