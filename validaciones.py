# ==========================================
# Importaciones
# ==========================================

import pandas as pd

# ==========================================
# Función de Validación
# ==========================================

def validar_ventas_sii(path_csv, tolerancia=1):
    df = pd.read_csv(path_csv)

    resultados = []

    for index, fila in df.iterrows():
        tipo_doc = int(fila["Tipo Documento"])
        factor = -1 if tipo_doc == 61 else 1

        # Montos base (reemplaza NaN por 0)
        neto = fila.get("Monto Neto", 0) or 0
        exento = fila.get("Monto Exento", 0) or 0
        iva = fila.get("Monto IVA", 0) or 0
        total_informado = fila.get("Monto Total", 0) or 0

        # Otros impuestos (IVA adicionales, ILA, etc.)
        otros_impuestos = 0
        for col in df.columns:
            if col.startswith("IVA") and col not in ["Monto IVA"]:
                otros_impuestos += fila[col] or 0

        if "Valor Otro Imp." in df.columns:
            otros_impuestos += fila["Valor Otro Imp."] or 0

        # Total calculado
        total_calculado = (
            neto
            + exento
            + iva
            + otros_impuestos
        ) * factor

        total_informado = total_informado * factor

        diferencia = round(total_calculado - total_informado, 0)

        valido = abs(diferencia) <= tolerancia

        resultados.append({
            "fila": index + 1,
            "tipo_documento": tipo_doc,
            "total_calculado": total_calculado,
            "total_informado": total_informado,
            "diferencia": diferencia,
            "valido": valido
        })

    return pd.DataFrame(resultados)
