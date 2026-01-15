# app.py - VERSIÓN CORREGIDA Y COMPLETA
import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime

# Importar módulos propios
from validaciones import validar_ventas_sii, validar_compras_sii
from core import ProcesadorArchivos, CalculadoraResultados, formatear_monto

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
# FUNCIONES DE INTERFAZ
# ==========================================

def mostrar_resumen_archivo(info_archivo, numero, tipo):
    """Muestra resumen de un archivo procesado."""
    porcentaje = (info_archivo['cantidad_predominante'] / info_archivo['documentos_count']) * 100
    
    st.success(f"✅ {tipo} {numero} procesado: {info_archivo['documentos_count']} documentos")
    st.write(f"**📅 Rango de fechas:** {info_archivo['fecha_minima'].strftime('%d/%m/%Y')} - {info_archivo['fecha_maxima'].strftime('%d/%m/%Y')}")
    st.write(f"**💰 Total archivo:** {formatear_monto(info_archivo['total_monto'])}")
    
    if info_archivo['año_predominante']:
        st.info(f"**🔍 DETECTADO:** {info_archivo['cantidad_predominante']} de {info_archivo['documentos_count']} documentos ({porcentaje:.0f}%) corresponden a **{info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d}**")
    
    return info_archivo['año_predominante'], info_archivo['mes_predominante']

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
    
    mes_numero = meses.index(mes_seleccionado) + 1
    return año_seleccionado, mes_numero

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

st.subheader("📥 Carga de Archivos")

# SECCIÓN VENTAS
st.markdown("### 📋 Archivos de Ventas (máximo 3)")
ventas_cols = st.columns(3)

# Lista para almacenar archivos de ventas procesados
ventas_procesadas = []

for i in range(3):
    with ventas_cols[i]:
        ventas_file = st.file_uploader(
            f"Ventas {i+1}",
            type=["xlsx", "xls", "csv"],
            key=f"ventas_uploader_{i+1}"
        )
        if ventas_file:
            try:
                # Verificar si ya fue procesado
                if ventas_file.name in st.session_state.archivos_procesados:
                    st.info(f"✅ Archivo ya procesado")
                    continue
                
                st.markdown(f"---")
                st.markdown(f"#### 📄 Procesando: Ventas {i+1} - {ventas_file.name}")
                
                # Procesar archivo
                info_archivo = ProcesadorArchivos.procesar_archivo(ventas_file, "venta")
                
                # Mostrar resumen
                año_pred, mes_pred = mostrar_resumen_archivo(info_archivo, i+1, "Ventas")
                
                # Solicitar confirmación
                año_confirmado, mes_confirmado = solicitar_confirmacion_periodo(
                    año_pred, mes_pred, "venta", i+1, ventas_file.name
                )
                
                # Guardar en estado
                st.session_state.archivos_procesados[ventas_file.name] = info_archivo
                st.session_state.periodos_asignados[ventas_file.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                
                st.success(f"**✅ PERÍODO CONFIRMADO:** {año_confirmado}-{mes_confirmado:02d}")
                ventas_procesadas.append(info_archivo)
                
            except Exception as e:
                st.error(f"❌ Error procesando Ventas {i+1}: {str(e)}")

# SECCIÓN COMPRAS
st.markdown("### 📋 Archivos de Compras (máximo 3)")
compras_cols = st.columns(3)

# Lista para almacenar archivos de compras procesados
compras_procesadas = []

for i in range(3):
    with compras_cols[i]:
        compras_file = st.file_uploader(
            f"Compras {i+1}",
            type=["xlsx", "xls", "csv"],
            key=f"compras_uploader_{i+1}"
        )
        if compras_file:
            try:
                # Verificar si ya fue procesado
                if compras_file.name in st.session_state.archivos_procesados:
                    st.info(f"✅ Archivo ya procesado")
                    continue
                
                st.markdown(f"---")
                st.markdown(f"#### 📄 Procesando: Compras {i+1} - {compras_file.name}")
                
                # Procesar archivo
                info_archivo = ProcesadorArchivos.procesar_archivo(compras_file, "compra")
                
                # Mostrar resumen
                año_pred, mes_pred = mostrar_resumen_archivo(info_archivo, i+1, "Compras")
                
                # Solicitar confirmación
                año_confirmado, mes_confirmado = solicitar_confirmacion_periodo(
                    año_pred, mes_pred, "compra", i+1, compras_file.name
                )
                
                # Guardar en estado
                st.session_state.archivos_procesados[compras_file.name] = info_archivo
                st.session_state.periodos_asignados[compras_file.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                
                st.success(f"**✅ PERÍODO CONFIRMADO:** {año_confirmado}-{mes_confirmado:02d}")
                compras_procesadas.append(info_archivo)
                
            except Exception as e:
                st.error(f"❌ Error procesando Compras {i+1}: {str(e)}")

# ==========================================
# RESUMEN Y CÁLCULOS
# ==========================================

if st.session_state.archivos_procesados:
    st.markdown("---")
    st.markdown("### 📊 RESUMEN DE ARCHIVOS CARGADOS")
    
    # Separar por tipo
    archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                      if v['tipo_archivo'] == 'venta'}
    archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                       if v['tipo_archivo'] == 'compra'}
    
    # Mostrar ventas
    if archivos_ventas:
        st.markdown("#### 📥 Archivos de Ventas")
        for archivo, info in archivos_ventas.items():
            periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
            st.write(f"• **{archivo}** | {periodo} | {info['documentos_count']} doc | {formatear_monto(info['total_monto'])}")
    
    # Mostrar compras
    if archivos_compras:
        st.markdown("#### 📤 Archivos de Compras")
        for archivo, info in archivos_compras.items():
            periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
            st.write(f"• **{archivo}** | {periodo} | {info['documentos_count']} doc | {formatear_monto(info['total_monto'])}")
    
    # Calcular totales
    total_ventas = sum(info['total_monto'] for info in archivos_ventas.values())
    total_compras = sum(info['total_monto'] for info in archivos_compras.values())
    total_docs_ventas = sum(info['documentos_count'] for info in archivos_ventas.values())
    total_docs_compras = sum(info['documentos_count'] for info in archivos_compras.values())
    
    # Mostrar métricas
    st.markdown("---")
    st.markdown("### 🎯 TOTALES ACUMULADOS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📥 VENTAS**")
        st.markdown(f"<h3 style='color: #2ecc71;'>{formatear_monto(total_ventas)}</h3>", 
                   unsafe_allow_html=True)
        st.write(f"{total_docs_ventas} documentos")
    
    with col2:
        st.markdown("**📤 COMPRAS**")
        st.markdown(f"<h3 style='color: #e74c3c;'>{formatear_monto(total_compras)}</h3>", 
                   unsafe_allow_html=True)
        st.write(f"{total_docs_compras} documentos")
    
    with col3:
        st.markdown("**💰 RESULTADO**")
        resultado = total_ventas - total_compras
        color = "#2ecc71" if resultado >= 0 else "#e74c3c"
        st.markdown(f"<h3 style='color: {color};'>{formatear_monto(resultado)}</h3>", 
                   unsafe_allow_html=True)
        st.write(f"{total_docs_ventas + total_docs_compras} documentos totales")
    
    # Botón para calcular análisis detallado
    st.markdown("---")
    
    if st.button("🚀 CALCULAR ANÁLISIS DETALLADO", type="primary", use_container_width=True):
        st.session_state.mostrar_resultados = True
        st.rerun()

# ==========================================
# MOSTRAR RESULTADOS DETALLADOS
# ==========================================

if st.session_state.mostrar_resultados and st.session_state.archivos_procesados:
    # Recolectar todos los documentos
    todos_documentos = []
    for info in st.session_state.archivos_procesados.values():
        for doc in info['documentos']:
            # Asignar período del archivo a cada documento
            periodo = st.session_state.periodos_asignados.get(doc['archivo_origen'], "Sin_periodo")
            doc['periodo_asignado'] = periodo
            todos_documentos.append(doc)
    
    # Usar CalculadoraResultados
    resumen_periodos = CalculadoraResultados.agrupar_por_periodo(
        todos_documentos, 
        st.session_state.periodos_asignados
    )
    
    totales = CalculadoraResultados.calcular_totales(resumen_periodos)
    datos_tabla = CalculadoraResultados.generar_dataframe_resultados(resumen_periodos)
    estadisticas = CalculadoraResultados.calcular_estadisticas(todos_documentos)
    
    # Mostrar resultados
    st.markdown("---")
    st.subheader("📊 ANÁLISIS DETALLADO POR PERÍODO")
    
    # Crear DataFrame
    df_resultados = pd.DataFrame(datos_tabla)
    
    # Función para aplicar estilos
    def aplicar_estilo(val):
        if isinstance(val, (int, float)) and val < 0:
            return 'color: #e74c3c; font-weight: bold;'
        elif isinstance(val, (int, float)) and val > 0:
            return 'color: #2ecc71; font-weight: bold;'
        return ''
    
    # Formatear tabla
    styled_df = df_resultados.style.format({
        'Ventas': lambda x: formatear_monto(x),
        'Compras': lambda x: formatear_monto(x),
        'Resultado': lambda x: formatear_monto(x),
        'Margen %': '{:+.1f}%'
    }).applymap(aplicar_estilo, subset=['Resultado', 'Margen %'])
    
    st.dataframe(styled_df, use_container_width=True)
    
    # Mostrar métricas finales
    st.markdown("---")
    st.markdown("### 📈 RESUMEN FINAL")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ventas Totales", formatear_monto(totales['ventas_totales']))
    
    with col2:
        st.metric("Compras Totales", formatear_monto(totales['compras_totales']))
    
    with col3:
        st.metric("Resultado Neto", formatear_monto(totales['resultado_total']))
    
    with col4:
        st.metric("Total Documentos", totales['documentos_totales'])
    
    # Estadísticas adicionales
    with st.expander("📊 ESTADÍSTICAS ADICIONALES"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📝 Notas de crédito (tipo 61):**")
            st.write(f"- Ventas: {estadisticas['notas_credito_ventas']}")
            st.write(f"- Compras: {estadisticas['notas_credito_compras']}")
            st.write(f"- Total: {estadisticas['notas_credito_ventas'] + estadisticas['notas_credito_compras']}")
        
        with col2:
            st.write("**📊 Promedios:**")
            st.write(f"- Venta promedio: {formatear_monto(estadisticas['promedio_venta'])}")
            st.write(f"- Compra promedio: {formatear_monto(estadisticas['promedio_compra'])}")
            st.write(f"- Total ventas: {estadisticas['total_ventas_count']} documentos")
            st.write(f"- Total compras: {estadisticas['total_compras_count']} documentos")

# ==========================================
# BOTÓN DE REINICIO
# ==========================================

if st.session_state.archivos_procesados:
    st.markdown("---")
    
    if st.button("🔄 INICIAR NUEVO ANÁLISIS", type="secondary", use_container_width=True):
        # Limpiar estado
        for key in ['archivos_procesados', 'periodos_asignados', 'mostrar_resultados']:
            if key in st.session_state:
                st.session_state[key] = {} if 'periodos' in key or 'archivos' in key else False
        st.rerun()

# Mensaje inicial
if not st.session_state.archivos_procesados and not st.session_state.mostrar_resultados:
    st.info("👈 Comienza cargando archivos de ventas y compras. Para cada archivo, confirma el año-mes correspondiente.")

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
