# app.py
import streamlit as st
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer
import requests
import tempfile
import os

# — Votre clé Deepgram (remplacez par une clé valide)
DEEPGRAM_API_KEY = "67fc6fe4cd313d0407dccee289ce7441fbcf5372"

# — Configuration de la page
st.set_page_config(page_title="Assistant Vocal", page_icon="🎤")

# — États de session
st.session_state.setdefault('transcribed_text', "")
st.session_state.setdefault('is_paused', False)

# — Titre
st.title("🎤 Application de reconnaissance vocale améliorée")

# — 1️⃣ Sélection de la langue
lang_choice = st.selectbox(
    "1️⃣ Choisissez la langue :",
    ["fr", "en", "es", "de", "it", "pt"],
    format_func=lambda x: {
        "fr": "Français", "en": "Anglais", "es": "Espagnol",
        "de": "Allemand", "it": "Italien", "pt": "Portugais"
    }[x]
)

# — 2️⃣ Sélection de l'API
api_choice = st.selectbox(
    "2️⃣ API de reconnaissance :",
    ["Google", "Sphinx", "Deepgram"]
)

# — 3️⃣ Durée
duration = st.slider("3️⃣ Durée d'enregistrement (s)", 5, 30, 10, step=5)

def save_temp_wav(audio):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(audio.get_wav_data())
    tmp.close()
    return tmp.name

def transcribe_with_deepgram(audio):
    wav_path = save_temp_wav(audio)
    try:
        with open(wav_path, "rb") as f:
            resp = requests.post(
                f"https://api.deepgram.com/v1/listen?language={lang_choice}&punctuate=true",
                headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": "audio/wav"
                },
                data=f
            )
        os.remove(wav_path)
        resp.raise_for_status()
        return resp.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    except requests.exceptions.HTTPError:
        return f"❌ Deepgram HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"❌ Erreur Deepgram : {e}"

def transcribe_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Enregistrement en cours… Parlez maintenant.")
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = r.listen(source, timeout=duration)
            if api_choice == "Google":
                return r.recognize_google(audio, language=f"{lang_choice}-{lang_choice.upper()}")
            if api_choice == "Sphinx":
                return r.recognize_sphinx(audio, language=f"{lang_choice}-{lang_choice.upper()}")
            if api_choice == "Deepgram":
                return transcribe_with_deepgram(audio)
        except sr.UnknownValueError:
            return "❌ Impossible de comprendre l'audio."
        except sr.RequestError as e:
            return f"❌ Erreur API : {e}"
        except Exception as e:
            return f"❌ Erreur inattendue : {e}"

# — Callbacks
def start_recording():
    st.session_state.is_paused = False
    st.session_state.transcribed_text = transcribe_speech()

def pause_recording():
    st.session_state.is_paused = True

def resume_recording():
    if st.session_state.is_paused:
        st.session_state.is_paused = False
        st.session_state.transcribed_text = transcribe_speech()

# — Boutons
col1, col2, col3 = st.columns(3)
col1.button("🎤 Démarrer", on_click=start_recording)
col2.button("⏸️ Mettre en pause", on_click=pause_recording)
col3.button("▶️ Reprendre", on_click=resume_recording)

# — Affichage
st.subheader("📝 Transcription")
st.text_area("Texte transcrit :", value=st.session_state.transcribed_text, height=150)

if st.button("💾 Enregistrer la transcription"):
    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(st.session_state.transcribed_text)
    st.success("💾 Transcription enregistrée sous 'transcription.txt'.")

# — Conseils
st.info("""
💡 Conseils :
- Parlez clairement à 15–20 cm du micro  
- Évitez le bruit de fond  
- Attendez le message « Enregistrement en cours… » avant de parler  
""")
