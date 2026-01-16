# app.py - VERSIÓN CON DASHBOARD COMPLETO
import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

# Importar desde core
from core import ProcesadorArchivos, CalculadoraResultados, formatear_monto, VisualizadorResultados

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="wide")

# CSS
st.markdown("""
<style>
    .st-emotion-cache-1gulkj5 {
        display: none !important;
    }
    
    .st-emotion-cache-1y4p8pa {
        min-width: 0 !important;
    }
    
    /* Mejorar cards de métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    /* Espacio para gráficos */
    .stPlotlyChart {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 10px;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Simulador de Resultados - Dashboard Analítico")

# ==========================================
# ESTADO DE LA APLICACIÓN
# ==========================================

if 'archivos_procesados' not in st.session_state:
    st.session_state.archivos_procesados = {}
if 'periodos_asignados' not in st.session_state:
    st.session_state.periodos_asignados = {}

# ==========================================
# FUNCIONES AUXILIARES (MANTENIENDO LAS ANTERIORES)
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
# PESTAÑA 1: CARGA (MANTENIENDO LO ANTERIOR)
# ==========================================

def pestana_carga():
    """Pestaña de carga (mantener versión anterior)."""
    # ... (MANTENER TODO EL CÓDIGO ANTERIOR DE CARGA)
    # (Se mantiene igual que la versión que te gustó)
    pass

# ==========================================
# PESTAÑA 2: DASHBOARD ANALÍTICO COMPLETO
# ==========================================

def pestana_dashboard():
    """Pestaña con dashboard analítico completo."""
    st.header("📈 Dashboard Analítico")
    
    if not st.session_state.archivos_procesados:
        st.info("📭 **No hay archivos procesados**")
        return
    
    # ===== FILTROS INTERACTIVOS =====
    st.markdown("---")
    st.markdown("### 🔍 **Filtros de Análisis**")
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        # Filtro por tipo de análisis
        tipo_analisis = st.selectbox(
            "Tipo de Análisis",
            ["Completo", "Solo Ventas", "Solo Compras", "Comparativo"],
            help="Selecciona el enfoque del análisis"
        )
    
    with col_filtro2:
        # Filtro por rango de períodos
        mostrar_todos = st.checkbox("Mostrar todos los períodos", value=True)
    
    with col_filtro3:
        # Filtro por tipo de gráfico
        graficos_disponibles = ["Barras", "Líneas", "Torta", "Heatmap", "Todos"]
        grafico_seleccionado = st.multiselect(
            "Gráficos a mostrar",
            graficos_disponibles,
            default=["Barras", "Líneas"]
        )
    
    # ===== PROCESAR DATOS PARA ANÁLISIS =====
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
    
    # Aplicar filtros
    if tipo_analisis == "Solo Ventas" and not df_resultados.empty:
        df_resultados['Compras'] = 0
        df_resultados['Resultado'] = df_resultados['Ventas']
    elif tipo_analisis == "Solo Compras" and not df_resultados.empty:
        df_resultados['Ventas'] = 0
        df_resultados['Resultado'] = -df_resultados['Compras']
    
    # ===== PANEL DE MÉTRICAS PRINCIPALES =====
    st.markdown("---")
    st.markdown("### 🎯 **Métricas Principales**")
    
    # Fila 1: Métricas financieras
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Ventas Totales", 
            formatear_monto(totales['ventas_totales']),
            f"{totales['documentos_ventas']} docs"
        )
    
    with col2:
        st.metric(
            "Compras Totales", 
            formatear_monto(totales['compras_totales']),
            f"{totales['documentos_compras']} docs"
        )
    
    with col3:
        resultado_color = "normal" if totales['resultado_total'] >= 0 else "inverse"
        st.metric(
            "Resultado Neto", 
            formatear_monto(totales['resultado_total']),
            delta_color=resultado_color
        )
    
    with col4:
        # Calcular margen total
        margen_total = (totales['resultado_total'] / totales['ventas_totales'] * 100) if totales['ventas_totales'] != 0 else 0
        margen_color = "normal" if margen_total >= 0 else "inverse"
        st.metric(
            "Margen Total", 
            f"{margen_total:+.1f}%",
            delta_color=margen_color
        )
    
    with col5:
        st.metric(
            "Total Documentos", 
            totales['documentos_totales'],
            f"V:{totales['documentos_ventas']} C:{totales['documentos_compras']}"
        )
    
    # Fila 2: Métricas adicionales
    col6, col7, col8, col9, col10 = st.columns(5)
    
    with col6:
        st.metric("Promedio Venta", formatear_monto(estadisticas['promedio_venta']))
    
    with col7:
        st.metric("Promedio Compra", formatear_monto(estadisticas['promedio_compra']))
    
    with col8:
        st.metric("NC Ventas", estadisticas['notas_credito_ventas'])
    
    with col9:
        st.metric("NC Compras", estadisticas['notas_credito_compras'])
    
    with col10:
        eficiencia = (totales['documentos_ventas'] / totales['documentos_totales'] * 100) if totales['documentos_totales'] != 0 else 0
        st.metric("Eficiencia Docs", f"{eficiencia:.1f}%")
    
    # ===== VISUALIZACIONES INTERACTIVAS =====
    st.markdown("---")
    st.markdown("### 📊 **Visualizaciones Interactivas**")
    
    # Crear visualizaciones
    visualizaciones = VisualizadorResultados.crear_dashboard_completo(df_resultados, totales, estadisticas)
    
    # Mostrar gráficos según selección
    if "Barras" in grafico_seleccionado or "Todos" in grafico_seleccionado:
        if visualizaciones.get('barras_apiladas'):
            st.plotly_chart(visualizaciones['barras_apiladas'], use_container_width=True)
    
    # Dos columnas para gráficos medianos
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        if "Líneas" in grafico_seleccionado or "Todos" in grafico_seleccionado:
            if visualizaciones.get('linea_resultado'):
                st.plotly_chart(visualizaciones['linea_resultado'], use_container_width=True)
        
        if "Barras" in grafico_seleccionado or "Todos" in grafico_seleccionado:
            if visualizaciones.get('barras_margen'):
                st.plotly_chart(visualizaciones['barras_margen'], use_container_width=True)
    
    with col_der:
        if "Torta" in grafico_seleccionado or "Todos" in grafico_seleccionado:
            if visualizaciones.get('torta_totales'):
                st.plotly_chart(visualizaciones['torta_totales'], use_container_width=True)
        
        if visualizaciones.get('barras_documentos'):
            st.plotly_chart(visualizaciones['barras_documentos'], use_container_width=True)
    
    # Gráficos de ancho completo
    if visualizaciones.get('evolucion_mensual'):
        st.plotly_chart(visualizaciones['evolucion_mensual'], use_container_width=True)
    
    if "Heatmap" in grafico_seleccionado and visualizaciones.get('heatmap_correlacion'):
        st.plotly_chart(visualizaciones['heatmap_correlacion'], use_container_width=True)
    
    # ===== TABLAS DETALLADAS =====
    st.markdown("---")
    st.markdown("### 📋 **Tablas de Datos**")
    
    tab1, tab2, tab3 = st.tabs(["📅 Por Período", "📊 Estadísticas", "📁 Archivos"])
    
    with tab1:
        if not df_resultados.empty:
            # Formatear tabla con estilo
            styled_df = df_resultados.style.format({
                'Ventas': lambda x: formatear_monto(x),
                'Compras': lambda x: formatear_monto(x),
                'Resultado': lambda x: formatear_monto(x),
                'Margen %': '{:+.1f}%'
            })
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Opciones de exportación
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar tabla como CSV",
                data=csv,
                file_name="resultados_por_periodo.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with tab2:
        # Crear DataFrame de estadísticas
        stats_data = {
            'Métrica': [
                'Ventas Totales', 'Compras Totales', 'Resultado Neto',
                'Margen Total', 'Documentos Totales', 'Promedio Venta',
                'Promedio Compra', 'NC Ventas', 'NC Compras'
            ],
            'Valor': [
                formatear_monto(totales['ventas_totales']),
                formatear_monto(totales['compras_totales']),
                formatear_monto(totales['resultado_total']),
                f"{margen_total:+.1f}%",
                totales['documentos_totales'],
                formatear_monto(estadisticas['promedio_venta']),
                formatear_monto(estadisticas['promedio_compra']),
                estadisticas['notas_credito_ventas'],
                estadisticas['notas_credito_compras']
            ]
        }
        
        df_stats = pd.DataFrame(stats_data)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
    
    with tab3:
        # Lista de archivos procesados
        archivos_data = []
        for nombre, info in st.session_state.archivos_procesados.items():
            periodo = st.session_state.periodos_asignados.get(nombre, "Sin asignar")
            archivos_data.append({
                'Archivo': formatear_nombre_archivo(nombre),
                'Tipo': info['tipo_archivo'].capitalize(),
                'Período': periodo,
                'Documentos': info['documentos_count'],
                'Monto': formatear_monto(info['total_monto']),
                'Fecha Min': info['fecha_minima'].strftime('%d/%m/%Y'),
                'Fecha Max': info['fecha_maxima'].strftime('%d/%m/%Y')
            })
        
        if archivos_data:
            df_archivos = pd.DataFrame(archivos_data)
            st.dataframe(df_archivos, use_container_width=True)
        else:
            st.info("No hay archivos procesados")
    
    # ===== ANÁLISIS AVANZADO =====
    st.markdown("---")
    with st.expander("🔬 **Análisis Avanzado**", expanded=False):
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            st.markdown("##### 📈 **Tendencias**")
            
            if len(df_resultados) > 1:
                # Calcular tendencia de ventas
                ventas_trend = df_resultados['Ventas'].pct_change().mean() * 100
                compras_trend = df_resultados['Compras'].pct_change().mean() * 100
                resultado_trend = df_resultados['Resultado'].pct_change().mean() * 100
                
                st.metric("Tendencia Ventas", f"{ventas_trend:+.1f}%")
                st.metric("Tendencia Compras", f"{compras_trend:+.1f}%")
                st.metric("Tendencia Resultado", f"{resultado_trend:+.1f}%")
            else:
                st.info("Se necesitan al menos 2 períodos para análisis de tendencias")
        
        with col_adv2:
            st.markdown("##### 🎯 **KPIs Clave**")
            
            # Calcular KPIs
            if totales['ventas_totales'] > 0:
                rotacion = totales['documentos_totales'] / len(st.session_state.archivos_procesados)
                densidad = totales['resultado_total'] / totales['documentos_totales'] if totales['documentos_totales'] > 0 else 0
                eficiencia_docs = (totales['documentos_ventas'] / totales['documentos_totales'] * 100) if totales['documentos_totales'] > 0 else 0
                
                st.metric("Rotación Docs/Archivo", f"{rotacion:.1f}")
                st.metric("Densidad por Doc", formatear_monto(densidad))
                st.metric("Eficiencia Docs", f"{eficiencia_docs:.1f}%")

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN (MANTENER)
# ==========================================

def pestana_configuracion():
    """Pestaña de configuración."""
    st.header("⚙️ Configuración")
    
    if st.button("🔄 **Limpiar Todo y Reiniciar**", 
                type="secondary",
                use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.session_state.archivos_procesados = {}
        st.session_state.periodos_asignados = {}
        
        st.success("✅ Sistema reiniciado correctamente")
        st.rerun()

# ==========================================
# APLICACIÓN PRINCIPAL CON 3 PESTAÑAS
# ==========================================

tab1, tab2, tab3 = st.tabs(["📥 Carga", "📈 Dashboard", "⚙️ Config"])

with tab1:
    # Aquí iría la función pestana_carga() que ya tienes
    # Por ahora usamos un placeholder
    st.header("📥 Carga de Archivos")
    st.info("Esta funcionalidad está implementada en la versión anterior.")
    st.write("Para mantener este código manejable, se mantiene separado.")

with tab2:
    pestana_dashboard()

with tab3:
    pestana_configuracion()

# Pie
st.caption(f"Dashboard Analítico | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
