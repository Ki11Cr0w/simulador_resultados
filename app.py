# app.py - VERSIÓN ULTRA COMPACTA
import streamlit as st
from datetime import datetime
import pandas as pd

# Importar desde core
from core import ProcesadorArchivos, CalculadoraResultados, formatear_monto

# ==========================================
# CONFIGURACIÓN - CSS EXTREMO PARA OCULTAR
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="wide")

# CSS AGGRESIVO para ocultar TODO lo automático
st.markdown("""
<style>
    /* OCULTAR COMPLETAMENTE la visualización de archivos de Streamlit */
    .st-emotion-cache-1gulkj5,
    div[data-testid="stFileUploader"] > div > div > div > div,
    .st-emotion-cache-1e5imcs {
        display: none !important;
    }
    
    /* Asegurar que el área de upload sea mínima */
    .st-emotion-cache-7ym5gk {
        min-height: 40px !important;
        padding: 8px !important;
    }
    
    /* Compactar todo */
    .st-emotion-cache-16idsys p {
        margin: 2px 0 !important;
        font-size: 13px !important;
    }
    
    /* Espaciado mínimo entre elementos */
    .st-emotion-cache-1y4p8pa {
        padding: 0.5rem !important;
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
if 'archivos_subidos' not in st.session_state:
    st.session_state.archivos_subidos = {'ventas': [], 'compras': []}

# ==========================================
# FUNCIONES AUXILIARES COMPACTAS
# ==========================================

def nombre_super_corto(nombre_archivo, max_len=15):
    """Devuelve nombre ultra corto sin extensión."""
    # Eliminar extensión
    if '.' in nombre_archivo:
        nombre = nombre_archivo[:nombre_archivo.rfind('.')]
    else:
        nombre = nombre_archivo
    
    # Eliminar palabras comunes
    palabras_comunes = ['VENTAS', 'COMPRAS', 'VENTA', 'COMPRA', 'ARCHIVO', 'FILE', 'DATA']
    for palabra in palabras_comunes:
        nombre = nombre.replace(palabra, '').replace(palabra.lower(), '')
    
    # Limpiar espacios y acortar
    nombre = nombre.strip(' _-')
    
    if len(nombre) > max_len:
        return nombre[:max_len-2] + ".."
    return nombre

# ==========================================
# PESTAÑA 1: CARGA ULTRA COMPACTA
# ==========================================

def pestana_carga():
    """Pestaña ultra compacta - solo subir y asignar."""
    st.header("📥 Carga Rápida")
    
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
    
    # ===== VENTAS - DISEÑO COMPACTO =====
    st.markdown("### 🟢 **Ventas**")
    
    # Uploader COMPACTO
    ventas_files = st.file_uploader(
        "",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="ventas_upload",
        label_visibility="collapsed",
        help="Arrastra o selecciona archivos de ventas"
    )
    
    # Procesar nuevos archivos de ventas
    if ventas_files:
        for archivo in ventas_files:
            if archivo.name not in st.session_state.archivos_subidos['ventas']:
                st.session_state.archivos_subidos['ventas'].append(archivo.name)
                
                try:
                    # Procesar rápidamente
                    info = ProcesadorArchivos.procesar_archivo(archivo, "venta")
                    
                    # GUARDAR EN SESIÓN (para procesar después)
                    st.session_state[f"pendiente_{archivo.name}"] = {
                        'info': info,
                        'tipo': 'venta'
                    }
                    
                except Exception as e:
                    st.error(f"❌ Error en {nombre_super_corto(archivo.name)}")
    
    # ===== COMPRAS - DISEÑO COMPACTO =====
    st.markdown("### 🔵 **Compras**")
    
    compras_files = st.file_uploader(
        "",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="compras_upload",
        label_visibility="collapsed",
        help="Arrastra o selecciona archivos de compras"
    )
    
    if compras_files:
        for archivo in compras_files:
            if archivo.name not in st.session_state.archivos_subidos['compras']:
                st.session_state.archivos_subidos['compras'].append(archivo.name)
                
                try:
                    info = ProcesadorArchivos.procesar_archivo(archivo, "compra")
                    st.session_state[f"pendiente_{archivo.name}"] = {
                        'info': info,
                        'tipo': 'compra'
                    }
                except Exception as e:
                    st.error(f"❌ Error en {nombre_super_corto(archivo.name)}")
    
    # ===== LISTA COMPACTA DE ARCHIVOS PENDIENTES =====
    st.markdown("---")
    st.markdown("### 📝 **Asignar Períodos**")
    
    archivos_pendientes = [
        (nombre, datos) for nombre, datos in st.session_state.items()
        if nombre.startswith('pendiente_')
    ]
    
    if not archivos_pendientes and not st.session_state.archivos_procesados:
        st.info("📤 **Sube archivos arriba para comenzar**")
        return
    
    if not archivos_pendientes and st.session_state.archivos_procesados:
        st.success("✅ **Todos los archivos asignados**")
        st.info("Ve a la pestaña '📈 Análisis' para ver resultados")
        return
    
    # Mostrar lista COMPACTA de pendientes
    for nombre_key, datos in archivos_pendientes:
        nombre_archivo = nombre_key.replace('pendiente_', '')
        info = datos['info']
        tipo = datos['tipo']
        
        with st.container():
            # UNA SOLA LÍNEA por archivo
            col_nombre, col_periodo, col_accion = st.columns([3, 4, 2])
            
            with col_nombre:
                # Nombre ULTRA CORTO + icono pequeño
                nombre_corto = nombre_super_corto(nombre_archivo, 12)
                emoji = "🟢" if tipo == 'venta' else "🔵"
                st.markdown(f"{emoji} **{nombre_corto}**")
                
                # Mini info en tooltip hover (no ocupa espacio)
                with st.popover("ℹ️"):
                    st.caption(f"Docs: {info['documentos_count']}")
                    st.caption(f"Desde: {info['fecha_minima'].strftime('%d/%m')}")
                    st.caption(f"Hasta: {info['fecha_maxima'].strftime('%d/%m/%y')}")
                    st.caption(f"Monto: {formatear_monto(info['total_monto'])}")
            
            with col_periodo:
                # Detección automática (si hay)
                if info['año_predominante']:
                    default_año = info['año_predominante']
                    default_mes = info['mes_predominante'] - 1
                else:
                    default_año = datetime.now().year
                    default_mes = 0
                
                # Selectboxes COMPACTOS en línea
                col_año, col_mes = st.columns(2)
                with col_año:
                    año = st.selectbox(
                        "Año",
                        range(2020, datetime.now().year + 2),
                        index=default_año - 2020 if default_año else 0,
                        key=f"año_{nombre_archivo}",
                        label_visibility="collapsed"
                    )
                with col_mes:
                    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    mes_idx = st.selectbox(
                        "Mes",
                        meses,
                        index=default_mes,
                        key=f"mes_{nombre_archivo}",
                        label_visibility="collapsed"
                    )
                    mes_num = meses.index(mes_idx) + 1
            
            with col_accion:
                # Botón COMPACTO para confirmar
                periodo = f"{año}-{mes_num:02d}"
                
                if st.button("✅", 
                          key=f"confirm_{nombre_archivo}",
                          help=f"Asignar {periodo}",
                          type="secondary"):
                    
                    # Guardar definitivamente
                    st.session_state.archivos_procesados[nombre_archivo] = info
                    st.session_state.periodos_asignados[nombre_archivo] = periodo
                    
                    # Eliminar de pendientes
                    del st.session_state[nombre_key]
                    
                    # Actualizar lista de subidos
                    if tipo == 'venta' and nombre_archivo in st.session_state.archivos_subidos['ventas']:
                        st.session_state.archivos_subidos['ventas'].remove(nombre_archivo)
                    elif tipo == 'compra' and nombre_archivo in st.session_state.archivos_subidos['compras']:
                        st.session_state.archivos_subidos['compras'].remove(nombre_archivo)
                    
                    st.rerun()
                
                # Mostrar período previsto
                st.caption(f"`{periodo}`")
    
    # ===== RESUMEN FINAL COMPACTO =====
    if archivos_pendientes:
        st.warning(f"⏳ **{len(archivos_pendientes)} archivo(s) pendiente(s) de asignación**")

# ==========================================
# PESTAÑA 2: ANÁLISIS COMPACTO
# ==========================================

def pestana_analisis():
    """Pestaña de análisis compacta."""
    st.header("📈 Análisis")
    
    if not st.session_state.archivos_procesados:
        st.info("📭 **No hay archivos procesados**")
        return
    
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
    
    # ===== MÉTRICAS EN UNA SOLA LÍNEA =====
    cols = st.columns(4)
    with cols[0]:
        st.metric("Ventas", formatear_monto(totales['ventas_totales']))
    with cols[1]:
        st.metric("Compras", formatear_monto(totales['compras_totales']))
    with cols[2]:
        st.metric("Resultado", formatear_monto(totales['resultado_total']))
    with cols[3]:
        st.metric("Documentos", totales['documentos_totales'])
    
    # ===== TABLA COMPACTA =====
    if datos_tabla:
        st.markdown("---")
        st.markdown("**📅 Resultados por Período**")
        
        df = pd.DataFrame(datos_tabla)
        
        # Formatear compacto
        def formato_compacto(val):
            if isinstance(val, (int, float)):
                if abs(val) >= 1_000_000:
                    return f"{val/1_000_000:,.1f}M"
                elif abs(val) >= 1_000:
                    return f"{val:,.0f}"
            return val
        
        # Aplicar formato
        for col in ['Ventas', 'Compras', 'Resultado']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: formatear_monto(x))
        
        # Mostrar tabla compacta
        st.dataframe(
            df,
            use_container_width=True,
            height=min(400, 45 * len(df)),
            hide_index=True
        )
    
    # ===== LISTA RÁPIDA DE ARCHIVOS =====
    with st.expander(f"📁 Archivos ({len(st.session_state.archivos_procesados)})"):
        for nombre, info in st.session_state.archivos_procesados.items():
            periodo = st.session_state.periodos_asignados.get(nombre, "Sin asignar")
            tipo = info['tipo_archivo']
            emoji = "🟢" if tipo == 'venta' else "🔵"
            
            nombre_corto = nombre_super_corto(nombre, 20)
            
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.text(f"{emoji} {nombre_corto}")
            with col2:
                st.code(periodo)
            with col3:
                st.text(formatear_monto(info['total_monto']))

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN
# ==========================================

def pestana_configuracion():
    """Pestaña de configuración mínima."""
    st.header("⚙️")
    
    st.markdown("**Acciones del sistema:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 **Limpiar Todo**", 
                    type="secondary",
                    use_container_width=True):
            # Limpiar absolutamente TODO
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Inicializar estados vacíos
            st.session_state.archivos_procesados = {}
            st.session_state.periodos_asignados = {}
            st.session_state.archivos_subidos = {'ventas': [], 'compras': []}
            
            st.success("✅ Sistema reiniciado")
            st.rerun()
    
    with col2:
        if st.session_state.archivos_procesados:
            st.metric("Archivos listos", len(st.session_state.archivos_procesados))

# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📥 Carga", "📈 Análisis", "⚙️"])

with tab1:
    pestana_carga()

with tab2:
    pestana_analisis()

with tab3:
    pestana_configuracion()

# Pie mínimo
st.caption(f"v1.0 | {datetime.now().strftime('%d/%m')}")
