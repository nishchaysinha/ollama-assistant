from gtts import gTTS
import os
import speech_recognition as sr
from pydub import AudioSegment

def test_tts(text):
    """Convert text to speech and play the audio."""
    # Convert the text to speech
    tts = gTTS(text=text, lang='en')
    
    # Save the audio file
    audio_filename = 'test_audio.mp3'
    tts.save(audio_filename)
    
    print(f"Audio saved as: {audio_filename}")
    
    # Convert MP3 to WAV
    sound = AudioSegment.from_mp3(audio_filename)
    wav_filename = 'test_audio.wav'
    sound.export(wav_filename, format="wav")
    
    print(f"Audio converted to WAV: {wav_filename}")

def test_speech_recognition():
    """Test the speech recognition functionality."""
    recognizer = sr.Recognizer()
    
    # Load the audio file
    wav_filename = 'test_audio.wav'
    with sr.AudioFile(wav_filename) as source:
        audio_data = recognizer.record(source)
    
    # Recognize the speech
    text = recognizer.recognize_google(audio_data)
    print(f"Recognized text: {text}")

if __name__ == "__main__":
    test_string = ""  # Simple test string
    test_tts(test_string)  # Test TTS
    test_speech_recognition()  # Test speech recognition