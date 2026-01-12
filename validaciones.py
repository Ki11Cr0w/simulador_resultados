# ==========================================
# Importaciones
# ==========================================

import pandas as pd

# ==========================================
# Función de Validación
# ==========================================

def validar_ventas_sii(df, tolerancia=1):

    resultados = []

    for index, fila in df.iterrows():
        tipo_doc = int(fila["Tipo Documento"]) if not pd.isna(fila["Tipo Documento"]) else 0
        factor = -1 if tipo_doc == 61 else 1

        neto = fila.get("Monto Neto", 0) or 0
        exento = fila.get("Monto Exento", 0) or 0
        iva = fila.get("Monto IVA", 0) or 0
        total_informado = fila.get("Monto Total", 0) or 0

        otros_impuestos = 0
        for col in df.columns:
            if col.startswith("IVA") and col != "Monto IVA":
                otros_impuestos += fila[col] or 0

        if "Valor Otro Imp." in df.columns:
            otros_impuestos += fila["Valor Otro Imp."] or 0

        total_calculado = (
            neto + exento + iva + otros_impuestos
        ) * factor

        total_informado = total_informado * factor
        diferencia = round(total_calculado - total_informado, 0)

        valido = abs(diferencia) <= tolerancia

        resultados.append({
            "fila": index,
            "valido": valido,
            "diferencia": diferencia
        })

    df_resultado = df.copy()
    df_resultado["valido"] = [r["valido"] for r in resultados]
    df_resultado["diferencia"] = [r["diferencia"] for r in resultados]

    return df_resultado

