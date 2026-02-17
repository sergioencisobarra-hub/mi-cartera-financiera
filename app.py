import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    df["Ticker"] = df["STICKER"].str.replace(":", "-")

    tickers = df["Ticker"].tolist()
    data = yf.download(tickers, period="1d")["Close"].iloc[-1]

    eurusd = yf.download("EURUSD=X", period="1d")["Close"].iloc[-1]
    eurgbp = yf.download("EURGBP=X", period="1d")["Close"].iloc[-1]

    precios_actuales = []

    for t in df["Ticker"]:
        precio = data[t]

        if ".L" in t:  # UK
            precio = precio / eurgbp
        elif t.startswith("NYSE") or t.startswith("NASDAQ"):
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
    st.dataframe(df.sort_values("Rentabilidad %", ascending=False))

else:
    st.info("Sube tu archivo Excel para empezar.")
