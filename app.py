# app.py - VERSIÓN SIN VISUALIZACIÓN AUTOMÁTICA DE ARCHIVOS
import streamlit as st
from datetime import datetime
import pandas as pd
from collections import defaultdict

# Importar desde core
from core import ProcesadorArchivos, CalculadoraResultados, formatear_monto

# ==========================================
# CONFIGURACIÓN - CON CSS PARA OCULTAR
# ==========================================

st.set_page_config(page_title="Simulador de Resultados", layout="wide")

# CSS para ocultar la visualización automática de archivos
st.markdown("""
<style>
    /* Ocultar la lista de archivos que Streamlit muestra automáticamente */
    div[data-testid="stFileUploader"] div[style*="flex-direction: column;"] > div:first-child {
        display: none !important;
    }
    
    /* Ocultar también el texto de los archivos seleccionados */
    .st-emotion-cache-1gulkj5 {
        display: none !important;
    }
    
    /* Mejorar el diseño general */
    .st-emotion-cache-16idsys p {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Simulador de Resultados")

# ==========================================
# ESTADO DE LA APLICACIÓN
# ==========================================

if 'archivos_procesados' not in st.session_state:
    st.session_state.archivos_procesados = {}
if 'periodos_asignados' not in st.session_state:
    st.session_state.periodos_asignados = {}

# ==========================================
# COMPONENTES DE INTERFAZ MEJORADOS
# ==========================================

def crear_uploader_multiple(tipo):
    """Crea uploader para múltiples archivos OCULTANDO la visualización automática."""
    st.markdown(f"### 📋 Archivos de {tipo}")
    
    # Mensaje personalizado más claro
    st.markdown(f"**Selecciona tus archivos de {tipo.lower()}:**")
    
    archivos = st.file_uploader(
        "",  # Texto vacío para que no se duplique
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        key=f"{tipo.lower()}_uploader",
        help=f"📌 Arrastra o selecciona archivos de {tipo.lower()} (CSV, Excel)",
        label_visibility="collapsed"  # Ocultamos la label
    )
    
    if archivos:
        # Mostrar mensaje personalizado en lugar del automático
        st.success(f"✅ **{len(archivos)} archivo(s) de {tipo.lower()} listo(s) para procesar**")
    
    return archivos

def mostrar_resumen_archivo(info_archivo, tipo):
    """Muestra un resumen limpio del archivo procesado."""
    with st.container():
        st.markdown("---")
        
        # Encabezado compacto
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Nombre sin extensión
            nombre_base = info_archivo['nombre_archivo']
            if '.' in nombre_base:
                nombre_base = nombre_base[:nombre_base.rfind('.')]
            
            if len(nombre_base) > 25:
                nombre_base = nombre_base[:22] + "..."
            
            st.markdown(f"**📄 {nombre_base}**")
            
            # Información clave en línea
            st.caption(f"""
            📅 **Período de datos:** {info_archivo['fecha_minima'].strftime('%d/%m')} al {info_archivo['fecha_maxima'].strftime('%d/%m/%Y')}  
            📋 **Documentos:** {info_archivo['documentos_count']}  
            💰 **Monto total:** {formatear_monto(info_archivo['total_monto'])}
            """)
        
        with col2:
            # Icono según tipo
            if tipo.lower() == 'venta':
                st.markdown("🟢 **VENTA**")
            else:
                st.markdown("🔵 **COMPRA**")
        
        # Detección automática (si aplica)
        if info_archivo['año_predominante']:
            porcentaje = (info_archivo['cantidad_predominante'] / info_archivo['documentos_count']) * 100
            
            if porcentaje >= 70:
                st.info(f"🎯 **Período detectado:** {info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d} "
                       f"({porcentaje:.0f}% coincidencia)")
            elif porcentaje >= 50:
                st.warning(f"⚠️ **Posible período:** {info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d} "
                          f"({porcentaje:.0f}% coincidencia)")
            else:
                st.error(f"❌ **Período no claro:** {info_archivo['año_predominante']}-{info_archivo['mes_predominante']:02d} "
                        f"({porcentaje:.0f}% coincidencia)")
        else:
            st.error("❌ **No se detectó un período predominante**")
        
        return info_archivo['año_predominante'], info_archivo['mes_predominante']

def solicitar_periodo(año_pred, mes_pred, nombre_archivo, tipo):
    """Solicita confirmación del período."""
    st.markdown("**🔧 Asignar período contable:**")
    
    col_a, col_b, col_c = st.columns([2, 2, 2])
    
    with col_a:
        años_disponibles = list(range(2020, datetime.now().year + 2))
        año_default = año_pred if año_pred and año_pred in años_disponibles else datetime.now().year
        año_index = años_disponibles.index(año_default) if año_default in años_disponibles else len(años_disponibles)-1
        
        año_seleccionado = st.selectbox(
            "Año",
            años_disponibles,
            index=año_index,
            key=f"año_{nombre_archivo}",
            label_visibility="collapsed"
        )
    
    with col_b:
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_default = mes_pred - 1 if mes_pred else 0
        
        mes_seleccionado = st.selectbox(
            "Mes",
            meses,
            index=mes_default,
            key=f"mes_{nombre_archivo}",
            label_visibility="collapsed"
        )
    
    with col_c:
        mes_numero = meses.index(mes_seleccionado) + 1
        periodo_asignado = f"{año_seleccionado}-{mes_numero:02d}"
        
        # Estado de confirmación
        estado_key = f"confirmado_{nombre_archivo}"
        if estado_key not in st.session_state:
            st.session_state[estado_key] = False
        
        if st.session_state[estado_key]:
            st.success(f"✅ **{periodo_asignado}**")
            st.caption("Período confirmado")
            return año_seleccionado, mes_numero, True
        else:
            if st.button("📌 **Asignar Período**", 
                       key=f"btn_confirm_{nombre_archivo}",
                       type="primary",
                       use_container_width=True):
                st.session_state[estado_key] = True
                st.rerun()
            
            # Mostrar preview sin confirmar
            st.caption(f"🔄 Previsto: **{periodo_asignado}**")
            return año_seleccionado, mes_numero, False

# ==========================================
# PESTAÑA 1: CARGA DE ARCHIVOS (SIN VISUALIZACIÓN AUTOMÁTICA)
# ==========================================

def pestana_carga():
    """Pestaña para cargar archivos SIN la lista automática de archivos."""
    st.header("📥 Carga de Archivos")
    
    # Resumen rápido si ya hay archivos
    if st.session_state.archivos_procesados:
        total_archivos = len(st.session_state.archivos_procesados)
        ventas_count = sum(1 for v in st.session_state.archivos_procesados.values() 
                          if v['tipo_archivo'] == 'venta')
        compras_count = total_archivos - ventas_count
        
        st.success(f"📊 **{total_archivos} archivo(s) cargado(s):** {ventas_count} ventas, {compras_count} compras")
    
    st.markdown("---")
    
    # Contadores
    nuevos_confirmados = 0
    pendientes = 0
    
    # ===== SECCIÓN VENTAS =====
    st.markdown("### 📤 Archivos de Ventas")
    archivos_ventas = crear_uploader_multiple("Ventas")
    
    if archivos_ventas:
        for archivo in archivos_ventas:
            # Saltar si ya está procesado
            if archivo.name in st.session_state.archivos_procesados:
                continue
            
            try:
                # Procesar con spinner
                with st.spinner(f"Analizando {archivo.name[:20]}..."):
                    info_archivo = ProcesadorArchivos.procesar_archivo(archivo, "venta")
                
                # Mostrar resumen (NO el nombre crudo)
                año_pred, mes_pred = mostrar_resumen_archivo(info_archivo, "venta")
                
                # Solicitar período
                año_confirmado, mes_confirmado, confirmado = solicitar_periodo(
                    año_pred, mes_pred, archivo.name, "venta"
                )
                
                if confirmado:
                    st.session_state.archivos_procesados[archivo.name] = info_archivo
                    st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                    nuevos_confirmados += 1
                    
                    # Mensaje de éxito
                    nombre_simple = archivo.name
                    if '.' in nombre_simple:
                        nombre_simple = nombre_simple[:nombre_simple.rfind('.')]
                    
                    if len(nombre_simple) > 25:
                        nombre_simple = nombre_simple[:22] + "..."
                    
                    st.success(f"✅ **{nombre_simple}** → Período **{año_confirmado}-{mes_confirmado:02d}**")
                else:
                    pendientes += 1
                
                st.markdown("---")
                
            except Exception as e:
                st.error(f"❌ **Error procesando archivo:** {str(e)[:80]}")
                st.markdown("---")
    
    # ===== SECCIÓN COMPRAS =====
    st.markdown("### 📥 Archivos de Compras")
    archivos_compras = crear_uploader_multiple("Compras")
    
    if archivos_compras:
        for archivo in archivos_compras:
            if archivo.name in st.session_state.archivos_procesados:
                continue
            
            try:
                with st.spinner(f"Analizando {archivo.name[:20]}..."):
                    info_archivo = ProcesadorArchivos.procesar_archivo(archivo, "compra")
                
                año_pred, mes_pred = mostrar_resumen_archivo(info_archivo, "compra")
                
                año_confirmado, mes_confirmado, confirmado = solicitar_periodo(
                    año_pred, mes_pred, archivo.name, "compra"
                )
                
                if confirmado:
                    st.session_state.archivos_procesados[archivo.name] = info_archivo
                    st.session_state.periodos_asignados[archivo.name] = f"{año_confirmado}-{mes_confirmado:02d}"
                    nuevos_confirmados += 1
                    
                    nombre_simple = archivo.name
                    if '.' in nombre_simple:
                        nombre_simple = nombre_simple[:nombre_simple.rfind('.')]
                    
                    if len(nombre_simple) > 25:
                        nombre_simple = nombre_simple[:22] + "..."
                    
                    st.success(f"✅ **{nombre_simple}** → Período **{año_confirmado}-{mes_confirmado:02d}**")
                else:
                    pendientes += 1
                
                st.markdown("---")
                
            except Exception as e:
                st.error(f"❌ **Error procesando archivo:** {str(e)[:80]}")
                st.markdown("---")
    
    # ===== RESUMEN FINAL =====
    if nuevos_confirmados > 0:
        st.balloons()
        st.success(f"""
        🎉 **¡{nuevos_confirmados} nuevo(s) archivo(s) asignado(s) correctamente!**
        
        **Total de archivos procesados:** {len(st.session_state.archivos_procesados)}
        **Siguiente paso:** Ve a la pestaña **'📈 Análisis'** para ver los resultados.
        """)
    
    if pendientes > 0:
        st.warning(f"""
        ⚠️ **{pendientes} archivo(s) pendiente(s) de asignación**
        
        **Para completar:** Asigna el período contable y haz clic en **'Asignar Período'**.
        """)

# ==========================================
# PESTAÑA 2: ANÁLISIS (MANTENIENDO LO ANTERIOR)
# ==========================================

def pestana_analisis():
    """Pestaña para ver análisis y resultados."""
    st.header("📈 Análisis de Resultados")
    
    if not st.session_state.archivos_procesados:
        st.info("""
        ⚠️ **No hay archivos cargados.**
        
        **Pasos a seguir:**
        1. Ve a la pestaña **'📥 Carga de Archivos'**
        2. Sube tus archivos de ventas y compras
        3. Asigna períodos a cada archivo
        4. Regresa aquí para ver los resultados
        """)
        return
    
    # Recolectar documentos
    todos_documentos = []
    for info in st.session_state.archivos_procesados.values():
        for doc in info['documentos']:
            periodo = st.session_state.periodos_asignados.get(doc['archivo_origen'], "Sin_periodo")
            doc['periodo_asignado'] = periodo
            todos_documentos.append(doc)
    
    # Calcular
    resumen_periodos = CalculadoraResultados.agrupar_por_periodo(
        todos_documentos, 
        st.session_state.periodos_asignados
    )
    totales = CalculadoraResultados.calcular_totales(resumen_periodos)
    datos_tabla = CalculadoraResultados.generar_dataframe_resultados(resumen_periodos)
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ventas Totales", formatear_monto(totales['ventas_totales']))
    with col2:
        st.metric("Compras Totales", formatear_monto(totales['compras_totales']))
    with col3:
        st.metric("Resultado Neto", formatear_monto(totales['resultado_total']))
    with col4:
        st.metric("Documentos", totales['documentos_totales'])
    
    # Tabla de resultados
    if datos_tabla:
        df_resultados = pd.DataFrame(datos_tabla)
        st.dataframe(df_resultados, use_container_width=True)

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN
# ==========================================

def pestana_configuracion():
    """Pestaña para configuración."""
    st.header("⚙️ Configuración")
    
    if st.button("🔄 **NUEVO ANÁLISIS (Borrar Todo)**", 
                 type="secondary", 
                 use_container_width=True):
        # Limpiar TODO
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.session_state.archivos_procesados = {}
        st.session_state.periodos_asignados = {}
        
        st.success("✅ ¡Sistema reiniciado!")
        st.rerun()

# ==========================================
# FLUJO PRINCIPAL
# ==========================================

tab1, tab2, tab3 = st.tabs(["📥 Carga", "📈 Análisis", "⚙️ Configuración"])

with tab1:
    pestana_carga()

with tab2:
    pestana_analisis()

with tab3:
    pestana_configuracion()

st.caption(f"Simulador de Resultados | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
