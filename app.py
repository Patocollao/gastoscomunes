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
    "💸 ABONO / PAGO DEUDA", # <--- NUEVA CATEGORÍA ESPECIAL
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

# Título
st.markdown("<h2 style='text-align: center;'>🏡 Gastos & Pagos</h2>", unsafe_allow_html=True)

# --- FORMULARIO ---
with st.container():
    with st.form("entry_form_v2", clear_on_submit=True):
        c1, c2 = st.columns(2)
        quien = c1.selectbox("Pagado por", MIEMBROS)
        monto = c2.number_input("Monto ($)", min_value=0.0, step=10.0)
        
        cat = st.selectbox("Categoría", CATEGORIAS)
        detalle = st.text_input("Detalle (Opcional)", placeholder="Ej. Sushi, o 'Transfiero lo del arriendo'")
        
        enviar = st.form_submit_button("💾 REGISTRAR", type="primary", use_container_width=True)
        
        if enviar and monto > 0:
            # Lógica del concepto
            if cat == "✏️ Otro (Escribir manual)":
                concepto_final = detalle if detalle else "Varios"
            elif cat == "💸 ABONO / PAGO DEUDA":
                 # Si es un abono, lo marcamos claro
                 concepto_final = f"💸 PAGO A COMPAÑERO ({detalle})" if detalle else "💸 PAGO DEUDA"
            else:
                concepto_final = f"{cat} ({detalle})" if detalle else cat
                
            fecha = datetime.date.today().strftime("%Y-%m-%d")
            nuevo = pd.DataFrame([{
                "Fecha": fecha, "Pagado Por": quien, 
                "Concepto": concepto_final, "Monto": monto
            }])
            
            df_historico = pd.concat([df_historico, nuevo], ignore_index=True)
            guardar_datos(df_historico)
            st.success("✅ ¡Registrado!")
            st.rerun()

# --- BALANCE INTELIGENTE (LA MAGIA ESTÁ AQUÍ) ---
st.markdown("---")
df_ciclo = obtener_datos_ciclo_actual(df_historico)

if not df_ciclo.empty:
    st.markdown("<h4 style='text-align: center;'>📊 Estado de Cuentas</h4>", unsafe_allow_html=True)
    
    # 1. Separamos Gastos Reales de los Abonos entre compañeros
    # Identificamos los abonos por el icono de billete volador 💸
    mask_abono = df_ciclo["Concepto"].str.contains("💸", na=False)
    
    df_gastos_reales = df_ciclo[~mask_abono] # Gastos de la casa (Super, Luz, etc)
    df_abonos = df_ciclo[mask_abono]         # Pagos entre Patricio y Sergio
    
    # 2. Calculamos DEUDA TOTAL (Basado solo en gastos reales)
    total_gastado = df_gastos_reales["Monto"].sum()
    cuota_individual = total_gastado / 2
    
    gastos_por_persona = df_gastos_reales.groupby("Pagado Por")["Monto"].sum()
    for m in MIEMBROS: 
        if m not in gastos_por_persona: gastos_por_persona[m] = 0.0
        
    # Diferencia original (Quién gastó más en la casa)
    p1, p2 = MIEMBROS[0], MIEMBROS[1] # Patricio, Sergio
    diff_original = gastos_por_persona[p1] - gastos_por_persona[p2]
    
    # 3. Calculamos ABONOS (Pagos ya realizados)
    abonos_por_persona = df_abonos.groupby("Pagado Por")["Monto"].sum()
    for m in MIEMBROS:
        if m not in abonos_por_persona: abonos_por_persona[m] = 0.0
        
    # Ajustamos la deuda con los abonos
    # Si Patricio gastó más (diff > 0), Sergio le debe. 
    # Pero si Sergio hizo abonos, restamos eso de su deuda.
    
    c1, c2 = st.columns(2)
    c1.metric("Gasto Total Casa", f"${total_gastado:,.0f}")
    c2.metric("Mitad Exacta", f"${cuota_individual:,.0f}")
    
    st.write(f"🔹 **{p1}** gastó en cosas: ${gastos_por_persona[p1]:,.0f}")
    st.write(f"🔹 **{p2}** gastó en cosas: ${gastos_por_persona[p2]:,.0f}")
    
    # Mostrar si hubo abonos
    if not df_abonos.empty:
        st.info(f"💸 Hubo pagos entre ustedes: {p1} abonó ${abonos_por_persona[p1]:,.0f} | {p2} abonó ${abonos_por_persona[p2]:,.0f}")

    # Lógica Final de Quién debe a Quién
    # (Lo que gastó P1 - Lo que gastó P2) - (Lo que abonó P1 - Lo que abonó P2)
    # Explicación: Si P1 gastó mucho, saldo positivo. Si P2 le transfirió (Abono P2), reduce el saldo.
    saldo_final = (gastos_por_persona[p1] - gastos_por_persona[p2]) + (abonos_por_persona[p1] - abonos_por_persona[p2])
    
    st.markdown("---")
    if saldo_final > 0:
        # Saldo a favor de P1 -> P2 debe pagar
        deuda = saldo_final / 2
        st.error(f"👉 **{p2}** le debe a **{p1}**: ${deuda:,.2f}")
    elif saldo_final < 0:
        # Saldo a favor de P2 -> P1 debe pagar
        deuda = abs(saldo_final) / 2
        st.error(f"👉 **{p1}** le debe a **{p2}**: ${deuda:,.2f}")
    else:
        st.success("✅ ¡Cuentas saldadas perfectamente!")

    # Tabla detallada
    with st.expander("Ver detalle de movimientos"):
        st.dataframe(df_ciclo[["Fecha", "Pagado Por", "Concepto", "Monto"]], use_container_width=True)

    # --- BOTÓN DE CIERRE CON RESUMEN ---
    if st.button("🤝 Cerrar Ciclo y Guardar Resumen", use_container_width=True):
        fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
        
        # Creamos 3 filas de resumen para que quede en el Excel
        fila_resumen_1 = pd.DataFrame([{
            "Fecha": fecha_hoy, "Pagado Por": "SISTEMA",
            "Concepto": f"📊 TOTAL CICLO: ${total_gastado:,.2f}", "Monto": 0
        }])
        fila_resumen_2 = pd.DataFrame([{
            "Fecha": fecha_hoy, "Pagado Por": "SISTEMA",
            "Concepto": f"💰 CUOTA INDIVIDUAL: ${cuota_individual:,.2f}", "Monto": 0
        }])
        fila_cierre = pd.DataFrame([{
            "Fecha": fecha_hoy, "Pagado Por": "SISTEMA",
            "Concepto": "⛔ CIERRE DE CICLO ⛔", "Monto": 0
        }])
        
        # Concatenamos todo
        df_final = pd.concat([df_historico, fila_resumen_1, fila_resumen_2, fila_cierre], ignore_index=True)
        guardar_datos(df_final)
        
        st.balloons()
        st.rerun()
else:
    st.info("Comenzando nuevo ciclo. No hay movimientos aún.")
