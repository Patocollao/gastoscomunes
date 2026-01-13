import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gastos Casa", page_icon="💸", layout="centered")

# --- 2. CONSTANTES Y CONFIGURACIÓN ---
MIEMBROS = ["Patricio (ytbl)", "Sergio (tururucini)"] 
MONEDA = "$" 

# --- TUS CATEGORÍAS PERSONALIZADAS ---
CATEGORIAS = [
    "🛒 Supermercado",
    "📱 Celulares",
    "🌐 Internet Casa",
    "🏠 Arriendo",
    "🛍️ Dollorama",
    "📦 Costco",
    "🍽️ Restaurante",
    "🧽 Limpieza / Aseo",
    "✏️ Otro (Escribir manual)"
]

# Google Sheets Config
NOMBRE_ARCHIVO_SHEETS = "DB_Gastos_Casa"
NOMBRE_PESTANA = "Hoja 1"

# --- 3. CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(
            spreadsheet=NOMBRE_ARCHIVO_SHEETS,
            worksheet=NOMBRE_PESTANA,
            usecols=[0, 1, 2, 3],
            ttl=0
        )
        df = df.dropna(how="all")
        df["Monto"] = pd.to_numeric(df["Monto"], errors='coerce').fillna(0)
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Fecha", "Pagado Por", "Concepto", "Monto"])

def guardar_datos(df):
    try:
        conn.update(
            spreadsheet=NOMBRE_ARCHIVO_SHEETS,
            worksheet=NOMBRE_PESTANA,
            data=df
        )
    except Exception as e:
        st.error(f"Error guardando: {e}")

def obtener_datos_ciclo_actual(df):
    if df.empty: return df
    cierres = df[df["Concepto"] == "⛔ CIERRE DE CICLO ⛔"]
    if not cierres.empty:
        return df.loc[cierres.index[-1] + 1:]
    return df

# --- 4. CARGA DE DATOS ---
df_historico = cargar_datos()

# --- 5. INTERFAZ ---
st.title("🏡 Gastos Compartidos")
st.caption(f"Hola **{MIEMBROS[0]}** y **{MIEMBROS[1]}**")

# --- FORMULARIO CON CATEGORÍAS NUEVAS ---
st.write("💡 *Tip: Si eliges 'Otro', escribe el detalle abajo.*")

with st.form("entry_form_v2", clear_on_submit=True):
    c1, c2 = st.columns(2)
    quien = c1.selectbox("Pagado por", MIEMBROS)
    monto = c2.number_input("Monto", min_value=0, step=500)
    
    # Aquí aparecen tus opciones nuevas
    cat = st.selectbox("Categoría", CATEGORIAS)
    
    detalle = st.text_input("Detalle opcional", placeholder="Ej. Qué se compró (Opcional)")
    
    enviar = st.form_submit_button("💾 Guardar", type="primary")
    
    if enviar and monto > 0:
        # Lógica para construir el nombre del gasto
        if cat == "✏️ Otro (Escribir manual)":
            # Si es 'Otro', usamos lo que escribas en detalle, o 'Varios' si lo dejas vacío
            concepto_final = detalle if detalle else "Varios"
        else:
            # Si es una categoría normal, agregamos el detalle entre paréntesis si existe
            concepto_final = f"{cat} ({detalle})" if detalle else cat
            
        fecha = datetime.date.today().strftime("%Y-%m-%d")
        nuevo = pd.DataFrame([{
            "Fecha": fecha, "Pagado Por": quien, 
            "Concepto": concepto_final, "Monto": monto
        }])
        
        df_historico = pd.concat([df_historico, nuevo], ignore_index=True)
        guardar_datos(df_historico)
        st.rerun()

# --- BALANCE Y TABLAS ---
df_ciclo = obtener_datos_ciclo_actual(df_historico)

if not df_ciclo.empty:
    st.header("📊 Balance del Mes")
    
    gastos = df_ciclo.groupby("Pagado Por")["Monto"].sum()
    for m in MIEMBROS: 
        if m not in gastos: gastos[m] = 0.0
        
    total = df_ciclo["Monto"].sum()
    cuota = total / 2
    
    c1, c2 = st.columns(2)
    c1.metric("Total", f"${total:,.0f}")
    c2.metric("Cuota c/u", f"${cuota:,.0f}")
    
    diff = gastos[MIEMBROS[0]] - gastos[MIEMBROS[1]]
    
    if diff > 0:
        st.error(f"👉 **{MIEMBROS[1]}** debe pagar: ${diff/2:,.0f}")
    elif diff < 0:
        st.error(f"👉 **{MIEMBROS[0]}** debe pagar: ${abs(diff)/2:,.0f}")
    else:
        st.success("✅ ¡Cuentas saldadas!")
        
    st.dataframe(df_ciclo, use_container_width=True)

    if st.button("✂️ Cerrar Ciclo (Saldar Cuentas)"):
        cierre = pd.DataFrame([{
            "Fecha": datetime.date.today(), "Pagado Por": "SISTEMA",
            "Concepto": "⛔ CIERRE DE CICLO ⛔", "Monto": 0
        }])
        guardar_datos(pd.concat([df_historico, cierre], ignore_index=True))
        st.balloons()
        st.rerun()
else:
    st.info("No hay gastos en este ciclo.")

with st.expander("Historial Completo"):
    st.dataframe(df_historico)
