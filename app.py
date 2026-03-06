import streamlit as st
import pandas as pd
import yfinance as yf
import investpy
from datetime import datetime

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

# =========================
# CACHE DATOS
# =========================

@st.cache_data(ttl=1800)
def descargar_precios(tickers):
    return yf.download(tickers, period="2d", interval="1d", progress=False)


@st.cache_data(ttl=1800)
def descargar_divisas():

    fx = yf.download(["EURUSD=X","GBPUSD=X"], period="2d", progress=False)

    eurusd = fx["Close"]["EURUSD=X"].iloc[-1]
    gbpusd = fx["Close"]["GBPUSD=X"].iloc[-1]

    return eurusd, gbpusd


eurusd, gbpusd = descargar_divisas()

tickers_acciones = df[df["TIPO"]!="FONDO"]["TICKER"].unique().tolist()

precios = descargar_precios(tickers_acciones)

close_data = precios["Close"]

# =========================
# FUNCIÓN NAV FONDOS
# =========================

def obtener_nav_fondo(row):

    try:

        isin = row["IDENTIFICADOR"]
        nombre = row["EMPRESA"]

        hoy = datetime.today().strftime("%d/%m/%Y")

        # Intentar por ISIN
        try:

            datos = investpy.get_fund_historical_data(
                fund=isin,
                country="luxembourg",
                from_date="01/01/2024",
                to_date=hoy
            )

        except:

            # Intentar por nombre
            datos = investpy.get_fund_historical_data(
                fund=nombre,
                country="luxembourg",
                from_date="01/01/2024",
                to_date=hoy
            )

        nav = datos["Close"].iloc[-1]
        nav_ayer = datos["Close"].iloc[-2]

        return nav, nav_ayer

    except:

        return 0,0


precio_actual = []
cambio_dia_eur = []
cambio_dia_pct = []

# =========================
# CALCULAR PRECIOS
# =========================

for _,row in df.iterrows():

    ticker = row["TICKER"]
    acciones = row["ACCIONES"]
    tipo = row["TIPO"]
    divisa = str(row.get("DIVISA","EUR")).upper()

    p_actual = 0
    p_ayer = 0

    # ---------- ACCIONES / ETF ----------

    if tipo != "FONDO":

        try:

            datos = close_data[ticker]

            p_actual = datos.iloc[-1]
            p_ayer = datos.iloc[-2]

        except:

            p_actual = 0
            p_ayer = 0

    # ---------- FONDOS ----------

    else:

        nav, nav_ayer = obtener_nav_fondo(row)

        p_actual = nav
        p_ayer = nav_ayer

    # ---------- DIVISAS ----------

    if divisa == "USD" and p_actual != 0:

        p_actual /= eurusd
        p_ayer /= eurusd

    if divisa == "GBP" and p_actual != 0:

        p_actual = (p_actual/100*gbpusd)/eurusd
        p_ayer = (p_ayer/100*gbpusd)/eurusd

    # ---------- CAMBIO DIARIO ----------

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

rentabilidad_total = (total_actual-total_inicial)/total_inicial*100

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
            delta=f"{mayor_subida['CAMBIO DÍA €']:,.2f} € ({mayor_subida['CAMBIO DÍA %']:.2f}%)"
        )

        col2.metric(
            "🔽 Mayor bajada",
            mayor_bajada["EMPRESA"],
            delta=f"{mayor_bajada['CAMBIO DÍA €']:,.2f} € ({mayor_bajada['CAMBIO DÍA %']:.2f}%)"
        )

        st.markdown("---")

        tabla=data[[
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

esp = acciones[acciones["TICKER"].str.endswith(".MC")]
uk = acciones[acciones["TICKER"].str.endswith(".L")]
eur = acciones[acciones["TICKER"].str.endswith((".DE",".AS",".PA"))]
usa = acciones[~acciones["TICKER"].str.contains(r"\.")]

st.header("📈 Acciones")

mostrar_tabla(esp,"🇪🇸 España")
mostrar_tabla(eur,"🇪🇺 Europa")
mostrar_tabla(usa,"🇺🇸 USA")
mostrar_tabla(uk,"🇬🇧 UK")

st.header("📊 ETFs")
mostrar_tabla(df[df["TIPO"]=="ETF"],"ETFs")

st.header("🏦 Fondos")
mostrar_tabla(df[df["TIPO"]=="FONDO"],"Fondos")
