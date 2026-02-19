import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Mi Cartera", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background-color: #111827;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        color: white;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Dashboard Dinámico de Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

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

    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Rentabilidad %"] = (df["Valor Actual €"] - df["PRECIO TOTAL"]) / df["PRECIO TOTAL"] * 100

    total_actual = df["Valor Actual €"].sum()
    total_inicial = df["PRECIO TOTAL"].sum()
    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100
    df["Peso %"] = df["Valor Actual €"] / total_actual * 100

    # ==============================
    # MÉTRICAS GRANDES
    # ==============================

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f'<div class="metric-card"><h2>{total_actual:,.0f} €</h2><p>Valor Total</p></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-card"><h2>{rentabilidad_total:.2f}%</h2><p>Rentabilidad Total</p></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="metric-card"><h2>{len(df)}</h2><p>Posiciones</p></div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="metric-card"><h2>{df["Peso %"].max():.2f}%</h2><p>Mayor Peso</p></div>', unsafe_allow_html=True)

    st.divider()

    # ==============================
    # DONUT POR TIPO
    # ==============================
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

    # ==============================
    # GRÁFICO BURBUJA
    # ==============================
    st.subheader("🎯 Peso vs Rentabilidad")

    fig_bubble = px.scatter(
        df,
        x="Peso %",
        y="Rentabilidad %",
        size="Valor Actual €",
        color="Rentabilidad %",
        hover_name="EMPRESA",
        color_continuous_scale="RdYlGn"
    )

    st.plotly_chart(fig_bubble, use_container_width=True)

    # ==============================
    # BARRAS HORIZONTALES
    # ==============================
    st.subheader("📈 Peso en Cartera")

    df_sorted = df.sort_values("Peso %")

    fig_bar = px.bar(
        df_sorted,
        x="Peso %",
        y="EMPRESA",
        orientation="h",
        color="Rentabilidad %",
        color_continuous_scale="RdYlGn"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # ==============================
    # TABLA ESTILIZADA
    # ==============================
    st.subheader("📋 Detalle")

    def color_rent(val):
        return "color: #00ff88" if val > 0 else "color: #ff4d4d"

    st.dataframe(
        df.style.applymap(color_rent, subset=["Rentabilidad %"]),
        use_container_width=True
    )

else:
    st.info("Sube tu archivo Excel para empezar.")
