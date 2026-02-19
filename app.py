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

    with col_tipo:
        st.subheader("Distribución por Tipo")
        tipo_chart = df.groupby("TIPO")["Valor Actual €"].sum().reset_index()
        fig_tipo = px.pie(tipo_chart, names="TIPO", values="Valor Actual €", hole=0.6)
        fig_tipo.update_layout(showlegend=False)
        st.plotly_chart(fig_tipo, use_container_width=True)

    with col_region:
        st.subheader("Distribución por Región (Acciones)")
        acciones_tmp = df[df["TIPO"] == "ACCION"].copy()

        def clasificar_region(ticker):
            if ticker.endswith(".MC"):
                return "España"
            if ticker.endswith(".L"):
                return "UK"
            if ticker.endswith((".DE", ".AS", ".PA")):
                return "Europa"
            if "." not in ticker:
                return "USA"
            return "Otros"

        acciones_tmp["REGION"] = acciones_tmp["Ticker"].apply(clasificar_region)
        region_chart = acciones_tmp.groupby("REGION")["Valor Actual €"].sum().reset_index()

        fig_region = px.pie(region_chart, names="REGION", values="Valor Actual €", hole=0.6)
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
                    "Segmento": ["Bloque", "Resto"],
                    "Porcentaje": [peso_bloque, resto]
                })
                fig_pie = px.pie(pie_data, names="Segmento", values="Porcentaje", hole=0.5)
                fig_pie.update_layout(showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

            tabla = data[[
                "EMPRESA",
                "ACCIONES",
                "PRECIO TOTAL",
                "Precio Actual €",
                "Diferencia €",
                "Rentabilidad %",
                "Peso %"
            ]].sort_values("Peso %", ascending=False)

            def estilo_rentabilidad(val):
                if val >= 15:
                    return "color: #0f5132; font-weight: bold; font-size: 110%; background-color: rgba(25,135,84,0.15);"
                elif val > 0:
                    return "color: #198754; font-weight: bold;"
                elif val <= -10:
                    return "color: #842029; font-weight: bold; background-color: rgba(220,53,69,0.15);"
                elif val < 0:
                    return "color: #dc3545; font-weight: bold;"
                return ""

            def estilo_diferencia(val):
                if val > 0:
                    return "color: #198754; font-weight: bold;"
                elif val < 0:
                    return "color: #dc3545; font-weight: bold;"
                return ""

            def estilo_peso(val):
                if val > 10:
                    return "color: #dc3545; font-weight: bold;"
                elif val > 5:
                    return "color: #fd7e14; font-weight: bold;"
                elif val > 3:
                    return "color: #ffc107;"
                return ""

            styled = tabla.style \
                .applymap(estilo_rentabilidad, subset=["Rentabilidad %"]) \
                .applymap(estilo_diferencia, subset=["Diferencia €"]) \
                .applymap(estilo_peso, subset=["Peso %"]) \
                .format({
                    "PRECIO TOTAL": "{:,.2f}",
                    "Precio Actual €": "{:,.2f}",
                    "Diferencia €": "{:,.2f}",
                    "Rentabilidad %": "{:.2f}",
                    "Peso %": "{:.2f}"
                })

            st.dataframe(styled, use_container_width=True)

    # =========================
    # BLOQUES
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

    st.header("📊 ETFs")
    etfs = df[df["TIPO"] == "ETF"]
    mostrar_bloque(etfs, "ETFs")

    st.divider()

    st.header("🏦 Fondos de Inversión")
    fondos = df[df["TIPO"] == "FONDO"]
    mostrar_bloque(fondos, "Fondos")

else:
    st.info("Sube tu archivo Excel para empezar.")
