#######################
# Agente Económico    #
# App de Streamlit    #
# con Supabase        #
#######################

import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client

from agente_core import process_response

# Cargar variables de entorno (para correr en local con .env)
load_dotenv()

MEMORY_MAX_MESSAGES = 10


def get_secret(name):
    # Primero busca en st.secrets (Streamlit Cloud), si no, en .env / variables de entorno
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name)


st.set_page_config(page_title="Economiko", page_icon="🐒")
st.title("💱 Agente Económico")
st.caption("Tipo de cambio, conversión de monedas, indicadores del Banco Mundial y clima.")

groq_key = get_secret("GROQ_API_KEY")
sb_url = get_secret("SUPABASE_URL")
sb_key = get_secret("SUPABASE_KEY")

if not (groq_key and sb_url and sb_key):
    st.error("Faltan claves: revisa GROQ_API_KEY, SUPABASE_URL y SUPABASE_KEY en tu .env o en los secrets.")
    st.stop()

groq_client = Groq(api_key=groq_key)


@st.cache_resource
def get_supabase():
    # Sin login, el cliente puede compartirse entre sesiones
    return create_client(sb_url, sb_key)


sb = get_supabase()

# Conversación en pantalla (cada visita empieza vacía)
if "messages" not in st.session_state:
    st.session_state.messages = []


def consultas_recientes(n=10):
    try:
        res = (
            sb.table("mensajes")
            .select("content")
            .eq("role", "user")
            .order("id", desc=True)
            .limit(n)
            .execute()
        )
        return [r["content"] for r in (res.data or [])]
    except Exception:
        return None


# Barra lateral
with st.sidebar:
    st.header("Opciones")
    if st.button("Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()

    st.subheader("Consultas recientes")
    st.caption("Registro compartido en Supabase (de todos los visitantes).")
    recientes = consultas_recientes()
    if recientes is None:
        st.warning("No se pudo leer el registro de Supabase.")
    elif not recientes:
        st.write("Aún no hay consultas.")
    else:
        for c in recientes:
            st.write(f"• {c}")

# Mostrar la conversación
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Entrada del usuario
if user_text := st.chat_input("Escribe tu pregunta..."):
    with st.chat_message("user"):
        st.markdown(user_text)

    memory_messages = st.session_state.messages[-MEMORY_MAX_MESSAGES:]

    hubo_error = False
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                answer = process_response(groq_client, memory_messages, user_text)
            except Exception as e:
                hubo_error = True
                answer = f"Ocurrió un error: {e}"
        st.markdown(answer)

    # Los errores se muestran pero no se guardan
    if not hubo_error:
        nuevos = [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": answer},
        ]
        try:
            sb.table("mensajes").insert(nuevos).execute()
        except Exception as e:
            st.warning(f"No se pudo guardar en Supabase: {e}")
        st.session_state.messages.extend(nuevos)
