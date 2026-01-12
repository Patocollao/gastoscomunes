import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gastos Casa (Google Sheets)", page_icon="☁️", layout="centered")

MIEMBROS = ["Patricio (ytbl)", "Sergio (tururucini)"] 
MONEDA = "$" 

# --- CONEXIÓN CON GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    # ttl=0 hace que no use caché y siempre traiga los datos frescos de Google
    return conn.read(worksheet="Hoja 1", usecols=[0, 1, 2, 3], ttl=0)

def guardar_datos(df):
    conn.update(worksheet="Hoja 1", data=df)

def obtener_datos_ciclo_actual(df):
    if df.empty: return df
    cierres = df[df["Concepto"] == "⛔ CIERRE DE CICLO ⛔"]
    if not cierres.empty:
        ultimo_cierre_idx = cierres.index[-1]
        return df.loc[ultimo_cierre_idx + 1:]
    return df

# Cargar datos EN VIVO desde Google
try:
    df_historico = cargar_datos()
    # Aseguramos que los tipos de datos sean correctos para evitar errores
    df_historico = df_historico.dropna(how="all") # Limpiar filas vacías si las hay
    df_historico["Monto"] = pd.to_numeric(df_historico["Monto"], errors='coerce').fillna(0)
except Exception as e:
    st.error("Error conectando con Google Sheets. Revisa los 'Secrets'.")
    st.stop()

# --- INTERFAZ ---
st.title("☁️ Gastos Compartidos")
st.caption(f"Conectado a Google Sheets | {MIEMBROS[0]} & {MIEMBROS[1]}")

# --- FORMULARIO ---
with st.container():
    st.subheader("➕ Agregar Gasto")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            quien = st.selectbox("¿Quién pagó?", MIEMBROS)
        with col2:
            monto = st.number_input("Monto", min_value=0, step=100)
        
        concepto = st.text_input("Concepto")
        submitted = st.form_submit_button("Guardar en Nube", type="primary")
        
        if submitted:
            if monto > 0 and concepto:
                fecha = datetime.date.today().strftime("%Y-%m-%d")
                nuevo_gasto = pd.DataFrame({
                    "Fecha": [fecha],
                    "Pagado Por": [quien], 
                    "Concepto": [concepto], 
                    "Monto": [monto]
                })
                # Concatenamos y enviamos a Google
                df_actualizado = pd.concat([df_historico, nuevo_gasto], ignore_index=True)
                guardar_datos(df_actualizado)
                st.success("¡Guardado en Google Drive!")
                st.rerun()

# --- BALANCE DEL CICLO ---
st.markdown("---")
df_ciclo = obtener_datos_ciclo_actual(df_historico)

if not df_ciclo.empty:
    st.header("📊 Ciclo Actual")
    
    gastos_por_persona = df_ciclo.groupby("Pagado Por")["Monto"].sum()
    for m in MIEMBROS: 
        if m not in gastos_por_persona: gastos_por_persona[m] = 0.0

    total_ciclo = df_ciclo["Monto"].sum()
    cuota_justa = total_ciclo / 2

    c1, c2 = st.columns(2)
    c1.metric("Total Gastado", f"${total_ciclo:,.0f}")
    c2.metric("A poner c/u", f"${cuota_justa:,.0f}")
    
    p1, p2 = MIEMBROS[0], MIEMBROS[1]
    diff = gastos_por_persona[p1] - gastos_por_persona[p2]

    st.info(f"💰 {p1}: ${gastos_por_persona[p1]:,.0f} | {p2}: ${gastos_por_persona[p2]:,.0f}")
    
    if diff > 0:
        st.error(f"👉 **{p2}** debe pagarle a **{p1}**: ${diff/2:,.0f}")
    elif diff < 0:
        st.error(f"👉 **{p1}** debe pagarle a **{p2}**: ${abs(diff)/2:,.0f}")
    else:
        st.success("🎉 ¡Cuentas saldadas!")

    # Botón Cierre de Ciclo
    if st.button("🤝 Saldar y Cerrar Ciclo"):
        fecha_cierre = datetime.date.today().strftime("%Y-%m-%d")
        cierre_row = pd.DataFrame({
            "Fecha": [fecha_cierre], "Pagado Por": ["SISTEMA"],
            "Concepto": ["⛔ CIERRE DE CICLO ⛔"], "Monto": [0]
        })
        df_final = pd.concat([df_historico, cierre_row], ignore_index=True)
        guardar_datos(df_final)
        st.balloons()
        st.rerun()

else:
    st.info("Comenzamos nuevo ciclo.")

# --- HISTORIAL ---
with st.expander("Ver Historial Completo (Google Sheets)"):
    st.dataframe(df_historico, use_container_width=True)
    st.markdown(f"[Ver Hoja de Cálculo Original](https://docs.google.com/spreadsheets)")
