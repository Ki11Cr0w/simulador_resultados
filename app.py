# app.py - VERSIÓN SIMPLIFICADA PARA PRUEBAS
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador", layout="wide")
st.title("📊 Simulador de Resultados")

# ==========================================
# ESTADO
# ==========================================

if 'archivos_procesados' not in st.session_state:
    st.session_state.archivos_procesados = {}
if 'periodos_asignados' not in st.session_state:
    st.session_state.periodos_asignados = {}
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False

# ==========================================
# FUNCIÓN TEMPORAL - Mientras arreglamos los imports
# ==========================================

def vista_carga_simple():
    """Vista simple mientras arreglamos imports."""
    st.subheader("📥 Carga de Archivos")
    
    # Uploaders básicos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        v1 = st.file_uploader("Ventas 1", type=["xlsx", "csv"])
    
    with col2:
        v2 = st.file_uploader("Ventas 2", type=["xlsx", "csv"])
    
    with col3:
        v3 = st.file_uploader("Ventas 3", type=["xlsx", "csv"])
    
    # Compras
    st.markdown("### Compras")
    col4, col5, col6 = st.columns(3)
    
    with col4:
        c1 = st.file_uploader("Compras 1", type=["xlsx", "csv"])
    
    with col5:
        c2 = st.file_uploader("Compras 2", type=["xlsx", "csv"])
    
    with col6:
        c3 = st.file_uploader("Compras 3", type=["xlsx", "csv"])

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

# Usar vista simple temporalmente
vista_carga_simple()

# Mostrar estado actual
if st.session_state.archivos_procesados:
    st.info(f"Archivos cargados: {len(st.session_state.archivos_procesados)}")

# Botón de prueba
if st.button("Probar"):
    st.success("✅ App funcionando")

# Pie de página
st.markdown("---")
st.caption(f"Versión de prueba | {datetime.now().strftime('%d/%m/%Y')}")
