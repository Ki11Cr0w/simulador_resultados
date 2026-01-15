# ui/vistas.py
import streamlit as st
import pandas as pd
from core import ProcesadorArchivos, CalculadoraResultados
from .componentes import (
    mostrar_resumen_archivo, solicitar_confirmacion_periodo,
    mostrar_metricas_principales, mostrar_tabla_resultados,
    crear_uploader_columnas
)

def vista_carga_archivos():
    """Vista para cargar archivos."""
    st.subheader("📥 Carga de Archivos")
    
    # Ventas
    st.markdown("### 📋 Archivos de Ventas (máximo 3)")
    archivos_ventas = crear_uploader_columnas("Ventas", 3)
    
    ventas_procesadas = []
    for ventas_file, numero in archivos_ventas:
        if ventas_file.name in st.session_state.archivos_procesados:
            continue
            
        st.markdown(f"---")
        st.markdown(f"#### 📄 Procesando: Ventas {numero} - {ventas_file.name}")
        
        try:
            info_archivo = ProcesadorArchivos.procesar_archivo(ventas_file, "venta")
            año_pred, mes_pred = mostrar_resumen_archivo(info_archivo, numero, "Ventas")
            año_confirmado, mes_confirmado = solicitar_confirmacion_periodo(
                año_pred, mes_pred, "venta", numero, ventas_file.name
            )
            
            st.session_state.archivos_procesados[ventas_file.name] = info_archivo
            st.session_state.periodos_asignados[ventas_file.name] = f"{año_confirmado}-{mes_confirmado:02d}"
            st.success(f"**✅ PERÍODO CONFIRMADO:** {año_confirmado}-{mes_confirmado:02d}")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Compras
    st.markdown("### 📋 Archivos de Compras (máximo 3)")
    archivos_compras = crear_uploader_columnas("Compras", 3)
    
    for compras_file, numero in archivos_compras:
        if compras_file.name in st.session_state.archivos_procesados:
            continue
            
        st.markdown(f"---")
        st.markdown(f"#### 📄 Procesando: Compras {numero} - {compras_file.name}")
        
        try:
            info_archivo = ProcesadorArchivos.procesar_archivo(compras_file, "compra")
            año_pred, mes_pred = mostrar_resumen_archivo(info_archivo, numero, "Compras")
            año_confirmado, mes_confirmado = solicitar_confirmacion_periodo(
                año_pred, mes_pred, "compra", numero, compras_file.name
            )
            
            st.session_state.archivos_procesados[compras_file.name] = info_archivo
            st.session_state.periodos_asignados[compras_file.name] = f"{año_confirmado}-{mes_confirmado:02d}"
            st.success(f"**✅ PERÍODO CONFIRMADO:** {año_confirmado}-{mes_confirmado:02d}")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def vista_resumen():
    """Vista de resumen de archivos cargados."""
    if not st.session_state.archivos_procesados:
        return False
    
    st.markdown("### 📊 RESUMEN DE ARCHIVOS CARGADOS")
    
    # Separar por tipo
    archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                      if v['tipo_archivo'] == 'venta'}
    archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                       if v['tipo_archivo'] == 'compra'}
    
    from core.utils import formatear_monto
    
    # Mostrar ventas
    if archivos_ventas:
        st.markdown("#### 📥 Archivos de Ventas")
        for archivo, info in archivos_ventas.items():
            periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
            st.write(f"• **{archivo}** | {periodo} | {info['documentos_count']} doc | {formatear_monto(info['total_monto'])}")
    
    # Mostrar compras
    if archivos_compras:
        st.markdown("#### 📤 Archivos de Compras")
        for archivo, info in archivos_compras.items():
            periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
            st.write(f"• **{archivo}** | {periodo} | {info['documentos_count']} doc | {formatear_monto(info['total_monto'])}")
    
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
    st.subheader("📊 ANÁLISIS DETALLADO POR PERÍODO")
    df_resultados = pd.DataFrame(datos_tabla)
    mostrar_tabla_resultados(df_resultados)
    
    # Métricas principales
    st.markdown("---")
    st.markdown("### 📈 RESUMEN FINAL")
    mostrar_metricas_principales(totales)
    
    # Estadísticas adicionales
    with st.expander("📊 ESTADÍSTICAS ADICIONALES"):
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
