import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard Visual de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    # =========================
    # CARGA Y LIMPIEZA
    # =========================
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df = df[df["IDENTIFICADOR"].notna()]
    df = df[df["IDENTIFICADOR"] != df["TIPO"]]

    df["ACCIONES"] = pd.to_numeric(df["ACCIONES"], errors="coerce")
    df["PRECIO TOTAL"] = pd.to_numeric(df["PRECIO TOTAL"], errors="coerce")

    # =========================
    # CONVERSIÓN A YAHOO
    # =========================
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

    # =========================
    # TIPOS DE CAMBIO
    # =========================
    eurusd = float(yf.Ticker("EURUSD=X").history(period="1d")["Close"].iloc[-1])
    gbpusd = float(yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1])

    precios_eur = []

    for index, row in df.iterrows():

        ticker = row["Ticker"]
        divisa = str(row["DIVISA"]).upper()

        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")

            if hist.empty:
                raise Exception("Sin datos")

            precio = float(hist["Close"].iloc[-1])

            if divisa == "USD":
                precio = precio / eurusd
            elif divisa == "GBP":
                precio = precio / 100
                precio = (precio * gbpusd) / eurusd

            precios_eur.append(precio)

        except:
            st.warning(f"No se pudo obtener precio para {ticker}")
            precios_eur.append(None)

    df["Precio Actual €"] = precios_eur
    df = df.dropna(subset=["Precio Actual €"])

    # =========================
    # CÁLCULOS
    # =========================
    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Inversión Inicial €"] = df["PRECIO TOTAL"]
    df["Rentabilidad €"] = df["Valor Actual €"] - df["Inversión Inicial €"]
    df["Rentabilidad %"] = df["Rentabilidad €"] / df["Inversión Inicial €"] * 100

    total_actual = df["Valor Actual €"].sum()
    total_inicial = df["Inversión Inicial €"].sum()
    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

    df["Peso %"] = df["Valor Actual €"] / total_actual * 100

    # =========================
    # MÉTRICA GENERAL
    # =========================
    st.divider()
    st.metric("Rentabilidad Total Cartera", f"{rentabilidad_total:.2f} %")
    st.divider()

    # =========================
    # CLASIFICACIÓN REGIÓN
    # =========================
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

    # =========================
    # GRÁFICO POR TIPO
    # =========================
    st.subheader("📊 Distribución por Tipo")
    tipo_chart = df.groupby("TIPO")["Valor Actual €"].sum().reset_index()
    fig_tipo = px.pie(tipo_chart, names="TIPO", values="Valor Actual €", hole=0.4)
    st.plotly_chart(fig_tipo, use_container_width=True)

    # =========================
    # GRÁFICO POR REGIÓN (solo acciones)
    # =========================
    st.subheader("🌍 Distribución por Región (Acciones)")
    acciones = df[df["TIPO"] == "ACCION"]
    region_chart = acciones.groupby("REGION")["Valor Actual €"].sum().reset_index()
    fig_region = px.pie(region_chart, names="REGION", values="Valor Actual €", hole=0.4)
    st.plotly_chart(fig_region, use_container_width=True)

    # =========================
    # PESO EN CARTERA
    # =========================
    st.subheader("📈 Peso de cada activo en la cartera")

    df_sorted = df.sort_values("Peso %", ascending=True)

    fig_peso = px.bar(
        df_sorted,
        x="Peso %",
        y="EMPRESA",
        orientation="h",
        color="Rentabilidad %",
        color_continuous_scale=["red", "yellow", "green"]
    )

    st.plotly_chart(fig_peso, use_container_width=True)

    # =========================
    # TABLA FINAL CON COLORES
    # =========================
    st.subheader("📋 Detalle completo")

    def color_rentabilidad(val):
        if val > 0:
            return "color: green"
        elif val < 0:
            return "color: red"
        else:
            return "color: white"

    st.dataframe(
        df.style.applymap(color_rentabilidad, subset=["Rentabilidad %"]),
        use_container_width=True
    )

else:
    st.info("Sube tu archivo Excel para empezar.")
