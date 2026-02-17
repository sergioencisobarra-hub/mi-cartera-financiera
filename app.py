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
    eurusd = float(yf.Ticker("EURUSD=X").history(period="1d")["Close"].iloc[-1])
    gbpusd = float(yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1])

    precios = []

    for index, row in df.iterrows():

        ticker = row["Ticker"]
        tipo = row["TIPO"]

        try:
            ticker_obj = yf.Ticker(ticker)

            # ACCION / ETF → fast_info
            if tipo in ["ACCION", "ETF"]:
                precio = ticker_obj.fast_info.get("lastPrice", None)

            # FONDO → usar history (NAV suele estar aquí)
            else:
                hist = ticker_obj.history(period="1d")
                if hist.empty:
                    raise Exception("Sin datos")
                precio = float(hist["Close"].iloc[-1])

            if precio is None:
                raise Exception("Sin precio")

            # Conversión divisa SOLO por sufijo
            if ticker.endswith(".L"):
                precio = (precio * gbpusd) / eurusd

            elif "." not in ticker:
                precio = precio / eurusd

            precios.append(precio)

        except:
            st.warning(f"No se pudo obtener precio para {ticker}")
            precios.append(None)

    df["Precio Actual €"] = precios
    df = df.dropna(subset=["ACCIONES", "PRECIO TOTAL", "Precio Actual €"])

    if df.empty:
        st.error("No hay datos válidos.")
        st.stop()

    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Inversión Inicial €"] = df["PRECIO TOTAL"]

    df["Rentabilidad €"] = df["Valor Actual €"] - df["Inversión Inicial €"]
    df["Rentabilidad %"] = df["Rentabilidad €"] / df["Inversión Inicial €"] * 100

    total_inicial = df["Inversión Inicial €"].sum()
    total_actual = df["Valor Actual €"].sum()

    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

    st.metric("Rentabilidad Total Cartera", f"{rentabilidad_total:.2f} %")

    st.dataframe(
        df[[
            "Ticker",
            "TIPO",
            "ACCIONES",
            "Precio Actual €",
            "Valor Actual €",
            "Rentabilidad %"
        ]],
        use_container_width=True
    )

else:
    st.info("Sube tu archivo Excel para empezar.")
