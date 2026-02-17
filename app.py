import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

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

    precios_unitarios = []

    for t in df["Ticker"]:
        try:
            datos = yf.download(t, period="1d", progress=False)
            if datos.empty:
                raise Exception("Sin datos")

            precio_unitario = float(datos["Close"].iloc[-1])

            # UK → GBP
            if t.endswith(".L"):
                precio_unitario = (precio_unitario * gbpusd) / eurusd

            # USA → USD
            elif "." not in t:
                precio_unitario = precio_unitario / eurusd

            # Europa → ya EUR

            precios_unitarios.append(precio_unitario)

        except:
            st.warning(f"No se pudo obtener precio para {t}")
            precios_unitarios.append(None)

    df["Precio Unitario Actual €"] = precios_unitarios
    df = df.dropna(subset=["Precio Unitario Actual €"])

    # Ahora sí: valor total actual
    df["Valor Actual €"] = df["Precio Unitario Actual €"] * df["ACCIONES"]

    df["Inversión Inicial €"] = df["PRECIO TOTAL"]

    df["Rentabilidad €"] = df["Valor Actual €"] - df["Inversión Inicial €"]
    df["Rentabilidad %"] = df["Rentabilidad €"] / df["Inversión Inicial €"] * 100

    total_inicial = float(df["Inversión Inicial €"].sum())
    total_actual = float(df["Valor Actual €"].sum())
    rentabilidad_total = ((total_actual - total_inicial) / total_inicial) * 100

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Inicial", f"{total_inicial:,.2f} €")
    col2.metric("Valor Actual", f"{total_actual:,.2f} €")
    col3.metric("Rentabilidad Total", f"{rentabilidad_total:.2f} %")

    st.divider()

    st.subheader("Detalle por posición")
    st.dataframe(
        df[[
            "Ticker",
            "ACCIONES",
            "Precio Unitario Actual €",
            "Valor Actual €",
            "Inversión Inicial €",
            "Rentabilidad €",
            "Rentabilidad %"
        ]].sort_values("Rentabilidad %", ascending=False),
        use_container_width=True
    )

else:
    st.info("Sube tu archivo Excel para empezar.")
