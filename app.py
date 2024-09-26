from flask import Flask, request, jsonify, send_file, render_template
import os
import uuid
import wave
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
import requests

app = Flask(__name__)
AUDIO_FOLDER = 'audio'  # Folder to save audio files

response_audio_mp3_path = os.path.join(AUDIO_FOLDER, 'response.mp3')
response_audio_wav_path = os.path.join(AUDIO_FOLDER, 'response.wav')

# Ensure the audio folder exists
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def text_to_speech(text, filename):
    """Convert text to speech and save the audio file."""
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    
    # Convert MP3 to WAV for uniformity
    sound = AudioSegment.from_mp3(filename)
    wav_filename = filename.replace('.mp3', '.wav')
    sound.export(wav_filename, format="wav")
    return wav_filename

@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML template

OLLAMA_API_URL = "http://host.docker.internal:11434/api/generate"  # Ollama API URL

@app.route('/api/voice', methods=['POST'])
def voice_api():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']

    # Save the uploaded audio file temporarily
    temp_file_path = os.path.join(AUDIO_FOLDER, f'temp_{uuid.uuid4()}.wav')
    audio_file.save(temp_file_path)

    # Use SpeechRecognition to recognize the speech
    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_file_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)  # Use Google Web Speech API for recognition
        except sr.UnknownValueError:
            return jsonify({'error': 'Could not understand the audio'}), 400
        except sr.RequestError:
            return jsonify({'error': 'API unavailable'}), 500

    # Call Ollama API with the recognized text as the prompt
    try:
        ollama_response = requests.post(OLLAMA_API_URL, json={
            "model": "llama3.1",
            "prompt": f"""
            Please incorporate the following information into your knowledge in case a question arises:

            Your name is Manu.
            VIT refers to Vellore Institute of Technology.
            graVITas is a tech fest organized by VIT Vellore, currently in its 15th edition.
            Sharmila N is the convenor of graVITas.
            graVITas features over 120+ tech events.
            The event has a total registration of 25,000 participants.
            The prize pool for graVITas is 25 lakhs.
            The Chancellor of VIT Vellore is G. Viswanathan.

            Conversation Guidelines
            Answer as concisely as possible, and avoid providing unnecessary information. try to keep your responses to a maximum of 3-4 sentences.
            You can also answer about other topics unrelated to VIT Vellore or graVITas.

            Prompt:
            {text}""",
            "stream": False
        })

        # Check if the request was successful
        if ollama_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch response from Ollama API'}), 500

        # Extract the response from Ollama
        ollama_data = ollama_response.json()
        ollama_text_response = ollama_data.get('response', '')

    except Exception as e:
        return jsonify({'error': 'Ollama API request failed', 'details': str(e)}), 500

    if os.path.exists(response_audio_mp3_path):
        os.remove(response_audio_mp3_path)
    if os.path.exists(response_audio_wav_path):
        os.remove(response_audio_wav_path)

    # Generate a TTS response from the Ollama response
    response_audio_mp3_path = os.path.join(AUDIO_FOLDER, f'response.mp3')
    response_audio_wav_path = text_to_speech(ollama_text_response, response_audio_mp3_path)

    # Clean up the temporary file
    os.remove(temp_file_path)

    return jsonify({'text': ollama_text_response, 'audio_path': os.path.basename(response_audio_wav_path)})


@app.route('/audio/<filename>', methods=['GET'])
def get_audio(filename):
    # Construct the full file path
    file_path = os.path.join(AUDIO_FOLDER, filename)

    # Check if the file exists before sending
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=False)
    else:
        return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

