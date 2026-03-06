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

    if isinstance(t,str):

        if t.startswith("BME:"):
            return t.split(":")[1]+".MC"

        if t.startswith("LON:"):
            return t.split(":")[1]+".L"

        if t.startswith("ETR:"):
            return t.split(":")[1]+".DE"

        if t.startswith("AMS:"):
            return t.split(":")[1]+".AS"

        if t.startswith("EPA:"):
            return t.split(":")[1]+".PA"

        if t.startswith("NYSE:") or t.startswith("NASDAQ:"):
            return t.split(":")[1]

    return t

df["TICKER"] = df["IDENTIFICADOR"].apply(convertir_ticker)

# =========================
# CACHE PRECIOS
# =========================

@st.cache_data(ttl=1800)
def descargar_precios(tickers):

    return yf.download(
        tickers,
        period="2d",
        interval="1d",
        progress=False
    )

@st.cache_data(ttl=1800)
def descargar_divisas():

    fx=yf.download(["EURUSD=X","GBPUSD=X"],period="2d")

    eurusd=fx["Close"]["EURUSD=X"].iloc[-1]
    gbpusd=fx["Close"]["GBPUSD=X"].iloc[-1]

    return eurusd,gbpusd

eurusd,gbpusd=descargar_divisas()

tickers=df[df["TIPO"]!="FONDO"]["TICKER"].dropna().unique().tolist()

precios=descargar_precios(tickers)

close_data=precios["Close"]

# =========================
# NAV FONDOS
# =========================

def obtener_nav_fondo(identificador):

    try:

        hoy=datetime.today().strftime("%d/%m/%Y")

        datos=investpy.get_fund_historical_data(
            fund=identificador,
            country="luxembourg",
            from_date="01/01/2024",
            to_date=hoy
        )

        nav=datos["Close"].iloc[-1]
        nav_ayer=datos["Close"].iloc[-2]

        return nav,nav_ayer

    except:

        return 0,0

# =========================
# CALCULAR PRECIOS
# =========================

precio_actual=[]
cambio_dia_eur=[]
cambio_dia_pct=[]

for _,row in df.iterrows():

    ticker=row["TICKER"]
    acciones=row["ACCIONES"]
    tipo=row["TIPO"]
    divisa=str(row.get("DIVISA","EUR")).upper()

    p_actual=0
    p_ayer=0

    if tipo!="FONDO":

        try:

            datos=close_data[ticker]

            p_actual=datos.iloc[-1]
            p_ayer=datos.iloc[-2]

        except:
            pass

    else:

        nav,nav_ayer=obtener_nav_fondo(row["IDENTIFICADOR"])

        p_actual=nav
        p_ayer=nav_ayer

    if divisa=="USD" and p_actual!=0:

        p_actual/=eurusd
        p_ayer/=eurusd

    if divisa=="GBP" and p_actual!=0:

        p_actual=(p_actual/100*gbpusd)/eurusd
        p_ayer=(p_ayer/100*gbpusd)/eurusd

    if p_ayer!=0:

        cambio_eur=(p_actual-p_ayer)*acciones
        cambio_pct=((p_actual-p_ayer)/p_ayer)*100

    else:

        cambio_eur=0
        cambio_pct=0

    precio_actual.append(p_actual)
    cambio_dia_eur.append(cambio_eur)
    cambio_dia_pct.append(cambio_pct)

df["PRECIO ACTUAL €"]=precio_actual
df["CAMBIO DÍA €"]=cambio_dia_eur
df["CAMBIO DÍA %"]=cambio_dia_pct

# =========================
# CÁLCULOS
# =========================

df["VALOR ACTUAL €"]=df["PRECIO ACTUAL €"]*df["ACCIONES"]
df["DIFERENCIA €"]=df["VALOR ACTUAL €"]-df["PRECIO TOTAL"]
df["RENTABILIDAD %"]=df["DIFERENCIA €"]/df["PRECIO TOTAL"].replace(0,1)*100

total_inicial=df["PRECIO TOTAL"].sum()
total_actual=df["VALOR ACTUAL €"].sum()

rentabilidad_total=(total_actual-total_inicial)/total_inicial*100

cambio_total_dia=df["CAMBIO DÍA €"].sum()

# =========================
# CARDS
# =========================

col1,col2,col3=st.columns(3)

col1.metric("Inversión Inicial",f"{total_inicial:,.2f} €")
col2.metric("Valor Actual",f"{total_actual:,.2f} €",delta=f"{cambio_total_dia:,.2f} €")
col3.metric("Rentabilidad Total",f"{rentabilidad_total:.2f}%")

st.dataframe(df)
