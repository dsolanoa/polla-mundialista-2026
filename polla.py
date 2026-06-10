import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO
import json
import datetime
import time
import pytz
import re

# --- INICIALIZACIÓN DEL SESSION STATE ---
# Aseguramos que las variables críticas existan desde el segundo cero
if "jugador_activo" not in st.session_state:
    st.session_state.jugador_activo = "-- Selecciona --"

EQUIPOS_POR_GRUPO = {
    "Grupo A": ["México", "Sudáfrica", "República de Corea", "Chequia"],
    "Grupo B": ["Canadá", "Bosnia y Herzegovina", "Catar", "Suiza"],
    "Grupo C": ["Brasil", "Marruecos", "Haití", "Escocia"],
    "Grupo D": ["EE. UU.", "Paraguay", "Australia", "Turquía"],
    "Grupo E": ["Alemania", "Curazao", "Costa de Marfil", "Ecuador"],
    "Grupo F": ["Países Bajos", "Japón", "Suecia", "Túnez"],
    "Grupo G": ["Bélgica", "Egipto", "RI de Irán", "Nueva Zelanda"],
    "Grupo H": ["España", "Islas de Cabo Verde", "Arabia Saudí", "Uruguay"],
    "Grupo I": ["Francia", "Senegal", "Irak", "Noruega"],
    "Grupo J": ["Argentina", "Argelia", "Austria", "Jordania"],
    "Grupo K": ["Portugal", "RD Congo", "Uzbekistán", "Colombia"],
    "Grupo L": ["Inglaterra", "Croacia", "Ghana", "Panamá"]
}

FECHA_LIMITE_BRACKET = datetime.datetime(2026, 6, 11, 14, 0)
mundial_empezo = datetime.datetime.now() >= FECHA_LIMITE_BRACKET

# Cargar partidos
with open('partidos_nombres.json', 'r', encoding='utf-8') as f:
    nombres_reales = json.load(f)

# Cargar resultados reales (con manejo de error por si el archivo está vacío)
try:
    with open('resultados.json', 'r') as f:
        resultados_reales = json.load(f)
except FileNotFoundError:
    resultados_reales = {}

# Cargar nombres reales desde el JSON
try:
    with open("partidos_nombres.json", "r", encoding="utf-8") as f:
        nombres_reales = json.load(f)
except FileNotFoundError:
    nombres_reales = {} # Si no existe el archivo, usará nombres genéricos

from datetime import datetime

def esta_bloqueado(partido_id):
    # 🌎 1. Forzamos la zona horaria de Colombia/México para evitar desfases con el servidor
    zona_local = pytz.timezone("America/Bogota")
    ahora_local = datetime.now(zona_local)
    
    # 🔍 2. Buscamos el partido en la lista global 'partidos'
    # (Donde ya uniste lo que cargó de 'partidos_nombres.json' junto con los bucles de las fases finales)
    partido_encontrado = next((p for p in partidos if p["id"] == partido_id), None)
    
    if partido_encontrado:
        # Obtenemos el valor de la fecha. Buscamos en "cierre" o en "fecha" por si acaso.
        fecha_cierre = partido_encontrado.get("cierre", partido_encontrado.get("fecha", None))
        
        if fecha_cierre:
            try:
                # --- CASO A: La fecha viene como TEXTO (Suele pasar al leer el JSON de grupos) ---
                if isinstance(fecha_cierre, str):
                    # Limpiamos espacios y quitamos etiquetas de texto si las hay
                    fecha_limpia = fecha_cierre.strip()
                    # Convertimos el texto a un objeto datetime real
                    fecha_dt = datetime.strptime(fecha_limpia, "%Y-%m-%d %H:%M:%S")
                    fecha_final = zona_local.localize(fecha_dt)
                
                # --- CASO B: Ya es un objeto DATETIME (Como los que pusimos en INFO_OCTAVOS, etc.) ---
                elif isinstance(fecha_cierre, datetime):
                    # Si no tiene zona horaria asignada, se la ponemos
                    if fecha_cierre.tzinfo is None:
                        fecha_final = zona_local.localize(fecha_cierre)
                    else:
                        fecha_final = fecha_cierre
                else:
                    return False # Si el tipo de dato es extraño, lo dejamos abierto por seguridad
                
                # 🎯 COMPARACIÓN REAL EN TIEMPO REAL
                # Si la hora de tu reloj en Colombia ya es MAYOR o IGUAL a la del partido -> Se bloquea (True)
                return ahora_local >= fecha_final
                
            except Exception as e:
                print(f"Error procesando la fecha para el partido {partido_id}: {e}")
                
    # 3. Si el partido no existe o no tiene fecha asignada todavía, se queda abierto (False)
    return False

# Configuración de la página web
st.set_page_config(page_title="La Polla de los 8 - Mundial 2026", page_icon="⚽", layout="centered")

# --- CONEXIONES OFICIALES A TU GOOGLE SHEETS ---
URL_SHEET_CSV = "https://docs.google.com/spreadsheets/d/1jycuYiB2478uhqZw17ovONaAzMMla4l1c3vTrO3aYho/edit?usp=sharing"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbwTXyQkw4KYT4PotQyfLQp9x6xrG5JrYBO3XONi0SolW7wp5f7az2tX0HxU__LOO4se/exec"

# --- TRUCO DE FONDO CON IMAGEN LOCAL ---
def cargar_fondo_local(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        return encoded_string.decode()
    except FileNotFoundError:
        return None

fondo_base64 = cargar_fondo_local("fondo.jpg")
if fondo_base64:
    st.markdown(
        f"""
        <style>
        /* --- 1. DESTRABAR TODAS LAS CAPAS INTERNAS DE STREAMLIT --- */
        html, body, [data-testid="stAppViewContainer"], .main, [data-testid="stMainSpaceTrigger"] {{
            height: auto !important;
            min-height: 100vh !important;
            overflow-y: visible !important;
        }}

        /* --- 2. CONFIGURACIÓN DEL FONDO --- */
        .stApp {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("data:image/jpg;base64,{fondo_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            height: auto !important;
            min-height: 100vh !important;
        }}
        
        /* --- 3. CONTENEDOR DE LA POLLA (LA TARJETA OSCURA) --- */
        .block-container {{
            background: rgba(20, 20, 20, 0.85);
            padding: 30px !important;
            border-radius: 15px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.5);
            margin-top: 20px;
            margin-bottom: 50px;             /* Espacio extra al final para que respire el último partido */
            height: auto !important;          /* Se estira infinitamente con los partidos */
            min-height: calc(100vh - 40px) !important;
            overflow-y: visible !important;   /* No esconde nada hacia abajo */
            overflow-x: hidden !important;    /* Evita scroll de lados en celulares */
        }}
        
        /* --- 4. TUS ESTILOS DE COLORES E INPUTS (INTACTOS) --- */
        h1, h2, h3, p, span, label, .stMarkdown {{
            color: #ffffff !important;
        }}
        
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div {{
            background-color: #ffffff !important;
            color: #000000 !important;
            font-weight: 500;
        }}
        
        .stDataFrame div, .stDataFrame span, td, th {{
            color: #ffffff !important;
        }}
        
        button[data-baseweb="tab"] {{
            color: #bbbbbb !important;
        }}
        
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: #ffffff !important;
            font-weight: bold;
            border-bottom-color: #f04444 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    

st.title("⚽ Polla 2026: El Gran Derbi Solano-Alzate-Taborda-Vásquez 🧠")

with st.expander("📜 Reglamento y Sistema de Puntuación (¡Léase antes de apostar!)", expanded=True):
    st.markdown("""
    Para llevarse el pozo acumulado de la casa, cada acierto cuenta. El sistema calculará tus puntos automáticamente bajo la siguiente tabla:
    """)
    
    # Creamos la tabla de puntuación organizada por importancia
    tabla_puntos = {
        "Proceso / Acierto": [
            "🎯 Marcador Exacto", 
            "⚽ Ganador o Empate (Tendencia)", 
            "🏃‍♂️ Clasificados a Octavos", 
            "🏅 Clasificados a Cuartos", 
            "🥈 Clasificados a Semifinal", 
            "🏆 Clasificados a la Gran Final", 
            "👑 Campeón del Mundo"
        ],
        "Puntos Otorgados": [
            "6 Puntos", 
            "3 Puntos", 
            "2 Puntos (Por equipo)", 
            "3 Puntos (Por equipo)", 
            "4 Puntos (Por equipo)", 
            "6 Puntos (Por equipo)", 
            "10 Puntos"
        ],
        "Detalle": [
            "Pegarle al resultado idéntico (Ej: pusiste 2-1 y quedó 2-1).",
            "Acertar quién gana o si hay empate, pero no los goles exactos.",
            "Acertar qué equipos pasan de la fase de grupos.",
            "Acertar qué equipos logran meterse a los mejores 8.",
            "Acertar los 4 equipos que llegan a la recta final.",
            "Acertar los 2 finalistas que jugarán el último partido.",
            "Adivinar con precisión el dueño de la copa mundial."
        ]
    }
    
    # Dibujamos la tabla de forma elegante en Streamlit
    st.table(tabla_puntos)
    
    st.caption("💡 *Nota: Los puntos de los partidos (Marcador Exacto o Tendencia) no son acumulables entre sí por un mismo juego. Si aciertas el marcador exacto, te llevas 6 puntos en total en ese partido.*")

st.write("""
Bienvenidos al torneo oficial donde se acaban los favoritismos y las ayudas familiares. 

Sean **Solano Alzate**, **Solano**, **Alzate**, **Solano Taborda**, **Taborda** o **Vásquez**... ¡en esta app todos somos rivales! Son 87 batallas puras donde se define quién es el verdadero gurú del futbol ¡aquí hay plata de por medio y el botín se lo lleva solo el mejor! 💸🏆

*¿Listos para la gloria o para aguantarse el conteo de puntos cada fin de semana? ¡A pronosticar!*
""")

# 📋 Lista de tus 8 participantes oficiales originales
JUGADORES_PERMITIDOS = ["Duvan", "Marlon", "Adriana", "Anthony", "Irra", "Gloria", "Catherin", "Julio"]

# --- GENERACIÓN AUTOMÁTICA DEL CALENDARIO DE 88 PARTIDOS ---
partidos = []
id_partido = 1

# 2. DEFINIR LA LISTA DE GRUPOS (Aquí es donde te falta)
grupos = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

# 1. Fase de Grupos: 12 Grupos (A al L), 6 partidos por grupo = 72 partidos
try:
    with open("partidos_nombres.json", "r", encoding="utf-8") as f:
        nombres_reales = json.load(f)
except:
    nombres_reales = {}

# --- FUNCIÓN PARA OBTENER NOMBRE O USAR POR DEFECTO ---
def get_nombres_y_fecha(id_p, def_local, def_visitante, def_fecha, def_grupo):
    # Primero: ¿Existe este ID en el JSON?
    id_str = str(id_p)
    if str(id_p) in nombres_reales:
        data = nombres_reales[str(id_p)]
        # Usamos .get() para evitar errores si falta alguna llave
        loc = data.get("local", def_local)
        vis = data.get("visitante", def_visitante)
        fec = data.get("fecha", def_fecha)
        gru = data.get("grupo", def_grupo)

        return loc, vis, fec, gru
    
    # Si el ID NO está en el JSON, devolvemos los valores por defecto
    return def_local, def_visitante, def_fecha, def_grupo

# 1. Fase de Grupos
for g in grupos:
    parejas = [("Equipo 1", "Equipo 2"), ("Equipo 3", "Equipo 4"), ("Equipo 1", "Equipo 3"), 
               ("Equipo 4", "Equipo 2"), ("Equipo 4", "Equipo 1"), ("Equipo 2", "Equipo 3")]
    
    for local, visitante in parejas:
        # 1. Llamamos a la función con 5 parámetros y recibimos 4 valores
        l_name, v_name, fecha_cierre, grupo_real = get_nombres_y_fecha(
            id_partido, 
            f"{local} Grp {g}", 
            f"{visitante} Grp {g}", 
            "2026-06-30 18:00:00", 
            f"Grupo {g}" # Valor por defecto si no está en el JSON
        )
        
        # 2. Usamos 'grupo_real' en la fase para que muestre el valor correcto del JSON
        partidos.append({
            "id": id_partido,
            "pestana": f"Grupos {grupos[0]}-{grupos[3]}" if g in grupos[0:4] else (f"Grupos {grupos[4]}-{grupos[7]}" if g in grupos[4:8] else f"Grupos {grupos[8]}-{grupos[11]}"),
            "fase": grupo_real, 
            "fecha": "Fase de Grupos",
            "local": l_name,
            "visitante": v_name,
            "cierre": fecha_cierre
        })
        id_partido += 1

# 2. Octavos de Final
INFO_OCTAVOS = {
    73: {"local": "Clasificado 1", "visitante": "Clasificado 3", "fecha": "2026-07-04 12:00:00"},
    74: {"local": "Clasificado 3", "visitante": "Clasificado 4", "fecha": "2026-07-04 16:00:00"},
    75: {"local": "Clasificado 5", "visitante": "Clasificado 6", "fecha": "2026-07-05 15:00:00"},
    76: {"local": "Clasificado 7", "visitante": "Clasificado 8", "fecha": "2026-07-05 19:00:00"},
    77: {"local": "Clasificado 9", "visitante": "Clasificado 10", "fecha": "2026-07-06 14:00:00"},
    78: {"local": "Clasificado 11", "visitante": "Clasificado 12", "fecha": "2026-07-06 19:00:00"},
    79: {"local": "Clasificado 13", "visitante": "Clasificado 14", "fecha": "2026-07-07 11:00:00"},
    80: {"local": "Clasificado 15", "visitante": "Clasificado 16", "fecha": "2026-07-07 15:00:00"},
}

# --- 2. Bucle de Octavos de Final ---
for i in range(1, 9):
    # 1. Tomamos los valores del diccionario según el ID actual del partido
    config_partido = INFO_OCTAVOS[id_partido]
    
    # 2. Se los pasamos a tu función de mapeo
    l_name, v_name, fecha_cierre, fase_real = get_nombres_y_fecha(
        id_partido, 
        config_partido["local"], 
        config_partido["visitante"], 
        config_partido["fecha"], 
        "Octavos"
    )
    
    partidos.append({
        "id": id_partido, 
        "pestana": "Octavos de Final", 
        "fase": fase_real, 
        "fecha": fecha_cierre, # Muestra la fecha/hora formateada individual
        "local": l_name, 
        "visitante": v_name,
        "cierre": fecha_cierre 
    })
    id_partido += 1

# 3. Cuartos de Final
INFO_CUARTOS = {
    81: {"local": "Ganador Octavos 1", "visitante": "Ganador Octavos 2", "fecha": "2026-07-09 15:00:00"},
    82: {"local": "Ganador Octavos 3", "visitante": "Ganador Octavos 4", "fecha": "2026-07-10 14:00:00"},
    83: {"local": "Ganador Octavos 5", "visitante": "Ganador Octavos 6", "fecha": "2026-07-11 16:00:00"},
    84: {"local": "Ganador Octavos 7", "visitante": "Ganador Octavos 8", "fecha": "2026-07-11 20:00:00"},
}
for i in range(1, 5):
    config_partido = INFO_CUARTOS[id_partido]
    
    l_name, v_name, fecha_cierre, fase_real = get_nombres_y_fecha(
        id_partido, 
        config_partido["local"], 
        config_partido["visitante"], 
        config_partido["fecha"], 
        "Cuartos"
    )
    partidos.append({
        "id": id_partido, 
        "pestana": "Cuartos de Final", 
        "fase": fase_real, 
        "fecha": fecha_cierre, 
        "local": l_name, 
        "visitante": v_name,
        "cierre": fecha_cierre
    })
    id_partido += 1

# 4. Semifinales
INFO_SEMIFINALES = {
    85: {"local": "Ganador Cuartos 1", "visitante": "Ganador Cuartos 2", "fecha": "2026-07-14 14:00:00"},
    86: {"local": "Ganador Cuartos 3", "visitante": "Ganador Cuartos 4", "fecha": "2026-07-15 14:00:00"},
}
for i in range(1, 3):
    config_partido = INFO_SEMIFINALES[id_partido]
    
    l_name, v_name, fecha_cierre, fase_real = get_nombres_y_fecha(
        id_partido, 
        config_partido["local"], 
        config_partido["visitante"], 
        config_partido["fecha"], 
        "Semifinal"
    )
    partidos.append({
        "id": id_partido, 
        "pestana": "Semifinal y Finales", 
        "fase": fase_real, 
        "fecha": fecha_cierre, 
        "local": l_name, 
        "visitante": v_name,
        "cierre": fecha_cierre
    })
    id_partido += 1

# Gran Final
INFO_FINAL = {
    87: {"local": "Ganador Semifinal 1", "visitante": "Ganador Semifinal 2", "fecha": "2026-07-19 14:00:00"}
}
config_final = INFO_FINAL[87]
l_f, v_f, f_f, gru_f = get_nombres_y_fecha(
    87, 
    config_final["local"], 
    config_final["visitante"], 
    config_final["fecha"], 
    "Gran Final"
)
partidos.append({
    "id": 87, 
    "pestana": "Semifinal y Finales", 
    "fase": gru_f, 
    "fecha": f_f, 
    "local": l_f, 
    "visitante": v_f, 
    "cierre": f_f
})
# --- AÑADE ESTA LÍNEA AQUÍ ---
partidos.sort(key=lambda x: x["cierre"])


# --- CONFIGURACIÓN DE PUNTOS DE FASES ---
CONFIG_FASES = {
    "octavos": {"cantidad": 16, "puntos": 2, "titulo": "16 Clasificados a Octavos"},
    "cuartos": {"cantidad": 8, "puntos": 3, "titulo": "8 Clasificados a Cuartos"},
    "semi": {"cantidad": 4, "puntos": 4, "titulo": "4 Semifinalistas"},
    "final": {"cantidad": 2, "puntos": 6, "titulo": "2 Finalistas"},
    "campeon": {"cantidad": 1, "puntos": 10, "titulo": "Campeón del Mundo 🏆"}
}

# Inicialización de memorias
if "resultados_reales" not in st.session_state:
    st.session_state.resultados_reales = {p["id"]: {"goles_l": 0, "goles_v": 0, "jugado": False} for p in partidos}
if "fases_finales_reales" not in st.session_state:
    st.session_state.fases_finales_reales = {fase: ["Por definir"] * info["cantidad"] for fase, info in CONFIG_FASES.items()}

if "base_predicciones" not in st.session_state:
    st.session_state.base_predicciones = {}
    for jugador in JUGADORES_PERMITIDOS:
        st.session_state.base_predicciones[jugador] = {
            "partidos": {p["id"]: {"goles_l": 0, "goles_v": 0} for p in partidos},
            "fases": {fase: [""] * info["cantidad"] for fase, info in CONFIG_FASES.items()},
            "puntos_actuales": 0
        }

# Aseguramos también que las variables del Admin existan antes de llamar a la función
if "resultados_reales" not in st.session_state:
    st.session_state.resultados_reales = {p["id"]: {"goles_l": 0, "goles_v": 0, "jugado": False} for p in partidos}

if "fases_finales_reales" not in st.session_state:
    st.session_state.fases_finales_reales = {fase: ["Por definir"] * info["cantidad"] for fase, info in CONFIG_FASES.items()}

# =========================================================================
# 🔄 FUNCIÓN DE CARGA DESDE GOOGLE SHEETS (CSV)
# =========================================================================
def cargar_datos_desde_sheets():
    try:
        response = requests.get(URL_APPS_SCRIPT, allow_redirects=True)
        
        if response.status_code == 200:
            try:
                datos_jugadores = response.json()
            except ValueError:
                st.warning("⚠️ Google Sheets está procesando los datos. Los cambios se reflejarán por completo en unos segundos.")
                return
            
            if not datos_jugadores:
                return
                
            # 🧼 SUB-FUNCIÓN INTERNA PARA DETECTAR Y REPARAR MARCADORES MUTADOS
            def reparar_marcador(valor):
                if valor is None:
                    return None
                val_clean = str(valor).strip().replace("'", "") # Quitamos comillas remanentes
                
                if not val_clean or val_clean in ["-", "None", ""]:
                    return None
                    
                # Caso 1: Vino correcto como "X-Y"
                if "-" in val_clean and len(val_clean.split("-")) == 2:
                    partes = val_clean.split("-")
                    if partes[0].isdigit() and partes[1].isdigit():
                        return int(partes[0]), int(partes[1])
                
                # Caso 2: Google Sheets lo transformó en fecha estándar "YYYY-MM-DD..." (ej: 2026-02-01)
                # Evaluamos si cumple con el patrón de año-mes-día
                match_fecha = re.match(r"^(\d{4})[-/](\d{2})[-/](\d{2})", val_clean)
                if match_fecha:
                    # En fechas tipo 2026-02-01, el mes suele ser el marcador local y el día el visitante
                    gl = int(match_fecha.group(2))
                    gv = int(match_fecha.group(3))
                    return gl, gv
                    
                # Caso 3: Google Sheets lo transformó en fecha corta "DD/MM" o "MM/DD" (ej: 2/1 o 02/01)
                if "/" in val_clean:
                    partes = val_clean.split("/")
                    if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
                        return int(partes[0]), int(partes[1])
                        
                # Si no se pudo descifrar por mutación radical, devolvemos un estado seguro por defecto
                return None

            for row in datos_jugadores:
                jugador = str(row.get("Jugador", row.get("jugador", ""))).strip()
                
                # --- 🛠️ PROCESAR ADMINISTRADOR ---
                if jugador == "Admin":
                    for p in partidos:
                        try:
                            val_p = row.get(f"P_{p['id']}")
                            marcador_reparado = reparar_marcador(val_p)
                            
                            if marcador_reparado is None:
                                st.session_state.resultados_reales[p["id"]] = {
                                    "goles_l": 0, "goles_v": 0, "jugado": False
                                }
                            else:
                                gl, gv = marcador_reparado
                                estado_actual = st.session_state.resultados_reales.get(p["id"], {})
                                ya_jugado_en_pantalla = estado_actual.get("jugado", False)
                                
                                es_jugado = ya_jugado_en_pantalla if (gl == 0 and gv == 0) else True
                                    
                                st.session_state.resultados_reales[p["id"]] = {
                                    "goles_l": gl, "goles_v": gv, "jugado": es_jugado
                                }
                        except:
                            pass
                            
                    todas_fases = list(CONFIG_FASES.keys()) + ["campeon"]
                    for fase in todas_fases:
                        try:
                            val_f = row.get(fase.capitalize(), row.get(fase, None))
                            if val_f:
                                elementos = [e.strip() for e in str(val_f).split("-") if e.strip() != ""]
                                cant_max = 1 if fase == "campeon" else CONFIG_FASES[fase]["cantidad"]
                                while len(elementos) < cant_max: 
                                    elementos.append("Por definir")
                                    
                                if fase == "campeon":
                                    st.session_state.fases_finales_reales["campeon"] = elementos[:1]
                                else:
                                    st.session_state.fases_finales_reales[fase] = elementos[:cant_max]
                        except:
                            pass
                            
                # --- ⚽ PROCESAR JUGADORES ---
                elif jugador in st.session_state.base_predicciones:
                    for p in partidos:
                        try:
                            val_p = row.get(f"P_{p['id']}")
                            marcador_reparado = reparar_marcador(val_p)
                            
                            if marcador_reparado is not None:
                                gl, gv = marcador_reparado
                                st.session_state.base_predicciones[jugador]["partidos"][p["id"]] = {"goles_l": gl, "goles_v": gv}
                            else:
                                st.session_state.base_predicciones[jugador]["partidos"][p["id"]] = {"goles_l": 0, "goles_v": 0}
                        except:
                            st.session_state.base_predicciones[jugador]["partidos"][p["id"]] = {"goles_l": 0, "goles_v": 0}
                    
                    todas_fases = list(CONFIG_FASES.keys()) + ["campeon"]
                    for fase in todas_fases:
                        try:
                            val_f = row.get(fase.capitalize(), row.get(fase, None))
                            if val_f:
                                elementos = [e.strip() for e in str(val_f).split("-") if e.strip() != ""]
                                cant_max = 1 if fase == "campeon" else CONFIG_FASES[fase]["cantidad"]
                                while len(elementos) < cant_max: 
                                    elementos.append("")
                                    
                                st.session_state.base_predicciones[jugador]["fases"][fase] = elementos[:cant_max]
                        except:
                            pass
                
    except Exception as e:
        st.error(f"🚨 Error crítico al cargar datos desde la API: {e}")

# =========================================================================
# 🚀 GATILLO DE EJECUCIÓN ÚNICA VIA WEB
# =========================================================================
if "datos_cargados" not in st.session_state:
    cargar_datos_desde_sheets()
    st.session_state.datos_cargados = True

def enviar_datos_a_sheets(es_admin=False):
    try:
        jugador = "Admin" if es_admin else st.session_state.get("jugador_activo", "")
        datos_jugador = {"Jugador": jugador}
        
        # 🔄 CAPTURA DE GOLES (Partidos)
        for p in partidos:
            id_p = p['id']
            
            try:
                if es_admin:
                    res_partido = st.session_state.get("resultados_reales", {}).get(id_p, {})
                    
                    if res_partido.get("jugado", False):
                        goles_l = res_partido.get("goles_l", 0)
                        goles_v = res_partido.get("goles_v", 0)
                        # 🎯 TRUCO: Agregamos el apóstrofe "'" al principio para congelarlo como texto
                        datos_jugador[f"P_{id_p}"] = f"'{goles_l}-{goles_v}"
                    else:
                        datos_jugador[f"P_{id_p}"] = "-"
                else:
                    key_local = f"u_l_{id_p}_{jugador}"
                    key_vis = f"u_v_{id_p}_{jugador}"
                    goles_l = st.session_state.get(key_local, 0)
                    goles_v = st.session_state.get(key_vis, 0)
                    # 🎯 TRUCO: También protegemos las predicciones de los usuarios normales
                    datos_jugador[f"P_{id_p}"] = f"'{goles_l}-{goles_v}"
            except Exception as e_partido:
                print(f"Advertencia en partido {id_p}: {e_partido}")
                datos_jugador[f"P_{id_p}"] = "-" if es_admin else "'0-0"

        # 🔄 CAPTURA DE FASES FINALES
        fases_mapeo = {
            "Octavos": "octavos",
            "Cuartos": "cuartos",
            "Semi": "semi",
            "Final": "final",
            "Campeon": "campeon"
        }
        
        for columna_excel, llave_diccionario in fases_mapeo.items():
            datos_jugador[columna_excel] = "" 
            try:
                if es_admin:
                    dicc_fases = st.session_state.get("fases_finales_reales", {})
                    lista_equipos = dicc_fases.get(llave_diccionario, []) if isinstance(dicc_fases, dict) else []
                else:
                    lista_equipos = st.session_state.base_predicciones[jugador]["fases"].get(llave_diccionario, [])
                
                if lista_equipos:
                    equipos_limpios = [str(e).strip() for e in lista_equipos if e and str(e).strip() not in ["-- Selecciona --", "Por definir", ""]]
                    if equipos_limpios:
                        if columna_excel == "Campeon":
                            datos_jugador[columna_excel] = equipos_limpios[0]
                        else:
                            # 🎯 Aquí no suele haber problema, pero le ponemos protección por si acaso
                            datos_jugador[columna_excel] = " - ".join(equipos_limpios)
            except Exception as e_fase:
                print(f"Advertencia en fase {columna_excel}: {e_fase}")
                datos_jugador[columna_excel] = ""

        filas = [datos_jugador]

        print("====== 🚀 PAQUETE TEXTO CONGELADO EN RUTA A GOOGLE ======")
        print(filas)
        print("===============================================")

        headers = {"Content-Type": "application/json"}
        res = requests.post(URL_APPS_SCRIPT, json=filas, headers=headers)
        return res.status_code == 200

    except Exception as e_general:
        print(f"❌ ERROR CRÍTICO INTERNO EN ENVIAR_DATOS: {e_general}")
        return False
    
    # =========================================================================
    # PROCESAR JUGADORES
    # =========================================================================
    for jugador in JUGADORES_PERMITIDOS:
        datos = st.session_state.base_predicciones[jugador]
        # Inicializamos con valores vacíos para mantener la estructura perfecta de columnas
        fila = {llave: "" for llave in todas_las_llaves}
        fila["Jugador"] = jugador
        
        # Guardar predicciones de TODOS los partidos (Grupos + Fases Finales)
        for p in partidos:
            pred = datos["partidos"].get(p["id"], {"goles_l": 0, "goles_v": 0})
            fila[f"P_{p['id']}"] = f"{pred['goles_l']}-{pred['goles_v']}"
            
        # Guardar elecciones del Bracket
        for fase in CONFIG_FASES.keys():
            columna_sheet = fase.capitalize()
            # Validamos que existan datos en la llave de la fase para evitar KeyErrors
            lista_equipos = datos["fases"].get(fase, [])
            
            # Filtramos para no concatenar espacios vacíos ni el string por defecto del selector
            equipos_validos = [f for f in lista_equipos if f not in ["", "-- Selecciona --"]]
            fila[columna_sheet] = ", ".join(equipos_validos)
        
        filas.append(fila)
    
    # =========================================================================
    # PROCESAR ADMINISTRADOR (RESULTADOS REALES)
    # =========================================================================
    fila_admin = {llave: "" for llave in todas_las_llaves}
    fila_admin["Jugador"] = "Admin"
    
    # Guardar resultados reales de los partidos procesados
    for p in partidos:
        real = st.session_state.resultados_reales.get(p["id"], {"goles_l": 0, "goles_v": 0, "jugado": False})
        if real.get("jugado"):
            fila_admin[f"P_{p['id']}"] = f"{real['goles_l']}-{real['goles_v']}"
    
    # Guardar resultados reales del Bracket
    for fase in CONFIG_FASES.keys():
        columna_sheet = fase.capitalize()
        lista_real_admin = st.session_state.fases_finales_reales.get(fase, [])
        
        # Filtramos banderas de exclusión incluyendo el nuevo "-- Selecciona --"
        reales_validos = [f for f in lista_real_admin if f not in ["Por definir", "-- Selecciona --", ""]]
        fila_admin[columna_sheet] = ", ".join(reales_validos)
    
    filas.append(fila_admin)
    
    # =========================================================================
    # ENVIAR A GOOGLE SHEETS
    # =========================================================================
    try:
        headers = {"Content-Type": "application/json"}
        print("Datos a enviar:", json.dumps(filas, indent=2))
        res = requests.post(URL_APPS_SCRIPT, json=filas, headers=headers)
        return res.status_code == 200
    except: 
        return False

# --- NAVEGACIÓN ---
st.sidebar.header("🕹️ Navegación")
menu = st.sidebar.selectbox("¿A dónde quieres ir?", ["🏆 Tabla de Posiciones Generales", "🏃 Entrar a mi Perfil (Jugadores)", "⚙️ Panel Administrador"])

if menu == "🏆 Tabla de Posiciones Generales":
    st.header("🏆 Clasificación General de los 8")
    tabla_puntos = []
    for jugador in JUGADORES_PERMITIDOS:
        puntos_totales = 0
        datos_j = st.session_state.base_predicciones[jugador]
        for p_id, pronostico in datos_j["partidos"].items():
            real = st.session_state.resultados_reales[p_id]
            if real["jugado"]:
                tend_user = 1 if pronostico['goles_l'] > pronostico['goles_v'] else (-1 if pronostico['goles_l'] < pronostico['goles_v'] else 0)
                tend_real = 1 if real['goles_l'] > real['goles_v'] else (-1 if real['goles_l'] < real['goles_v'] else 0)
                if pronostico['goles_l'] == real['goles_l'] and pronostico['goles_v'] == real['goles_v']: puntos_totales += 6
                elif tend_user == tend_real: puntos_totales += 3
        
        for fase, info in CONFIG_FASES.items():
            lista_real = [r.strip().lower() for r in st.session_state.fases_finales_reales[fase] if r != "por definir" and r != ""]
            lista_user = [u.strip().lower() for u in datos_j["fases"][fase] if u != ""]
            for equipo_user in lista_user:
                if equipo_user in lista_real: puntos_totales += info["puntos"]
                    
        st.session_state.base_predicciones[jugador]["puntos_actuales"] = puntos_totales
        tabla_puntos.append({"Jugador": jugador, "Puntos Totales": puntos_totales})
    
    df_puntos = pd.DataFrame(tabla_puntos).sort_values(by="Puntos Totales", ascending=False).reset_index(drop=True)
    st.dataframe(df_puntos, use_container_width=True)

elif menu == "🏃 Entrar a mi Perfil (Jugadores)":
    st.header("🏃 Zona de Jugadores")
    jugador_activo = st.selectbox("Selecciona tu nombre:", ["-- Selecciona --"] + JUGADORES_PERMITIDOS, key="jugador_activo")
    if jugador_activo != "-- Selecciona --":
        tabs_principales = st.tabs(["📝 Marcadores", "📊 Estadísticas", "👀 Chismosear"])
        # 2. Usamos los índices [0], [1] y [2] en lugar de redeclarar
        tab1 = tabs_principales[0]
        tab2 = tabs_principales[1]
        tab3 = tabs_principales[2]
        
        with tab1:
            st.subheader("📅 Marcadores de Partidos")
        
            # 1. Definimos los nuevos nombres de las pestañas
            nombres_pestanas = [
            "Etapa 1", "Etapa 2", "Etapa 3", 
            "Octavos de Final", "Cuartos de Final", "Semifinal y Finales"
            ]
        
            # 2. Creamos las pestañas
            sub_tabs = st.tabs(nombres_pestanas)
            
            pred_partidos = st.session_state.base_predicciones[jugador_activo]["partidos"]
            
            # 3. Lógica para asignar partidos a cada pestaña
            # Primero, filtramos los de las fases finales usando la etiqueta "pestana" 
            # que ya tienes en tus append
            partidos_octavos = [p for p in partidos if p["pestana"] == "Octavos de Final"]
            partidos_cuartos = [p for p in partidos if p["pestana"] == "Cuartos de Final"]
            partidos_semis_final = [p for p in partidos if p["pestana"] == "Semifinal y Finales"]

            # Para las etapas de grupos, dividimos la lista de grupos ordenada cronológicamente
            # Partidos de grupo son los que NO están en las fases finales (asumiendo que los marcaste así)
            partidos_grupos = [p for p in partidos if p["pestana"] not in ["Octavos de Final", "Cuartos de Final", "Semifinal y Finales"]]

            # Ahora asignamos cada sub-lista a la pestaña correspondiente
            etapa_data = {
                "Etapa 1": partidos_grupos[:27],
                "Etapa 2": partidos_grupos[27:52],   # 27 + 25 = 52
                "Etapa 3": partidos_grupos[52:72],   # 52 + 20 = 72 (Total grupos)
                "Octavos de Final": partidos_octavos,
                "Cuartos de Final": partidos_cuartos,
                "Semifinal y Finales": partidos_semis_final
            }
            
            for t_idx, nombre_p in enumerate(nombres_pestanas):
                with sub_tabs[t_idx]:
                    partidos_fase = etapa_data.get(nombre_p, [])
                    
                    if not partidos_fase:
                        st.info(f"No hay partidos programados en {nombre_p} aún.")
                        continue
                        
                    # =========================================================================
                    # 📅 FILTRO POR FECHAS DINÁMICO
                    # =========================================================================
                    # Extraemos la fecha (AAAA-MM-DD) del campo cierre
                    fechas_disponibles = sorted(list(set(p['cierre'].split(" ")[0] for p in partidos_fase)))
                    opciones_filtro = ["📅 Mostrar todas las fechas"] + fechas_disponibles
                    
                    fecha_seleccionada = st.selectbox(
                        "Filtrar partidos por día:",
                        options=opciones_filtro,
                        key=f"filtro_fecha_{t_idx}_{jugador_activo}"
                    )
                    
                    # Aplicamos el filtro a la sublista
                    if fecha_seleccionada != "📅 Mostrar todas las fechas":
                        partidos_mostrar = [p for p in partidos_fase if p['cierre'].startswith(fecha_seleccionada)]
                    else:
                        partidos_mostrar = partidos_fase
                        
                    st.write("---") 
                    
                    # =========================================================================
                    # DESPLIEGUE EXCLUSIVO DE PARTIDOS FILTRADOS
                    # =========================================================================
                    if not partidos_mostrar:
                        st.info("No hay partidos para la fecha seleccionada.")
                    else:
                        for partido in partidos_mostrar:
                            st.markdown(f"**{partido['local']} vs {partido['visitante']}** (`ID: {partido['id']}` - *{partido['fase']}*)")
                            st.caption(f"⏰ Fecha y hora: {partido['cierre']}")
                            
                            col1, col2 = st.columns(2)
                            with col1: 
                                gl = st.number_input(f"Goles {partido['local']}", min_value=0, max_value=10, 
                                                    value=pred_partidos[partido['id']]["goles_l"], 
                                                    key=f"u_l_{partido['id']}_{jugador_activo}", 
                                                    disabled=esta_bloqueado(partido['id']))
                            with col2: 
                                gv = st.number_input(f"Goles {partido['visitante']}", min_value=0, max_value=10, 
                                                    value=pred_partidos[partido['id']]["goles_v"], 
                                                    key=f"u_v_{partido['id']}_{jugador_activo}", 
                                                    disabled=esta_bloqueado(partido['id']))
                            
                            st.session_state.base_predicciones[jugador_activo]["partidos"][partido['id']] = {"goles_l": gl, "goles_v": gv}
                            st.divider()
            
            # =========================================================================
            # 🏆 BRACKET DE FASES FINALES (ELECCIÓN DE EQUIPOS)
            # =========================================================================
            st.write("##")
            st.header("🏆 Elección de Equipos Clasificados por Fase")
            
            if mundial_empezo:
                st.error("🔒 El periodo de modificaciones para el Bracket de clasificados ha cerrado porque el Mundial ya inició.")
            else:
                st.warning("⚠️ Tienes hasta el inicio del primer partido del mundial para configurar o modificar esta sección.")
            
            # 1. Lista con TODOS los equipos del mundial ordenados alfabéticamente
            todos_los_equipos = ["-- Selecciona --"] + sorted([eq for sublist in EQUIPOS_POR_GRUPO.values() for eq in sublist])

            # --- 1. CONFIGURACIÓN COMPLETA DE OCTAVOS ---
            st.markdown("### ⚽ Clasificados a Octavos de Final (Ganadores de Dieciseisavos)")
            st.caption("Selecciona las 16 selecciones que crees que ganarán sus llaves de dieciseisavos de final y entrarán a Octavos.")
            config_octavos = [
                {"label": "Ganador Llave 1 (W1)", "index": 0}, {"label": "Ganador Llave 2 (W2)", "index": 1},
                {"label": "Ganador Llave 3 (W3)", "index": 2}, {"label": "Ganador Llave 4 (W4)", "index": 3},
                {"label": "Ganador Llave 5 (W5)", "index": 4}, {"label": "Ganador Llave 6 (W6)", "index": 5},
                {"label": "Ganador Llave 7 (W7)", "index": 6}, {"label": "Ganador Llave 8 (W8)", "index": 7},
                {"label": "Ganador Llave 9 (W9)", "index": 8}, {"label": "Ganador Llave 10 (W10)", "index": 9},
                {"label": "Ganador Llave 11 (W11)", "index": 10}, {"label": "Ganador Llave 12 (W12)", "index": 11},
                {"label": "Ganador Llave 13 (W13)", "index": 12}, {"label": "Ganador Llave 14 (W14)", "index": 13},
                {"label": "Ganador Llave 15 (W15)", "index": 14}, {"label": "Ganador Llave 16 (W16)", "index": 15},
            ]

            col_oct1, col_oct2 = st.columns(2)
            for idx, casilla in enumerate(config_octavos):
                col_actual = col_oct1 if idx % 2 == 0 else col_oct2
                with col_actual:
                    val_actual = st.session_state.base_predicciones[jugador_activo]["fases"]["octavos"][casilla["index"]]
                    default_idx = todos_los_equipos.index(val_actual) if val_actual in todos_los_equipos else 0
                    
                    nuevo_val = st.selectbox(
                        f"{casilla['label']}:",
                        options=todos_los_equipos,
                        index=default_idx,
                        key=f"sel_oct_{casilla['index']}_{jugador_activo}",
                        disabled=mundial_empezo
                    )
                    if nuevo_val != "-- Selecciona --":
                        st.session_state.base_predicciones[jugador_activo]["fases"]["octavos"][casilla["index"]] = nuevo_val

            # --- 2. OTRAS FASES COMPLETAS (CUARTOS, SEMIFINALES, FINALISTAS Y CAMPEÓN) ---
            st.markdown("### 🥈 Cuartos, Semifinales, Finales y Campeón")
            
            col_fases1, col_fases2 = st.columns(2)
            
            # --- COLUMNA IZQUIERDA: CUARTOS DE FINAL (8 CASILLAS) ---
            with col_fases1:
                st.write("**Cuartos de Final (Elige 8 equipos):**")
                
                lista_cuartos = st.session_state.base_predicciones[jugador_activo]["fases"].get("cuartos", [])
                while len(lista_cuartos) < 8:
                    lista_cuartos.append("")
                st.session_state.base_predicciones[jugador_activo]["fases"]["cuartos"] = lista_cuartos
                
                for i in range(8):
                    val_cuartos = st.session_state.base_predicciones[jugador_activo]["fases"]["cuartos"][i]
                    def_idx_c = todos_los_equipos.index(val_cuartos) if val_cuartos in todos_los_equipos else 0
                    
                    nuevo_cuartos = st.selectbox(
                        f"Cuartos - Cupo {i+1}:", 
                        todos_los_equipos, 
                        index=def_idx_c, 
                        key=f"sel_cua_{i}_{jugador_activo}",
                        disabled=mundial_empezo
                    )
                    if nuevo_cuartos != "-- Selecciona --":
                        st.session_state.base_predicciones[jugador_activo]["fases"]["cuartos"][i] = nuevo_cuartos

            # --- COLUMNA DERECHA: SEMIS (4), FINAL (2) Y CAMPEÓN (1) ---
            with col_fases2:
                st.write("**Fases Finales y Campeón:**")
                
                # --- SEMIFINALISTAS (4 CUPOS) ---
                # Cambiado de "semis" a "semi" para consistencia con CONFIG_FASES
                lista_semis = st.session_state.base_predicciones[jugador_activo]["fases"].get("semi", [])
                while len(lista_semis) < 4:
                    lista_semis.append("")
                st.session_state.base_predicciones[jugador_activo]["fases"]["semi"] = lista_semis
                
                for i in range(4):
                    val_semi = st.session_state.base_predicciones[jugador_activo]["fases"]["semi"][i]
                    def_idx_s = todos_los_equipos.index(val_semi) if val_semi in todos_los_equipos else 0
                    
                    nuevo_semi = st.selectbox(
                        f"Semifinalista {i+1}:", 
                        todos_los_equipos, 
                        index=def_idx_s, 
                        key=f"sel_semi_{i}_{jugador_activo}",
                        disabled=mundial_empezo
                    )
                    if nuevo_semi != "-- Selecciona --":
                        st.session_state.base_predicciones[jugador_activo]["fases"]["semi"][i] = nuevo_semi
                        
                st.write("---")
                
                # --- FINALISTAS (2 CUPOS) --- ⚽ ¡Añadido con éxito!
                st.write("**Gran Final (Elige los 2 Finalistas):**")
                lista_final = st.session_state.base_predicciones[jugador_activo]["fases"].get("final", [])
                while len(lista_final) < 2:
                    lista_final.append("")
                st.session_state.base_predicciones[jugador_activo]["fases"]["final"] = lista_final
                
                for i in range(2):
                    val_final = st.session_state.base_predicciones[jugador_activo]["fases"]["final"][i]
                    def_idx_f = todos_los_equipos.index(val_final) if val_final in todos_los_equipos else 0
                    
                    nuevo_final = st.selectbox(
                        f"Finalista {i+1} (Avanza a la Final):", 
                        todos_los_equipos, 
                        index=def_idx_f, 
                        key=f"sel_final_{i}_{jugador_activo}",
                        disabled=mundial_empezo
                    )
                    if nuevo_final != "-- Selecciona --":
                        st.session_state.base_predicciones[jugador_activo]["fases"]["final"][i] = nuevo_final

                st.write("---")

                # --- CAMPEÓN ÚNICO (1 CUPO) ---
                lista_campeon = st.session_state.base_predicciones[jugador_activo]["fases"].get("campeon", [])
                while len(lista_campeon) < 1:
                    lista_campeon.append("")
                st.session_state.base_predicciones[jugador_activo]["fases"]["campeon"] = lista_campeon
                
                val_campeon = st.session_state.base_predicciones[jugador_activo]["fases"]["campeon"][0]
                def_idx_camp = todos_los_equipos.index(val_campeon) if val_campeon in todos_los_equipos else 0
                
                nuevo_campeon = st.selectbox(
                    "🏆 ¿Quién será el Campeón?:", 
                    todos_los_equipos, 
                    index=def_idx_camp, 
                    key=f"sel_camp_{jugador_activo}",
                    disabled=mundial_empezo
                )
                if nuevo_campeon != "-- Selecciona --":
                    st.session_state.base_predicciones[jugador_activo]["fases"]["campeon"][0] = nuevo_campeon

            # --- 3. BOTÓN DE GUARDADO ---
            st.write("---")
            if st.button("💾 Guardar Mis Pronósticos", width="stretch"):
                with st.spinner("Guardando tus apuestas en la nube... 🚀"):
                    
                    # 🎯 CHISMOSO 1: Ver en la web qué está intentando mandar antes de enviarlo
                    st.write("DEBUG - Intentando enviar datos al Apps Script...")
                    
                    if enviar_datos_a_sheets():
                        # 🔄 1. Descargamos los datos frescos rompiendo la caché de Google de inmediato
                        cargar_datos_desde_sheets()
                        
                        # 🎉 2. Mensaje animado con la vibra del dinero y el pozo familiar
                        st.success("¡Marcadores blindados con éxito! Tus datos ya están en la nube y listos para pelear por ese pozo acumulado. ¡Que tiemble el resto de la casa! 🎉💰")
                        st.balloons()
                        
                        # ⏰ 3. Pausa corta para ver los globos
                        time.sleep(1)
                        
                        # 🔄 4. Forzamos el refresco visual para consolidar los cambios en la pantalla
                        st.rerun()
                    else:
                        # 🎯 CHISMOSO 2: Si falla, que nos muestre una alerta roja explicativa
                        st.error("Error de conexión al guardar tus pronósticos. Revisa la consola negra (CMD) para ver el código de error de Google.")
        with tab2:
            st.subheader("📊 Resumen de mis Apuestas")
            
            # --- AQUÍ ESTÁ LA CLAVE ---
            # Lee directamente del session_state que el administrador está modificando
            resultados_reales = st.session_state.resultados_reales 

            pred_jugador = st.session_state.base_predicciones[jugador_activo]["partidos"]

            datos_tabla = []
            pts_partidos = 0

            # --- 1. CÁLCULO DE PUNTOS POR PARTIDOS ---
            for partido in partidos:
                id_p = partido['id']
                apuesta = pred_jugador.get(id_p, {"goles_l": 0, "goles_v": 0})
                real = resultados_reales.get(id_p, {"goles_l": None, "goles_v": None, "jugado": False})
                
                puntos = 0
                if real.get("jugado", False):
                    if apuesta["goles_l"] == real["goles_l"] and apuesta["goles_v"] == real["goles_v"]:
                        puntos = 6
                    elif (apuesta["goles_l"] > apuesta["goles_v"] and real["goles_l"] > real["goles_v"]) or \
                        (apuesta["goles_l"] < apuesta["goles_v"] and real["goles_l"] < real["goles_v"]) or \
                        (apuesta["goles_l"] == apuesta["goles_v"] and real["goles_l"] == real["goles_v"]):
                        puntos = 3
                
                pts_partidos += puntos
                
                datos_tabla.append({
                    "Partido": f"{partido['local']} vs {partido['visitante']}",
                    "Apuesta": f"{apuesta['goles_l']}-{apuesta['goles_v']}",
                    "Marcador": f"{real['goles_l']}-{real['goles_v']}" if real.get("jugado") else "---",
                    "Pts": puntos
                })

            # --- 2. CÁLCULO DE PUNTOS DINÁMICO POR BRACKET (USANDO TU CONFIG_FASES) ---
            pts_bracket = 0
            datos_fases_tabla = []

            CONFIG_FASES = {
                "octavos": {"cantidad": 16, "puntos": 2, "titulo": "16 Clasificados a Octavos"},
                "cuartos": {"cantidad": 8, "puntos": 3, "titulo": "8 Clasificados a Cuartos"},
                "semi": {"cantidad": 4, "puntos": 4, "titulo": "4 Semifinalistas"},
                "final": {"cantidad": 2, "puntos": 6, "titulo": "2 Finalistas"},
                "campeon": {"cantidad": 1, "puntos": 10, "titulo": "Campeón del Mundo 🏆"}
            }

            pred_fases_jugador = st.session_state.base_predicciones[jugador_activo].get("fases", {})
            fases_reales_admin = st.session_state.get("fases_finales_reales", {})

            for llave_fase, info in CONFIG_FASES.items():
                lista_jugador = pred_fases_jugador.get(llave_fase, [])
                lista_real = fases_reales_admin.get(llave_fase, [])
                
                # Puntos asignados por cada acierto en esta fase específica
                puntos_por_acierto = info["puntos"]
                titulo_pantalla = info["titulo"]
                
                for equipo in lista_jugador:
                    if equipo and equipo != "-- Selecciona --":
                        # Si el equipo predicho por el jugador está en la lista real validada por el Admin
                        if equipo in lista_real:
                            estado = f"✅ Acertado (+{puntos_por_acierto} pts)"
                            pts_bracket += puntos_por_acierto
                        else:
                            # Si el Admin no ha completado la lista de esa fase en el panel real, queda pendiente
                            fase_jugada = any(x for x in lista_real if x and x != "-- Selecciona --")
                            estado = "❌ Fallado (0 pts)" if fase_jugada else "⏳ Pendiente"
                        
                        datos_fases_tabla.append({
                            "Instancia del Torneo": titulo_pantalla,
                            "Tu Elección": equipo,
                            "Estado del Acierto": estado
                        })

            # --- 3. MÉTRICAS CONSOLIDADAS ---
            pts_totales_general = pts_partidos + pts_bracket

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("🏆 Puntos Totales", f"{pts_totales_general} pts")
            with col_m2:
                st.metric("⚽ Puntos en Partidos", f"{pts_partidos} pts")
            with col_m3:
                st.metric("🎯 Puntos en Bracket", f"{pts_bracket} pts")

            st.write("---")

            # --- 4. RENDER DE LAS TABLAS DE RENDIMIENTO ---
            st.markdown("### 📋 Desglose de Puntos: Goles y Marcadores")
            st.dataframe(pd.DataFrame(datos_tabla), use_container_width=True, hide_index=True)

            st.write("##")

            st.markdown("### 🏹 Desglose de Puntos: Clasificados del Bracket")
            if datos_fases_tabla:
                st.dataframe(pd.DataFrame(datos_fases_tabla), use_container_width=True, hide_index=True)
            else:
                st.info("Aún no tienes predicciones registradas en las fases finales o no se han procesado clasificados.")
        
        with tab3:
            st.subheader("👀 ¿Qué apostaron los demás?")
            st.markdown("Compara tus predicciones con las de todo el grupo.")
            
            # 1. Preparamos la lista de jugadores a mostrar (excluyendo al Admin si quieres)
            jugadores_chisme = [j for j in JUGADORES_PERMITIDOS if j != "Admin"]
            
            # 2. Construimos los datos de la matriz
            datos_chismosear = []
            
            for partido in partidos:
                id_p = partido['id']
                
                # Iniciamos la fila con la información básica del partido
                fila_partido = {
                    "Partido": f"{partido['local']} vs {partido['visitante']}",
                    "Fase": partido['fase']
                }
                
                # Agregamos la apuesta de cada jugador para este partido específico
                for jugador in jugadores_chisme:
                    # Buscamos la predicción del jugador seguro con .get()
                    pred = st.session_state.base_predicciones[jugador]["partidos"].get(id_p, None)
                    
                    if pred is not None:
                        fila_partido[jugador] = f"{pred['goles_l']}-{pred['goles_v']}"
                    else:
                        fila_partido[jugador] = "---" # Por si no ha apostado aún
                        
                datos_chismosear.append(fila_partido)
                
            # 3. Convertimos a DataFrame de Pandas
            df_chisme = pd.DataFrame(datos_chismosear)
            
            # 4. Filtro amigable por si quieren ver solo una fase (Etapa 1, Octavos, etc.)
            fases_disponibles = ["Todos"] + list(df_chisme["Fase"].unique())
            fase_seleccionada = st.selectbox("Filtrar por Fase o Etapa:", fases_disponibles, key="filtro_chisme")
            
            if fase_seleccionada != "Todos":
                df_filtrado = df_chisme[df_chisme["Fase"] == fase_seleccionada]
            else:
                df_filtrado = df_chisme.copy()
                
            # Quitamos la columna interna "Fase" antes de mostrar la tabla para que quede más limpia
            df_mostrar = df_filtrado.drop(columns=["Fase"])
            
            # 5. Renderizamos la tabla en Streamlit
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

else:
    st.write("---")
    st.header("⚙️ Panel de Control del Administrador")

    # 1. CANDADO DE SEGURIDAD
    pass_admin = st.text_input("🔑 Introduce la contraseña de Administrador:", type="password", key="pass_admin_global")

    if pass_admin == "admin2026":
        st.success("🔓 Acceso concedido al panel oficial.")
        
        # =========================================================================
        # PARTEDE ADMINISTRADOR 1: MARCADORES REALES DE LOS 72 PARTIDOS
        # =========================================================================
        st.subheader("⚽ Registro de Marcadores Reales (Fase de Grupos y Más)")
        st.info("Introduce los goles reales de cada partido a medida que vayan jugando. Esto calculará los puntos de los marcadores.")

        nombres_pestanas_admin = [
            "Etapa 1", "Etapa 2", "Etapa 3", 
            "Octavos de Final", "Cuartos de Final", "Semifinal y Finales"
        ]
        
        sub_tabs_admin = st.tabs(nombres_pestanas_admin)
        
        # Segmentación de partidos para el Admin (Espejo de la interfaz del jugador)
        partidos_octavos = [p for p in partidos if p["pestana"] == "Octavos de Final"]
        partidos_cuartos = [p for p in partidos if p["pestana"] == "Cuartos de Final"]
        partidos_semis_final = [p for p in partidos if p["pestana"] == "Semifinal y Finales"]
        partidos_grupos = [p for p in partidos if p["pestana"] not in ["Octavos de Final", "Cuartos de Final", "Semifinal y Finales"]]

        etapa_data_admin = {
            "Etapa 1": partidos_grupos[:27],
            "Etapa 2": partidos_grupos[27:52],
            "Etapa 3": partidos_grupos[52:72],
            "Octavos de Final": partidos_octavos,
            "Cuartos de Final": partidos_cuartos,
            "Semifinal y Finales": partidos_semis_final
        }

        # Render de los 72 partidos + partidos de eliminación directa para el Admin
        for t_idx, nombre_p in enumerate(nombres_pestanas_admin):
            with sub_tabs_admin[t_idx]:
                partidos_fase = etapa_data_admin.get(nombre_p, [])
                
                if not partidos_fase:
                    st.info(f"No hay partidos cargados en {nombre_p} aún.")
                    continue
                    
                for partido in partidos_fase:
                    # Recuperamos el resultado real actual del st.session_state
                    real_actual = st.session_state.resultados_reales.get(partido["id"], {"goles_l": 0, "goles_v": 0, "jugado": False})
                    
                    st.markdown(f"**{partido['local']} vs {partido['visitante']}** (`ID: {partido['id']}` - *{partido['fase']}*)")
                    
                    # Checkbox para indicar si el partido ya se jugó o no
                    fue_jugado = st.checkbox("¿Partido Jugado/Finalizado?", value=real_actual.get("jugado", False), key=f"adm_chk_{partido['id']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        gl_real = st.number_input(
                            f"Goles Reales {partido['local']}", min_value=0, max_value=10,
                            value=real_actual.get("goles_l", 0),
                            key=f"adm_l_{partido['id']}"
                        )
                    with col2:
                        gv_real = st.number_input(
                            f"Goles Reales {partido['visitante']}", min_value=0, max_value=10,
                            value=real_actual.get("goles_v", 0),
                            key=f"adm_v_{partido['id']}"
                        )
                    
                    # Guardamos la información en el estado del Admin
                    st.session_state.resultados_reales[partido['id']] = {
                        "goles_l": gl_real,
                        "goles_v": gv_real,
                        "jugado": fue_jugado
                    }
                    st.divider()

        # =========================================================================
        # PARTEDE ADMINISTRADOR 2: RESULTADOS REALES DE EQUIPOS (BRACKET)
        # =========================================================================
        st.write("##")
        st.subheader("🏆 Configuración de Clasificados Reales (Bracket)")
        st.caption("Selecciona los equipos oficiales que avanzan en cada etapa del torneo.")

        todos_los_equipos = ["-- Selecciona --"] + sorted([eq for sublist in EQUIPOS_POR_GRUPO.values() for eq in sublist])

        # --- 1. OCTAVOS DE FINAL REALES (W1 hasta W16) ---
        st.markdown("### ⚽ Equipos Reales en Octavos de Final")
        config_octavos_admin = [{"label": f"Ganador Llave {i} (W{i}) Real", "index": i-1} for i in range(1, 17)]

        # Asegurar tamaño de Octavos
        lista_octavos_real = st.session_state.fases_finales_reales.get("octavos", [])
        while len(lista_octavos_real) < 16:
            lista_octavos_real.append("")
        st.session_state.fases_finales_reales["octavos"] = lista_octavos_real

        col_admin_oct1, col_admin_oct2 = st.columns(2)
        for idx, casilla in enumerate(config_octavos_admin):
            col_actual = col_admin_oct1 if idx % 2 == 0 else col_admin_oct2
            with col_actual:
                val_real_oct = st.session_state.fases_finales_reales["octavos"][casilla["index"]]
                def_idx_ro = todos_los_equipos.index(val_real_oct) if val_real_oct in todos_los_equipos else 0
                
                nuevo_real_oct = st.selectbox(
                    f"{casilla['label']}:",
                    options=todos_los_equipos,
                    index=def_idx_ro,
                    key=f"adm_oct_{casilla['index']}"
                )
                if nuevo_real_oct != "-- Selecciona --":
                    st.session_state.fases_finales_reales["octavos"][casilla["index"]] = nuevo_real_oct

        # --- 2. CUARTOS, SEMIFINALES, FINALISTAS Y CAMPEÓN REALES ---
        st.markdown("### 🥈 Cuartos, Semifinales, Finales y Campeón Reales")
        col_admin_f1, col_admin_f2 = st.columns(2)

        # =========================================================================
        # COLUMNA IZQUIERDA: CUARTOS DE FINAL (8 EQUIPOS)
        # =========================================================================
        with col_admin_f1:
            st.write("**Cuartos de Final Reales:**")
            
            lista_cuartos_real = st.session_state.fases_finales_reales.get("cuartos", [])
            while len(lista_cuartos_real) < 8:
                lista_cuartos_real.append("")
            st.session_state.fases_finales_reales["cuartos"] = lista_cuartos_real
            
            for i in range(8):
                val_real_cua = lista_cuartos_real[i]
                def_idx_rc = todos_los_equipos.index(val_real_cua) if val_real_cua in todos_los_equipos else 0
                
                # Key único con prefijo para el Admin
                nuevo_real_cua = st.selectbox(
                    f"Clasificado Real Cuartos {i+1}:", 
                    todos_los_equipos, 
                    index=def_idx_rc, 
                    key=f"admin_bracket_cuartos_{i}"
                )
                if nuevo_real_cua != "-- Selecciona --":
                    st.session_state.fases_finales_reales["cuartos"][i] = nuevo_real_cua

        # =========================================================================
        # COLUMNA DERECHA: SEMIS (4), FINAL (2) Y CAMPEÓN (1)
        # =========================================================================
        with col_admin_f2:
            st.write("**Semifinales, Finalistas y Campeón Reales:**")
            
            # --- SEMIFINALISTAS (4 EQUIPOS) ---
            lista_semis_real = st.session_state.fases_finales_reales.get("semi", [])
            while len(lista_semis_real) < 4:
                lista_semis_real.append("")
            st.session_state.fases_finales_reales["semi"] = lista_semis_real
            
            for i in range(4):
                val_real_semi = lista_semis_real[i]
                def_idx_rs = todos_los_equipos.index(val_real_semi) if val_real_semi in todos_los_equipos else 0
                
                nuevo_real_semi = st.selectbox(
                    f"Semifinalista Real {i+1}:", 
                    todos_los_equipos, 
                    index=def_idx_rs, 
                    key=f"admin_bracket_semi_{i}"
                )
                if nuevo_real_semi != "-- Selecciona --":
                    st.session_state.fases_finales_reales["semi"][i] = nuevo_real_semi
                    
            st.write("---")
            
            # --- FINALISTAS (2 EQUIPOS) ---
            st.write("**Gran Final Reales:**")
            lista_final_real = st.session_state.fases_finales_reales.get("final", [])
            while len(lista_final_real) < 2:
                lista_final_real.append("")
            st.session_state.fases_finales_reales["final"] = lista_final_real
            
            for i in range(2):
                val_real_final = lista_final_real[i]
                def_idx_rf = todos_los_equipos.index(val_real_final) if val_real_final in todos_los_equipos else 0
                
                nuevo_real_final = st.selectbox(
                    f"Finalista Real {i+1} (Avanza a la Final):", 
                    todos_los_equipos, 
                    index=def_idx_rf, 
                    key=f"admin_bracket_final_{i}"
                )
                if nuevo_real_final != "-- Selecciona --":
                    st.session_state.fases_finales_reales["final"][i] = nuevo_real_final

            st.write("---")

            # --- CAMPEÓN (1 EQUIPO) ---
            lista_campeon_real = st.session_state.fases_finales_reales.get("campeon", [])
            while len(lista_campeon_real) < 1:
                lista_campeon_real.append("")
            st.session_state.fases_finales_reales["campeon"] = lista_campeon_real
            
            val_real_camp = lista_campeon_real[0]
            def_idx_rcamp = todos_los_equipos.index(val_real_camp) if val_real_camp in todos_los_equipos else 0
            
            nuevo_real_camp = st.selectbox(
                "🏆 CAMPEÓN REAL DEL MUNDIAL:", 
                todos_los_equipos, 
                index=def_idx_rcamp, 
                key="admin_bracket_campeon"
            )
            if nuevo_real_camp != "-- Selecciona --":
                st.session_state.fases_finales_reales["campeon"][0] = nuevo_real_camp

        # --- 3. BOTÓN DE ENVÍO FINAL ---
                        # --- 3. BOTÓN DE ENVÍO FINAL ---
                st.write("---")
                if st.button("💾 Finalizar y Publicar Resultados Oficiales", use_container_width=True):
                    with st.spinner("Sincronizando los marcadores y clasificados con Google Sheets... 🚀"):
                        if enviar_datos_a_sheets(es_admin=True):
                            
                            # ⏱️ LE DAMOS 1 SEGUNDO A GOOGLE PARA QUE TERMINE DE ESCRIBIR EN SU BASE DE DATOS
                            time.sleep(1)
                            
                            # 🔄 Ahora sí, descargamos los datos frescos sin que se rompa el JSON
                            cargar_datos_desde_sheets()
                            
                            st.success("🏆 ¡Resultados oficiales publicados con éxito!")
                            st.rerun()
                        else:
                            st.error("Error de conexión al guardar los datos del Administrador.")
                    
                    # 🎉 2. Mostramos el mensaje con la vibra competitiva y el dinero del pozo
                    st.success("¡Perfecto! Todo el sistema se ha actualizado con los marcadores y equipos reales. ¡Que empiece a moverse esa plata del pozo! 🏆💰")
                    st.balloons()
                    
                    # ⏰ 3. Pausa de un segundo para disfrutar los globos
                    time.sleep(1)
                    
                    # 🔄 4. Forzamos el reinicio de la interfaz para pintar los nuevos datos reales
                    st.rerun()
                else:
                    st.error("Error de conexión al guardar los datos del Administrador.")

    elif pass_admin != "":
        st.error("❌ Contraseña incorrecta.")
