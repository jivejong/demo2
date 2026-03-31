import streamlit as st
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Agent Diagnostic", page_icon="🤖")

st.title("🤖 AI Agent: Connection Portal")

# --- STEP 1: THE DIAGNOSTIC PANEL ---
with st.expander("System Diagnostic (Click to view)", expanded=True):
    # Check st.secrets keys
    found_keys = list(st.secrets.keys())
    st.write(f"📂 **Detected Secret Keys:** `{found_keys}`")
    
    # Check OS Environment (Backup)
    env_key = os.environ.get("GENAI_API_KEY")
    st.write(f"🌐 **OS Environment Backup:** {'✅ Detected' if env_key else '❌ Not Found'}")

# --- STEP 2: KEY RETRIEVAL LOGIC ---
api_key = None

if "GENAI_API_KEY" in st.secrets:
    api_key = st.secrets["GENAI_API_KEY"]
elif env_key:
    api_key = env_key

# --- STEP 3: INITIALIZATION ---
if api_key:
    try:
        # We try the new 2026 SDK first
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # Test call to verify the key isn't revoked
        client.models.get(model="gemini-1.5-flash")
        
        st.success("✅ API Key Connected & Verified!")
        
        # --- YOUR AGENT INTERFACE ---
        user_input = st.chat_input("Ask your agent something...")
        if user_input:
            with st.chat_message("user"):
                st.write(user_input)
            
            with st.chat_message("assistant"):
                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=user_input
                )
                st.write(response.text)

    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.info("Check if your API Key is restricted in Google AI Studio.")
else:
    st.error("🔒 Critical Error: 'GENAI_API_KEY' is missing.")
    st.markdown("""
    ### How to fix this right now:
    1. Go to your **Streamlit Cloud Dashboard**.
    2. Click **Settings** -> **Secrets**.
    3. Paste the following EXACTLY (including quotes):
    ```toml
    GENAI_API_KEY = "AIzaSy..." 
    ```
    4. Click **Save** and **Reboot App** from the 'Manage App' menu.
    """)