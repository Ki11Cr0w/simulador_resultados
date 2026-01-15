# ui/vistas.py
import streamlit as st
import pandas as pd
from core import ProcesadorArchivos, CalculadoraResultados
from .componentes import (
    mostrar_resumen_compacto, solicitar_confirmacion_periodo_compacto,
    mostrar_metricas_principales, mostrar_tabla_resultados,
    crear_uploader_columnas, procesar_archivo_compacto
)

def vista_carga_archivos_compacta():
    """Vista para cargar archivos en formato COMPACTO."""
    st.subheader("📥 Carga de Archivos")
    
    # ==========================================
    # SECCIÓN VENTAS (COMPACTA)
    # ==========================================
    st.markdown("### 📋 Archivos de Ventas")
    
    # Crear 3 uploaders en una línea
    archivos_ventas = crear_uploader_columnas("Ventas", 3)
    
    # Procesar cada archivo de ventas
    for ventas_file, numero in archivos_ventas:
        if ventas_file.name in st.session_state.archivos_procesados:
            continue
        
        # Procesar en formato compacto
        resultado = procesar_archivo_compacto(ventas_file, "Venta", numero)
        
        if resultado['success']:
            info_archivo = resultado['info_archivo']
            año_confirmado = resultado['año_confirmado']
            mes_confirmado = resultado['mes_confirmado']
            
            # Guardar en estado
            st.session_state.archivos_procesados[ventas_file.name] = info_archivo
            st.session_state.periodos_asignados[ventas_file.name] = f"{año_confirmado}-{mes_confirmado:02d}"
    
    # ==========================================
    # SECCIÓN COMPRAS (COMPACTA)
    # ==========================================
    st.markdown("### 📋 Archivos de Compras")
    
    # Crear 3 uploaders en una línea
    archivos_compras = crear_uploader_columnas("Compras", 3)
    
    # Procesar cada archivo de compras
    for compras_file, numero in archivos_compras:
        if compras_file.name in st.session_state.archivos_procesados:
            continue
        
        # Procesar en formato compacto
        resultado = procesar_archivo_compacto(compras_file, "Compra", numero)
        
        if resultado['success']:
            info_archivo = resultado['info_archivo']
            año_confirmado = resultado['año_confirmado']
            mes_confirmado = resultado['mes_confirmado']
            
            # Guardar en estado
            st.session_state.archivos_procesados[compras_file.name] = info_archivo
            st.session_state.periodos_asignados[compras_file.name] = f"{año_confirmado}-{mes_confirmado:02d}"

def vista_resumen_compacto():
    """Vista de resumen de archivos cargados en formato COMPACTO."""
    if not st.session_state.archivos_procesados:
        return False
    
    st.markdown("### 📊 Resumen de Archivos")
    
    # Usar columnas para mostrar resumen compacto
    archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                      if v['tipo_archivo'] == 'venta'}
    archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                       if v['tipo_archivo'] == 'compra'}
    
    from core.utils import formatear_monto
    
    # Mostrar en tabs para mejor organización
    tab1, tab2, tab3 = st.tabs(["📥 Ventas", "📤 Compras", "📈 Totales"])
    
    with tab1:
        if archivos_ventas:
            for archivo, info in archivos_ventas.items():
                periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{archivo[:25]}{'...' if len(archivo) > 25 else ''}**")
                with col2:
                    st.markdown(f"`{periodo}`")
                with col3:
                    st.markdown(f"**{formatear_monto(info['total_monto'])}**")
        else:
            st.info("No hay archivos de ventas cargados")
    
    with tab2:
        if archivos_compras:
            for archivo, info in archivos_compras.items():
                periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{archivo[:25]}{'...' if len(archivo) > 25 else ''}**")
                with col2:
                    st.markdown(f"`{periodo}`")
                with col3:
                    st.markdown(f"**{formatear_monto(info['total_monto'])}**")
        else:
            st.info("No hay archivos de compras cargados")
    
    with tab3:
        # Calcular totales
        total_ventas = sum(info['total_monto'] for info in archivos_ventas.values())
        total_compras = sum(info['total_monto'] for info in archivos_compras.values())
        total_docs_ventas = sum(info['documentos_count'] for info in archivos_ventas.values())
        total_docs_compras = sum(info['documentos_count'] for info in archivos_compras.values())
        
        # Mostrar en columnas compactas
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
    """Vista de resultados detallados."""
    if not st.session_state.mostrar_resultados:
        return
    
    # Recolectar todos los documentos
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
    
    # Mostrar resultados
    st.subheader("📊 Análisis por Período")
    df_resultados = pd.DataFrame(datos_tabla)
    mostrar_tabla_resultados(df_resultados)
    
    # Métricas principales
    st.markdown("---")
    st.markdown("### 📈 Resumen Final")
    mostrar_metricas_principales(totales)
    
    # Estadísticas adicionales en tabs
    with st.expander("📊 Estadísticas Detalladas"):
        tab1, tab2 = st.tabs(["📝 Notas de Crédito", "📊 Promedios"])
        
        with tab1:
            st.write(f"**Ventas (tipo 61):** {estadisticas['notas_credito_ventas']}")
            st.write(f"**Compras (tipo 61):** {estadisticas['notas_credito_compras']}")
            st.write(f"**Total notas crédito:** {estadisticas['notas_credito_ventas'] + estadisticas['notas_credito_compras']}")
        
        with tab2:
            from core.utils import formatear_monto
            st.write(f"**Venta promedio:** {formatear_monto(estadisticas['promedio_venta'])}")
            st.write(f"**Compra promedio:** {formatear_monto(estadisticas['promedio_compra'])}")
            st.write(f"**Total ventas:** {estadisticas['total_ventas_count']} documentos")
            st.write(f"**Total compras:** {estadisticas['total_compras_count']} documentos")
