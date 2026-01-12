# ==========================================
# APP WEB - SIMULADOR DE RESULTADO
# ==========================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

from validaciones import validar_ventas_sii

# ==========================================
# CONFIG APP
# ==========================================
st.set_page_config(page_title="Simulador de Resultado", layout="centered")
st.title("Simulador de Resultado")

# ==========================================
# CARGA ARCHIVO
# ==========================================
archivo = st.file_uploader("Cargar Ventas SII", type="csv")
documentos = []

# ==========================================
# NORMALIZACIÓN
# ==========================================
def normalizar_columnas(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df


def normalizar_ventas(df):
    documentos = []

    for _, fila in df.iterrows():
        tipo_doc = int(fila.get("tipo_documento", 0) or 0)
        factor = -1 if tipo_doc == 61 else 1

        documentos.append({
            "fecha": fila.get("fecha_emision", ""),
            "tipo": "ingreso",
            "neto": (fila.get("monto_neto", 0) or 0) * factor,
            "total": (fila.get("monto_total", 0) or 0) * factor,
        })

    return documentos


# ==========================================
# PROCESAMIENTO
# ==========================================
if archivo:
    df_ventas = pd.read_csv(archivo)
    df_ventas = normalizar_columnas(df_ventas)

    df_validado = validar_ventas_sii(df_ventas)
    df_validos = df_validado[df_validado["valido"] == True]

    documentos = normalizar_ventas(df_validos)

    st.success(f"Documentos válidos: {len(documentos)}")

# ==========================================
# MOTOR CÁLCULO
# ==========================================
def calcular_resultados(documentos, tipo_periodo="mensual"):
    resumen = defaultdict(lambda: {
        "ingresos_neto": 0,
        "ingresos_total": 0,
    })

    for d in documentos:
        if tipo_periodo == "mensual":
            periodo = d["fecha"][:7]
        elif tipo_periodo == "trimestral":
            mes = int(d["fecha"][5:7])
            trimestre = (mes - 1) // 3 + 1
            periodo = f"{d['fecha'][:4]}-T{trimestre}"
        else:
            periodo = d["fecha"][:4]

        resumen[periodo]["ingresos_neto"] += d["neto"]
        resumen[periodo]["ingresos_total"] += d["total"]

    return dict(resumen)

# ==========================================
# UI
# ==========================================
periodo_ui = st.selectbox("Periodo", ["Mensual", "Trimestral", "Anual"])

if st.button("Ver resultado") and documentos:
    periodo_map = {
        "Mensual": "mensual",
        "Trimestral": "trimestral",
        "Anual": "anual"
    }

    resumen = calcular_resultados(documentos, periodo_map[periodo_ui])

    total_neto = sum(v["ingresos_neto"] for v in resumen.values())
    total_total = sum(v["ingresos_total"] for v in resumen.values())

    st.metric("Resultado Neto", f"${total_neto:,.0f}")
    st.metric("Movimiento Total", f"${total_total:,.0f}")

    fig, ax = plt.subplots()
    ax.bar(resumen.keys(), [v["ingresos_neto"] for v in resumen.values()])
    ax.set_title("Resultado por periodo")
    st.pyplot(fig)
