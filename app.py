# app.py - CON MEJOR MANEJO DE ERRORES
import streamlit as st
from datetime import datetime
import traceback

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
# IMPORTAR MÓDULOS CON MANEJO DE ERRORES DETALLADO
# ==========================================

try:
    # Intentar importar módulos core primero
    from core import ProcesadorArchivos, CalculadoraResultados, formatear_monto
    CORE_DISPONIBLE = True
except ImportError as e:
    st.error(f"❌ Error importando módulos CORE: {str(e)}")
    CORE_DISPONIBLE = False
    with st.expander("🔍 Ver detalles del error CORE"):
        st.code(traceback.format_exc())

try:
    # Intentar importar módulos UI
    from ui.vistas import vista_carga_multiple_archivos, vista_resumen_compacto, vista_resultados
    UI_DISPONIBLE = True
except ImportError as e:
    st.error(f"❌ Error importando módulos UI: {str(e)}")
    UI_DISPONIBLE = False
    with st.expander("🔍 Ver detalles del error UI"):
        st.code(traceback.format_exc())

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

if CORE_DISPONIBLE and UI_DISPONIBLE:
    # 1. Cargar múltiples archivos
    vista_carga_multiple_archivos()
    
    # 2. Mostrar resumen si hay archivos
    if st.session_state.archivos_procesados:
        st.markdown("---")
        
        if vista_resumen_compacto():
            # Botón para calcular análisis
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                total_archivos = len(st.session_state.archivos_procesados)
                st.success(f"✅ **{total_archivos} archivo(s) cargado(s) y listo(s) para análisis**")
            
            with col2:
                if st.button("🚀 Calcular Análisis", type="primary", use_container_width=True):
                    st.session_state.mostrar_resultados = True
                    st.rerun()
    
    # 3. Mostrar resultados si se solicitó
    if st.session_state.mostrar_resultados:
        st.markdown("---")
        vista_resultados()

else:
    # Mostrar ayuda detallada
    st.error("⚠️ **Error en la configuración de módulos**")
    
    with st.expander("🛠️ Diagnóstico y solución"):
        st.markdown("""
        ### **PROBLEMA:** No se pueden importar los módulos necesarios.
        
        ### **SOLUCIÓN:**
        
        1. **Verifica que existan estas carpetas y archivos:**
        
        ```
        simulador_resultados/
        ├── app.py
        ├── validaciones.py
        ├── core/
        │   ├── __init__.py
        │   ├── utils.py
        │   ├── procesamiento.py
        │   └── calculos.py
        ├── ui/
        │   ├── __init__.py
        │   ├── componentes.py
        │   └── vistas.py
        ```
        
        2. **Contenido mínimo de `ui/__init__.py`:**
        ```python
        from .vistas import vista_carga_multiple_archivos
        from .vistas import vista_resumen_compacto
        from .vistas import vista_resultados
        
        __all__ = [
            'vista_carga_multiple_archivos',
            'vista_resumen_compacto',
            'vista_resultados'
        ]
        ```
        
        3. **Reinicia la aplicación** después de hacer los cambios.
        """)

# ==========================================
# BOTÓN DE REINICIO
# ==========================================

if st.session_state.archivos_procesados:
    st.markdown("---")
    
    if st.button("🔄 Iniciar Nuevo Análisis", type="secondary", use_container_width=True):
        # Limpiar estado
        for key in ['archivos_procesados', 'periodos_asignados', 'mostrar_resultados']:
            if key in st.session_state:
                st.session_state[key] = {} if 'periodos' in key or 'archivos' in key else False
        st.rerun()

# Mensaje inicial
if not st.session_state.archivos_procesados and not st.session_state.mostrar_resultados and CORE_DISPONIBLE and UI_DISPONIBLE:
    st.info("👇 **Comienza cargando tus archivos de ventas y compras**")

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
