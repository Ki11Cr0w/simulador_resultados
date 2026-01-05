# ==========================================
# APP WEB - SIMULADOR DE RESULTADO
# ==========================================

import streamlit as st
import matplotlib.pyplot as plt
from collections import defaultdict

# ==========================================
# DATOS FICTICIOS (SIMULAN SII)
# ==========================================

documentos = [
    # ENERO
    {"fecha": "2025-01-05", "tipo": "ingreso", "neto": 100000, "total": 119000},
    {"fecha": "2025-01-15", "tipo": "gasto", "neto": 30000, "total": 35700},
    {"fecha": "2025-01-20", "tipo": "honorario", "neto": 20000, "total": 20000},

    # FEBRERO
    {"fecha": "2025-02-04", "tipo": "ingreso", "neto": 120000, "total": 142800},
    {"fecha": "2025-02-10", "tipo": "gasto", "neto": 35000, "total": 41650},
    {"fecha": "2025-02-18", "tipo": "honorario", "neto": 25000, "total": 25000},

    # MARZO
    {"fecha": "2025-03-03", "tipo": "ingreso", "neto": 110000, "total": 130900},
    {"fecha": "2025-03-22", "tipo": "gasto", "neto": 40000, "total": 47600},

    # ABRIL
    {"fecha": "2025-04-05", "tipo": "ingreso", "neto": 130000, "total": 154700},
    {"fecha": "2025-04-18", "tipo": "gasto", "neto": 45000, "total": 53550},

    # MAYO
    {"fecha": "2025-05-06", "tipo": "ingreso", "neto": 125000, "total": 148750},
    {"fecha": "2025-05-15", "tipo": "honorario", "neto": 22000, "total": 22000},

    # JUNIO
    {"fecha": "2025-06-02", "tipo": "ingreso", "neto": 140000, "total": 166600},
    {"fecha": "2025-06-20", "tipo": "gasto", "neto": 50000, "total": 59500},

    # JULIO
    {"fecha": "2025-07-07", "tipo": "ingreso", "neto": 135000, "total": 160650},
    {"fecha": "2025-07-18", "tipo": "gasto", "neto": 42000, "total": 49980},

    # AGOSTO
    {"fecha": "2025-08-03", "tipo": "ingreso", "neto": 145000, "total": 172550},
    {"fecha": "2025-08-22", "tipo": "honorario", "neto": 24000, "total": 24000},

    # SEPTIEMBRE
    {"fecha": "2025-09-01", "tipo": "ingreso", "neto": 138000, "total": 164220},
    {"fecha": "2025-09-19", "tipo": "gasto", "neto": 47000, "total": 55930},

    # OCTUBRE
    {"fecha": "2025-10-05", "tipo": "ingreso", "neto": 150000, "total": 178500},
    {"fecha": "2025-10-21", "tipo": "gasto", "neto": 52000, "total": 61880},

    # NOVIEMBRE
    {"fecha": "2025-11-04", "tipo": "ingreso", "neto": 155000, "total": 184450},
    {"fecha": "2025-11-18", "tipo": "honorario", "neto": 26000, "total": 26000},

    # DICIEMBRE
    {"fecha": "2025-12-02", "tipo": "ingreso", "neto": 160000, "total": 190400},
    {"fecha": "2025-12-20", "tipo": "gasto", "neto": 60000, "total": 71400},
]

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
