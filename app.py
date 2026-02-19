import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Mi Cartera", layout="wide")
st.title("🚀 Dashboard de Cartera – Control de Riesgo")

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

    df = df.sort_values("Peso %", ascending=False).reset_index(drop=True)
    df["Ranking"] = df.index + 1

    # =========================
    # MÉTRICAS DE CONCENTRACIÓN
    # =========================
    top3 = df["Peso %"].head(3).sum()
    mayor = df["Peso %"].max()
    hhi = np.sum((df["Peso %"])**2)

    col1, col2, col3 = st.columns(3)

    col1.metric("Top 3 posiciones (%)", f"{top3:.2f}%")
    col2.metric("Mayor posición (%)", f"{mayor:.2f}%")
    col3.metric("Índice HHI", f"{hhi:.0f}")

    if hhi > 2500:
        st.error("⚠ Alta concentración de cartera")
    elif hhi > 1500:
        st.warning("⚠ Concentración moderada")
    else:
        st.success("✔ Cartera diversificada")

    st.divider()

    # =========================
    # TABLA FINAL
    # =========================
    tabla = df[[
        "Ranking",
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

    def color_diferencia(val):
        return "color: #00cc66" if val > 0 else "color: #ff4d4d"

    def color_peso(val):
        if val > 10:
            return "color: #ff0000"
        elif val > 5:
            return "color: #ff8800"
        elif val > 3:
            return "color: #ffaa00"
        return ""

    styled = tabla.style \
        .applymap(color_diferencia, subset=["Diferencia €", "Rentabilidad %"]) \
        .applymap(color_peso, subset=["Peso %"]) \
        .bar(subset=["Peso %"], color="#4da6ff") \
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
