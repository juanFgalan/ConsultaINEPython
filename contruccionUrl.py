import streamlit as st
import pandas as pd
import re
from datetime import date

# ----------------------------
# Carga de tabla desde INE
# ----------------------------
@st.cache_data
def cargar_tabla(tabla_id: int) -> pd.DataFrame:
    url = f"https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{tabla_id}.csv"
    df = pd.read_csv(url, sep=";")
    df = df.rename(columns=lambda c: c.strip())  # limpiar espacios en columnas
    df = df.dropna(how="all", axis=1)            # quitar columnas vacías
    return df

# ----------------------------
# Función para convertir periodos a valor numérico
# ----------------------------
def periodo_to_num(periodo_str):
    if pd.isna(periodo_str):
        return -1
    s = str(periodo_str)
    if re.match(r"^\d{4}$", s):
        return int(s) * 100
    if re.match(r"^\d{4}M\d{1,2}$", s):
        year, month = s.split("M")
        return int(year) * 100 + int(month)
    if re.match(r"^\d{4}T\d$", s):
        year, q = s.split("T")
        month = (int(q) - 1) * 3 + 1
        return int(year) * 100 + month
    return -1

# ----------------------------
# Función para convertir periodos a fechas
# ----------------------------
def periodo_to_date(periodo_str):
    s = str(periodo_str)
    if re.match(r"^\d{4}$", s):
        return date(int(s), 1, 1)
    if re.match(r"^\d{4}M\d{1,2}$", s):
        year, month = map(int, s.split("M"))
        return date(year, month, 1)
    if re.match(r"^\d{4}T\d$", s):
        year, q = int(s[:4]), int(s[5])
        month = (q - 1) * 3 + 1
        return date(year, month, 1)
    return None

# ----------------------------
# Interfaz Streamlit
# ----------------------------
st.title("📊 INE IPC - Consulta a Tablas")

TABLAS = {
    50913: "IPC por provincias y subgrupos",
    50914: "IPC por comunidades autónomas",
    50915: "IPC por provincias y grupos ECOICOP",
    50916: "IPC por comunidades autónomas y grupos ECOICOP",
    50917: "IPC por provincias y tipo de dato ",
    50918: "IPC por comunidades autónomas y tipo de dato",
    50919: "IPC por provincias, grupos ECOICOP y tipo de dato"
}

# Selección de tabla
tabla_id = st.selectbox(
    "Selecciona tabla",
    options=list(TABLAS.keys()),
    format_func=lambda x: f"{x} - {TABLAS[x]}"
)

df = cargar_tabla(tabla_id)

# ----------------------------
# Filtro por rango de periodos con calendario
# ----------------------------
if "Periodo" in df.columns:
    periodos = df["Periodo"].dropna().unique()
    periodos_dates = [periodo_to_date(p) for p in periodos]
    
    # Ordenar por fecha
    periodos_dates_sorted, periodos_sorted = zip(*sorted(zip(periodos_dates, periodos)))

    # Selector de rango de fechas
    fechas_seleccionadas = st.date_input(
        "Selecciona rango de fechas",
        value=(periodos_dates_sorted[0], periodos_dates_sorted[-1])
    )

    # Normalizar selección a (inicio, fin)
    if isinstance(fechas_seleccionadas, tuple) and len(fechas_seleccionadas) == 2:
        fecha_inicio, fecha_fin = fechas_seleccionadas
    elif isinstance(fechas_seleccionadas, date):
        st.info("ℹ️ Has seleccionado una sola fecha. Se mostrarán solo los datos de ese día.")
        fecha_inicio = fecha_fin = fechas_seleccionadas
    else:
        st.warning("⚠️ No se ha seleccionado ninguna fecha válida.")
        st.stop()

    # Filtrar según rango seleccionado
    def in_rango(p):
        dt = periodo_to_date(p)
        return dt is not None and fecha_inicio <= dt <= fecha_fin

    df = df[df["Periodo"].apply(in_rango)]

    # Si no hay datos en el rango seleccionado
    if df.empty:
        st.warning("⚠️ No hay datos disponibles para el rango de fechas seleccionado.")
        st.stop()

# ----------------------------
# Filtros dinámicos de categorías
# ----------------------------
placeholderESP = " Selecciona una o varias opciones "

# Filtrar por localización (Provincias o Comunidades)
loc_col = None
for col in ["Comunidades y Ciudades Autónomas", "Provincias"]:
    if col in df.columns:
        loc_col = col
        break

if loc_col:
    loc_values = st.multiselect(loc_col, df[loc_col].dropna().unique(), placeholder=placeholderESP)
    if loc_values:
        df = df[df[loc_col].isin(loc_values)]

# Subgrupos
subgrupo_col = None
for col in df.columns:
    if "subgrupo" in col.lower():
        subgrupo_col = col
        break

if subgrupo_col:
    subgrupos = st.multiselect("Subgrupos", df[subgrupo_col].dropna().unique(), placeholder=placeholderESP)
    if subgrupos:
        df = df[df[subgrupo_col].isin(subgrupos)]

# Grupos ECOICOP
grupo_col = None
for col in df.columns:
    if "ecoicop" in col.lower():
        grupo_col = col
        break

if grupo_col:
    grupos = st.multiselect("Grupos ECOICOP", df[grupo_col].dropna().unique(), placeholder=placeholderESP)
    if grupos:
        df = df[df[grupo_col].isin(grupos)]

# Tipo de dato
tipo_col = None
for col in df.columns:
    if "tipo de dato" in col.lower():
        tipo_col = col
        break

if tipo_col:
    tipos = st.multiselect("Tipo de dato", df[tipo_col].dropna().unique(), placeholder=placeholderESP)
    if tipos:
        df = df[df[tipo_col].isin(tipos)]

# Rúbricas
rubrica_col = None
for col in df.columns:
    if "rúbricas" in col.lower():
        rubrica_col = col
        break

if rubrica_col:
    rubricas = st.multiselect("Rúbricas", df[rubrica_col].dropna().unique(), placeholder=placeholderESP)
    if rubricas:
        df = df[df[rubrica_col].isin(rubricas)]

# Grupos especiales
grupos_esp_col = None
for col in df.columns:
    if "grupos especiales" in col.lower():
        grupos_esp_col = col
        break

if grupos_esp_col:
    grupos_esp = st.multiselect("Grupos especiales", df[grupos_esp_col].dropna().unique(), placeholder=placeholderESP)
    if grupos_esp:
        df = df[df[grupos_esp_col].isin(grupos_esp)]

# ----------------------------
# Mostrar resultados
# ----------------------------
st.subheader("Datos filtrados")
st.dataframe(df.head(100))

# Botón de descarga
st.download_button(
    label="⬇️ Descargar datos filtrados",
    data=df.to_csv(index=False, sep=";"),
    file_name=f"tabla_{tabla_id}_filtrada.csv",
    mime="text/csv"
)
