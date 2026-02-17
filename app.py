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

    # =============================
    # Conversión Yahoo
    # =============================
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

    # =============================
    # Tipos de cambio
    # =============================
    eurusd = float(yf.download("EURUSD=X", period="1d", progress=False)["Close"].iloc[-1])
    gbpusd = float(yf.download("GBPUSD=X", period="1d", progress=False)["Close"].iloc[-1])

    precios = []

    for index, row in df.iterrows():
        identificador = row["Ticker"]
        tipo = row["TIPO"]

        try:
            datos = yf.download(identificador, period="1d", progress=False)
            if datos.empty:
                raise Exception("Sin datos")

            precio = float(datos["Close"].iloc[-1])

            if tipo in ["ACCION", "ETF"]:

                if identificador.endswith(".L"):
                    if precio > 100:
                        precio = precio / 100
                    precio = (precio * gbpusd) / eurusd

                elif "." not in identificador:
                    precio = precio / eurusd

            elif tipo == "FONDO":
                if "." not in identificador:
                    precio = precio / eurusd

            precios.append(precio)

        except:
            precios.append(None)

    df["Precio Actual €"] = precios
    df = df.dropna(subset=["Precio Actual €"])

    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Inversión Inicial €"] = df["PRECIO TOTAL"]
    df["Rentabilidad €"] = df["Valor Actual €"] - df["Inversión Inicial €"]
    df["Rentabilidad %"] = df["Rentabilidad €"] / df["Inversión Inicial €"] * 100

    # =============================
    # Clasificación geográfica
    # =============================
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

    # =============================
    # Métrica total
    # =============================
    total_inicial = df["Inversión Inicial €"].sum()
    total_actual = df["Valor Actual €"].sum()
    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

    st.divider()
    st.metric("Rentabilidad Total Cartera", f"{rentabilidad_total:.2f} %")
    st.divider()

    # =============================
    # BLOQUE ACCIONES
    # =============================
    st.header("📈 ACCIONES")

    acciones = df[df["TIPO"] == "ACCION"]

    for region in ["España", "UK", "USA", "Europa"]:
        st.subheader(region)

        bloque = acciones[acciones["REGION"] == region]

        if not bloque.empty:
            valor = bloque["Valor Actual €"].sum()
            rent = (valor - bloque["Inversión Inicial €"].sum()) / bloque["Inversión Inicial €"].sum() * 100

            col1, col2 = st.columns(2)
            col1.metric("Valor Actual", f"{valor:,.2f} €")
            col2.metric("Rentabilidad", f"{rent:.2f} %")

            st.dataframe(
                bloque.sort_values("Rentabilidad %", ascending=False),
                use_container_width=True
            )

            st.bar_chart(
                bloque.set_index("Ticker")["Valor Actual €"]
            )

    # =============================
    # BLOQUE ETFs
    # =============================
    st.header("📊 ETFs")

    etfs = df[df["TIPO"] == "ETF"]

    if not etfs.empty:
        valor = etfs["Valor Actual €"].sum()
        rent = (valor - etfs["Inversión Inicial €"].sum()) / etfs["Inversión Inicial €"].sum() * 100

        col1, col2 = st.columns(2)
        col1.metric("Valor Actual ETFs", f"{valor:,.2f} €")
        col2.metric("Rentabilidad ETFs", f"{rent:.2f} %")

        st.dataframe(etfs.sort_values("Rentabilidad %", ascending=False), use_container_width=True)
        st.bar_chart(etfs.set_index("Ticker")["Valor Actual €"])

    # =============================
    # BLOQUE FONDOS
    # =============================
    st.header("🏦 FONDOS")

    fondos = df[df["TIPO"] == "FONDO"]

    if not fondos.empty:
        valor = fondos["Valor Actual €"].sum()
        rent = (valor - fondos["Inversión Inicial €"].sum()) / fondos["Inversión Inicial €"].sum() * 100

        col1, col2 = st.columns(2)
        col1.metric("Valor Actual Fondos", f"{valor:,.2f} €")
        col2.metric("Rentabilidad Fondos", f"{rent:.2f} %")

        st.dataframe(fondos.sort_values("Rentabilidad %", ascending=False), use_container_width=True)
        st.bar_chart(fondos.set_index("IDENTIFICADOR")["Valor Actual €"])

else:
    st.info("Sube tu archivo Excel para empezar.")
