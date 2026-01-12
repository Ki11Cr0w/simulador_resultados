# ==========================
# app.py
# ==========================
import streamlit as st
import pandas as pd
from validaciones import validar_documentos

st.set_page_config(page_title="Simulador de Resultados SII", layout="wide")

st.title("Simulador de Resultados SII")
st.write("Carga tus archivos de **Ventas** y **Compras** para simular resultados.")

# --- Carga de archivos ---
col1, col2 = st.columns(2)

with col1:
    ventas_file = st.file_uploader("Archivo CSV de Ventas", type=["csv"], key="ventas")

with col2:
    compras_file = st.file_uploader("Archivo CSV de Compras", type=["csv"], key="compras")

# --- Inicialización de totales ---
total_ingresos = 0
total_egresos = 0

# --- Procesamiento ---
if ventas_file or compras_file:
    st.divider()

    if ventas_file:
        df_ventas = pd.read_csv(ventas_file)
        resultado_ventas = validar_documentos(df_ventas, tipo="Ventas")

        st.subheader("Resultado Validación Ventas")
        st.metric("Documentos válidos", resultado_ventas["validos"].shape[0])
        st.metric("Documentos rechazados", resultado_ventas["rechazados"].shape[0])

        if not resultado_ventas["validos"].empty:
            total_ingresos = resultado_ventas["validos"]["Monto"].sum()

        if not resultado_ventas["rechazados"].empty:
            st.warning("Se detectaron documentos rechazados en Ventas")
            st.dataframe(resultado_ventas["rechazados"], use_container_width=True)

    if compras_file:
        df_compras = pd.read_csv(compras_file)
        resultado_compras = validar_documentos(df_compras, tipo="Compras")

        st.subheader("Resultado Validación Compras")
        st.metric("Documentos válidos", resultado_compras["validos"].shape[0])
        st.metric("Documentos rechazados", resultado_compras["rechazados"].shape[0])

        if not resultado_compras["validos"].empty:
            total_egresos = resultado_compras["validos"]["Monto"].sum()

        if not resultado_compras["rechazados"].empty:
            st.warning("Se detectaron documentos rechazados en Compras")
            st.dataframe(resultado_compras["rechazados"], use_container_width=True)

# --- Resumen ---
st.divider()
st.subheader("Resumen General")
st.metric("Total Ingresos", max(total_ingresos, 0))
st.metric("Total Egresos", max(total_egresos, 0))
st.metric("Resultado", max(total_ingresos - total_egresos, 0))
