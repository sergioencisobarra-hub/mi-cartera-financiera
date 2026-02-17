import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip()
    st.write("Columnas detectadas:", df.columns)

    # Detectar columna ticker
    col_ticker = [c for c in df.columns if "STICKER" in c.upper()]

    if not col_ticker:
        st.error("No se encontró columna de ticker.")
        st.stop()

    df["Ticker"] = df[col_ticker[0]].astype(str)

    # Convertir formato tipo BME:ENG a ENG.MC etc. (simplificado)
    def convertir_ticker(t):
        if t.startswith("BME:"):
            return t.split(":")[1] + ".MC"
        if t.startswith("LON:"):
            return t.split(":")[1] + ".L"
        if t.startswith("ETR:") or t.startswith("etr:") or t.startswith("vie:"):
            return t.split(":")[1] + ".DE"
        if t.startswith("NYSE:") or t.startswith("nyse:") or t.startswith("NASDAQ:"):
            return t.split(":")[1]
        if t.startswith("AMS:"):
            return t.split(":")[1] + ".AS"
        if t.startswith("epa:"):
            return t.split(":")[1] + ".PA"
        return t

    df["Ticker"] = df["Ticker"].apply(convertir_ticker)

    tickers = df["Ticker"].tolist()

    data = yf.download(tickers, period="1d")["Close"].iloc[-1]

    eurusd = yf.download("EURUSD=X", period="1d")["Close"].iloc[-1]
    eurgbp = yf.download("EURGBP=X", period="1d")["Close"].iloc[-1]

    precios_actuales = []

    for t in df["Ticker"]:
        precio = data[t]

        if t.endswith(".L"):  # UK en GBP
            precio = precio / eurgbp
        elif "." not in t:  # USA en USD
            precio = precio / eurusd

        precios_actuales.append(precio)

    df["Precio Actual €"] = precios_actuales
    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Inversión Inicial €"] = df["PRECIO TOTAL"]
    df["Rentabilidad €"] = df["Valor Actual €"] - df["Inversión Inicial €"]
    df["Rentabilidad %"] = df["Rentabilidad €"] / df["Inversión Inicial €"] * 100

    total_inicial = df["Inversión Inicial €"].sum()
    total_actual = df["Valor Actual €"].sum()
    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Inicial", f"{total_inicial:,.2f} €")
    col2.metric("Valor Actual", f"{total_actual:,.2f} €")
    col3.metric("Rentabilidad Total", f"{rentabilidad_total:.2f} %")

    st.subheader("Detalle por posición")
    st.dataframe(df.sort_values("Rentabilidad %", ascending=False)_
