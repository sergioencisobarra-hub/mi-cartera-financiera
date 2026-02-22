import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Cartera", layout="wide")
st.title("📊 Mi Cartera")

# =========================
# CARGA CARTERA DESDE REPO
# =========================

df = pd.read_excel("CARTERA.xlsx")
df.columns = df.columns.str.strip().str.upper()

if "IDENTIFICADOR" not in df.columns:
    st.error("No se encontró columna IDENTIFICADOR en CARTERA.xlsx")
    st.stop()

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
    if t.startswith("ETR:") or t.startswith("VIE:"):
        return t.split(":")[1] + ".DE"
    if t.startswith("AMS:"):
        return t.split(":")[1] + ".AS"
    if t.startswith("EPA:"):
        return t.split(":")[1] + ".PA"
    if t.startswith("NYSE:") or t.startswith("NASDAQ:"):
        return t.split(":")[1]
    return t

df["TICKER"] = df["IDENTIFICADOR"].apply(convertir_ticker).str.upper()

tickers = df["TICKER"].unique().tolist()

# =========================
# CACHE DESCARGA PRECIOS
# =========================

@st.cache_data(ttl=900)
def descargar_datos(tickers):
    return yf.download(tickers, period="2d", interval="1d", progress=False)

@st.cache_data(ttl=900)
def descargar_divisas():
    fx = yf.download(["EURUSD=X", "GBPUSD=X"], period="2d", progress=False)
    eurusd = fx["Close"]["EURUSD=X"].iloc[-1]
    gbpusd = fx["Close"]["GBPUSD=X"].iloc[-1]
    return eurusd, gbpusd

precios = descargar_datos(tickers)
eurusd, gbpusd = descargar_divisas()

close_data = precios["Close"]

precio_actual = []
cambio_dia_eur = []
cambio_dia_pct = []

for _, row in df.iterrows():

    ticker = row["TICKER"]
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

df["PRECIO ACTUAL €"] = precio_actual
df["CAMBIO DÍA €"] = cambio_dia_eur
df["CAMBIO DÍA %"] = cambio_dia_pct

df["PRECIO ACTUAL €"] = df["PRECIO ACTUAL €"].fillna(0)

df["VALOR ACTUAL €"] = df["PRECIO ACTUAL €"] * df["ACCIONES"]
df["DIFERENCIA €"] = df["VALOR ACTUAL €"] - df["PRECIO TOTAL"]
df["RENTABILIDAD %"] = df["DIFERENCIA €"] / df["PRECIO TOTAL"] * 100

total_inicial = df["PRECIO TOTAL"].sum()
total_actual = df["VALOR ACTUAL €"].sum()
rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

# =========================
# MOVIMIENTO DIARIO GLOBAL
# =========================

cambio_total_dia = df["CAMBIO DÍA €"].sum()
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
    f"<h3 style='color:{color};'>"
    f"{flecha} Movimiento Diario: {cambio_total_dia:,.2f} € ({cambio_total_pct:.2f}%)"
    f"</h3>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)
col1.metric("Inversión Inicial", f"{total_inicial:,.2f} €")
col2.metric("Valor Actual", f"{total_actual:,.2f} €", delta=f"{cambio_total_dia:,.2f} €")
col3.metric("Rentabilidad Total", f"{rentabilidad_total:.2f} %")

st.divider()

# =========================
# FUNCIÓN TABLAS
# =========================

def mostrar_tabla(data, titulo):

    if data.empty:
        return

    with st.expander(titulo, expanded=True):

        # -------------------------
        # Detectar mayor subida y bajada
        # -------------------------
        mayor_subida = data.loc[data["CAMBIO DÍA €"].idxmax()]
        mayor_bajada = data.loc[data["CAMBIO DÍA €"].idxmin()]

        col1, col2 = st.columns(2)

        col1.metric(
            "🔼 Mayor subida",
            f"{mayor_subida['EMPRESA']}",
            delta=f"{mayor_subida['CAMBIO DÍA €']:,.2f} € ({mayor_subida['CAMBIO DÍA %']:.2f}%)"
        )

        col2.metric(
            "🔽 Mayor bajada",
            f"{mayor_bajada['EMPRESA']}",
            delta=f"{mayor_bajada['CAMBIO DÍA €']:,.2f} € ({mayor_bajada['CAMBIO DÍA %']:.2f}%)"
        )

        st.markdown("---")

        # -------------------------
        # Tabla
        # -------------------------
        tabla = data[[
            "EMPRESA",
            "ACCIONES",
            "PRECIO TOTAL",
            "PRECIO ACTUAL €",
            "CAMBIO DÍA €",
            "CAMBIO DÍA %",
            "DIFERENCIA €",
            "RENTABILIDAD %",
        ]].sort_values("RENTABILIDAD %", ascending=False)

        def estilo(val):
            if val > 0:
                return "color: green; font-weight: bold;"
            elif val < 0:
                return "color: red; font-weight: bold;"
            return ""

        styled = tabla.style \
            .applymap(estilo, subset=[
                "CAMBIO DÍA €",
                "CAMBIO DÍA %",
                "DIFERENCIA €",
                "RENTABILIDAD %"
            ]) \
            .format({
                "PRECIO TOTAL": "{:,.2f}",
                "PRECIO ACTUAL €": "{:,.2f}",
                "CAMBIO DÍA €": "{:,.2f}",
                "CAMBIO DÍA %": "{:.2f}",
                "DIFERENCIA €": "{:,.2f}",
                "RENTABILIDAD %": "{:.2f}"
            })

        st.dataframe(styled, use_container_width=True)
# =========================
# BLOQUES GEOGRÁFICOS
# =========================

acciones = df[df["TIPO"] == "ACCION"]

esp = acciones[acciones["TICKER"].str.endswith(".MC")]
uk = acciones[acciones["TICKER"].str.endswith(".L")]
eur = acciones[acciones["TICKER"].str.endswith((".DE", ".AS", ".PA"))]
usa = acciones[~acciones["TICKER"].str.contains(r"\.")]

st.header("📈 Acciones")
mostrar_tabla(esp, "🇪🇸 España")
mostrar_tabla(eur, "🇪🇺 Europa")
mostrar_tabla(usa, "🇺🇸 USA")
mostrar_tabla(uk, "🇬🇧 UK")

st.header("📊 ETFs")
mostrar_tabla(df[df["TIPO"] == "ETF"], "ETFs")

st.header("🏦 Fondos")
mostrar_tabla(df[df["TIPO"] == "FONDO"], "Fondos")


