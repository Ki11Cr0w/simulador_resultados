# app.py - VERSIÓN CON SEPARACIÓN Y NOMBRES COMPLETOS
import streamlit as st
from datetime import datetime
import pandas as pd

# Importar desde core
from core import ProcesadorArchivos, CalculadoraResultados, formatear_monto

# ==========================================
# CONFIGURACIÓN - CSS MÁS SELECTIVO
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="wide")

# CSS solo para ocultar la visualización automática
st.markdown("""
<style>
    /* Solo ocultar la lista automática de archivos */
    .st-emotion-cache-1gulkj5 {
        display: none !important;
    }
    
    /* Asegurar que los nombres no se corten */
    .st-emotion-cache-1y4p8pa {
        min-width: 0 !important;
    }
    
    /* Compactar selectboxes */
    .stSelectbox {
        min-height: 40px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Simulador de Resultados")

# ==========================================
# ESTADO DE LA APLICACIÓN
# ==========================================

if 'archivos_procesados' not in st.session_state:
    st.session_state.archivos_procesados = {}
if 'periodos_asignados' not in st.session_state:
    st.session_state.periodos_asignados = {}

# ==========================================
# FUNCIONES AUXILIARES MEJORADAS
# ==========================================

def formatear_nombre_archivo(nombre_completo):
    """Formatea nombre de archivo para mostrar lo importante."""
    # Eliminar extensión
    if '.' in nombre_completo:
        nombre = nombre_completo[:nombre_completo.rfind('.')]
    else:
        nombre = nombre_completo
    
    # Eliminar prefijos comunes
    prefijos = ['VENTAS_', 'COMPRAS_', 'VENTA_', 'COMPRA_', 'ARCHIVO_']
    for prefijo in prefijos:
        if nombre.upper().startswith(prefijo):
            nombre = nombre[len(prefijo):]
    
    # Si es muy largo, mostrar principio y final
    if len(nombre) > 30:
        return f"{nombre[:15]}...{nombre[-10:]}"
    
    return nombre

# ==========================================
# PESTAÑA 1: CARGA SEPARADA Y CLARA
# ==========================================

def pestana_carga():
    """Pestaña con ventas y compras claramente separados."""
    st.header("📥 Carga de Archivos")
    
    # ===== SECCIÓN VENTAS =====
    st.markdown("---")
    st.markdown("### 🟢 **ARCHIVOS DE VENTAS**")
    
    # Uploader ventas
    ventas_files = st.file_uploader(
        "Selecciona archivos de VENTAS",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="ventas_upload",
        help="Archivos CSV o Excel con documentos de ventas"
    )
    
    # Procesar y mostrar ventas pendientes
    ventas_pendientes = []
    if ventas_files:
        for archivo in ventas_files:
            if archivo.name not in st.session_state.archivos_procesados:
                try:
                    info = ProcesadorArchivos.procesar_archivo(archivo, "venta")
                    ventas_pendientes.append((archivo.name, info, 'venta'))
                    # Guardar en estado temporal
                    st.session_state[f"temp_venta_{archivo.name}"] = info
                except Exception as e:
                    st.error(f"❌ Error en {archivo.name}: {str(e)[:50]}")
    
    # Mostrar ventas pendientes de asignación
    if ventas_pendientes:
        st.markdown("**📋 Ventas pendientes de asignación:**")
        
        for nombre_archivo, info, tipo in ventas_pendientes:
            with st.container():
                # Fila compacta para cada archivo de venta
                col_nombre, col_info, col_año, col_mes, col_accion = st.columns([3, 2, 1.5, 1.5, 1])
                
                with col_nombre:
                    # Nombre formateado completo
                    nombre_display = formatear_nombre_archivo(nombre_archivo)
                    st.markdown(f"**{nombre_display}**")
                    st.caption(f"{info['documentos_count']} docs")
                
                with col_info:
                    # Info compacta
                    fecha_min = info['fecha_minima'].strftime('%d/%m')
                    fecha_max = info['fecha_maxima'].strftime('%d/%m')
                    st.caption(f"{fecha_min}-{fecha_max}")
                    st.caption(formatear_monto(info['total_monto']))
                
                with col_año:
                    # Selectbox año
                    año_pred = info['año_predominante'] or datetime.now().year
                    año = st.selectbox(
                        "Año",
                        range(2020, datetime.now().year + 2),
                        index=año_pred - 2020,
                        key=f"año_venta_{nombre_archivo}",
                        label_visibility="collapsed"
                    )
                
                with col_mes:
                    # Selectbox mes
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
                    # Botón de confirmación
                    periodo = f"{año}-{mes_num:02d}"
                    
                    if st.button("✅", 
                               key=f"btn_venta_{nombre_archivo}",
                               help=f"Asignar {periodo}",
                               type="primary"):
                        
                        # Guardar definitivamente
                        st.session_state.archivos_procesados[nombre_archivo] = info
                        st.session_state.periodos_asignados[nombre_archivo] = periodo
                        
                        # Limpiar temporal
                        if f"temp_venta_{nombre_archivo}" in st.session_state:
                            del st.session_state[f"temp_venta_{nombre_archivo}"]
                        
                        st.rerun()
                    
                    st.caption(f"`{periodo}`")
    
    # ===== SECCIÓN COMPRAS =====
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
    
    # Procesar y mostrar compras pendientes
    compras_pendientes = []
    if compras_files:
        for archivo in compras_files:
            if archivo.name not in st.session_state.archivos_procesados:
                try:
                    info = ProcesadorArchivos.procesar_archivo(archivo, "compra")
                    compras_pendientes.append((archivo.name, info, 'compra'))
                    st.session_state[f"temp_compra_{archivo.name}"] = info
                except Exception as e:
                    st.error(f"❌ Error en {archivo.name}: {str(e)[:50]}")
    
    # Mostrar compras pendientes de asignación
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
        
        **Siguiente paso:** Ve a la pestaña **'📈 Análisis'** para ver resultados.
        """)
    
    pendientes_total = len(ventas_pendientes) + len(compras_pendientes)
    if pendientes_total > 0:
        st.warning(f"⚠️ **{pendientes_total} archivo(s) pendiente(s) de asignación**")

# ==========================================
# PESTAÑA 2: ANÁLISIS MEJORADO
# ==========================================

def pestana_analisis():
    """Pestaña de análisis con separación."""
    st.header("📈 Análisis de Resultados")
    
    if not st.session_state.archivos_procesados:
        st.info("📭 **No hay archivos procesados**")
        return
    
    # Resumen de archivos
    total = len(st.session_state.archivos_procesados)
    ventas = sum(1 for v in st.session_state.archivos_procesados.values() 
                if v['tipo_archivo'] == 'venta')
    compras = total - ventas
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Archivos", total)
    with col2:
        st.metric("Ventas", ventas)
    with col3:
        st.metric("Compras", compras)
    
    # Recolectar documentos
    todos_documentos = []
    for nombre, info in st.session_state.archivos_procesados.items():
        for doc in info['documentos']:
            periodo = st.session_state.periodos_asignados.get(nombre, "Sin período")
            doc['periodo_asignado'] = periodo
            todos_documentos.append(doc)
    
    # Calcular
    resumen_periodos = CalculadoraResultados.agrupar_por_periodo(
        todos_documentos, 
        st.session_state.periodos_asignados
    )
    totales = CalculadoraResultados.calcular_totales(resumen_periodos)
    datos_tabla = CalculadoraResultados.generar_dataframe_resultados(resumen_periodos)
    
    # ===== MÉTRICAS FINANCIERAS =====
    st.markdown("---")
    st.markdown("### 📊 **Métricas Financieras**")
    
    cols = st.columns(4)
    with cols[0]:
        st.metric("Ventas", formatear_monto(totales['ventas_totales']))
    with cols[1]:
        st.metric("Compras", formatear_monto(totales['compras_totales']))
    with cols[2]:
        st.metric("Resultado", formatear_monto(totales['resultado_total']))
    with cols[3]:
        st.metric("Documentos", totales['documentos_totales'])
    
    # ===== TABLA POR PERÍODO =====
    if datos_tabla:
        st.markdown("---")
        st.markdown("### 📅 **Resultados por Período**")
        
        df = pd.DataFrame(datos_tabla)
        
        # Formatear montos
        for col in ['Ventas', 'Compras', 'Resultado']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: formatear_monto(x))
        
        # Mostrar tabla
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ===== LISTA DE ARCHIVOS CON SEPARACIÓN =====
    st.markdown("---")
    
    # Ventas
    archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                      if v['tipo_archivo'] == 'venta'}
    
    if archivos_ventas:
        with st.expander(f"🟢 **Archivos de Ventas ({len(archivos_ventas)})**"):
            for nombre, info in archivos_ventas.items():
                periodo = st.session_state.periodos_asignados.get(nombre, "Sin asignar")
                
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.text(formatear_nombre_archivo(nombre))
                with col2:
                    st.code(periodo)
                with col3:
                    st.text(formatear_monto(info['total_monto']))
    
    # Compras
    archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                       if v['tipo_archivo'] == 'compra'}
    
    if archivos_compras:
        with st.expander(f"🔵 **Archivos de Compras ({len(archivos_compras)})**"):
            for nombre, info in archivos_compras.items():
                periodo = st.session_state.periodos_asignados.get(nombre, "Sin asignar")
                
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.text(formatear_nombre_archivo(nombre))
                with col2:
                    st.code(periodo)
                with col3:
                    st.text(formatear_monto(info['total_monto']))

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN
# ==========================================

def pestana_configuracion():
    """Pestaña de configuración."""
    st.header("⚙️ Configuración")
    
    if st.button("🔄 **Limpiar Todo y Reiniciar**", 
                type="secondary",
                use_container_width=True):
        # Limpiar TODO
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Inicializar estados vacíos
        st.session_state.archivos_procesados = {}
        st.session_state.periodos_asignados = {}
        
        st.success("✅ Sistema reiniciado correctamente")
        st.rerun()

# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📥 Carga", "📈 Análisis", "⚙️ Config"])

with tab1:
    pestana_carga()

with tab2:
    pestana_analisis()

with tab3:
    pestana_configuracion()

# Pie
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y')}")
