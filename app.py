# ==========================================
# APP.PY - VERSIÓN COMPLETA CON CÁLCULOS
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
                'tipo': tipo_archivo,
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
            
            # Mostrar resumen inmediato de ventas
            if documentos_ventas:
                total_ventas = sum(d['monto'] for d in documentos_ventas)
                docs_61 = len([d for d in documentos_ventas if d['tipo_doc'] == 61])
                
                st.success(f"✅ Ventas cargadas: {len(documentos_ventas)} documentos")
                st.info(f"📊 Total ventas: ${total_ventas:,.0f}")
                
                if docs_61 > 0:
                    total_61 = sum(d['monto'] for d in documentos_ventas if d['tipo_doc'] == 61)
                    st.info(f"📝 Notas de crédito (61): {docs_61} documentos (${total_61:,.0f})")
    
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
            
            # Mostrar resumen inmediato de compras
            if documentos_compras:
                total_compras = sum(d['monto'] for d in documentos_compras)
                docs_61 = len([d for d in documentos_compras if d['tipo_doc'] == 61])
                
                st.success(f"✅ Compras cargadas: {len(documentos_compras)} documentos")
                st.info(f"📊 Total compras: ${total_compras:,.0f}")
                
                if docs_61 > 0:
                    total_61 = sum(d['monto'] for d in documentos_compras if d['tipo_doc'] == 61)
                    st.info(f"📝 Notas de crédito (61): {docs_61} documentos (${total_61:,.0f})")
    
    except Exception as e:
        st.error(f"❌ Error al procesar compras: {str(e)}")

# ==========================================
# BOTÓN DE CÁLCULO Y CONFIGURACIÓN
# ==========================================
st.markdown("---")

ventas_cargadas = len(st.session_state.ventas_cargadas) > 0
compras_cargadas = len(st.session_state.compras_cargadas) > 0

if ventas_cargadas and compras_cargadas:
    st.success("✅ Ambos archivos están cargados y listos para calcular")
    
    # Configuración de cálculo
    st.markdown("### ⚙️ Configuración de Cálculos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        periodo = st.selectbox(
            "Período de agrupación:",
            ["Mensual", "Trimestral", "Anual"],
            key="periodo_select"
        )
    
    with col2:
        tipo_calculo = st.radio(
            "Tipo de cálculo:",
            ["Flujo de caja (ingresos - egresos)", "Rentabilidad (sin impuestos)"],
            key="tipo_calculo"
        )
    
    # Botón para calcular
    if st.button("🚀 Calcular Resultados Completos", type="primary", use_container_width=True):
        st.session_state.mostrar_resultados = True
        st.rerun()

elif ventas_cargadas and not compras_cargadas:
    st.warning("⚠️ Falta cargar archivo de compras")
elif not ventas_cargadas and compras_cargadas:
    st.warning("⚠️ Falta cargar archivo de ventas")
else:
    st.info("👈 Carga ambos archivos para habilitar los cálculos")

# ==========================================
# CÁLCULOS COMPLETOS
# ==========================================
if st.session_state.mostrar_resultados and ventas_cargadas and compras_cargadas:
    st.markdown("---")
    st.subheader("📊 Resultados del Análisis")
    
    # Combinar documentos
    todos_documentos = st.session_state.ventas_cargadas + st.session_state.compras_cargadas
    
    # Cálculos por período
    resumen = defaultdict(lambda: {
        'ventas': 0, 
        'compras': 0, 
        'resultado': 0,
        'ventas_positivas': 0,
        'ventas_negativas': 0,
        'compras_positivas': 0,
        'compras_negativas': 0
    })
    
    # Agrupar por período
    for doc in todos_documentos:
        fecha = doc['fecha']
        
        if periodo == "Mensual":
            clave = f"{fecha.year}-{fecha.month:02d}"
        elif periodo == "Trimestral":
            trimestre = (fecha.month - 1) // 3 + 1
            clave = f"{fecha.year}-T{trimestre}"
        else:
            clave = str(fecha.year)
        
        monto = doc['monto']
        
        if doc['tipo'] == 'venta':
            resumen[clave]['ventas'] += monto
            if monto >= 0:
                resumen[clave]['ventas_positivas'] += monto
            else:
                resumen[clave]['ventas_negativas'] += monto
        else:
            resumen[clave]['compras'] += monto
            if monto >= 0:
                resumen[clave]['compras_positivas'] += monto
            else:
                resumen[clave]['compras_negativas'] += monto
    
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
    total_ventas_pos = sum(resumen[p]['ventas_positivas'] for p in periodos)
    total_ventas_neg = sum(resumen[p]['ventas_negativas'] for p in periodos)
    total_compras_pos = sum(resumen[p]['compras_positivas'] for p in periodos)
    total_compras_neg = sum(resumen[p]['compras_negativas'] for p in periodos)
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "Ventas Totales", 
        f"${total_ventas:,.0f}",
        f"${total_ventas_pos:,.0f} positivas" if total_ventas_pos > 0 else ""
    )
    
    col2.metric(
        "Compras Totales", 
        f"${total_compras:,.0f}",
        f"${total_compras_pos:,.0f} positivas" if total_compras_pos > 0 else ""
    )
    
    col3.metric(
        "Resultado Neto", 
        f"${total_resultado:,.0f}",
        f"{(total_resultado/total_ventas*100):.1f}%" if total_ventas > 0 else ""
    )
    
    col4.metric(
        "Documentos", 
        f"{len(todos_documentos)}",
        f"V:{len(st.session_state.ventas_cargadas)} C:{len(st.session_state.compras_cargadas)}"
    )
    
    # ==========================================
    # TABLA DE RESULTADOS POR PERÍODO
    # ==========================================
    st.markdown("### 📋 Resultados por Período")
    
    df_resultados = pd.DataFrame({
        'Período': periodos,
        'Ventas': [resumen[p]['ventas'] for p in periodos],
        'Compras': [resumen[p]['compras'] for p in periodos],
        'Resultado': [resumen[p]['resultado'] for p in periodos],
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
    
    # Colorear resultados negativos
    def color_negativos(val):
        if isinstance(val, (int, float)) and val < 0:
            return 'color: red'
        return ''
    
    styled_df = styled_df.applymap(color_negativos, subset=['Resultado', 'Margen %'])
    
    st.dataframe(styled_df)
    
    # ==========================================
    # ANÁLISIS DETALLADO
    # ==========================================
    st.markdown("### 🔍 Análisis Detallado")
    
    # Estadísticas de ventas
    with st.expander("📊 Análisis de Ventas"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Ventas Positivas", f"${total_ventas_pos:,.0f}")
            st.metric("Ventas Negativas", f"${total_ventas_neg:,.0f}")
        
        with col2:
            ventas_sin_61 = total_ventas - total_ventas_neg
            st.metric("Ventas sin notas crédito", f"${ventas_sin_61:,.0f}")
        
        with col3:
            if total_ventas_pos > 0:
                proporcion_negativas = abs(total_ventas_neg) / total_ventas_pos * 100
                st.metric("% Notas Crédito", f"{proporcion_negativas:.1f}%")
    
    # Estadísticas de compras
    with st.expander("📊 Análisis de Compras"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Compras Positivas", f"${total_compras_pos:,.0f}")
            st.metric("Compras Negativas", f"${total_compras_neg:,.0f}")
        
        with col2:
            compras_sin_61 = total_compras - total_compras_neg
            st.metric("Compras sin notas crédito", f"${compras_sin_61:,.0f}")
        
        with col3:
            if total_compras_pos > 0:
                proporcion_negativas = abs(total_compras_neg) / total_compras_pos * 100
                st.metric("% Notas Crédito", f"{proporcion_negativas:.1f}%")
    
    # ==========================================
    # CÁLCULOS AVANZADOS
    # ==========================================
    st.markdown("### 🧮 Cálculos Avanzados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Promedio mensual/trimestral/anual
        if periodo == "Mensual":
            st.metric("Promedio Mensual", f"${total_resultado/len(periodos):,.0f}")
        elif periodo == "Trimestral":
            st.metric("Promedio Trimestral", f"${total_resultado/len(periodos):,.0f}")
        else:
            st.metric("Promedio Anual", f"${total_resultado/len(periodos):,.0f}")
    
    with col2:
        # Mejor y peor período
        mejor_periodo = periodos[df_resultados['Resultado'].idxmax()]
        mejor_resultado = df_resultados['Resultado'].max()
        st.metric("Mejor Período", f"{mejor_periodo}", f"${mejor_resultado:,.0f}")
    
    with col3:
        peor_periodo = periodos[df_resultados['Resultado'].idxmin()]
        peor_resultado = df_resultados['Resultado'].min()
        st.metric("Peor Período", f"{peor_periodo}", f"${peor_resultado:,.0f}")
    
    # ==========================================
    # RESUMEN POR AÑO (si no es anual)
    # ==========================================
    if periodo != "Anual":
        st.markdown("### 📅 Resumen Anual")
        
        resumen_anual = defaultdict(lambda: {'ventas': 0, 'compras': 0, 'resultado': 0})
        
        for p in periodos:
            año = p.split('-')[0]
            resumen_anual[año]['ventas'] += resumen[p]['ventas']
            resumen_anual[año]['compras'] += resumen[p]['compras']
            resumen_anual[año]['resultado'] += resumen[p]['resultado']
        
        años = sorted(resumen_anual.keys())
        
        df_anual = pd.DataFrame({
            'Año': años,
            'Ventas': [resumen_anual[a]['ventas'] for a in años],
            'Compras': [resumen_anual[a]['compras'] for a in años],
            'Resultado': [resumen_anual[a]['resultado'] for a in años],
            'Crecimiento Ventas': [
                ((resumen_anual[años[i]]['ventas'] / resumen_anual[años[i-1]]['ventas'] - 1) * 100) 
                if i > 0 and resumen_anual[años[i-1]]['ventas'] > 0 else 0
                for i in range(len(años))
            ]
        })
        
        st.dataframe(df_anual.style.format({
            'Ventas': '${:,.0f}',
            'Compras': '${:,.0f}',
            'Resultado': '${:,.0f}',
            'Crecimiento Ventas': '{:.1f}%'
        }))
    
    # ==========================================
    # ESTADÍSTICAS DE DOCUMENTOS
    # ==========================================
    st.markdown("### 📄 Estadísticas de Documentos")
    
    # Crear DataFrame con todos los documentos
    df_documentos = pd.DataFrame(todos_documentos)
    df_documentos['mes'] = df_documentos['fecha'].dt.month
    df_documentos['año'] = df_documentos['fecha'].dt.year
    df_documentos['trimestre'] = (df_documentos['mes'] - 1) // 3 + 1
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Documentos por tipo
        ventas_count = len([d for d in todos_documentos if d['tipo'] == 'venta'])
        compras_count = len([d for d in todos_documentos if d['tipo'] == 'compra'])
        st.metric("Ventas", ventas_count)
        st.metric("Compras", compras_count)
    
    with col2:
        # Documentos tipo 61
        ventas_61 = len([d for d in todos_documentos if d['tipo'] == 'venta' and d['tipo_doc'] == 61])
        compras_61 = len([d for d in todos_documentos if d['tipo'] == 'compra' and d['tipo_doc'] == 61])
        st.metric("Notas Crédito Ventas", ventas_61)
        st.metric("Notas Crédito Compras", compras_61)
    
    with col3:
        # Promedio por documento
        if ventas_count > 0:
            avg_venta = total_ventas / ventas_count
            st.metric("Promedio Venta", f"${avg_venta:,.0f}")
        
        if compras_count > 0:
            avg_compra = total_compras / compras_count
            st.metric("Promedio Compra", f"${avg_compra:,.0f}")
    
    # ==========================================
    # BOTÓN DE REINICIO
    # ==========================================
    st.markdown("---")
    if st.button("🔄 Realizar nuevo análisis", type="secondary", use_container_width=True):
        st.session_state.ventas_cargadas = []
        st.session_state.compras_cargadas = []
        st.session_state.mostrar_resultados = False
        st.rerun()

# Pie de página
st.markdown("---")
st.caption("Simulador de Resultados | Versión completa sin gráficos")
