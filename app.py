# app.py - VERSIÓN CORREGIDA (sin redundancia y limpia correctamente)
import streamlit as st
from datetime import datetime
import pandas as pd
from collections import defaultdict

# Importar desde core
from core import ProcesadorArchivos, CalculadoraResultados, formatear_monto

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="wide")
st.title("📊 Simulador de Resultados")

# ==========================================
# ESTADO DE LA APLICACIÓN
# ==========================================

if 'archivos_procesados' not in st.session_state:
    st.session_state.archivos_procesados = {}
if 'periodos_asignados' not in st.session_state:
    st.session_state.periodos_asignados = {}

# ==========================================
# COMPONENTES DE INTERFAZ MEJORADOS
# ==========================================

def crear_uploader_multiple(tipo):
    """Crea uploader para múltiples archivos SIN mostrar lista."""
    st.markdown(f"### 📋 Archivos de {tipo}")
    
    archivos = st.file_uploader(
        f"Selecciona UNO o VARIOS archivos de {tipo.lower()}",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        key=f"{tipo.lower()}_uploader_multiple",
        help="📌 Puedes seleccionar MÚLTIPLES archivos a la vez.",
        label_visibility="visible"
    )
    
    if archivos:
        st.success(f"✅ **{len(archivos)} archivo(s) de {tipo.lower()} seleccionado(s)**")
    
    return archivos

def mostrar_info_archivo_simple(info_archivo, tipo):
    """Muestra información MÍNIMA del archivo (solo para confirmación)."""
    with st.container():
        # Solo mostramos lo esencial para confirmar el período
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Nombre muy corto
            nombre = info_archivo['nombre_archivo']
            if len(nombre) > 20:
                nombre = nombre[:17] + "..."
            st.markdown(f"**Archivo:** `{nombre}`")
            
            # Solo información clave
            st.caption(f"📄 {info_archivo['documentos_count']} documentos | " 
                      f"📅 {info_archivo['fecha_minima'].strftime('%d/%m')}-"
                      f"{info_archivo['fecha_maxima'].strftime('%d/%m/%Y')}")
        
        with col2:
            st.markdown(f"**{formatear_monto(info_archivo['total_monto'])}**")
        
        # Detección automática
        if info_archivo['año_predominante']:
            porcentaje = (info_archivo['cantidad_predominante'] / info_archivo['documentos_count']) * 100
            if porcentaje >= 50:
                st.info(f"📅 **Detección automática:** {info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d} "
                       f"({porcentaje:.0f}% de los documentos)")
            else:
                st.warning("⚠️ **Múltiples períodos detectados** - Verifica cuidadosamente")
        else:
            st.error("❌ **No se pudo detectar período** - Asigna manualmente")
        
        return info_archivo['año_predominante'], info_archivo['mes_predominante']

def solicitar_periodo(año_pred, mes_pred, nombre_archivo, tipo, idx):
    """Solicita confirmación del año-mes CON botón de confirmación."""
    with st.container():
        st.markdown("**Asignar Período:**")
        
        col_a, col_b, col_c = st.columns([2, 2, 1])
        
        with col_a:
            años_disponibles = list(range(2020, datetime.now().year + 2))
            año_default = año_pred if año_pred and año_pred in años_disponibles else datetime.now().year
            año_index = años_disponibles.index(año_default) if año_default in años_disponibles else len(años_disponibles)-1
            
            año_seleccionado = st.selectbox(
                "Año",
                años_disponibles,
                index=año_index,
                key=f"año_{tipo}_{idx}_{nombre_archivo}",
                label_visibility="collapsed"
            )
        
        with col_b:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_default = mes_pred - 1 if mes_pred else 0
            
            mes_seleccionado = st.selectbox(
                "Mes",
                meses,
                index=mes_default,
                key=f"mes_{tipo}_{idx}_{nombre_archivo}",
                label_visibility="collapsed"
            )
        
        with col_c:
            mes_numero = meses.index(mes_seleccionado) + 1
            
            # Estado para saber si ya se confirmó este archivo
            estado_key = f"confirmado_{nombre_archivo}"
            if estado_key not in st.session_state:
                st.session_state[estado_key] = False
            
            if st.session_state[estado_key]:
                st.success(f"✅ {año_seleccionado}-{mes_numero:02d}")
                return año_seleccionado, mes_numero, True
            else:
                if st.button("Confirmar", 
                           key=f"btn_{tipo}_{idx}_{nombre_archivo}", 
                           type="primary",
                           use_container_width=True):
                    st.session_state[estado_key] = True
                    st.rerun()
                return año_seleccionado, mes_numero, False
        
        st.markdown("---")

# ==========================================
# PESTAÑA 1: CARGA DE ARCHIVOS (SIMPLIFICADA)
# ==========================================

def pestana_carga():
    """Pestaña para cargar archivos SIN redundancia."""
    st.header("📥 Carga de Archivos")
    
    # Mostrar solo un resumen rápido si ya hay archivos
    if st.session_state.archivos_procesados:
        st.success(f"✅ **{len(st.session_state.archivos_procesados)} archivo(s) ya cargado(s)**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            ventas = sum(1 for v in st.session_state.archivos_procesados.values() 
                        if v['tipo_archivo'] == 'venta')
            st.metric("Ventas", ventas)
        with col2:
            compras = sum(1 for v in st.session_state.archivos_procesados.values() 
                         if v['tipo_archivo'] == 'compra')
            st.metric("Compras", compras)
        with col3:
            total_docs = sum(v['documentos_count'] for v in st.session_state.archivos_procesados.values())
            st.metric("Documentos", total_docs)
        
        st.info("💡 Para agregar más archivos, súbelos a continuación. Para reiniciar, ve a la pestaña 'Configuración'.")
        st.markdown("---")
    
    # Inicializar contadores
    archivos_nuevos_procesados = 0
    archivos_pendientes = 0
    
    # ===== SECCIÓN VENTAS =====
    with st.expander("📤 **Cargar Archivos de VENTAS**", expanded=True):
        archivos_ventas = crear_uploader_multiple("Ventas")
        
        if archivos_ventas:
            for idx, archivo in enumerate(archivos_ventas):
                # Verificar si ya está procesado
                if archivo.name in st.session_state.archivos_procesados:
                    continue
                
                try:
                    # Procesar archivo
                    with st.spinner(f"Procesando {archivo.name[:20]}..."):
                        info_archivo = ProcesadorArchivos.procesar_archivo(archivo, "venta")
                    
                    # Mostrar info mínima y solicitar período
                    año_pred, mes_pred = mostrar_info_archivo_simple(info_archivo, "Venta")
                    año_confirmado, mes_confirmado, confirmado = solicitar_periodo(
                        año_pred, mes_pred, archivo.name, "venta", idx
                    )
                    
                    if confirmado:
                        st.session_state.archivos_procesados[archivo.name] = info_archivo
                        st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                        archivos_nuevos_procesados += 1
                        st.success(f"✅ **{archivo.name[:20]}...** asignado a **{año_confirmado}-{mes_confirmado:02d}**")
                    else:
                        archivos_pendientes += 1
                    
                except Exception as e:
                    st.error(f"❌ **Error en {archivo.name[:20]}...:** {str(e)[:100]}")
    
    # ===== SECCIÓN COMPRAS =====
    with st.expander("📥 **Cargar Archivos de COMPRAS**", expanded=True):
        archivos_compras = crear_uploader_multiple("Compras")
        
        if archivos_compras:
            for idx, archivo in enumerate(archivos_compras):
                if archivo.name in st.session_state.archivos_procesados:
                    continue
                
                try:
                    with st.spinner(f"Procesando {archivo.name[:20]}..."):
                        info_archivo = ProcesadorArchivos.procesar_archivo(archivo, "compra")
                    
                    año_pred, mes_pred = mostrar_info_archivo_simple(info_archivo, "Compra")
                    año_confirmado, mes_confirmado, confirmado = solicitar_periodo(
                        año_pred, mes_pred, archivo.name, "compra", idx
                    )
                    
                    if confirmado:
                        st.session_state.archivos_procesados[archivo.name] = info_archivo
                        st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                        archivos_nuevos_procesados += 1
                        st.success(f"✅ **{archivo.name[:20]}...** asignado a **{año_confirmado}-{mes_confirmado:02d}**")
                    else:
                        archivos_pendientes += 1
                    
                except Exception as e:
                    st.error(f"❌ **Error en {archivo.name[:20]}...:** {str(e)[:100]}")
    
    # ===== RESUMEN FINAL =====
    if archivos_nuevos_procesados > 0:
        st.success(f"""
        🎉 **{archivos_nuevos_procesados} nuevo(s) archivo(s) procesado(s) correctamente.**
        
        **Total de archivos cargados:** {len(st.session_state.archivos_procesados)}
        **Ve a la pestaña '📈 Análisis' para ver resultados.**
        """)
    
    if archivos_pendientes > 0:
        st.warning(f"""
        ⚠️ **{archivos_pendientes} archivo(s) pendiente(s) de confirmación.**
        
        **Para confirmar:** Asigna el período y haz clic en 'Confirmar' para cada archivo.
        """)

# ==========================================
# PESTAÑA 2: ANÁLISIS Y RESULTADOS
# ==========================================

def pestana_analisis():
    """Pestaña para ver análisis y resultados."""
    st.header("📈 Análisis de Resultados")
    
    if not st.session_state.archivos_procesados:
        st.info("""
        ⚠️ **No hay archivos cargados.**
        
        **Pasos a seguir:**
        1. Ve a la pestaña **'📥 Carga de Archivos'**
        2. Sube tus archivos de ventas y compras
        3. Asigna períodos a cada archivo
        4. Regresa aquí para ver los resultados
        
        💡 Puedes cargar múltiples archivos a la vez.
        """)
        return
    
    # Botón para recalcular
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Recalcular", type="primary", use_container_width=True):
            st.rerun()
    
    # Resumen rápido
    total_archivos = len(st.session_state.archivos_procesados)
    archivos_ventas = sum(1 for v in st.session_state.archivos_procesados.values() 
                         if v['tipo_archivo'] == 'venta')
    archivos_compras = total_archivos - archivos_ventas
    
    with st.expander(f"📋 **Resumen: {total_archivos} archivo(s) cargado(s)**", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Archivos", total_archivos)
        with col2:
            st.metric("Archivos Ventas", archivos_ventas)
        with col3:
            st.metric("Archivos Compras", archivos_compras)
        with col4:
            total_docs = sum(v['documentos_count'] for v in st.session_state.archivos_procesados.values())
            st.metric("Documentos", total_docs)
    
    st.markdown("---")
    
    # Recolectar documentos para cálculo
    todos_documentos = []
    for info in st.session_state.archivos_procesados.values():
        for doc in info['documentos']:
            periodo = st.session_state.periodos_asignados.get(doc['archivo_origen'], "Sin_periodo")
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
    
    # ===== SECCIÓN 1: MÉTRICAS PRINCIPALES =====
    st.subheader("📊 Métricas Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ventas Totales", formatear_monto(totales['ventas_totales']), 
                 f"{totales['documentos_ventas']} docs")
    with col2:
        st.metric("Compras Totales", formatear_monto(totales['compras_totales']), 
                 f"{totales['documentos_compras']} docs")
    with col3:
        st.metric("Resultado Neto", formatear_monto(totales['resultado_total']))
    with col4:
        st.metric("Total Documentos", totales['documentos_totales'])
    
    # ===== SECCIÓN 2: TABLA POR PERÍODO =====
    st.markdown("---")
    st.subheader("📅 Resultados por Período")
    
    if datos_tabla:
        df_resultados = pd.DataFrame(datos_tabla)
        
        # Formatear tabla
        def formatear_fila(row):
            styles = []
            for val in row:
                if isinstance(val, (int, float)):
                    if val < 0:
                        styles.append('color: #e74c3c; font-weight: bold;')
                    elif val > 0 and row.name in ['Resultado', 'Margen %']:
                        styles.append('color: #2ecc71; font-weight: bold;')
                    else:
                        styles.append('')
                else:
                    styles.append('')
            return styles
        
        # Aplicar formato condicional
        styled_df = df_resultados.style.format({
            'Ventas': lambda x: formatear_monto(x),
            'Compras': lambda x: formatear_monto(x),
            'Resultado': lambda x: formatear_monto(x),
            'Margen %': '{:+.1f}%'
        }).apply(formatear_fila, axis=1)
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Exportar opción
        csv = df_resultados.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar como CSV",
            data=csv,
            file_name="resultados_por_periodo.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No hay datos para mostrar por período.")
    
    # ===== SECCIÓN 3: ESTADÍSTICAS ADICIONALES =====
    st.markdown("---")
    with st.expander("📊 **Estadísticas Detalladas**"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📈 Promedios")
            st.metric("Promedio por Venta", formatear_monto(estadisticas['promedio_venta']))
            st.metric("Promedio por Compra", formatear_monto(estadisticas['promedio_compra']))
            
            st.markdown("##### 📝 Notas de Crédito")
            st.metric("Ventas", estadisticas['notas_credito_ventas'])
            st.metric("Compras", estadisticas['notas_credito_compras'])
        
        with col2:
            st.markdown("##### 📋 Distribución")
            dist_data = pd.DataFrame({
                'Tipo': ['Ventas', 'Compras'],
                'Documentos': [estadisticas['total_ventas_count'], estadisticas['total_compras_count']],
                'Monto Total': [totales['ventas_totales'], totales['compras_totales']]
            })
            st.dataframe(dist_data, use_container_width=True, hide_index=True)

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN (CORREGIDA PARA LIMPIAR)
# ==========================================

def pestana_configuracion():
    """Pestaña para configuración - CORREGIDA para limpiar TODO."""
    st.header("⚙️ Configuración")
    
    st.markdown("### 📊 Estado Actual del Sistema")
    
    # Mostrar estado actual
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Archivos Cargados", len(st.session_state.archivos_procesados))
    with col2:
        st.metric("Períodos Asignados", len(st.session_state.periodos_asignados))
    with col3:
        if st.session_state.archivos_procesados:
            total_docs = sum(info['documentos_count'] for info in st.session_state.archivos_procesados.values())
            st.metric("Documentos", total_docs)
        else:
            st.metric("Documentos", 0)
    
    # Lista de archivos cargados
    if st.session_state.archivos_procesados:
        st.markdown("---")
        st.markdown("### 📁 Archivos Actualmente Cargados")
        
        for archivo, info in st.session_state.archivos_procesados.items():
            periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
            with st.container():
                col_a, col_b, col_c = st.columns([3, 2, 1])
                with col_a:
                    st.text(archivo[:40] + ("..." if len(archivo) > 40 else ""))
                with col_b:
                    st.code(periodo)
                with col_c:
                    st.text(formatear_monto(info['total_monto']))
                st.markdown("---")
    
    st.markdown("---")
    st.markdown("### 🚨 Acciones del Sistema")
    
    # Acción PELIGROSA: Limpiar TODO
    if st.button("🔄 **INICIAR NUEVO ANÁLISIS (Borra Todo)**", 
                 type="secondary", 
                 use_container_width=True,
                 help="⚠️ Esta acción eliminará TODOS los archivos y datos cargados"):
        
        # Crear lista de TODAS las keys a eliminar
        todas_keys = list(st.session_state.keys())
        
        # Filtrar solo las que queremos eliminar
        keys_a_preservar = []  # Ninguna, queremos limpiar TODO
        
        # Eliminar cada key excepto las preservadas
        for key in todas_keys:
            if key not in keys_a_preservar:
                del st.session_state[key]
        
        # Reinicializar los estados vacíos
        st.session_state.archivos_procesados = {}
        st.session_state.periodos_asignados = {}
        
        st.success("✅ **¡Todo ha sido limpiado correctamente!**")
        st.info("💡 El sistema ha sido reiniciado. Puedes comenzar un nuevo análisis.")
        st.rerun()

# ==========================================
# FLUJO PRINCIPAL CON TABS
# ==========================================

# Crear tabs
tab1, tab2, tab3 = st.tabs([
    "📥 Carga de Archivos", 
    "📈 Análisis", 
    "⚙️ Configuración"
])

with tab1:
    pestana_carga()

with tab2:
    pestana_analisis()

with tab3:
    pestana_configuracion()

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
