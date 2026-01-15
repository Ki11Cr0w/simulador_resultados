# ui/vistas.py
import streamlit as st
import pandas as pd
from core import ProcesadorArchivos, CalculadoraResultados
from .componentes import (
    mostrar_metricas_principales,
    mostrar_tabla_resultados,
    crear_uploader_columnas
)

def vista_carga_archivos_compacta():
    """Vista para cargar archivos."""
    st.subheader("📥 Carga de Archivos")
    
    # Ventas
    st.markdown("### 📋 Archivos de Ventas")
    archivos_ventas = crear_uploader_columnas("Ventas", 3)
    
    for ventas_file, numero in archivos_ventas:
        if ventas_file.name in st.session_state.archivos_procesados:
            continue
        
        try:
            info_archivo = ProcesadorArchivos.procesar_archivo(ventas_file, "venta")
            
            # Mostrar info compacta
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**Venta {numero}:** {ventas_file.name[:20]}...")
                st.markdown(f"📊 {info_archivo['documentos_count']} documentos")
            
            with col2:
                fecha_min = info_archivo['fecha_minima'].strftime('%d/%m')
                fecha_max = info_archivo['fecha_maxima'].strftime('%d/%m/%Y')
                st.markdown(f"📅 {fecha_min} - {fecha_max}")
            
            with col3:
                from core.utils import formatear_monto
                st.markdown(f"**{formatear_monto(info_archivo['total_monto'])}**")
            
            # Confirmar período
            st.markdown("**Confirmar período:**")
            col_a, col_b, col_c = st.columns([1, 1, 1])
            
            with col_a:
                años = list(range(2020, 2025))
                año = st.selectbox("Año", años, key=f"año_v{numero}")
            
            with col_b:
                meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                mes = st.selectbox("Mes", meses, key=f"mes_v{numero}")
            
            with col_c:
                st.success(f"✅ {año}-{meses.index(mes)+1:02d}")
            
            # Guardar
            st.session_state.archivos_procesados[ventas_file.name] = info_archivo
            st.session_state.periodos_asignados[ventas_file.name] = f"{año}-{meses.index(mes)+1:02d}"
            
        except Exception as e:
            st.error(f"Error: {str(e)[:50]}")

def vista_resumen_compacto():
    """Vista de resumen."""
    if not st.session_state.archivos_procesados:
        return False
    
    st.markdown("### 📊 Resumen")
    return True

def vista_resultados():
    """Vista de resultados."""
    if not st.session_state.mostrar_resultados:
        return
    
    st.markdown("### 📈 Resultados")
