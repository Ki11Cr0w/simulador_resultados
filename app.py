# ==========================================
# APP.PY - VERSIÓN SIMPLIFICADA CON CONFIRMACIÓN DE AÑO-MES
# ==========================================

import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime
import numpy as np

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
    
    if isinstance(monto, (int, float)):
        return float(monto)
    
    monto_str = str(monto).strip()
    
    if not monto_str or monto_str.lower() in ['nan', 'none', 'null']:
        return 0
    
    # Formato 1.000,00 -> 1000.00
    if '.' in monto_str and ',' in monto_str:
        monto_str = monto_str.replace('.', '').replace(',', '.')
    elif ',' in monto_str:
        monto_str = monto_str.replace(',', '.')
    
    monto_str = monto_str.replace('$', '').replace('€', '').replace('£', '').strip()
    
    try:
        return float(monto_str)
    except:
        return 0


def _formatear_monto(monto):
    """Formatea monto con separadores de miles."""
    if monto == 0:
        return "$0"
    
    signo = "-" if monto < 0 else ""
    monto_abs = abs(monto)
    
    if monto_abs >= 1_000_000_000:
        return f"{signo}${monto_abs/1_000_000_000:,.2f} MM"
    elif monto_abs >= 1_000_000:
        return f"{signo}${monto_abs/1_000_000:,.2f} M"
    elif monto_abs >= 1_000:
        return f"{signo}${monto_abs:,.0f}"
    else:
        return f"{signo}${monto_abs:,.2f}"


def detectar_año_mes_predominante(fechas):
    """Detecta el año-mes que predomina en las fechas."""
    if not fechas:
        return None, None
    
    # Contar por año-mes
    contador = defaultdict(int)
    
    for fecha in fechas:
        año_mes = f"{fecha.year}-{fecha.month:02d}"
        contador[año_mes] += 1
    
    # Encontrar el año-mes más común
    if not contador:
        return None, None
    
    año_mes_comun, cantidad = max(contador.items(), key=lambda x: x[1])
    
    # Extraer año y mes
    año_str, mes_str = año_mes_comun.split('-')
    return int(año_str), int(mes_str), cantidad


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

# Estado de la aplicación
if 'archivos_procesados' not in st.session_state:
    st.session_state.archivos_procesados = {}
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False

st.subheader("📥 Carga de Archivos")

# ==========================================
# FUNCIÓN PARA PROCESAR UN ARCHIVO INDIVIDUAL
# ==========================================
def procesar_archivo_con_periodo(archivo, tipo, numero):
    """Procesa un archivo y permite confirmar/modificar su año-mes."""
    try:
        # Leer archivo
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo, sep=';', decimal=',')
        else:
            df = pd.read_excel(archivo)
        
        df = normalizar_columnas(df)
        
        # Verificar columnas requeridas
        columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
        columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
        
        if columnas_faltantes:
            st.error(f"❌ {tipo} {numero}: Faltan columnas {columnas_faltantes}")
            return None
        
        # Procesar documentos y recoger fechas
        documentos = []
        fechas_validas = []
        
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
                    'tipo': tipo,
                    'tipo_doc': tipo_doc,
                    'archivo_origen': archivo.name
                })
                fechas_validas.append(fecha_dt)
        
        if not documentos:
            st.warning(f"⚠️ {tipo} {numero}: No se encontraron documentos con fecha válida")
            return None
        
        # Detectar año-mes predominante
        año_pred, mes_pred, cantidad = detectar_año_mes_predominante(fechas_validas)
        
        # Mostrar información básica del archivo
        st.success(f"✅ {tipo} {numero} procesado: {len(documentos)} documentos")
        
        # Información de fechas
        fecha_min = min(fechas_validas)
        fecha_max = max(fechas_validas)
        total_monto = sum(d['monto'] for d in documentos)
        
        st.write(f"**📅 Rango de fechas:** {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}")
        st.write(f"**💰 Total archivo:** {_formatear_monto(total_monto)}")
        
        # Mostrar detección de año-mes
        if año_pred and mes_pred:
            porcentaje = (cantidad / len(documentos)) * 100
            st.info(f"**🔍 DETECTADO:** {cantidad} de {len(documentos)} documentos ({porcentaje:.0f}%) corresponden a **{año_pred}-{mes_pred:02d}**")
        else:
            st.warning("No se pudo detectar un año-mes predominante")
            año_pred = datetime.now().year
            mes_pred = datetime.now().month
        
        # CONFIRMACIÓN/MODIFICACIÓN DEL AÑO-MES
        st.write("---")
        st.write("**📝 CONFIRMAR AÑO-MES DEL ARCHIVO:**")
        
        # Crear columnas para año y mes
        col_año, col_mes = st.columns(2)
        
        with col_año:
            # Selector de año
            años_disponibles = list(range(2020, datetime.now().year + 2))
            año_seleccionado = st.selectbox(
                f"Año para {tipo} {numero}:",
                años_disponibles,
                index=años_disponibles.index(año_pred) if año_pred in años_disponibles else len(años_disponibles)-1,
                key=f"año_{tipo}_{numero}"
            )
        
        with col_mes:
            # Selector de mes
            meses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            mes_seleccionado = st.selectbox(
                f"Mes para {tipo} {numero}:",
                meses,
                index=mes_pred - 1 if mes_pred else 0,
                key=f"mes_{tipo}_{numero}"
            )
        
        # Convertir mes de nombre a número
        mes_numero = meses.index(mes_seleccionado) + 1
        
        # Guardar período confirmado
        periodo_key = f"{tipo}_{numero}_{archivo.name}"
        st.session_state.archivos_procesados[periodo_key] = {
            'documentos': documentos,
            'año': año_seleccionado,
            'mes': mes_numero,
            'tipo': tipo,
            'nombre_archivo': archivo.name,
            'total_monto': total_monto
        }
        
        st.success(f"**✅ PERÍODO CONFIRMADO:** {año_seleccionado}-{mes_numero:02d}")
        
        return documentos
    
    except Exception as e:
        st.error(f"❌ Error procesando {tipo} {numero}: {str(e)}")
        return None


# ==========================================
# SECCIÓN VENTAS - MÁXIMO 3 ARCHIVOS
# ==========================================
st.markdown("### 📋 Archivos de Ventas")

ventas_files = []

# Uploaders para ventas en columnas
ventas_cols = st.columns(3)
for i in range(3):
    with ventas_cols[i]:
        ventas_file = st.file_uploader(
            f"Ventas {i+1}",
            type=["xlsx", "xls", "csv"],
            key=f"ventas_uploader_{i+1}"
        )
        if ventas_file:
            ventas_files.append((ventas_file, i+1))

# Procesar cada archivo de ventas
if ventas_files:
    for ventas_file, numero in ventas_files:
        st.markdown(f"---")
        st.markdown(f"#### 📄 Procesando: Ventas {numero} - {ventas_file.name}")
        procesar_archivo_con_periodo(ventas_file, "venta", numero)

# ==========================================
# SECCIÓN COMPRAS - MÁXIMO 3 ARCHIVOS
# ==========================================
st.markdown("### 📋 Archivos de Compras")

compras_files = []

# Uploaders para compras en columnas
compras_cols = st.columns(3)
for i in range(3):
    with compras_cols[i]:
        compras_file = st.file_uploader(
            f"Compras {i+1}",
            type=["xlsx", "xls", "csv"],
            key=f"compras_uploader_{i+1}"
        )
        if compras_file:
            compras_files.append((compras_file, i+1))

# Procesar cada archivo de compras
if compras_files:
    for compras_file, numero in compras_files:
        st.markdown(f"---")
        st.markdown(f"#### 📄 Procesando: Compras {numero} - {compras_file.name}")
        procesar_archivo_con_periodo(compras_file, "compra", numero)

# ==========================================
# RESUMEN Y CÁLCULO FINAL
# ==========================================
st.markdown("---")

# Recolectar todos los documentos procesados
todos_documentos = []
resumen_archivos = []

if st.session_state.archivos_procesados:
    st.markdown("### 📊 RESUMEN DE ARCHIVOS CARGADOS")
    
    for key, info in st.session_state.archivos_procesados.items():
        # Agregar período a cada documento
        for doc in info['documentos']:
            doc['periodo_asignado'] = f"{info['año']}-{info['mes']:02d}"
            todos_documentos.append(doc)
        
        # Guardar resumen del archivo
        resumen_archivos.append({
            'tipo': info['tipo'],
            'archivo': info['nombre_archivo'],
            'periodo': f"{info['año']}-{info['mes']:02d}",
            'documentos': len(info['documentos']),
            'total': info['total_monto']
        })
    
    # Mostrar tabla de resumen
    if resumen_archivos:
        df_resumen = pd.DataFrame(resumen_archivos)
        
        # Formatear tabla
        def formatear_fila(row):
            tipo_icon = "📥" if row['tipo'] == 'venta' else "📤"
            return f"{tipo_icon} {row['archivo']} | {row['periodo']} | {row['documentos']} doc | {_formatear_monto(row['total'])}"
        
        st.write("**Archivos procesados:**")
        for archivo in resumen_archivos:
            st.write(formatear_fila(archivo))
        
        # Totales
        total_ventas = sum(a['total'] for a in resumen_archivos if a['tipo'] == 'venta')
        total_compras = sum(a['total'] for a in resumen_archivos if a['tipo'] == 'compra')
        total_documentos = len(todos_documentos)
        
        st.markdown("---")
        st.markdown("### 🎯 TOTALES ACUMULADOS")
        
        # Mostrar en formato vertical
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📥 VENTAS**")
            st.markdown(f"<h2 style='color: #2ecc71;'>{_formatear_monto(total_ventas)}</h2>", 
                       unsafe_allow_html=True)
            docs_ventas = sum(a['documentos'] for a in resumen_archivos if a['tipo'] == 'venta')
            st.write(f"{docs_ventas} documentos")
        
        with col2:
            st.markdown("**📤 COMPRAS**")
            st.markdown(f"<h2 style='color: #e74c3c;'>{_formatear_monto(total_compras)}</h2>", 
                       unsafe_allow_html=True)
            docs_compras = sum(a['documentos'] for a in resumen_archivos if a['tipo'] == 'compra')
            st.write(f"{docs_compras} documentos")
        
        with col3:
            st.markdown("**📄 TOTAL**")
            resultado = total_ventas - total_compras
            color = "#2ecc71" if resultado >= 0 else "#e74c3c"
            st.markdown(f"<h2 style='color: {color};'>{_formatear_monto(resultado)}</h2>", 
                       unsafe_allow_html=True)
            st.write(f"{total_documentos} documentos")
        
        # ==========================================
        # CÁLCULOS DETALLADOS POR PERÍODO
        # ==========================================
        st.markdown("---")
        
        if st.button("🚀 CALCULAR ANÁLISIS DETALLADO", type="primary", use_container_width=True):
            st.session_state.mostrar_resultados = True
            st.rerun()

# ==========================================
# ANÁLISIS DETALLADO
# ==========================================
if st.session_state.mostrar_resultados and todos_documentos:
    st.markdown("---")
    st.subheader("📊 ANÁLISIS DETALLADO POR PERÍODO")
    
    # Agrupar por período asignado (año-mes)
    resumen_periodos = defaultdict(lambda: {
        'ventas': 0,
        'compras': 0,
        'documentos_ventas': 0,
        'documentos_compras': 0
    })
    
    for doc in todos_documentos:
        periodo = doc['periodo_asignado']
        
        if doc['tipo'] == 'venta':
            resumen_periodos[periodo]['ventas'] += doc['monto']
            resumen_periodos[periodo]['documentos_ventas'] += 1
        else:
            resumen_periodos[periodo]['compras'] += doc['monto']
            resumen_periodos[periodo]['documentos_compras'] += 1
    
    # Ordenar periodos cronológicamente
    periodos_ordenados = sorted(resumen_periodos.keys())
    
    # Crear tabla de resultados
    datos_tabla = []
    
    for periodo in periodos_ordenados:
        datos = resumen_periodos[periodo]
        resultado = datos['ventas'] - datos['compras']
        
        datos_tabla.append({
            'Período': periodo,
            'Ventas': datos['ventas'],
            'Compras': datos['compras'],
            'Resultado': resultado,
            'Docs V': datos['documentos_ventas'],
            'Docs C': datos['documentos_compras'],
            'Margen %': (resultado / datos['ventas'] * 100) if datos['ventas'] != 0 else 0
        })
    
    df_resultados = pd.DataFrame(datos_tabla)
    
    # Formatear con colores
    def aplicar_estilo(val):
        if isinstance(val, (int, float)) and val < 0:
            return 'color: #e74c3c; font-weight: bold;'
        elif isinstance(val, (int, float)) and val > 0:
            return 'color: #2ecc71; font-weight: bold;'
        return ''
    
    styled_df = df_resultados.style.format({
        'Ventas': lambda x: _formatear_monto(x),
        'Compras': lambda x: _formatear_monto(x),
        'Resultado': lambda x: _formatear_monto(x),
        'Margen %': '{:+.1f}%'
    }).applymap(aplicar_estilo, subset=['Resultado', 'Margen %'])
    
    st.dataframe(styled_df, use_container_width=True)
    
    # ==========================================
    # RESUMEN FINAL
    # ==========================================
    st.markdown("---")
    st.markdown("### 📈 RESUMEN FINAL")
    
    # Calcular totales
    total_ventas = sum(r['ventas'] for r in resumen_periodos.values())
    total_compras = sum(r['compras'] for r in resumen_periodos.values())
    total_resultado = total_ventas - total_compras
    total_documentos = len(todos_documentos)
    
    # Mostrar métricas principales en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ventas Totales", _formatear_monto(total_ventas))
    
    with col2:
        st.metric("Compras Totales", _formatear_monto(total_compras))
    
    with col3:
        st.metric("Resultado Neto", _formatear_monto(total_resultado))
    
    with col4:
        st.metric("Total Documentos", total_documentos)
    
    # Estadísticas adicionales
    with st.expander("📊 ESTADÍSTICAS ADICIONALES"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Documentos tipo 61
            docs_61_ventas = len([d for d in todos_documentos if d['tipo'] == 'venta' and d['tipo_doc'] == 61])
            docs_61_compras = len([d for d in todos_documentos if d['tipo'] == 'compra' and d['tipo_doc'] == 61])
            
            st.write("**Notas de crédito (tipo 61):**")
            st.write(f"- Ventas: {docs_61_ventas}")
            st.write(f"- Compras: {docs_61_compras}")
            st.write(f"- Total: {docs_61_ventas + docs_61_compras}")
        
        with col2:
            # Promedios
            docs_ventas = sum(r['documentos_ventas'] for r in resumen_periodos.values())
            docs_compras = sum(r['documentos_compras'] for r in resumen_periodos.values())
            
            if docs_ventas > 0:
                promedio_venta = total_ventas / docs_ventas
                st.write(f"**Promedio por venta:** {_formatear_monto(promedio_venta)}")
            
            if docs_compras > 0:
                promedio_compra = total_compras / docs_compras
                st.write(f"**Promedio por compra:** {_formatear_monto(promedio_compra)}")
    
    # ==========================================
    # BOTÓN DE REINICIO
    # ==========================================
    st.markdown("---")
    
    if st.button("🔄 INICIAR NUEVO ANÁLISIS", type="secondary", use_container_width=True):
        # Limpiar estado
        for key in ['archivos_procesados', 'mostrar_resultados']:
            if key in st.session_state:
                st.session_state[key] = {} if 'archivos' in key else False
        st.rerun()

# Mensaje inicial
if not st.session_state.archivos_procesados and not st.session_state.mostrar_resultados:
    st.info("👈 Comienza cargando archivos de ventas y compras. Para cada archivo, confirma el año-mes correspondiente.")

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
