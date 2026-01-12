# ==========================================
# APP WEB - SIMULADOR DE RESULTADO
# ==========================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

from validaciones import validar_ventas_sii

# ==========================================
# VALIDACION DE FORMATO INTERNO
# ==========================================
def normalizar_ventas(df_ventas):
    documentos = []

    for _, fila in df_ventas.iterrows():
        tipo_doc = int(fila["Tipo Documento"]) if not pd.isna(fila["Tipo Documento"]) else 0
        factor = -1 if tipo_doc == 61 else 1

        neto = fila["Monto Neto"] if not pd.isna(fila["Monto Neto"]) else 0
        total = fila["Monto Total"] if not pd.isna(fila["Monto Total"]) else 0

        documentos.append({
            "fecha": fila["Fecha Emisión"],
            "tipo": "ingreso",
            "neto": neto * factor,
            "total": total * factor
        })

    return documentos

# ==========================================
# DATOS DE CARGA POR EL SII
# ==========================================

archivo = st.file_uploader("Cargar Ventas SII", type="csv")

documentos = []

if archivo:
    df_ventas = pd.read_csv(archivo)

    validacion = validar_ventas_sii(df_ventas)
    df_validos = df_ventas[validacion["valido"] == True]

    documentos = normalizar_ventas(df_validos)

    st.success(f"Ventas cargadas correctamente: {len(documentos)} documentos válidos")
# ==========================================
# Boton de Validacion
# ==========================================
#if st.button("Ver resultado"):
#    if not documentos:
#        st.warning("Primero debes cargar el archivo de Ventas SII")
#        st.stop()

# ==========================================
# MOTOR DE CÁLCULO
# ==========================================

def calcular_resultados(documentos, tipo_periodo="mensual"):
    resumen = defaultdict(lambda: {
        "ingresos_neto": 0,
        "ingresos_total": 0,
        "gastos_neto": 0,
        "gastos_total": 0,
        "honorarios_neto": 0,
        "honorarios_total": 0,
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

        if d["tipo"] == "ingreso":
            resumen[periodo]["ingresos_neto"] += d["neto"]
            resumen[periodo]["ingresos_total"] += d["total"]

        elif d["tipo"] == "gasto":
            resumen[periodo]["gastos_neto"] += d["neto"]
            resumen[periodo]["gastos_total"] += d["total"]

        elif d["tipo"] == "honorario":
            resumen[periodo]["honorarios_neto"] += d["neto"]
            resumen[periodo]["honorarios_total"] += d["total"]

    return dict(resumen)

# ==========================================
# APP WEB
# ==========================================

st.set_page_config(page_title="Simulador de Resultado", layout="centered")

st.title("📊 Simulador de Resultado")
st.write("Una visión simple para entender cómo va tu negocio")

tipo_analisis_ui = st.radio(
    "¿Cómo quieres ver los números?",
    [
        "Resultado del negocio (sin impuestos)",
        "Movimiento de dinero (con impuestos)"
    ]
)

periodo_ui = st.selectbox(
    "Periodo de análisis",
    ["Mensual", "Trimestral", "Anual"]
)

if st.button("Ver resultado"):
    tipo_analisis = "negocio" if "negocio" in tipo_analisis_ui else "caja"
    periodo_map = {
        "Mensual": "mensual",
        "Trimestral": "trimestral",
        "Anual": "anual"
    }

    resumen = calcular_resultados(documentos, periodo_map[periodo_ui])
    periodos = sorted(resumen.keys())

    resultados = []
    total_ingresos = 0
    total_gastos = 0

    for p in periodos:
        d = resumen[p]

        if tipo_analisis == "negocio":
            ingresos = d["ingresos_neto"]
            gastos = d["gastos_neto"] + d["honorarios_neto"]
        else:
            ingresos = d["ingresos_total"]
            gastos = d["gastos_total"] + d["honorarios_total"]

        total_ingresos += ingresos
        total_gastos += gastos
        resultados.append(ingresos - gastos)

    resultado_final = total_ingresos - total_gastos

    st.subheader("📌 Resumen general")
    col1, col2, col3 = st.columns(3)
    col1.metric("Entradas", f"${total_ingresos:,.0f}")
    col2.metric("Salidas", f"${total_gastos:,.0f}")
    col3.metric("Resultado", f"${resultado_final:,.0f}")

    # Gráfico de torta
    fig1, ax1 = plt.subplots()
    ax1.pie(
        [total_ingresos, total_gastos],
        labels=["Ingresos", "Gastos"],
        autopct="%1.0f%%",
        startangle=90
    )
    ax1.set_title("Equilibrio del negocio")
    st.pyplot(fig1)

    # Gráfico de barras
    fig2, ax2 = plt.subplots()
    ax2.bar(periodos, resultados)
    ax2.set_title("Resultado por periodo")
    ax2.set_ylabel("Resultado")
    ax2.tick_params(axis="x", rotation=45)

    for i, valor in enumerate(resultados):
        ax2.text(i, valor, f"${valor:,.0f}", ha="center", va="bottom")

    st.pyplot(fig2)
