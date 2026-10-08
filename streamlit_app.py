import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import json
import requests

# ==========================================
# 1. CONFIGURACIÓN Y DISEÑO CORPORATIVO (DARK MODE)
# ==========================================
st.set_page_config(page_title="SouthGenetics | BI", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Estilos adaptados para Dark Mode */
    .titulo-principal {
        font-size: 2.2rem !important;
        color: #5C95A6 !important;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        margin-bottom: 0px;
        padding-bottom: 10px;
    }
    .descripcion-modulo {
        color: #B4B4B4;
        font-size: 1.1rem;
        margin-top: 0px;
        margin-bottom: 25px;
        border-bottom: 1px solid #333333;
        padding-bottom: 15px;
    }
    [data-testid="stMetric"] {
        background-color: #262730;
        border-left: 6px solid #5C95A6;
        border-radius: 8px;
        padding: 15px 20px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.4);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important; 
        color: #FFFFFF !important;
        white-space: normal !important;
        line-height: 1.3 !important;
        overflow-wrap: break-word !important;
    }
    [data-testid="stMetricValue"] > div, 
    [data-testid="stMetricValue"] span,
    [data-testid="stMetricValue"] label {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #B4B4B4 !important;
        font-weight: bold;
    }
    h2, h3 { color: #5C95A6 !important; font-family: 'Arial', sans-serif; }
    hr { border-color: #333333 !important; }

    .brand-banner {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.5rem; 
        padding: 1.5rem 2rem;
        margin: 0 0 1.25rem 0;
        border-radius: 28px;
        border: 1px solid rgba(92,149,166,0.25);
        background: linear-gradient(90deg, rgba(18,26,35,0.98), rgba(11,18,23,0.94));
        box-sizing: border-box;
        min-height: 140px;
    }
    .brand-left {
        display: flex;
        align-items: baseline;
        white-space: nowrap;
    }
    .brand-south,
    .brand-genetics,
    .brand-country {
        display: inline-block;
        white-space: nowrap;
        line-height: 1;
    }
    .brand-south {
        color: #C9CED0;
        font-size: clamp(3rem, 6.8vw, 8.3rem);
        font-weight: 700;
        letter-spacing: -0.08em;
        font-family: 'Arial', sans-serif;
    }
    .brand-genetics {
        color: #87B4C2; 
        font-size: clamp(3rem, 6.8vw, 8.3rem);
        font-weight: 700;
        letter-spacing: -0.08em;
        font-family: 'Arial', sans-serif;
    }
    .brand-right {
        display: flex;
        align-items: baseline;
    }
    .brand-country {
        color: rgba(135, 180, 194, 0.96); 
        font-size: clamp(3rem, 6.8vw, 8.3rem);
        font-family: 'Georgia', 'Times New Roman', serif;
        font-style: italic;
        font-weight: 400;
        letter-spacing: -0.04em;
    }
    @media (max-width: 900px) {
        .brand-banner {
            flex-wrap: wrap;
            padding: 1rem;
            gap: 0.5rem;
            min-height: auto;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN A DATOS, MONEDA Y MAPAS
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    cred_dict = json.loads(st.secrets["google_credentials"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1Zr3YUCUXFwZIRRSGIBnnW60dji1pcnda1VHwZ6HXcYQ/edit?usp=sharing"
    doc = client.open_by_url(sheet_url)
    
    # --- DATOS MEDICOS ---
    datos_medicos = doc.worksheet('MEDICOS').get_all_values()
    idx_med = next(i for i, row in enumerate(datos_medicos) if 'NOMBRE' in str(row))
    df_medicos = pd.DataFrame(datos_medicos[idx_med+1:], columns=datos_medicos[idx_med])
    
    df_medicos.columns = df_medicos.columns.astype(str).str.strip()
    df_medicos = df_medicos[df_medicos['NOMBRE'].astype(str).str.strip() != ""]
    
    mapa_estados = {
        'Guadalajara': 'Jalisco', 'Chihuahua': 'Chihuahua', 'Cd. Juárez': 'Chihuahua',
        'CDMX Norte': 'Ciudad de México', 'CDMX Sur': 'Ciudad de México',
        'CDMX Centro': 'Ciudad de México', 'CDMX': 'Ciudad de México',
        'Monterrey': 'Nuevo León', 'Nuevo Leon': 'Nuevo León', 
        'Mérida, México': 'Yucatán', 'Mérida': 'Yucatán',
        'Cancun': 'Quintana Roo', 'Culiacan': 'Sinaloa', 'Mazatlan': 'Sinaloa',
        'Tampico': 'Tamaulipas', 'Los Cabos': 'Baja California Sur',
        'Aguascalientes': 'Aguascalientes', 'Querétaro': 'Querétaro',
        'Veracruz': 'Veracruz', 'Puebla': 'Puebla', 'Leon': 'Guanajuato',
        'Tijuana': 'Baja California', 'Hermosillo': 'Sonora', 'Oaxaca': 'Oaxaca',
        'Morelia': 'Michoacán', 'Toluca': 'México', 'Cuernavaca': 'Morelos'
    }
    
    def obtener_estado(territorio):
        t = str(territorio).strip()
        return mapa_estados.get(t, t)
        
    if 'TERRITORIO' in df_medicos.columns:
        df_medicos['Estado_oficial'] = df_medicos['TERRITORIO'].apply(obtener_estado)
        
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

    # --- DATOS FACTURACIÓN ---
    datos_fact = doc.worksheet('FACTURACION').get_all_values()
    idx_fac = next(i for i, row in enumerate(datos_fact) if 'NOMBRE' in str(row))
    df_fact = pd.DataFrame(datos_fact[idx_fac+1:], columns=datos_fact[idx_fac])
    
    df_fact.columns = df_fact.columns.astype(str).str.strip()
    df_fact = df_fact[df_fact['NOMBRE'].astype(str).str.strip() != ""]
    
    for col in df_fact.columns:
        if 'Monto' in col or 'Inversión' in col or 'INVERSIÓN' in col.upper():
            texto_limpio = df_fact[col].astype(str).str.replace('$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False) 
            df_fact[col] = pd.to_numeric(texto_limpio, errors='coerce').fillna(0)
        elif 'Cantidad' in col:
            df_fact[col] = pd.to_numeric(df_fact[col], errors='coerce').fillna(0)
            
    # --- DATOS VENTAS (SEGUIMIENTO DE PRUEBAS) ---
    try:
        datos_ventas = doc.worksheet('VENTAS').get_all_values()
        idx_ven = next((i for i, row in enumerate(datos_ventas) if 'PACIENTE' in str(row).upper() or 'FOLIO' in str(row).upper()), 0)
        
        headers = datos_ventas[idx_ven]
        new_headers = []
        counts = {}
        for h in headers:
            h = str(h).strip().upper()
            if h in counts:
                counts[h] += 1
                new_headers.append(f"{h}.{counts[h]}")
            else:
                counts[h] = 0
                new_headers.append(h)
                
        df_ventas = pd.DataFrame(datos_ventas[idx_ven+1:], columns=new_headers)
    except Exception as e:
        try:
            df_ventas = pd.read_excel("Puente_Dashboard_Medicos (3).xlsx", sheet_name="VENTAS", header=2)
            df_ventas.columns = df_ventas.columns.str.upper()
        except:
            df_ventas = pd.DataFrame()
            
    return df_medicos, df_fact, df_ventas

# DESCARGA DEL MAPA GEOJSON OFICIAL
@st.cache_data(ttl=3600)
def get_geojson():
    url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return None

try:
    df_medicos, df_fact, df_ventas = load_data()
    mexico_geojson = get_geojson()
except Exception as e:
    st.error(f"Error conectando a la base de datos: {e}")
    st.stop()

# ==========================================
# 3. MENÚ DE NAVEGACIÓN GLOBAL (BARRA LATERAL)
# ==========================================
try:
    st.sidebar.image("LOGO SG (1) (2) (1).png", use_container_width=True)
except:
    st.sidebar.markdown("### SouthGenetics")

# --- DESCRIPCIÓN GLOBAL EN LA BARRA LATERAL ---
st.sidebar.markdown("""
<div style="color: #A3C1CC; font-size: 0.9rem; margin-bottom: 25px; line-height: 1.5; padding: 0 5px;">
    <strong>Sistema Integral de Inteligencia de Negocios.</strong><br>
    Herramienta centralizada para el monitoreo estratégico de desempeño comercial y la trazabilidad operativa de pruebas genéticas.
</div>
""", unsafe_allow_html=True)

st.sidebar.title("Navegación")
modulo_seleccionado = st.sidebar.radio(
    "Seleccione un módulo:",
    ["Desempeño Médico", "Seguimiento de Pruebas"]
)

st.sidebar.markdown("---")

if st.sidebar.button("Actualizar Datos", use_container_width=True, help="Forzar la descarga de datos nuevos desde Google Sheets"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# 4. MÓDULO 1: DESEMPEÑO MÉDICO
# ==========================================
if modulo_seleccionado == "Desempeño Médico":
    
    # --- SISTEMA DE SEGURIDAD Y CONTRASEÑA ---
    if "acceso_modulo_1" not in st.session_state:
        st.session_state["acceso_modulo_1"] = False

    # Si NO está desbloqueado, mostramos la pantalla de login
    if not st.session_state["acceso_modulo_1"]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col_vacia1, col_login, col_vacia2 = st.columns([1, 1, 1])
        
        with col_login:
            st.markdown("""
            <div style="background-color: #262730; padding: 30px; border-radius: 8px; border-top: 6px solid #5C95A6; box-shadow: 2px 2px 8px rgba(0,0,0,0.4); text-align: center;">
                <h3 style="color: #FFFFFF; margin-top: 0;">Acceso Restringido</h3>
                <p style="color: #B4B4B4; font-size: 14px;">Módulo exclusivo para Dirección y Gerencia.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            pwd = st.text_input("Ingrese su contraseña de acceso:", type="password")
            
            if st.button("Desbloquear Dashboard", use_container_width=True):
                # Contraseña de acceso
                if pwd == "South2026": 
                    st.session_state["acceso_modulo_1"] = True
                    st.rerun()
                elif pwd != "":
                    st.error("Contraseña incorrecta. Intente de nuevo.")
                    
    # Si YA está desbloqueado, mostramos todo el dashboard
    else:
        # Botón sutil para cerrar sesión
        col_logout, _ = st.columns([1, 8])
        with col_logout:
            if st.button("Cerrar Sesión"):
                st.session_state["acceso_modulo_1"] = False
                st.rerun()
                
        # Filtro específico de este módulo
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        st.sidebar.title("Filtro Ejecutivo")
        lista_medicos = ["Todos"] + df_medicos['NOMBRE'].unique().tolist()
        medico_seleccionado = st.sidebar.selectbox("Seleccione un Médico", lista_medicos)

        if medico_seleccionado != "Todos":
            df_med_filtrado = df_medicos[df_medicos['NOMBRE'] == medico_seleccionado]
            df_fact_filtrado = df_fact[df_fact['NOMBRE'] == medico_seleccionado]
        else:
            df_med_filtrado = df_medicos
            df_fact_filtrado = df_fact

        # Cálculos globales
        cant_meses = [f'Cantidad {m}' for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']]
        monto_meses = [f'Monto {m}' for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']]

        pruebas_global = df_fact[[c for c in cant_meses if c in df_fact.columns]].sum().sum()
        pruebas_totales = df_fact_filtrado[[c for c in cant_meses if c in df_fact_filtrado.columns]].sum().sum()
        porcentaje_pruebas = (pruebas_totales / pruebas_global) * 100 if pruebas_global > 0 else 0

        # CORRECCIÓN DE VUELTA AL ORIGINAL: Leemos todas las columnas que digan Inversión sin importar si dicen "Total" o no
        inversion_cols_top = [c for c in df_fact.columns if 'Inversión' in c or 'INVERSIÓN' in c.upper()]
        inversion_total_filtrada = df_fact_filtrado[inversion_cols_top].sum().sum() if inversion_cols_top else 0
        
        if medico_seleccionado == "Todos":
            estatus_beneficios = "Múltiples"
        else:
            estatus_beneficios = "Sí" if inversion_total_filtrada > 0 else "No"

        st.markdown("""
        <div class="brand-banner">
          <div class="brand-left">
            <span class="brand-south">South</span><span class="brand-genetics">Genetics</span>
          </div>
          <div class="brand-right">
            <span class="brand-country">México</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<h1 class='titulo-principal'>Inteligencia Comercial y Desempeño</h1>", unsafe_allow_html=True)
        # --- DESCRIPCIÓN DEL MÓDULO 1 ---
        st.markdown("<p class='descripcion-modulo'>Analice el impacto comercial, la cuota de participación por especialidad y el rendimiento detallado de la red médica a nivel nacional.</p>", unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Participación de Pruebas (%)", f"{porcentaje_pruebas:.2f}%")
        with col2:
            st.metric("Total de Pruebas", int(pruebas_totales))
        with col3:
            rep = df_med_filtrado['REPRESENTANTE'].iloc[0] if medico_seleccionado != "Todos" else "Múltiples"
            st.metric("Representante", rep)
        with col4:
            esp = df_med_filtrado['ESPECIALIDAD'].iloc[0] if medico_seleccionado != "Todos" else "Todas"
            st.metric("Especialidad", esp)
        with col5:
            st.metric("Beneficios Activos", estatus_beneficios)

        st.markdown("<br>", unsafe_allow_html=True)

        # Sistema de Pestañas
        tab1, tab2, tab3 = st.tabs(["Visión General", "Análisis de Pruebas", "Ranking y Beneficios"])

        # --- PESTAÑA 1: VISIÓN GENERAL ---
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            colA, colB = st.columns([2, 1])
            
            with colA:
                st.subheader("Evolución Global de Pruebas")
                ventas_por_mes = [df_fact_filtrado[col].sum() if col in df_fact_filtrado.columns else 0 for col in cant_meses]
                meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                df_linea = pd.DataFrame({'Mes': meses_nombres, 'Pruebas': ventas_por_mes})
                fig_line = px.line(df_linea, x='Mes', y='Pruebas', template="plotly_dark", markers=True, line_shape="spline")
                fig_line.update_traces(line_color='#5C95A6', line_width=4, marker=dict(size=8, color='#87A98A'))
                st.plotly_chart(fig_line, use_container_width=True)

            with colB:
                st.subheader("Cobertura Territorial")
                if not df_med_filtrado.empty and mexico_geojson:
                    try:
                        todos_los_estados = [f['properties']['name'] for f in mexico_geojson['features']]
                        nombre_cdmx = next((n for n in todos_los_estados if 'Distrito' in n or 'Ciudad' in n or 'CDMX' in n), 'Ciudad de México')
                        
                        estado_tmp = df_med_filtrado['Estado_oficial'].copy()
                        estado_tmp = estado_tmp.replace(['Ciudad de México', 'Distrito Federal'], nombre_cdmx)
                        
                        df_agrupado = estado_tmp.value_counts().reset_index()
                        df_agrupado.columns = ['Estado_oficial', 'Doctores']
                        
                        df_base = pd.DataFrame({'Estado_oficial': todos_los_estados, 'Doctores': 0})
                        df_mapa = pd.concat([df_base, df_agrupado]).groupby('Estado_oficial', as_index=False).sum()
                        
                        max_docs = df_mapa['Doctores'].max()
                        if max_docs == 0: max_docs = 1
                        
                        fig_map = px.choropleth(
                            df_mapa, 
                            geojson=mexico_geojson, 
                            locations='Estado_oficial', 
                            featureidkey='properties.name', 
                            color='Doctores',
                            color_continuous_scale=["#1a1a1a", "#5C95A6", "#2EC4B6"],
                            range_color=(0, max_docs),
                            template="plotly_dark"
                        )
                        
                        fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
                        
                        fig_map.update_layout(
                            margin={"r":0,"t":0,"l":0,"b":0},
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            geo=dict(bgcolor='rgba(0,0,0,0)'),
                            coloraxis_showscale=False
                        )
                        fig_map.update_traces(marker_line_width=1, marker_line_color='#444444')
                        
                        st.plotly_chart(fig_map, use_container_width=True)
                    except Exception as e:
                        st.info("Configurando vista territorial...")
                else:
                    st.info("Sin datos para mostrar en el mapa.")
                    
            st.markdown("<hr>", unsafe_allow_html=True)

            st.subheader("Distribución Mensual por Tipo de Prueba")
            meses_completos = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            meses_cortos = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            datos_barras = []
            
            for idx_m, mes in enumerate(meses_completos):
                if f'Producto {mes}' in df_fact_filtrado.columns and f'Cantidad {mes}' in df_fact_filtrado.columns:
                    temp = df_fact_filtrado[[f'Producto {mes}', f'Cantidad {mes}']].copy()
                    temp.columns = ['Prueba', 'Cantidad']
                    temp['Mes'] = meses_cortos[idx_m]
                    datos_barras.append(temp)
                    
            if datos_barras:
                df_barras = pd.concat(datos_barras).dropna()
                df_barras['Prueba'] = df_barras['Prueba'].astype(str).str.strip()
                df_barras = df_barras[(df_barras['Prueba'] != '0') & (df_barras['Prueba'] != '')]
                df_barras = df_barras.groupby(['Mes', 'Prueba'])['Cantidad'].sum().reset_index()
                
                df_pivot = df_barras.pivot(index='Mes', columns='Prueba', values='Cantidad').fillna(0)
                df_pivot = df_pivot.reindex(meses_cortos).fillna(0) 
                df_barras_clean = df_pivot.reset_index().melt(id_vars='Mes', value_name='Cantidad')
                
                colores_marca = ['#2EC4B6', '#FF9F1C', '#5C95A6', '#87A98A', '#E2A973', '#4A7A8A', '#999999', '#A3C1CC']
                fig_line_prod = px.line(df_barras_clean, x='Mes', y='Cantidad', color='Prueba', markers=True, template="plotly_dark", color_discrete_sequence=colores_marca)
                
                fig_line_prod.update_traces(line=dict(width=4), marker=dict(size=8))
                fig_line_prod.update_xaxes(categoryorder='array', categoryarray=meses_cortos)
                fig_line_prod.update_layout(legend_title_text='Tipo de Prueba', xaxis_title="Meses", yaxis_title="Pruebas Vendidas", hovermode="x unified")
                st.plotly_chart(fig_line_prod, use_container_width=True)
            else:
                st.info("No hay datos suficientes para graficar.")

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
                        st.metric(label=f"{row.Producto}", value=f"{row.Porcentaje:.1f}%", delta=f"{int(row.Cantidad)} ventas", delta_color="off")
                        st.progress(int(row.Porcentaje))
                
                st.markdown("<br>", unsafe_allow_html=True)
                colores_marca = ['#5C95A6', '#87A98A', '#A3C1CC', '#999999', '#D1E0E5']
                fig_pie = px.pie(df_productos, values='Cantidad', names='Producto', hole=0.45, template="plotly_dark", color_discrete_sequence=colores_marca)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No hay ventas registradas para generar el desglose.")

        # --- PESTAÑA 3: RANKING Y BENEFICIOS ---
        with tab3:
            st.subheader("Ranking de Médicos (100% Confidencial)")
            
            st.markdown(f"""
            <div style="background-color: #262730; padding: 15px 25px; border-radius: 8px; border-left: 6px solid #FF9F1C; margin-bottom: 25px; box-shadow: 2px 2px 8px rgba(0,0,0,0.4);">
                <p style="margin: 0; color: #B4B4B4; font-size: 0.95rem; font-weight: bold; text-transform: uppercase;">Representación de la tabla actual</p>
                <p style="margin: 5px 0 0 0; color: #FFFFFF; font-size: 1.6rem; font-weight: bold;">
                    {porcentaje_pruebas:.2f}% <span style="font-size: 1.05rem; font-weight: normal; color: #A3C1CC;">del total global de la empresa</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            df_ranking = []
            ingreso_global = df_fact[[c for c in monto_meses if c in df_fact.columns]].sum().sum()
            
            # CORRECCIÓN DE VUELTA AL ORIGINAL: Leemos todas las columnas que digan Inversión
            inversion_cols = [c for c in df_fact.columns if 'Inversión' in c or 'INVERSIÓN' in c.upper()]
            inversion_global = df_fact[inversion_cols].sum().sum() if inversion_cols else 0
            
            for index, row in df_fact_filtrado.iterrows():
                nombre = row['NOMBRE']
                ingresos_medico = sum(pd.to_numeric(row[c], errors='coerce') for c in monto_meses if c in df_fact.columns)
                pruebas_medico = sum(pd.to_numeric(row[c], errors='coerce') for c in cant_meses if c in df_fact.columns)
                
                inversion_medico = 0
                for col in inversion_cols:
                    inversion_medico += pd.to_numeric(row[col], errors='coerce')
                    
                df_ranking.append({
                    'Médico': nombre, 
                    'Pruebas': pruebas_medico, 
                    'Ingreso ($)': ingresos_medico, 
                    'Beneficio ($)': inversion_medico
                })
                
            df_ranking = pd.DataFrame(df_ranking).groupby('Médico').sum().reset_index()
            
            if not df_ranking.empty:
                df_ranking['% de Pruebas'] = (df_ranking['Pruebas'] / pruebas_global) * 100 if pruebas_global > 0 else 0
                df_ranking['% de Ingresos'] = (df_ranking['Ingreso ($)'] / ingreso_global) * 100 if ingreso_global > 0 else 0
                df_ranking['% de Beneficios'] = (df_ranking['Beneficio ($)'] / inversion_global) * 100 if inversion_global > 0 else 0
                
                # Convertir a numérico y luego ordenar de forma segura
                df_ranking['% de Pruebas'] = pd.to_numeric(df_ranking['% de Pruebas'], errors='coerce').fillna(0)
                df_ranking = df_ranking.sort_values('% de Pruebas', ascending=False, kind='stable', na_position='last')
                df_ranking = df_ranking.reset_index(drop=True)
                
                # MOSTRAR RANKING PRINCIPAL (Ocultamos "Pruebas" totales absolutas por confidencialidad)
                st.dataframe(
                    df_ranking,
                    column_config={
                        "Médico": st.column_config.TextColumn("Nombre del Médico", width="medium"),
                        "% de Pruebas": st.column_config.ProgressColumn("Cuota de Pruebas (%)", format="%.2f%%", min_value=0, max_value=100),
                        "% de Ingresos": st.column_config.ProgressColumn("Cuota de Ingresos (%)", format="%.2f%%", min_value=0, max_value=100),
                        "% de Beneficios": st.column_config.ProgressColumn("Cuota de Beneficios (%)", format="%.2f%%", min_value=0, max_value=100)
                    },
                    hide_index=True,
                    column_order=["Médico", "% de Pruebas", "% de Ingresos", "% de Beneficios"],
                    use_container_width=True
                )
                
                # --- NUEVA TABLA: DESGLOSE POR TIPO DE PRUEBA (CON COLUMNA DE CANTIDAD) ---
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("Desglose de Participación por Tipo de Prueba")
                st.markdown("Muestra la cantidad de pruebas vendidas por médico y qué porcentaje representan frente a **todas las ventas nacionales** de ese mismo tipo de prueba.")
                
                lista_global_prod = []
                for mes in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']:
                    if f'Producto {mes}' in df_fact.columns and f'Cantidad {mes}' in df_fact.columns:
                        temp = df_fact[[f'Producto {mes}', f'Cantidad {mes}']].copy()
                        temp.columns = ['Producto', 'Cantidad']
                        lista_global_prod.append(temp)
                
                df_global_prod = pd.concat(lista_global_prod).dropna()
                df_global_prod['Producto'] = df_global_prod['Producto'].astype(str).str.strip()
                df_global_prod = df_global_prod[(df_global_prod['Producto'] != '0') & (df_global_prod['Producto'] != '')]
                totales_globales_producto = df_global_prod.groupby('Producto')['Cantidad'].sum().to_dict()

                lista_todas_ventas = []
                for mes in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']:
                    if f'Producto {mes}' in df_fact_filtrado.columns and f'Cantidad {mes}' in df_fact_filtrado.columns:
                        temp = df_fact_filtrado[['NOMBRE', f'Producto {mes}', f'Cantidad {mes}']].copy()
                        temp.columns = ['Médico', 'Prueba', 'Cantidad']
                        lista_todas_ventas.append(temp)
                
                if lista_todas_ventas:
                    df_todas_ventas = pd.concat(lista_todas_ventas).dropna()
                    df_todas_ventas['Prueba'] = df_todas_ventas['Prueba'].astype(str).str.strip()
                    df_todas_ventas = df_todas_ventas[(df_todas_ventas['Prueba'] != '0') & (df_todas_ventas['Prueba'] != '')]
                    
                    df_doc_prueba = df_todas_ventas.groupby(['Médico', 'Prueba'])['Cantidad'].sum().reset_index()
                    df_doc_prueba = df_doc_prueba[df_doc_prueba['Cantidad'] > 0]
                    
                    df_doc_prueba['Total Global'] = df_doc_prueba['Prueba'].map(totales_globales_producto).fillna(0)
                    df_doc_prueba['Cuota del Producto (%)'] = (df_doc_prueba['Cantidad'] / df_doc_prueba['Total Global']) * 100
                    
                    # Se incluye la columna 'Cantidad' para que el usuario pueda ver el número exacto
                    df_doc_prueba_display = df_doc_prueba[['Médico', 'Prueba', 'Cantidad', 'Cuota del Producto (%)']].sort_values(['Médico', 'Cantidad'], ascending=[True, False])
                    
                    st.dataframe(
                        df_doc_prueba_display,
                        column_config={
                            "Médico": st.column_config.TextColumn("Nombre del Médico", width="medium"),
                            "Prueba": st.column_config.TextColumn("Tipo de Prueba", width="medium"),
                            "Cantidad": st.column_config.NumberColumn("Pruebas Vendidas", format="%d"),
                            "Cuota del Producto (%)": st.column_config.ProgressColumn("Participación Nacional (%)", format="%.2f%%", min_value=0, max_value=100),
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("No hay datos de pruebas detalladas para este médico.")
            else:
                st.info("Sin datos para generar ranking.")

# ==========================================
# 5. MÓDULO 2: SEGUIMIENTO DE PRUEBAS
# ==========================================
elif modulo_seleccionado == "Seguimiento de Pruebas":
    st.markdown("<h1 class='titulo-principal'>Seguimiento y Estatus de Pruebas</h1>", unsafe_allow_html=True)
    st.markdown("<p class='descripcion-modulo'>Consulte la bitácora operativa y monitoree el progreso en tiempo real de las pruebas genéticas solicitadas.</p>", unsafe_allow_html=True)
    
    if df_ventas.empty:
        st.warning("No se encontraron datos en la hoja de VENTAS. Asegúrate de cargar el archivo Excel correctamente o que exista la pestaña en tu Google Sheet.")
    else:
        status_cols = [c for c in df_ventas.columns if 'STATUS' in c]
        fecha_cols = [c for c in df_ventas.columns if 'FECHA' in c]
        
        def get_current_status(row):
            for sc in reversed(status_cols):
                val = str(row.get(sc, '')).strip()
                if val and val.upper() not in ['NAN', 'NONE', 'NAT', '']:
                    return val
            return 'PENDIENTE'
            
        df_ventas['ESTADO_ACTUAL'] = df_ventas.apply(get_current_status, axis=1)
        
        def map_status_category(estado):
            estado = str(estado).upper()
            if any(x in estado for x in ['PROSPECTO', 'SOLICITUD', 'CANCELADA', 'PENDIENTE']):
                return "Pendiente de Toma"
            elif any(x in estado for x in ['RECOLECCION', 'CORTES', 'ENTREGA', 'ENVIO', 'TRANSITO']):
                return "En Tránsito"
            elif any(x in estado for x in ['LABORATORIO', 'ANALISIS', 'RECEPCION']):
                return "En Laboratorio"
            elif any(x in estado for x in ['RESULTADO', 'LISTO', 'COMPLETADO', 'FINALIZADO']):
                return "Resultado Listo"
            return "Pendiente de Toma"
            
        df_ventas['CATEGORIA_ESTADO'] = df_ventas['ESTADO_ACTUAL'].apply(map_status_category)
        
        st.markdown("<br>", unsafe_allow_html=True)
        filtro_estado = st.radio(
            "Filtros rápido:",
            ["Todos", "Pendiente de Toma", "En Tránsito", "En Laboratorio", "Resultado Listo"],
            horizontal=True
        )
        
        if filtro_estado != "Todos":
            df_filtrado = df_ventas[df_ventas['CATEGORIA_ESTADO'] == filtro_estado]
        else:
            df_filtrado = df_ventas
            
        lista_pacientes = df_filtrado['PACIENTE'].dropna().unique().tolist()
        lista_pacientes = [p for p in lista_pacientes if str(p).strip() and str(p).upper() != 'NAN']
        
        col_search, _ = st.columns([2, 1])
        with col_search:
            paciente_seleccionado = st.selectbox("Búsqueda por Paciente", ["Seleccione un paciente..."] + sorted(lista_pacientes))
            
        if paciente_seleccionado != "Seleccione un paciente...":
            datos_paciente = df_ventas[df_ventas['PACIENTE'] == paciente_seleccionado].iloc[-1]
            
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: #FFFFFF; font-size: 1.2rem; margin-bottom: 20px;'>HISTORIAL Y ESTATUS DE LA PRUEBA - PACIENTE: {str(paciente_seleccionado).upper()}</h3>", unsafe_allow_html=True)
            
            col_track, col_details = st.columns([2, 1], gap="large")
            
            with col_track:
                st.markdown("<h4 style='color: #B4B4B4; font-size: 1rem;'>Progreso de la prueba</h4>", unsafe_allow_html=True)
                
                etapas = ["Pendiente de Toma", "En Tránsito", "En Laboratorio", "Resultado Listo"]
                etapas_labels = ["Toma de Muestra", "Envíado / Courier", "En Laboratorio / Análisis", "Resultado Listo"]
                cat_actual = datos_paciente['CATEGORIA_ESTADO']
                idx_actual = etapas.index(cat_actual) if cat_actual in etapas else 0
                
                progress_percentage = (idx_actual / (len(etapas) - 1)) * 100
                
                html_stepper = f"""
<div style="display: flex; justify-content: space-between; align-items: flex-start; position: relative; margin: 40px 0 30px 0;">
<div style="position: absolute; top: 17px; left: 12.5%; width: 75%; height: 4px; background-color: #333333; z-index: 0;"></div>
<div style="position: absolute; top: 17px; left: 12.5%; width: {progress_percentage * 0.75}%; height: 4px; background-color: #5C95A6; z-index: 1; transition: width 0.5s ease;"></div>
"""
                for i, label in enumerate(etapas_labels):
                    if i < idx_actual:
                        icon, color, text_color, sub_text = "✔", "#5C95A6", "#FFFFFF", "Completado"
                    elif i == idx_actual:
                        icon, color, text_color, sub_text = "●", "#FF9F1C", "#FF9F1C", "En Proceso"
                    else:
                        icon, color, text_color, sub_text = "", "#333333", "#888888", "Pendiente"
                        
                    html_stepper += f"""
<div style="z-index: 2; display: flex; flex-direction: column; align-items: center; flex: 1; background: transparent;">
<div style="width: 38px; height: 38px; border-radius: 50%; background-color: #1E1F25; border: 4px solid {color}; display: flex; align-items: center; justify-content: center; color: {color}; font-size: 18px; font-weight: bold;">{icon}</div>
<div style="font-weight: bold; color: {text_color}; font-size: 13px; text-align: center; line-height: 1.2;">{label}</div>
<div style="color: {text_color}; font-size: 11px; text-align: center; opacity: 0.7; margin-top: 4px;">{sub_text}</div>
</div>
"""
                html_stepper += "</div>"
                st.markdown(html_stepper, unsafe_allow_html=True)
                
            with col_details:
                html_detalles = f"""
<div style="background-color: #262730; padding: 20px 25px; border-radius: 8px; border-left: 6px solid #5C95A6; box-shadow: 2px 2px 8px rgba(0,0,0,0.4);">
<h4 style="color: #5C95A6; margin-top: 0; font-family: 'Arial', sans-serif; font-size: 1rem; border-bottom: 1px solid #333; padding-bottom: 10px;">Detalles del Paciente e Institución</h4>
<p style="margin: 10px 0; color: #FFFFFF; font-size: 14px;"><b>Paciente:</b> {datos_paciente.get('PACIENTE', 'N/A')}</p>
<p style="margin: 10px 0; color: #FFFFFF; font-size: 14px;"><b>ID de Prueba:</b> {datos_paciente.get('FOLIO', 'N/A')}</p>
<p style="margin: 10px 0; color: #FFFFFF; font-size: 14px;"><b>Institución:</b> {datos_paciente.get('INSTITUCION', 'N/A')}</p>
<p style="margin: 10px 0; color: #FFFFFF; font-size: 14px;"><b>Médico Tratante:</b> {datos_paciente.get('MEDICO', 'N/A')}</p>
<p style="margin: 10px 0; color: #FFFFFF; font-size: 14px;"><b>Prueba:</b> {datos_paciente.get('PRUEBA', 'N/A')}</p>
<p style="margin: 10px 0; color: #FFFFFF; font-size: 14px;"><b>Representante:</b> {datos_paciente.get('VENDEDOR', 'N/A')}</p>
</div>
"""
                st.markdown(html_detalles, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #B4B4B4; font-size: 1rem; margin-bottom: 15px;'>Historial de Estados y Bitácora</h4>", unsafe_allow_html=True)
            
            historial = []
            for f_col, s_col in zip(fecha_cols, status_cols):
                fecha_val = str(datos_paciente.get(f_col, '')).strip()
                status_val = str(datos_paciente.get(s_col, '')).strip()
                if status_val and status_val.upper() not in ['NAN', 'NONE', 'NAT', '']:
                    if ' ' in fecha_val:
                        fecha_limpia = fecha_val.split()[0]
                        hora_limpia = fecha_val.split()[1][:5]
                    else:
                        fecha_limpia = fecha_val
                        hora_limpia = "-"
                        
                    historial.append({
                        "Fecha": fecha_limpia,
                        "Hora": hora_limpia,
                        "Estado": status_val,
                        "Descripción": "Actualización registrada en sistema",
                        "Nota": "-"
                    })
                    
            if historial:
                df_historial = pd.DataFrame(historial)
                st.dataframe(df_historial, use_container_width=True, hide_index=True)
            else:
                st.info("No hay historial registrado en la bitácora para esta prueba.")
