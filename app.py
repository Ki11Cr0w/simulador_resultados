# ==========================================
# APP.PY - VERSIÓN SIMPLE
# ==========================================

import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime

from validaciones import validar_ventas_sii

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
    
    # Intentar formatos comunes
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
        except:
            continue
    
    return None


def procesar_archivo_ventas(df):
    """Procesa el archivo de ventas."""
    documentos = []
    
    for _, fila in df.iterrows():
        # Obtener tipo de documento
        try:
            tipo_doc = int(float(fila.get('tipo_documento', 0) or 0))
        except:
            tipo_doc = 0
        
        # Aplicar factor negativo si es tipo 61
        factor = -1 if tipo_doc == 61 else 1
        
        # Obtener monto total
        try:
            monto_total = float(fila.get('monto_total', 0) or 0)
        except:
            monto_total = 0
        
        # Obtener fecha
        fecha_raw = fila.get('fecha_docto', '')
        fecha_dt = _parsear_fecha(fecha_raw)
        
        if fecha_dt:
            documentos.append({
                'fecha': fecha_dt,
                'monto': monto_total * factor,
                'tipo_doc': tipo_doc
            })
    
    return documentos


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

st.subheader("📥 Cargar Archivo de Ventas")

# Cargar archivo
archivo_ventas = st.file_uploader(
    "Selecciona archivo Excel de ventas", 
    type=["xlsx", "xls", "csv"]
)

if archivo_ventas:
    try:
        # Leer archivo según extensión
        if archivo_ventas.name.endswith('.csv'):
            df = pd.read_csv(archivo_ventas, sep=';', decimal=',')
        else:
            df = pd.read_excel(archivo_ventas)
        
        # Normalizar columnas
        df = normalizar_columnas(df)
        
        # Mostrar vista previa
        with st.expander("📋 Vista previa del archivo"):
            st.write(f"Filas: {len(df)}, Columnas: {len(df.columns)}")
            st.dataframe(df.head())
        
        # Verificar columnas requeridas
        columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
        columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
        
        if columnas_faltantes:
            st.error(f"❌ Faltan columnas requeridas: {', '.join(columnas_faltantes)}")
            st.info("Columnas disponibles:")
            st.write(list(df.columns))
        else:
            # Procesar archivo
            documentos = procesar_archivo_ventas(df)
            
            if documentos:
                st.success(f"✅ Archivo procesado correctamente")
                st.info(f"📄 Documentos válidos: {len(documentos)}")
                
                # ==========================================
                # CÁLCULOS SIMPLES
                # ==========================================
                
                # Agrupación por periodo
                periodo = st.selectbox(
                    "Agrupar por:",
                    ["Mensual", "Trimestral", "Anual"]
                )
                
                # Calcular resultados
                resumen = defaultdict(float)
                
                for doc in documentos:
                    fecha = doc['fecha']
                    
                    if periodo == "Mensual":
                        clave = f"{fecha.year}-{fecha.month:02d}"
                    elif periodo == "Trimestral":
                        trimestre = (fecha.month - 1) // 3 + 1
                        clave = f"{fecha.year}-T{trimestre}"
                    else:
                        clave = str(fecha.year)
                    
                    resumen[clave] += doc['monto']
                
                # Ordenar periodos
                periodos = sorted(resumen.keys())
                montos = [resumen[p] for p in periodos]
                
                # ==========================================
                # RESULTADOS
                # ==========================================
                
                st.subheader("📊 Resultados")
                
                # Métricas principales
                total_general = sum(montos)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total General", f"${total_general:,.0f}")
                col2.metric("Documentos", len(documentos))
                col3.metric("Periodos", len(periodos))
                
                # Tabla de resultados
                st.subheader("📋 Detalle por periodo")
                
                df_resultados = pd.DataFrame({
                    'Periodo': periodos,
                    'Total Ventas': montos,
                    '% del Total': [m/total_general*100 if total_general != 0 else 0 for m in montos]
                })
                
                st.dataframe(df_resultados.style.format({
                    'Total Ventas': '${:,.0f}',
                    '% del Total': '{:.1f}%'
                }))
                
                # Resumen estadístico
                with st.expander("📈 Estadísticas"):
                    if montos:
                        st.write(f"**Promedio por periodo:** ${sum(montos)/len(montos):,.0f}")
                        st.write(f"**Máximo:** ${max(montos):,.0f}")
                        st.write(f"**Mínimo:** ${min(montos):,.0f}")
                        
                        # Documentos tipo 61
                        docs_61 = [d for d in documentos if d['tipo_doc'] == 61]
                        if docs_61:
                            total_61 = sum(d['monto'] for d in docs_61)
                            st.write(f"**Documentos tipo 61:** {len(docs_61)} (Total: ${total_61:,.0f})")
                
            else:
                st.warning("⚠️ No se encontraron documentos con fecha válida")
    
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.exception(e)

else:
    st.info("👈 Por favor, carga un archivo Excel o CSV para comenzar")
    
    # Ejemplo de formato esperado
    with st.expander("📝 Formato esperado del archivo"):
        st.write("""
        El archivo debe contener al menos estas columnas:
        
        - **fecha_docto**: Fecha del documento (ej: 15/01/2024)
        - **tipo_documento**: Tipo de documento (61 = negativo, otros = positivo)
        - **monto_total**: Valor total del documento
        
        **Ejemplo de datos:**
        
        | fecha_docto | tipo_documento | monto_total |
        |-------------|----------------|-------------|
        | 15/01/2024 | 33             | 100000      |
        | 20/01/2024 | 61             | 50000       |
        | 25/01/2024 | 34             | 75000       |
        """)

# Pie de página
st.markdown("---")
st.caption("Versión simple - Solo ventas | Solo monto_total")
