import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Cartera", layout="wide")
st.title("📊 Mi Cartera")

uploaded_file = st.file_uploader("Sube tu archivo CARTERA.xlsx", type=["xlsx"])

if uploaded_file is not None:

    # =========================
    # CARGA Y LIMPIEZA
    # =========================
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df = df[df["IDENTIFICADOR"].notna()]
    df["ACCIONES"] = pd.to_numeric(df["ACCIONES"], errors="coerce")
    df["PRECIO TOTAL"] = pd.to_numeric(df["PRECIO TOTAL"], errors="coerce")

    # =========================
    # CONVERSIÓN TICKERS
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

    for _, row in df.iterrows():
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

    # =========================
    # CÁLCULOS
    # =========================
    df["Valor Actual €"] = df["Precio Actual €"] * df["ACCIONES"]
    df["Diferencia €"] = df["Valor Actual €"] - df["PRECIO TOTAL"]
    df["Rentabilidad %"] = df["Diferencia €"] / df["PRECIO TOTAL"] * 100

    total_inicial = df["PRECIO TOTAL"].sum()
    total_actual = df["Valor Actual €"].sum()
    rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

    df["Peso %"] = df["Valor Actual €"] / total_actual * 100

    # =========================
    # CARDS PRINCIPALES
    # =========================
    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Inicial", f"{total_inicial:,.2f} €")
    col2.metric("Valor Actual", f"{total_actual:,.2f} €")
    col3.metric("Rentabilidad Total", f"{rentabilidad_total:.2f} %")

    st.divider()

    # =========================
    # VISIÓN MACRO
    # =========================
    col_tipo, col_region = st.columns(2)

    # Donut por tipo
    with col_tipo:
        st.subheader("Distribución por Tipo")
        tipo_chart = df.groupby("TIPO")["Valor Actual €"].sum().reset_index()
        fig_tipo = px.pie(
            tipo_chart,
            names="TIPO",
            values="Valor Actual €",
            hole=0.6
        )
        fig_tipo.update_layout(showlegend=False)
        st.plotly_chart(fig_tipo, use_container_width=True)

    # Donut por región (solo acciones)
    with col_region:
        st.subheader("Distribución por Región (Acciones)")

        acciones = df[df["TIPO"] == "ACCION"]

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

        acciones["REGION"] = acciones["Ticker"].apply(clasificar_region)

        region_chart = acciones.groupby("REGION")["Valor Actual €"].sum().reset_index()

        fig_region = px.pie(
            region_chart,
            names="REGION",
            values="Valor Actual €",
            hole=0.6
        )

        fig_region.update_layout(showlegend=False)
        st.plotly_chart(fig_region, use_container_width=True)

    st.divider()

    # =========================
    # FUNCIÓN BLOQUES
    # =========================
    def mostrar_bloque(data, titulo):

        if data.empty:
            return

        with st.expander(titulo, expanded=True):

            valor = data["Valor Actual €"].sum()
            inversion = data["PRECIO TOTAL"].sum()
            rent = (valor - inversion) / inversion * 100
            peso_bloque = valor / total_actual * 100
            resto = 100 - peso_bloque

            col1, col2, col3 = st.columns(3)
            col1.metric("Valor del bloque", f"{valor:,.2f} €")
            col2.metric("Rentabilidad del bloque", f"{rent:.2f} %")
            col3.metric("% sobre la cartera", f"{peso_bloque:.2f} %")

            st.markdown("---")

            col_bar, col_pie = st.columns([4, 2])

            with col_bar:
                fig_bar = px.bar(
                    data.sort_values("Peso %"),
                    x="Peso %",
                    y="EMPRESA",
                    orientation="h",
                    height=350
                )
                fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_pie:
                pie_data = pd.DataFrame({
                    "Segmento": ["Bloque", "Resto cartera"],
                    "Porcentaje": [peso_bloque, resto]
                })

                fig_pie = px.pie(
                    pie_data,
                    names="Segmento",
                    values="Porcentaje",
                    hole=0.5
                )

                fig_pie.update_layout(showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

            st.dataframe(
                data[[
                    "EMPRESA",
                    "ACCIONES",
                    "PRECIO TOTAL",
                    "Precio Actual €",
                    "Diferencia €",
                    "Rentabilidad %",
                    "Peso %"
                ]].sort_values("Peso %", ascending=False),
                use_container_width=True
            )

    # =========================
    # ACCIONES POR REGIÓN
    # =========================
    acciones = df[df["TIPO"] == "ACCION"]

    esp = acciones[acciones["Ticker"].str.endswith(".MC")]
    uk = acciones[acciones["Ticker"].str.endswith(".L")]
    eur = acciones[acciones["Ticker"].str.endswith((".DE", ".AS", ".PA"))]
    usa = acciones[~acciones["Ticker"].str.contains(r"\.")]

    st.header("📈 Acciones")
    mostrar_bloque(esp, "🇪🇸 España")
    mostrar_bloque(eur, "🇪🇺 Europa")
    mostrar_bloque(usa, "🇺🇸 USA")
    mostrar_bloque(uk, "🇬🇧 UK")

    st.divider()

    # =========================
    # ETFs
    # =========================
    st.header("📊 ETFs")
    etfs = df[df["TIPO"] == "ETF"]
    mostrar_bloque(etfs, "ETFs")

    st.divider()

    # =========================
    # Fondos
    # =========================
    st.header("🏦 Fondos de Inversión")
    fondos = df[df["TIPO"] == "FONDO"]
    mostrar_bloque(fondos, "Fondos")

else:
    st.info("Sube tu archivo Excel para empezar.")
