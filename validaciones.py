# ==========================================
# VALIDACIONES SII
# ==========================================

import pandas as pd


def validar_ventas_sii(df, tolerancia=1):
    """
    Recibe DataFrame ya cargado desde Streamlit
    Retorna el mismo DataFrame con columnas:
    - valido
    - diferencia
    """

    resultados_valido = []
    resultados_diferencia = []

    for _, fila in df.iterrows():
        tipo_doc = int(fila.get("tipo_documento", 0) or 0)
        factor = -1 if tipo_doc == 61 else 1

        neto = fila.get("monto_neto", 0) or 0
        exento = fila.get("monto_exento", 0) or 0
        iva = fila.get("monto_iva", 0) or 0
        total_informado = fila.get("monto_total", 0) or 0

        otros_impuestos = 0
        for col in df.columns:
            if col.startswith("iva") and col != "monto_iva":
                otros_impuestos += fila[col] or 0

        if "valor_otro_imp." in df.columns:
            otros_impuestos += fila.get("valor_otro_imp.", 0) or 0

        total_calculado = (neto + exento + iva + otros_impuestos) * factor
        total_informado = total_informado * factor

        diferencia = round(total_calculado - total_informado, 0)
        valido = abs(diferencia) <= tolerancia

        resultados_valido.append(valido)
        resultados_diferencia.append(diferencia)

    df_resultado = df.copy()
    df_resultado["valido"] = resultados_valido
    df_resultado["diferencia"] = resultados_diferencia

    return df_resultado

