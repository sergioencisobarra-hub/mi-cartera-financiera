import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Cartera", layout="wide")
st.title("📊 Mi Cartera")

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

    # =========================
    # CONVERSIÓN TICKER
    # =========================
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
    cambio_dia_eur = []
    cambio_dia_pct = []

    for _, row in df.iterrows():
        ticker = row["Ticker"]
        divisa = str(row["DIVISA"]).upper()

        try:
            hist = yf.Ticker(ticker).history(period="2d")

            if len(hist) < 2:
                raise Exception("Histórico insuficiente")

            precio_actual = float(hist["Close"].iloc[-1])
            precio_ayer = float(hist["Close"].iloc[-2])

            if divisa == "USD":
                precio_actual /= eurusd
                precio_ayer /= eurusd
            elif divisa == "GBP":
                precio_actual = (precio_actual / 100 * gbpusd) / eurusd
                precio_ayer = (precio_ayer / 100 * gbpusd) / eurusd

            precios.append(precio_actual)

            cambio_eur = (precio_actual - precio_ayer) * row["ACCIONES"]
            cambio_pct = ((precio_actual - precio_ayer) / precio_ayer) * 100

            cambio_dia_eur.append(cambio_eur)
            cambio_dia_pct.append(cambio_pct)

        except:
            precios.append(None)
            cambio_dia_eur.append(None)
            cambio_dia_pct.append(None)

    df["Precio Actual €"] = precios
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

    # =========================
    # RESUMEN DIARIO GLOBAL
    # =========================
    cambio_total_dia = df["Cambio Día €"].sum()
    cambio_total_pct = (cambio_total_dia / total_actual) * 100

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
        f"<h3 style='color:{color};'>{flecha} Movimiento Diario: {cambio_total_dia:,.2f} € ({cambio_total_pct:.2f}%)</h3>",
        unsafe_allow_html=True
    )

    # =========================
    # CARDS PRINCIPALES
    # =========================
    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Inicial", f"{total_inicial:,.2f} €")
    col2.metric("Valor Actual", f"{total_actual:,.2f} €", delta=f"{cambio_total_dia:,.2f} €")
    col3.metric("Rentabilidad Total", f"{rentabilidad_total:.2f} %")

    st.divider()

    # =========================
    # MINI HISTÓRICO SEMANAL
    # =========================
    try:
        tickers_lista = df["Ticker"].tolist()
        precios_semana = yf.download(tickers_lista, period="7d", interval="1d", group_by="ticker", progress=False)

        valores_diarios = []

        for fecha in precios_semana.index:
            valor_dia = 0

            for _, row in df.iterrows():
                ticker = row["Ticker"]
                acciones = row["ACCIONES"]
                divisa = row["DIVISA"]

                try:
                    if len(tickers_lista) == 1:
                        precio = precios_semana["Close"].loc[fecha]
                    else:
                        precio = precios_semana[ticker]["Close"].loc[fecha]

                    if divisa == "USD":
                        precio /= eurusd
                    elif divisa == "GBP":
                        precio = (precio / 100 * gbpusd) / eurusd

                    valor_dia += precio * acciones

                except:
                    continue

            valores_diarios.append(valor_dia)

        historico_df = pd.DataFrame({
            "Fecha": precios_semana.index,
            "Valor Total €": valores_diarios
        })

        fig_hist = px.line(historico_df, x="Fecha", y="Valor Total €")
        fig_hist.update_layout(height=250, showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

    except:
        st.warning("No se pudo generar el histórico semanal.")

    st.divider()

    # =========================
    # FUNCIÓN TABLAS
    # =========================
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
                .applymap(estilo, subset=["Cambio Día €", "Cambio Día %", "Diferencia €", "Rentabilidad %"]) \
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

    # =========================
    # BLOQUES
    # =========================
    acciones = df[df["TIPO"] == "ACCION"]
    etfs = df[df["TIPO"] == "ETF"]
    fondos = df[df["TIPO"] == "FONDO"]

    st.header("📈 Acciones")
    mostrar_tabla(acciones, "Acciones")

    st.header("📊 ETFs")
    mostrar_tabla(etfs, "ETFs")

    st.header("🏦 Fondos")
    mostrar_tabla(fondos, "Fondos")

else:
    st.info("Sube tu archivo Excel para empezar.")
