# app.py - INTERFAZ PRINCIPAL (Streamlit)
import streamlit as st
from datetime import datetime

# Importar vistas
from ui import vista_carga_archivos, vista_resumen, vista_resultados

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="centered")
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
# FLUJO PRINCIPAL
# ==========================================

# 1. Cargar archivos
vista_carga_archivos()

# 2. Mostrar resumen si hay archivos
if st.session_state.archivos_procesados:
    st.markdown("---")
    
    if vista_resumen():
        # Calcular totales para el botón
        archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                          if v['tipo_archivo'] == 'venta'}
        archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                           if v['tipo_archivo'] == 'compra'}
        
        total_ventas = sum(info['total_monto'] for info in archivos_ventas.values())
        total_compras = sum(info['total_monto'] for info in archivos_compras.values())
        
        from core.utils import formatear_monto
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📥 VENTAS TOTALES**")
            st.markdown(f"<h3 style='color: #2ecc71;'>{formatear_monto(total_ventas)}</h3>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("**📤 COMPRAS TOTALES**")
            st.markdown(f"<h3 style='color: #e74c3c;'>{formatear_monto(total_compras)}</h3>", unsafe_allow_html=True)
        
        # Botón para calcular
        if st.button("🚀 CALCULAR ANÁLISIS DETALLADO", type="primary", use_container_width=True):
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
    
    if st.button("🔄 INICIAR NUEVO ANÁLISIS", type="secondary", use_container_width=True):
        for key in ['archivos_procesados', 'periodos_asignados', 'mostrar_resultados']:
            if key in st.session_state:
                st.session_state[key] = {} if 'periodos' in key or 'archivos' in key else False
        st.rerun()

# Mensaje inicial
if not st.session_state.archivos_procesados and not st.session_state.mostrar_resultados:
    st.info("👈 Comienza cargando archivos de ventas y compras")

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
