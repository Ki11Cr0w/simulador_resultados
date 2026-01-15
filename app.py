# app.py - VERSIÓN ROBUSTA
import streamlit as st
from datetime import datetime

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
# IMPORTAR MÓDULOS CON MANEJO DE ERRORES
# ==========================================

try:
    # Intentar importar los módulos UI
    from ui.vistas import vista_carga_multiple_archivos, vista_resumen_compacto, vista_resultados
    UI_DISPONIBLE = True
    
except ImportError as e:
    # Mostrar ayuda para diagnosticar el problema
    st.error(f"❌ Error importando módulos: {str(e)}")
    
    with st.expander("🔧 Ayuda para diagnosticar el problema"):
        st.write("""
        **Problema:** No se pueden importar los módulos de la interfaz.
        
        **Solución:**
        
        1. **Verifica que exista la carpeta `ui/`**
        2. **Dentro debe tener estos 3 archivos:**
           - `ui/__init__.py`
           - `ui/componentes.py`
           - `ui/vistas.py`
        
        3. **Contenido mínimo requerido:**
        
        **ui/__init__.py:**
        ```python
        from .vistas import vista_carga_multiple_archivos, vista_resumen_compacto, vista_resultados
        __all__ = ['vista_carga_multiple_archivos', 'vista_resumen_compacto', 'vista_resultados']
        ```
        
        **ui/componentes.py** y **ui/vistas.py** deben tener el código que te proporcioné.
        """)
    
    UI_DISPONIBLE = False

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

if UI_DISPONIBLE:
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
                st.success(f"✅ **{total_archivos} archivo(s) cargado(s)**")
            
            with col2:
                if st.button("🚀 Calcular Análisis", type="primary", use_container_width=True):
                    st.session_state.mostrar_resultados = True
                    st.rerun()
    
    # 3. Mostrar resultados si se solicitó
    if st.session_state.mostrar_resultados:
        st.markdown("---")
        vista_resultados()

else:
    # Modo de emergencia: interfaz básica
    st.warning("⚠️ **Modo de emergencia activado**")
    
    st.markdown("""
    La interfaz avanzada no está disponible, pero puedes usar esta versión básica.
    
    **Funcionalidades disponibles:**
    - Carga básica de archivos
    - Procesamiento simple
    """)
    
    # Uploaders básicos
    st.subheader("📥 Carga Básica de Archivos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Ventas")
        ventas_files = st.file_uploader(
            "Archivos de ventas",
            type=["xlsx", "csv"],
            accept_multiple_files=True,
            key="ventas_basico"
        )
    
    with col2:
        st.markdown("### Compras")
        compras_files = st.file_uploader(
            "Archivos de compras",
            type=["xlsx", "csv"],
            accept_multiple_files=True,
            key="compras_basico"
        )
    
    if ventas_files or compras_files:
        total_files = len(ventas_files) + len(compras_files)
        st.success(f"📦 **{total_files} archivo(s) seleccionado(s)**")

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
if not st.session_state.archivos_procesados and not st.session_state.mostrar_resultados and UI_DISPONIBLE:
    st.info("""
    👈 **Instrucciones:**
    
    1. **Ventas:** Selecciona uno o varios archivos de ventas
    2. **Compras:** Selecciona uno o varios archivos de compras  
    3. **Confirma** el período (año-mes) para cada archivo
    4. **Calcula** el análisis cuando todos estén listos
    """)

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
