# ==========================================
# APP.PY - VERSIÓN CON DEBUGGING
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
# FUNCIONES AUXILIARES - ACTUALIZADAS
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


def _convertir_monto(monto):
    """Convierte monto a float de forma segura."""
    if pd.isna(monto):
        return 0
    
    # Si ya es numérico
    if isinstance(monto, (int, float)):
        return float(monto)
    
    # Si es string, limpiarlo
    monto_str = str(monto).strip()
    
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


def procesar_archivo(df, tipo_archivo):
    """Procesa archivo de ventas o compras con mejor manejo de errores."""
    documentos = []
    errores = []
    
    for idx, fila in df.iterrows():
        try:
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
                    'monto_original': monto_raw
                })
            else:
                errores.append(f"Fila {idx}: Fecha inválida - {fecha_raw}")
        
        except Exception as e:
            errores.append(f"Fila {idx}: Error - {str(e)}")
    
    return documentos, errores


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
if 'ventas_errores' not in st.session_state:
    st.session_state.ventas_errores = []
if 'compras_errores' not in st.session_state:
    st.session_state.compras_errores = []

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
        # Leer archivo
        if ventas_file.name.endswith('.csv'):
            df_ventas = pd.read_csv(ventas_file, sep=';', decimal=',')
        else:
            df_ventas = pd.read_excel(ventas_file)
        
        df_ventas = normalizar_columnas(df_ventas)
        
        # Mostrar información del archivo
        with st.expander("🔍 Ver información del archivo de ventas"):
            st.write(f"**Filas:** {len(df_ventas)}")
            st.write(f"**Columnas:** {len(df_ventas.columns)}")
            st.write("**Columnas encontradas:**", list(df_ventas.columns))
            
            if 'monto_total' in df_ventas.columns:
                st.write("**Primeros valores de monto_total:**")
                st.write(df_ventas['monto_total'].head(10).tolist())
                st.write("**Tipo de datos:**", df_ventas['monto_total'].dtype)
        
        columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
        columnas_faltantes = [c for c in columnas_requeridas if c not in df_ventas.columns]
        
        if columnas_faltantes:
            st.error(f"❌ Faltan columnas en ventas: {', '.join(columnas_faltantes)}")
        else:
            # Procesar archivo
            documentos_ventas, errores_ventas = procesar_archivo(df_ventas, 'venta')
            st.session_state.ventas_cargadas = documentos_ventas
            st.session_state.ventas_errores = errores_ventas
            
            # Mostrar resumen
            if documentos_ventas:
                total_ventas = sum(d['monto'] for d in documentos_ventas)
                docs_61 = len([d for d in documentos_ventas if d['tipo_doc'] == 61])
                
                st.success(f"✅ Ventas procesadas: {len(documentos_ventas)} documentos")
                st.info(f"📊 Total ventas: ${total_ventas:,.0f}")
                
                if docs_61 > 0:
                    total_61 = sum(d['monto'] for d in documentos_ventas if d['tipo_doc'] == 61)
                    st.info(f"📝 Notas de crédito (61): {docs_61} documentos (${total_61:,.0f})")
                
                # Mostrar primeros documentos
                with st.expander("📄 Ver primeros 5 documentos procesados"):
                    for i, doc in enumerate(documentos_ventas[:5]):
                        st.write(f"**Doc {i+1}:** Fecha: {doc['fecha'].strftime('%d/%m/%Y')}, "
                               f"Monto: ${doc['monto']:,.0f}, Tipo: {doc['tipo_doc']}")
            
            # Mostrar errores si existen
            if errores_ventas:
                with st.expander("⚠️ Errores en ventas"):
                    for error in errores_ventas[:10]:  # Mostrar primeros 10 errores
                        st.write(error)
    
    except Exception as e:
        st.error(f"❌ Error al procesar ventas: {str(e)}")
        st.exception(e)

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
        # Leer archivo
        if compras_file.name.endswith('.csv'):
            df_compras = pd.read_csv(compras_file, sep=';', decimal=',')
        else:
            df_compras = pd.read_excel(compras_file)
        
        df_compras = normalizar_columnas(df_compras)
        
        # MOSTRAR INFORMACIÓN DETALLADA DEL ARCHIVO DE COMPRAS
        with st.expander("🔍 Ver información DETALLADA del archivo de compras"):
            st.write("### Información del archivo")
            st.write(f"**Nombre:** {compras_file.name}")
            st.write(f"**Filas:** {len(df_compras)}")
            st.write(f"**Columnas:** {len(df_compras.columns)}")
            st.write("**Todas las columnas:**", list(df_compras.columns))
            
            # Información específica de columnas importantes
            for col in ['fecha_docto', 'tipo_documento', 'monto_total']:
                if col in df_compras.columns:
                    st.write(f"---")
                    st.write(f"**Columna: {col}**")
                    st.write(f"**Tipo:** {df_compras[col].dtype}")
                    st.write(f"**Valores únicos:** {df_compras[col].nunique()}")
                    st.write(f"**Valores nulos:** {df_compras[col].isnull().sum()}")
                    st.write(f"**Primeros 10 valores:**")
                    st.write(df_compras[col].head(10).tolist())
            
            # Mostrar primeras filas completas
            st.write("---")
            st.write("**Primeras 5 filas del archivo:**")
            st.dataframe(df_compras.head())
        
        columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
        columnas_faltantes = [c for c in columnas_requeridas if c not in df_compras.columns]
        
        if columnas_faltantes:
            st.error(f"❌ Faltan columnas en compras: {', '.join(columnas_faltantes)}")
            st.info("Columnas disponibles en el archivo:")
            st.write(list(df_compras.columns))
        else:
            # Procesar archivo
            documentos_compras, errores_compras = procesar_archivo(df_compras, 'compra')
            st.session_state.compras_cargadas = documentos_compras
            st.session_state.compras_errores = errores_compras
            
            # Mostrar resumen DETALLADO
            if documentos_compras:
                total_compras = sum(d['monto'] for d in documentos_compras)
                docs_61 = len([d for d in documentos_compras if d['tipo_doc'] == 61])
                
                st.success(f"✅ Compras procesadas: {len(documentos_compras)} documentos")
                st.info(f"📊 Total compras: ${total_compras:,.0f}")
                
                if docs_61 > 0:
                    total_61 = sum(d['monto'] for d in documentos_compras if d['tipo_doc'] == 61)
                    st.info(f"📝 Notas de crédito (61): {docs_61} documentos (${total_61:,.0f})")
                
                # Mostrar estadísticas detalladas
                with st.expander("📊 Estadísticas detalladas de compras"):
                    # Montos
                    montos = [d['monto'] for d in documentos_compras]
                    if montos:
                        st.write(f"**Monto máximo:** ${max(montos):,.0f}")
                        st.write(f"**Monto mínimo:** ${min(montos):,.0f}")
                        st.write(f"**Monto promedio:** ${sum(montos)/len(montos):,.0f}")
                    
                    # Fechas
                    fechas = [d['fecha'] for d in documentos_compras]
                    if fechas:
                        st.write(f"**Fecha más antigua:** {min(fechas).strftime('%d/%m/%Y')}")
                        st.write(f"**Fecha más reciente:** {max(fechas).strftime('%d/%m/%Y')}")
                    
                    # Tipos de documento
                    tipos_doc = {}
                    for d in documentos_compras:
                        tipo = d['tipo_doc']
                        tipos_doc[tipo] = tipos_doc.get(tipo, 0) + 1
                    
                    st.write("**Distribución por tipo de documento:**")
                    for tipo, count in sorted(tipos_doc.items()):
                        st.write(f"  - Tipo {tipo}: {count} documentos")
                
                # Mostrar primeros documentos procesados
                with st.expander("📄 Ver primeros 10 documentos procesados"):
                    for i, doc in enumerate(documentos_compras[:10]):
                        st.write(f"**Doc {i+1}:** Fecha: {doc['fecha'].strftime('%d/%m/%Y')}, "
                               f"Monto: ${doc['monto']:,.0f}, Tipo doc: {doc['tipo_doc']}, "
                               f"Original: {doc['monto_original']}")
            
            else:
                st.warning("⚠️ No se pudieron procesar documentos de compras")
            
            # Mostrar errores si existen
            if errores_compras:
                with st.expander("⚠️ Errores en compras (primeros 20)"):
                    for error in errores_compras[:20]:
                        st.write(error)
    
    except Exception as e:
        st.error(f"❌ Error al procesar compras: {str(e)}")
        st.exception(e)

# Resto del código permanece igual...
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
    
    periodo = st.selectbox(
        "Período de agrupación:",
        ["Mensual", "Trimestral", "Anual"],
        key="periodo_select"
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
# CÁLCULOS COMPLETOS (se mantiene igual)
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Ventas Totales", f"${total_ventas:,.0f}")
    col2.metric("Compras Totales", f"${total_compras:,.0f}")
    col3.metric("Resultado Neto", f"${total_resultado:,.0f}")
    col4.metric("Documentos", f"{len(todos_documentos)}")
    
    # Resto del código de resultados se mantiene igual...
    # (Las tablas y análisis detallados)

# Pie de página
st.markdown("---")
st.caption("Simulador de Resultados | Versión con debugging mejorado")
