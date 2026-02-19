import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Mi Cartera", layout="wide")

st.title("🚀 Dashboard de Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    # =========================
    # CARGA
    # =========================
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df = df[df["IDENTIFICADOR"].notna()]
    df["ACCIONES"] = pd.to_numeric(df["ACCIONES"], errors="coerce")
    df["PRECIO TOTAL"] = pd.to_numeric(df["PRECIO TOTAL"], errors="coerce")

    # =========================
    # CONVERSIÓN TICKER
    # =========================
    def convertir_ticker(t):
        if t.startswith("BME:"):
            return t.split(":")[1] + ".MC"
        if t.startswith("LON:"):
            return t.split(":")[1] + ".L"
        if t.startswith("ETR:") or t.startswith("vie:"):
            return t.split(":")[1] + ".DE"
        if t.startswith("AMS:"):
            return t.split(":")[1] + ".AS"
        if t.startswith("epa:"):
            return t.split(":")[1] + ".PA"
        if t.startswith("NYSE:") or t.startswith("NASDAQ:"):
            return t.split(":")[1]
        return t

    df["Ticker"] = df["IDENTIFICADOR"].apply(convertir_ticker).str.upper()

    eurusd = float(yf.Ticker("EURUSD=X").history(period="1d")["Close"].iloc[-1])
    gbpusd = float(yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1])

    precios = []

    for index, row in df.iterrows():
        ticker = row["Ticker"]
        divisa = str(row["DIVISA"]).upper()

        try:
            hist = yf.Ticker(ticker).history(period="1d")
            precio = float(hist["Close"].iloc[-1])

            if divisa == "USD":
                precio = precio / eurusd
            elif divisa == "GBP":
                precio = precio / 100
                precio = (precio * gbpusd) / eurusd

            precios.append(precio)

        except:
            precios.append(None)

    df["Precio Actual €"] = precios
    df = df.dropna(subset=["Precio Actual €"])

    # =========================
    # CÁLCULOS
    # =========================
    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Diferencia €"] = df["Valor Actual €"] - df["PRECIO TOTAL"]
    df["Rentabilidad %"] = df["Diferencia €"] / df["PRECIO TOTAL"] * 100

    total_actual = df["Valor Actual €"].sum()
    df["Peso %"] = df["Valor Actual €"] / total_actual * 100

    # =========================
    # DONUT POR TIPO
    # =========================
    st.subheader("📊 Distribución por Tipo")
    tipo_chart = df.groupby("TIPO")["Valor Actual €"].sum().reset_index()

    fig_tipo = px.pie(
        tipo_chart,
        names="TIPO",
        values="Valor Actual €",
        hole=0.5,
        color_discrete_sequence=px.colors.sequential.Tealgrn
    )

    st.plotly_chart(fig_tipo, use_container_width=True)

    st.divider()

    # =========================
    # TABLA REORDENADA
    # =========================
    st.subheader("📋 Detalle de posiciones")

    tabla = df[[
        "EMPRESA",
        "ACCIONES",
        "PRECIO TOTAL",
        "Precio Actual €",
        "Diferencia €",
        "Rentabilidad %",
        "Peso %"
    ]].copy()

    tabla.rename(columns={
        "PRECIO TOTAL": "Precio Compra Total €"
    }, inplace=True)

    # =========================
    # ESTILOS
    # =========================
    def color_diferencia(val):
        return "color: #00ff88" if val > 0 else "color: #ff4d4d"

    def color_rentabilidad(val):
        return "color: #00ff88" if val > 0 else "color: #ff4d4d"

    def color_peso(val):
        return "color: #ff4d4d" if val > 3 else "color: white"

    styled = tabla.style \
        .applymap(color_diferencia, subset=["Diferencia €"]) \
        .applymap(color_rentabilidad, subset=["Rentabilidad %"]) \
        .applymap(color_peso, subset=["Peso %"]) \
        .format({
            "Precio Compra Total €": "{:,.2f}",
            "Precio Actual €": "{:,.2f}",
            "Diferencia €": "{:,.2f}",
            "Rentabilidad %": "{:.2f}",
            "Peso %": "{:.2f}"
        })

    st.dataframe(styled, use_container_width=True)

else:
    st.info("Sube tu archivo Excel para empezar.")
