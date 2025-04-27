import base64
import logging
import os
import re
import threading
from dataclasses import dataclass

import requests
import yaml
import yt_dlp
from dataclasses_json import dataclass_json

# --- Custom Exception ---
class SubtitleError(Exception):
    """Custom exception for subtitle generation errors."""
    pass



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
            logging.info(f"Successfully sent subtitles in {filename} to {http_url}")
            logging.debug(f"requests response: {response.text}")
        else:
            logging.error(f"Failed to send subtitles to {http_url}. requests returned code: {response.status_code}")
            logging.error(f"requests response text: {response.text}")
    except FileNotFoundError as e:
        logging.error(f"SRT file not found: {srt_file_path}")
    except Exception as e:
        logging.error(f"An error occurred while sending subtitles via HTTP: {e}")

@dataclass_json
@dataclass
class Config:
    LOCAL_OR_REMOTE: int = 2
    GROQ_API_KEY: str = ""
    GRADIO_URL: str = "Nick088/Fast-Subtitle-Maker"
    RUN_ASB_WEBSOCKET_SERVER: bool = True
    hf_token: str = ""
    model: str = "whisper-large-v3-turbo"
    output_dir: str = "output"

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
         logging.warning(f"Could not pre-extract video ID, using default filename: {e}")
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
    final_audio_path = f"{base_filename}.mp3"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info("Starting download and audio extraction...")
            info_dict = ydl.extract_info(youtube_url, download=True)
            if os.path.exists(final_audio_path):
                 logging.info(f"Audio download and conversion successful: {final_audio_path}")
                 return final_audio_path
            else:
                 downloaded_path = ydl.prepare_filename(info_dict)
                 if downloaded_path and downloaded_path.endswith('.mp3') and os.path.exists(downloaded_path):
                    logging.warning("yt-dlp returned a different filename than expected, using it.")
                    if downloaded_path != final_audio_path:
                        try:
                            os.rename(downloaded_path, final_audio_path)
                            logging.info(f"Renamed {downloaded_path} to {final_audio_path}")
                            return final_audio_path
                        except OSError as rename_err:
                            logging.error(f"Failed to rename downloaded file: {rename_err}")
                            return downloaded_path
                    else:
                        return final_audio_path
                 else:
                    raise SubtitleError(f"Expected audio file not found after download: {final_audio_path}")

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"yt-dlp download error: {e}")
        return None
    except Exception as e:
        logging.error(f"Error during audio download/extraction: {e}", exc_info=True)
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
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'verbose': False}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            language = info_dict.get('language', None)  # Extract language metadata if available
            if language == desired:  # 'ja' is the language code for Japanese
                return True
            else:
                logging.info("Video language does not match desired language.")
                override = timed_input("Override language check? Will timeout in 15 seconds. (y/n): ", timeout=15)
                if override and override.strip().lower() in ['y', 'yes']:
                    logging.info("Language check overridden by user.")
                    return True
    except Exception as e:
        logging.error(f"Error checking video language: {e}", exc_info=True)
    return False

config = parse_config('config.yaml')
