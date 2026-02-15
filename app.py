import streamlit as st
# ... (tus otros imports)

# Verificación segura de secretos
if "password" not in st.secrets:
    st.error("Error: No se ha configurado la contraseña en los 'Secrets' de Streamlit.")
    st.stop()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    password_usuario = st.text_input("Contraseña de acceso", type="password")
    if password_usuario == st.secrets["password"]:
        st.session_state.autenticado = True
        st.rerun()
    else:
        if password_usuario:
            st.error("Contraseña incorrecta")
        st.stop()

# --- TODO EL RESTO DEL CÓDIGO DE TU CARTERA ---
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Mi Cartera Internacional", layout="wide")

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

@st.cache_data(ttl=3600)
def cargar_datos():
    tickers = list(datos_cartera.keys())
    pares = ['EURUSD=X', 'EURGBP=X']
    precios = {}
    errores = []
    
    for s in tickers + pares:
        try:
            # Descarga individual para evitar MultiIndex
            df_temp = yf.download(s, period="5d", progress=False)
            if not df_temp.empty:
                # Forzamos la obtención del último valor disponible
                precios[s] = float(df_temp['Close'].iloc[-1])
            else:
                errores.append(s)
        except:
            errores.append(s)
    return precios, errores

# --- LÓGICA PRINCIPAL ---
st.title("📊 Mi Cartera Internacional")

with st.spinner('Cargando datos de mercado...'):
    precios_actuales, lista_errores = cargar_datos()

if precios_actuales:
    resumen = []
    # Tipos de cambio (usamos 1.0 como base para EUR)
    eur_usd = precios_actuales.get('EURUSD=X', 1.08)
    eur_gbp = precios_actuales.get('EURGBP=X', 0.85)
    
    for t, info in datos_cartera.items():
        if t not in precios_actuales:
            continue
            
        p_compra_eur, cant, div = info
        p_orig = precios_actuales[t]
        
        # Conversión a Euros
        if div == 'USD':
            p_eur = p_orig / eur_usd
        elif div == 'GBP':
            # Londres cotiza en peniques (GBp), dividimos por 100
            p_eur = (p_orig / 100) / eur_gbp
        else:
            p_eur = p_orig
            
        valor_actual = p_eur * cant
        invertido = p_compra_eur * cant
        ganancia = valor_actual - invertido
        
        resumen.append({
            'Activo': t,
            'Valor Actual (€)': valor_actual,
            'Invertido (€)': invertido,
            'B/P (€)': ganancia,
            'Rent. (%)': (ganancia / invertido) * 100 if invertido != 0 else 0
        })

    df = pd.DataFrame(resumen)

    # Métricas Globales
    total_inv = df['Invertido (€)'].sum()
    total_val = df['Valor Actual (€)'].sum()
    total_bp = total_val - total_inv
    total_perc = (total_bp / total_inv) * 100 if total_inv != 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Invertido", f"{total_inv:,.2f} €")
    c2.metric("Valor Cartera", f"{total_val:,.2f} €", f"{total_bp:,.2f} €")
    c3.metric("Rentabilidad Total", f"{total_perc:.2f} %")

    # Gráficos
    st.plotly_chart(px.bar(df, x='Activo', y='B/P (€)', color='B/P (€)', 
                           title="Beneficio/Pérdida por Activo",
                           color_continuous_scale='RdYlGn'), use_container_width=True)

    st.subheader("Detalle de posiciones")
    st.dataframe(df.style.format({
        'Valor Actual (€)': '{:,.2f}',
        'Invertido (€)': '{:,.2f}',
        'B/P (€)': '{:,.2f}',
        'Rent. (%)': '{:.2f}%'
    }), use_container_width=True)

    if lista_errores:
        with st.expander("Ver activos no disponibles"):
            st.write(", ".join(lista_errores))
else:
    st.error("No se pudieron obtener datos de Yahoo Finance. Reintenta en unos minutos.")

