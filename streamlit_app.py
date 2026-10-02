import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Dashboard Comercial | SouthGenetics", layout="wide")

# 2. DISEÑO CORPORATIVO (CSS) - Colores de SouthGenetics
st.markdown("""
<style>
    /* Estilo de Tarjetas para los KPIs */
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border-left: 5px solid #5C95A6; /* Color Teal del logo */
        border-right: 1px solid #333333;
        border-top: 1px solid #333333;
        border-bottom: 1px solid #333333;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    /* Darle color corporativo a los títulos */
    h1, h2, h3 {
        color: #5C95A6 !important; 
        font-family: 'Arial', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data():
    cred_dict = json.loads(st.secrets["google_credentials"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1Zr3YUCUXFwZIRRSGIBnnW60dji1pcnda1VHwZ6HXcYQ/edit?usp=sharing"
    doc = client.open_by_url(sheet_url)
    
    # LEER MÉDICOS
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

    # LEER FACTURACIÓN
    datos_fact = doc.worksheet('FACTURACION').get_all_values()
    idx_fac = next(i for i, row in enumerate(datos_fact) if 'NOMBRE' in row)
    df_fact = pd.DataFrame(datos_fact[idx_fac+1:], columns=datos_fact[idx_fac])
    df_fact = df_fact[df_fact['NOMBRE'] != ""]
    
    monto_cols = [f'Monto {m}' for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']]
    for col in monto_cols:
        if col in df_fact.columns:
            df_fact[col] = df_fact[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df_fact[col] = pd.to_numeric(df_fact[col], errors='coerce').fillna(0)

    cant_cols = [f'Cantidad {m}' for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']]
    for col in cant_cols:
        if col in df_fact.columns:
            df_fact[col] = pd.to_numeric(df_fact[col], errors='coerce').fillna(0)
            
    return df_medicos, df_fact

try:
    df_medicos, df_fact = load_data()
except Exception as e:
    st.error(f"Error técnico: {e}")
    st.stop()

# --- BARRA LATERAL (LOGO Y FILTROS) ---
try:
    st.sidebar.image("LOGO SG (1) (2).png", use_container_width=True)
except:
    st.sidebar.markdown("### SouthGenetics") # Por si el nombre de la imagen varía

st.sidebar.markdown("---")
st.sidebar.title("Menú Ejecutivo")
lista_medicos = ["Todos"] + df_medicos['NOMBRE'].unique().tolist()
medico_seleccionado = st.sidebar.selectbox("Seleccione un Médico", lista_medicos)

if medico_seleccionado != "Todos":
    df_med_filtrado = df_medicos[df_medicos['NOMBRE'] == medico_seleccionado]
    df_fact_filtrado = df_fact[df_fact['NOMBRE'] == medico_seleccionado]
else:
    df_med_filtrado = df_medicos
    df_fact_filtrado = df_fact

# --- CABECERA ---
st.title("📊 Inteligencia Comercial y Territorios")
st.markdown("Plataforma de análisis de ventas y posicionamiento médico estratégico.")
st.markdown("<br>", unsafe_allow_html=True) # Espacio en blanco

# --- TARJETAS DE INDICADORES (KPIs) ---
monto_meses = ['Monto Enero', 'Monto Febrero', 'Monto Marzo', 'Monto Abril', 'Monto Mayo', 'Monto Junio', 'Monto Julio', 'Monto Agosto', 'Monto Septiembre', 'Monto Octubre', 'Monto Noviembre', 'Monto Diciembre']
ingreso_total = df_fact_filtrado[[c for c in monto_meses if c in df_fact_filtrado.columns]].sum().sum()

cant_meses = ['Cantidad Enero', 'Cantidad Febrero', 'Cantidad Marzo', 'Cantidad Abril', 'Cantidad Mayo', 'Cantidad Junio', 'Cantidad Julio', 'Cantidad Agosto', 'Cantidad Septiembre', 'Cantidad Octubre', 'Cantidad Noviembre', 'Cantidad Diciembre']
pruebas_totales = df_fact_filtrado[[c for c in cant_meses if c in df_fact_filtrado.columns]].sum().sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ingreso Total Real", f"${ingreso_total:,.2f}")
with col2:
    st.metric("Total de Pruebas", int(pruebas_totales))
with col3:
    rep = df_med_filtrado['REPRESENTANTE'].iloc[0] if medico_seleccionado != "Todos" else "Múltiples"
    st.metric("Representante", rep)
with col4:
    esp = df_med_filtrado['ESPECIALIDAD'].iloc[0] if medico_seleccionado != "Todos" else "Todas"
    st.metric("Especialidad", esp)

st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# SECCIÓN 1: LÍNEA DE TENDENCIA (RENGLÓN 1)
# ==========================================
st.subheader("📈 Evolución de Ventas (Mensual)")
ventas_por_mes = [df_fact_filtrado[col].sum() if col in df_fact_filtrado.columns else 0 for col in monto_meses]
meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

df_linea = pd.DataFrame({'Mes': meses_nombres, 'Ventas': ventas_por_mes})
fig_line = px.line(df_linea, x='Mes', y='Ventas', template="plotly_dark", markers=True, line_shape="spline")
# Color Teal de SouthGenetics
fig_line.update_traces(line_color='#5C95A6', line_width=5, marker=dict(size=10, color='#999999'))
st.plotly_chart(fig_line, use_container_width=True)

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# ==========================================
# SECCIÓN 2: PASTEL DE PRUEBAS (RENGLÓN 2)
# ==========================================
st.subheader("🧬 Mix de Pruebas Vendidas")
meses_completos = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
lista_df_prod = []

for mes in meses_completos:
    c_prod = f'Producto {mes}'
    c_cant = f'Cantidad {mes}'
    if c_prod in df_fact_filtrado.columns and c_cant in df_fact_filtrado.columns:
        temp = df_fact_filtrado[[c_prod, c_cant]].copy()
        temp.columns = ['Producto', 'Cantidad']
        lista_df_prod.append(temp)
        
if lista_df_prod:
    df_productos = pd.concat(lista_df_prod)
    df_productos = df_productos[df_productos['Producto'].notna()]
    df_productos['Producto'] = df_productos['Producto'].astype(str).str.strip()
    df_productos = df_productos[(df_productos['Producto'] != '0') & (df_productos['Producto'] != '')]
    df_productos = df_productos.groupby('Producto')['Cantidad'].sum().reset_index()
    df_productos = df_productos[df_productos['Cantidad'] > 0]
    
    if not df_productos.empty:
        # Paleta de colores corporativos
        colores_marca = ['#5C95A6', '#87A98A', '#A3C1CC', '#999999', '#D1E0E5']
        fig_pie = px.pie(df_productos, values='Cantidad', names='Producto', hole=0.5, template="plotly_dark", color_discrete_sequence=colores_marca)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No hay ventas de pruebas registradas para esta selección.")

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# ==========================================
# SECCIÓN 3: MAPA TERRITORIAL (RENGLÓN 3)
# ==========================================
st.subheader("📍 Cobertura y Territorio Médico")
st.map(df_med_filtrado, zoom=5, color='#5C95A6')
territorio = df_med_filtrado['TERRITORIO'].iloc[0] if medico_seleccionado != "Todos" else "Cobertura Nacional"
st.caption(f"**Zona de análisis actual:** {territorio}")
