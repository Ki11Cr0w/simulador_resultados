# ui/componentes.py
import streamlit as st
from datetime import datetime
from core.utils import formatear_monto

def mostrar_metricas_principales(totales):
    """Muestra métricas principales en formato vertical."""
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
    """Muestra tabla de resultados con formato."""
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
    """Crea uploaders en columnas para un tipo de archivo."""
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

def solicitar_confirmacion_periodo(año_pred, mes_pred, tipo, numero, archivo_nombre):
    """Solicita confirmación del año-mes al usuario."""
    st.write("---")
    st.write("**📝 CONFIRMAR AÑO-MES DEL ARCHIVO:**")
    
    col_año, col_mes = st.columns(2)
    
    with col_año:
        años_disponibles = list(range(2020, datetime.now().year + 2))
        año_default = año_pred if año_pred and año_pred in años_disponibles else datetime.now().year
        año_index = años_disponibles.index(año_default) if año_default in años_disponibles else len(años_disponibles)-1
        año_seleccionado = st.selectbox(
            f"Año para {tipo} {numero}:",
            años_disponibles,
            index=año_index,
            key=f"año_{tipo}_{numero}_{archivo_nombre}"
        )
    
    with col_mes:
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_default = mes_pred - 1 if mes_pred else 0
        mes_seleccionado = st.selectbox(
            f"Mes para {tipo} {numero}:",
            meses,
            index=mes_default,
            key=f"mes_{tipo}_{numero}_{archivo_nombre}"
        )
    
    return año_seleccionado, meses.index(mes_seleccionado) + 1

def mostrar_resumen_archivo(info_archivo, numero, tipo):
    """Muestra resumen de un archivo procesado."""
    porcentaje = (info_archivo['cantidad_predominante'] / info_archivo['documentos_count']) * 100
    
    st.success(f"✅ {tipo} {numero} procesado: {info_archivo['documentos_count']} documentos")
    st.write(f"**📅 Rango de fechas:** {info_archivo['fecha_minima'].strftime('%d/%m/%Y')} - {info_archivo['fecha_maxima'].strftime('%d/%m/%Y')}")
    st.write(f"**💰 Total archivo:** {formatear_monto(info_archivo['total_monto'])}")
    
    if info_archivo['año_predominante']:
        st.info(f"**🔍 DETECTADO:** {info_archivo['cantidad_predominante']} de {info_archivo['documentos_count']} documentos ({porcentaje:.0f}%) corresponden a **{info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d}**")
    
    return info_archivo['año_predominante'], info_archivo['mes_predominante']
