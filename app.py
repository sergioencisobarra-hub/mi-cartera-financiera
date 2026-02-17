import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    # ==================================
    # 1️⃣ CARGA Y LIMPIEZA
    # ==================================
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df = df[df["IDENTIFICADOR"].notna()]
    df = df[df["IDENTIFICADOR"] != df["TIPO"]]

    df["ACCIONES"] = pd.to_numeric(df["ACCIONES"], errors="coerce")
    df["PRECIO TOTAL"] = pd.to_numeric(df["PRECIO TOTAL"], errors="coerce")

    # ==================================
    # 2️⃣ CONVERSIÓN IDENTIFICADOR → YAHOO
    # ==================================
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

    # ==================================
    # 3️⃣ TIPOS DE CAMBIO
    # ==================================
    eurusd = float(yf.Ticker("EURUSD=X").history(period="1d")["Close"].iloc[-1])
    gbpusd = float(yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1])

    st.write("EURUSD:", eurusd)
    st.write("GBPUSD:", gbpusd)

    precios_brutos = []
    precios_eur = []

    # ==================================
    # 4️⃣ DESCARGA DE PRECIOS
    # ==================================
    for index, row in df.iterrows():

        ticker = row["Ticker"]
        tipo = str(row["TIPO"]).upper()
        divisa = str(row["DIVISA"]).upper()

        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")

            if hist.empty:
                raise Exception("Sin datos")

            precio_bruto = float(hist["Close"].iloc[-1])
            precios_brutos.append(precio_bruto)

            # ===============================
            # LÓGICA DE CONVERSIÓN DEFINITIVA
            # ===============================

            # ACCIONES Y ETFs
            if tipo in ["ACCION", "ETF"]:

                if divisa == "USD":
                    precio_eur = precio_bruto / eurusd

                elif divisa == "GBP":
                    # Yahoo devuelve pence
                    precio_gbp = precio_bruto / 100
                    precio_eur = (precio_gbp * gbpusd) / eurusd

                else:  # EUR
                    precio_eur = precio_bruto

            # FONDOS → NO convertir (Yahoo ya devuelve en EUR en tus casos)
            elif tipo == "FONDO":
                precio_eur = precio_bruto

            else:
                precio_eur = precio_bruto

            precios_eur.append(precio_eur)

        except:
            st.warning(f"No se pudo obtener precio para {ticker}")
            precios_brutos.append(None)
            precios_eur.append(None)

    df["Precio Bruto Descargado"] = precios_brutos
    df["Precio Actual €"] = precios_eur

    df = df.dropna(subset=["Precio Actual €"])

    if df.empty:
        st.error("No hay datos válidos.")
        st.stop()

    # ==================================
    # 5️⃣ CÁLCULOS
    # ==================================
    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Inversión Inicial €"] = df["PRECIO TOTAL"]

    df["Rentabilidad €"] = df["Valor Actual €"] - df["Inversión Inicial €"]
    df["Rentabilidad %"] = df["Rentabilidad €"] / df["Inversión Inicial €"] * 100

    total_inicial = df["Inversión Inicial €"].sum()
    total_actual = df["Valor Actual €"].sum()
    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

    # ==================================
    # 6️⃣ DASHBOARD
    # ==================================
    st.divider()
    st.metric("Rentabilidad Total Cartera", f"{rentabilidad_total:.2f} %")
    st.divider()

    st.dataframe(
        df[[
            "EMPRESA",
            "TIPO",
            "DIVISA",
            "ACCIONES",
            "Precio Bruto Descargado",
            "Precio Actual €",
            "Valor Actual €",
            "Rentabilidad %"
        ]],
        use_container_width=True
    )

else:
    st.info("Sube tu archivo Excel para empezar.")
