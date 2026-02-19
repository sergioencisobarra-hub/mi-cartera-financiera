import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Cartera Premium", layout="wide")

# =========================
# ESTILO PREMIUM
# =========================
st.markdown("""
<style>

html, body, [class*="css"]  {
    background-color: #0b1220;
    color: #e5e7eb;
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding-top: 2rem;
}

.premium-card {
    background: linear-gradient(145deg, #111827, #0f172a);
    padding: 25px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0px 10px 30px rgba(0,0,0,0.6);
    text-align: center;
}

.metric-value {
    font-size: 28px;
    font-weight: 600;
}

.metric-label {
    font-size: 14px;
    opacity: 0.7;
}

</style>
""", unsafe_allow_html=True)

st.title("📈 Cartera – Edición Premium")

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
    # MÉTRICAS PREMIUM
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""
    <div class="premium-card">
        <div class="metric-value">{total_actual:,.0f} €</div>
        <div class="metric-label">Valor Total</div>
    </div>
    """, unsafe_allow_html=True)

    color_rent = "#00ff99" if rentabilidad_total > 0 else "#ff4d6d"

    col2.markdown(f"""
    <div class="premium-card">
        <div class="metric-value" style="color:{color_rent}">
            {rentabilidad_total:.2f}%
        </div>
        <div class="metric-label">Rentabilidad Total</div>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class="premium-card">
        <div class="metric-value">{len(df)}</div>
        <div class="metric-label">Posiciones</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # DONUT MODERNO
    # =========================
    st.subheader("Distribución por Tipo")

    tipo_chart = df.groupby("TIPO")["Valor Actual €"].sum().reset_index()

    fig_tipo = px.pie(
        tipo_chart,
        names="TIPO",
        values="Valor Actual €",
        hole=0.65,
        template="plotly_dark",
        color_discrete_sequence=["#6366f1", "#10b981", "#f59e0b"]
    )

    fig_tipo.update_traces(textposition="outside", textinfo="percent+label")
    fig_tipo.update_layout(showlegend=False)

    st.plotly_chart(fig_tipo, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # TABLA PREMIUM
    # =========================
    st.subheader("Detalle de posiciones")

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
        return "color: #00ff99" if val > 0 else "color: #ff4d6d"

    def color_peso(val):
        if val > 5:
            return "color: #ff4d6d"
        elif val > 3:
            return "color: #f59e0b"
        return ""

    styled = tabla.style \
        .applymap(color_dif, subset=["Diferencia €", "Rentabilidad %"]) \
        .applymap(color_peso, subset=["Peso %"]) \
        .bar(subset=["Peso %"], color="#6366f1") \
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
