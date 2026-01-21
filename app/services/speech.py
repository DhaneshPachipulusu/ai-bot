from app.config import USE_MOCK_AI, client


def speech_to_text(audio_path: str) -> str:
    if USE_MOCK_AI:
        return "This is a mock transcribed answer"

    with open(audio_path, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio
        )
    return transcript.text


def text_to_speech(text: str, output_path: str):
    if USE_MOCK_AI:
        with open(output_path, "w") as f:
            f.write("MOCK AUDIO FILE")
        return

    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )

    with open(output_path, "wb") as f:
        f.write(response.content)
