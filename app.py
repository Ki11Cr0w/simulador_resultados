# app.py - VERSIÓN COMPLETA Y FINAL
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
# IMPORTAR MÓDULOS
# ==========================================

try:
    # Intentar importar los módulos UI
    from ui.vistas import vista_carga_multiple_archivos, vista_resumen_compacto, vista_resultados
    UI_DISPONIBLE = True
    
except ImportError as e:
    st.error(f"❌ Error importando módulos: {str(e)}")
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
    # Modo de emergencia si hay errores
    st.error("⚠️ **Error en la configuración de módulos**")
    st.info("Por favor verifica que los archivos en las carpetas 'core/' y 'ui/' existen y tienen el código correcto.")

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
    with st.expander("📋 **INSTRUCCIONES - Carga MÚLTIPLE de archivos**", expanded=True):
        st.markdown("""
        ### 🚀 **CÓMO USAR ESTE SIMULADOR:**
        
        **1. 📥 CARGA DE ARCHIVOS (ILIMITADOS):**
        - **Ventas:** Selecciona TODOS tus archivos de ventas (pueden ser varios a la vez)
        - **Compras:** Selecciona TODOS tus archivos de compras (pueden ser varios a la vez)
        - ✅ **Puedes seleccionar MÚLTIPLES archivos SIMULTÁNEAMENTE**
        
        **2. 📝 CONFIRMACIÓN DE PERÍODO:**
        - Para cada archivo, el sistema detectará automáticamente el período
        - Confirma o corrige el **AÑO** y **MES** correspondiente
        
        **3. 📊 ANÁLISIS FINAL:**
        - Revisa el resumen de todos los archivos cargados
        - Haz click en **"Calcular Análisis"** para ver resultados detallados
        
        ---
        
        **💡 CONSEJOS PRÁCTICOS:**
        - Puedes cargar **tantos archivos como necesites** (no hay límite de 3)
        - Usa **Ctrl/Cmd + click** para seleccionar archivos individuales
        - O **arrastra y suelta** para seleccionar varios a la vez
        - Cada archivo debe corresponder a un **mes específico** (ej: 2024-01, 2024-02, etc.)
        """)

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | Carga múltiple ilimitada | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
