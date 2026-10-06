import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import json

# ==========================================
# 1. CONFIGURACIÓN Y DISEÑO CORPORATIVO
# ==========================================
st.set_page_config(page_title="SouthGenetics | BI", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .titulo-principal {
        font-size: 2.2rem !important;
        color: #5C95A6 !important;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        margin-bottom: 0px;
        padding-bottom: 15px;
    }
    [data-testid="stMetric"] {
        background-color: #F8F9FA;
        border-left: 6px solid #5C95A6;
        border-radius: 8px;
        padding: 15px 20px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #333333 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #666666 !important;
        font-weight: bold;
    }
    h2, h3 { color: #5C95A6 !important; font-family: 'Arial', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN A DATOS Y CORRECCIÓN DE MONEDA
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    cred_dict = json.loads(st.secrets["google_credentials"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1Zr3YUCUXFwZIRRSGIBnnW60dji1pcnda1VHwZ6HXcYQ/edit?usp=sharing"
    doc = client.open_by_url(sheet_url)
    
    datos_medicos = doc.worksheet('MEDICOS').get_all_values()
    idx_med = next(i for i, row in enumerate(datos_medicos) if 'NOMBRE' in row)
    df_medicos = pd.DataFrame(datos_medicos[idx_med+1:], columns=datos_medicos[idx_med])
    df_medicos = df_medicos[df_medicos['NOMBRE'] != ""]
    
    coords = {
        'Guadalajara': [20.6596, -103.3496], 'Chihuahua': [28.6329, -106.0691],
        'CDMX Norte': [19.4326, -99.1332], 'CDMX Sur': [19.3000, -99.1500],
        'CDMX Centro': [19.4326, -99.1332], 'CDMX': [19.4326, -99.1332],
        'Monterrey': [25.6866, -100.3161], 'Mérida, México': [20.9673, -89.6242],
        'Cancun': [21.1619, -86.8515], 'Culiacan': [24.8032, -107.3938],
        'Tampico': [22.2158, -97.8584], 'Los Cabos': [22.8905, -109.9167],
        'Aguascalientes': [21.8853, -102.2916], 'Nuevo Leon': [25.6866, -100.3161],
        'Querétaro': [20.5881, -100.3899], 'Mazatlan': [23.2494, -106.4111],
        'Veracruz': [19.1738, -96.1342], 'Cd. Juárez': [31.7333, -106.4833]
    }
    df_medicos['lat'] = df_medicos['TERRITORIO'].map(lambda x: coords.get(x, [19.4326, -99.1332])[0])
    df_medicos['lon'] = df_medicos['TERRITORIO'].map(lambda x: coords.get(x, [19.4326, -99.1332])[1])

    datos_fact = doc.worksheet('FACTURACION').get_all_values()
    idx_fac = next(i for i, row in enumerate(datos_fact) if 'NOMBRE' in row)
    df_fact = pd.DataFrame(datos_fact[idx_fac+1:], columns=datos_fact[idx_fac])
    df_fact = df_fact[df_fact['NOMBRE'] != ""]
    
    for col in df_fact.columns:
        if 'Monto' in col or 'Inversión' in col or 'INVERSIÓN' in col.upper():
            texto_limpio = df_fact[col].astype(str).str.
