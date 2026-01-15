# app.py - INTERFAZ PRINCIPAL (Streamlit)
import streamlit as st
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

def solicitar_confirmacion_periodo(año_pred, mes_pred, tipo, numero):
    """Solicita confirmación del año-mes al usuario."""
    st.write("---")
    st.write("**📝 CONFIRMAR AÑO-MES DEL ARCHIVO:**")
    
    col_año, col_mes = st.columns(2)
    
    with col_año:
        años_disponibles = list(range(2020, datetime.now().year + 2))
        año_default = año_pred if año_pred in años_disponibles else datetime.now().year
        año_seleccionado = st.selectbox(
            f"Año para {tipo} {numero}:",
            años_disponibles,
            index=años_disponibles.index(año_default) if año_default in años_disponibles else len(años_disponibles)-1,
            key=f"año_{tipo}_{numero}"
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
            key=f"mes_{tipo}_{numero}"
        )
    
    mes_numero = meses.index(mes_seleccionado) + 1
    return año_seleccionado, mes_numero

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

st.subheader("📥 Carga de Archivos")

# SECCIÓN VENTAS
st.markdown("### 📋 Archivos de Ventas")
ventas_cols = st.columns(3)
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
                st.markdown(f"---")
                st.markdown(f"#### 📄 Procesando: Ventas {i+1} - {ventas_file.name}")
                
                # Procesar archivo
                info_archivo = ProcesadorArchivos.procesar_archivo(ventas_file, "venta")
                
                # Mostrar resumen
                año_pred, mes_pred = mostrar_resumen_archivo(info_archivo, i+1, "Ventas")
                
                # Solicitar confirmación
                año_confirmado, mes_confirmado = solicitar_confirmacion_periodo(
                    año_pred, mes_pred, "venta", i+1
                )
                
                # Guardar en estado
                st.session_state.archivos_procesados[ventas_file.name] = info_archivo
                st.session_state.periodos_asignados[ventas_file.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                
                st.success(f"**✅ PERÍODO CONFIRMADO:** {año_confirmado}-{mes_confirmado:02d}")
                ventas_procesadas.append(info_archivo)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# SECCIÓN COMPRAS (similar a ventas)
# ... (código similar omitido por brevedad)

# ==========================================
# RESUMEN Y CÁLCULOS
# ==========================================

if st.session_state.archivos_procesados:
    # Recolectar todos los documentos
    todos_documentos = []
    for info in st.session_state.archivos_procesados.values():
        for doc in info['documentos']:
            # Asignar período del archivo a cada documento
            periodo = st.session_state.periodos_asignados.get(doc['archivo_origen'], "Sin_periodo")
            doc['periodo_asignado'] = periodo
            todos_documentos.append(doc)
    
    # Mostrar resumen
    st.markdown("---")
    st.markdown("### 📊 RESUMEN DE ARCHIVOS")
    
    for archivo, info in st.session_state.archivos_procesados.items():
        periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
        tipo_icon = "📥" if info['tipo_archivo'] == 'venta' else "📤"
        st.write(f"{tipo_icon} **{archivo}** | {periodo} | {info['documentos_count']} doc | {formatear_monto(info['total_monto'])}")
    
    # Botón para calcular
    if st.button("🚀 CALCULAR RESULTADOS", type="primary", use_container_width=True):
        st.session_state.mostrar_resultados = True
        st.rerun()

# ==========================================
# MOSTRAR RESULTADOS
# ==========================================

if st.session_state.mostrar_resultados and st.session_state.archivos_procesados:
    # Usar CalculadoraResultados
    resumen_periodos = CalculadoraResultados.agrupar_por_periodo(
        todos_documentos, 
        st.session_state.periodos_asignados
    )
    
    totales = CalculadoraResultados.calcular_totales(resumen_periodos)
    datos_tabla = CalculadoraResultados.generar_dataframe_resultados(resumen_periodos)
    estadisticas = CalculadoraResultados.calcular_estadisticas(todos_documentos)
    
    # Mostrar resultados (código de interfaz similar al anterior)
    # ... (se mantiene la lógica de visualización)

# ==========================================
# BOTÓN DE REINICIO
# ==========================================

if st.session_state.archivos_procesados:
    if st.button("🔄 NUEVO ANÁLISIS", type="secondary"):
        for key in ['archivos_procesados', 'periodos_asignados', 'mostrar_resultados']:
            if key in st.session_state:
                st.session_state[key] = {} if 'periodos' in key or 'archivos' in key else False
        st.rerun()

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
