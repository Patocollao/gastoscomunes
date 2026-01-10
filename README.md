# 🏠 Gastos Compartidos

Aplicación web para gestionar gastos compartidos entre personas. Calcula automáticamente quién debe a quién y cuánto.

## 🚀 Cómo usar esta app

### Opción 1: Desplegar en Streamlit Cloud (Recomendado)

1. **Crear cuenta en Streamlit Cloud**
   - Ve a [share.streamlit.io](https://share.streamlit.io)
   - Inicia sesión con tu cuenta de GitHub

2. **Conectar tu repositorio**
   - Haz clic en "New app"
   - Selecciona este repositorio: `Patocollao/gastoscomunes`
   - Branch: `main`
   - Archivo principal: `app.py`
   - Haz clic en "Deploy"

3. **¡Listo!**
   - En unos minutos tendrás tu app funcionando
   - Obtendrás una URL pública como: `https://tu-app.streamlit.app`

### Opción 2: Ejecutar localmente

```bash
# Clonar el repositorio
git clone https://github.com/Patocollao/gastoscomunes.git
cd gastoscomunes

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la app
streamlit run app.py
```

## ✨ Funcionalidades

- ➕ Agregar gastos con nombre, concepto y monto
- 📊 Ver historial de gastos recientes
- 💰 Calcular automáticamente quién debe a quién
- 🗑️ Reiniciar gastos al final del mes
- 💾 Los datos se guardan en un archivo CSV

## 🛠️ Personalización

Puedes editar el archivo `app.py` para:
- Cambiar los nombres de las personas (línea 31)
- Modificar los colores y estilos
- Agregar más funcionalidades

## 📝 Nota importante

Esta app usa un archivo CSV local para guardar los datos. Si usas Streamlit Cloud, los datos se reiniciarán cada vez que la app se reinicie. Para datos persistentes, considera usar una base de datos externa.
