import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gastos Casa", page_icon="💸", layout="centered")

# --- 2. CONSTANTES ---
# Nombres de los usuarios
MIEMBROS = ["Patricio (ytbl)", "Sergio (tururucini)"] 
MONEDA = "$" 

# IMPORTANTE: El nombre exacto de tu archivo y tu pestaña en Google Sheets
NOMBRE_ARCHIVO_SHEETS = "DB_Gastos_Casa"
NOMBRE_PESTANA = "Hoja 1"

# --- 3. CONEXIÓN CON GOOGLE SHEETS ---
# Establecemos la conexión usando los "Secrets"
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    """Lee los datos desde Google Sheets forzando la actualización (ttl=0)"""
    try:
        df = conn.read(
            spreadsheet=NOMBRE_ARCHIVO_SHEETS,
            worksheet=NOMBRE_PESTANA,
            usecols=[0, 1, 2, 3], # Lee solo las primeras 4 columnas
            ttl=0 # No guardar en memoria caché (importante para ver cambios al instante)
        )
        # Limpieza de datos básica
        df = df.dropna(how="all") # Eliminar filas vacías
        # Asegurar que el Monto sea un número y no texto
        df["Monto"] = pd.to_numeric(df["Monto"], errors='coerce').fillna(0)
        return df
    except Exception as e:
        # Si falla, devolvemos un DataFrame vacío para que no explote la app
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(columns=["Fecha", "Pagado Por", "Concepto", "Monto"])

def guardar_datos(df):
    """Sobrescribe la hoja de cálculo con los nuevos datos"""
    try:
        conn.update(
            spreadsheet=NOMBRE_ARCHIVO_SHEETS,
            worksheet=NOMBRE_PESTANA,
            data=df
        )
    except Exception as e:
        st.error(f"Error guardando datos: {e}")

def obtener_datos_ciclo_actual(df):
    """Filtra solo los gastos desde el último 'Cierre de Ciclo'"""
    if df.empty: return df
    
    cierres = df[df["Concepto"] == "⛔ CIERRE DE CICLO ⛔"]
    
    if not cierres.empty:
        ultimo_cierre_idx = cierres.index[-1]
        return df.loc[ultimo_cierre_idx + 1:]
    else:
        return df

# --- 4. CARGA INICIAL ---
df_historico = cargar_datos()

# --- 5. INTERFAZ: TÍTULO ---
st.title("🏡 Control de Gastos")
st.caption(f"Hola **{MIEMBROS[0]}** y **{MIEMBROS[1]}**")

# --- 6. INTERFAZ: AGREGAR GASTO ---
with st.container():
    st.subheader("➕ Nuevo Gasto")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            quien = st.selectbox("¿Quién pagó?", MIEMBROS)
        with col2:
            monto = st.number_input("Monto ($)", min_value=0, step=100)
        
        concepto = st.text_input("Concepto (Ej. Supermercado, Luz)")
        submitted = st.form_submit_button("Guardar Gasto", type="primary")
        
        if submitted:
            if monto > 0 and concepto:
                fecha = datetime.date.today().strftime("%Y-%m-%d")
                nuevo_gasto = pd.DataFrame({
                    "Fecha": [fecha],
                    "Pagado Por": [quien], 
                    "Concepto": [concepto], 
                    "Monto": [monto]
                })
                
                # Unimos el nuevo gasto al historial existente
                df_actualizado = pd.concat([df_historico, nuevo_gasto], ignore_index=True)
                
                # Guardamos en Google Sheets
                guardar_datos(df_actualizado)
                
                st.success("¡Gasto guardado en la nube! ☁️")
                st.rerun() # Recarga la página
            else:
                st.warning("Por favor ingresa un monto y un concepto.")

# --- 7. INTERFAZ: BALANCE Y DEUDAS ---
st.markdown("---")
df_ciclo = obtener_datos_ciclo_actual(df_historico)

if not df_ciclo.empty:
    st.header("📊 Ciclo Actual (Balance)")

    # Calcular totales por persona
    gastos_por_persona = df_ciclo.groupby("Pagado Por")["Monto"].sum()
    
    # Asegurar que ambos nombres existan en el cálculo (aunque sea con 0)
    for m in MIEMBROS:
        if m not in gastos_por_persona:
            gastos_por_persona[m] = 0.0

    total_ciclo = df_ciclo["Monto"].sum()
    cuota_justa = total_ciclo / 2

    # Mostrar métricas grandes
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Gastado", f"${total_ciclo:,.0f}")
    col_m2.metric("Cada uno debió poner", f"${cuota_justa:,.0f}")

    # Calcular quién debe a quién
    p1 = MIEMBROS[0] # Patricio
    p2 = MIEMBROS[1] # Sergio
    
    pago_p1 = gastos_por_persona[p1]
    pago_p2 = gastos_por_persona[p2]
    
    diferencia = pago_p1 - pago_p2

    # Mostrar barras de progreso o texto simple
    st.info(f"💰 **{p1}** puso: ${pago_p1:,.0f} | 💰 **{p2}** puso: ${pago_p2:,.0f}")

    if diferencia > 0:
        # P1 pagó más, P2 debe pagarle
        deuda = diferencia / 2
        st.error(f"👉 **{p2}** le debe a **{p1}**: ${deuda:,.0f}")
    elif diferencia < 0:
        # P2 pagó más, P1 debe pagarle
        deuda = abs(diferencia) / 2
        st.error(f"👉 **{p1}** le debe a **{p2}**: ${deuda:,.0f}")
    else:
        st.success("✅ ¡Cuentas saldadas! Nadie debe nada.")

    # Tabla de detalle
    with st.expander("Ver gastos de este mes"):
        st.dataframe(df_ciclo, use_container_width=True)

    # --- 8. BOTÓN PARA CERRAR CICLO ---
    st.markdown("---")
    st.subheader("⚙️ Opciones")
    if st.button("🤝 Saldar Cuentas y Comenzar de Cero"):
        fecha_cierre = datetime.date.today().strftime("%Y-%m-%d")
        # Creamos una fila "fantasma" que marca el cierre
        cierre_row = pd.DataFrame({
            "Fecha": [fecha_cierre],
            "Pagado Por": ["SISTEMA"],
            "Concepto": ["⛔ CIERRE DE CICLO ⛔"],
            "Monto": [0]
        })
        df_final = pd.concat([df_historico, cierre_row], ignore_index=True)
        guardar_datos(df_final)
        st.balloons()
        st.success("Ciclo cerrado correctamente.")
        st.rerun()

else:
    st.info("👋 Estamos en un nuevo ciclo. Agrega el primer gasto para ver el balance.")

# --- 9. HISTORIAL COMPLETO ---
st.markdown("---")
with st.expander("📂 Ver Historial Histórico Completo"):
    st.dataframe(df_historico, use_container_width=True)
    st.markdown("Datos almacenados en Google Sheets.")
