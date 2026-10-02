import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(page_title="Dashboard Comercial Médico", layout="wide")

@st.cache_data(ttl=600) # Se actualiza solo cada 10 minutos
def load_data():
    # 1. Leer la Llave Secreta
    cred_dict = json.loads(st.secrets["google_credentials"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 2. Conectar a tu Excel (¡PON TU LINK AQUÍ ABAJO!)
    sheet_url = "https://docs.google.com/spreadsheets/d/1Zr3YUCUXFwZIRRSGIBnnW60dji1pcnda1VHwZ6HXcYQ/edit?usp=sharing"
    doc = client.open_by_url(sheet_url)
    
    # 3. Leer la lista de Médicos
    datos = doc.worksheet('MEDICOS').get_all_values()
    df = pd.DataFrame(datos[2:], columns=datos[1]) # Toma los títulos de tu Excel
    df = df[df['NOMBRE'] != ""] # Quita filas vacías
    return df

st.title("📊 Portal de Inteligencia Comercial")

try:
    df_medicos = load_data()
except Exception as e:
    st.warning("Conectando con la Base de Datos... (Asegúrate de pegar la llave secreta en el Paso 3)")
    st.stop()

# --- FILTROS LATERALES ---
st.sidebar.title("Menú Ejecutivo")
lista_medicos = ["Todos"] + df_medicos['NOMBRE'].unique().tolist()
medico_seleccionado = st.sidebar.selectbox("Seleccione un Médico", lista_medicos)

if medico_seleccionado != "Todos":
    df_filtrado = df_medicos[df_medicos['NOMBRE'] == medico_seleccionado]
else:
    df_filtrado = df_medicos

# --- TARJETAS DE INDICADORES (KPIs) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ingreso Total Real", "$2,030,112", "+ 15% vs mes anterior")
with col2:
    st.metric("Total de Pruebas", "385")
with col3:
    rep = df_filtrado['REPRESENTANTE'].iloc[0] if medico_seleccionado != "Todos" else "Varios"
    st.metric("Representante a Cargo", rep)
with col4:
    esp = df_filtrado['ESPECIALIDAD'].iloc[0] if medico_seleccionado != "Todos" else "Todas"
    st.metric("Especialidad", esp)

st.markdown("---")

# --- GRÁFICOS ---
colA, colB = st.columns([2, 1])

with colA:
    st.subheader("📈 Evolución de Ventas (Histograma)")
    # Simularemos los meses aquí, en el siguiente paso conectaremos tu hoja de facturación
    df_chart = pd.DataFrame({'Mes': ['Ene','Feb','Mar','Abr','May','Jun'], 'Ventas': [120, 150, 180, 130, 200, 250]})
    fig = px.bar(df_chart, x='Mes', y='Ventas', template="plotly_dark", color_discrete_sequence=['#00a4ff'])
    st.plotly_chart(fig, use_container_width=True)

with colB:
    st.subheader("📍 Ubicación")
    territorio = df_filtrado['TERRITORIO'].iloc[0] if medico_seleccionado != "Todos" else "México Nacional"
    st.info(f"📍 Zona de influencia: **{territorio}**")
