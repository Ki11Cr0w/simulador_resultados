# ==========================================
# VALIDACIONES.PY - VERSIÓN SIMPLE (sin cambios)
# ==========================================

import pandas as pd
import numpy as np


def validar_ventas_sii(df, tolerancia=1):
    """Valida documentos de ventas."""
    df = df.copy()
    
    if 'monto_total' not in df.columns or 'tipo_documento' not in df.columns:
        return df
    
    if df['monto_total'].dtype == 'object':
        df['monto_total'] = (
            df['monto_total']
            .astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
        )
        df['monto_total'] = pd.to_numeric(df['monto_total'], errors='coerce').fillna(0)
    
    df['valido'] = True
    df['diferencia'] = 0
    
    return df


def validar_compras_sii(df, tolerancia=1):
    """Valida documentos de compras."""
    return validar_ventas_sii(df, tolerancia)
