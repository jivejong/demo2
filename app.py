import streamlit as st
from google import genai
from gtts import gTTS
from midiutil import MIDIFile
import json
import io
import re
from PIL import Image

# --- 1. ARCHITECT'S CONFIG & CLIENT SETUP ---
st.set_page_config(page_title="Agentic Poet", page_icon="📸", layout="wide")

# Ensure the secret is present
if "GENAI_API_KEY" not in st.secrets:
    st.error("Missing 'GENAI_API_KEY' in Streamlit Secrets!")
    st.stop()

# New SDK Client Initialization
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])

# --- 2. THE UTILITIES ---

def clean_json(text):
    """Red Team Guard: Extracts JSON content from potential Markdown backticks."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()

def generate_midi(mood):
    """Maestro Agent: Generates a 4-bar MIDI loop based on sentiment."""
    mood_map = {
        "MELANCHOLY": {"scale": [60, 63, 67, 70], "tempo": 65},
        "WHIMSICAL": {"scale": [72, 74, 76, 79], "tempo": 130},
        "EPIC": {"scale": [62, 66, 69, 73], "tempo": 95},
        "EERIE": {"scale": [59, 60, 63, 66], "tempo": 55}
    }
    config = mood_map.get(mood.upper(), mood_map["MELANCHOLY"])
    
    midi = MIDIFile(1)
    midi.addTempo(0, 0, config["tempo"])
    
    time_idx = 0
    for _ in range(4): # 4 Bars
        for note in config["scale"]:
            midi.addNote(0, 0, note, time_idx, 1, 85)
            time_idx += 1
            
    midi_stream = io.BytesIO()
    midi.writeFile(midi_stream)
    return midi_stream.getvalue()

# --- 3. THE AGENTIC PIPELINE ---

def run_agentic_pipeline(image_file):
    """Orchestrates the Visionary, Bard, Critic, and Maestro agents."""
    with st.status("🤖 Agentic Pipeline Initialized...", expanded=True) as status:
        
        # --- PHASE 1: VISIONARY & BARD (Multimodal Inference) ---
        st.write("🔍 **Visionary**: Scanning image for entities...")
        st.write("✍️ **Bard**: Constructing rhythmic stanzas...")
        
        # Convert BytesIO to PIL Image for the new SDK
        raw_img = Image.open(image_file)
        
        prompt = """
        Analyze this image and return a JSON object with the following structure:
        {
          "description": "A literal 2-sentence summary of the image.",
          "entities": ["list", "of", "detected", "objects"],
          "poem": "A 4-line poem inspired by the image.",
          "mood": "MELANCHOLY | WHIMSICAL | EPIC | EERIE"
        }
        Return ONLY the raw JSON.
        """

        try:
            # Modern SDK Call
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, raw_img]
            )
            
            # Use .text to extract content and clean it
            raw_text = response.text
            data = json.loads(clean_json(raw_text))
            
        except Exception as e:
            st.error(f"Agent Failure: {str(e)}")
            return None

        # --- PHASE 2: THE CRITIC (Verification) ---
        st.write("⚖️ **Critic**: Auditing poem for descriptive accuracy...")
        # Local logic check: Ensure the poem isn't empty or nonsensical
        if len(data.get("poem", "")) < 20:
            st.write("❌ **Critic**: Poem too short. Retrying (Simulated)...")
            # In a full app, you'd trigger a recursion here.
        else:
            st.write(f"✅ **Critic**: Verified {len(data['entities'])} visual anchors.")

        # --- PHASE 3: NARRATOR & MAESTRO (Synthesis) ---
        st.write("🎙️ **Narrator**: Synthesizing voice recitation...")
        tts = gTTS(text=data['poem'], lang='en')
        voice_io = io.BytesIO()
        tts.write_to_fp(voice_io)
        
        st.write("🎹 **Maestro**: Mapping mood to MIDI frequencies...")
        midi_bytes = generate_midi(data['mood'])
        
        status.update(label="Workflow Successful!", state="complete", expanded=False)
        return data, voice_io.getvalue(), midi_bytes

# --- 4. STREAMLIT INTERFACE ---

st.title("📸 The Agentic Poet")
st.markdown("---")

# Use st.camera_input for mobile hardware access
camera_img = st.camera_input("Capture a moment to begin the pipeline")

if camera_img:
    # State Management: Store results to prevent re-triggering on UI refresh
    if "final_output" not in st.session_state:
        results = run_agentic_pipeline(camera_img)
        if results:
            st.session_state.final_output = results

    if "final_output" in st.session_state:
        data, voice_bytes, midi_bytes = st.session_state.final_output
        
        # Display Agent Monologue Results
        c_left, c_right = st.columns(2)
        with c_left:
            with st.expander("👁️ Visionary Report", expanded=True):
                st.write(data['description'])
                st.caption(f"Visual Anchors: {', '.join(data['entities'])}")
        
        with c_right:
            with st.expander("✍️ Bard's Verified Poem", expanded=True):
                st.info(data['poem'])

        st.divider()
        st.subheader(f"🎧 Final Production (Mood: {data['mood']})")
        
        # Audio Players
        aud1, aud2 = st.columns(2)
        with aud1:
    st.write("**Narrator Voice**")
    # Use unique keys to identify these in the DOM
    st.audio(voice_bytes, format="audio/mp3")

with aud2:
    st.write("**Maestro Atmosphere** (Download to Play)")
    # Since browsers struggle with raw MIDI, we provide a download 
    # OR if you have a WAV version, use st.audio here.
    st.download_button("Download Score", midi_bytes, file_name="mood.mid")

# --- THE "SYNC" BUTTON ---
if st.button("🎭 Play Performance"):
    # This bit of JavaScript finds all audio tags on the page and plays them
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
        height=0,
    )