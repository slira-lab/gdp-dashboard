import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(page_title="Dashboard Comercial Médico", layout="wide")

@st.cache_data(ttl=600)
def load_data():
    cred_dict = json.loads(st.secrets["google_credentials"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1Zr3YUCUXFwZIRRSGIBnnW60dji1pcnda1VHwZ6HXcYQ/edit?usp=sharing"
    doc = client.open_by_url(sheet_url)
    
    # --- LEER MÉDICOS CON DETECTOR AUTOMÁTICO ---
    datos_medicos = doc.worksheet('MEDICOS').get_all_values()
    idx_med = next(i for i, row in enumerate(datos_medicos) if 'NOMBRE' in row)
    df_medicos = pd.DataFrame(datos_medicos[idx_med+1:], columns=datos_medicos[idx_med])
    df_medicos = df_medicos[df_medicos['NOMBRE'] != ""]
    
    # Coordenadas para el mapa
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

    # --- LEER FACTURACIÓN CON DETECTOR AUTOMÁTICO ---
    datos_fact = doc.worksheet('FACTURACION').get_all_values()
    idx_fac = next(i for i, row in enumerate(datos_fact) if 'NOMBRE' in row)
    df_fact = pd.DataFrame(datos_fact[idx_fac+1:], columns=datos_fact[idx_fac])
    df_fact = df_fact[df_fact['NOMBRE'] != ""]
    
    # Limpiar columnas de dinero para poder sumarlas
    monto_cols = [f'Monto {m}' for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']]
    for col in monto_cols:
        if col in df_fact.columns:
            df_fact[col] = df_fact[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df_fact[col] = pd.to_numeric(df_fact[col], errors='coerce').fillna(0)

    # Limpiar columnas de cantidad 
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

# --- FILTROS LATERALES ---
st.sidebar.title("Menú Ejecutivo")
lista_medicos = ["Todos"] + df_medicos['NOMBRE'].unique().tolist()
medico_seleccionado = st.sidebar.selectbox("Seleccione un Médico", lista_medicos)

# Filtrar bases de datos
if medico_seleccionado != "Todos":
    df_med_filtrado = df_medicos[df_medicos['NOMBRE'] == medico_seleccionado]
    df_fact_filtrado = df_fact[df_fact['NOMBRE'] == medico_seleccionado]
else:
    df_med_filtrado = df_medicos
    df_fact_filtrado = df_fact

# --- TARJETAS DE INDICADORES (KPIs REALES) ---
st.title("📊 Portal de Inteligencia Comercial")

monto_meses = ['Monto Enero', 'Monto Febrero', 'Monto Marzo', 'Monto Abril', 'Monto Mayo', 'Monto Junio', 'Monto Julio', 'Monto Agosto', 'Monto Septiembre', 'Monto Octubre', 'Monto Noviembre', 'Monto Diciembre']
ingreso_total = df_fact_filtrado[[c for c in monto_meses if c in df_fact_filtrado.columns]].sum().sum()

# Cálculo de pruebas extraídas de "Cantidad"
cant_meses = ['Cantidad Enero', 'Cantidad Febrero', 'Cantidad Marzo', 'Cantidad Abril', 'Cantidad Mayo', 'Cantidad Junio', 'Cantidad Julio', 'Cantidad Agosto', 'Cantidad Septiembre', 'Cantidad Octubre', 'Cantidad Noviembre', 'Cantidad Diciembre']
pruebas_totales = df_fact_filtrado[[c for c in cant_meses if c in df_fact_filtrado.columns]].sum().sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ingreso Total Real", f"${ingreso_total:,.2f}")
with col2:
    st.metric("Total de Pruebas", int(pruebas_totales))
with col3:
    rep = df_med_filtrado['REPRESENTANTE'].iloc[0] if medico_seleccionado != "Todos" else "Varios"
    st.metric("Representante a Cargo", rep)
with col4:
    esp = df_med_filtrado['ESPECIALIDAD'].iloc[0] if medico_seleccionado != "Todos" else "Todas"
    st.metric("Especialidad", esp)

st.markdown("---")

# --- GRÁFICOS (LÍNEAS Y PASTEL) ---
colA, colB, colC = st.columns([2, 1, 1])

with colA:
    st.subheader("📈 Evolución de Ventas")
    # Extraer los datos mes a mes reales
    ventas_por_mes = [df_fact_filtrado[col].sum() if col in df_fact_filtrado.columns else 0 for col in monto_meses]
    meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    df_linea = pd.DataFrame({'Mes': meses_nombres, 'Ventas': ventas_por_mes})
    # Cambiamos a gráfico de líneas interactivo
    fig_line = px.line(df_linea, x='Mes', y='Ventas', template="plotly_dark", markers=True, line_shape="spline")
    fig_line.update_traces(line_color='#00a4ff', line_width=4, marker=dict(size=8))
    st.plotly_chart(fig_line, use_container_width=True)

with colB:
    st.subheader("🧬 Mix de Pruebas")
    # Algoritmo para extraer y sumar pruebas reales vendidas
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
            fig_pie = px.pie(df_productos, values='Cantidad', names='Producto', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin pruebas registradas")

with colC:
    st.subheader("📍 Ubicación")
    # Mapa de México usando latitud y longitud
    st.map(df_med_filtrado, zoom=4, color='#00a4ff')
    territorio = df_med_filtrado['TERRITORIO'].iloc[0] if medico_seleccionado != "Todos" else "Nacional"
    st.caption(f"Zona de influencia: **{territorio}**")
