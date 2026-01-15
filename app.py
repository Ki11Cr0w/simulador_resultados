# app.py - VERSIÓN MODULAR CORTA
import streamlit as st
from datetime import datetime
import pandas as pd
from collections import defaultdict

# Importar funciones desde funciones.py
from funciones import (
    procesar_archivo, formatear_monto, agrupar_por_periodo,
    calcular_totales, generar_dataframe_resultados, calcular_estadisticas
)

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
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False

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
        # PRIMERA LÍNEA: Información básica
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
    """Solicita confirmación del año-mes."""
    with st.container():
        col_a, col_b, col_c, col_d = st.columns([1, 2, 2, 1])
        
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
            st.success(f"**{año_seleccionado}-{mes_numero:02d}**")
        
        return año_seleccionado, mes_numero

def vista_carga():
    """Vista para cargar archivos."""
    st.subheader("📥 Carga de Archivos")
    
    # Ventas
    archivos_ventas = crear_uploader_multiple("Ventas")
    
    if archivos_ventas:
        for idx, archivo in enumerate(archivos_ventas):
            if archivo.name in st.session_state.archivos_procesados:
                st.info(f"⏭️ Archivo '{archivo.name[:20]}...' ya procesado")
                continue
            
            try:
                info_archivo = procesar_archivo(archivo, "venta")
                año_pred, mes_pred = mostrar_archivo_compacto(info_archivo, idx, "Venta")
                año_confirmado, mes_confirmado = solicitar_periodo(año_pred, mes_pred, idx, archivo.name, "venta")
                
                st.session_state.archivos_procesados[archivo.name] = info_archivo
                st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                
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
                info_archivo = procesar_archivo(archivo, "compra")
                año_pred, mes_pred = mostrar_archivo_compacto(info_archivo, idx, "Compra")
                año_confirmado, mes_confirmado = solicitar_periodo(año_pred, mes_pred, idx, archivo.name, "compra")
                
                st.session_state.archivos_procesados[archivo.name] = info_archivo
                st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                
            except Exception as e:
                st.error(f"❌ **Compra {idx+1} - {archivo.name}:** {str(e)[:50]}")

def vista_resumen():
    """Vista de resumen."""
    if not st.session_state.archivos_procesados:
        return False
    
    st.markdown("### 📊 Resumen de Archivos")
    
    # Separar por tipo
    archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                      if v['tipo_archivo'] == 'venta'}
    archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                       if v['tipo_archivo'] == 'compra'}
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([f"📥 Ventas ({len(archivos_ventas)})", 
                                f"📤 Compras ({len(archivos_compras)})", 
                                "📈 Totales"])
    
    with tab1:
        if archivos_ventas:
            for archivo, info in archivos_ventas.items():
                periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{archivo[:30]}...**")
                with col2:
                    st.markdown(f"`{periodo}`")
                with col3:
                    st.markdown(f"**{formatear_monto(info['total_monto'])}**")
        else:
            st.info("No hay archivos de ventas")
    
    with tab2:
        if archivos_compras:
            for archivo, info in archivos_compras.items():
                periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{archivo[:30]}...**")
                with col2:
                    st.markdown(f"`{periodo}`")
                with col3:
                    st.markdown(f"**{formatear_monto(info['total_monto'])}**")
        else:
            st.info("No hay archivos de compras")
    
    with tab3:
        total_ventas = sum(info['total_monto'] for info in archivos_ventas.values())
        total_compras = sum(info['total_monto'] for info in archivos_compras.values())
        total_docs_ventas = sum(info['documentos_count'] for info in archivos_ventas.values())
        total_docs_compras = sum(info['documentos_count'] for info in archivos_compras.values())
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Ventas", formatear_monto(total_ventas), f"{total_docs_ventas} doc")
        with col2:
            st.metric("Compras", formatear_monto(total_compras), f"{total_docs_compras} doc")
        with col3:
            resultado = total_ventas - total_compras
            st.metric("Resultado", formatear_monto(resultado))
        with col4:
            st.metric("Total Docs", total_docs_ventas + total_docs_compras)
    
    return True

def vista_resultados():
    """Vista de resultados."""
    if not st.session_state.mostrar_resultados:
        return
    
    # Recolectar documentos
    todos_documentos = []
    for info in st.session_state.archivos_procesados.values():
        for doc in info['documentos']:
            periodo = st.session_state.periodos_asignados.get(doc['archivo_origen'], "Sin_periodo")
            doc['periodo_asignado'] = periodo
            todos_documentos.append(doc)
    
    # Calcular
    resumen_periodos = agrupar_por_periodo(todos_documentos, st.session_state.periodos_asignados)
    totales = calcular_totales(resumen_periodos)
    datos_tabla = generar_dataframe_resultados(resumen_periodos)
    estadisticas = calcular_estadisticas(todos_documentos)
    
    # Mostrar tabla
    st.subheader("📊 Análisis por Período")
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
    
    # Métricas
    st.markdown("---")
    st.markdown("### 📈 Resumen Final")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ventas Totales", formatear_monto(totales['ventas_totales']))
    with col2:
        st.metric("Compras Totales", formatear_monto(totales['compras_totales']))
    with col3:
        st.metric("Resultado Neto", formatear_monto(totales['resultado_total']))
    with col4:
        st.metric("Total Documentos", totales['documentos_totales'])

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

# 1. Cargar archivos
vista_carga()

# 2. Mostrar resumen si hay archivos
if st.session_state.archivos_procesados:
    st.markdown("---")
    
    if vista_resumen():
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            total_archivos = len(st.session_state.archivos_procesados)
            st.success(f"✅ **{total_archivos} archivo(s) listo(s) para análisis**")
        
        with col2:
            if st.button("🚀 Calcular Análisis", type="primary", use_container_width=True):
                st.session_state.mostrar_resultados = True
                st.rerun()

# 3. Mostrar resultados
if st.session_state.mostrar_resultados:
    st.markdown("---")
    vista_resultados()

# ==========================================
# BOTÓN DE REINICIO
# ==========================================

if st.session_state.archivos_procesados:
    st.markdown("---")
    if st.button("🔄 Nuevo Análisis", type="secondary", use_container_width=True):
        for key in ['archivos_procesados', 'periodos_asignados', 'mostrar_resultados']:
            if key in st.session_state:
                st.session_state[key] = {} if 'periodos' in key or 'archivos' in key else False
        st.rerun()

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
