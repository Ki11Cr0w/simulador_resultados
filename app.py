# app.py - VERSIÓN CON CARGA MÚLTIPLE
import streamlit as st
from datetime import datetime

# Importar vistas
try:
    from ui import vista_carga_multiple_archivos, vista_resumen_compacto, vista_resultados
    UI_DISPONIBLE = True
except ImportError as e:
    st.error(f"❌ Error importando módulos UI: {str(e)}")
    UI_DISPONIBLE = False

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
# FLUJO PRINCIPAL
# ==========================================

if not UI_DISPONIBLE:
    st.error("""
    ⚠️ **Error de configuración**
    
    Faltan los módulos de interfaz. Por favor asegúrate de que:
    1. Existe la carpeta `ui/`
    2. Dentro tiene: `__init__.py`, `componentes.py`, `vistas.py`
    3. Los archivos tienen el código correcto
    """)
    st.stop()

# 1. Cargar múltiples archivos
vista_carga_multiple_archivos()

# 2. Mostrar resumen si hay archivos
if st.session_state.archivos_procesados:
    st.markdown("---")
    
    if vista_resumen_compacto():
        # Botón para calcular análisis
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            total_archivos = len(st.session_state.archivos_procesados)
            st.success(f"✅ **{total_archivos} archivo(s) listo(s) para análisis**")
        
        with col2:
            if st.button("📊 Ver Resumen", type="secondary", use_container_width=True):
                st.info("Mostrando resumen actual")
        
        with col3:
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
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**¿Deseas realizar otro análisis?**")
    
    with col2:
        if st.button("🔄 Nuevo Análisis", type="secondary", use_container_width=True):
            # Limpiar estado
            for key in ['archivos_procesados', 'periodos_asignados', 'mostrar_resultados']:
                if key in st.session_state:
                    st.session_state[key] = {} if 'periodos' in key or 'archivos' in key else False
            st.rerun()

# Mensaje inicial
if not st.session_state.archivos_procesados and not st.session_state.mostrar_resultados:
    st.info("""
    👈 **Instrucciones:**
    
    1. **Ventas:** Selecciona uno o varios archivos de ventas
    2. **Compras:** Selecciona uno o varios archivos de compras  
    3. **Confirma** el período (año-mes) para cada archivo
    4. **Calcula** el análisis cuando todos estén listos
    """)

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | Carga múltiple | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
