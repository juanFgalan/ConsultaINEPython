# Lo que he tenido que hacer es realizar una descarga automatizada para poder leer el csv completo y despues con pandas filtrar los datos que me interesan para poder tenerlos a mano no es posible usar la api directamente porque no permite eso

import streamlit as st
import pandas as pd
import re

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
#  Interfaz Streamlit
# ----------------------------
st.title("📊 INE IPC - Consulta a Tablas")

# Selección de tabla
TABLAS = {
    50913: "IPC por provincias y subgrupos",
    50914: "IPC por comunidades autónomas",
    50915: "IPC por provincias y grupos ECOICOP",
    50916: "IPC por comunidades autónomas y grupos ECOICOP",
    50917: "IPC por provincias y tipo de dato ",
    50918: "IPC por comunidades autónomas y tipo de dato",
    50919: "IPC por provincias, grupos ECOICOP y tipo de dato"
}

#tabla_id = st.selectbox("Selecciona tabla", list(range(50913, 50920)))
# Selección de tabla
tabla_id = st.selectbox(
    "Selecciona tabla",
    options=list(TABLAS.keys()),
    format_func=lambda x: f"{x} - {TABLAS[x]}"
)

df = cargar_tabla(tabla_id)

# ----------------------------
# Filtro por rango de periodos
# ----------------------------
if "Periodo" in df.columns:
    periodos = df["Periodo"].dropna().unique()
    periodos_sorted = sorted(periodos, key=periodo_to_num)

    start_idx, end_idx = st.select_slider(
        "Selecciona rango de periodos",
        options=list(range(len(periodos_sorted))),
        value=(0, len(periodos_sorted)-1),
        format_func=lambda x: periodos_sorted[x]
    )

    periodo_inicio = periodos_sorted[start_idx]
    periodo_fin = periodos_sorted[end_idx]

    def in_rango(p):
        n = periodo_to_num(p)
        return periodo_to_num(periodo_inicio) <= n <= periodo_to_num(periodo_fin)
    
    df = df[df["Periodo"].apply(in_rango)]

# ----------------------------
# Filtros dinámicos de categorías
# ----------------------------
#variable placeholder para cambiar nombre de los selectores en esp
placeholderESP = " Selecciona una o varias opciones "

# Filtrar por localización (Provincias o Comunidades)
loc_col = None
for col in ["Comunidades y Ciudades Autónomas", "Provincias"]:
    if col in df.columns:
        loc_col = col
        break

if loc_col:
    loc_values = st.multiselect(loc_col, df[loc_col].dropna().unique(), placeholder = placeholderESP)
    if loc_values:
        df = df[df[loc_col].isin(loc_values)]

# Filtrar Subgrupos si existe (busca cualquier columna que contenga 'subgrupo')
subgrupo_col = None
for col in df.columns:
    if "subgrupo" in col.lower():
        subgrupo_col = col
        break

if subgrupo_col:
    subgrupos = st.multiselect("Subgrupos", df[subgrupo_col].dropna().unique(), placeholder = placeholderESP)
    if subgrupos:
        df = df[df[subgrupo_col].isin(subgrupos)]

# Filtrar Grupos ECOICOP
grupo_col = None
for col in df.columns:
    if "ecoicop" in col.lower():
        grupo_col = col
        break

if grupo_col:
    grupos = st.multiselect("Grupos ECOICOP", df[grupo_col].dropna().unique(), placeholder = placeholderESP)
    if grupos:
        df = df[df[grupo_col].isin(grupos)]

# Filtrar Tipo de dato si existe
tipo_col = None
for col in df.columns:
    if "tipo de dato" in col.lower():
        tipo_col = col
        break

if tipo_col:
    tipos = st.multiselect("Tipo de dato", df[tipo_col].dropna().unique(), placeholder = placeholderESP)
    if tipos:
        df = df[df[tipo_col].isin(tipos)]

# Filtrar Rúbricas si existe
rubrica_col = None
for col in df.columns:
    if "rúbricas" in col.lower():
        rubrica_col = col
        break

if rubrica_col:
    rubricas = st.multiselect("Rúbricas", df[rubrica_col].dropna().unique(), placeholder = placeholderESP)
    if rubricas:
        df = df[df[rubrica_col].isin(rubricas)]

# Filtrar Grupos especiales si existe
grupos_esp_col = None
for col in df.columns:
    if "grupos especiales" in col.lower():
        grupos_esp_col = col
        break

if grupos_esp_col:
    grupos_esp = st.multiselect("Grupos especiales", df[grupos_esp_col].dropna().unique(), placeholder = placeholderESP)
    if grupos_esp:
        df = df[df[grupos_esp_col].isin(grupos_esp)]

# ----------------------------
# Mostrar resultados
# ----------------------------
st.subheader("Datos filtrados")
st.dataframe(df.head(100)) # mostar los 100 primeros

# ----------------------------
# Botón de descarga
# ----------------------------
st.download_button(
    label="⬇️ Descargar datos filtrados",
    data=df.to_csv(index=False, sep=";"),
    file_name=f"tabla_{tabla_id}_filtrada.csv",
    mime="text/csv"
)