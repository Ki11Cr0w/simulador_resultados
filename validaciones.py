# ==========================================
# VALIDACIONES.PY - VERSIÓN MEJORADA
# ==========================================

import pandas as pd
import numpy as np


def _clean_numeric_column(serie):
    """Limpia y convierte columnas numéricas."""
    if serie.dtype == 'object':
        serie = serie.astype(str).str.replace(r'\.', '', regex=True)
        serie = serie.str.replace(',', '.', regex=False)
    return pd.to_numeric(serie, errors='coerce').fillna(0)


def _calcular_total_fila(fila, tipo_doc):
    """Calcula el total de una fila según tipo de documento."""
    factor = -1 if tipo_doc == 61 else 1
    
    neto = fila.get('monto_neto', 0)
    exento = fila.get('monto_exento', 0)
    iva = fila.get('monto_iva', 0)
    
    otros_impuestos = sum(fila[col] for col in fila.index 
                         if col.startswith('iva') and col != 'monto_iva')
    
    if 'valor_otro_imp' in fila.index:
        otros_impuestos += fila.get('valor_otro_imp', 0)
    
    total_calculado = (neto + exento + iva + otros_impuestos) * factor
    total_informado = fila.get('monto_total', 0) * factor
    
    return total_calculado, total_informado


def validar_documentos(df, tolerancia=1):
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
    
    for _, fila in df.iterrows():
        tipo_doc = int(fila.get('tipo_documento', 0) or 0)
        calc, info = _calcular_total_fila(fila, tipo_doc)
        calculados.append(calc)
        informados.append(info)
    
    # Agregar resultados
    df['total_calculado'] = calculados
    df['total_informado'] = informados
    df['diferencia'] = np.round(df['total_calculado'] - df['total_informado'], 2)
    df['valido'] = df['diferencia'].abs() <= tolerancia
    
    return df


def validar_ventas_sii(df, tolerancia=1):
    """Valida documentos de ventas."""
    return validar_documentos(df, tolerancia)


def validar_compras_sii(df, tolerancia=1):
    """Valida documentos de compras."""
    return validar_documentos(df, tolerancia)
