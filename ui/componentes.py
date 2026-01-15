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

def crear_uploader_multiple(tipo):
    """Crea un uploader que acepta MÚLTIPLES archivos a la vez."""
    st.markdown(f"### 📋 Archivos de {tipo}")
    
    archivos = st.file_uploader(
        f"Selecciona uno o más archivos de {tipo.lower()}",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        key=f"{tipo.lower()}_uploader_multiple",
        help=f"Puedes seleccionar varios archivos de {tipo.lower()} a la vez. Máximo recomendado: 10 archivos."
    )
    
    return archivos

def mostrar_resumen_archivo_compacto(info_archivo, idx, tipo):
    """Muestra resumen COMPACTO de un archivo procesado."""
    # Crear contenedor con borde sutil
    with st.container():
        # PRIMERA LÍNEA: Información básica
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            nombre_corto = info_archivo['nombre_archivo'][:25]
            if len(info_archivo['nombre_archivo']) > 25:
                nombre_corto += "..."
            st.markdown(f"**{idx+1}. {nombre_corto}**")
            st.markdown(f"📄 **{info_archivo['documentos_count']} doc**")
        
        with col2:
            fecha_min = info_archivo['fecha_minima'].strftime('%d/%m')
            fecha_max = info_archivo['fecha_maxima'].strftime('%d/%m/%Y')
            st.markdown(f"📅 **{fecha_min} - {fecha_max}**")
        
        with col3:
            if info_archivo['año_predominante']:
                porcentaje = (info_archivo['cantidad_predominante'] / info_archivo['documentos_count']) * 100
                if porcentaje >= 50:
                    st.markdown(f"🔍 **{info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d}**")
                    st.markdown(f"*({porcentaje:.0f}% de los doc)*")
                else:
                    st.markdown(f"⚠️ **Varios períodos**")
                    st.markdown(f"*Pred: {info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d}*")
            else:
                st.markdown("❓ **Sin detección**")
        
        with col4:
            st.markdown(f"💰 **{formatear_monto(info_archivo['total_monto'])}**")
        
        return info_archivo['año_predominante'], info_archivo['mes_predominante']

def solicitar_confirmacion_periodo_compacto(año_pred, mes_pred, idx, nombre_archivo, tipo):
    """Solicita confirmación del año-mes en formato COMPACTO."""
    # SEGUNDA LÍNEA: Confirmación de período
    with st.container():
        col_a, col_b, col_c, col_d = st.columns([1, 2, 2, 1])
        
        with col_a:
            st.markdown("**Período:**")
        
        with col_b:
            años_disponibles = list(range(2020, datetime.now().year + 2))
            año_default = año_pred if año_pred and año_pred in años_disponibles else datetime.now().year
            año_index = años_disponibles.index(año_default) if año_default in años_disponibles else len(años_disponibles)-1
            
            año_seleccionado = st.selectbox(
                "Año",
                años_disponibles,
                index=año_index,
                key=f"año_{tipo}_{idx}_{nombre_archivo}",
                label_visibility="collapsed"
            )
        
        with col_c:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_default = mes_pred - 1 if mes_pred else 0
            
            mes_seleccionado = st.selectbox(
                "Mes",
                meses,
                index=mes_default,
                key=f"mes_{tipo}_{idx}_{nombre_archivo}",
                label_visibility="collapsed"
            )
        
        with col_d:
            mes_numero = meses.index(mes_seleccionado) + 1
            st.success(f"**{año_seleccionado}-{mes_numero:02d}**")
        
        return año_seleccionado, mes_numero

def procesar_lote_archivos(archivos, tipo):
    """Procesa un lote de archivos y devuelve resultados."""
    from core import ProcesadorArchivos
    
    resultados = []
    
    for idx, archivo in enumerate(archivos):
        # Verificar si ya fue procesado
        if archivo.name in st.session_state.archivos_procesados:
            st.info(f"⏭️ Archivo '{archivo.name[:20]}...' ya procesado")
            continue
        
        try:
            # Procesar archivo
            info_archivo = ProcesadorArchivos.procesar_archivo(archivo, tipo.lower())
            
            # Mostrar resumen compacto
            año_pred, mes_pred = mostrar_resumen_archivo_compacto(info_archivo, idx, tipo)
            
            # Solicitar confirmación
            año_confirmado, mes_confirmado = solicitar_confirmacion_periodo_compacto(
                año_pred, mes_pred, idx, archivo.name, tipo
            )
            
            resultados.append({
                'archivo': archivo,
                'info_archivo': info_archivo,
                'año_confirmado': año_confirmado,
                'mes_confirmado': mes_confirmado,
                'success': True
            })
            
        except Exception as e:
            # Mostrar error compacto
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.error(f"❌ **{tipo} {idx+1} - {archivo.name}:** {str(e)[:50]}")
                with col2:
                    with st.expander("Detalles"):
                        st.exception(e)
            
            resultados.append({
                'archivo': archivo,
                'success': False,
                'error': str(e)
            })
    
    return resultados
