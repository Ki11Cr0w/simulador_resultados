# core/utils.py
import pandas as pd
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
