import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df = df[df["IDENTIFICADOR"].notna()]
    df = df[df["IDENTIFICADOR"] != df["TIPO"]]

    df["ACCIONES"] = pd.to_numeric(df["ACCIONES"], errors="coerce")
    df["PRECIO TOTAL"] = pd.to_numeric(df["PRECIO TOTAL"], errors="coerce")

    def convertir_ticker(t):
        if t.startswith("BME:"):
            return t.split(":")[1] + ".MC"
        if t.startswith("LON:"):
            return t.split(":")[1] + ".L"
        if t.startswith("ETR:") or t.startswith("etr:") or t.startswith("vie:"):
            return t.split(":")[1] + ".DE"
        if t.startswith("AMS:"):
            return t.split(":")[1] + ".AS"
        if t.startswith("epa:"):
            return t.split(":")[1] + ".PA"
        if t.startswith("NYSE:") or t.startswith("nyse:"):
            return t.split(":")[1]
        if t.startswith("NASDAQ:"):
            return t.split(":")[1]
        return t

    df["Ticker"] = df["IDENTIFICADOR"].apply(convertir_ticker).str.upper()

    # Tipos de cambio
    eurusd = float(yf.download("EURUSD=X", period="1d", progress=False)["Close"].iloc[-1])
    gbpusd = float(yf.download("GBPUSD=X", period="1d", progress=False)["Close"].iloc[-1])

    precios = []

    for ticker in df["Ticker"]:

        try:
            datos = yf.download(ticker, period="1d", progress=False)

            if datos.empty:
                raise Exception("Sin datos")

            precio = float(datos["Close"].iloc[-1])

            # UK (.L) → GBP
            if ticker.endswith(".L"):
                precio = (precio * gbpusd) / eurusd

            # USA (sin punto)
            elif "." not in ticker:
                precio = precio / eurusd

            # Europa ya en EUR

            precios.append(precio)

        except:
            st.warning(f"No se pudo obtener precio para {ticker}")
            precios.append(None)

    df["Precio Actual €"] = precios
    df = df.dropna(subset=["ACCIONES", "PRECIO TOTAL", "Precio Actual €"])

    if df.empty:
        st.error("No hay datos válidos para calcular.")
        st.stop()

    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Inversión Inicial €"] = df["PRECIO TOTAL"]

    df["Rentabilidad €"] = df["Valor Actual €"] - df["Inversión Inicial €"]
    df["Rentabilidad %"] = df["Rentabilidad €"] / df["Inversión Inicial €"] * 100

    total_inicial = df["Inversión Inicial €"].sum()
    total_actual = df["Valor Actual €"].sum()

    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

    # Clasificación geográfica
    def clasificar_region(ticker):
        if ticker.endswith(".MC"):
            return "España"
        if ticker.endswith(".L"):
            return "UK"
        if ticker.endswith(".DE") or ticker.endswith(".AS") or ticker.endswith(".PA"):
            return "Europa"
        if "." not in ticker:
            return "USA"
        return "Otros"

    df["REGION"] = df["Ticker"].apply(clasificar_region)

    st.divider()
    st.metric("Rentabilidad Total Cartera", f"{rentabilidad_total:.2f} %")
    st.divider()

    # ACCIONES
    st.header("📈 ACCIONES")
    acciones = df[df["TIPO"] == "ACCION"]

    for region in ["España", "UK", "USA", "Europa"]:
        bloque = acciones[acciones["REGION"] == region]

        if not bloque.empty:
            st.subheader(region)

            valor = bloque["Valor Actual €"].sum()
            inversion = bloque["Inversión Inicial €"].sum()
            rent = (valor - inversion) / inversion * 100

            col1, col2 = st.columns(2)
            col1.metric("Valor Actual", f"{valor:,.2f} €")
            col2.metric("Rentabilidad", f"{rent:.2f} %")

            st.dataframe(bloque.sort_values("Rentabilidad %", ascending=False), use_container_width=True)

    # ETFs
    st.header("📊 ETFs")
    etfs = df[df["TIPO"] == "ETF"]

    if not etfs.empty:
        valor = etfs["Valor Actual €"].sum()
        inversion = etfs["Inversión Inicial €"].sum()
        rent = (valor - inversion) / inversion * 100

        col1, col2 = st.columns(2)
        col1.metric("Valor Actual ETFs", f"{valor:,.2f} €")
        col2.metric("Rentabilidad ETFs", f"{rent:.2f} %")

        st.dataframe(etfs.sort_values("Rentabilidad %", ascending=False), use_container_width=True)

    # FONDOS
    st.header("🏦 FONDOS")
    fondos = df[df["TIPO"] == "FONDO"]

    if not fondos.empty:
        valor = fondos["Valor Actual €"].sum()
        inversion = fondos["Inversión Inicial €"].sum()
        rent = (valor - inversion) / inversion * 100

        col1, col2 = st.columns(2)
        col1.metric("Valor Actual Fondos", f"{valor:,.2f} €")
        col2.metric("Rentabilidad Fondos", f"{rent:.2f} %")

        st.dataframe(fondos.sort_values("Rentabilidad %", ascending=False), use_container_width=True)

else:
    st.info("Sube tu archivo Excel para empezar.")
