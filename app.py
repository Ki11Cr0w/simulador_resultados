# ==========================================
# APP.PY - VERSIÓN CON MÚLTIPLES ARCHIVOS Y CONFIRMACIÓN DE PERÍODO
# ==========================================

import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np

from validaciones import validar_ventas_sii, validar_compras_sii

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="centered")
st.title("📊 Simulador de Resultados")

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def normalizar_columnas(df):
    """Normaliza nombres de columnas."""
    df = df.copy()
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
        .str.replace('.', '', regex=False)
    )
    return df


def _parsear_fecha(fecha_str):
    """Convierte string de fecha a objeto datetime de forma segura."""
    if pd.isna(fecha_str) or fecha_str in ['', 'nan', 'NaT', 'None']:
        return None
    
    fecha_str = str(fecha_str).strip()
    
    formatos = [
        '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y%m%d', '%d.%m.%Y',
        '%Y/%m/%d', '%m/%d/%Y'
    ]
    
    for formato in formatos:
        try:
            return datetime.strptime(fecha_str, formato)
        except:
            continue
    
    # Intentar extraer números
    try:
        numeros = ''.join(filter(str.isdigit, fecha_str))
        if len(numeros) >= 8:
            return datetime.strptime(numeros[:8], '%Y%m%d')
    except:
        pass
    
    return None


def _convertir_monto(monto):
    """Convierte monto a float de forma segura."""
    if pd.isna(monto):
        return 0
    
    # Si ya es numérico
    if isinstance(monto, (int, float)):
        return float(monto)
    
    # Si es string, limpiarlo
    monto_str = str(monto).strip()
    
    if not monto_str or monto_str.lower() in ['nan', 'none', 'null']:
        return 0
    
    # Remover puntos como separadores de miles
    if '.' in monto_str and ',' in monto_str:
        # Formato 1.000,00 -> quitar punto, cambiar coma por punto
        monto_str = monto_str.replace('.', '').replace(',', '.')
    elif ',' in monto_str:
        # Formato 1000,00 -> cambiar coma por punto
        monto_str = monto_str.replace(',', '.')
    
    # Remover símbolos de moneda
    monto_str = monto_str.replace('$', '').replace('€', '').replace('£', '').strip()
    
    try:
        return float(monto_str)
    except:
        return 0


def procesar_archivo(df, tipo_archivo, nombre_archivo=""):
    """Procesa archivo de ventas o compras."""
    documentos = []
    
    for idx, fila in df.iterrows():
        # Tipo de documento
        try:
            tipo_doc_val = fila.get('tipo_documento', 0)
            if pd.isna(tipo_doc_val):
                tipo_doc = 0
            else:
                tipo_doc = int(float(tipo_doc_val))
        except:
            tipo_doc = 0
        
        factor = -1 if tipo_doc == 61 else 1
        
        # Monto total
        monto_raw = fila.get('monto_total', 0)
        monto_total = _convertir_monto(monto_raw)
        
        # Fecha
        fecha_raw = fila.get('fecha_docto', '')
        fecha_dt = _parsear_fecha(fecha_raw)
        
        if fecha_dt:
            documentos.append({
                'fecha': fecha_dt,
                'monto': monto_total * factor,
                'tipo': tipo_archivo,
                'tipo_doc': tipo_doc,
                'archivo_origen': nombre_archivo
            })
    
    return documentos


def detectar_periodo_sugerido(documentos):
    """Detecta automáticamente el período sugerido basado en las fechas."""
    if not documentos:
        return None, None, None
    
    fechas = [doc['fecha'] for doc in documentos if doc['fecha']]
    
    if not fechas:
        return None, None, None
    
    fecha_min = min(fechas)
    fecha_max = max(fechas)
    
    # Calcular rango de fechas
    dias_diferencia = (fecha_max - fecha_min).days
    
    # Sugerir período basado en el rango
    if dias_diferencia <= 90:  # 3 meses
        periodo_sugerido = "Mensual"
    elif dias_diferencia <= 365:  # 1 año
        periodo_sugerido = "Trimestral"
    else:
        periodo_sugerido = "Anual"
    
    # Detectar años presentes
    años = sorted(set(fecha.year for fecha in fechas))
    
    return periodo_sugerido, fecha_min, fecha_max, años


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

# Estado de la aplicación
if 'documentos_ventas' not in st.session_state:
    st.session_state.documentos_ventas = []
if 'documentos_compras' not in st.session_state:
    st.session_state.documentos_compras = []
if 'archivos_ventas' not in st.session_state:
    st.session_state.archivos_ventas = {}
if 'archivos_compras' not in st.session_state:
    st.session_state.archivos_compras = {}
if 'periodo_seleccionado' not in st.session_state:
    st.session_state.periodo_seleccionado = "Mensual"
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False

st.subheader("📥 Carga de Archivos Múltiples")

# ==========================================
# SECCIÓN VENTAS - MÚLTIPLES ARCHIVOS
# ==========================================
st.markdown("### 📋 Archivos de Ventas (máx. 3)")

# Usar columnas para mostrar múltiples uploaders
ventas_col1, ventas_col2, ventas_col3 = st.columns(3)

archivos_ventas = []

with ventas_col1:
    ventas_file1 = st.file_uploader(
        "Ventas 1",
        type=["xlsx", "xls", "csv"],
        key="ventas_uploader_1"
    )
    if ventas_file1:
        archivos_ventas.append(ventas_file1)

with ventas_col2:
    ventas_file2 = st.file_uploader(
        "Ventas 2",
        type=["xlsx", "xls", "csv"],
        key="ventas_uploader_2"
    )
    if ventas_file2:
        archivos_ventas.append(ventas_file2)

with ventas_col3:
    ventas_file3 = st.file_uploader(
        "Ventas 3", 
        type=["xlsx", "xls", "csv"],
        key="ventas_uploader_3"
    )
    if ventas_file3:
        archivos_ventas.append(ventas_file3)

# Procesar archivos de ventas
if archivos_ventas:
    documentos_ventas_totales = []
    
    for i, ventas_file in enumerate(archivos_ventas):
        try:
            if ventas_file.name.endswith('.csv'):
                df_ventas = pd.read_csv(ventas_file, sep=';', decimal=',')
            else:
                df_ventas = pd.read_excel(ventas_file)
            
            df_ventas = normalizar_columnas(df_ventas)
            
            columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
            columnas_faltantes = [c for c in columnas_requeridas if c not in df_ventas.columns]
            
            if columnas_faltantes:
                st.error(f"❌ Archivo {i+1} de ventas: Faltan columnas {columnas_faltantes}")
            else:
                documentos = procesar_archivo(df_ventas, 'venta', ventas_file.name)
                documentos_ventas_totales.extend(documentos)
                
                # Guardar en estado
                st.session_state.archivos_ventas[ventas_file.name] = {
                    'documentos': len(documentos),
                    'procesado': True
                }
                
                st.success(f"✅ Ventas {i+1} procesadas: {len(documentos)} documentos")
        
        except Exception as e:
            st.error(f"❌ Error en archivo {i+1} de ventas: {str(e)}")
    
    st.session_state.documentos_ventas = documentos_ventas_totales
    
    if documentos_ventas_totales:
        total_ventas = sum(d['monto'] for d in documentos_ventas_totales)
        st.info(f"📊 Total ventas acumuladas: ${total_ventas:,.0f}")

# ==========================================
# SECCIÓN COMPRAS - MÚLTIPLES ARCHIVOS
# ==========================================
st.markdown("### 📋 Archivos de Compras (máx. 3)")

# Usar columnas para mostrar múltiples uploaders
compras_col1, compras_col2, compras_col3 = st.columns(3)

archivos_compras = []

with compras_col1:
    compras_file1 = st.file_uploader(
        "Compras 1",
        type=["xlsx", "xls", "csv"],
        key="compras_uploader_1"
    )
    if compras_file1:
        archivos_compras.append(compras_file1)

with compras_col2:
    compras_file2 = st.file_uploader(
        "Compras 2",
        type=["xlsx", "xls", "csv"],
        key="compras_uploader_2"
    )
    if compras_file2:
        archivos_compras.append(compras_file2)

with compras_col3:
    compras_file3 = st.file_uploader(
        "Compras 3",
        type=["xlsx", "xls", "csv"],
        key="compras_uploader_3"
    )
    if compras_file3:
        archivos_compras.append(compras_file3)

# Procesar archivos de compras
if archivos_compras:
    documentos_compras_totales = []
    
    for i, compras_file in enumerate(archivos_compras):
        try:
            if compras_file.name.endswith('.csv'):
                df_compras = pd.read_csv(compras_file, sep=';', decimal=',')
            else:
                df_compras = pd.read_excel(compras_file)
            
            df_compras = normalizar_columnas(df_compras)
            
            columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
            columnas_faltantes = [c for c in columnas_requeridas if c not in df_compras.columns]
            
            if columnas_faltantes:
                st.error(f"❌ Archivo {i+1} de compras: Faltan columnas {columnas_faltantes}")
            else:
                documentos = procesar_archivo(df_compras, 'compra', compras_file.name)
                documentos_compras_totales.extend(documentos)
                
                # Guardar en estado
                st.session_state.archivos_compras[compras_file.name] = {
                    'documentos': len(documentos),
                    'procesado': True
                }
                
                st.success(f"✅ Compras {i+1} procesadas: {len(documentos)} documentos")
        
        except Exception as e:
            st.error(f"❌ Error en archivo {i+1} de compras: {str(e)}")
    
    st.session_state.documentos_compras = documentos_compras_totales
    
    if documentos_compras_totales:
        total_compras = sum(d['monto'] for d in documentos_compras_totales)
        st.info(f"📊 Total compras acumuladas: ${total_compras:,.0f}")

# ==========================================
# DETECCIÓN Y CONFIRMACIÓN DE PERÍODO
# ==========================================
st.markdown("---")

# Combinar todos los documentos para análisis
todos_documentos = st.session_state.documentos_ventas + st.session_state.documentos_compras

if todos_documentos:
    # Detectar período sugerido
    periodo_sugerido, fecha_min, fecha_max, años = detectar_periodo_sugerido(todos_documentos)
    
    if periodo_sugerido:
        st.markdown("### ⚙️ Configuración del Período de Análisis")
        
        # Mostrar información detectada
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Fecha más antigua", fecha_min.strftime('%d/%m/%Y'))
        
        with col2:
            st.metric("Fecha más reciente", fecha_max.strftime('%d/%m/%Y'))
        
        with col3:
            st.metric("Rango de días", (fecha_max - fecha_min).days)
        
        # Mostrar años detectados
        st.info(f"📅 Años detectados en los datos: {', '.join(map(str, años))}")
        
        # Sugerencia del sistema
        st.success(f"🔍 **Sugerencia del sistema:** Agrupar por **{periodo_sugerido}**")
        st.caption(f"*Basado en el rango de fechas: {(fecha_max - fecha_min).days} días*")
        
        # Permitir confirmar o corregir
        st.markdown("### 📊 ¿Cómo desea agrupar los datos?")
        
        # Opciones de período
        periodo_opciones = ["Mensual", "Trimestral", "Anual"]
        
        # Seleccionar período (por defecto la sugerencia)
        periodo_index = periodo_opciones.index(periodo_sugerido) if periodo_sugerido in periodo_opciones else 0
        
        periodo_seleccionado = st.radio(
            "Seleccione el período de agrupación:",
            periodo_opciones,
            index=periodo_index,
            horizontal=True,
            key="periodo_selector"
        )
        
        # Guardar selección
        st.session_state.periodo_seleccionado = periodo_seleccionado
        
        # Mostrar vista previa del agrupamiento
        if st.button("👁️ Ver vista previa del agrupamiento", type="secondary"):
            st.markdown("### 👁️ Vista Previa del Agrupamiento")
            
            # Agrupar para vista previa
            conteo_por_periodo = defaultdict(int)
            monto_por_periodo = defaultdict(float)
            
            for doc in todos_documentos:
                fecha = doc['fecha']
                
                if periodo_seleccionado == "Mensual":
                    clave = f"{fecha.year}-{fecha.month:02d}"
                elif periodo_seleccionado == "Trimestral":
                    trimestre = (fecha.month - 1) // 3 + 1
                    clave = f"{fecha.year}-T{trimestre}"
                else:
                    clave = str(fecha.year)
                
                conteo_por_periodo[clave] += 1
                monto_por_periodo[clave] += doc['monto']
            
            # Crear DataFrame para vista previa
            periodos_vista = sorted(conteo_por_periodo.keys())
            
            df_vista = pd.DataFrame({
                'Período': periodos_vista,
                'Documentos': [conteo_por_periodo[p] for p in periodos_vista],
                'Monto Total': [monto_por_periodo[p] for p in periodos_vista]
            })
            
            st.dataframe(df_vista.style.format({
                'Monto Total': '${:,.0f}'
            }))
            
            st.info(f"📊 Se crearán {len(periodos_vista)} períodos de análisis")
        
        # ==========================================
        # BOTÓN PARA CALCULAR
        # ==========================================
        st.markdown("---")
        
        if st.button("🚀 Calcular Resultados Completos", type="primary", use_container_width=True):
            st.session_state.mostrar_resultados = True
            st.rerun()

# ==========================================
# CÁLCULOS COMPLETOS
# ==========================================
if st.session_state.mostrar_resultados and todos_documentos:
    st.markdown("---")
    st.subheader("📊 Resultados del Análisis")
    
    # Estadísticas de carga
    with st.expander("📦 Resumen de archivos cargados"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📥 Ventas**")
            for archivo, info in st.session_state.archivos_ventas.items():
                st.write(f"• {archivo}: {info['documentos']} documentos")
        
        with col2:
            st.markdown("**📤 Compras**")
            for archivo, info in st.session_state.archivos_compras.items():
                st.write(f"• {archivo}: {info['documentos']} documentos")
    
    # Agrupar por período seleccionado
    resumen = defaultdict(lambda: {
        'ventas': 0, 
        'compras': 0, 
        'resultado': 0,
        'documentos_ventas': 0,
        'documentos_compras': 0
    })
    
    for doc in todos_documentos:
        fecha = doc['fecha']
        
        if st.session_state.periodo_seleccionado == "Mensual":
            clave = f"{fecha.year}-{fecha.month:02d}"
        elif st.session_state.periodo_seleccionado == "Trimestral":
            trimestre = (fecha.month - 1) // 3 + 1
            clave = f"{fecha.year}-T{trimestre}"
        else:
            clave = str(fecha.year)
        
        if doc['tipo'] == 'venta':
            resumen[clave]['ventas'] += doc['monto']
            resumen[clave]['documentos_ventas'] += 1
        else:
            resumen[clave]['compras'] += doc['monto']
            resumen[clave]['documentos_compras'] += 1
    
    # Calcular resultados
    for clave in resumen:
        resumen[clave]['resultado'] = resumen[clave]['ventas'] - resumen[clave]['compras']
    
    # Ordenar periodos
    def ordenar_periodo(p):
        if '-' in p and 'T' in p:
            año, trim = p.split('-T')
            return (int(año), int(trim))
        elif '-' in p:
            año, mes = p.split('-')
            return (int(año), int(mes))
        else:
            return (int(p), 0)
    
    periodos = sorted(resumen.keys(), key=ordenar_periodo)
    
    # ==========================================
    # MÉTRICAS PRINCIPALES
    # ==========================================
    st.markdown("### 🎯 Métricas Principales")
    
    total_ventas = sum(resumen[p]['ventas'] for p in periodos)
    total_compras = sum(resumen[p]['compras'] for p in periodos)
    total_resultado = total_ventas - total_compras
    total_documentos = len(todos_documentos)
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Ventas Totales", f"${total_ventas:,.0f}")
    col2.metric("Compras Totales", f"${total_compras:,.0f}")
    col3.metric("Resultado Neto", f"${total_resultado:,.0f}")
    col4.metric("Total Documentos", total_documentos)
    
    # ==========================================
    # TABLA DE RESULTADOS POR PERÍODO
    # ==========================================
    st.markdown("### 📋 Resultados por Período")
    
    df_resultados = pd.DataFrame({
        'Período': periodos,
        'Ventas': [resumen[p]['ventas'] for p in periodos],
        'Compras': [resumen[p]['compras'] for p in periodos],
        'Resultado': [resumen[p]['resultado'] for p in periodos],
        'Docs Ventas': [resumen[p]['documentos_ventas'] for p in periodos],
        'Docs Compras': [resumen[p]['documentos_compras'] for p in periodos],
        'Margen %': [
            (resumen[p]['resultado'] / resumen[p]['ventas'] * 100) if resumen[p]['ventas'] > 0 else 0 
            for p in periodos
        ]
    })
    
    # Formatear tabla
    styled_df = df_resultados.style.format({
        'Ventas': '${:,.0f}',
        'Compras': '${:,.0f}',
        'Resultado': '${:,.0f}',
        'Margen %': '{:.1f}%'
    })
    
    st.dataframe(styled_df)
    
    # ==========================================
    # ANÁLISIS ADICIONAL
    # ==========================================
    with st.expander("📈 Análisis Adicional"):
        # Estadísticas por tipo de documento
        ventas_61 = len([d for d in todos_documentos if d['tipo'] == 'venta' and d['tipo_doc'] == 61])
        compras_61 = len([d for d in todos_documentos if d['tipo'] == 'compra' and d['tipo_doc'] == 61])
        
        st.write("**Documentos tipo 61 (Notas de crédito):**")
        st.write(f"- Ventas: {ventas_61} documentos")
        st.write(f"- Compras: {compras_61} documentos")
        
        # Distribución por origen de archivo
        st.write("**Distribución por archivo de origen:**")
        origenes = {}
        for doc in todos_documentos:
            origen = doc.get('archivo_origen', 'Desconocido')
            origenes[origen] = origenes.get(origen, 0) + 1
        
        for origen, cantidad in sorted(origenes.items()):
            st.write(f"- {origen}: {cantidad} documentos")
    
    # ==========================================
    # BOTONES DE ACCIÓN FINAL
    # ==========================================
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Realizar nuevo análisis", type="secondary", use_container_width=True):
            # Resetear estado
            for key in ['documentos_ventas', 'documentos_compras', 'archivos_ventas', 
                       'archivos_compras', 'mostrar_resultados']:
                if key in st.session_state:
                    st.session_state[key] = [] if 'archivos' not in key else {}
            st.rerun()
    
    with col2:
        if st.button("📊 Exportar resumen", type="primary", use_container_width=True):
            # Preparar datos para exportación
            datos_exportacion = {
                'configuracion': {
                    'periodo': st.session_state.periodo_seleccionado,
                    'fecha_min': fecha_min.strftime('%Y-%m-%d'),
                    'fecha_max': fecha_max.strftime('%Y-%m-%d')
                },
                'metricas_totales': {
                    'ventas_totales': total_ventas,
                    'compras_totales': total_compras,
                    'resultado_total': total_resultado,
                    'total_documentos': total_documentos
                },
                'resultados_por_periodo': df_resultados.to_dict('records')
            }
            
            st.success("✅ Datos listos para exportación")
            st.json(datos_exportacion)

# Pie de página
st.markdown("---")
st.caption("Simulador de Resultados | Múltiples archivos + Confirmación de período")
