import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json

# ==========================================
# 1. CONFIGURACIÓN Y DISEÑO CORPORATIVO
# ==========================================
st.set_page_config(page_title="SouthGenetics | Dashboard Comercial", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Tarjetas de Indicadores Principales */
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border-left: 5px solid #5C95A6;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    /* Títulos con color de la marca */
    h1, h2, h3 { color: #5C95A6 !important; font-family: 'Arial', sans-serif; }
    /* Estilo de la tabla de beneficios */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN Y LIMPIEZA DE DATOS (Optimizada)
# ==========================================
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
    
    # COORDENADAS MAPA
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

    # LEER FACTURACIÓN Y BENEFICIOS
    datos_fact = doc.worksheet('FACTURACION').get_all_values()
    idx_fac = next(i for i, row in enumerate(datos_fact) if 'NOMBRE' in row)
    df_fact = pd.DataFrame(datos_fact[idx_fac+1:], columns=datos_fact[idx_fac])
    df_fact = df_fact[df_fact['NOMBRE'] != ""]
    
    # Limpiar columnas numéricas (Montos, Cantidades e Inversiones)
    for col in df_fact.columns:
        if 'Monto' in col or 'Inversión' in col or 'INVERSIÓN' in col.upper():
            df_fact[col] = df_fact[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df_fact[col] = pd.to_numeric(df_fact[col], errors='coerce').fillna(0)
        elif 'Cantidad' in col:
            df_fact[col] = pd.to_numeric(df_fact[col], errors='coerce').fillna(0)
            
    return df_medicos, df_fact

try:
    df_medicos, df_fact = load_data()
except Exception as e:
    st.error(f"Error conectando a la base de datos: {e}")
    st.stop()

# ==========================================
# 3. BARRA LATERAL (LOGO Y FILTROS)
# ==========================================
try:
    st.sidebar.image("LOGO SG (1) (2).png", use_container_width=True)
except:
    st.sidebar.markdown("### SouthGenetics")

st.sidebar.markdown("---")
st.sidebar.title("Filtro Ejecutivo")
lista_medicos = ["Todos"] + df_medicos['NOMBRE'].unique().tolist()
medico_seleccionado = st.sidebar.selectbox("Seleccione un Médico", lista_medicos)

if medico_seleccionado != "Todos":
    df_med_filtrado = df_medicos[df_medicos['NOMBRE'] == medico_seleccionado]
    df_fact_filtrado = df_fact[df_fact['NOMBRE'] == medico_seleccionado]
else:
    df_med_filtrado = df_medicos
    df_fact_filtrado = df_fact

# ==========================================
# 4. PROCESAMIENTO DE PRUEBAS VENDIDAS
# ==========================================
meses_completos = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
lista_df_prod = []

for mes in meses_completos:
    c_prod, c_cant = f'Producto {mes}', f'Cantidad {mes}'
    if c_prod in df_fact_filtrado.columns and c_cant in df_fact_filtrado.columns:
        temp = df_fact_filtrado[[c_prod, c_cant]].copy()
        temp.columns = ['Producto', 'Cantidad']
        lista_df_prod.append(temp)

df_productos = pd.DataFrame()
if lista_df_prod:
    df_productos = pd.concat(lista_df_prod)
    df_productos = df_productos[df_productos['Producto'].notna()]
    df_productos['Producto'] = df_productos['Producto'].astype(str).str.strip()
    df_productos = df_productos[(df_productos['Producto'] != '0') & (df_productos['Producto'] != '')]
    df_productos = df_productos.groupby('Producto')['Cantidad'].sum().reset_index()
    df_productos = df_productos[df_productos['Cantidad'] > 0].sort_values('Cantidad', ascending=False)
    
    # Calcular Porcentajes
    total_pruebas = df_productos['Cantidad'].sum()
    df_productos['Porcentaje'] = (df_productos['Cantidad'] / total_pruebas) * 100 if total_pruebas > 0 else 0

# ==========================================
# 5. DASHBOARD VISUAL
# ==========================================
st.title("📊 Análisis de Desempeño y Territorios")
st.markdown("---")

# FILA 1: DESGLOSE DE PORCENTAJES DE PRUEBAS (El nuevo requerimiento)
st.subheader("🧬 Desglose de Pruebas (%)")
if not df_productos.empty:
    # Mostramos el top 4 de pruebas para que se vea estético
    top_pruebas = df_productos.head(4)
    cols_porcentaje = st.columns(len(top_pruebas))
    
    for idx, row in enumerate(top_pruebas.itertuples()):
        with cols_porcentaje[idx]:
            st.metric(label=f"Prueba: {row.Producto}", value=f"{row.Porcentaje:.1f}%", delta=f"{int(row.Cantidad)} vendidas", delta_color="off")
            # Barra de progreso visual
            st.progress(int(row.Porcentaje))
else:
    st.info("No hay ventas registradas para generar el porcentaje.")

st.markdown("<br>", unsafe_allow_html=True)

# FILA 2: GRÁFICOS (Evolución y Donillo)
col_graf1, col_graf2 = st.columns([2, 1])

with col_graf1:
    st.subheader("📈 Evolución de Ventas (Volumen Mensual)")
    cant_meses = [f'Cantidad {m}' for m in meses_completos]
    ventas_por_mes = [df_fact_filtrado[col].sum() if col in df_fact_filtrado.columns else 0 for col in cant_meses]
    meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    df_linea = pd.DataFrame({'Mes': meses_nombres, 'Pruebas': ventas_por_mes})
    fig_line = px.line(df_linea, x='Mes', y='Pruebas', template="plotly_dark", markers=True, line_shape="spline")
    fig_line.update_traces(line_color='#5C95A6', line_width=4, marker=dict(size=8, color='#87A98A'))
    st.plotly_chart(fig_line, use_container_width=True)

with col_graf2:
    st.subheader("📊 Mix Histórico")
    if not df_productos.empty:
        colores_marca = ['#5C95A6', '#87A98A', '#A3C1CC', '#999999', '#D1E0E5']
        fig_pie = px.pie(df_productos, values='Cantidad', names='Producto', hole=0.45, template="plotly_dark", color_discrete_sequence=colores_marca)
        fig_pie.update_layout(showlegend=False)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# FILA 3: BENEFICIOS (INVERSIÓN) Y MAPA
col_ben, col_mapa = st.columns([2, 1])

with col_ben:
    st.subheader("🏆 Médicos con Programa de Beneficios")
    
    # Buscar la columna de Inversión
    col_inversion = next((c for c in df_fact.columns if 'Inversión Total' in c or 'INVERSIÓN' in c.upper()), None)
    
    if col_inversion:
        # Filtrar solo los que tienen inversión mayor a 0
        df_beneficios = df_fact[df_fact[col_inversion] > 0][['NOMBRE', col_inversion]].copy()
        
        if not df_beneficios.empty:
            # Cruzar con datos médicos para traer especialidad y territorio
            df_beneficios = pd.merge(df_beneficios, df_medicos[['NOMBRE', 'ESPECIALIDAD', 'TERRITORIO']], on='NOMBRE', how='left')
            df_beneficios = df_beneficios.rename(columns={col_inversion: 'Inversión (USD)'})
            
            # Formatear el dinero para que se vea bonito
            df_beneficios['Inversión (USD)'] = df_beneficios['Inversión (USD)'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_beneficios, use_container_width=True, hide_index=True)
        else:
            st.info("Ningún médico en la selección actual cuenta con Inversión registrada.")
    else:
        st.warning("No se encontró la columna de 'Inversión Total' en la hoja de Facturación.")

with col_mapa:
    st.subheader("📍 Cobertura")
    st.map(df_med_filtrado, zoom=4, color='#5C95A6')
    territorio = df_med_filtrado['TERRITORIO'].iloc[0] if medico_seleccionado != "Todos" else "Nacional"
    st.caption(f"**Zona actual:** {territorio}")
