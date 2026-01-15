# app.py - VERSIÓN FINAL COMPACTA
import streamlit as st
from datetime import datetime

# Importar vistas compactas
from ui import vista_carga_archivos_compacta, vista_resumen_compacto, vista_resultados

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
# FLUJO PRINCIPAL COMPACTO
# ==========================================

# 1. Cargar archivos (formato compacto)
vista_carga_archivos_compacta()

# 2. Mostrar resumen compacto si hay archivos
if st.session_state.archivos_procesados:
    st.markdown("---")
    
    if vista_resumen_compacto():
        # Botón para calcular análisis
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("**¿Listo para analizar los datos?**")
        
        with col2:
            if st.button("🚀 Calcular Análisis", type="primary", use_container_width=True):
                st.session_state.mostrar_resultados = True
                st.rerun()

# 3. Mostrar resultados si se solicitó
if st.session_state.mostrar_resultados:
    st.markdown("---")
    vista_resultados()

# ==========================================
# BOTÓN DE REINICIO
# ==========================================

if st.session_state.archivos_procesados:
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    
    with col2:
        if st.button("🔄 Nuevo Análisis", type="secondary", use_container_width=True):
            for key in ['archivos_procesados', 'periodos_asignados', 'mostrar_resultados']:
                if key in st.session_state:
                    st.session_state[key] = {} if 'periodos' in key or 'archivos' in key else False
            st.rerun()

# Mensaje inicial
if not st.session_state.archivos_procesados and not st.session_state.mostrar_resultados:
    st.info("👈 Comienza cargando archivos de ventas y compras. Para cada archivo, confirma el año-mes correspondiente.")

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
