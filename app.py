import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Mi Cartera", layout="wide")

# =========================
# ESTILO OSCURO GLOBAL
# =========================
st.markdown("""
<style>
html, body, [class*="css"]  {
    background-color: #0f172a;
    color: white;
}

.block-container {
    padding-top: 2rem;
}

.metric-card {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.4);
}
</style>
""", unsafe_allow_html=True)

st.title("🌙 Dashboard Oscuro de Cartera")

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
    df["Diferencia €"] = df["Valor Actual €"] - df["PRECIO TOTAL"]
    df["Rentabilidad %"] = df["Diferencia €"] / df["PRECIO TOTAL"] * 100

    total_actual = df["Valor Actual €"].sum()
    total_inicial = df["PRECIO TOTAL"].sum()
    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100
    df["Peso %"] = df["Valor Actual €"] / total_actual * 100

    # =========================
    # MÉTRICAS GRANDES
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""
    <div class="metric-card">
        <h2>{total_actual:,.0f} €</h2>
        <p>Valor Total</p>
    </div>
    """, unsafe_allow_html=True)

    color_rent = "#00ff88" if rentabilidad_total > 0 else "#ff4d4d"

    col2.markdown(f"""
    <div class="metric-card">
        <h2 style="color:{color_rent}">{rentabilidad_total:.2f}%</h2>
        <p>Rentabilidad Total</p>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class="metric-card">
        <h2>{len(df)}</h2>
        <p>Posiciones</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # =========================
    # DONUT POR TIPO
    # =========================
    st.subheader("📊 Distribución por Tipo")

    tipo_chart = df.groupby("TIPO")["Valor Actual €"].sum().reset_index()

    fig_tipo = px.pie(
        tipo_chart,
        names="TIPO",
        values="Valor Actual €",
        hole=0.6,
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Plasma
    )

    st.plotly_chart(fig_tipo, use_container_width=True)

    st.divider()

    # =========================
    # TABLA
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

    def color_dif(val):
        return "color: #00ff88" if val > 0 else "color: #ff4d4d"

    def color_peso(val):
        return "color: #ff4d4d" if val > 3 else ""

    styled = tabla.style \
        .applymap(color_dif, subset=["Diferencia €", "Rentabilidad %"]) \
        .applymap(color_peso, subset=["Peso %"]) \
        .bar(subset=["Peso %"], color="#1f77ff") \
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
