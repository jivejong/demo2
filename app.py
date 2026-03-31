import streamlit as st
from google import genai
from gtts import gTTS
import json
import io
import re
import os
from PIL import Image

# --- 1. CONFIG & CLIENT SETUP ---
st.set_page_config(page_title="Agentic Poet v3", page_icon="📸", layout="wide")

# Secure API Key Check
if "GENAI_API_KEY" in st.secrets:
    api_key = st.secrets["GENAI_API_KEY"]
elif "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Missing API Key in Streamlit Secrets!")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 2. UTILITIES ---

def clean_json(text):
    """Extracts JSON content from Markdown backticks."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text.strip()

def get_mood_music(mood):
    """Maestro Agent: Loads an MP3 based on the detected mood."""
    mood = mood.upper()
    # Normalize to folder structure
    path = f"audio_library/{mood.lower()}.mp3"
    
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    else:
        # Diagnostic fallback: if file is missing, return None
        return None

# --- 3. THE AGENTIC PIPELINE ---

def run_agentic_pipeline(image_file):
    with st.status("🤖 Initializing Multi-Agent Workflow...", expanded=True) as status:
        
        st.write("🔍 **Visionary**: Scanning pixels...")
        st.write("✍️ **Bard**: Crafting stanzas...")
        
        raw_img = Image.open(image_file)
        
        prompt = """
        Analyze this image and return ONLY a raw JSON object:
        {
          "description": "2-sentence summary.",
          "entities": ["list", "of", "objects"],
          "poem": "A 4-line rhythmic poem.",
          "mood": "MELANCHOLY | WHIMSICAL | EPIC | EERIE"
        }
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, raw_img]
            )
            data = json.loads(clean_json(response.text))
        except Exception as e:
            st.error(f"Inference Failed: {e}")
            return None

        # --- NARRATOR (TTS) ---
        st.write("🎙️ **Narrator**: Recording recitation...")
        tts = gTTS(text=data['poem'], lang='en')
        voice_io = io.BytesIO()
        tts.write_to_fp(voice_io)
        
        # --- MAESTRO (Music Selection) ---
        st.write("🎹 **Maestro**: Selecting atmospheric score...")
        music_bytes = get_mood_music(data['mood'])
        
        status.update(label="Creative Cycle Complete!", state="complete", expanded=False)
        return data, voice_io.getvalue(), music_bytes

# --- 4. INTERFACE ---

st.title("📸 The Agentic Poet")
st.caption("Capture a photo. Let the agents perform.")

camera_img = st.camera_input("Take a photo")

if camera_img:
    if "final_output" not in st.session_state:
        results = run_agentic_pipeline(camera_img)
        if results:
            st.session_state.final_output = results

    if "final_output" in st.session_state:
        data, voice_bytes, music_bytes = st.session_state.final_output
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("👁️ Visionary Report")
            st.write(data['description'])
            st.caption(f"Tags: {', '.join(data['entities'])}")
        
        with col2:
            st.subheader("✍️ The Poem")
            st.info(data['poem'])

        st.divider()
        st.subheader(f"🎭 The Performance (Mood: {data['mood']})")
        
        # The Secret Sync Mechanism
        if music_bytes:
            # Hidden players
            st.write("Adjust mix:")
            c1, c2 = st.columns(2)
            with c1: st.audio(voice_bytes, format="audio/mp3")
            with c2: st.audio(music_bytes, format="audio/mp3")
            
            # The Sync Button
            if st.button("▶️ PLAY COMBINED PERFORMANCE", use_container_width=True):
                st.components.v1.html(
                    """
                    <script>
                        var audios = window.parent.document.querySelectorAll('audio');
                        audios.forEach(audio => {
                            audio.currentTime = 0;
                            audio.play();
                        });
                    </script>
                    """, height=0
                )
                st.balloons()
        else:
            st.warning("⚠️ Maestro could not find the music files in /audio_library/")
            st.audio(voice_bytes)

        if st.button("Reset"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()