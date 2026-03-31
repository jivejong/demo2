import streamlit as st
from google import genai
from gtts import gTTS
import json
import io
import re
import os
from PIL import Image

# --- 1. CONFIG & CLIENT SETUP ---
st.set_page_config(page_title="Agentic Poet v4", page_icon="📸", layout="wide")

# Secure API Key Check
if "GENAI_API_KEY" in st.secrets:
    api_key = st.secrets["GENAI_API_KEY"]
elif "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Missing API Key in Streamlit Secrets! Go to Settings > Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 2. INITIALIZE SESSION STATE ---
if "camera_key" not in st.session_state:
    st.session_state.camera_key = 0
if "final_output" not in st.session_state:
    st.session_state.final_output = None

# --- 3. UTILITY FUNCTIONS ---

def clean_json(text):
    """Red Team Guard: Extracts JSON content from potential Markdown backticks."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text.strip()

def get_mood_music(mood):
    """Maestro Agent: Loads an MP3 based on the detected mood."""
    mood_str = str(mood).upper()
    path = f"audio_library/{mood_str.lower()}.mp3"
    
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None

def run_agentic_pipeline(image_file):
    """Orchestrates the Visionary, Bard, Narrator, and Maestro agents."""
    with st.status("🤖 Running Multi-Agent Workflow...", expanded=True) as status:
        st.write("🔍 **Visionary**: Scanning pixels...")
        st.write("✍️ **Bard**: Crafting stanzas...")
        
        raw_img = Image.open(image_file)
        
        prompt = """
        Analyze this image and return ONLY a raw JSON object:
        {
          "description": "A literal 2-sentence summary of the image.",
          "entities": ["list", "of", "detected", "objects"],
          "poem": "A 4-line rhythmic poem inspired by the image.",
          "mood": "MELANCHOLY | WHIMSICAL | EPIC | EERIE"
        }
        """

        import time

        # ... inside run_agentic_pipeline ...
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, raw_img]
            )
            data = json.loads(clean_json(response.text))
        except Exception as e:
            if "429" in str(e):
                st.error("🚦 Rate Limit Hit: Google is busy. Please wait 30 seconds and try again.")
            else:
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

# --- 4. STREAMLIT INTERFACE ---

st.title("📸 The Agentic Poet")
st.caption("A Multimodal AI Performance: Vision, Poetry, and Sound")
st.markdown("---")

# Use a dynamic key to force the camera to reset on 'Start Over'
camera_img = st.camera_input("Take a photo to begin", key=f"cam_{st.session_state.camera_key}")

# Logic: Process ONLY if there is a new image and we haven't produced output yet
if camera_img and st.session_state.final_output is None:
    results = run_agentic_pipeline(camera_img)
    if results:
        st.session_state.final_output = results
        st.rerun()

# Display Results UI
if st.session_state.final_output:
    data, voice_bytes, music_bytes = st.session_state.final_output
    
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("👁️ Visionary Report", expanded=True):
            st.write(data['description'])
            st.caption(f"Visual Anchors: {', '.join(data['entities'])}")
    
    with col2:
        with st.expander("✍️ Bard's Verified Poem", expanded=True):
            st.info(data['poem'])

    st.divider()
    st.subheader(f"🎭 The Performance (Mood: {data['mood']})")
    
    if music_bytes:
        # Audio playback controls
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Narrator**")
            st.audio(voice_bytes, format="audio/mp3")
        with c2:
            st.write("**Maestro**")
            st.audio(music_bytes, format="audio/mp3")
        
        # Combined Sync Button
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
                """,
                height=0
            )
            st.balloons()
    else:
        st.warning("⚠️ Maestro could not find music files in /audio_library/. Playing voice only.")
        st.audio(voice_bytes, format="audio/mp3")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- RESET BUTTON (Clears buffer and camera) ---
    if st.button("🔄 START OVER", type="primary", use_container_width=True):
        st.session_state.final_output = None
        st.session_state.camera_key += 1 # Increments key to kill camera buffer
        st.rerun()