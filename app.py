import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(
    page_title="Spotify Commercial, Music & Travel Insights", 
    page_icon="🎵", 
    layout="wide"
)

# Estilo visual tipo Spotify Dark Mode
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    div[data-testid="stMetricValue"] { color: #1DB954; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🎵 Spotify Analytics — Inteligencia de Mercado, Hábitos y Monetización")
st.caption("Procesado con PySpark & Docker | Nora & Fernando")

# --- FUNCIONES DE APOYO Y CLASIFICACIÓN ---
def classify_device(platform_str):
    if not isinstance(platform_str, str):
        return "Otro"
    p = platform_str.lower()
    if any(k in p for k in ["ios", "iphone", "ipad", "android"]):
        return "📱 Teléfono / Tablet"
    elif any(k in p for k in ["windows", "mac", "osx", "linux"]):
        return "💻 Computadora"
    elif any(k in p for k in ["partner", "tv", "playstation", "xbox", "chromecast", "webos", "soundbar"]):
        return "📺 Smart TV / Altavoz / Consola"
    elif "web" in p:
        return "🌐 Reproductor Web"
    else:
        return "❓ Otro Dispositivo"

def infer_spotify_plan(df):
    if 'skipped' not in df.columns:
        return "Indeterminado"
    mobile_df = df[df['device_category'] == "📱 Teléfono / Tablet"]
    if len(mobile_df) == 0:
        mobile_df = df
    skips_count = mobile_df['skipped'].sum()
    hours_count = mobile_df['minutes_played'].sum() / 60
    skips_per_hour = skips_count / (hours_count if hours_count > 0 else 1)
    
    # Inferencia de plan individual vs familiar
    if skips_per_hour > 6:
        return "⭐ Premium (Individual / Dúo / Familiar)"
    else:
        return "🎧 Probable Premium / Free Adaptativo"

def classify_artist_region(artist_name):
    """Mapeo de región e idioma según el artista."""
    if not isinstance(artist_name, str):
        return "Otro"
    a = artist_name.lower()
    
    # Artistas / Bandas de habla hispana comunes
    hispano = ["bad bunny", "feid", "rauw alejandro", "karol g", "peso pluma", "fuerza regida", 
               "luis miguel", "zoé", "caifanes", "mora", "quevedo", "rosalía", "daddy yankee", 
               "ozuna", "j balvin", "anuel", "shakira", "maluma", "natanael cano", "grupo frontera"]
    
    # Artistas de K-Pop
    kpop = ["bts", "blackpink", "stray kids", "twice", "newjeans", "seventeen"]
    
    if any(h in a for h in hispano):
        return "🇲🇽/🇪🇸 Español / Latino"
    elif any(k in a for k in kpop):
        return "🇰🇷 Coreano (K-Pop)"
    else:
        return "🇺🇸/🇬🇧 Inglés / Anglosajón / Internacional"

@st.cache_data
def load_data():
    df = pd.read_parquet("spotify_history_cleaned.parquet")
    df['played_at'] = pd.to_datetime(df['played_at'])
    df['date'] = pd.to_datetime(df['date'])
    df['day_name'] = df['played_at'].dt.day_name()
    
    if 'platform' in df.columns:
        df['device_category'] = df['platform'].apply(classify_device)
    else:
        df['device_category'] = "Desconocido"
        
    if 'artist_name' in df.columns:
        df['artist_region'] = df['artist_name'].apply(classify_artist_region)
        
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error al cargar los datos Parquet: {e}")
    st.stop()

# --- FILTRO TOGGLE DE USUARIO ---
st.sidebar.header("🎛️ Vista de Cliente")
opcion_vista = st.sidebar.radio(
    "Selecciona la perspectiva:",
    options=["Ambos Combinados", "Solo Nora", "Solo Fernando"],
    index=0
)

if opcion_vista == "Solo Nora":
    df = df_raw[df_raw["user"] == "Nora"]
elif opcion_vista == "Solo Fernando":
    df = df_raw[df_raw["user"] == "Fernando"]
else:
    df = df_raw.copy()

# --- MÉTRICAS GENERALES & PLAN ---
st.subheader("🎯 Métricas Monetizables & Perfil del Cliente")
m1, m2, m3, m4, m5 = st.columns(5)

total_horas = df['minutes_played'].sum() / 60
skip_count = df['skipped'].sum() if 'skipped' in df.columns else 0
skip_rate = (skip_count / len(df) * 100) if len(df) > 0 else 0

hora_ocupada = df.groupby("hour")["minutes_played"].sum().idxmin()
hora_pico = df.groupby("hour")["minutes_played"].sum().idxmax()
plan_estimado = infer_spotify_plan(df)

m1.metric("Tiempo Escuchado", f"{total_horas:,.1f} hrs")
m2.metric("Tasa de Salto", f"{skip_rate:.1f}%")
m3.metric("Hora Pico", f"{hora_pico}:00 hrs")
m4.metric("Hora Ocupada", f"{hora_ocupada}:00 hrs")
m5.metric("Plan Inferido", plan_estimado)

st.markdown("---")

# --- MÓDULO: ARTISTAS MÁS ESCUCHADOS & IDIOMAS/REGIÓN ---
st.subheader("🏆 Top Artistas e Idioma/Región Preferida")
st.write("Identificación del origen idiomático del catálogo y creadores principales.")

col_art1, col_art2 = st.columns([3, 2])

top_artistas_df = df.groupby("artist_name").agg(
    Minutos_Totales=("minutes_played", "sum"),
    Reproducciones=("track_name", "count")
).reset_index()

top_artistas_df["Horas"] = (top_artistas_df["Minutos_Totales"] / 60).round(1)
top_10_artistas = top_artistas_df.sort_values(by="Minutos_Totales", ascending=False).head(10)

with col_art1:
    fig_top_art = px.bar(
        top_10_artistas,
        x="Minutos_Totales",
        y="artist_name",
        orientation="h",
        labels={"Minutos_Totales": "Minutos Escuchados", "artist_name": "Artista"},
        color="Minutos_Totales",
        color_continuous_scale="Viridis"
    )
    fig_top_art.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
    st.plotly_chart(fig_top_art, use_container_width=True)

with col_art2:
    st.write("### 🌍 Idioma / Región Dominante")
    if 'artist_region' in df.columns:
        region_df = df.groupby("artist_region")["minutes_played"].sum().reset_index()
        fig_region = px.pie(
            region_df,
            values="minutes_played",
            names="artist_region",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel1
        )
        st.plotly_chart(fig_region, use_container_width=True)

st.markdown("---")

# --- MÓDULO: ÁLBUMES / DISCOS MÁS ESCUCHADOS ---
st.subheader("💿 Top 10 Álbumes / Discos Más Escuchados")
st.write("Ranking de los álbumes con mayor reproducciones y tiempo acumulado.")

if 'album_name' in df.columns:
    album_df = df.groupby(["album_name", "artist_name"]).agg(
        Minutos_Totales=("minutes_played", "sum"),
        Reproducciones=("track_name", "count")
    ).reset_index()
    
    album_df["Horas"] = (album_df["Minutos_Totales"] / 60).round(1)
    top_10_albums = album_df.sort_values(by="Minutos_Totales", ascending=False).head(10)
    
    col_alb1, col_alb2 = st.columns([3, 2])
    
    with col_alb1:
        fig_album = px.bar(
            top_10_albums,
            x="Minutos_Totales",
            y="album_name",
            orientation="h",
            labels={"Minutos_Totales": "Minutos Escuchados", "album_name": "Álbum"},
            color="Minutos_Totales",
            color_continuous_scale="Greens"
        )
        fig_album.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(fig_album, use_container_width=True)
        
    with col_alb2:
        st.dataframe(
            top_10_albums[["album_name", "artist_name", "Horas", "Reproducciones"]].rename(
                columns={"album_name": "Álbum", "artist_name": "Artista"}
            ),
            use_container_width=True,
            hide_index=True
        )

st.markdown("---")

# --- MÓDULO REINTEGRADO: TARGETING DE EVENTOS Y CONCIERTOS ---
st.subheader("🎟️ Targeting de Eventos, Conciertos y Boletos")
st.write("Artistas candidatas a notificaciones push de boletaje (Live Nation / Ticketmaster) por fanatismo.")

eventos_df = top_artistas_df.sort_values(by="Reproducciones", ascending=False).head(5).copy()
eventos_df["Potencial de Venta de Boletos"] = ["🔥 Muy Alto", "🔥 Muy Alto", "⚡ Alto", "⚡ Alto", "👍 Medio"]

col_ev1, col_ev2 = st.columns(2)

with col_ev1:
    st.write("### 🎤 Top 5 Artistas Objetivo para Venta de Entradas")
    st.dataframe(
        eventos_df[["artist_name", "Reproducciones", "Horas", "Potencial de Venta de Boletos"]].rename(
            columns={"artist_name": "Artista"}
        ),
        use_container_width=True,
        hide_index=True
    )

with col_ev2:
    fig_events = px.pie(
        eventos_df,
        values="Minutos_Totales",
        names="artist_name",
        title="Share de Escucha en Artistas Relevantes para Conciertos",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    st.plotly_chart(fig_events, use_container_width=True)

st.markdown("---")

# --- MÓDULO: VIAJES INTERNACIONALES Y PAÍSES ---
st.subheader("✈️ Registro de Escucha Internacional (Viajes)")
if 'country' in df.columns:
    country_summary = df.groupby("country").agg(
        Minutos_Totales=("minutes_played", "sum"),
        Primer_Registro=("date", "min"),
        Ultimo_Registro=("date", "max"),
        Reproducciones=("track_name", "count")
    ).reset_index()
    
    country_summary["Horas_Totales"] = (country_summary["Minutos_Totales"] / 60).round(1)
    country_summary["Fecha_Inicio"] = country_summary["Primer_Registro"].dt.strftime('%Y-%m-%d')
    country_summary["Fecha_Fin"] = country_summary["Ultimo_Registro"].dt.strftime('%Y-%m-%d')
    country_summary = country_summary.sort_values(by="Minutos_Totales", ascending=False)
    
    col_geo1, col_geo2 = st.columns([1, 1])
    
    with col_geo1:
        fig_country = px.pie(
            country_summary,
            values="Horas_Totales",
            names="country",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        st.plotly_chart(fig_country, use_container_width=True)
        
    with col_geo2:
        st.dataframe(
            country_summary[["country", "Horas_Totales", "Fecha_Inicio", "Fecha_Fin", "Reproducciones"]].rename(
                columns={"country": "País (ISO)", "Horas_Totales": "Horas", "Fecha_Inicio": "Desde", "Fecha_Fin": "Hasta"}
            ),
            use_container_width=True,
            hide_index=True
        )

st.markdown("---")

# --- MÓDULO SOCIAL: COMPATIBILIDAD ENTRE NORA Y FERNANDO ---
if opcion_vista == "Ambos Combinados":
    st.subheader("🤝 Análisis de Conexión & Compatibilidad Musical (Social Insights)")
    nora_artists = set(df_raw[df_raw["user"] == "Nora"]["artist_name"].dropna().unique())
    fer_artists = set(df_raw[df_raw["user"] == "Fernando"]["artist_name"].dropna().unique())
    
    artistas_comunes = list(nora_artists.intersection(fer_artists))
    union_artistas = nora_artists.union(fer_artists)
    
    jaccard_score = (len(artistas_comunes) / len(union_artistas) * 100) if len(union_artistas) > 0 else 0
    
    s1, s2, s3 = st.columns(3)
    s1.metric("Artistas Exclusivos Nora", f"{len(nora_artists - fer_artists):,}")
    s2.metric("Artistas Compartidos", f"{len(artistas_comunes):,}")
    s3.metric("Índice de Compatibilidad Musical", f"{jaccard_score:.1f}%")
    
    if artistas_comunes:
        st.info("**Top Artistas Compartidos:** " + ", ".join(artistas_comunes[:15]) + "...")
        
    st.markdown("---")

# --- DISPOSITIVOS Y PATRONES ---
col_dev, col_hour = st.columns(2)

with col_dev:
    st.subheader("📱 Clasificación de Dispositivos")
    cat_df = df.groupby("device_category")["minutes_played"].sum().reset_index()
    fig_cat = px.pie(
        cat_df,
        values="minutes_played",
        names="device_category",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with col_hour:
    st.subheader("🕵️‍♂️ Curva de Actividad Diaria")
    hour_df = df.groupby("hour")["minutes_played"].sum().reset_index()
    fig_hour = px.area(
        hour_df,
        x="hour",
        y="minutes_played",
        labels={"hour": "Hora del Día", "minutes_played": "Minutos Escuchados"},
        color_discrete_sequence=["#1DB954"]
    )
    st.plotly_chart(fig_hour, use_container_width=True)