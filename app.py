# ==========================================
# APP.PY - ACTUALIZADO CON IVA RECUPERABLE EN COSTOS
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
# FUNCIONES AUXILIARES - CON IVA RECUPERABLE
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
    
    formatos = [
        '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y%m%d', '%d.%m.%Y',
        '%Y/%m/%d', '%m/%d/%Y'
    ]
    
    for formato in formatos:
        try:
            return datetime.strptime(fecha_str, formato)
        except:
            continue
    
    # Extraer números
    try:
        numeros = ''.join(filter(str.isdigit, fecha_str))
        if len(numeros) >= 8:
            return datetime.strptime(numeros[:8], '%Y%m%d')
    except:
        pass
    
    return None


def _obtener_valor(fila, clave, default=0):
    """Obtiene valor numérico de forma segura."""
    try:
        return float(fila.get(clave, default) or default)
    except:
        return default


def procesar_documento_venta(fila):
    """Procesa un documento de venta."""
    tipo_doc = int(_obtener_valor(fila, 'tipo_documento', 0))
    factor = -1 if tipo_doc == 61 else 1
    
    neto = _obtener_valor(fila, 'monto_neto', 0)
    exento = _obtener_valor(fila, 'monto_exento', 0)
    total = _obtener_valor(fila, 'monto_total', 0)
    
    fecha_raw = fila.get('fecha_docto', '')
    fecha_dt = _parsear_fecha(fecha_raw)
    fecha_str = fecha_dt.strftime('%Y-%m-%d') if fecha_dt else ''
    
    return {
        'fecha': fecha_str,
        'fecha_dt': fecha_dt,
        'tipo': 'ingreso',
        'neto': (neto + exento) * factor,      # Sin impuestos
        'total': total * factor,               # Con impuestos
        'iva': _obtener_valor(fila, 'monto_iva', 0) * factor,
        'tipo_doc': tipo_doc
    }


def procesar_documento_compra(fila):
    """Procesa un documento de compra (CON IVA RECUPERABLE)."""
    tipo_doc = int(_obtener_valor(fila, 'tipo_documento', 0))
    factor = -1 if tipo_doc == 61 else 1
    
    neto = _obtener_valor(fila, 'monto_neto', 0)
    exento = _obtener_valor(fila, 'monto_exento', 0)
    total = _obtener_valor(fila, 'monto_total', 0)
    iva = _obtener_valor(fila, 'monto_iva', 0)
    iva_recuperable = _obtener_valor(fila, 'monto_iva_recuperable', 0)
    
    fecha_raw = fila.get('fecha_docto', '')
    fecha_dt = _parsear_fecha(fecha_raw)
    fecha_str = fecha_dt.strftime('%Y-%m-%d') if fecha_dt else ''
    
    # NETO: base afecta + exenta (sin impuestos)
    neto_total = (neto + exento) * factor
    
    # TOTAL CON IMPUESTOS: incluye IVA no recuperable
    total_con_impuestos = total * factor
    
    # COSTO REAL (para análisis de negocio): neto + IVA no recuperable
    # Si hay IVA recuperable, no es costo real del negocio
    iva_no_recuperable = max(0, iva - iva_recuperable)
    costo_real = (neto + exento + iva_no_recuperable) * factor
    
    return {
        'fecha': fecha_str,
        'fecha_dt': fecha_dt,
        'tipo': 'gasto',
        'neto': neto_total,                    # Solo base afecta + exenta
        'costo_real': costo_real,              # Base + IVA no recuperable
        'total': total_con_impuestos,          # Total del documento
        'iva': iva * factor,
        'iva_recuperable': iva_recuperable * factor,
        'iva_no_recuperable': iva_no_recuperable * factor,
        'tipo_doc': tipo_doc
    }


def cargar_archivo(titulo, tipo):
    """Interfaz para cargar archivos."""
    st.subheader(titulo)
    archivo = st.file_uploader(f"Cargar {tipo}", type="csv", key=f"{tipo}_uploader")
    
    if not archivo:
        return []
    
    try:
        # Leer archivo
        try:
            df = pd.read_csv(archivo, sep=';', decimal=',', encoding='utf-8')
        except:
            df = pd.read_csv(archivo, sep=',', decimal='.', encoding='latin-1')
        
        df = normalizar_columnas(df)
        
        # Validar columnas mínimas
        if 'fecha_docto' not in df.columns or 'tipo_documento' not in df.columns:
            st.error("El archivo no tiene las columnas requeridas: fecha_docto, tipo_documento")
            return []
        
        # Validar documentos
        validador = validar_ventas_sii if tipo == 'ventas' else validar_compras_sii
        df_val = validador(df)
        df_ok = df_val[df_val['valido']]
        
        st.success(f"✅ {tipo.capitalize()} válidas: {len(df_ok)}")
        
        # Mostrar inválidos
        df_inv = df_val[~df_val['valido']]
        if not df_inv.empty:
            with st.expander(f"⚠️ {len(df_inv)} {tipo} con diferencias > $1"):
                st.dataframe(df_inv[['fecha_docto', 'tipo_documento', 'diferencia']].head(20))
        
        # Procesar documentos
        documentos = []
        procesador = procesar_documento_venta if tipo == 'ventas' else procesar_documento_compra
        
        for _, fila in df_ok.iterrows():
            doc = procesador(fila)
            if doc['fecha_dt']:
                documentos.append(doc)
        
        # Estadísticas
        if documentos:
            total_monto = sum(d['total'] for d in documentos)
            st.info(f"💰 Total {tipo}: ${total_monto:,.0f}")
        
        return documentos
    
    except Exception as e:
        st.error(f"❌ Error al procesar {tipo}: {str(e)}")
        return []


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

# Cargar datos
st.markdown("---")
documentos = []
documentos += cargar_archivo("📥 Ventas SII", "ventas")
st.markdown("---")
documentos += cargar_archivo("📤 Compras SII", "compras")
st.markdown("---")

if not documentos:
    st.info("👈 Carga archivos CSV para comenzar")
    st.stop()

# Configuración
st.subheader("⚙️ Configuración del análisis")
col1, col2 = st.columns(2)

with col1:
    tipo_analisis = st.radio(
        "Tipo de análisis",
        ["Resultado del negocio", "Movimiento de dinero"],
        help="""• Resultado del negocio: Ventas netas vs Costos reales (sin IVA recuperable)
        • Movimiento de dinero: Ingresos totales vs Egresos totales"""
    )

with col2:
    periodo = st.selectbox(
        "Agrupación",
        ["Mensual", "Trimestral", "Anual"]
    )

# ==========================================
# CÁLCULOS - CON IVA RECUPERABLE CONSIDERADO
# ==========================================

resumen = defaultdict(lambda: {"ingresos": 0, "gastos": 0, "gastos_reales": 0})

for doc in documentos:
    if not doc['fecha_dt']:
        continue
    
    año = doc['fecha_dt'].year
    mes = doc['fecha_dt'].month
    
    if periodo == "Mensual":
        key = f"{año}-{mes:02d}"
    elif periodo == "Trimestral":
        trimestre = (mes - 1) // 3 + 1
        key = f"{año}-T{trimestre}"
    else:
        key = str(año)
    
    # INGRESOS (siempre de ventas)
    if doc['tipo'] == 'ingreso':
        if tipo_analisis == "Resultado del negocio":
            resumen[key]['ingresos'] += doc['neto']  # Sin impuestos
        else:
            resumen[key]['ingresos'] += doc['total']  # Con impuestos
    
    # GASTOS (compras)
    elif doc['tipo'] == 'gasto':
        if tipo_analisis == "Resultado del negocio":
            # Para resultado del negocio: usar costo_real (neto + IVA no recuperable)
            resumen[key]['gastos'] += doc.get('costo_real', doc['neto'])
            resumen[key]['gastos_reales'] += doc.get('costo_real', doc['neto'])
        else:
            # Para flujo de dinero: usar total del documento
            resumen[key]['gastos'] += doc['total']
            resumen[key]['gastos_reales'] += doc['total']

# Ordenar periodos
def _key_periodo(p):
    """Función para ordenar periodos correctamente."""
    if '-' in p and 'T' in p:  # 2024-T1
        año, trim = p.split('-T')
        return (int(año), 0, int(trim))
    elif '-' in p and 'T' not in p:  # 2024-01
        año, mes = p.split('-')
        return (int(año), int(mes), 0)
    else:  # 2024
        return (int(p), 0, 0)

periodos = sorted(resumen.keys(), key=_key_periodo)
ingresos = [resumen[p]['ingresos'] for p in periodos]
gastos = [resumen[p]['gastos'] for p in periodos]
resultados = [i - g for i, g in zip(ingresos, gastos)]

# ==========================================
# RESULTADOS
# ==========================================

st.subheader("📊 Resultados Finales")

# Métricas principales
total_ingresos = sum(ingresos)
total_gastos = sum(gastos)
total_resultado = total_ingresos - total_gastos
margen = (total_resultado / total_ingresos * 100) if total_ingresos > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ingresos", f"${total_ingresos:,.0f}")
col2.metric("Gastos", f"${total_gastos:,.0f}")
col3.metric("Resultado", f"${total_resultado:,.0f}")
col4.metric("Margen", f"{margen:.1f}%", 
           delta_color="normal" if margen >= 0 else "inverse")

# Tabla detallada
st.subheader("📋 Detalle por periodo")
df_resumen = pd.DataFrame({
    'Periodo': periodos,
    'Ingresos': ingresos,
    'Gastos': gastos,
    'Resultado': resultados,
    'Margen %': [r/i*100 if i > 0 else 0 for i, r in zip(ingresos, resultados)]
})

st.dataframe(df_resumen.style.format({
    'Ingresos': '${:,.0f}',
    'Gastos': '${:,.0f}',
    'Resultado': '${:,.0f}',
    'Margen %': '{:.1f}%'
}).applymap(
    lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '',
    subset=['Resultado', 'Margen %']
))

# Gráficos
if len(periodos) > 0:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Gráfico 1: Barras apiladas
    x_pos = range(len(periodos))
    ax1.bar(x_pos, ingresos, width=0.6, label='Ingresos', color='#27ae60', alpha=0.8)
    ax1.bar(x_pos, [-g for g in gastos], width=0.6, label='Gastos', color='#e74c3c', alpha=0.8)
    ax1.axhline(y=0, color='black', linewidth=0.8)
    ax1.set_xlabel('Periodo')
    ax1.set_ylabel('Monto ($)')
    ax1.set_title('Ingresos vs Gastos')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(periodos, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Gráfico 2: Resultado con línea de tendencia
    colors = ['#27ae60' if r >= 0 else '#e74c3c' for r in resultados]
    bars = ax2.bar(periodos, resultados, color=colors, alpha=0.7, width=0.6)
    ax2.axhline(y=0, color='black', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Periodo')
    ax2.set_ylabel('Resultado ($)')
    ax2.set_title('Resultado por Periodo')
    ax2.set_xticklabels(periodos, rotation=45, ha='right')
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # Agregar valores en barras
    for bar, valor in zip(bars, resultados):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., 
                height + (0.02 * max(resultados) if height >= 0 else -0.05 * max(map(abs, resultados))),
                f'${valor:,.0f}', ha='center', va='bottom' if height >= 0 else 'top',
                fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig)

# Estadísticas avanzadas
with st.expander("📈 Estadísticas Avanzadas"):
    # Separar ventas y compras
    ventas = [d for d in documentos if d['tipo'] == 'ingreso']
    compras = [d for d in documentos if d['tipo'] == 'gasto']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Ventas", len(ventas))
        if ventas:
            total_ventas = sum(v['total'] for v in ventas)
            st.write(f"Valor: ${total_ventas:,.0f}")
    
    with col2:
        st.metric("Total Compras", len(compras))
        if compras:
            total_compras = sum(c['total'] for c in compras)
            st.write(f"Valor: ${total_compras:,.0f}")
            
            # Calcular IVA recuperable total
            iva_rec_total = sum(c.get('iva_recuperable', 0) for c in compras)
            st.write(f"IVA Recuperable: ${iva_rec_total:,.0f}")
    
    with col3:
        ratio = len(compras)/len(ventas) if ventas else 0
        st.metric("Ratio Compra/Venta", f"{ratio:.2f}")
        st.write(f"Documentos con fecha: {len([d for d in documentos if d['fecha_dt']])}")

# Exportar resultados
st.subheader("💾 Exportar")
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Descargar Excel", use_container_width=True):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja de documentos detallados
            df_docs = pd.DataFrame([
                {
                    'Fecha': d['fecha'],
                    'Tipo': d['tipo'],
                    'Neto': d['neto'],
                    'Total': d['total'],
                    'IVA Recuperable': d.get('iva_recuperable', 0) if d['tipo'] == 'gasto' else 0,
                    'Tipo Doc': d.get('tipo_doc', 0)
                }
                for d in documentos if d['fecha_dt']
            ])
            df_docs.to_excel(writer, sheet_name='Documentos', index=False)
        
        st.download_button(
            label="⬇️ Hacer click para descargar",
            data=output.getvalue(),
            file_name=f"resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with col2:
    if st.button("🔄 Reiniciar", type="secondary", use_container_width=True):
        st.rerun()
