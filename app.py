# ==========================================
# APP WEB - SIMULADOR DE RESULTADO
# ==========================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

from validaciones import validar_ventas_sii, validar_compras_sii

# ==========================================
# CONFIGURACIÓN APP
# ==========================================

st.set_page_config(page_title="Simulador de Resultado", layout="centered")

# ==========================================
# NORMALIZACIÓN DE COLUMNAS (SII → INTERNO)
# ==========================================

def normalizar_columnas(df):
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(".", "", regex=False)
    )
    return df

# ==========================================
# NORMALIZADORES
# ==========================================

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


def normalizar_compras(df):
    documentos = []

    for _, fila in df.iterrows():
        tipo_doc = int(fila.get("tipo_documento", 0) or 0)
        factor = -1 if tipo_doc == 61 else 1

        documentos.append({
            "fecha": fila.get("fecha_emision", ""),
            "tipo": "gasto",
            "neto": (fila.get("monto_neto", 0) or 0) * factor,
            "total": (fila.get("monto_total", 0) or 0) * factor,
        })

    return documentos

# ==========================================
# MOTOR DE CÁLCULO
# ==========================================

def calcular_resultados(documentos, tipo_periodo="mensual"):
    resumen = defaultdict(lambda: {
        "ingresos_neto": 0,
        "ingresos_total": 0,
        "gastos_neto": 0,
        "gastos_total": 0,
    })

    for d in documentos:
        if not d["fecha"]:
            continue

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

    return dict(resumen)

# ==========================================
# INTERFAZ
# ==========================================

st.title("📊 Simulador de Resultado")
st.write("Simulación simple a partir de archivos SII")

documentos = []

# -------- VENTAS --------
st.subheader("📥 Ventas SII")
archivo_ventas = st.file_uploader("Cargar Ventas", type="csv")

if archivo_ventas:
    df_ventas = pd.read_csv(archivo_ventas, sep=";", decimal=",")
    df_ventas = normalizar_columnas(df_ventas)

    st.subheader("🔎 Diagnóstico Ventas – Datos crudos")
    st.write(df_ventas.head())
    st.write("Columnas:", list(df_ventas.columns))

    df_ventas_val = validar_ventas_sii(df_ventas)

    st.subheader("✅ Resultado Validación Ventas")
    st.write(df_ventas_val["valido"].value_counts())

    st.subheader("📄 Detalle Ventas (primeras 20)")
    st.dataframe(df_ventas_val.head(20))

    df_ventas_ok = df_ventas_val[df_ventas_val["valido"] == True]

    documentos += normalizar_ventas(df_ventas_ok)

    st.success(f"Ventas válidas cargadas: {len(df_ventas_ok)}")


# -------- COMPRAS --------
st.subheader("📤 Compras SII")
archivo_compras = st.file_uploader("Cargar Compras", type="csv")

if archivo_compras:
    df_compras = pd.read_csv(archivo_compras, sep=";", decimal=",")
    df_compras = normalizar_columnas(df_compras)

    df_compras_val = validar_compras_sii(df_compras)
    df_compras_ok = df_compras_val[df_compras_val["valido"] == True]

    documentos += normalizar_compras(df_compras_ok)

    st.success(f"Compras válidas cargadas: {len(df_compras_ok)}")

# ==========================================
# VISUALIZACIÓN
# ==========================================

tipo_analisis_ui = st.radio(
    "Tipo de análisis",
    [
        "Resultado del negocio (sin impuestos)",
        "Movimiento de dinero (con impuestos)"
    ]
)

periodo_ui = st.selectbox(
    "Periodo",
    ["Mensual", "Trimestral", "Anual"]
)

if st.button("Ver resultado"):
    if not documentos:
        st.warning("Debes cargar al menos un archivo")
        st.stop()

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
            gastos = d["gastos_neto"]
        else:
            ingresos = d["ingresos_total"]
            gastos = d["gastos_total"]

        total_ingresos += ingresos
        total_gastos += gastos
        resultados.append(ingresos - gastos)

    resultado_final = total_ingresos - total_gastos

    st.subheader("📌 Resumen")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos", f"${total_ingresos:,.0f}")
    c2.metric("Gastos", f"${total_gastos:,.0f}")
    c3.metric("Resultado", f"${resultado_final:,.0f}")

    # =========================
    # Gráfico de torta (seguro)
    # =========================

    fig1, ax1 = plt.subplots()

    valores_pie = [
        max(total_ingresos, 0),
        max(total_gastos, 0)
    ]

    if sum(valores_pie) > 0:
        ax1.pie(
            valores_pie,
            labels=["Ingresos", "Gastos"],
            autopct="%1.0f%%",
            startangle=90
        )
        ax1.set_title("Distribución Ingresos vs Gastos")
        st.pyplot(fig1)
    else:
        st.info("No hay datos suficientes para mostrar el gráfico de torta.")

    fig2, ax2 = plt.subplots()
    ax2.bar(periodos, resultados)
    ax2.set_title("Resultado por periodo")
    ax2.tick_params(axis="x", rotation=45)
    st.pyplot(fig2)

