# app.py
import os
import tempfile
import requests
import streamlit as st
import speech_recognition as sr
from st_audiorec import st_audiorec

# — Récupération de la clé Deepgram depuis les variables d'environnement
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    st.error("🔑 Veuillez définir la variable d'environnement DEEPGRAM_API_KEY.")
    st.stop()

# — Configuration de la page
st.set_page_config(page_title="Assistant Vocal", page_icon="🎤")

# — États de session
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""

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

# — 3️⃣ Durée d'enregistrement
duration = st.slider("3️⃣ Durée d'enregistrement (s)", 5, 30, 10, step=5)


def save_temp_wav(wav_bytes: bytes) -> str:
    """Enregistre les octets WAV dans un fichier temporaire"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(wav_bytes)
    tmp.close()
    return tmp.name


def transcribe_with_deepgram(wav_bytes: bytes) -> str:
    """Envoie l'audio à Deepgram pour transcription"""
    wav_path = save_temp_wav(wav_bytes)
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
    except Exception as e:
        return f"❌ Deepgram erreur : {e}"


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    """Transcrit les octets WAV avec l'API choisie"""
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(wav_bytes, sample_rate=44100, sample_width=2)
    try:
        if api_choice == "Google":
            return recognizer.recognize_google(
                audio_data, language=f"{lang_choice}-{lang_choice.upper()}"
            )
        elif api_choice == "Sphinx":
            return recognizer.recognize_sphinx(
                audio_data, language=f"{lang_choice}-{lang_choice.upper()}"
            )
        else:
            return transcribe_with_deepgram(wav_bytes)
    except sr.UnknownValueError:
        return "❌ Impossible de comprendre l'audio."
    except sr.RequestError as e:
        return f"❌ Erreur API : {e}"
    except Exception as e:
        return f"❌ Erreur inattendue : {e}"

# — Enregistrement audio
st.info(f"Appuyez sur 'Enregistrer' et parlez pendant {duration} secondes...")
wav_bytes = st_audiorec()
if wav_bytes:
    st.audio(wav_bytes, format='audio/wav')
    st.session_state.transcribed_text = transcribe_wav_bytes(wav_bytes)

# — Affichage de la transcription
st.subheader("📝 Transcription")
st.text_area("Texte transcrit :", value=st.session_state.transcribed_text, height=150)

# — Sauvegarde
if st.button("💾 Enregistrer la transcription"):
    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(st.session_state.transcribed_text)
    st.success("💾 Transcription enregistrée sous 'transcription.txt'.")

# — Conseils
st.info("""
💡 Conseils :
- Parlez clairement à 15–20 cm du micro  
- Évitez le bruit de fond  
- Attendez la fin de l'enregistrement avant de parler  
""")
