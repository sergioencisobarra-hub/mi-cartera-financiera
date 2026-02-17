import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Tomamos la quinta columna como ticker (índice 4)
    df["Ticker"] = df.iloc[:, 4].astype(str)

    # Función para convertir a formato Yahoo Finance
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

    df["Ticker"] = df["Ticker"].apply(convertir_ticker).str.upper()

    tickers = df["Ticker"].tolist()

    # Descargar precios
    data = yf.download(tickers, period="1d", progress=False)

    if "Close" not in data:
        st.error("No se pudieron descargar precios.")
        st.stop()

    precios_cierre = data["Close"].iloc[-1]

    # Descargar tipos de cambio
    eurusd = yf.download("EURUSD=X", period="1d", progress=False)["Close"].iloc[-1]
    eurgbp = yf.download("EURGBP=X", period="1d", progress=False)["Close"].iloc[-1]

    precios_actuales = []
    tickers_validos = []

    for t in df["Ticker"]:
        if t in precios_cierre.index:
            precio = precios_cierre[t]

            # UK → GBP
            if t.endswith(".L"):
                precio = precio / eurgbp

            # USA → USD (sin sufijo de país)
            elif "." not in t:
                precio = precio / eurusd

            precios_actuales.append(precio)
            tickers_validos.append(True)
        else:
            st.warning(f"No se encontró precio para {t}")
            precios_actuales.append(None)
            tickers_validos.append(False)

    df["Precio Actual €"] = precios_actuales

    # Eliminar posiciones sin precio
    df = df.dropna(subset=["Precio Actual €"])

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
    st.dataframe(
        df.sort_values("Rentabilidad %", ascending=False),
        use_container_width=True
    )

    st.subheader("Top 10 Ganadores")
    st.bar_chart(
        df.sort_values("Rentabilidad %", ascending=False)
        .head(10)
        .set_index("Ticker")["Rentabilidad %"]
    )

    st.subheader("Top 10 Perdedores")
    st.bar_chart(
        df.sort_values("Rentabilidad %")
        .head(10)
        .set_index("Ticker")["Rentabilidad %"]
    )

else:
    st.info("Sube tu archivo Excel para empezar.")
