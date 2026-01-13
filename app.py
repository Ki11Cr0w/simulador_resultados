# ==========================================
# APP.PY - VERSIÓN CON COMPRAS Y BOTÓN DE CÁLCULO
# ==========================================

import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime

from validaciones import validar_ventas_sii, validar_compras_sii

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador Simple", layout="centered")
st.title("📊 Simulador Simple de Resultados")

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
    ]
    
    for formato in formatos:
        try:
            return datetime.strptime(fecha_str, formato)
        except:
            continue
    
    return None


def procesar_archivo(df, tipo_archivo):
    """Procesa archivo de ventas o compras."""
    documentos = []
    
    for _, fila in df.iterrows():
        try:
            tipo_doc = int(float(fila.get('tipo_documento', 0) or 0))
        except:
            tipo_doc = 0
        
        factor = -1 if tipo_doc == 61 else 1
        
        try:
            monto_total = float(fila.get('monto_total', 0) or 0)
        except:
            monto_total = 0
        
        fecha_raw = fila.get('fecha_docto', '')
        fecha_dt = _parsear_fecha(fecha_raw)
        
        if fecha_dt:
            documentos.append({
                'fecha': fecha_dt,
                'monto': monto_total * factor,
                'tipo': tipo_archivo,  # 'venta' o 'compra'
                'tipo_doc': tipo_doc
            })
    
    return documentos


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

# Estado de la aplicación
if 'ventas_cargadas' not in st.session_state:
    st.session_state.ventas_cargadas = []
if 'compras_cargadas' not in st.session_state:
    st.session_state.compras_cargadas = []
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False

st.subheader("📥 Cargar Archivos")

# ==========================================
# SECCIÓN VENTAS
# ==========================================
st.markdown("### 📋 Archivo de Ventas")

ventas_file = st.file_uploader(
    "Seleccionar archivo de ventas",
    type=["xlsx", "xls", "csv"],
    key="ventas_uploader"
)

if ventas_file:
    try:
        if ventas_file.name.endswith('.csv'):
            df_ventas = pd.read_csv(ventas_file, sep=';', decimal=',')
        else:
            df_ventas = pd.read_excel(ventas_file)
        
        df_ventas = normalizar_columnas(df_ventas)
        
        columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
        columnas_faltantes = [c for c in columnas_requeridas if c not in df_ventas.columns]
        
        if columnas_faltantes:
            st.error(f"❌ Faltan columnas en ventas: {', '.join(columnas_faltantes)}")
        else:
            documentos_ventas = procesar_archivo(df_ventas, 'venta')
            st.session_state.ventas_cargadas = documentos_ventas
            st.success(f"✅ Ventas cargadas: {len(documentos_ventas)} documentos")
            
            with st.expander("📊 Ver resumen ventas"):
                st.write(f"Total documentos: {len(documentos_ventas)}")
                if documentos_ventas:
                    total_ventas = sum(d['monto'] for d in documentos_ventas)
                    docs_61 = len([d for d in documentos_ventas if d['tipo_doc'] == 61])
                    st.write(f"Total monto: ${total_ventas:,.0f}")
                    st.write(f"Documentos tipo 61: {docs_61}")
    
    except Exception as e:
        st.error(f"❌ Error al procesar ventas: {str(e)}")

# ==========================================
# SECCIÓN COMPRAS
# ==========================================
st.markdown("### 📋 Archivo de Compras")

compras_file = st.file_uploader(
    "Seleccionar archivo de compras",
    type=["xlsx", "xls", "csv"],
    key="compras_uploader"
)

if compras_file:
    try:
        if compras_file.name.endswith('.csv'):
            df_compras = pd.read_csv(compras_file, sep=';', decimal=',')
        else:
            df_compras = pd.read_excel(compras_file)
        
        df_compras = normalizar_columnas(df_compras)
        
        columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
        columnas_faltantes = [c for c in columnas_requeridas if c not in df_compras.columns]
        
        if columnas_faltantes:
            st.error(f"❌ Faltan columnas en compras: {', '.join(columnas_faltantes)}")
        else:
            documentos_compras = procesar_archivo(df_compras, 'compra')
            st.session_state.compras_cargadas = documentos_compras
            st.success(f"✅ Compras cargadas: {len(documentos_compras)} documentos")
            
            with st.expander("📊 Ver resumen compras"):
                st.write(f"Total documentos: {len(documentos_compras)}")
                if documentos_compras:
                    total_compras = sum(d['monto'] for d in documentos_compras)
                    docs_61 = len([d for d in documentos_compras if d['tipo_doc'] == 61])
                    st.write(f"Total monto: ${total_compras:,.0f}")
                    st.write(f"Documentos tipo 61: {docs_61}")
    
    except Exception as e:
        st.error(f"❌ Error al procesar compras: {str(e)}")

# ==========================================
# BOTÓN DE CÁLCULO
# ==========================================
st.markdown("---")

# Verificar si ambos archivos están cargados
ventas_cargadas = len(st.session_state.ventas_cargadas) > 0
compras_cargadas = len(st.session_state.compras_cargadas) > 0

if ventas_cargadas and compras_cargadas:
    st.success("✅ Ambos archivos están cargados")
    
    # Selector de período
    periodo = st.selectbox(
        "Seleccionar período para agrupar:",
        ["Mensual", "Trimestral", "Anual"],
        key="periodo_select"
    )
    
    # Botón para calcular
    if st.button("🚀 Calcular Resultados", type="primary", use_container_width=True):
        st.session_state.mostrar_resultados = True
        st.rerun()

elif ventas_cargadas and not compras_cargadas:
    st.warning("⚠️ Falta cargar archivo de compras")
elif not ventas_cargadas and compras_cargadas:
    st.warning("⚠️ Falta cargar archivo de ventas")
else:
    st.info("👈 Carga ambos archivos para habilitar los cálculos")

# ==========================================
# MOSTRAR RESULTADOS (solo después de click en botón)
# ==========================================
if st.session_state.mostrar_resultados and ventas_cargadas and compras_cargadas:
    st.markdown("---")
    st.subheader("📊 Resultados del Análisis")
    
    # Combinar todos los documentos
    todos_documentos = st.session_state.ventas_cargadas + st.session_state.compras_cargadas
    
    # Calcular resultados por período
    resumen = defaultdict(lambda: {'ventas': 0, 'compras': 0, 'resultado': 0})
    
    for doc in todos_documentos:
        fecha = doc['fecha']
        
        if periodo == "Mensual":
            clave = f"{fecha.year}-{fecha.month:02d}"
        elif periodo == "Trimestral":
            trimestre = (fecha.month - 1) // 3 + 1
            clave = f"{fecha.year}-T{trimestre}"
        else:
            clave = str(fecha.year)
        
        if doc['tipo'] == 'venta':
            resumen[clave]['ventas'] += doc['monto']
        else:
            resumen[clave]['compras'] += doc['monto']
    
    # Calcular resultado
    for clave in resumen:
        resumen[clave]['resultado'] = resumen[clave]['ventas'] - resumen[clave]['compras']
    
    # Ordenar periodos
    periodos = sorted(resumen.keys())
    ventas_totales = [resumen[p]['ventas'] for p in periodos]
    compras_totales = [resumen[p]['compras'] for p in periodos]
    resultados = [resumen[p]['resultado'] for p in periodos]
    
    # ==========================================
    # MÉTRICAS GENERALES
    # ==========================================
    st.markdown("### 📈 Métricas Generales")
    
    total_ventas = sum(ventas_totales)
    total_compras = sum(compras_totales)
    total_resultado = total_ventas - total_compras
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Ventas", f"${total_ventas:,.0f}")
    col2.metric("Total Compras", f"${total_compras:,.0f}")
    col3.metric("Resultado", f"${total_resultado:,.0f}")
    
    if total_ventas > 0:
        margen = (total_resultado / total_ventas) * 100
        col4.metric("Margen %", f"{margen:.1f}%")
    else:
        col4.metric("Margen %", "N/A")
    
    # ==========================================
    # TABLA DETALLADA
    # ==========================================
    st.markdown("### 📋 Detalle por Período")
    
    df_resultados = pd.DataFrame({
        'Período': periodos,
        'Ventas': ventas_totales,
        'Compras': compras_totales,
        'Resultado': resultados,
        'Margen %': [r/v*100 if v > 0 else 0 for r, v in zip(resultados, ventas_totales)]
    })
    
    st.dataframe(df_resultados.style.format({
        'Ventas': '${:,.0f}',
        'Compras': '${:,.0f}',
        'Resultado': '${:,.0f}',
        'Margen %': '{:.1f}%'
    }))
    
    # ==========================================
    # ESTADÍSTICAS ADICIONALES
    # ==========================================
    with st.expander("📊 Estadísticas Detalladas"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📥 Ventas**")
            st.write(f"- Documentos: {len(st.session_state.ventas_cargadas)}")
            st.write(f"- Total: ${total_ventas:,.0f}")
            
            # Documentos tipo 61 en ventas
            ventas_61 = [d for d in st.session_state.ventas_cargadas if d['tipo_doc'] == 61]
            if ventas_61:
                total_61 = sum(d['monto'] for d in ventas_61)
                st.write(f"- Notas de crédito (61): {len(ventas_61)} (${total_61:,.0f})")
        
        with col2:
            st.markdown("**📤 Compras**")
            st.write(f"- Documentos: {len(st.session_state.compras_cargadas)}")
            st.write(f"- Total: ${total_compras:,.0f}")
            
            # Documentos tipo 61 en compras
            compras_61 = [d for d in st.session_state.compras_cargadas if d['tipo_doc'] == 61]
            if compras_61:
                total_61 = sum(d['monto'] for d in compras_61)
                st.write(f"- Notas de crédito (61): {len(compras_61)} (${total_61:,.0f})")
    
    # ==========================================
    # RESUMEN POR AÑO (si no es anual)
    # ==========================================
    if periodo != "Anual":
        st.markdown("### 📅 Resumen Anual")
        
        # Agrupar por año
        resumen_anual = defaultdict(lambda: {'ventas': 0, 'compras': 0})
        
        for doc in todos_documentos:
            año = doc['fecha'].year
            if doc['tipo'] == 'venta':
                resumen_anual[año]['ventas'] += doc['monto']
            else:
                resumen_anual[año]['compras'] += doc['monto']
        
        años = sorted(resumen_anual.keys())
        df_anual = pd.DataFrame({
            'Año': años,
            'Ventas': [resumen_anual[a]['ventas'] for a in años],
            'Compras': [resumen_anual[a]['compras'] for a in años],
            'Resultado': [resumen_anual[a]['ventas'] - resumen_anual[a]['compras'] for a in años]
        })
        
        st.dataframe(df_anual.style.format({
            'Ventas': '${:,.0f}',
            'Compras': '${:,.0f}',
            'Resultado': '${:,.0f}'
        }))
    
    # Botón para reiniciar
    st.markdown("---")
    if st.button("🔄 Realizar nuevo análisis", type="secondary"):
        st.session_state.ventas_cargadas = []
        st.session_state.compras_cargadas = []
        st.session_state.mostrar_resultados = False
        st.rerun()

# Pie de página
st.markdown("---")
st.caption("Versión simple | Ventas + Compras | Botón de cálculo")
