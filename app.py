# app.py - VERSIÓN COMPLETA CON TU CARGA + DASHBOARD
import streamlit as st
from datetime import datetime
import pandas as pd

# Importar desde core
from core import ProcesadorArchivos, CalculadoraResultados, formatear_monto, VisualizadorResultados

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="wide")

# CSS para ocultar lista automática de archivos
st.markdown("""
<style>
    .st-emotion-cache-1gulkj5 {
        display: none !important;
    }
    
    /* Mejorar visualización */
    .st-emotion-cache-1y4p8pa {
        min-width: 0 !important;
    }
    
    /* Espacio para gráficos */
    .stPlotlyChart {
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Simulador de Resultados - Dashboard")

# ==========================================
# ESTADO DE LA APLICACIÓN
# ==========================================

if 'archivos_procesados' not in st.session_state:
    st.session_state.archivos_procesados = {}
if 'periodos_asignados' not in st.session_state:
    st.session_state.periodos_asignados = {}

# ==========================================
# FUNCIONES AUXILIARES (TU VERSIÓN)
# ==========================================

def formatear_nombre_archivo(nombre_completo):
    """Formatea nombre de archivo para mostrar lo importante."""
    if '.' in nombre_completo:
        nombre = nombre_completo[:nombre_completo.rfind('.')]
    else:
        nombre = nombre_completo
    
    prefijos = ['VENTAS_', 'COMPRAS_', 'VENTA_', 'COMPRA_', 'ARCHIVO_']
    for prefijo in prefijos:
        if nombre.upper().startswith(prefijo):
            nombre = nombre[len(prefijo):]
    
    if len(nombre) > 30:
        return f"{nombre[:15]}...{nombre[-10:]}"
    
    return nombre

# ==========================================
# PESTAÑA 1: CARGA (TU VERSIÓN COMPLETA)
# ==========================================

def pestana_carga():
    """TU VERSIÓN DE CARGA - Separada ventas/compras."""
    st.header("📥 Carga de Archivos")
    
    # ===== CONTADORES SUPERIORES =====
    if st.session_state.archivos_procesados:
        total = len(st.session_state.archivos_procesados)
        ventas = sum(1 for v in st.session_state.archivos_procesados.values() 
                    if v['tipo_archivo'] == 'venta')
        compras = total - ventas
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 Total", total)
        with col2:
            st.metric("🟢 Ventas", ventas)
        with col3:
            st.metric("🔵 Compras", compras)
    
    st.markdown("---")
    
    # ===== VENTAS =====
    st.markdown("### 🟢 **ARCHIVOS DE VENTAS**")
    
    # Uploader ventas
    ventas_files = st.file_uploader(
        "Selecciona archivos de VENTAS",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="ventas_upload",
        help="Archivos CSV o Excel con documentos de ventas"
    )
    
    # Procesar ventas
    ventas_pendientes = []
    if ventas_files:
        for archivo in ventas_files:
            if archivo.name in st.session_state.archivos_procesados:
                continue
            
            try:
                info = ProcesadorArchivos.procesar_archivo(archivo, "venta")
                ventas_pendientes.append((archivo.name, info, 'venta'))
                st.session_state[f"temp_venta_{archivo.name}"] = info
            except Exception as e:
                st.error(f"❌ Error en {archivo.name}: {str(e)[:50]}")
    
    # Mostrar ventas pendientes
    if ventas_pendientes:
        st.markdown("**📋 Ventas pendientes de asignación:**")
        
        for nombre_archivo, info, tipo in ventas_pendientes:
            with st.container():
                col_nombre, col_info, col_año, col_mes, col_accion = st.columns([3, 2, 1.5, 1.5, 1])
                
                with col_nombre:
                    nombre_display = formatear_nombre_archivo(nombre_archivo)
                    st.markdown(f"**{nombre_display}**")
                    st.caption(f"{info['documentos_count']} docs")
                
                with col_info:
                    fecha_min = info['fecha_minima'].strftime('%d/%m')
                    fecha_max = info['fecha_maxima'].strftime('%d/%m')
                    st.caption(f"{fecha_min}-{fecha_max}")
                    st.caption(formatear_monto(info['total_monto']))
                
                with col_año:
                    año_pred = info['año_predominante'] or datetime.now().year
                    año = st.selectbox(
                        "Año",
                        range(2020, datetime.now().year + 2),
                        index=año_pred - 2020,
                        key=f"año_venta_{nombre_archivo}",
                        label_visibility="collapsed"
                    )
                
                with col_mes:
                    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    mes_pred = info['mes_predominante'] or 1
                    mes_idx = st.selectbox(
                        "Mes",
                        meses,
                        index=mes_pred - 1,
                        key=f"mes_venta_{nombre_archivo}",
                        label_visibility="collapsed"
                    )
                    mes_num = meses.index(mes_idx) + 1
                
                with col_accion:
                    periodo = f"{año}-{mes_num:02d}"
                    
                    if st.button("✅", 
                               key=f"btn_venta_{nombre_archivo}",
                               help=f"Asignar {periodo}",
                               type="primary"):
                        
                        st.session_state.archivos_procesados[nombre_archivo] = info
                        st.session_state.periodos_asignados[nombre_archivo] = periodo
                        
                        if f"temp_venta_{nombre_archivo}" in st.session_state:
                            del st.session_state[f"temp_venta_{nombre_archivo}"]
                        
                        st.rerun()
                    
                    st.caption(f"`{periodo}`")
    
    # ===== COMPRAS =====
    st.markdown("---")
    st.markdown("### 🔵 **ARCHIVOS DE COMPRAS**")
    
    # Uploader compras
    compras_files = st.file_uploader(
        "Selecciona archivos de COMPRAS",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="compras_upload",
        help="Archivos CSV o Excel con documentos de compras"
    )
    
    # Procesar compras
    compras_pendientes = []
    if compras_files:
        for archivo in compras_files:
            if archivo.name in st.session_state.archivos_procesados:
                continue
            
            try:
                info = ProcesadorArchivos.procesar_archivo(archivo, "compra")
                compras_pendientes.append((archivo.name, info, 'compra'))
                st.session_state[f"temp_compra_{archivo.name}"] = info
            except Exception as e:
                st.error(f"❌ Error en {archivo.name}: {str(e)[:50]}")
    
    # Mostrar compras pendientes
    if compras_pendientes:
        st.markdown("**📋 Compras pendientes de asignación:**")
        
        for nombre_archivo, info, tipo in compras_pendientes:
            with st.container():
                col_nombre, col_info, col_año, col_mes, col_accion = st.columns([3, 2, 1.5, 1.5, 1])
                
                with col_nombre:
                    nombre_display = formatear_nombre_archivo(nombre_archivo)
                    st.markdown(f"**{nombre_display}**")
                    st.caption(f"{info['documentos_count']} docs")
                
                with col_info:
                    fecha_min = info['fecha_minima'].strftime('%d/%m')
                    fecha_max = info['fecha_maxima'].strftime('%d/%m')
                    st.caption(f"{fecha_min}-{fecha_max}")
                    st.caption(formatear_monto(info['total_monto']))
                
                with col_año:
                    año_pred = info['año_predominante'] or datetime.now().year
                    año = st.selectbox(
                        "Año",
                        range(2020, datetime.now().year + 2),
                        index=año_pred - 2020,
                        key=f"año_compra_{nombre_archivo}",
                        label_visibility="collapsed"
                    )
                
                with col_mes:
                    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    mes_pred = info['mes_predominante'] or 1
                    mes_idx = st.selectbox(
                        "Mes",
                        meses,
                        index=mes_pred - 1,
                        key=f"mes_compra_{nombre_archivo}",
                        label_visibility="collapsed"
                    )
                    mes_num = meses.index(mes_idx) + 1
                
                with col_accion:
                    periodo = f"{año}-{mes_num:02d}"
                    
                    if st.button("✅", 
                               key=f"btn_compra_{nombre_archivo}",
                               help=f"Asignar {periodo}",
                               type="primary"):
                        
                        st.session_state.archivos_procesados[nombre_archivo] = info
                        st.session_state.periodos_asignados[nombre_archivo] = periodo
                        
                        if f"temp_compra_{nombre_archivo}" in st.session_state:
                            del st.session_state[f"temp_compra_{nombre_archivo}"]
                        
                        st.rerun()
                    
                    st.caption(f"`{periodo}`")
    
    # ===== RESUMEN FINAL =====
    st.markdown("---")
    
    if st.session_state.archivos_procesados:
        total = len(st.session_state.archivos_procesados)
        ventas_count = sum(1 for v in st.session_state.archivos_procesados.values() 
                          if v['tipo_archivo'] == 'venta')
        compras_count = total - ventas_count
        
        st.success(f"""
        ✅ **{total} archivo(s) asignado(s):** 
        🟢 {ventas_count} ventas | 🔵 {compras_count} compras
        
        **Siguiente paso:** Ve a la pestaña **'📈 Dashboard'** para ver gráficos.
        """)
    
    pendientes_total = len(ventas_pendientes) + len(compras_pendientes)
    if pendientes_total > 0:
        st.warning(f"⚠️ **{pendientes_total} archivo(s) pendiente(s) de asignación**")

# ==========================================
# PESTAÑA 2: DASHBOARD CON GRÁFICOS
# ==========================================

def pestana_dashboard():
    """Pestaña con dashboard y gráficos interactivos."""
    st.header("📈 Dashboard Analítico")
    
    if not st.session_state.archivos_procesados:
        st.info("📭 **No hay archivos cargados. Ve a la pestaña 'Carga' primero.**")
        return
    
    # ===== FILTROS SIMPLES =====
    st.markdown("---")
    st.markdown("### 🔍 **Opciones de Visualización**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mostrar_tabla = st.checkbox("Mostrar tabla de datos", value=True)
    
    with col2:
        tipo_grafico = st.selectbox(
            "Tipo de análisis",
            ["Completo", "Solo Ventas", "Solo Compras"],
            help="Selecciona el enfoque del análisis"
        )
    
    # ===== PROCESAR DATOS =====
    todos_documentos = []
    for nombre, info in st.session_state.archivos_procesados.items():
        for doc in info['documentos']:
            periodo = st.session_state.periodos_asignados.get(nombre, "Sin período")
            doc['periodo_asignado'] = periodo
            todos_documentos.append(doc)
    
    # Calcular resultados
    resumen_periodos = CalculadoraResultados.agrupar_por_periodo(
        todos_documentos, 
        st.session_state.periodos_asignados
    )
    totales = CalculadoraResultados.calcular_totales(resumen_periodos)
    datos_tabla = CalculadoraResultados.generar_dataframe_resultados(resumen_periodos)
    estadisticas = CalculadoraResultados.calcular_estadisticas(todos_documentos)
    
    df_resultados = pd.DataFrame(datos_tabla)
    
    # Aplicar filtro de tipo
    if tipo_grafico == "Solo Ventas" and not df_resultados.empty:
        df_resultados['Compras'] = 0
        df_resultados['Resultado'] = df_resultados['Ventas']
    elif tipo_grafico == "Solo Compras" and not df_resultados.empty:
        df_resultados['Ventas'] = 0
        df_resultados['Resultado'] = -df_resultados['Compras']
    
    # ===== MÉTRICAS PRINCIPALES =====
    st.markdown("### 🎯 **Métricas Principales**")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Ventas Totales", formatear_monto(totales['ventas_totales']))
    
    with col2:
        st.metric("Compras Totales", formatear_monto(totales['compras_totales']))
    
    with col3:
        resultado_color = "normal" if totales['resultado_total'] >= 0 else "inverse"
        st.metric("Resultado Neto", formatear_monto(totales['resultado_total']),
                 delta_color=resultado_color)
    
    with col4:
        margen_total = (totales['resultado_total'] / totales['ventas_totales'] * 100) if totales['ventas_totales'] != 0 else 0
        margen_color = "normal" if margen_total >= 0 else "inverse"
        st.metric("Margen Total", f"{margen_total:+.1f}%",
                 delta_color=margen_color)
    
    with col5:
        st.metric("Total Documentos", totales['documentos_totales'])
    
    # ===== GRÁFICOS INTERACTIVOS =====
    st.markdown("---")
    st.markdown("### 📊 **Gráficos Interactivos**")
    
    # Crear visualizaciones
    visualizaciones = VisualizadorResultados.crear_dashboard_completo(
        df_resultados, totales, estadisticas
    )
    
    # Gráfico principal
    if visualizaciones.get('barras_apiladas'):
        st.plotly_chart(visualizaciones['barras_apiladas'], use_container_width=True)
    
    # Dos columnas para gráficos pequeños
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        if visualizaciones.get('linea_resultado'):
            st.plotly_chart(visualizaciones['linea_resultado'], use_container_width=True)
        
        if visualizaciones.get('barras_margen') and not df_resultados.empty:
            st.plotly_chart(visualizaciones['barras_margen'], use_container_width=True)
    
    with col_der:
        if visualizaciones.get('torta_totales'):
            st.plotly_chart(visualizaciones['torta_totales'], use_container_width=True)
        
        if visualizaciones.get('barras_documentos'):
            st.plotly_chart(visualizaciones['barras_documentos'], use_container_width=True)
    
    # ===== TABLA DE DATOS =====
    if mostrar_tabla:
        st.markdown("---")
        st.markdown("### 📋 **Tabla de Resultados por Período**")
        
        if not df_resultados.empty:
            # Formatear tabla
            df_display = df_resultados.copy()
            
            # Formatear montos
            for col in ['Ventas', 'Compras', 'Resultado']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: formatear_monto(x))
            
            # Formatear margen
            if 'Margen %' in df_display.columns:
                df_display['Margen %'] = df_display['Margen %'].apply(lambda x: f"{x:+.1f}%")
            
            st.dataframe(df_display, use_container_width=True)
            
            # Botón para descargar
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar como CSV",
                data=csv,
                file_name="resultados.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # ===== ESTADÍSTICAS ADICIONALES =====
    with st.expander("📊 **Estadísticas Detalladas**"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📈 Promedios")
            st.metric("Promedio Venta", formatear_monto(estadisticas['promedio_venta']))
            st.metric("Promedio Compra", formatear_monto(estadisticas['promedio_compra']))
            
            st.markdown("##### 📝 Notas de Crédito")
            st.metric("Ventas", estadisticas['notas_credito_ventas'])
            st.metric("Compras", estadisticas['notas_credito_compras'])
        
        with col2:
            st.markdown("##### 📊 Distribución")
            dist_data = pd.DataFrame({
                'Tipo': ['Ventas', 'Compras'],
                'Documentos': [estadisticas['total_ventas_count'], estadisticas['total_compras_count']],
                'Monto Total': [totales['ventas_totales'], totales['compras_totales']]
            })
            st.dataframe(dist_data, use_container_width=True, hide_index=True)
    
    # ===== LISTA DE ARCHIVOS =====
    with st.expander("📁 **Archivos Cargados**"):
        archivos_data = []
        for nombre, info in st.session_state.archivos_procesados.items():
            periodo = st.session_state.periodos_asignados.get(nombre, "Sin asignar")
            archivos_data.append({
                'Archivo': formatear_nombre_archivo(nombre),
                'Tipo': info['tipo_archivo'].capitalize(),
                'Período': periodo,
                'Documentos': info['documentos_count'],
                'Monto': formatear_monto(info['total_monto'])
            })
        
        if archivos_data:
            df_archivos = pd.DataFrame(archivos_data)
            st.dataframe(df_archivos, use_container_width=True)

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN
# ==========================================

def pestana_configuracion():
    """Pestaña de configuración."""
    st.header("⚙️ Configuración")
    
    st.markdown("### 📊 **Estado Actual**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Archivos Cargados", len(st.session_state.archivos_procesados))
    
    with col2:
        if st.session_state.archivos_procesados:
            total_docs = sum(info['documentos_count'] for info in st.session_state.archivos_procesados.values())
            st.metric("Documentos", total_docs)
    
    st.markdown("---")
    st.markdown("### 🚨 **Acciones del Sistema**")
    
    if st.button("🔄 **Limpiar Todo y Reiniciar**", 
                type="secondary",
                use_container_width=True):
        # Limpiar TODO
        for key in list(st.session_state.keys()):
            if key.startswith('temp_') or key in ['archivos_procesados', 'periodos_asignados']:
                del st.session_state[key]
        
        # Inicializar estados vacíos
        st.session_state.archivos_procesados = {}
        st.session_state.periodos_asignados = {}
        
        st.success("✅ Sistema reiniciado correctamente")
        st.rerun()

# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================

# Crear tabs
tab1, tab2, tab3 = st.tabs(["📥 Carga", "📈 Dashboard", "⚙️ Config"])

with tab1:
    pestana_carga()

with tab2:
    pestana_dashboard()

with tab3:
    pestana_configuracion()

# Pie
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
