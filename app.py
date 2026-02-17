import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Dashboard Cartera", layout="wide")
st.title("📊 Dashboard de mi Cartera (Acciones + ETFs + Fondos)")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Forzar numéricos
    df["ACCIONES"] = pd.to_numeric(df["ACCIONES"], errors="coerce")
    df["PRECIO TOTAL"] = pd.to_numeric(df["PRECIO TOTAL"], errors="coerce")

    # Tipos de cambio
    try:
        eurusd = float(yf.download("EURUSD=X", period="1d", progress=False)["Close"].iloc[-1])
        gbpusd = float(yf.download("GBPUSD=X", period="1d", progress=False)["Close"].iloc[-1])
    except:
        st.error("No se pudieron descargar tipos de cambio.")
        st.stop()

    precios_actuales = []

    for index, row in df.iterrows():

        identificador_original = str(row["IDENTIFICADOR"]).strip()
        tipo = str(row["TIPO"]).upper()

        # Convertir identificador a formato Yahoo si es ACCION o ETF
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

        identificador = convertir_ticker(identificador_original).upper()

        try:
            datos = yf.download(identificador, period="1d", progress=False)
            if datos.empty:
                raise Exception("Sin datos")

            precio = float(datos["Close"].iloc[-1])

            # ACCIONES y ETFs
            if tipo in ["ACCION", "ETF"]:

                # UK (GBP)
                if identificador.endswith(".L"):
                    if precio > 100:
                        precio = precio / 100
                    precio = (precio * gbpusd) / eurusd

                # USA (USD)
                elif "." not in identificador:
                    precio = precio / eurusd

                # Europa ya en EUR

            # FONDOS
            elif tipo == "FONDO":
                # Si estuviera en USD
                if "." not in identificador:
                    precio = precio / eurusd

            precios_actuales.append(precio)

        except:
            st.warning(f"No se pudo obtener precio para {identificador_original}")
            precios_actuales.append(None)

    df["Precio Actual €"] = precios_actuales

    # Limpiar filas inválidas
    df = df.dropna(subset=["ACCIONES", "PRECIO TOTAL", "Precio Actual €"])

    # Cálculos financieros
    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
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
        df.sort_values("Rentabilidad %", ascending=False),
        use_container_width=True
    )

else:
    st.info("Sube tu archivo Excel para empezar.")
