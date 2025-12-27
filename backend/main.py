import os
import tempfile
import logging
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from yt_dlp import YoutubeDL
from groq import Groq


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yt-summary")

app = FastAPI(title="YT Summarizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


class SummarizeRequest(BaseModel):
    url: str


def extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url


def fetch_transcript_text(video_id: str) -> Optional[str]:
    """
    Compatible with your version — requires instance call:
    YouTubeTranscriptApi().list(video_id) -> transcript.fetch()
    """
    try:
        api = YouTubeTranscriptApi()
        transcripts = api.list(video_id)

        for t in transcripts:
            if t.language_code.startswith("en"):
                data = t.fetch()
                return " ".join(d["text"] for d in data)

        return None

    except NoTranscriptFound:
        logger.error("Transcript not available")
        return None
    except Exception as e:
        logger.error(f"Transcript fetch error: {e}")
        return None


def download_audio(url: str) -> str:
    temp_dir = tempfile.mkdtemp()
    output = os.path.join(temp_dir, "audio.m4a")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output,
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return output

    except Exception as e:
        logger.error(f"yt-dlp failed: {e}")
        raise RuntimeError("Could not download audio")


def groq_whisper_transcribe(path: str) -> str:
    try:
        with open(path, "rb") as f:
            resp = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
            )
        return resp.text

    except Exception as e:
        logger.error(f"Groq whisper failed: {e}")
        raise RuntimeError("Groq transcription failed")


def summarize_text(text: str) -> str:
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": (
                    "Summarize the following YouTube video clearly in bullet points. "
                    "Avoid fluff.\n\n"
                    f"{text}"
                ),
            }
        ],
    )

    return resp.choices[0].message.content


@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    video_id = extract_video_id(req.url)
    logger.info(f"Processing video: {video_id}")

    # 1️⃣ Try transcript
    transcript = fetch_transcript_text(video_id)

    if transcript:
        summary = summarize_text(transcript)
        return {"summary": summary, "source": "transcript"}

    # 2️⃣ Fallback to audio
    try:
        audio_path = download_audio(req.url)
        text = groq_whisper_transcribe(audio_path)
        summary = summarize_text(text)
        return {"summary": summary, "source": "audio"}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"status": "ok", "message": "Go to /docs"}
