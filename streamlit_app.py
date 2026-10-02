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
# 2. CONEXIÓN A DATOS
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    cred_dict = json.loads(st.secrets["google_credentials"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1Zr3YUCUXFwZIRRSGIBnnW60dji1pcnda1VHwZ6HXcYQ/edit?usp=sharing"
    doc = client.open_by_url(sheet_url)
    
    # MÉDICOS
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

    # FACTURACIÓN
    datos_fact = doc.worksheet('FACTURACION').get_all_values()
    idx_fac = next(i for i, row in enumerate(datos_fact) if 'NOMBRE' in row)
    df_fact = pd.DataFrame(datos_fact[idx_fac+1:], columns=datos_fact[idx_fac])
    df_fact = df_fact[df_fact['NOMBRE'] != ""]
    
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
# 3. BARRA LATERAL
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
# 4. CÁLCULO DE PORCENTAJES (SIN CIFRAS)
# ==========================================
monto_meses = [f'Monto {m}' for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']]
cant_meses = [f'Cantidad {m}' for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']]

# Globales (para sacar el %)
ingreso_global = df_fact[[c for c in monto_meses if c in df_fact.columns]].sum().sum()
pruebas_global = df_fact[[c for c in cant_meses if c in df_fact.columns]].sum().sum()

# Filtrados
ingreso_total = df_fact_filtrado[[c for c in monto_meses if c in df_fact_filtrado.columns]].sum().sum()
pruebas_totales = df_fact_filtrado[[c for c in cant_meses if c in df_fact_filtrado.columns]].sum().sum()

porcentaje_ingreso = (ingreso_total / ingreso_global) * 100 if ingreso_global > 0 else 0
porcentaje_pruebas = (pruebas_totales / pruebas_global) * 100 if pruebas_global > 0 else 0

# ==========================================
# 5. DASHBOARD - CABECERA
# ==========================================
st.markdown("<h1 class='titulo-principal'>📊 Inteligencia Comercial y Desempeño</h1>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Participación de Ingresos", f"{porcentaje_ingreso:.1f}%")
with col2:
    st.metric("Participación de Pruebas", f"{porcentaje_pruebas:.1f}%")
with col3:
    rep = df_med_filtrado['REPRESENTANTE'].iloc[0] if medico_seleccionado != "Todos" else "Múltiples"
    st.metric("Representante", rep)
with col4:
    esp = df_med_filtrado['ESPECIALIDAD'].iloc[0] if medico_seleccionado != "Todos" else "Todas"
    st.metric("Especialidad", esp)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 6. SISTEMA DE PESTAÑAS (TABS)
# ==========================================
tab1, tab2, tab3 = st.tabs(["🌎 Visión General", "🧬 Análisis de Pruebas", "🏆 Ranking y Beneficios"])

# --- PESTAÑA 1: VISIÓN GENERAL ---
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    col_gauge1, col_gauge2 = st.columns(2)
    
    with col_gauge1:
        # Velocímetro 100%
        fig_g1 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = porcentaje_pruebas,
            number = {'suffix': "%", 'valueformat': '.1f'},
            title = {'text': "Cuota de Pruebas", 'font': {'color': '#5C95A6', 'size': 18}},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#5C95A6"}, 'bgcolor': "#E5E5E5"}
        ))
        fig_g1.update_layout(height=300, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_g1, use_container_width=True)
        
    with col_gauge2:
        # Velocímetro 100%
        fig_g2 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = porcentaje_ingreso,
            number = {'suffix': "%", 'valueformat': '.1f'},
            title = {'text': "Cuota de Ingresos", 'font': {'color': '#87A98A', 'size': 18}},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#87A98A"}, 'bgcolor': "#E5E5E5"}
        ))
        fig_g2.update_layout(height=300, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_g2, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    
    colA, colB = st.columns([2, 1])
    with colA:
        st.subheader("📈 Tendencia Mensual (Sin Cifras)")
        ventas_por_mes = [df_fact_filtrado[col].sum() if col in df_fact_filtrado.columns else 0 for col in cant_meses]
        meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        df_linea = pd.DataFrame({'Mes': meses_nombres, 'Tendencia': ventas_por_mes})
        fig_line = px.line(df_linea, x='Mes', y='Tendencia', template="plotly_white", markers=True, line_shape="spline")
        fig_line.update_traces(line_color='#5C95A6', line_width=4, marker=dict(size=8, color='#87A98A'))
        # MAGIA: Ocultar los números del eje lateral para mayor confidencialidad
        fig_line.update_yaxes(showticklabels=False, title="")
        st.plotly_chart(fig_line, use_container_width=True)

    with colB:
        st.subheader("📍 Cobertura Activa")
        st.map(df_med_filtrado, zoom=4, color='#5C95A6')

# --- PESTAÑA 2: MIX DE PRUEBAS ---
with tab2:
    st.subheader("Porcentaje de Participación por Prueba")
    lista_df_prod = []
    for mes in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']:
        if f'Producto {mes}' in df_fact_filtrado.columns and f'Cantidad {mes}' in df_fact_filtrado.columns:
            temp = df_fact_filtrado[[f'Producto {mes}', f'Cantidad {mes}']].copy()
            temp.columns = ['Producto', 'Cantidad']
            lista_df_prod.append(temp)
            
    df_productos = pd.DataFrame()
    if lista_df_prod:
        df_productos = pd.concat(lista_df_prod).dropna()
        df_productos['Producto'] = df_productos['Producto'].astype(str).str.strip()
        df_productos = df_productos[(df_productos['Producto'] != '0') & (df_productos['Producto'] != '')]
        df_productos = df_productos.groupby('Producto')['Cantidad'].sum().reset_index()
        df_productos = df_productos[df_productos['Cantidad'] > 0].sort_values('Cantidad', ascending=False)
        total_p = df_productos['Cantidad'].sum()
        df_productos['Porcentaje'] = (df_productos['Cantidad'] / total_p) * 100 if total_p > 0 else 0

    if not df_productos.empty:
        top_pruebas = df_productos.head(4)
        cols_porcentaje = st.columns(len(top_pruebas))
        for idx, row in enumerate(top_pruebas.itertuples()):
            with cols_porcentaje[idx]:
                # Removimos las ventas exactas, ahora solo dice la prueba y el %
                st.metric(label=f"🧬 {row.Producto}", value=f"{row.Porcentaje:.1f}%")
                st.progress(int(row.Porcentaje))
        
        st.markdown("<br>", unsafe_allow_html=True)
        colores_marca = ['#5C95A6', '#87A98A', '#A3C1CC', '#999999', '#D1E0E5']
        fig_pie = px.pie(df_productos, values='Cantidad', names='Producto', hole=0.45, template="plotly_white", color_discrete_sequence=colores_marca)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+percent')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No hay ventas registradas para generar el desglose.")

# --- PESTAÑA 3: RANKING Y BENEFICIOS (TABLA 100% PORCENTUAL) ---
with tab3:
    st.subheader("🏆 Ranking de Participación (%)")
    
    df_ranking = []
    for index, row in df_fact_filtrado.iterrows():
        nombre = row['NOMBRE']
        ingresos_medico = sum(pd.to_numeric(row[c], errors='coerce') for c in monto_meses if c in df_fact.columns)
        pruebas_medico = sum(pd.to_numeric(row[c], errors='coerce') for c in cant_meses if c in df_fact.columns)
        df_ranking.append({'Médico': nombre, 'Pruebas': pruebas_medico, 'Ingreso ($)': ingresos_medico})
        
    df_ranking = pd.DataFrame(df_ranking).groupby('Médico').sum().reset_index().sort_values('Ingreso ($)', ascending=False)
    
    if not df_ranking.empty:
        # Convertir montos a porcentajes del total global
        df_ranking['% de Pruebas'] = (df_ranking['Pruebas'] / pruebas_global) * 100 if pruebas_global > 0 else 0
        df_ranking['% de Ingresos'] = (df_ranking['Ingreso ($)'] / ingreso_global) * 100 if ingreso_global > 0 else 0
        
        # Filtramos para que SOLO muestre las columnas de porcentaje (ocultamos dinero y número de pruebas)
        df_mostrar = df_ranking[['Médico', '% de Pruebas', '% de Ingresos']]
        
        st.dataframe(
            df_mostrar,
            column_config={
                "Médico": st.column_config.TextColumn("Nombre del Médico", width="medium"),
                "% de Pruebas": st.column_config.ProgressColumn("Participación de Pruebas", format="%.2f%%", min_value=0, max_value=100),
                "% de Ingresos": st.column_config.ProgressColumn("Participación de Ingresos", format="%.2f%%", min_value=0, max_value=100)
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Sin datos para generar ranking.")
