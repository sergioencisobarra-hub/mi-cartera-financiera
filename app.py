import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Cartera", layout="wide")
st.title("📊 Mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

# =========================
# CACHE DATOS
# =========================
@st.cache_data(ttl=900)
def descargar_precios(tickers):
    return yf.download(tickers, period="7d", interval="1d", progress=False)

@st.cache_data(ttl=900)
def descargar_divisas():
    fx = yf.download(["EURUSD=X", "GBPUSD=X"], period="2d", progress=False)
    eurusd = fx["Close"]["EURUSD=X"].iloc[-1]
    gbpusd = fx["Close"]["GBPUSD=X"].iloc[-1]
    return eurusd, gbpusd


if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    df = df[df["IDENTIFICADOR"].notna()]

    df["ACCIONES"] = pd.to_numeric(df["ACCIONES"], errors="coerce")
    df["PRECIO TOTAL"] = pd.to_numeric(df["PRECIO TOTAL"], errors="coerce")

    # -------------------------
    # Conversión ticker
    # -------------------------
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

    tickers = df["Ticker"].unique().tolist()

    precios = descargar_precios(tickers)
    eurusd, gbpusd = descargar_divisas()

    close_data = precios["Close"]

    precio_actual = []
    cambio_dia_eur = []
    cambio_dia_pct = []

    for _, row in df.iterrows():

        ticker = row["Ticker"]
        acciones = row["ACCIONES"]
        divisa = str(row["DIVISA"]).upper()

        try:
            if len(tickers) == 1:
                datos = close_data
            else:
                datos = close_data[ticker]

            p_actual = datos.iloc[-1]
            p_ayer = datos.iloc[-2]

            if divisa == "USD":
                p_actual /= eurusd
                p_ayer /= eurusd
            elif divisa == "GBP":
                p_actual = (p_actual / 100 * gbpusd) / eurusd
                p_ayer = (p_ayer / 100 * gbpusd) / eurusd

            precio_actual.append(p_actual)

            cambio_eur = (p_actual - p_ayer) * acciones
            cambio_pct = ((p_actual - p_ayer) / p_ayer) * 100

            cambio_dia_eur.append(cambio_eur)
            cambio_dia_pct.append(cambio_pct)

        except:
            precio_actual.append(None)
            cambio_dia_eur.append(0)
            cambio_dia_pct.append(0)

    df["Precio Actual €"] = precio_actual
    df["Cambio Día €"] = cambio_dia_eur
    df["Cambio Día %"] = cambio_dia_pct

    df = df.dropna(subset=["Precio Actual €"])

    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Diferencia €"] = df["Valor Actual €"] - df["PRECIO TOTAL"]
    df["Rentabilidad %"] = df["Diferencia €"] / df["PRECIO TOTAL"] * 100

    total_inicial = df["PRECIO TOTAL"].sum()
    total_actual = df["Valor Actual €"].sum()
    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

    df["Peso %"] = df["Valor Actual €"] / total_actual * 100

    # -------------------------
    # Movimiento diario global
    # -------------------------
    cambio_total_dia = df["Cambio Día €"].sum()
    cambio_total_pct = (cambio_total_dia / total_actual) * 100 if total_actual != 0 else 0

    if cambio_total_dia > 0:
        flecha = "↑"
        color = "green"
    elif cambio_total_dia < 0:
        flecha = "↓"
        color = "red"
    else:
        flecha = "→"
        color = "gray"

    st.markdown(
        f"<h3 style='color:{color};'>{flecha} Movimiento Diario: "
        f"{cambio_total_dia:,.2f} € ({cambio_total_pct:.2f}%)</h3>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Inicial", f"{total_inicial:,.2f} €")
    col2.metric("Valor Actual", f"{total_actual:,.2f} €", delta=f"{cambio_total_dia:,.2f} €")
    col3.metric("Rentabilidad Total", f"{rentabilidad_total:.2f} %")

    st.divider()

    # -------------------------
    # Histórico semanal
    # -------------------------
    valores_diarios = []

    for i in range(len(close_data)):
        valor_dia = 0
        for _, row in df.iterrows():

            ticker = row["Ticker"]
            acciones = row["ACCIONES"]
            divisa = row["DIVISA"]

            try:
                if len(tickers) == 1:
                    precio = close_data.iloc[i]
                else:
                    precio = close_data[ticker].iloc[i]

                if divisa == "USD":
                    precio /= eurusd
                elif divisa == "GBP":
                    precio = (precio / 100 * gbpusd) / eurusd

                valor_dia += precio * acciones

            except:
                continue

        valores_diarios.append(valor_dia)

    historico_df = pd.DataFrame({
        "Fecha": close_data.index,
        "Valor Total €": valores_diarios
    })

    fig = px.line(historico_df, x="Fecha", y="Valor Total €", markers=True)
    fig.update_layout(height=250, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # -------------------------
    # FUNCIÓN TABLA
    # -------------------------
    def mostrar_tabla(data, titulo):

        if data.empty:
            return

        with st.expander(titulo, expanded=True):

            tabla = data[[
                "EMPRESA",
                "ACCIONES",
                "PRECIO TOTAL",
                "Precio Actual €",
                "Cambio Día €",
                "Cambio Día %",
                "Diferencia €",
                "Rentabilidad %",
                "Peso %"
            ]].sort_values("Peso %", ascending=False)

            def estilo(val):
                if val > 0:
                    return "color: green; font-weight: bold;"
                elif val < 0:
                    return "color: red; font-weight: bold;"
                return ""

            styled = tabla.style \
                .applymap(estilo, subset=[
                    "Cambio Día €",
                    "Cambio Día %",
                    "Diferencia €",
                    "Rentabilidad %"
                ]) \
                .format({
                    "PRECIO TOTAL": "{:,.2f}",
                    "Precio Actual €": "{:,.2f}",
                    "Cambio Día €": "{:,.2f}",
                    "Cambio Día %": "{:.2f}",
                    "Diferencia €": "{:,.2f}",
                    "Rentabilidad %": "{:.2f}",
                    "Peso %": "{:.2f}"
                })

            st.dataframe(styled, use_container_width=True)

    # -------------------------
    # BLOQUES GEOGRÁFICOS
    # -------------------------
    acciones = df[df["TIPO"] == "ACCION"]

    esp = acciones[acciones["Ticker"].str.endswith(".MC")]
    uk = acciones[acciones["Ticker"].str.endswith(".L")]
    eur = acciones[acciones["Ticker"].str.endswith((".DE", ".AS", ".PA"))]
    usa = acciones[~acciones["Ticker"].str.contains(r"\.")]

    st.header("📈 Acciones")

    mostrar_tabla(esp, "🇪🇸 España")
    mostrar_tabla(eur, "🇪🇺 Europa")
    mostrar_tabla(usa, "🇺🇸 USA")
    mostrar_tabla(uk, "🇬🇧 UK")

    st.header("📊 ETFs")
    mostrar_tabla(df[df["TIPO"] == "ETF"], "ETFs")

    st.header("🏦 Fondos")
    mostrar_tabla(df[df["TIPO"] == "FONDO"], "Fondos")

else:
    st.info("Sube tu archivo Excel para empezar.")
