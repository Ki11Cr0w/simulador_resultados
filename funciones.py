# funciones.py
import pandas as pd
from collections import defaultdict
from datetime import datetime

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

def procesar_archivo(archivo, tipo_archivo):
    """Procesa un archivo y extrae la información."""
    try:
        # Leer archivo según extensión
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo, sep=';', decimal=',')
        else:
            df = pd.read_excel(archivo)
        
        df = normalizar_columnas(df)
        
        # Verificar columnas requeridas
        columnas_requeridas = ['fecha_docto', 'tipo_documento', 'monto_total']
        columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
        
        if columnas_faltantes:
            raise ValueError(f"Faltan columnas: {columnas_faltantes}")
        
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
                    'tipo': tipo_archivo,
                    'tipo_doc': tipo_doc,
                    'archivo_origen': archivo.name
                })
                fechas_validas.append(fecha_dt)
        
        if not documentos:
            raise ValueError("No se encontraron documentos con fecha válida")
        
        # Detectar año-mes predominante
        año_pred, mes_pred, cantidad = detectar_año_mes_predominante(fechas_validas)
        
        # Calcular estadísticas
        fecha_min = min(fechas_validas)
        fecha_max = max(fechas_validas)
        total_monto = sum(d['monto'] for d in documentos)
        
        return {
            'documentos': documentos,
            'fechas_validas': fechas_validas,
            'año_predominante': año_pred,
            'mes_predominante': mes_pred,
            'cantidad_predominante': cantidad,
            'fecha_minima': fecha_min,
            'fecha_maxima': fecha_max,
            'total_monto': total_monto,
            'nombre_archivo': archivo.name,
            'tipo_archivo': tipo_archivo,
            'documentos_count': len(documentos)
        }
        
    except Exception as e:
        raise Exception(f"Error procesando archivo {archivo.name}: {str(e)}")

def agrupar_por_periodo(documentos, periodos_asignados):
    """Agrupa documentos por período asignado."""
    resumen = defaultdict(lambda: {
        'ventas': 0,
        'compras': 0,
        'documentos_ventas': 0,
        'documentos_compras': 0
    })
    
    for doc in documentos:
        # Obtener período asignado para este documento
        archivo_key = doc['archivo_origen']
        periodo = periodos_asignados.get(archivo_key, "Sin_periodo")
        
        if doc['tipo'] == 'venta':
            resumen[periodo]['ventas'] += doc['monto']
            resumen[periodo]['documentos_ventas'] += 1
        else:
            resumen[periodo]['compras'] += doc['monto']
            resumen[periodo]['documentos_compras'] += 1
    
    return dict(resumen)

def calcular_totales(resumen_periodos):
    """Calcula totales a partir del resumen por períodos."""
    total_ventas = sum(p['ventas'] for p in resumen_periodos.values())
    total_compras = sum(p['compras'] for p in resumen_periodos.values())
    total_resultado = total_ventas - total_compras
    
    total_docs_ventas = sum(p['documentos_ventas'] for p in resumen_periodos.values())
    total_docs_compras = sum(p['documentos_compras'] for p in resumen_periodos.values())
    total_documentos = total_docs_ventas + total_docs_compras
    
    return {
        'ventas_totales': total_ventas,
        'compras_totales': total_compras,
        'resultado_total': total_resultado,
        'documentos_ventas': total_docs_ventas,
        'documentos_compras': total_docs_compras,
        'documentos_totales': total_documentos
    }

def generar_dataframe_resultados(resumen_periodos):
    """Genera lista de diccionarios con resultados por período."""
    periodos_ordenados = sorted(resumen_periodos.keys())
    
    datos = []
    for periodo in periodos_ordenados:
        datos_periodo = resumen_periodos[periodo]
        resultado = datos_periodo['ventas'] - datos_periodo['compras']
        margen = (resultado / datos_periodo['ventas'] * 100) if datos_periodo['ventas'] != 0 else 0
        
        datos.append({
            'Período': periodo,
            'Ventas': datos_periodo['ventas'],
            'Compras': datos_periodo['compras'],
            'Resultado': resultado,
            'Docs V': datos_periodo['documentos_ventas'],
            'Docs C': datos_periodo['documentos_compras'],
            'Margen %': margen
        })
    
    return datos

def calcular_estadisticas(documentos):
    """Calcula estadísticas adicionales."""
    # Documentos tipo 61
    docs_61_ventas = len([d for d in documentos if d['tipo'] == 'venta' and d['tipo_doc'] == 61])
    docs_61_compras = len([d for d in documentos if d['tipo'] == 'compra' and d['tipo_doc'] == 61])
    
    # Promedios
    ventas = [d for d in documentos if d['tipo'] == 'venta']
    compras = [d for d in documentos if d['tipo'] == 'compra']
    
    promedio_venta = sum(d['monto'] for d in ventas) / len(ventas) if ventas else 0
    promedio_compra = sum(d['monto'] for d in compras) / len(compras) if compras else 0
    
    return {
        'notas_credito_ventas': docs_61_ventas,
        'notas_credito_compras': docs_61_compras,
        'promedio_venta': promedio_venta,
        'promedio_compra': promedio_compra,
        'total_ventas_count': len(ventas),
        'total_compras_count': len(compras)
    }
