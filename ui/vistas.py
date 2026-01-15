# ui/vistas.py
import streamlit as st
import pandas as pd
from core import ProcesadorArchivos, CalculadoraResultados
from .componentes import (
    mostrar_metricas_principales,
    mostrar_tabla_resultados,
    crear_uploader_multiple,
    procesar_lote_archivos
)

def vista_carga_multiple_archivos():
    """Vista para cargar MÚLTIPLES archivos a la vez."""
    st.subheader("📥 Carga de Archivos Múltiple")
    
    # ==========================================
    # SECCIÓN VENTAS - MÚLTIPLES ARCHIVOS
    # ==========================================
    st.markdown("---")
    
    # Uploader para múltiples archivos de ventas
    archivos_ventas = crear_uploader_multiple("Ventas")
    
    if archivos_ventas:
        st.markdown(f"**📦 {len(archivos_ventas)} archivo(s) de ventas seleccionado(s)**")
        
        # Procesar lote de ventas
        resultados_ventas = procesar_lote_archivos(archivos_ventas, "Venta")
        
        # Guardar ventas exitosas
        for resultado in resultados_ventas:
            if resultado['success']:
                archivo = resultado['archivo']
                info_archivo = resultado['info_archivo']
                año_confirmado = resultado['año_confirmado']
                mes_confirmado = resultado['mes_confirmado']
                
                st.session_state.archivos_procesados[archivo.name] = info_archivo
                st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
    
    # ==========================================
    # SECCIÓN COMPRAS - MÚLTIPLES ARCHIVOS
    # ==========================================
    st.markdown("---")
    
    # Uploader para múltiples archivos de compras
    archivos_compras = crear_uploader_multiple("Compras")
    
    if archivos_compras:
        st.markdown(f"**📦 {len(archivos_compras)} archivo(s) de compras seleccionado(s)**")
        
        # Procesar lote de compras
        resultados_compras = procesar_lote_archivos(archivos_compras, "Compra")
        
        # Guardar compras exitosas
        for resultado in resultados_compras:
            if resultado['success']:
                archivo = resultado['archivo']
                info_archivo = resultado['info_archivo']
                año_confirmado = resultado['año_confirmado']
                mes_confirmado = resultado['mes_confirmado']
                
                st.session_state.archivos_procesados[archivo.name] = info_archivo
                st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"

def vista_resumen_compacto():
    """Vista de resumen de archivos cargados."""
    if not st.session_state.archivos_procesados:
        return False
    
    st.markdown("### 📊 Resumen de Archivos Cargados")
    
    # Separar por tipo
    archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                      if v['tipo_archivo'] == 'venta'}
    archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                       if v['tipo_archivo'] == 'compra'}
    
    from core.utils import formatear_monto
    
    # Mostrar en tabs para mejor organización
    tab1, tab2, tab3 = st.tabs([f"📥 Ventas ({len(archivos_ventas)})", 
                                f"📤 Compras ({len(archivos_compras)})", 
                                "📈 Totales"])
    
    with tab1:
        if archivos_ventas:
            for archivo, info in archivos_ventas.items():
                periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    nombre_corto = archivo[:30] + "..." if len(archivo) > 30 else archivo
                    st.markdown(f"**{nombre_corto}**")
                with col2:
                    st.markdown(f"`{periodo}`")
                with col3:
                    st.markdown(f"**{formatear_monto(info['total_monto'])}**")
                    st.markdown(f"*{info['documentos_count']} doc*")
        else:
            st.info("No hay archivos de ventas cargados")
    
    with tab2:
        if archivos_compras:
            for archivo, info in archivos_compras.items():
                periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    nombre_corto = archivo[:30] + "..." if len(archivo) > 30 else archivo
                    st.markdown(f"**{nombre_corto}**")
                with col2:
                    st.markdown(f"`{periodo}`")
                with col3:
                    st.markdown(f"**{formatear_monto(info['total_monto'])}**")
                    st.markdown(f"*{info['documentos_count']} doc*")
        else:
            st.info("No hay archivos de compras cargados")
    
    with tab3:
        # Calcular totales
        total_ventas = sum(info['total_monto'] for info in archivos_ventas.values())
        total_compras = sum(info['total_monto'] for info in archivos_compras.values())
        total_docs_ventas = sum(info['documentos_count'] for info in archivos_ventas.values())
        total_docs_compras = sum(info['documentos_count'] for info in archivos_compras.values())
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Ventas", formatear_monto(total_ventas), f"{total_docs_ventas} doc")
        
        with col2:
            st.metric("Compras", formatear_monto(total_compras), f"{total_docs_compras} doc")
        
        with col3:
            resultado = total_ventas - total_compras
            color = "normal" if resultado >= 0 else "inverse"
            st.metric("Resultado", formatear_monto(resultado), delta_color=color)
        
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
    
    # Estadísticas adicionales
    with st.expander("📊 Estadísticas Detalladas"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📝 Notas de crédito (tipo 61):**")
            st.write(f"- Ventas: {estadisticas['notas_credito_ventas']}")
            st.write(f"- Compras: {estadisticas['notas_credito_compras']}")
            st.write(f"- Total: {estadisticas['notas_credito_ventas'] + estadisticas['notas_credito_compras']}")
        
        with col2:
            from core.utils import formatear_monto
            st.write("**📊 Promedios:**")
            st.write(f"- Venta promedio: {formatear_monto(estadisticas['promedio_venta'])}")
            st.write(f"- Compra promedio: {formatear_monto(estadisticas['promedio_compra'])}")
