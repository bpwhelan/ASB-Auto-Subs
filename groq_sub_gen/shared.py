import json
import base64
import logging
import os
import re
import subprocess
import threading
from dataclasses import dataclass

import requests
import yaml
import yt_dlp
import torch
from dataclasses_json import dataclass_json

# --- Custom Exception ---


class SubtitleError(Exception):
    """Custom exception for subtitle generation errors."""
    pass


class DirectoryWatcher(threading.Thread):
    def __init__(self, directory, callback):
        super().__init__()
        self.directory = directory
        self.callback = callback
        self.running = True

    def run(self):
        logging.info(f"Starting directory watcher for {self.directory}")
        initial_files = set(os.listdir(self.directory))
        while self.running:
            current_files = set(os.listdir(self.directory))
            new_files = current_files - initial_files
            if new_files:
                for new_file in new_files:
                    full_path = os.path.join(self.directory, new_file)
                    if os.path.isfile(full_path):
                        logging.info(f"New file detected: {new_file}")
                        self.callback(full_path)
            initial_files = current_files

    def stop(self):
        self.running = False
        logging.info("Stopping directory watcher")


def send_subtitles_http(srt_file_path):
    """
    Reads an SRT file, encodes it to Base64, and sends it to an HTTP endpoint using requests.

    Args:
        srt_file_path (str): The path to the generated SRT file.
    """
    http_url = "http://127.0.0.1:8766/asbplayer/load-subtitles"
    if not os.path.exists(srt_file_path):
        logging.error(f"SRT file does not exist: {srt_file_path}")
        return
    try:
        with open(srt_file_path, 'rb') as f:
            srt_content_bytes = f.read()
        base64_srt = base64.b64encode(srt_content_bytes).decode('utf-8')
        filename = os.path.basename(srt_file_path)
        post_data = {"files": [{"name": filename, "base64": base64_srt}]}
        response = requests.post(http_url, json=post_data)
        if response.status_code == 200:
            logging.info(
                f"Successfully sent subtitles in {filename} to {http_url}")
            logging.debug(f"requests response: {response.text}")
        else:
            logging.error(
                f"Failed to send subtitles to {http_url}. requests returned code: {response.status_code}")
            logging.error(f"requests response text: {response.text}")
    except FileNotFoundError as e:
        logging.error(f"SRT file not found: {srt_file_path}")
    except Exception as e:
        logging.error(
            f"An error occurred while sending subtitles via HTTP: {e}")


@dataclass_json
@dataclass
class Config:
    process_locally: bool = True
    whisper_model: str = "turbo"
    RUN_ASB_WEBSOCKET_SERVER: bool = True
    GROQ_API_KEY: str = ""
    model: str = "whisper-large-v3-turbo"
    output_dir: str = "output"
    language: str = "ja"
    # path_to_watch: str = "./watch"
    cookies: str = ""

    def __init__(self, process_locally=True, GROQ_API_KEY="", whisper_model="turbo", RUN_ASB_WEBSOCKET_SERVER=True, model="whisper-large-v3-turbo", output_dir="output", language="ja", path_to_watch="./watch", cookies="", *args, **kwargs):
        self.process_locally = process_locally
        self.GROQ_API_KEY = GROQ_API_KEY
        self.whisper_model = whisper_model
        self.RUN_ASB_WEBSOCKET_SERVER = RUN_ASB_WEBSOCKET_SERVER
        self.model = model
        self.output_dir = output_dir
        self.language = language
        # self.path_to_watch = path_to_watch
        self.cookies = cookies


def parse_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config = Config(**yaml.safe_load(file))
    except FileNotFoundError:
        config = Config()
        with open(file_path, 'w') as file:
            yaml.safe_dump(config.to_dict(), file)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file {file_path}: {e}")
        raise
    return config


# --- YouTube Functions ---

def download_audio(youtube_url, output_dir="."):
    """Downloads audio from YouTube URL, returns final audio file path."""
    logging.info(f"Attempting to download audio from: {youtube_url}")
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'verbose': False, 'skip_download': True}) as ydl:
            info_dict_pre = ydl.extract_info(youtube_url, download=False)
            video_id = info_dict_pre.get('id', 'youtube_audio')
            base_filename = os.path.join(output_dir, video_id)
            logging.info(f"Video ID detected: {video_id}")
    except Exception as e:
        logging.warning(
            f"Could not pre-extract video ID, using default filename: {e}")
        base_filename = os.path.join(output_dir, "youtube_audio")

    ydl_opts = {
        'quiet': False,
        'verbose': False,
        'format': 'bestaudio/best',
        'outtmpl': f'{base_filename}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'keepvideo': False,
        'noplaylist': True,
    }

    if config.cookies:
        ydl_opts['cookiesfrombrowser'] = (config.cookies,)
    final_audio_path = f"{base_filename}.mp3"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info("Starting download and audio extraction...")
            info_dict = ydl.extract_info(youtube_url, download=True)
            if os.path.exists(final_audio_path):
                logging.info(
                    f"Audio download and conversion successful: {final_audio_path}")
                return final_audio_path
            else:
                downloaded_path = ydl.prepare_filename(info_dict)
                if downloaded_path and downloaded_path.endswith('.mp3') and os.path.exists(downloaded_path):
                    logging.warning(
                        "yt-dlp returned a different filename than expected, using it.")
                    if downloaded_path != final_audio_path:
                        try:
                            os.rename(downloaded_path, final_audio_path)
                            logging.info(
                                f"Renamed {downloaded_path} to {final_audio_path}")
                            return final_audio_path
                        except OSError as rename_err:
                            logging.error(
                                f"Failed to rename downloaded file: {rename_err}")
                            return downloaded_path
                    else:
                        return final_audio_path
                else:
                    raise SubtitleError(
                        f"Expected audio file not found after download: {final_audio_path}")

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"yt-dlp download error: {e}")
        return None
    except Exception as e:
        logging.error(
            f"Error during audio download/extraction: {e}", exc_info=True)
        return None


def is_youtube_url(url):
    """Checks if the given URL is a valid YouTube URL."""
    if not url or not isinstance(url, str):
        return False
    youtube_regex = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?'
        r'(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)'
        r'([a-zA-Z0-9_-]{11})'
        r'(?:\S*)?'
    )
    return bool(youtube_regex.match(url))


def timed_input(prompt, timeout=5):
    user_input = [None]

    def get_input():
        user_input[0] = input(prompt)

    input_thread = threading.Thread(target=get_input)
    input_thread.start()
    input_thread.join(timeout)

    if input_thread.is_alive():
        logging.info("Input timed out.")
        return None
    return user_input[0]


def is_language_desired(url, desired='ja'):
    """
    Checks if the YouTube video is in desired language.
    """
    logging.info("Checking video language...")
    yt_dlp_ops = {'quiet': True, 'verbose': False}
    if config.cookies:
        yt_dlp_ops['cookiesfrombrowser'] = (config.cookies,)
    try:
        with yt_dlp.YoutubeDL(yt_dlp_ops) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            # Extract language metadata if available
            language = info_dict.get('language', None)
            if language == desired:  # 'ja' is the language code for Japanese
                return True
            else:
                print(
                    f"Video language {language}, does not match desired language '{desired}'.")
                override = timed_input(
                    "Override language check? Will timeout in 15 seconds. (y/n): ", timeout=15)
                if override and override.strip().lower() in ['y', 'yes']:
                    logging.info("Language check overridden by user.")
                    return True
                else:
                    logging.info("Skipping video due to language mismatch.")
                return False
    except Exception as e:
        logging.error(f"Error checking video language: {e}", exc_info=True)
    return False


def is_file_path(path):
    """Checks if the given path is a valid file path."""
    path = path.replace('"', "")
    if not path or not isinstance(path, str):
        return False
    return os.path.isfile(path) and os.path.exists(path)


def extract_audio_from_local_video(path):
    """Extracts audio from a local video file."""
    if not is_file_path(path):
        logging.error(f"Invalid file path: {path}")
        return None

    output_audio_path = f"{os.path.splitext(path)[0]}.mp3"
    try:
        subprocess.run(["ffmpeg", "-i", path, "-q:a", "0",
                       "-map", "a", output_audio_path], check=True)
        logging.info(f"Audio extracted successfully: {output_audio_path}")
        return output_audio_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Error extracting audio: {e}")
        return None


class StableTSProcessor:
    """
    Processor to run stable-ts on a local audio file and return segment/word timestamps similar to groq output.
    """

    def __init__(self, model="turbo", extra_args=None):
        self.model = model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.extra_args = extra_args or []
        
        if config.model:
            self.model = config.model

        try:
            import stable_whisper
        except ImportError:
            raise SubtitleError(
                "stable_whisper (stable-ts) is not installed. Please install it via pip.")
        try:
            self.model = stable_whisper.load_model(model, device=self.device)
        except Exception as e:
            logging.error(f"Failed to load stable-ts model: {e}")
            raise SubtitleError(f"Failed to load stable-ts model: {e}")

    def get_audio_segments(self, audio_path, language="ja", word_timestamps=False, vad=True, min_silence_duration_ms=250):
        """
        Run stable-ts (via stable_whisper) on the given audio file and return parsed segments/words.
        Returns a dict with 'segments' and 'words' keys, similar to groq output.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Transcribe
        try:
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                vad=vad,
                temperature=0.0,
                # Add any extra args if needed
            )
        except Exception as e:
            logging.error(f"stable-ts transcription failed: {e}")
            raise SubtitleError(f"stable-ts transcription failed: {e}")

        # Convert to groq-like format
        segments = []
        words = []
        for i, seg in enumerate(result.segments):
            segments.append({
                "id": i,
                "start": float(seg.start) if hasattr(seg, 'start') else 0.0,
                "end": float(seg.end) if hasattr(seg, 'end') else 0.0,
                "text": getattr(seg, 'text', "")
            })
            if hasattr(seg, 'words') and seg.words:
                for w in seg.words:
                    words.append({
                        "id": len(words),
                        "start": float(getattr(w, 'start', 0.0)),
                        "end": float(getattr(w, 'end', 0.0)),
                        "word": getattr(w, 'word', getattr(w, 'text', ""))
                    })

        return {"segments": segments, "words": words}


config = parse_config('config.yaml')
