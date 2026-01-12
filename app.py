# ==========================================
# APP.PY - VERSIÓN CORREGIDA (ERROR FECHA)
# ==========================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import io
from datetime import datetime

from validaciones import validar_ventas_sii, validar_compras_sii

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador de Resultado", layout="centered")
st.title("📊 Simulador de Resultado")

# ==========================================
# FUNCIONES AUXILIARES - CORREGIDAS
# ==========================================

def normalizar_columnas(df):
    """Normaliza nombres de columnas."""
    df = df.copy()
    df.columns = (df.columns
                  .astype(str)
                  .str.strip()
                  .str.lower()
                  .str.replace(' ', '_')
                  .str.replace('.', '', regex=False))
    return df


def _parsear_fecha(fecha_str):
    """Convierte string de fecha a objeto datetime de forma segura."""
    if pd.isna(fecha_str) or fecha_str in ['', 'nan', 'NaT', 'None']:
        return None
    
    fecha_str = str(fecha_str).strip()
    
    # Intentar diferentes formatos de fecha
    formatos = [
        '%Y-%m-%d',     # 2024-01-15
        '%d/%m/%Y',     # 15/01/2024
        '%d-%m-%Y',     # 15-01-2024
        '%Y%m%d',       # 20240115
        '%d.%m.%Y',     # 15.01.2024
    ]
    
    for formato in formatos:
        try:
            return datetime.strptime(fecha_str, formato)
        except (ValueError, TypeError):
            continue
    
    # Si no coincide ningún formato, intentar extraer números
    try:
        numeros = ''.join(filter(str.isdigit, fecha_str))
        if len(numeros) >= 8:
            return datetime.strptime(numeros[:8], '%Y%m%d')
    except:
        pass
    
    return None


def procesar_documento(fila, tipo):
    """Procesa un documento individual."""
    try:
        tipo_doc = int(float(fila.get('tipo_documento', 0) or 0))
    except:
        tipo_doc = 0
    
    factor = -1 if tipo_doc == 61 else 1
    
    try:
        neto = float(fila.get('monto_neto', 0) or 0)
    except:
        neto = 0
    
    try:
        exento = float(fila.get('monto_exento', 0) or 0)
    except:
        exento = 0
    
    try:
        total = float(fila.get('monto_total', 0) or 0)
    except:
        total = 0
    
    # Parsear fecha
    fecha_raw = fila.get('fecha_docto', '')
    fecha_dt = _parsear_fecha(fecha_raw)
    fecha_str = fecha_dt.strftime('%Y-%m-%d') if fecha_dt else ''
    
    return {
        'fecha': fecha_str,
        'fecha_dt': fecha_dt,
        'tipo': tipo,
        'neto': (neto + exento) * factor,
        'total': total * factor,
        'tipo_doc': tipo_doc
    }


def cargar_archivo(titulo, tipo):
    """Interfaz para cargar archivos."""
    st.subheader(titulo)
    archivo = st.file_uploader(f"Cargar {tipo}", type="csv", key=f"{tipo}_uploader")
    
    if not archivo:
        return []
    
    try:
        # Intentar diferentes encodings y separadores
        try:
            df = pd.read_csv(archivo, sep=';', decimal=',', encoding='utf-8')
        except:
            df = pd.read_csv(archivo, sep=',', decimal='.', encoding='latin-1')
        
        df = normalizar_columnas(df)
        
        # Validar columnas requeridas
        columnas_req = ['fecha_docto', 'tipo_documento']
        faltantes = [c for c in columnas_req if c not in df.columns]
        
        if faltantes:
            st.error(f"Faltan columnas: {', '.join(faltantes)}")
            st.write("Columnas disponibles:", list(df.columns))
            return []
        
        # Validar documentos
        validador = validar_ventas_sii if tipo == 'ventas' else validar_compras_sii
        df_val = validador(df)
        df_ok = df_val[df_val['valido']]
        
        st.success(f"{tipo.capitalize()} válidas: {len(df_ok)}")
        
        # Mostrar inválidos si existen
        df_inv = df_val[~df_val['valido']]
        if not df_inv.empty:
            with st.expander(f"⚠️ {len(df_inv)} {tipo} inválidas"):
                st.dataframe(df_inv.head(10))
        
        # Procesar documentos válidos
        documentos = []
        for _, fila in df_ok.iterrows():
            doc = procesar_documento(fila, tipo[:-1])
            if doc['fecha']:  # Solo agregar si tiene fecha válida
                documentos.append(doc)
        
        return documentos
    
    except Exception as e:
        st.error(f"Error al procesar {tipo}: {str(e)}")
        st.exception(e)
        return []


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

# Cargar datos
documentos = []
documentos += cargar_archivo("📥 Ventas SII", "ventas")
documentos += cargar_archivo("📤 Compras SII", "compras")

if not documentos:
    st.info("Carga archivos para comenzar")
    st.stop()

# Configuración
col1, col2 = st.columns(2)
with col1:
    tipo_analisis = st.radio(
        "Tipo de análisis",
        ["Resultado del negocio (sin impuestos)", "Movimiento de dinero (con impuestos)"]
    )
with col2:
    periodo = st.selectbox(
        "Periodo",
        ["Mensual", "Trimestral", "Anual"]
    )

# ==========================================
# CÁLCULOS - CORREGIDOS
# ==========================================

periodo_map = {"Mensual": "mensual", "Trimestral": "trimestral", "Anual": "anual"}
resumen = defaultdict(lambda: {"ingresos": 0, "gastos": 0})

for doc in documentos:
    if not doc['fecha_dt']:
        continue  # Saltar documentos sin fecha válida
    
    año = doc['fecha_dt'].year
    mes = doc['fecha_dt'].month
    
    if periodo == "Mensual":
        key = f"{año}-{mes:02d}"
    elif periodo == "Trimestral":
        trimestre = (mes - 1) // 3 + 1
        key = f"{año}-T{trimestre}"
    else:
        key = str(año)
    
    # Determinar valor según tipo de análisis
    if 'negocio' in tipo_analisis.lower():
        valor = doc['neto']
    else:
        valor = doc['total']
    
    if doc['tipo'] == 'ingreso':
        resumen[key]['ingresos'] += valor
    else:
        resumen[key]['gastos'] += valor

# Ordenar periodos
periodos = sorted(resumen.keys(), key=lambda x: (
    int(x.split('-')[0]),  # Año
    0 if 'T' in x else int(x.split('-')[1]) if '-' in x and 'T' not in x else 0,  # Mes
    int(x.split('T')[1]) if 'T' in x else 0  # Trimestre
))

ingresos = [resumen[p]['ingresos'] for p in periodos]
gastos = [resumen[p]['gastos'] for p in periodos]
resultados = [i - g for i, g in zip(ingresos, gastos)]

# ==========================================
# RESULTADOS
# ==========================================

st.subheader("📊 Resultados")

# Métricas
col1, col2, col3 = st.columns(3)
total_ingresos = sum(ingresos)
total_gastos = sum(gastos)
total_resultado = total_ingresos - total_gastos

col1.metric("Ingresos", f"${total_ingresos:,.0f}")
col2.metric("Gastos", f"${total_gastos:,.0f}")
col3.metric("Resultado", f"${total_resultado:,.0f}", 
            delta=f"{total_resultado/total_ingresos*100:.1f}%" if total_ingresos > 0 else None)

# Tabla detallada
st.subheader("📋 Detalle por periodo")
df_resumen = pd.DataFrame({
    'Periodo': periodos,
    'Ingresos': ingresos,
    'Gastos': gastos,
    'Resultado': resultados,
    'Margen (%)': [r/i*100 if i > 0 else 0 for i, r in zip(ingresos, resultados)]
})

st.dataframe(df_resumen.style.format({
    'Ingresos': '${:,.0f}',
    'Gastos': '${:,.0f}',
    'Resultado': '${:,.0f}',
    'Margen (%)': '{:.1f}%'
}))

# Gráficos
if periodos:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Gráfico de barras
    x = range(len(periodos))
    width = 0.35
    ax1.bar([i - width/2 for i in x], ingresos, width, label='Ingresos', color='#2ecc71', alpha=0.7)
    ax1.bar([i + width/2 for i in x], gastos, width, label='Gastos', color='#e74c3c', alpha=0.7)
    ax1.set_xlabel('Periodo')
    ax1.set_ylabel('Monto ($)')
    ax1.set_title('Ingresos vs Gastos')
    ax1.set_xticks(x)
    ax1.set_xticklabels(periodos, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Gráfico de resultado
    colors = ['#2ecc71' if r >= 0 else '#e74c3c' for r in resultados]
    ax2.bar(periodos, resultados, color=colors, alpha=0.7)
    ax2.set_xlabel('Periodo')
    ax2.set_ylabel('Resultado ($)')
    ax2.set_title('Resultado por periodo')
    ax2.set_xticklabels(periodos, rotation=45, ha='right')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig)

# Estadísticas adicionales
st.subheader("📈 Estadísticas")
col1, col2, col3 = st.columns(3)

con_fecha = len([d for d in documentos if d['fecha_dt']])
sin_fecha = len(documentos) - con_fecha

col1.metric("Documentos totales", len(documentos))
col2.metric("Con fecha válida", con_fecha)
col3.metric("Sin fecha válida", sin_fecha)

# Exportar
if st.button("📥 Exportar Resultados"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
        
        # Agregar hoja con documentos
        df_docs = pd.DataFrame(documentos)
        df_docs.to_excel(writer, sheet_name='Documentos', index=False)
    
    st.download_button(
        label="Descargar Excel",
        data=output.getvalue(),
        file_name="resultados_simulador.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Depuración (opcional)
with st.expander("🔍 Ver datos de depuración"):
    st.write(f"Total documentos procesados: {len(documentos)}")
    st.write("Primeros 5 documentos:", documentos[:5])
    st.write("Columnas del primer documento:", list(documentos[0].keys()) if documentos else [])
