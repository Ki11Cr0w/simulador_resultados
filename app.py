# app.py - VERSIÓN TODO EN UNO
import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="wide")
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

def parsear_fecha(fecha_str):
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

def convertir_monto(monto):
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

def formatear_monto(monto):
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
        return None, None, 0
    
    # Contar por año-mes
    contador = defaultdict(int)
    
    for fecha in fechas:
        año_mes = f"{fecha.year}-{fecha.month:02d}"
        contador[año_mes] += 1
    
    # Encontrar el año-mes más común
    if not contador:
        return None, None, 0
    
    año_mes_comun, cantidad = max(contador.items(), key=lambda x: x[1])
    
    # Extraer año y mes
    año_str, mes_str = año_mes_comun.split('-')
    return int(año_str), int(mes_str), cantidad

# ==========================================
# VISTAS
# ==========================================

def vista_carga_multiple_archivos():
    """Vista para cargar MÚLTIPLES archivos a la vez."""
    st.subheader("📥 Carga de Archivos Múltiple")
    
    # ==========================================
    # SECCIÓN VENTAS - MÚLTIPLES ARCHIVOS
    # ==========================================
    st.markdown("### 📋 Archivos de Ventas")
    
    archivos_ventas = st.file_uploader(
        "Selecciona UNO o VARIOS archivos de ventas",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        key="ventas_uploader_multiple",
        help="📌 Puedes seleccionar MÚLTIPLES archivos a la vez. No hay límite.",
        label_visibility="visible"
    )
    
    if archivos_ventas:
        st.success(f"📦 **{len(archivos_ventas)} archivo(s) de ventas seleccionado(s)**")
        
        for idx, archivo in enumerate(archivos_ventas):
            if archivo.name in st.session_state.archivos_procesados:
                st.info(f"⏭️ Archivo '{archivo.name[:20]}...' ya procesado")
                continue
            
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
                    st.error(f"❌ Faltan columnas: {columnas_faltantes}")
                    continue
                
                # Procesar documentos
                documentos = []
                fechas_validas = []
                
                for _, fila in df.iterrows():
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
                    monto_total = convertir_monto(monto_raw)
                    
                    # Fecha
                    fecha_raw = fila.get('fecha_docto', '')
                    fecha_dt = parsear_fecha(fecha_raw)
                    
                    if fecha_dt:
                        documentos.append({
                            'fecha': fecha_dt,
                            'monto': monto_total * factor,
                            'tipo': 'venta',
                            'tipo_doc': tipo_doc,
                            'archivo_origen': archivo.name
                        })
                        fechas_validas.append(fecha_dt)
                
                if not documentos:
                    st.error("❌ No se encontraron documentos con fecha válida")
                    continue
                
                # Detectar año-mes predominante
                año_pred, mes_pred, cantidad = detectar_año_mes_predominante(fechas_validas)
                
                # Calcular estadísticas
                fecha_min = min(fechas_validas)
                fecha_max = max(fechas_validas)
                total_monto = sum(d['monto'] for d in documentos)
                
                # Mostrar info compacta
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    
                    with col1:
                        nombre_corto = archivo.name[:25]
                        if len(archivo.name) > 25:
                            nombre_corto += "..."
                        st.markdown(f"**{idx+1}. {nombre_corto}**")
                        st.markdown(f"📄 **{len(documentos)} doc**")
                    
                    with col2:
                        fecha_min_str = fecha_min.strftime('%d/%m')
                        fecha_max_str = fecha_max.strftime('%d/%m/%Y')
                        st.markdown(f"📅 **{fecha_min_str} - {fecha_max_str}**")
                    
                    with col3:
                        if año_pred:
                            porcentaje = (cantidad / len(documentos)) * 100
                            if porcentaje >= 50:
                                st.markdown(f"🔍 **{año_pred}-{mes_pred:02d}**")
                                st.markdown(f"*({porcentaje:.0f}% de los doc)*")
                            else:
                                st.markdown(f"⚠️ **Varios períodos**")
                                st.markdown(f"*Pred: {año_pred}-{mes_pred:02d}*")
                        else:
                            st.markdown("❓ **Sin detección**")
                    
                    with col4:
                        st.markdown(f"💰 **{formatear_monto(total_monto)}**")
                
                # Confirmar período
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
                            key=f"año_venta_{idx}_{archivo.name}",
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
                            key=f"mes_venta_{idx}_{archivo.name}",
                            label_visibility="collapsed"
                        )
                    
                    with col_d:
                        mes_numero = meses.index(mes_seleccionado) + 1
                        st.success(f"**{año_seleccionado}-{mes_numero:02d}**")
                
                # Guardar en estado
                st.session_state.archivos_procesados[archivo.name] = {
                    'documentos': documentos,
                    'fechas_validas': fechas_validas,
                    'año_predominante': año_pred,
                    'mes_predominante': mes_pred,
                    'cantidad_predominante': cantidad,
                    'fecha_minima': fecha_min,
                    'fecha_maxima': fecha_max,
                    'total_monto': total_monto,
                    'nombre_archivo': archivo.name,
                    'tipo_archivo': 'venta',
                    'documentos_count': len(documentos)
                }
                st.session_state.periodos_asignados[archivo.name] = f"{año_seleccionado}-{mes_numero:02d}"
                
            except Exception as e:
                st.error(f"❌ **Venta {idx+1} - {archivo.name}:** {str(e)[:50]}")
    
    # ==========================================
    # SECCIÓN COMPRAS - MÚLTIPLES ARCHIVOS
    # ==========================================
    st.markdown("### 📋 Archivos de Compras")
    
    archivos_compras = st.file_uploader(
        "Selecciona UNO o VARIOS archivos de compras",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        key="compras_uploader_multiple",
        help="📌 Puedes seleccionar MÚLTIPLES archivos a la vez. No hay límite.",
        label_visibility="visible"
    )
    
    if archivos_compras:
        st.success(f"📦 **{len(archivos_compras)} archivo(s) de compras seleccionado(s)**")
        
        for idx, archivo in enumerate(archivos_compras):
            if archivo.name in st.session_state.archivos_procesados:
                st.info(f"⏭️ Archivo '{archivo.name[:20]}...' ya procesado")
                continue
            
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
                    st.error(f"❌ Faltan columnas: {columnas_faltantes}")
                    continue
                
                # Procesar documentos
                documentos = []
                fechas_validas = []
                
                for _, fila in df.iterrows():
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
                    monto_total = convertir_monto(monto_raw)
                    
                    # Fecha
                    fecha_raw = fila.get('fecha_docto', '')
                    fecha_dt = parsear_fecha(fecha_raw)
                    
                    if fecha_dt:
                        documentos.append({
                            'fecha': fecha_dt,
                            'monto': monto_total * factor,
                            'tipo': 'compra',
                            'tipo_doc': tipo_doc,
                            'archivo_origen': archivo.name
                        })
                        fechas_validas.append(fecha_dt)
                
                if not documentos:
                    st.error("❌ No se encontraron documentos con fecha válida")
                    continue
                
                # Detectar año-mes predominante
                año_pred, mes_pred, cantidad = detectar_año_mes_predominante(fechas_validas)
                
                # Calcular estadísticas
                fecha_min = min(fechas_validas)
                fecha_max = max(fechas_validas)
                total_monto = sum(d['monto'] for d in documentos)
                
                # Mostrar info compacta
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    
                    with col1:
                        nombre_corto = archivo.name[:25]
                        if len(archivo.name) > 25:
                            nombre_corto += "..."
                        st.markdown(f"**{idx+1}. {nombre_corto}**")
                        st.markdown(f"📄 **{len(documentos)} doc**")
                    
                    with col2:
                        fecha_min_str = fecha_min.strftime('%d/%m')
                        fecha_max_str = fecha_max.strftime('%d/%m/%Y')
                        st.markdown(f"📅 **{fecha_min_str} - {fecha_max_str}**")
                    
                    with col3:
                        if año_pred:
                            porcentaje = (cantidad / len(documentos)) * 100
                            if porcentaje >= 50:
                                st.markdown(f"🔍 **{año_pred}-{mes_pred:02d}**")
                                st.markdown(f"*({porcentaje:.0f}% de los doc)*")
                            else:
                                st.markdown(f"⚠️ **Varios períodos**")
                                st.markdown(f"*Pred: {año_pred}-{mes_pred:02d}*")
                        else:
                            st.markdown("❓ **Sin detección**")
                    
                    with col4:
                        st.markdown(f"💰 **{formatear_monto(total_monto)}**")
                
                # Confirmar período
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
                            key=f"año_compra_{idx}_{archivo.name}",
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
                            key=f"mes_compra_{idx}_{archivo.name}",
                            label_visibility="collapsed"
                        )
                    
                    with col_d:
                        mes_numero = meses.index(mes_seleccionado) + 1
                        st.success(f"**{año_seleccionado}-{mes_numero:02d}**")
                
                # Guardar en estado
                st.session_state.archivos_procesados[archivo.name] = {
                    'documentos': documentos,
                    'fechas_validas': fechas_validas,
                    'año_predominante': año_pred,
                    'mes_predominante': mes_pred,
                    'cantidad_predominante': cantidad,
                    'fecha_minima': fecha_min,
                    'fecha_maxima': fecha_max,
                    'total_monto': total_monto,
                    'nombre_archivo': archivo.name,
                    'tipo_archivo': 'compra',
                    'documentos_count': len(documentos)
                }
                st.session_state.periodos_asignados[archivo.name] = f"{año_seleccionado}-{mes_numero:02d}"
                
            except Exception as e:
                st.error(f"❌ **Compra {idx+1} - {archivo.name}:** {str(e)[:50]}")

def vista_resumen_compacto():
    """Vista de resumen de archivos cargados."""
    if not st.session_state.archivos_procesados:
        return False
    
    st.markdown("### 📊 Resumen de Archivos Cargados")
    
    # Separar por tipo
    archivos_ventas = {k:v for k,v in st.session_state.archivos_procesados.items() 
                      if v['tipo_archivo'] == 'venta'}
    archivos_compras = {k:v for k,v in st.session_state.archivos_procesados.items() 
                       if v['tipo_archivo'] == 'compra'}
    
    # Mostrar en tabs para mejor organización
    tab1, tab2, tab3 = st.tabs([f"📥 Ventas ({len(archivos_ventas)})", 
                                f"📤 Compras ({len(archivos_compras)})", 
                                "📈 Totales"])
    
    with tab1:
        if archivos_ventas:
            for archivo, info in archivos_ventas.items():
                periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    nombre_corto = archivo[:30] + "..." if len(archivo) > 30 else archivo
                    st.markdown(f"**{nombre_corto}**")
                with col2:
                    st.markdown(f"`{periodo}`")
                with col3:
                    st.markdown(f"**{formatear_monto(info['total_monto'])}**")
                    st.markdown(f"*{info['documentos_count']} doc*")
        else:
            st.info("No hay archivos de ventas cargados")
    
    with tab2:
        if archivos_compras:
            for archivo, info in archivos_compras.items():
                periodo = st.session_state.periodos_asignados.get(archivo, "No asignado")
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    nombre_corto = archivo[:30] + "..." if len(archivo) > 30 else archivo
                    st.markdown(f"**{nombre_corto}**")
                with col2:
                    st.markdown(f"`{periodo}`")
                with col3:
                    st.markdown(f"**{formatear_monto(info['total_monto'])}**")
                    st.markdown(f"*{info['documentos_count']} doc*")
        else:
            st.info("No hay archivos de compras cargados")
    
    with tab3:
        # Calcular totales
        total_ventas = sum(info['total_monto'] for info in archivos_ventas.values())
        total_compras = sum(info['total_monto'] for info in archivos_compras.values())
        total_docs_ventas = sum(info['documentos_count'] for info in archivos_ventas.values())
        total_docs_compras = sum(info['documentos_count'] for info in archivos_compras.values())
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Ventas", formatear_monto(total_ventas), f"{total_docs_ventas} doc")
        
        with col2:
            st.metric("Compras", formatear_monto(total_compras), f"{total_docs_compras} doc")
        
        with col3:
            resultado = total_ventas - total_compras
            color = "normal" if resultado >= 0 else "inverse"
            st.metric("Resultado", formatear_monto(resultado), delta_color=color)
        
        with col4:
            st.metric("Total Docs", total_docs_ventas + total_docs_compras)
    
    return True

def vista_resultados():
    """Vista de resultados detallados."""
    if not st.session_state.mostrar_resultados:
        return
    
    # Recolectar todos los documentos
    todos_documentos = []
    for info in st.session_state.archivos_procesados.values():
        for doc in info['documentos']:
            periodo = st.session_state.periodos_asignados.get(doc['archivo_origen'], "Sin_periodo")
            doc['periodo_asignado'] = periodo
            todos_documentos.append(doc)
    
    # Agrupar por período
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
    
    # Calcular totales
    total_ventas = sum(p['ventas'] for p in resumen_periodos.values())
    total_compras = sum(p['compras'] for p in resumen_periodos.values())
    total_resultado = total_ventas - total_compras
    total_docs_ventas = sum(p['documentos_ventas'] for p in resumen_periodos.values())
    total_docs_compras = sum(p['documentos_compras'] for p in resumen_periodos.values())
    total_documentos = total_docs_ventas + total_docs_compras
    
    # Generar tabla
    periodos_ordenados = sorted(resumen_periodos.keys())
    datos_tabla = []
    
    for periodo in periodos_ordenados:
        datos_periodo = resumen_periodos[periodo]
        resultado = datos_periodo['ventas'] - datos_periodo['compras']
        margen = (resultado / datos_periodo['ventas'] * 100) if datos_periodo['ventas'] != 0 else 0
        
        datos_tabla.append({
            'Período': periodo,
            'Ventas': datos_periodo['ventas'],
            'Compras': datos_periodo['compras'],
            'Resultado': resultado,
            'Docs V': datos_periodo['documentos_ventas'],
            'Docs C': datos_periodo['documentos_compras'],
            'Margen %': margen
        })
    
    # Mostrar resultados
    st.subheader("📊 Análisis por Período")
    df_resultados = pd.DataFrame(datos_tabla)
    
    # Formatear tabla
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
    
    # Métricas principales
    st.markdown("---")
    st.markdown("### 📈 Resumen Final")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ventas Totales", formatear_monto(total_ventas))
    
    with col2:
        st.metric("Compras Totales", formatear_monto(total_compras))
    
    with col3:
        st.metric("Resultado Neto", formatear_monto(total_resultado))
    
    with col4:
        st.metric("Total Documentos", total_documentos)

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

# 1. Cargar múltiples archivos
vista_carga_multiple_archivos()

# 2. Mostrar resumen si hay archivos
if st.session_state.archivos_procesados:
    st.markdown("---")
    
    if vista_resumen_compacto():
        # Botón para calcular análisis
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            total_archivos = len(st.session_state.archivos_procesados)
            st.success(f"✅ **{total_archivos} archivo(s) cargado(s) y listo(s) para análisis**")
        
        with col2:
            if st.button("🚀 Calcular Análisis", type="primary", use_container_width=True):
                st.session_state.mostrar_resultados = True
                st.rerun()

# 3. Mostrar resultados si se solicitó
if st.session_state.mostrar_resultados:
    st.markdown("---")
    vista_resultados()

# ==========================================
# BOTÓN DE REINICIO
# ==========================================

if st.session_state.archivos_procesados:
    st.markdown("---")
    
    if st.button("🔄 Iniciar Nuevo Análisis", type="secondary", use_container_width=True):
        # Limpiar estado
        for key in ['archivos_procesados', 'periodos_asignados', 'mostrar_resultados']:
            if key in st.session_state:
                st.session_state[key] = {} if 'periodos' in key or 'archivos' in key else False
        st.rerun()

# Mensaje inicial
if not st.session_state.archivos_procesados and not st.session_state.mostrar_resultados:
    with st.expander("📋 **INSTRUCCIONES - Carga MÚLTIPLE de archivos**", expanded=True):
        st.markdown("""
        ### 🚀 **CÓMO USAR ESTE SIMULADOR:**
        
        **1. 📥 CARGA DE ARCHIVOS (ILIMITADOS):**
        - **Ventas:** Selecciona TODOS tus archivos de ventas (pueden ser varios a la vez)
        - **Compras:** Selecciona TODOS tus archivos de compras (pueden ser varios a la vez)
        - ✅ **Puedes seleccionar MÚLTIPLES archivos SIMULTÁNEAMENTE**
        
        **2. 📝 CONFIRMACIÓN DE PERÍODO:**
        - Para cada archivo, el sistema detectará automáticamente el período
        - Confirma o corrige el **AÑO** y **MES** correspondiente
        
        **3. 📊 ANÁLISIS FINAL:**
        - Revisa el resumen de todos los archivos cargados
        - Haz click en **"Calcular Análisis"** para ver resultados detallados
        
        ---
        
        **💡 CONSEJOS PRÁCTICOS:**
        - Puedes cargar **tantos archivos como necesites** (no hay límite)
        - Usa **Ctrl/Cmd + click** para seleccionar archivos individuales
        - O **arrastra y suelta** para seleccionar varios a la vez
        - Cada archivo debe corresponder a un **mes específico** (ej: 2024-01, 2024-02, etc.)
        """)

# Pie de página
st.markdown("---")
st.caption(f"Simulador de Resultados | Carga múltiple ilimitada | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
