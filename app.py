from flask import Flask, request, jsonify, send_file, render_template
import os
import uuid
import wave
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
import requests
from elevenlabs import ElevenLabs, VoiceSettings


app = Flask(__name__)
AUDIO_FOLDER = 'audio'  # Folder to save audio files



# Ensure the audio folder exists
os.makedirs(AUDIO_FOLDER, exist_ok=True)


def text_to_speech_elevenlabs(text, filename):
    # Initialize ElevenLabs client
    client = ElevenLabs(
        api_key="sk_ffddba18933e8bf66ddcda2c55279becbe6c491c3681f8a9", #FOR CONTEXT I DO NOT OWN THIS API KEY,
        #I DO NOT LIKE THE PEOPLE WHO GAVE ME THIS API KEY
    )
    
    # Convert text to speech and get the response as a generator (streamed response)
    response_generator = client.text_to_speech.convert(
        voice_id="flq6f7yk4E4fJM5XTYuZ",
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        voice_settings=VoiceSettings(
            stability=0.1,
            similarity_boost=0.3,
            style=0.2,
        ),
    )
    
    # Write the streamed response to an MP3 file
    with open(filename, 'wb') as f:
        for chunk in response_generator:
            f.write(chunk)
    
    # Convert MP3 to WAV
    sound = AudioSegment.from_mp3(filename)
    wav_filename = filename.replace('.mp3', '.wav')
    sound.export(wav_filename, format="wav")
    
    return wav_filename



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
    temp_file_path = os.path.join(AUDIO_FOLDER, f'temp.wav')
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

    # Clean up the temporary audio file if it exists
    if os.path.isfile("audio/response.mp3"):
        print("Removing response.mp3")
        os.remove("audio/response.mp3")
    if os.path.isfile("audio/response.wav"):
        print("Removing response.wav")
        os.remove("audio/response.wav")

    # Generate a TTS response from the Ollama response
    response_audio_mp3_path = os.path.join(AUDIO_FOLDER, f'response.mp3')
    response_audio_wav_path = text_to_speech_elevenlabs(ollama_text_response, response_audio_mp3_path)
    

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

