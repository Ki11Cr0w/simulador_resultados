# ui/componentes.py
import streamlit as st
from datetime import datetime
from core.utils import formatear_monto

def mostrar_metricas_principales(totales):
    """Muestra métricas principales."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ventas Totales", formatear_monto(totales['ventas_totales']))
    
    with col2:
        st.metric("Compras Totales", formatear_monto(totales['compras_totales']))
    
    with col3:
        st.metric("Resultado Neto", formatear_monto(totales['resultado_total']))
    
    with col4:
        st.metric("Total Documentos", totales['documentos_totales'])

def mostrar_tabla_resultados(df_resultados):
    """Muestra tabla de resultados."""
    def aplicar_estilo(val):
        if isinstance(val, (int, float)) and val < 0:
            return 'color: #e74c3c; font-weight: bold;'
        elif isinstance(val, (int, float)) and val > 0:
            return 'color: #2ecc71; font-weight: bold;'
        return ''
    
    styled_df = df_resultados.style.format({
        'Ventas': lambda x: formatear_monto(x),
        'Compras': lambda x: formatear_monto(x),
        'Resultado': lambda x: formatear_monto(x),
        'Margen %': '{:+.1f}%'
    }).applymap(aplicar_estilo, subset=['Resultado', 'Margen %'])
    
    st.dataframe(styled_df, use_container_width=True)

def crear_uploader_columnas(tipo, max_archivos=3):
    """Crea uploaders en columnas."""
    cols = st.columns(max_archivos)
    archivos = []
    
    for i in range(max_archivos):
        with cols[i]:
            archivo = st.file_uploader(
                f"{tipo} {i+1}",
                type=["xlsx", "xls", "csv"],
                key=f"{tipo.lower()}_uploader_{i+1}"
            )
            if archivo:
                archivos.append((archivo, i+1))
    
    return archivos
