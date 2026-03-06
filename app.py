import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import re

st.set_page_config(page_title="Mi Cartera", layout="wide")
st.title("📊 Mi Cartera")

# =========================
# CARGAR CARTERA
# =========================

df = pd.read_excel("CARTERA.xlsx")
df.columns = df.columns.str.strip().str.upper()

df["ACCIONES"] = pd.to_numeric(df["ACCIONES"], errors="coerce").fillna(0)
df["PRECIO TOTAL"] = pd.to_numeric(df["PRECIO TOTAL"], errors="coerce").fillna(0)

# =========================
# CONVERTIR TICKERS
# =========================

def convertir_ticker(t):

    if isinstance(t, str):

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

df["TICKER"] = df["IDENTIFICADOR"].apply(convertir_ticker)

# =========================
# CACHE PRECIOS ACCIONES
# =========================

@st.cache_data(ttl=1800)
def descargar_precios(tickers):

    if len(tickers) == 0:
        return None

    return yf.download(
        tickers,
        period="2d",
        interval="1d",
        progress=False
    )

# =========================
# CACHE DIVISAS
# =========================

@st.cache_data(ttl=1800)
def descargar_divisas():

    fx = yf.download(["EURUSD=X","GBPUSD=X"], period="2d", progress=False)

    eurusd = fx["Close"]["EURUSD=X"].iloc[-1]
    gbpusd = fx["Close"]["GBPUSD=X"].iloc[-1]

    return eurusd, gbpusd

eurusd, gbpusd = descargar_divisas()

tickers_acciones = df[df["TIPO"]!="FONDO"]["TICKER"].dropna().unique().tolist()

precios = descargar_precios(tickers_acciones)

close_data = None
if precios is not None:
    close_data = precios["Close"]

# =========================
# NAV FONDOS MORNINGSTAR
# =========================

def obtener_nav_morningstar(isin):

    try:

        url = f"https://www.morningstar.es/es/funds/snapshot/snapshot.aspx?id={isin}"

        r = requests.get(url, timeout=10)

        texto = r.text

        nav = re.search(r'"LastPrice":"([\d\.]+)"', texto)

        if nav:
            return float(nav.group(1))

        return 0

    except:
        return 0

# =========================
# CALCULAR PRECIOS
# =========================

precio_actual = []
cambio_dia_eur = []
cambio_dia_pct = []

for _,row in df.iterrows():

    ticker = row["TICKER"]
    acciones = row["ACCIONES"]
    tipo = row["TIPO"]
    divisa = str(row.get("DIVISA","EUR")).upper()

    p_actual = 0
    p_ayer = 0

    # ACCIONES / ETFs
    if tipo != "FONDO":

        try:

            datos = close_data[ticker]

            p_actual = datos.iloc[-1]
            p_ayer = datos.iloc[-2]

        except:
            pass

    # FONDOS
    else:

        nav = obtener_nav_morningstar(row["IDENTIFICADOR"])

        p_actual = nav
        p_ayer = nav

    # DIVISAS

    if divisa == "USD" and p_actual != 0:

        p_actual /= eurusd
        p_ayer /= eurusd

    if divisa == "GBP" and p_actual != 0:

        p_actual = (p_actual/100 * gbpusd) / eurusd
        p_ayer = (p_ayer/100 * gbpusd) / eurusd

    if p_ayer != 0:

        cambio_eur = (p_actual - p_ayer) * acciones
        cambio_pct = ((p_actual - p_ayer) / p_ayer) * 100

    else:

        cambio_eur = 0
        cambio_pct = 0

    precio_actual.append(p_actual)
    cambio_dia_eur.append(cambio_eur)
    cambio_dia_pct.append(cambio_pct)

df["PRECIO ACTUAL €"] = precio_actual
df["CAMBIO DÍA €"] = cambio_dia_eur
df["CAMBIO DÍA %"] = cambio_dia_pct

# =========================
# CÁLCULOS
# =========================

df["VALOR ACTUAL €"] = df["PRECIO ACTUAL €"] * df["ACCIONES"]
df["DIFERENCIA €"] = df["VALOR ACTUAL €"] - df["PRECIO TOTAL"]
df["RENTABILIDAD %"] = df["DIFERENCIA €"] / df["PRECIO TOTAL"].replace(0,1) * 100

total_inicial = df["PRECIO TOTAL"].sum()
total_actual = df["VALOR ACTUAL €"].sum()

rentabilidad_total = (total_actual - total_inicial) / total_inicial * 100

# =========================
# MOVIMIENTO DIARIO
# =========================

cambio_total_dia = df["CAMBIO DÍA €"].sum()

if cambio_total_dia > 0:
    flecha="↑"
    color="green"
elif cambio_total_dia < 0:
    flecha="↓"
    color="red"
else:
    flecha="→"
    color="gray"

st.markdown(
f"<h3 style='color:{color};'>{flecha} Movimiento Diario: {cambio_total_dia:,.2f} €</h3>",
unsafe_allow_html=True
)

col1,col2,col3 = st.columns(3)

col1.metric("Inversión Inicial",f"{total_inicial:,.2f} €")
col2.metric("Valor Actual",f"{total_actual:,.2f} €",delta=f"{cambio_total_dia:,.2f} €")
col3.metric("Rentabilidad Total",f"{rentabilidad_total:.2f} %")

st.divider()

# =========================
# TABLAS
# =========================

def mostrar_tabla(data,titulo):

    if data.empty:
        return

    with st.expander(titulo,expanded=True):

        mayor_subida = data.loc[data["CAMBIO DÍA €"].idxmax()]
        mayor_bajada = data.loc[data["CAMBIO DÍA €"].idxmin()]

        col1,col2 = st.columns(2)

        col1.metric(
            "🔼 Mayor subida",
            mayor_subida["EMPRESA"],
            delta=f"{mayor_subida['CAMBIO DÍA €']:,.2f} €"
        )

        col2.metric(
            "🔽 Mayor bajada",
            mayor_bajada["EMPRESA"],
            delta=f"{mayor_bajada['CAMBIO DÍA €']:,.2f} €"
        )

        tabla = data[[
            "EMPRESA",
            "ACCIONES",
            "PRECIO TOTAL",
            "PRECIO ACTUAL €",
            "CAMBIO DÍA €",
            "CAMBIO DÍA %",
            "DIFERENCIA €",
            "RENTABILIDAD %"
        ]]

        st.dataframe(tabla,use_container_width=True)

# =========================
# BLOQUES GEOGRÁFICOS
# =========================

acciones = df[df["TIPO"]=="ACCION"]

esp = acciones[acciones["TICKER"].astype(str).str.endswith(".MC")]
uk = acciones[acciones["TICKER"].astype(str).str.endswith(".L")]
eur = acciones[acciones["TICKER"].astype(str).str.endswith((".DE",".AS",".PA"))]
usa = acciones[~acciones["TICKER"].astype(str).str.contains(r"\.")]

st.header("📈 Acciones")

mostrar_tabla(esp,"🇪🇸 España")
mostrar_tabla(eur,"🇪🇺 Europa")
mostrar_tabla(usa,"🇺🇸 USA")
mostrar_tabla(uk,"🇬🇧 UK")

st.header("📊 ETFs")
mostrar_tabla(df[df["TIPO"]=="ETF"],"ETFs")

st.header("🏦 Fondos")
mostrar_tabla(df[df["TIPO"]=="FONDO"],"Fondos")
