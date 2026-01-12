# ==========================================
# VALIDACIONES.PY - VERSIÓN COMPLETA
# ==========================================

import pandas as pd
import numpy as np


def _clean_numeric_column(serie):
    """Limpia y convierte columnas numéricas."""
    if serie.dtype == 'object':
        serie = serie.astype(str).str.replace(r'\.', '', regex=True)
        serie = serie.str.replace(',', '.', regex=False)
    return pd.to_numeric(serie, errors='coerce').fillna(0)


def _calcular_total_fila(fila, tipo_doc, es_compra=False):
    """Calcula el total de una fila según tipo de documento."""
    factor = -1 if tipo_doc == 61 else 1
    
    # Obtener montos base
    neto = fila.get('monto_neto', 0)
    exento = fila.get('monto_exento', 0)
    iva = fila.get('monto_iva', 0)
    
    # Para compras: buscar IVA recuperable y otros impuestos
    otros_impuestos = 0
    
    # Buscar columnas de otros impuestos
    for col in fila.index:
        if 'valor_otro_imp' in col.lower():
            otros_impuestos += fila[col]
    
    # Para compras, agregar IVA recuperable al IVA total
    if es_compra:
        iva_recuperable = fila.get('monto_iva_recuperable', 0)
        iva += iva_recuperable
    
    # Sumar otros impuestos de tipo IVA (excepto monto_iva principal)
    for col in fila.index:
        if col.startswith('iva') and col != 'monto_iva' and not col.startswith('monto_iva_recuperable'):
            otros_impuestos += fila[col]
    
    total_calculado = (neto + exento + iva + otros_impuestos) * factor
    total_informado = fila.get('monto_total', 0) * factor
    
    return total_calculado, total_informado, otros_impuestos


def validar_documentos(df, tolerancia=1, es_compra=False):
    """Valida coherencia entre montos en documentos."""
    df = df.copy()
    
    # Limpiar columnas numéricas
    numeric_cols = [col for col in df.columns 
                   if col.startswith(('monto', 'iva', 'valor_otro_imp'))]
    
    for col in numeric_cols:
        df[col] = _clean_numeric_column(df[col])
    
    # Calcular diferencias
    calculados = []
    informados = []
    otros_impuestos_list = []
    
    for _, fila in df.iterrows():
        tipo_doc = int(fila.get('tipo_documento', 0) or 0)
        calc, info, otros = _calcular_total_fila(fila, tipo_doc, es_compra)
        calculados.append(calc)
        informados.append(info)
        otros_impuestos_list.append(otros)
    
    # Agregar resultados
    df['total_calculado'] = calculados
    df['total_informado'] = informados
    df['otros_impuestos'] = otros_impuestos_list
    df['diferencia'] = np.round(df['total_calculado'] - df['total_informado'], 2)
    df['valido'] = df['diferencia'].abs() <= tolerancia
    
    return df


def validar_ventas_sii(df, tolerancia=1):
    """Valida documentos de ventas."""
    return validar_documentos(df, tolerancia, es_compra=False)


def validar_compras_sii(df, tolerancia=1):
    """Valida documentos de compras."""
    return validar_documentos(df, tolerancia, es_compra=True)
