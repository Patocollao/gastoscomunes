import streamlit as st
import pandas as pd
import os

# Configuración de la página
st.set_page_config(page_title="Gastos de la Casa", page_icon="💸")

st.title("🏠 Gastos Compartidos")

# Nombre del archivo donde se guardan los datos
DATA_FILE = "gastos.csv"

# Función para cargar datos
def cargar_datos():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["Nombre", "Concepto", "Monto"])
    return pd.read_csv(DATA_FILE)

# Función para guardar datos
def guardar_datos(df):
    df.to_csv(DATA_FILE, index=False)

# Cargar el historial actual
df = cargar_datos()

# --- SECCIÓN 1: AGREGAR NUEVO GASTO ---
st.header("➕ Nuevo Gasto")

col1, col2 = st.columns(2)
with col1:
    nombre = st.selectbox("¿Quién pagó?", ["Persona A", "Persona B", "Persona C"]) # Edita los nombres aquí
with col2:
    monto = st.number_input("Monto ($)", min_value=0.0, format="%.2f")

concepto = st.text_input("¿Qué se compró?", placeholder="Ej. Supermercado, Internet...")

if st.button("Guardar Gasto", type="primary"):
    if monto > 0 and concepto:
        nuevo_gasto = pd.DataFrame({"Nombre": [nombre], "Concepto": [concepto], "Monto": [monto]})
        df = pd.concat([df, nuevo_gasto], ignore_index=True)
        guardar_datos(df)
        st.success("¡Gasto guardado correctamente!")
        st.rerun()
    else:
        st.warning("Por favor ingresa un monto y un concepto.")

# --- SECCIÓN 2: HISTORIAL Y CUENTAS ---
st.markdown("---")
st.header("📊 Balance")

if not df.empty:
    # Mostrar tabla de gastos recientes
    st.subheader("Historial reciente")
    st.dataframe(df.tail(10), use_container_width=True)

    # Calcular totales por persona
    total_por_persona = df.groupby("Nombre")["Monto"].sum()
    total_general = df["Monto"].sum()
    promedio_por_persona = total_general / len(total_por_persona)

    st.write(f"**Gasto Total de la casa:** ${total_general:,.2f}")
    st.write(f"**Cada uno debería haber pagado:** ${promedio_por_persona:,.2f}")

    st.subheader("¿Quién debe a quién?")
    
    # Lógica simple de balance
    for persona, total_pagado in total_por_persona.items():
        diferencia = total_pagado - promedio_por_persona
        if diferencia > 0:
            st.write(f"🟢 **{persona}** debe recibir: ${diferencia:,.2f}")
        elif diferencia < 0:
            st.write(f"🔴 **{persona}** debe pagar: ${abs(diferencia):,.2f}")
        else:
            st.write(f"⚪ **{persona}** está al día.")
            
    # Botón para borrar todo (Reinicio de mes)
    if st.button("🗑️ Reiniciar Mes (Borrar todo)"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.rerun()

else:
    st.info("No hay gastos registrados aún.")
