import os
import time
import requests
import base64
import google.generativeai as genai  # <-- Google AI SDK
from flask import Flask, request, jsonify, render_template_string
from elevenlabs.client import ElevenLabs # <-- Naya ElevenLabs Client

# ==============================================================================
# === 1. API KEYS SET KAR DI GAYI HAIN ===
# ==============================================================================
GEMINI_API_KEY = "AIzaSyBIPUbbQzA7kC6uxsqqpHA8JcKIY6_bYHo"
ELEVENLABS_API_KEY = "sk_a88f8a467209964702f79c396767e032e824dad678a3ef13"
RUNWAY_API_TOKEN = "key_7f52ded68d71a11e3b8d56cb14f723754684806082d0473f6bec911c15e6c8dfe72c8dd7a52c213332fa68eac2daf00a49438c1f1861e2aaf9573f838bb311c1"

# ==============================================================================
# === 2. CONFIGURATIONS ===
# ==============================================================================
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Naye SDK mein client object banta hai
    elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) 
except Exception as e:
    print(f"API Key set karne mein ghalti: {e}")

model = genai.GenerativeModel('gemini-1.5-flash')
app = Flask(__name__)

# ==============================================================================
# === 3. APP KA FRONTEND ===
# ==============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Content Hub</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 10px; }
        .container { max-width: 800px; margin: auto; background-color: #1e1e1e; border-radius: 12px; padding: 15px; display: flex; flex-direction: column; height: 95vh; }
        h2 { text-align: center; color: #bb86fc; }
        #chat-box { flex-grow: 1; overflow-y: auto; border: 1px solid #333; padding: 10px; margin-bottom: 15px; border-radius: 8px; }
        .input-area { display: flex; flex-wrap: wrap; gap: 10px; }
        #user-input { flex-grow: 1; padding: 12px; border-radius: 8px; border: 1px solid #444; background-color: #2c2c2c; color: #e0e0e0; min-width: 200px;}
        .btn { padding: 12px 15px; border-radius: 8px; border: none; color: white; cursor: pointer; font-weight: bold; }
        #send-btn { background-color: #bb86fc; }
        #video-btn { background-color: #03dac6; }
        #voice-btn { background-color: #cf6679; }
        .message { margin-bottom: 15px; padding: 10px 15px; border-radius: 12px; max-width: 85%; line-height: 1.5; word-wrap: break-word; }
        .user-message { background-color: #373737; margin-left: auto; text-align: left; }
        .bot-message, .loading-message { background-color: #2a2a2a; margin-right: auto; }
        video, audio { max-width: 100%; border-radius: 8px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>AI Content Hub</h2>
        <div id="chat-box"></div>
        <div class="input-area">
            <input type="text" id="user-input" placeholder="Yahan likhein..." />
            <button id="send-btn" class="btn">Chat</button>
            <button id="voice-btn" class="btn">Voice</button>
            <button id="video-btn" class="btn">Video</button>
        </div>
    </div>
    <script>
        document.getElementById('send-btn').addEventListener('click', () => handleRequest('chat'));
        document.getElementById('voice-btn').addEventListener('click', () => handleRequest('voice'));
        document.getElementById('video-btn').addEventListener('click', () => handleRequest('video'));

        async function handleRequest(type) {
            const userInput = document.getElementById('user-input');
            const prompt = userInput.value;
            if (!prompt) return;

            displayMessage(prompt, 'user');
            userInput.value = '';

            let endpoint = `/` + (type === 'video' ? 'generate-video' : type);
            let loadingMessage = `Aapke ${type} par kaam ho raha hai...`;
            const loadingDiv = displayMessage(loadingMessage, 'loading');

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });
                const data = await response.json();
                loadingDiv.remove();

                if (data.video_url) displayVideo(data.video_url);
                else if (data.audio_url) displayAudio(data.audio_url);
                else displayMessage(data.reply, 'bot');
                
            } catch (error) {
                loadingDiv.remove();
                displayMessage('Ek error aagaya. Connection ya API key check karein.', 'bot');
            }
        }

        function displayMessage(message, type) {
            const chatBox = document.getElementById('chat-box');
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', type + '-message');
            messageDiv.innerText = message;
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
            return messageDiv;
        }

        function displayVideo(videoUrl) {
            const chatBox = document.getElementById('chat-box');
            const videoDiv = document.createElement('div');
            videoDiv.classList.add('message', 'bot-message');
            const video = document.createElement('video');
            video.src = videoUrl; video.controls = true; video.autoplay = true;
            videoDiv.appendChild(video);
            chatBox.appendChild(videoDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        function displayAudio(audioUrl) {
            const chatBox = document.getElementById('chat-box');
            const audioDiv = document.createElement('div');
            audioDiv.classList.add('message', 'bot-message');
            const audio = document.createElement('audio');
            audio.src = audioUrl; audio.controls = true; audio.autoplay = true;
            audioDiv.appendChild(audio);
            chatBox.appendChild(audioDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# === 4. APP KA BACKEND (FLASK ROUTES) ===
# ==============================================================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json['prompt']
        response = model.generate_content(user_message)
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'reply': f'Chat Error: {e}'})

@app.route('/voice', methods=['POST'])
def generate_voice():
    prompt = request.json.get('prompt')
    if not prompt: return jsonify({'reply': 'Voice ke liye text zaroori hai.'})
    try:
        # ElevenLabs naya SDK generator return karta hai, isliye humein bytes ko join karna hota hai
        audio_generator = elevenlabs_client.generate(
            text=prompt,
            voice="Adam",
            model="eleven_multilingual_v1"
        )
        audio_bytes = b"".join(list(audio_generator))
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        audio_data_url = f"data:audio/mpeg;base64,{audio_base64}"
        return jsonify({'audio_url': audio_data_url})
    except Exception as e:
        return jsonify({'reply': f'Voice Error: {e}'})

@app.route('/generate-video', methods=['POST'])
def generate_video():
    if not RUNWAY_API_TOKEN:
        return jsonify({'reply': 'RunwayML API Token set nahi hai.'})
    
    prompt = request.json.get('prompt')
    try:
        headers = {'Authorization': f'Bearer {RUNWAY_API_TOKEN}', 'Content-Type': 'application/json'}
        response = requests.post('https://api.runwayml.com/v1/inference', headers=headers, json={'text_prompt': prompt})
        response.raise_for_status()
        task_uuid = response.json().get('uuid')

        video_url = None
        for _ in range(60):
            time.sleep(5)
            status_res = requests.get(f'https://api.runwayml.com/v1/tasks/{task_uuid}', headers=headers)
            task_data = status_res.json()
            if task_data.get('status') == 'SUCCEEDED':
                video_url = task_data.get('output', {}).get('url')
                break
            elif task_data.get('status') == 'FAILED':
                return jsonify({'reply': 'Video generation failed on Runway.'})

        return jsonify({'video_url': video_url}) if video_url else jsonify({'reply': 'Waqt zyada lag raha hai...'})
    except Exception as e:
        return jsonify({'reply': f'Video Error: {e}'})

# ==============================================================================
# === 5. RUN APP ===
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
