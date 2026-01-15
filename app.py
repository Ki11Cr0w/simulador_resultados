# app.py - VERSIÓN CON TABS SEPARADAS
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
# COMPONENTES DE INTERFAZ
# ==========================================

def crear_uploader_multiple(tipo):
    """Crea uploader para múltiples archivos."""
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
        st.success(f"📦 **{len(archivos)} archivo(s) de {tipo.lower()} seleccionado(s)**")
    
    return archivos

def mostrar_archivo_compacto(info_archivo, idx, tipo):
    """Muestra información de archivo en formato compacto."""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            nombre_corto = info_archivo['nombre_archivo'][:25]
            if len(info_archivo['nombre_archivo']) > 25:
                nombre_corto += "..."
            st.markdown(f"**{idx+1}. {nombre_corto}**")
            st.markdown(f"📄 **{info_archivo['documentos_count']} doc**")
        
        with col2:
            fecha_min = info_archivo['fecha_minima'].strftime('%d/%m')
            fecha_max = info_archivo['fecha_maxima'].strftime('%d/%m/%Y')
            st.markdown(f"📅 **{fecha_min} - {fecha_max}**")
        
        with col3:
            if info_archivo['año_predominante']:
                porcentaje = (info_archivo['cantidad_predominante'] / info_archivo['documentos_count']) * 100
                if porcentaje >= 50:
                    st.markdown(f"🔍 **{info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d}**")
                else:
                    st.markdown(f"⚠️ **Varios períodos**")
            else:
                st.markdown("❓ **Sin detección**")
        
        with col4:
            st.markdown(f"💰 **{formatear_monto(info_archivo['total_monto'])}**")
        
        return info_archivo['año_predominante'], info_archivo['mes_predominante']

def solicitar_periodo(año_pred, mes_pred, idx, nombre_archivo, tipo):
    """Solicita confirmación del año-mes con botón de confirmación."""
    with st.container():
        col_a, col_b, col_c, col_d, col_e = st.columns([1, 2, 2, 2, 1])
        
        with col_a:
            st.markdown("**Período:**")
        
        with col_b:
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
        
        with col_c:
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
        
        with col_d:
            mes_numero = meses.index(mes_seleccionado) + 1
            periodo_texto = f"**{año_seleccionado}-{mes_numero:02d}**"
            st.markdown(periodo_texto)
        
        with col_e:
            estado_key = f"confirmado_{tipo}_{idx}_{nombre_archivo}"
            if estado_key not in st.session_state:
                st.session_state[estado_key] = False
            
            if st.session_state[estado_key]:
                st.success("✅")
                return año_seleccionado, mes_numero, True
            else:
                if st.button("✓", key=f"btn_{tipo}_{idx}_{nombre_archivo}", 
                           help="Confirmar período", type="secondary"):
                    st.session_state[estado_key] = True
                    st.rerun()
                return año_seleccionado, mes_numero, False

# ==========================================
# PESTAÑA 1: CARGA DE ARCHIVOS
# ==========================================

def pestana_carga():
    """Pestaña para cargar archivos."""
    st.header("📥 Carga de Archivos")
    
    # Contadores para mostrar advertencias
    archivos_pendientes_ventas = 0
    archivos_pendientes_compras = 0
    
    # Ventas
    archivos_ventas = crear_uploader_multiple("Ventas")
    
    if archivos_ventas:
        for idx, archivo in enumerate(archivos_ventas):
            if archivo.name in st.session_state.archivos_procesados:
                st.info(f"⏭️ Archivo '{archivo.name[:20]}...' ya procesado")
                continue
            
            try:
                info_archivo = ProcesadorArchivos.procesar_archivo(archivo, "venta")
                año_pred, mes_pred = mostrar_archivo_compacto(info_archivo, idx, "Venta")
                año_confirmado, mes_confirmado, confirmado = solicitar_periodo(
                    año_pred, mes_pred, idx, archivo.name, "venta"
                )
                
                if confirmado:
                    st.session_state.archivos_procesados[archivo.name] = info_archivo
                    st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                    st.success(f"✅ Período {año_confirmado}-{mes_confirmado:02d} confirmado")
                else:
                    archivos_pendientes_ventas += 1
                
            except Exception as e:
                st.error(f"❌ **Venta {idx+1} - {archivo.name}:** {str(e)[:50]}")
    
    # Compras
    archivos_compras = crear_uploader_multiple("Compras")
    
    if archivos_compras:
        for idx, archivo in enumerate(archivos_compras):
            if archivo.name in st.session_state.archivos_procesados:
                st.info(f"⏭️ Archivo '{archivo.name[:20]}...' ya procesado")
                continue
            
            try:
                info_archivo = ProcesadorArchivos.procesar_archivo(archivo, "compra")
                año_pred, mes_pred = mostrar_archivo_compacto(info_archivo, idx, "Compra")
                año_confirmado, mes_confirmado, confirmado = solicitar_periodo(
                    año_pred, mes_pred, idx, archivo.name, "compra"
                )
                
                if confirmado:
                    st.session_state.archivos_procesados[archivo.name] = info_archivo
                    st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                    st.success(f"✅ Período {año_confirmado}-{mes_confirmado:02d} confirmado")
                else:
                    archivos_pendientes_compras += 1
                
            except Exception as e:
                st.error(f"❌ **Compra {idx+1} - {archivo.name}:** {str(e)[:50]}")
    
    # Mostrar advertencias si hay archivos pendientes
    if archivos_pendientes_ventas > 0 or archivos_pendientes_compras > 0:
        st.warning(f"""
        ⚠️ **Archivos pendientes de confirmación:**
        - Ventas: {archivos_pendientes_ventas} archivo(s)
        - Compras: {archivos_pendientes_compras} archivo(s)
        
        **Para continuar:** Haz clic en ✓ en cada archivo para confirmar el período.
        """)
    
    # Mostrar resumen de lo que ya está cargado
    if st.session_state.archivos_procesados:
        st.markdown("---")
        st.subheader("📊 Resumen de Archivos Cargados")
        
        archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                          if v['tipo_archivo'] == 'venta'}
        archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                           if v['tipo_archivo'] == 'compra'}
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Archivos Totales", len(st.session_state.archivos_procesados))
        with col2:
            st.metric("Archivos Ventas", len(archivos_ventas))
        with col3:
            st.metric("Archivos Compras", len(archivos_compras))
        with col4:
            total_docs = sum(info['documentos_count'] for info in st.session_state.archivos_procesados.values())
            st.metric("Documentos", total_docs)
        
        st.success("✅ Archivos listos. Ve a la pestaña 'Análisis' para ver resultados.")

# ==========================================
# PESTAÑA 2: ANÁLISIS Y RESULTADOS
# ==========================================

def pestana_analisis():
    """Pestaña para ver análisis y resultados."""
    st.header("📈 Análisis de Resultados")
    
    if not st.session_state.archivos_procesados:
        st.info("""
        ⚠️ **No hay archivos cargados.**
        
        Por favor:
        1. Ve a la pestaña **'Carga de Archivos'**
        2. Sube tus archivos de ventas y compras
        3. Confirma los períodos para cada archivo
        4. Regresa a esta pestaña para ver los resultados
        """)
        return
    
    # Botón para recalcular
    if st.button("🔄 Recalcular Análisis", type="primary"):
        st.rerun()
    
    st.markdown("---")
    
    # Recolectar documentos
    todos_documentos = []
    for info in st.session_state.archivos_procesados.values():
        for doc in info['documentos']:
            periodo = st.session_state.periodos_asignados.get(doc['archivo_origen'], "Sin_periodo")
            doc['periodo_asignado'] = periodo
            todos_documentos.append(doc)
    
    # Calcular usando CalculadoraResultados
    resumen_periodos = CalculadoraResultados.agrupar_por_periodo(
        todos_documentos, 
        st.session_state.periodos_asignados
    )
    totales = CalculadoraResultados.calcular_totales(resumen_periodos)
    datos_tabla = CalculadoraResultados.generar_dataframe_resultados(resumen_periodos)
    estadisticas = CalculadoraResultados.calcular_estadisticas(todos_documentos)
    
    # ===== SECCIÓN 1: RESUMEN GENERAL =====
    st.subheader("📊 Resumen General")
    
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
    st.subheader("📅 Análisis por Período")
    
    if datos_tabla:
        df_resultados = pd.DataFrame(datos_tabla)
        
        def aplicar_estilo(val):
            if isinstance(val, (int, float)) and val < 0:
                return 'color: #e74c3c; font-weight: bold;'
            elif isinstance(val, (int, float)) and val > 0:
                return 'color: #2ecc71; font-weight: bold;'
            return ''
        
        styled_df = df_resultados.style.format({
            'Ventas': lambda x: formatear_monto(x),
            'Compras': lambda x: formatear_monto(x),
            'Resultado': lambda x: formatear_monto(x),
            'Margen %': '{:+.1f}%'
        }).applymap(aplicar_estilo, subset=['Resultado', 'Margen %'])
        
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No hay datos para mostrar por período.")
    
    # ===== SECCIÓN 3: ESTADÍSTICAS DETALLADAS =====
    st.markdown("---")
    st.subheader("📊 Estadísticas Detalladas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Promedios:**")
        st.metric("Promedio Venta", formatear_monto(estadisticas['promedio_venta']))
        st.metric("Promedio Compra", formatear_monto(estadisticas['promedio_compra']))
        
        st.markdown("**📝 Notas de Crédito:**")
        st.metric("NC Ventas", estadisticas['notas_credito_ventas'])
        st.metric("NC Compras", estadisticas['notas_credito_compras'])
    
    with col2:
        st.markdown("**📋 Distribución:**")
        
        # Crear DataFrame para gráfico de distribución
        dist_data = {
            'Tipo': ['Ventas', 'Compras'],
            'Cantidad': [estadisticas['total_ventas_count'], estadisticas['total_compras_count']],
            'Monto': [totales['ventas_totales'], totales['compras_totales']]
        }
        df_dist = pd.DataFrame(dist_data)
        
        st.dataframe(df_dist, use_container_width=True, hide_index=True)
    
    # ===== SECCIÓN 4: DETALLE DE ARCHIVOS =====
    st.markdown("---")
    with st.expander("📁 Ver Detalle de Archivos Cargados"):
        archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                          if v['tipo_archivo'] == 'venta'}
        archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                           if v['tipo_archivo'] == 'compra'}
        
        tab1, tab2 = st.tabs([f"Ventas ({len(archivos_ventas)})", f"Compras ({len(archivos_compras)})"])
        
        with tab1:
            if archivos_ventas:
                for archivo, info in archivos_ventas.items():
                    periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                    with st.container():
                        st.markdown(f"**{archivo}**")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.caption(f"Período: {periodo}")
                        with col_b:
                            st.caption(f"Documentos: {info['documentos_count']}")
                        with col_c:
                            st.caption(f"Monto: {formatear_monto(info['total_monto'])}")
                        st.markdown("---")
            else:
                st.info("No hay archivos de ventas")
        
        with tab2:
            if archivos_compras:
                for archivo, info in archivos_compras.items():
                    periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                    with st.container():
                        st.markdown(f"**{archivo}**")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.caption(f"Período: {periodo}")
                        with col_b:
                            st.caption(f"Documentos: {info['documentos_count']}")
                        with col_c:
                            st.caption(f"Monto: {formatear_monto(info['total_monto'])}")
                        st.markdown("---")
            else:
                st.info("No hay archivos de compras")

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN
# ==========================================

def pestana_configuracion():
    """Pestaña para configuración y limpieza."""
    st.header("⚙️ Configuración")
    
    st.markdown("### 📊 Estado Actual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Archivos Cargados", len(st.session_state.archivos_procesados))
        st.metric("Períodos Asignados", len(st.session_state.periodos_asignados))
    
    with col2:
        if st.session_state.archivos_procesados:
            total_docs = sum(info['documentos_count'] for info in st.session_state.archivos_procesados.values())
            st.metric("Documentos Totales", total_docs)
            
            total_monto = sum(info['total_monto'] for info in st.session_state.archivos_procesados.values())
            st.metric("Monto Total", formatear_monto(total_monto))
        else:
            st.info("No hay datos cargados")
    
    st.markdown("---")
    st.markdown("### 🗑️ Gestión de Datos")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        if st.button("🔍 Ver Datos en Bruto", use_container_width=True):
            if st.session_state.archivos_procesados:
                st.json(st.session_state.archivos_procesados, expanded=False)
            else:
                st.info("No hay datos para mostrar")
    
    with col_b:
        if st.button("📥 Exportar Resumen", use_container_width=True):
            if st.session_state.archivos_procesados:
                # Crear DataFrame para exportar
                datos_exportar = []
                for archivo, info in st.session_state.archivos_procesados.items():
                    datos_exportar.append({
                        'Archivo': archivo,
                        'Tipo': info['tipo_archivo'],
                        'Período': st.session_state.periodos_asignados.get(archivo, 'No asignado'),
                        'Documentos': info['documentos_count'],
                        'Monto Total': info['total_monto'],
                        'Fecha Mínima': info['fecha_minima'].strftime('%Y-%m-%d'),
                        'Fecha Máxima': info['fecha_maxima'].strftime('%Y-%m-%d')
                    })
                
                df_export = pd.DataFrame(datos_exportar)
                csv = df_export.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name="resumen_archivos.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No hay datos para exportar")
    
    st.markdown("---")
    st.markdown("### 🚨 Acciones Peligrosas")
    
    if st.button("🔄 Nuevo Análisis (Limpiar Todo)", type="secondary", use_container_width=True):
        # Limpiar estados de confirmación
        keys_a_eliminar = [k for k in st.session_state.keys() if k.startswith('confirmado_')]
        for key in keys_a_eliminar:
            del st.session_state[key]
        
        # Limpiar los otros estados
        for key in ['archivos_procesados', 'periodos_asignados']:
            if key in st.session_state:
                st.session_state[key] = {}
        
        st.success("✅ Todos los datos han sido limpiados")
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
