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

def mostrar_resumen_compacto(info_archivo, numero, tipo, archivo_nombre):
    """Muestra resumen COMPACTO de un archivo procesado (HORIZONTAL)."""
    # Crear un contenedor con borde
    with st.container():
        st.markdown(f"---")
        
        # PRIMERA LÍNEA: Información básica
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"**📄 {tipo} {numero}:** `{archivo_nombre[:30]}{'...' if len(archivo_nombre) > 30 else ''}`")
            st.markdown(f"📊 **{info_archivo['documentos_count']} documentos**")
        
        with col2:
            fecha_min = info_archivo['fecha_minima'].strftime('%d/%m')
            fecha_max = info_archivo['fecha_maxima'].strftime('%d/%m/%Y')
            st.markdown(f"📅 **Rango:** {fecha_min} - {fecha_max}")
            
            # Detección de período predominante
            if info_archivo['año_predominante']:
                porcentaje = (info_archivo['cantidad_predominante'] / info_archivo['documentos_count']) * 100
                st.markdown(f"🔍 **{info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d}** ({porcentaje:.0f}%)")
        
        with col3:
            st.markdown(f"💰 **Total:**")
            st.markdown(f"**{formatear_monto(info_archivo['total_monto'])}**")
        
        return info_archivo['año_predominante'], info_archivo['mes_predominante']

def solicitar_confirmacion_periodo_compacto(año_pred, mes_pred, tipo, numero, archivo_nombre):
    """Solicita confirmación del año-mes en formato COMPACTO."""
    # SEGUNDA LÍNEA: Confirmación de período
    with st.container():
        st.markdown("**📝 Confirmar período:**")
        
        # Crear columnas más ajustadas
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        
        with col1:
            st.markdown("Año:")
        
        with col2:
            años_disponibles = list(range(2020, datetime.now().year + 2))
            año_default = año_pred if año_pred and año_pred in años_disponibles else datetime.now().year
            año_index = años_disponibles.index(año_default) if año_default in años_disponibles else len(años_disponibles)-1
            año_seleccionado = st.selectbox(
                "Año",
                años_disponibles,
                index=año_index,
                key=f"año_compacto_{tipo}_{numero}_{archivo_nombre}",
                label_visibility="collapsed"
            )
        
        with col3:
            meses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            mes_default = mes_pred - 1 if mes_pred else 0
            mes_seleccionado = st.selectbox(
                "Mes",
                meses,
                index=mes_default,
                key=f"mes_compacto_{tipo}_{numero}_{archivo_nombre}",
                label_visibility="collapsed"
            )
        
        with col4:
            mes_numero = meses.index(mes_seleccionado) + 1
            st.success(f"✅ **{año_seleccionado}-{mes_numero:02d}**")
        
        return año_seleccionado, mes_numero

def procesar_archivo_compacto(archivo, tipo, numero):
    """Procesa y muestra un archivo en formato compacto."""
    from core import ProcesadorArchivos
    
    try:
        # Procesar archivo
        info_archivo = ProcesadorArchivos.procesar_archivo(archivo, tipo.lower())
        
        # Mostrar resumen compacto
        año_pred, mes_pred = mostrar_resumen_compacto(info_archivo, numero, tipo, archivo.name)
        
        # Solicitar confirmación compacta
        año_confirmado, mes_confirmado = solicitar_confirmacion_periodo_compacto(
            año_pred, mes_pred, tipo, numero, archivo.name
        )
        
        return {
            'info_archivo': info_archivo,
            'año_confirmado': año_confirmado,
            'mes_confirmado': mes_confirmado,
            'success': True
        }
        
    except Exception as e:
        # Mostrar error compacto
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.error(f"❌ **{tipo} {numero} - {archivo.name}:** {str(e)[:50]}...")
            with col2:
                with st.expander("Ver detalles"):
                    st.exception(e)
        
        return {'success': False, 'error': str(e)}
