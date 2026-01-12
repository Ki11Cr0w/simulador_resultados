# ==========================================
# APP.PY - VERSIÓN COMPLETA
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


def _obtener_valor(fila, clave, default=0):
    """Obtiene valor numérico de forma segura."""
    try:
        valor = fila.get(clave, default)
        if pd.isna(valor):
            return default
        return float(valor)
    except:
        return default


def _buscar_otros_impuestos(fila):
    """Busca y suma todos los otros impuestos en la fila."""
    total_otros = 0
    
    # Buscar por patrones en nombres de columnas
    for col in fila.index:
        col_lower = col.lower()
        if ('otro_imp' in col_lower or 'otros_imp' in col_lower or 
            'valor_imp' in col_lower and 'iva' not in col_lower):
            total_otros += _obtener_valor(fila, col)
    
    return total_otros


def procesar_documento_venta(fila):
    """Procesa un documento de venta."""
    tipo_doc = int(_obtener_valor(fila, 'tipo_documento', 0))
    factor = -1 if tipo_doc == 61 else 1
    
    neto = _obtener_valor(fila, 'monto_neto', 0)
    exento = _obtener_valor(fila, 'monto_exento', 0)
    iva = _obtener_valor(fila, 'monto_iva', 0)
    total = _obtener_valor(fila, 'monto_total', 0)
    otros_impuestos = _buscar_otros_impuestos(fila)
    
    fecha_raw = fila.get('fecha_docto', '')
    fecha_dt = _parsear_fecha(fecha_raw)
    fecha_str = fecha_dt.strftime('%Y-%m-%d') if fecha_dt else ''
    
    # TOTAL COMPLETO: Neto + Exento + IVA + Otros Impuestos
    total_completo = (neto + exento + iva + otros_impuestos) * factor
    
    return {
        'fecha': fecha_str,
        'fecha_dt': fecha_dt,
        'tipo': 'ingreso',
        'neto': (neto + exento) * factor,
        'total': total_completo,  # AHORA: Incluye TODO
        'iva': iva * factor,
        'otros_impuestos': otros_impuestos * factor,
        'tipo_doc': tipo_doc
    }


def procesar_documento_compra(fila):
    """Procesa un documento de compra (TODO INCLUIDO)."""
    tipo_doc = int(_obtener_valor(fila, 'tipo_documento', 0))
    factor = -1 if tipo_doc == 61 else 1
    
    neto = _obtener_valor(fila, 'monto_neto', 0)
    exento = _obtener_valor(fila, 'monto_exento', 0)
    iva = _obtener_valor(fila, 'monto_iva', 0)
    iva_recuperable = _obtener_valor(fila, 'monto_iva_recuperable', 0)
    otros_impuestos = _buscar_otros_impuestos(fila)
    
    fecha_raw = fila.get('fecha_docto', '')
    fecha_dt = _parsear_fecha(fecha_raw)
    fecha_str = fecha_dt.strftime('%Y-%m-%d') if fecha_dt else ''
    
    # CALCULAR TOTAL COMPLETO: Neto + Exento + IVA + Otros Impuestos
    total_completo = (neto + exento + iva + otros_impuestos) * factor
    
    # COSTO REAL DEL NEGOCIO: Neto + Exento + (IVA - IVA Recuperable) + Otros Impuestos
    iva_no_recuperable = max(0, iva - iva_recuperable)
    costo_real_negocio = (neto + exento + iva_no_recuperable + otros_impuestos) * factor
    
    return {
        'fecha': fecha_str,
        'fecha_dt': fecha_dt,
        'tipo': 'gasto',
        'neto': (neto + exento) * factor,
        'total': total_completo,  # AHORA: Incluye TODO
        'costo_real': costo_real_negocio,
        'iva': iva * factor,
        'iva_recuperable': iva_recuperable * factor,
        'iva_no_recuperable': iva_no_recuperable * factor,
        'otros_impuestos': otros_impuestos * factor,
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
        
        # Mostrar columnas para debugging
        with st.expander("🔍 Ver columnas del archivo"):
            st.write(f"Columnas encontradas ({len(df.columns)}):")
            st.write(list(df.columns))
        
        # Validar columnas mínimas
        columnas_requeridas = ['fecha_docto', 'tipo_documento']
        faltantes = [c for c in columnas_requeridas if c not in df.columns]
        
        if faltantes:
            st.error(f"Faltan columnas requeridas: {', '.join(faltantes)}")
            return []
        
        # Validar documentos
        validador = validar_ventas_sii if tipo == 'ventas' else validar_compras_sii
        df_val = validador(df)
        df_ok = df_val[df_val['valido']]
        
        st.success(f"✅ {tipo.capitalize()} válidas: {len(df_ok)}")
        
        # Mostrar estadísticas de otros impuestos
        if 'otros_impuestos' in df_val.columns:
            total_otros = df_val['otros_impuestos'].sum()
            if total_otros > 0:
                st.info(f"💰 Otros impuestos detectados: ${total_otros:,.0f}")
        
        # Mostrar inválidos
        df_inv = df_val[~df_val['valido']]
        if not df_inv.empty:
            with st.expander(f"⚠️ {len(df_inv)} {tipo} con diferencias > $1"):
                st.dataframe(df_inv[['fecha_docto', 'tipo_documento', 'diferencia', 'otros_impuestos']].head(20))
        
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
            st.info(f"📊 Total {tipo} (todo incluido): ${total_monto:,.0f}")
            
            # Mostrar desglose si hay otros impuestos
            total_otros = sum(d.get('otros_impuestos', 0) for d in documentos)
            if total_otros > 0:
                st.info(f"   ↳ Incluye otros impuestos: ${total_otros:,.0f}")
        
        return documentos
    
    except Exception as e:
        st.error(f"❌ Error al procesar {tipo}: {str(e)}")
        st.exception(e)
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

tipo_analisis = st.radio(
    "Tipo de análisis",
    ["Resultado del negocio", "Movimiento de dinero"],
    help="""• Resultado del negocio: Ventas netas vs Costos reales (sin IVA recuperable)
    • Movimiento de dinero: Ingresos totales vs Egresos totales (TODO incluido)""",
    horizontal=True
)

periodo = st.selectbox(
    "Agrupación por periodo",
    ["Mensual", "Trimestral", "Anual"]
)

# ==========================================
# CÁLCULOS - TODO INCLUIDO
# ==========================================

resumen = defaultdict(lambda: {
    "ingresos": 0, 
    "gastos": 0, 
    "gastos_reales": 0,
    "otros_impuestos": 0
})

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
    
    # Registrar otros impuestos
    resumen[key]['otros_impuestos'] += doc.get('otros_impuestos', 0)
    
    # INGRESOS (ventas)
    if doc['tipo'] == 'ingreso':
        if tipo_analisis == "Resultado del negocio":
            # Para análisis de negocio: usar solo neto (sin impuestos)
            resumen[key]['ingresos'] += doc['neto']
        else:
            # Para flujo de dinero: usar TOTAL (todo incluido)
            resumen[key]['ingresos'] += doc['total']
    
    # GASTOS (compras)
    elif doc['tipo'] == 'gasto':
        if tipo_analisis == "Resultado del negocio":
            # Para análisis de negocio: usar costo_real (sin IVA recuperable)
            resumen[key]['gastos'] += doc.get('costo_real', doc['total'])
            resumen[key]['gastos_reales'] += doc.get('costo_real', doc['total'])
        else:
            # Para flujo de dinero: usar TOTAL (todo incluido)
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
otros_impuestos = [resumen[p]['otros_impuestos'] for p in periodos]
resultados = [i - g for i, g in zip(ingresos, gastos)]

# ==========================================
# RESULTADOS
# ==========================================

st.subheader("📊 Resultados Finales")

# Métricas principales
total_ingresos = sum(ingresos)
total_gastos = sum(gastos)
total_resultado = total_ingresos - total_gastos
total_otros_impuestos = sum(otros_impuestos)
margen = (total_resultado / total_ingresos * 100) if total_ingresos > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ingresos", f"${total_ingresos:,.0f}")
col2.metric("Gastos", f"${total_gastos:,.0f}")
col3.metric("Resultado", f"${total_resultado:,.0f}")
col4.metric("Margen", f"{margen:.1f}%", 
           delta_color="normal" if margen >= 0 else "inverse")

# Mostrar otros impuestos si existen
if total_otros_impuestos > 0:
    st.info(f"📌 **Otros impuestos totales detectados:** ${total_otros_impuestos:,.0f}")

# Tabla detallada
st.subheader("📋 Detalle por periodo")

df_resumen = pd.DataFrame({
    'Periodo': periodos,
    'Ingresos': ingresos,
    'Gastos': gastos,
    'Resultado': resultados,
    'Otros Impuestos': otros_impuestos,
    'Margen %': [r/i*100 if i > 0 else 0 for i, r in zip(ingresos, resultados)]
})

# Formatear tabla
formato = {
    'Ingresos': '${:,.0f}',
    'Gastos': '${:,.0f}',
    'Resultado': '${:,.0f}',
    'Otros Impuestos': '${:,.0f}',
    'Margen %': '{:.1f}%'
}

st.dataframe(df_resumen.style.format(formato).applymap(
    lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '',
    subset=['Resultado', 'Margen %']
))

# Gráficos
if len(periodos) > 0:
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # Gráfico 1: Barras apiladas (Ingresos vs Gastos)
    x_pos = range(len(periodos))
    axes[0, 0].bar(x_pos, ingresos, width=0.6, label='Ingresos', color='#27ae60', alpha=0.8)
    axes[0, 0].bar(x_pos, [-g for g in gastos], width=0.6, label='Gastos', color='#e74c3c', alpha=0.8)
    axes[0, 0].axhline(y=0, color='black', linewidth=0.8)
    axes[0, 0].set_xlabel('Periodo')
    axes[0, 0].set_ylabel('Monto ($)')
    axes[0, 0].set_title('Ingresos vs Gastos')
    axes[0, 0].set_xticks(x_pos)
    axes[0, 0].set_xticklabels(periodos, rotation=45, ha='right')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3, linestyle='--')
    
    # Gráfico 2: Resultado
    colors = ['#27ae60' if r >= 0 else '#e74c3c' for r in resultados]
    bars = axes[0, 1].bar(periodos, resultados, color=colors, alpha=0.7, width=0.6)
    axes[0, 1].axhline(y=0, color='black', linewidth=1, alpha=0.5)
    axes[0, 1].set_xlabel('Periodo')
    axes[0, 1].set_ylabel('Resultado ($)')
    axes[0, 1].set_title('Resultado por Periodo')
    axes[0, 1].set_xticklabels(periodos, rotation=45, ha='right')
    axes[0, 1].grid(True, alpha=0.3, linestyle='--')
    
    # Agregar valores en barras
    for bar, valor in zip(bars, resultados):
        height = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width()/2., 
                height + (0.02 * max(resultados) if height >= 0 else -0.05 * max(map(abs, resultados))),
                f'${valor:,.0f}', ha='center', va='bottom' if height >= 0 else 'top',
                fontsize=9, fontweight='bold')
    
    # Gráfico 3: Otros impuestos
    if total_otros_impuestos > 0:
        axes[1, 0].bar(periodos, otros_impuestos, color='#f39c12', alpha=0.7, width=0.6)
        axes[1, 0].set_xlabel('Periodo')
        axes[1, 0].set_ylabel('Monto ($)')
        axes[1, 0].set_title('Otros Impuestos por Periodo')
        axes[1, 0].set_xticklabels(periodos, rotation=45, ha='right')
        axes[1, 0].grid(True, alpha=0.3, linestyle='--')
    else:
        axes[1, 0].text(0.5, 0.5, 'No hay otros impuestos', 
                       ha='center', va='center', fontsize=12)
        axes[1, 0].set_title('Otros Impuestos')
        axes[1, 0].axis('off')
    
    # Gráfico 4: Evolución del margen
    margenes = df_resumen['Margen %'].str.replace('%', '').astype(float)
    axes[1, 1].plot(periodos, margenes, marker='o', linewidth=2, color='#3498db')
    axes[1, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[1, 1].fill_between(periodos, margenes, 0, where=(margenes >= 0), 
                           color='#27ae60', alpha=0.3)
    axes[1, 1].fill_between(periodos, margenes, 0, where=(margenes < 0), 
                           color='#e74c3c', alpha=0.3)
    axes[1, 1].set_xlabel('Periodo')
    axes[1, 1].set_ylabel('Margen (%)')
    axes[1, 1].set_title('Evolución del Margen')
    axes[1, 1].set_xticklabels(periodos, rotation=45, ha='right')
    axes[1, 1].grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    st.pyplot(fig)

# Estadísticas avanzadas
with st.expander("📈 Estadísticas Avanzadas"):
    # Separar ventas y compras
    ventas = [d for d in documentos if d['tipo'] == 'ingreso']
    compras = [d for d in documentos if d['tipo'] == 'gasto']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ventas", len(ventas))
        if ventas:
            total_ventas_neto = sum(v['neto'] for v in ventas)
            total_ventas_total = sum(v['total'] for v in ventas)
            st.write(f"Neto: ${total_ventas_neto:,.0f}")
            st.write(f"Total: ${total_ventas_total:,.0f}")
    
    with col2:
        st.metric("Total Compras", len(compras))
        if compras:
            total_compras_neto = sum(c['neto'] for c in compras)
            total_compras_total = sum(c['total'] for c in compras)
            st.write(f"Neto: ${total_compras_neto:,.0f}")
            st.write(f"Total: ${total_compras_total:,.0f}")
    
    with col3:
        if ventas:
            iva_ventas = sum(v.get('iva', 0) for v in ventas)
            otros_ventas = sum(v.get('otros_impuestos', 0) for v in ventas)
            st.metric("Impuestos Ventas", f"${(iva_ventas + otros_ventas):,.0f}")
            st.write(f"IVA: ${iva_ventas:,.0f}")
            st.write(f"Otros: ${otros_ventas:,.0f}")
    
    with col4:
        if compras:
            iva_compras = sum(c.get('iva', 0) for c in compras)
            iva_rec_compras = sum(c.get('iva_recuperable', 0) for c in compras)
            otros_compras = sum(c.get('otros_impuestos', 0) for c in compras)
            st.metric("Impuestos Compras", f"${(iva_compras + otros_compras):,.0f}")
            st.write(f"IVA: ${iva_compras:,.0f}")
            st.write(f"IVA Recuperable: ${iva_rec_compras:,.0f}")
            st.write(f"Otros: ${otros_compras:,.0f}")

# Exportar resultados
st.subheader("💾 Exportar Resultados")

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Descargar Excel Completo", use_container_width=True):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Hoja 1: Resumen
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja 2: Documentos detallados
            df_docs = pd.DataFrame([
                {
                    'Fecha': d['fecha'],
                    'Tipo': d['tipo'],
                    'Neto': d['neto'],
                    'Total': d['total'],
                    'IVA': d.get('iva', 0),
                    'IVA Recuperable': d.get('iva_recuperable', 0) if d['tipo'] == 'gasto' else 0,
                    'Otros Impuestos': d.get('otros_impuestos', 0),
                    'Costo Real': d.get('costo_real', d['total']) if d['tipo'] == 'gasto' else d['neto'],
                    'Tipo Doc': d.get('tipo_doc', 0)
                }
                for d in documentos if d['fecha_dt']
            ])
            df_docs.to_excel(writer, sheet_name='Documentos', index=False)
            
            # Hoja 3: Estadísticas
            stats_data = {
                'Métrica': ['Total Ventas', 'Total Compras', 'Ingresos Totales', 
                          'Gastos Totales', 'Resultado Final', 'Margen %',
                          'Otros Impuestos Totales'],
                'Valor': [len(ventas), len(compras), total_ingresos, 
                         total_gastos, total_resultado, margen,
                         total_otros_impuestos]
            }
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='Estadísticas', index=False)
        
        st.download_button(
            label="⬇️ Hacer click para descargar",
            data=output.getvalue(),
            file_name=f"resultados_completos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with col2:
    if st.button("🔄 Reiniciar Aplicación", type="secondary", use_container_width=True):
        st.rerun()

# Pie de página
st.markdown("---")
st.caption(f"© {datetime.now().year} - Simulador de Resultados | Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
