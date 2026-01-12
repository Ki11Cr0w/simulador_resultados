# ==========================================
# APP.PY - VERSIÓN MEJORADA
# ==========================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import io

from validaciones import validar_ventas_sii, validar_compras_sii

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(page_title="Simulador de Resultado", layout="centered")
st.title("📊 Simulador de Resultado")

# ==========================================
# FUNCIONES AUXILIARES
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


def procesar_documento(fila, tipo):
    """Procesa un documento individual."""
    tipo_doc = int(fila.get('tipo_documento', 0) or 0)
    factor = -1 if tipo_doc == 61 else 1
    
    neto = float(fila.get('monto_neto', 0) or 0)
    exento = float(fila.get('monto_exento', 0) or 0)
    total = float(fila.get('monto_total', 0) or 0)
    
    return {
        'fecha': fila.get('fecha_docto', ''),
        'tipo': tipo,
        'neto': (neto + exento) * factor,
        'total': total * factor
    }


def cargar_archivo(titulo, tipo):
    """Interfaz para cargar archivos."""
    st.subheader(titulo)
    archivo = st.file_uploader(f"Cargar {tipo}", type="csv", key=f"{tipo}_uploader")
    
    if not archivo:
        return []
    
    try:
        df = pd.read_csv(archivo, sep=';', decimal=',')
        df = normalizar_columnas(df)
        
        # Validar
        validador = validar_ventas_sii if tipo == 'ventas' else validar_compras_sii
        df_val = validador(df)
        df_ok = df_val[df_val['valido']]
        
        st.success(f"{tipo.capitalize()} válidas: {len(df_ok)}")
        
        # Mostrar inválidos si existen
        df_inv = df_val[~df_val['valido']]
        if not df_inv.empty:
            with st.expander(f"⚠️ {len(df_inv)} {tipo} inválidas"):
                st.dataframe(df_inv[['fecha_docto', 'tipo_documento', 'diferencia']])
        
        # Procesar documentos válidos
        return [procesar_documento(fila, tipo[:-1]) for _, fila in df_ok.iterrows()]
    
    except Exception as e:
        st.error(f"Error al procesar {tipo}: {str(e)}")
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
        ["Resultado del negocio (sin impuestos)", "Movimiento de dinero (con impuestos)"],
        key="tipo_analisis"
    )
with col2:
    periodo = st.selectbox(
        "Periodo",
        ["Mensual", "Trimestral", "Anual"],
        key="periodo"
    )

# ==========================================
# CÁLCULOS
# ==========================================

periodo_map = {"Mensual": "mensual", "Trimestral": "trimestral", "Anual": "anual"}
resumen = defaultdict(lambda: {"ingresos": 0, "gastos": 0})

for doc in documentos:
    if not doc['fecha'] or len(doc['fecha']) < 7:
        continue
    
    año = doc['fecha'][:4]
    mes = int(doc['fecha'][5:7])
    
    if periodo == "Mensual":
        key = f"{año}-{mes:02d}"
    elif periodo == "Trimestral":
        trimestre = (mes - 1) // 3 + 1
        key = f"{año}-T{trimestre}"
    else:
        key = año
    
    if doc['tipo'] == 'ingreso':
        resumen[key]['ingresos'] += doc['neto' if 'negocio' in tipo_analisis else 'total']
    else:
        resumen[key]['gastos'] += doc['neto' if 'negocio' in tipo_analisis else 'total']

# Ordenar periodos
periodos = sorted(resumen.keys())
ingresos = [resumen[p]['ingresos'] for p in periodos]
gastos = [resumen[p]['gastos'] for p in periodos]
resultados = [i - g for i, g in zip(ingresos, gastos)]

# ==========================================
# RESULTADOS
# ==========================================

st.subheader("📊 Resultados")

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Ingresos", f"${sum(ingresos):,.0f}")
col2.metric("Gastos", f"${sum(gastos):,.0f}")
col3.metric("Resultado", f"${sum(resultados):,.0f}", 
            delta=f"{sum(resultados)/sum(ingresos)*100:.1f}%" if sum(ingresos) > 0 else None)

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
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

# Gráfico de barras
x = range(len(periodos))
width = 0.35
ax1.bar([i - width/2 for i in x], ingresos, width, label='Ingresos', color='green', alpha=0.7)
ax1.bar([i + width/2 for i in x], gastos, width, label='Gastos', color='red', alpha=0.7)
ax1.set_xlabel('Periodo')
ax1.set_ylabel('Monto ($)')
ax1.set_title('Ingresos vs Gastos')
ax1.set_xticks(x)
ax1.set_xticklabels(periodos, rotation=45, ha='right')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Gráfico de resultado
ax2.bar(periodos, resultados, color=['green' if r >= 0 else 'red' for r in resultados])
ax2.set_xlabel('Periodo')
ax2.set_ylabel('Resultado ($)')
ax2.set_title('Resultado por periodo')
ax2.set_xticklabels(periodos, rotation=45, ha='right')
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
st.pyplot(fig)

# Exportar
if st.button("📥 Exportar Resultados"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
    st.download_button(
        label="Descargar Excel",
        data=output.getvalue(),
        file_name="resultados_simulador.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
