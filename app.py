import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    # Leer Excel
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Quinta columna = ticker
    df["Ticker_Original"] = df.iloc[:, 4].astype(str)

    # Conversión a formato Yahoo Finance
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

    st.subheader("Descargando tipos de cambio...")

    try:
        eurusd = float(yf.download("EURUSD=X", period="1d", progress=False)["Close"].iloc[-1])
        eurgbp = float(yf.download("EURGBP=X", period="1d", progress=False)["Close"].iloc[-1])
    except:
        st.error("No se pudieron descargar tipos de cambio.")
        st.stop()

    precios_actuales = []

    st.subheader("Descargando precios de mercado...")

    for t in df["Ticker"]:
        try:
            datos = yf.download(t, period="1d", progress=False)

            if datos.empty:
                raise Exception("Sin datos")

            precio = float(datos["Close"].iloc[-1])

            # Conversión divisa
            if t.endswith(".L"):  # GBP
                precio = precio / eurgbp
            elif "." not in t:  # USD
                precio = precio / eurusd

            precios_actuales.append(precio)

        except:
            st.warning(f"No se pudo obtener precio para {t}")
            precios_actuales.append(None)

    df["Precio Actual €"] = precios_actuales

    # Eliminar posiciones sin precio
    df = df.dropna(subset=["Precio Actual €"])

    if df.empty:
        st.error("No se pudo obtener ningún precio válido.")
        st.stop()

    # Cálculos financieros
    df["Precio Actual €"] = pd.to_numeric(df["Precio Actual €"], errors="coerce")
    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Inversión Inicial €"] = df["PRECIO TOTAL"]

    df["Valor Actual €"] = pd.to_numeric(df["Valor Actual €"], errors="coerce")
    df["Inversión Inicial €"] = pd.to_numeric(df["Inversión Inicial €"], errors="coerce")

    df = df.dropna(subset=["Valor Actual €", "Inversión Inicial €"])

    total_inicial = float(df["Inversión Inicial €"].sum())
    total_actual = float(df["Valor Actual €"].sum())
    rentabilidad_total = ((total_actual - total_inicial) / total_inicial) * 100

    df["Rentabilidad €"] = df["Valor Actual €"] - df["Inversión Inicial €"]
    df["Rentabilidad %"] = (df["Rentabilidad €"] / df["Inversión Inicial €"]) * 100

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Inicial", f"{total_inicial:,.2f} €")
    col2.metric("Valor Actual", f"{total_actual:,.2f} €")
    col3.metric("Rentabilidad Total", f"{rentabilidad_total:.2f} %")

    st.divider()

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
