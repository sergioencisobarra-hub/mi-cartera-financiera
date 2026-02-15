import streamlit as st
# ... (los demás imports se quedan igual)

# Función para verificar la contraseña
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # No guardar la contraseña
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Introduce la contraseña para ver la cartera", 
                      type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Contraseña incorrecta", 
                      type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

# --- LÓGICA PRINCIPAL ---
if check_password():
    # AQUÍ PEGAS TODO EL RESTO DEL CÓDIGO QUE YA TENÍAS
    st.title("📊 Control de Cartera Multidivisa")
    # ... resto del código ...
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Mi Cartera Internacional", layout="wide")

st.title("📊 Control de Cartera Multidivisa")
st.markdown("Análisis en tiempo real con impacto de divisa (EUR/USD/GBP)")

# 1. BASE DE DATOS DE TU CARTERA
datos_cartera = {
    'ENG.MC': [19.89, 350, 'EUR'], 'ITX.MC': [24.55, 100, 'EUR'], 'RED.MC': [15.756, 350, 'EUR'],
    'TRE.MC': [25.51, 100, 'EUR'], 'MFEA.MC': [6.77, 140, 'EUR'], 'VIS.MC': [44.76, 30, 'EUR'],
    'NG.L': [7.56, 290, 'GBP'], 'BATS.L': [25.6841, 100, 'GBP'], 'VOD.L': [1.82698, 1000, 'GBP'],
    'ADM.L': [20.0, 50, 'GBP'], 'LGEN.L': [2.27, 500, 'GBP'], 'IMB.L': [18.0939, 100, 'GBP'],
    'GSK.L': [15.09, 100, 'GBP'], 'RKT.L': [54.42, 33, 'GBP'], 'DGE.L': [28.3433, 100, 'GBP'],
    'SHEL.L': [11.08, 100, 'GBP'], 'BAS.DE': [59.6, 25, 'EUR'], 'BAYN.DE': [49.35, 50, 'EUR'],
    'BMW.DE': [62.1, 25, 'EUR'], 'MBG.DE': [29.58, 30, 'EUR'], 'SIE.DE': [92.5, 15, 'EUR'],
    'PFE': [24.94, 75, 'USD'], 'PEP': [141.5, 20, 'USD'], 'GIS': [52.05, 25, 'USD'],
    'LYB': [47.43, 25, 'USD'], 'UNA.AS': [48.78, 44, 'EUR'], 'URW.PA': [91.07, 30, 'EUR'],
    'AENA.MC': [13.72, 200, 'EUR'], 'IBE.MC': [8.23, 205, 'EUR'], 'EBRO.MC': [16.095, 50, 'EUR'],
    'LOG.MC': [14.14, 75, 'EUR'], 'SAN.MC': [2.46, 300, 'EUR'], 'MMM': [151.9655, 20, 'USD'],
    'XOM': [60.78, 20, 'USD'], 'IBM': [104.61, 15, 'USD'], 'BMY': [43.22, 50, 'USD'],
    'O': [55.35, 25, 'USD'], 'MRK': [62.16, 15, 'USD'], 'MDT': [72.77, 10, 'USD'],
    'INTC': [35.36, 50, 'USD'], 'CSCO': [37.47, 30, 'USD'], 'GOOGL': [107.96, 10, 'USD'],
    'MSFT': [221.95, 5, 'USD'], 'AMZN': [99.48, 10, 'USD'], 'JNJ': [114.09, 10, 'USD'],
    'PG': [117.7, 25, 'USD'], 'DIS': [88.34, 15, 'USD'], 'KMB': [88.69, 10, 'USD'],
    'KHC': [29.06, 50, 'USD'], 'MO': [31.66, 30, 'USD'], 'VFC': [23.798, 50, 'USD'],
    'NKE': [51.23, 25, 'USD'], 'TROW': [112.38, 20, 'USD'], 'VZ': [46.87, 50, 'USD'],
    'T': [31.47, 100, 'USD']
}

@st.cache_data(ttl=3600) # Cache para no saturar la API
def cargar_datos():
    tickers = list(datos_cartera.keys())
    # Descargamos precios de 1 año para los históricos
    data = yf.download(tickers + ['EURUSD=X', 'EURGBP=X'], period="1y")['Adj Close']
    return data

data = cargar_datos()
hoy = data.index[-1]
y1_date = data.index[0]

# Procesamiento
resumen = []
for t, info in datos_cartera.items():
    p_compra_eur, cant, div = info
    p_act = data.loc[hoy, t]
    
    # Obtener FX
    fx_usd = data.loc[hoy, 'EURUSD=X']
    fx_gbp = data.loc[hoy, 'EURGBP=X']
    
    # Conversión actual
    if div == 'USD': p_eur = p_act / fx_usd
    elif div == 'GBP': p_eur = (p_act / 100) / fx_gbp
    else: p_eur = p_act
    
    val_act = p_eur * cant
    invested = p_compra_eur * cant
    profit = val_act - invested
    
    resumen.append({
        'Activo': t,
        'Valor Actual (€)': val_act,
        'B/P (€)': profit,
        'Rent. (%)': (profit / invested) * 100,
        'Invertido': invested
    })

df = pd.DataFrame(resumen)

# --- INTERFAZ ---
total_inv = df['Invertido'].sum()
total_val = df['Valor Actual (€)'].sum()
total_profit = total_val - total_inv
total_perc = (total_profit / total_inv) * 100

# Métricas destacadas en el Sidebar
st.sidebar.header("Resumen General")
st.sidebar.metric("Inversión Total", f"{total_inv:,.2f} €")
st.sidebar.metric("Valor Actual", f"{total_val:,.2f} €", f"{total_profit:,.2f} €")
st.sidebar.metric("Rentabilidad Global", f"{total_perc:.2f} %")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    fig_pie = px.pie(df, values='Valor Actual (€)', names='Activo', title="Peso de cada activo")
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    fig_bar = px.bar(df, x='Activo', y='B/P (€)', color='B/P (€)', 
                     title="Beneficio/Pérdida por Acción", color_continuous_scale='RdYlGn')
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Detalle de Cartera")
st.dataframe(df.style.format({
    'Valor Actual (€)': '{:,.2f}',
    'B/P (€)': '{:,.2f}',
    'Rent. (%)': '{:.2f}%',
    'Invertido': '{:,.2f}'

}), use_container_width=True)
