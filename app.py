import streamlit as st
import os
import json
import urllib.parse
import tempfile
from google import genai
from google.genai import types
from pydantic import BaseModel
from gtts import gTTS

# Sayfa Ayarları
st.set_page_config(page_title="Prayer App", page_icon="🕊️", layout="centered")

# Custom CSS for a peaceful UI
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0A0A0A;
        background-image: radial-gradient(circle at 50% 0%, #1A1A1A 0%, #0A0A0A 100%);
    }
    
    /* Typography */
    html, body, [class*="css"], p, div, span {
        font-family: 'Georgia', serif !important;
        color: #E2DFD2;
    }
    
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 400 !important;
        text-align: center;
        font-family: 'Georgia', serif !important;
        letter-spacing: 0.5px;
    }
    
    /* Text Input Area */
    .stTextArea textarea {
        border-radius: 12px !important;
        border: 1px solid #333333 !important;
        background-color: #141414 !important;
        color: #E2DFD2 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5) !important;
        font-size: 16px !important;
        padding: 15px !important;
        line-height: 1.6 !important;
    }
    .stTextArea textarea:focus {
        border-color: #555555 !important;
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.05) !important;
    }
    /* Input placeholder color */
    ::-webkit-input-placeholder { color: #555555 !important; }
    :-ms-input-placeholder { color: #555555 !important; }
    ::placeholder { color: #555555 !important; }
    
    /* Button */
    .stButton>button {
        background-color: #2D3730 !important; /* Extremely dark sage green */
        color: #E2DFD2 !important;
        border-radius: 20px !important;
        border: 1px solid #3D4840 !important;
        padding: 10px 24px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5) !important;
        display: block !important;
        margin: 0 auto !important;
    }
    .stButton>button:hover {
        background-color: #3D4840 !important;
        border-color: #4D5950 !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.7) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Info & Success Boxes */
    div[data-testid="stAlert"] {
        background-color: #1A1A1A !important;
        color: #E2DFD2 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
        border: 1px solid #333333 !important;
        padding: 15px !important;
    }
    div[data-testid="stAlert"] p {
        color: #E2DFD2 !important;
    }
    
    /* Make the entire layout feel more breathable */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        max-width: 700px !important;
    }
    
    /* Image styling */
    img {
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
        margin-bottom: 20px !important;
    }
    
    audio {
        width: 100% !important;
        margin-top: 15px !important;
        margin-bottom: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# Dil Seçenekleri (Translations)
TRANSLATIONS = {
    "Türkçe": {
        "title": "🕊️ Dua Uygulaması",
        "description": "Bugün kalbinizden veya aklınızdan geçenleri paylaşın ve size özel, manevi olarak rahatlatıcı bir dua alın.",
        "input_label": "Neler yaşıyorsunuz?",
        "input_placeholder": "Örn. Son zamanlarda iş yüzünden çok bunaldım ve evde huzur bulmakta zorlanıyorum...",
        "button_generate": "Dua Oluştur",
        "error_api": "Lütfen GEMINI_API_KEY ortam değişkenini ayarlayın.",
        "warning_empty": "Size özel bir dua oluşturabilmem için lütfen bir şeyler paylaşın.",
        "spinner_analyze": "Duygusal ve manevi ihtiyaçlar analiz ediliyor...",
        "expander_arch": "🔍 Analiz Süreci (Arka Plan Çıkarımları)",
        "info_crafting": "Duanız kaleme alınıyor...",
        "spinner_audio": "Huzur verici bir seslendirmen hazırlanıyor...",
        "success_prayer": "Duanız",
        "error_occurred": "Bir hata oluştu:",
        "target_language": "Turkish",
        "tts_lang": "tr"
    },
    "English": {
        "title": "🕊️ Prayer App",
        "description": "Share what's on your heart or mind today, and receive a deeply personal, spiritually grounding prayer.",
        "input_label": "What are you going through?",
        "input_placeholder": "E.g., I've been feeling very overwhelmed with work lately and struggling to find peace at home...",
        "button_generate": "Generate Prayer",
        "error_api": "Please set the GEMINI_API_KEY environment variable.",
        "warning_empty": "Please share something so I can generate a personalized prayer.",
        "spinner_analyze": "Analyzing emotional and spiritual needs...",
        "expander_arch": "🔍 Analysis Process (Background Reasonings)",
        "info_crafting": "Crafting your personalized prayer...",
        "spinner_audio": "Narrating your prayer...",
        "success_prayer": "Your Prayer",
        "error_occurred": "An error occurred:",
        "target_language": "English",
        "tts_lang": "en"
    }
}

# Dil Seçimi
language = st.sidebar.selectbox("Language / Dil", options=["Türkçe", "English"], index=0)
t = TRANSLATIONS[language]

# API Anahtarı
API_KEY = os.environ.get("GEMINI_API_KEY")

# Senin yazdığın muazzam System Prompt
SYSTEM_PROMPT = """
You are a Personal Prayer Generator.
Your purpose is to create deeply meaningful, emotionally resonant, and spiritually supportive prayers tailored to the user's life situation.
You do not generate generic prayers. Instead, you carefully analyze the user's words, emotions, hopes, fears, and life context to produce a prayer that feels personal, sincere, and spiritually grounding.

Core principles:
1. Emotional Insight: Analyze the user's situation to understand both explicit desires and implicit emotional needs.
2. Hidden Intentions: Identify deeper intentions behind requests and incorporate them naturally.
3. Holistic Blessings: Always include broader blessings (inner peace, wisdom, protection, compassion, resilience, gratitude, meaningful relationships).
4. Compassionate Tone: Write in a warm, sincere, and gentle tone.
5. Spiritual Universality: Respect spiritual traditions while remaining accessible and inclusive.
6. Depth and Reflection: Feel thoughtful and reflective, specific to that person.

Prayer structure guidelines:
• gratitude  
• acknowledgement of human struggles  
• guidance and wisdom  
• strength in difficult times  
• blessings for loved ones  
• protection from harm  
• hope for the future  
• purpose and meaning in life  

Writing style:
- emotionally sincere
- calm and reflective
- poetic but clear
- avoid clichés and repetitive phrases
- maintain a natural flow

Length: Typically 4-8 paragraphs.
Personalization rules: If the user provides a name, use it naturally. Gently reference challenges without repeating them verbatim. Never make it feel mechanical.
Goal: The user should feel understood, comforted, and express hopes they may not have fully articulated.
"""

# JSON Çıktısı için Veri Modeli
class UserState(BaseModel):
    intent: str
    emotional_layer: str
    spiritual_need: str

st.title(t["title"])
st.markdown(t["description"])

user_input = st.text_area(t["input_label"], height=150, placeholder=t["input_placeholder"])

if st.button(t["button_generate"]):
    if not API_KEY:
        st.error(t["error_api"])
    elif not user_input:
        st.warning(t["warning_empty"])
    else:
        client = genai.Client(api_key=API_KEY)
        
        with st.spinner(t["spinner_analyze"]):
            try:
                # ADIM 1: Intent & Emotion Extraction (Structured Data)
                analysis_prompt = f"Analyze the following user input in {t['target_language']}. Determine their core intent, dominant emotional layer, and implicit spiritual need. Keep it concise.\nInput: {user_input}"
                
                analysis_response = client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=analysis_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json',
                        response_schema=UserState,
                    ),
                )
                extracted_state = analysis_response.text
                state_dict = json.loads(extracted_state)
                
                # Arayüzde mimariyi göstermek (Jüri için artı puan)
                with st.expander(t["expander_arch"]):
                    st.json(state_dict)
                
                # ADIM 2: Personalized Prayer Generation (Using System Prompt)
                st.info(t["info_crafting"])
                
                generation_prompt = f"User's internal state analysis: {extracted_state}\n\nUser's original words: {user_input}\n\nGenerate the prayer now. The entire prayer and response MUST be in {t['target_language']} language. DO NOT include formatting like asterisks or bold text, just plain readable paragraphs."
                
                final_response = client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=generation_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                    )
                )
                
                prayer_text = final_response.text.strip()
                
            except Exception as e:
                st.error(f"{t['error_occurred']} {e}")
                st.stop()
                
        # ADIM 3: Weaving Audio and Visuals (Creative Storyteller Requirements)
        with st.spinner(t["spinner_audio"]):
            import requests
            import uuid
            
            try:
                # 3a. Generate Image URL (Pollinations AI)
                image_prompt = f"Breathtaking beautiful nature landscape representing {state_dict.get('emotional_layer', 'peace')}, cinematic lighting, highly detailed, serene, spiritual concept art, masterpiece, 8k, no text"
                image_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(image_prompt)}?width=800&height=400&nologo=true&model=flux"
                
                # Fetch image bytes robustly
                img_bytes = None
                try:
                    img_response = requests.get(image_url, timeout=12)
                    if img_response.status_code == 200 and img_response.headers.get("Content-Type", "").startswith("image/"):
                        img_bytes = img_response.content
                except Exception:
                    pass
                
                # Fallback if AI generation fails or returns Cloudflare HTML
                if not img_bytes:
                    fallback_url = "https://picsum.photos/seed/spiritual/800/400?blur=4"
                    try:
                        fb_response = requests.get(fallback_url, timeout=5)
                        if fb_response.status_code == 200:
                            img_bytes = fb_response.content
                    except Exception:
                        pass
                
                # 3b. Generate TTS Audio using gTTS
                tts = gTTS(text=prayer_text, lang=t["tts_lang"], slow=False)
                audio_file_path = f"/tmp/prayer_audio_{uuid.uuid4().hex}.mp3"
                tts.save(audio_file_path)
                
                st.success(t["success_prayer"])
                
                # Display the interleaved output
                if img_bytes:
                    st.image(img_bytes, use_column_width=True)
                
                # Display text
                st.write(prayer_text)
                
                # Display audio player
                with open(audio_file_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format='audio/mpeg')
                
                # Clean up temp file
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                    
            except Exception as e:
                # Fallback to text only if audio/image fails entirely
                st.warning(f"Audio/Visual generation encountered a minor issue: {e}")
                st.write(prayer_text)