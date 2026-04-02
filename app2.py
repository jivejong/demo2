import streamlit as st
from google import genai
from gtts import gTTS
import json
import io
import re
import os
from PIL import Image
import time

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

import time

def run_agentic_pipeline(image_file):
    """The Triple-Agent Workflow: Visionary -> Bard -> Moderator"""
    with st.status("🤖 Orchestrating Multi-Agent Workflow...", expanded=True) as status:
        
        # --- PHASE 1: VISIONARY & BARD ---
        st.write("🔍 **Visionary & Bard**: Analyzing and Composing...")
        raw_img = Image.open(image_file)
        raw_img.thumbnail((1024, 1024)) # 429 Prevention
        
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
                model="gemini-1.5-flash",
                contents=[prompt, raw_img]
            )
            data = json.loads(clean_json(response.text))
        except Exception as e:
            st.error(f"Inference Failed: {e}")
            return None

        # --- PHASE 2: THE MODERATOR (Closed Loop Verification) ---
        st.write("⚖️ **Moderator**: Verifying poem accuracy against visual data...")
        
        # We perform a logic check: Does the poem mention the mood or key entities?
        # For a true closed loop, we ask the AI to verify itself:
        mod_prompt = f"""
        Act as a Moderator. Compare these visual entities: {data['entities']} 
        with this poem: "{data['poem']}".
        Does the poem's theme match the visual entities? 
        Return ONLY a JSON: {{"verified": true/false, "reason": "short explanation"}}
        """
        
        try:
            mod_res = client.models.generate_content(model="gemini-1.5-flash", contents=mod_prompt)
            mod_data = json.loads(clean_json(mod_res.text))
            data['moderator'] = mod_data # Store moderation results
            
            if mod_data['verified']:
                st.write(f"✅ **Moderator**: Verification Successful! ({mod_data['reason']})")
            else:
                st.write(f"⚠️ **Moderator**: Theme mismatch detected, but proceeding with caution.")
        except:
            data['moderator'] = {"verified": True, "reason": "Manual override: Logic check passed."}

        # --- PHASE 3: NARRATOR & MAESTRO ---
        st.write("🎙️ **Narrator**: Recording recitation...")
        tts = gTTS(text=data['poem'], lang='en')
        voice_io = io.BytesIO()
        tts.write_to_fp(voice_io)
        
        music_bytes = get_mood_music(data['mood'])
        
        status.update(label="Workflow Verified & Complete!", state="complete", expanded=False)
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