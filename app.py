# ==========================================
# APP.PY - VERSIÓN CON PERÍODO POR ARCHIVO Y FORMATO MEJORADO
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


def detectar_periodo_predominante(fechas):
    """Detecta el período que predomina (mes, trimestre o año)."""
    if not fechas:
        return None
    
    # Contar por mes, trimestre y año
    contador_meses = defaultdict(int)
    contador_trimestres = defaultdict(int)
    contador_años = defaultdict(int)
    
    for fecha in fechas:
        mes_key = f"{fecha.year}-{fecha.month:02d}"
        trimestre = (fecha.month - 1) // 3 + 1
        trimestre_key = f"{fecha.year}-T{trimestre}"
        año_key = str(fecha.year)
        
        contador_meses[mes_key] += 1
        contador_trimestres[trimestre_key] += 1
        contador_años[año_key] += 1
    
    # Encontrar el más común para cada nivel
    mes_comun = max(contador_meses.items(), key=lambda x: x[1]) if contador_meses else (None, 0)
    trimestre_comun = max(contador_trimestres.items(), key=lambda x: x[1]) if contador_trimestres else (None, 0)
    año_comun = max(contador_años.items(), key=lambda x: x[1]) if contador_años else (None, 0)
    
    # Determinar qué nivel tiene mayor concentración
    total_fechas = len(fechas)
    concentracion_mes = mes_comun[1] / total_fechas if total_fechas > 0 else 0
    concentracion_trimestre = trimestre_comun[1] / total_fechas if total_fechas > 0 else 0
    concentracion_año = año_comun[1] / total_fechas if total_fechas > 0 else 0
    
    # Si hay alta concentración en un mes, sugerir mensual
    if concentracion_mes >= 0.7:  # 70% o más en un mes
        return "Mensual", mes_comun[0]
    elif concentracion_trimestre >= 0.6:  # 60% o más en un trimestre
        return "Trimestral", trimestre_comun[0]
    elif concentracion_año >= 0.5:  # 50% o más en un año
        return "Anual", año_comun[0]
    else:
        # Por defecto, usar mensual para detalle
        return "Mensual", None


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
if 'periodos_confirmados' not in st.session_state:
    st.session_state.periodos_confirmados = {}
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False

st.subheader("📥 Carga de Archivos Múltiples")

# ==========================================
# FUNCIÓN PARA PROCESAR UN ARCHIVO INDIVIDUAL
# ==========================================
def procesar_y_sugerir_periodo(archivo, tipo, numero):
    """Procesa un archivo y sugiere período predominante."""
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo, sep=';', decimal=',')
        else:
            df = pd.read_excel(archivo)
        
        df = normalizar_columnas(df)
        
        columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
        columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
        
        if columnas_faltantes:
            st.error(f"❌ {tipo} {numero}: Faltan columnas {columnas_faltantes}")
            return None
        
        # Procesar documentos
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
                    'archivo_origen': archivo.name,
                    'numero_archivo': numero
                })
                fechas_validas.append(fecha_dt)
        
        if not documentos:
            st.warning(f"⚠️ {tipo} {numero}: No se encontraron documentos con fecha válida")
            return None
        
        # Detectar período predominante
        periodo_sugerido, periodo_predominante = detectar_periodo_predominante(fechas_validas)
        
        # Mostrar información del archivo
        st.success(f"✅ {tipo} {numero} procesado: {len(documentos)} documentos")
        
        with st.expander(f"📊 Información de {tipo} {numero}"):
            # Estadísticas básicas
            total_monto = sum(d['monto'] for d in documentos)
            fechas = [d['fecha'] for d in documentos]
            fecha_min = min(fechas)
            fecha_max = max(fechas)
            
            st.write(f"**Nombre:** {archivo.name}")
            st.write(f"**Documentos procesados:** {len(documentos)}")
            st.write(f"**Total:** {_formatear_monto(total_monto)}")
            st.write(f"**Rango de fechas:** {fecha_min.strftime('%d/%m/%Y')} - {fecha_max.strftime('%d/%m/%Y')}")
            st.write(f"**Días cubiertos:** {(fecha_max - fecha_min).days}")
            
            # Sugerencia de período
            st.write("---")
            st.write("**🎯 SUGERENCIA DE PERÍODO:**")
            
            if periodo_predominante:
                st.success(f"**{periodo_sugerido}** - Período predominante: **{periodo_predominante}**")
            else:
                st.info(f"**{periodo_sugerido}** - Datos distribuidos en múltiples períodos")
            
            # Distribución por mes
            meses = {}
            for fecha in fechas:
                mes_key = f"{fecha.year}-{fecha.month:02d}"
                meses[mes_key] = meses.get(mes_key, 0) + 1
            
            if meses:
                st.write("**Distribución por mes:**")
                for mes, count in sorted(meses.items()):
                    porcentaje = (count / len(documentos)) * 100
                    st.write(f"  - {mes}: {count} documentos ({porcentaje:.1f}%)")
        
        # Solicitar confirmación/corrección del período
        st.write("---")
        st.write(f"**⚙️ Configurar período para {tipo} {numero}:**")
        
        # Opciones de período
        periodo_opciones = ["Mensual", "Trimestral", "Anual"]
        
        # Seleccionar período (por defecto la sugerencia)
        periodo_index = periodo_opciones.index(periodo_sugerido) if periodo_sugerido in periodo_opciones else 0
        
        periodo_seleccionado = st.radio(
            f"Seleccione el período de agrupación para {tipo} {numero}:",
            periodo_opciones,
            index=periodo_index,
            key=f"periodo_{tipo}_{numero}"
        )
        
        # Guardar en estado
        archivo_key = f"{tipo}_{numero}_{archivo.name}"
        st.session_state.periodos_confirmados[archivo_key] = periodo_seleccionado
        
        return documentos
    
    except Exception as e:
        st.error(f"❌ Error procesando {tipo} {numero}: {str(e)}")
        return None


# ==========================================
# SECCIÓN VENTAS - MÚLTIPLES ARCHIVOS CON PERÍODO INDIVIDUAL
# ==========================================
st.markdown("### 📋 Archivos de Ventas (máximo 3)")

ventas_files = []
ventas_documentos_totales = []

# Uploaders para ventas
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
        documentos = procesar_y_sugerir_periodo(ventas_file, "venta", numero)
        if documentos:
            ventas_documentos_totales.extend(documentos)
            
            # Guardar en estado
            st.session_state.archivos_ventas[ventas_file.name] = {
                'documentos': len(documentos),
                'numero': numero,
                'procesado': True
            }
    
    st.session_state.documentos_ventas = ventas_documentos_totales
    
    # Resumen de ventas
    if ventas_documentos_totales:
        total_ventas = sum(d['monto'] for d in ventas_documentos_totales)
        st.info(f"**📊 VENTAS ACUMULADAS:** {_formatear_monto(total_ventas)} ({len(ventas_documentos_totales)} documentos)")

# ==========================================
# SECCIÓN COMPRAS - MÚLTIPLES ARCHIVOS CON PERÍODO INDIVIDUAL
# ==========================================
st.markdown("### 📋 Archivos de Compras (máximo 3)")

compras_files = []
compras_documentos_totales = []

# Uploaders para compras
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
        documentos = procesar_y_sugerir_periodo(compras_file, "compra", numero)
        if documentos:
            compras_documentos_totales.extend(documentos)
            
            # Guardar en estado
            st.session_state.archivos_compras[compras_file.name] = {
                'documentos': len(documentos),
                'numero': numero,
                'procesado': True
            }
    
    st.session_state.documentos_compras = compras_documentos_totales
    
    # Resumen de compras
    if compras_documentos_totales:
        total_compras = sum(d['monto'] for d in compras_documentos_totales)
        st.info(f"**📊 COMPRAS ACUMULADAS:** {_formatear_monto(total_compras)} ({len(compras_documentos_totales)} documentos)")

# ==========================================
# CONFIGURACIÓN GLOBAL Y CÁLCULO
# ==========================================
st.markdown("---")

# Combinar todos los documentos
todos_documentos = st.session_state.documentos_ventas + st.session_state.documentos_compras

if todos_documentos:
    st.markdown("### ⚙️ Configuración Global del Análisis")
    
    # Determinar período global basado en los períodos confirmados
    periodos_usados = list(st.session_state.periodos_confirmados.values())
    
    if periodos_usados:
        # Usar el período más común entre los archivos
        from collections import Counter
        periodo_counter = Counter(periodos_usados)
        periodo_global = periodo_counter.most_common(1)[0][0]
    else:
        periodo_global = "Mensual"  # Por defecto
    
    st.info(f"**📅 Período global sugerido:** **{periodo_global}** (basado en archivos cargados)")
    
    # Opción para cambiar el período global
    periodo_final = st.selectbox(
        "Período final para el análisis completo:",
        ["Mensual", "Trimestral", "Anual"],
        index=["Mensual", "Trimestral", "Anual"].index(periodo_global)
    )
    
    # Botón para calcular
    st.markdown("---")
    
    if st.button("🚀 CALCULAR RESULTADOS COMPLETOS", type="primary", use_container_width=True):
        st.session_state.mostrar_resultados = True
        st.session_state.periodo_final = periodo_final
        st.rerun()

# ==========================================
# CÁLCULOS COMPLETOS CON FORMATO MEJORADO
# ==========================================
if st.session_state.mostrar_resultados and todos_documentos:
    st.markdown("---")
    st.subheader("📊 RESULTADOS DEL ANÁLISIS")
    
    # ==========================================
    # MÉTRICAS PRINCIPALES EN FORMATO VERTICAL
    # ==========================================
    st.markdown("### 🎯 MÉTRICAS PRINCIPALES")
    
    # Agrupar por período final
    resumen = defaultdict(lambda: {
        'ventas': 0, 
        'compras': 0, 
        'resultado': 0,
        'documentos_ventas': 0,
        'documentos_compras': 0
    })
    
    for doc in todos_documentos:
        fecha = doc['fecha']
        
        if st.session_state.periodo_final == "Mensual":
            clave = f"{fecha.year}-{fecha.month:02d}"
        elif st.session_state.periodo_final == "Trimestral":
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
    
    # Cálculos totales
    total_ventas = sum(resumen[p]['ventas'] for p in periodos)
    total_compras = sum(resumen[p]['compras'] for p in periodos)
    total_resultado = total_ventas - total_compras
    total_documentos = len(todos_documentos)
    
    # Mostrar métricas en formato vertical (una debajo de otra)
    metricas_container = st.container()
    
    with metricas_container:
        # Crear columnas para mejor layout
        col1, col2 = st.columns(2)
        
        with col1:
            # Ventas
            st.markdown("### 📥 VENTAS TOTALES")
            st.markdown(f"<h1 style='text-align: center; color: {'#2ecc71' if total_ventas >= 0 else '#e74c3c'};'>{_formatear_monto(total_ventas)}</h1>", 
                       unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>Documentos: {sum(resumen[p]['documentos_ventas'] for p in periodos)}</p>", 
                       unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Compras
            st.markdown("### 📤 COMPRAS TOTALES")
            st.markdown(f"<h1 style='text-align: center; color: {'#2ecc71' if total_compras >= 0 else '#e74c3c'};'>{_formatear_monto(total_compras)}</h1>", 
                       unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>Documentos: {sum(resumen[p]['documentos_compras'] for p in periodos)}</p>", 
                       unsafe_allow_html=True)
        
        with col2:
            # Resultado Neto
            st.markdown("### 💰 RESULTADO NETO")
            color_resultado = "#2ecc71" if total_resultado >= 0 else "#e74c3c"
            st.markdown(f"<h1 style='text-align: center; color: {color_resultado};'>{_formatear_monto(total_resultado)}</h1>", 
                       unsafe_allow_html=True)
            
            # Calcular margen
            if total_ventas != 0:
                margen = (total_resultado / abs(total_ventas)) * 100
                st.markdown(f"<p style='text-align: center; font-size: 1.5rem; color: {color_resultado};'>Margen: {margen:+.1f}%</p>", 
                           unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Total Documentos
            st.markdown("### 📄 TOTAL DOCUMENTOS")
            st.markdown(f"<h1 style='text-align: center; color: #3498db;'>{total_documentos}</h1>", 
                       unsafe_allow_html=True)
            
            # Desglose
            docs_ventas = sum(resumen[p]['documentos_ventas'] for p in periodos)
            docs_compras = sum(resumen[p]['documentos_compras'] for p in periodos)
            st.markdown(f"<p style='text-align: center;'>Ventas: {docs_ventas} | Compras: {docs_compras}</p>", 
                       unsafe_allow_html=True)
    
    # ==========================================
    # TABLA DE RESULTADOS POR PERÍODO
    # ==========================================
    st.markdown("---")
    st.markdown("### 📋 RESULTADOS POR PERÍODO")
    
    df_resultados = pd.DataFrame({
        'Período': periodos,
        'Ventas': [resumen[p]['ventas'] for p in periodos],
        'Compras': [resumen[p]['compras'] for p in periodos],
        'Resultado': [resumen[p]['resultado'] for p in periodos],
        'Docs V': [resumen[p]['documentos_ventas'] for p in periodos],
        'Docs C': [resumen[p]['documentos_compras'] for p in periodos],
        'Margen %': [
            (resumen[p]['resultado'] / resumen[p]['ventas'] * 100) if resumen[p]['ventas'] != 0 else 0 
            for p in periodos
        ]
    })
    
    # Función para formatear con color
    def colorizar_resultado(val):
        if isinstance(val, (int, float)) and val < 0:
            return 'color: #e74c3c; font-weight: bold;'
        elif isinstance(val, (int, float)) and val > 0:
            return 'color: #2ecc71; font-weight: bold;'
        return ''
    
    # Formatear tabla
    styled_df = df_resultados.style.format({
        'Ventas': lambda x: _formatear_monto(x),
        'Compras': lambda x: _formatear_monto(x),
        'Resultado': lambda x: _formatear_monto(x),
        'Margen %': '{:+.1f}%'
    }).applymap(colorizar_resultado, subset=['Resultado', 'Margen %'])
    
    st.dataframe(styled_df, height=400)
    
    # ==========================================
    # RESUMEN DE ARCHIVOS CARGADOS
    # ==========================================
    with st.expander("📦 RESUMEN DE ARCHIVOS CARGADOS"):
        if st.session_state.archivos_ventas:
            st.markdown("#### 📥 Archivos de Ventas")
            for archivo, info in st.session_state.archivos_ventas.items():
                periodo = st.session_state.periodos_confirmados.get(f"venta_{info['numero']}_{archivo}", "No confirmado")
                st.write(f"• **{archivo}** - {info['documentos']} documentos - Período: {periodo}")
        
        if st.session_state.archivos_compras:
            st.markdown("#### 📤 Archivos de Compras")
            for archivo, info in st.session_state.archivos_compras.items():
                periodo = st.session_state.periodos_confirmados.get(f"compra_{info['numero']}_{archivo}", "No confirmado")
                st.write(f"• **{archivo}** - {info['documentos']} documentos - Período: {periodo}")
    
    # ==========================================
    # ESTADÍSTICAS ADICIONALES
    # ==========================================
    with st.expander("📈 ESTADÍSTICAS ADICIONALES"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Documentos tipo 61
            ventas_61 = len([d for d in todos_documentos if d['tipo'] == 'venta' and d['tipo_doc'] == 61])
            compras_61 = len([d for d in todos_documentos if d['tipo'] == 'compra' and d['tipo_doc'] == 61])
            
            st.markdown("**📝 Documentos tipo 61 (Notas de crédito):**")
            st.write(f"- Ventas: {ventas_61} documentos")
            st.write(f"- Compras: {compras_61} documentos")
            
            if ventas_61 > 0 or compras_61 > 0:
                total_61 = ventas_61 + compras_61
                porcentaje_61 = (total_61 / total_documentos) * 100
                st.write(f"- **Total:** {total_61} documentos ({porcentaje_61:.1f}% del total)")
        
        with col2:
            # Promedios
            if len(st.session_state.documentos_ventas) > 0:
                promedio_venta = total_ventas / len(st.session_state.documentos_ventas)
                st.markdown("**📊 Promedio por documento:**")
                st.write(f"- Venta promedio: {_formatear_monto(promedio_venta)}")
            
            if len(st.session_state.documentos_compras) > 0:
                promedio_compra = total_compras / len(st.session_state.documentos_compras)
                st.write(f"- Compra promedio: {_formatear_monto(promedio_compra)}")
    
    # ==========================================
    # BOTONES FINALES
    # ==========================================
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 NUEVO ANÁLISIS", type="secondary", use_container_width=True):
            # Resetear todo
            keys_to_reset = ['documentos_ventas', 'documentos_compras', 'archivos_ventas', 
                           'archivos_compras', 'periodos_confirmados', 'mostrar_resultados']
            for key in keys_to_reset:
                if key in st.session_state:
                    if 'archivos' in key or 'periodos' in key:
                        st.session_state[key] = {}
                    else:
                        st.session_state[key] = []
            st.rerun()
    
    with col2:
        if st.button("📋 COPIAR RESUMEN", type="primary", use_container_width=True):
            # Crear resumen textual
            resumen_texto = f"""
            RESUMEN DE ANÁLISIS
            ===================
            Período: {st.session_state.periodo_final}
            Fecha de análisis: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            
            MÉTRICAS PRINCIPALES:
            --------------------
            Ventas Totales: {_formatear_monto(total_ventas)}
            Compras Totales: {_formatear_monto(total_compras)}
            Resultado Neto: {_formatear_monto(total_resultado)}
            Total Documentos: {total_documentos}
            
            ARCHIVOS PROCESADOS:
            -------------------
            Ventas: {len(st.session_state.archivos_ventas)} archivo(s)
            Compras: {len(st.session_state.archivos_compras)} archivo(s)
            
            PERÍODOS ANALIZADOS:
            -------------------
            {', '.join(periodos)}
            """
            
            st.code(resumen_texto, language='text')
            st.success("✅ Resumen listo para copiar")

# Mensaje inicial si no hay archivos
if not todos_documentos and not st.session_state.mostrar_resultados:
    st.info("👈 Comienza cargando archivos de ventas y compras")

# Pie de página
st.markdown("---")
st.caption(f"© {datetime.now().year} - Simulador de Resultados | Período por archivo + Formato mejorado")
