import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gastos Casa", page_icon="💸", layout="centered")

# --- CSS PARA ESTILO "APP NATIVA" ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {
                padding-top: 2rem;
                padding-bottom: 5rem;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. CONSTANTES ---
MIEMBROS = ["Patricio (ytbl)", "Sergio (tururucini)"] 
MONEDA = "$" 

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

# --- 4. LÓGICA PRINCIPAL ---
df_historico = cargar_datos()

# Título centrado
st.markdown("<h2 style='text-align: center;'>🏡 Gastos Compartidos</h2>", unsafe_allow_html=True)

# --- FORMULARIO ---
with st.container():
    with st.form("entry_form_v2", clear_on_submit=True):
        c1, c2 = st.columns(2)
        quien = c1.selectbox("Pagado por", MIEMBROS)
        monto = c2.number_input("Monto ($)", min_value=0.0, step=10.0)
        
        cat = st.selectbox("Categoría", CATEGORIAS)
        detalle = st.text_input("Detalle (Opcional)", placeholder="Ej. Sushi, Regalo...")
        
        enviar = st.form_submit_button("💾 REGISTRAR GASTO", type="primary", use_container_width=True)
        
        if enviar and monto > 0:
            if cat == "✏️ Otro (Escribir manual)":
                concepto_final = detalle if detalle else "Varios"
            else:
                concepto_final = f"{cat} ({detalle})" if detalle else cat
                
            fecha = datetime.date.today().strftime("%Y-%m-%d")
            nuevo = pd.DataFrame([{
                "Fecha": fecha, "Pagado Por": quien, 
                "Concepto": concepto_final, "Monto": monto
            }])
            
            df_historico = pd.concat([df_historico, nuevo], ignore_index=True)
            guardar_datos(df_historico)
            st.success("✅ ¡Guardado!")
            st.rerun()

# --- BALANCE ---
st.markdown("---")
df_ciclo = obtener_datos_ciclo_actual(df_historico)

if not df_ciclo.empty:
    st.markdown("<h4 style='text-align: center;'>📊 Balance Actual</h4>", unsafe_allow_html=True)
    
    gastos = df_ciclo.groupby("Pagado Por")["Monto"].sum()
    
    # --- CORRECCIÓN AQUÍ: Usamos la variable correcta 'MIEMBROS' ---
    for m in MIEMBROS: 
        if m not in gastos: gastos[m] = 0.0

    total = df_ciclo["Monto"].sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Total", f"${total:,.0f}")
    c2.metric("Mitad", f"${total/2:,.0f}")
    
    diff = gastos[MIEMBROS[0]] - gastos[MIEMBROS[1]]
    
    if diff > 0:
        st.warning(f"👉 **{MIEMBROS[1]}** debe pagar: **${diff/2:,.0f}**")
    elif diff < 0:
        st.warning(f"👉 **{MIEMBROS[0]}** debe pagar: **${abs(diff)/2:,.0f}**")
    else:
        st.success("✅ ¡Cuentas saldadas!")
        
    with st.expander("Ver lista de gastos"):
        st.dataframe(df_ciclo[["Fecha", "Pagado Por", "Concepto", "Monto"]], use_container_width=True)

    if st.button("🤝 Cerrar Ciclo (Todo Pagado)", use_container_width=True):
        cierre = pd.DataFrame([{
            "Fecha": datetime.date.today(), "Pagado Por": "SISTEMA",
            "Concepto": "⛔ CIERRE DE CICLO ⛔", "Monto": 0
        }])
        guardar_datos(pd.concat([df_historico, cierre], ignore_index=True))
        st.balloons()
        st.rerun()
else:
    st.info("Todo al día. No hay gastos pendientes.")
