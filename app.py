import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. SEGURIDAD
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Contraseña incorrecta", type="password", on_change=password_entered, key="password")
        return False
    return True

# 2. CARTERA COMPLETA
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
            df = yf.download(s, period="1y", progress=False)
            if not df.empty:
                col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
                precios[s] = df[col]
            else:
                errores.append(s)
        except:
            errores.append(s)
            
    return pd.DataFrame(precios).ffill(), errores

# 3. INTERFAZ PRINCIPAL
if check_password():
    st.title("📊 Cartera Internacional")
    
    with st.spinner('Actualizando precios de mercado...'):
        data, lista_errores = cargar_datos()
    
    if not data.empty:
        hoy = data.index[-1]
        resumen = []
        
        for t, info in datos_cartera.items():
            if t not in data.columns: continue
            
            p_compra_eur, cant, div = info
            p_act_orig = data.loc[hoy, t].values[0] if isinstance(data.loc[hoy, t], pd.Series) else data.loc[hoy, t]
            
            # Conversión
            if div == 'USD': p_eur = p_act_orig / data.loc[hoy, 'EURUSD=X']
            elif div == 'GBP': p_eur = (p_act_orig / 100) / data.loc[hoy, 'EURGBP=X']
            else: p_eur = p_act_orig
            
            val_act = float(p_eur) * cant
            inv = p_compra_eur * cant
            
            resumen.append({'Activo': t, 'Valor Actual (€)': val_act, 'B/P (€)': val_act - inv, 'Rent %': ((val_act/inv)-1)*100, 'Invertido': inv})

        df_res = pd.DataFrame(resumen)
        
        # Dashboard
        m1, m2, m3 = st.columns(3)
        total_inv = df_res['Invertido'].sum()
        total_val = df_res['Valor Actual (€)'].sum()
        m1.metric("Inversión", f"{total_inv:,.2f}€")
        m2.metric("Valor Actual", f"{total_val:,.2f}€", f"{total_val-total_inv:,.2f}€")
        m3.metric("Rentabilidad", f"{( (total_val/total_inv)-1)*100:.2f}%")
        
        st.plotly_chart(px.bar(df_res, x='Activo', y='B/P (€)', color='B/P (€)', color_continuous_scale='RdYlGn'))
        st.dataframe(df_res.style.format({'Valor Actual (€)': '{:,.2f}', 'B/P (€)': '{:,.2f}', 'Rent %': '{:.2f}%'}))

    # Sección de Salud de Datos
    if lista_errores:
        with st.expander("⚠️ Aviso de Salud de la Cartera"):
            st.write("Los siguientes tickers no respondieron y no aparecen en la tabla:")
            st.write(", ".join(lista_errores))
