import asyncio
import base64
import os
import subprocess
import json
import re
import logging
import time
import pyperclip # For clipboard monitoring
import requests
import yt_dlp    # For YouTube downloading
from io import BytesIO
# from groq import Groq # Assuming groq library is installed and used
from gradio_client import Client, handle_file

# --- Configuration ---
# Recommended: Load API key from environment variable
# GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# Alternative (less secure):
# GROQ_API_KEY = "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" # Replace with your actual key if not using environment variables

GRADIO_API_URL = "Nick088/Fast-Subtitle-Maker"

# Directory to save downloaded audio
OUTPUT_DIR = ".."  # Save in the current directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants (from SubtitleProcessor - relevant subset) ---

LANGUAGE_CODES = {
    "English": "en", "Chinese": "zh", "German": "de", "Spanish": "es", "Russian": "ru",
    "Korean": "ko", "French": "fr", "Japanese": "ja", "Portuguese": "pt", "Turkish": "tr",
    "Polish": "pl", "Catalan": "ca", "Dutch": "nl", "Arabic": "ar", "Swedish": "sv",
    "Italian": "it", "Indonesian": "id", "Hindi": "hi", "Finnish": "fi", "Vietnamese": "vi",
    "Hebrew": "he", "Ukrainian": "uk", "Greek": "el", "Malay": "ms", "Czech": "cs",
    "Romanian": "ro", "Danish": "da", "Hungarian": "hu", "Tamil": "ta", "Norwegian": "no",
    "Thai": "th", "Urdu": "ur", "Croatian": "hr", "Bulgarian": "bg", "Lithuanian": "lt",
    "Latin": "la", "Māori": "mi", "Malayalam": "ml", "Welsh": "cy", "Slovak": "sk",
    "Telugu": "te", "Persian": "fa", "Latvian": "lv", "Bengali": "bn", "Serbian": "sr",
    "Azerbaijani": "az", "Slovenian": "sl", "Kannada": "kn", "Estonian": "et",
    "Macedonian": "mk", "Breton": "br", "Basque": "eu", "Icelandic": "is", "Armenian": "hy",
    "Nepali": "ne", "Mongolian": "mn", "Bosnian": "bs", "Kazakh": "kk", "Albanian": "sq",
    "Swahili": "sw", "Galician": "gl", "Marathi": "mr", "Panjabi": "pa", "Sinhala": "si",
    "Khmer": "km", "Shona": "sn", "Yoruba": "yo", "Somali": "so", "Afrikaans": "af",
    "Occitan": "oc", "Georgian": "ka", "Belarusian": "be", "Tajik": "tg", "Sindhi": "sd",
    "Gujarati": "gu", "Amharic": "am", "Yiddish": "yi", "Lao": "lo", "Uzbek": "uz",
    "Faroese": "fo", "Haitian": "ht", "Pashto": "ps", "Turkmen": "tk", "Norwegian Nynorsk": "nn",
    "Maltese": "mt", "Sanskrit": "sa", "Luxembourgish": "lb", "Burmese": "my", "Tibetan": "bo",
    "Tagalog": "tl", "Malagasy": "mg", "Assamese": "as", "Tatar": "tt", "Hawaiian": "haw",
    "Lingala": "ln", "Hausa": "ha", "Bashkir": "ba", "Javanese": "jw", "Sundanese": "su",
}

ALLOWED_FILE_EXTENSIONS = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
MAX_FILE_SIZE_MB = 25

# --- Custom Exception ---
class SubtitleError(Exception):
    """Custom exception for subtitle generation errors."""
    pass

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

def generate_subtitles_remote(audio_file_path, language="ja"):
    """Calls the remote Gradio API to generate subtitles."""
    client = Client(GRADIO_API_URL)
    try:
        result = client.predict(
            input_file=handle_file(audio_file_path),
            prompt="",
            timestamp_granularities_str="word",
            language=language,
            auto_detect_language=False,
            model="whisper-large-v3-turbo",
            include_video=False,
            font_selection="Arial",
            font_file=None,
            font_color="#FFFFFF",
            font_size=24,
            outline_thickness=1,
            outline_color="#000000",
            api_name="/generate_subtitles"
        )
        if result and isinstance(result, tuple) and len(result) > 0:
            return result[0]
        else:
            logging.error(f"Remote subtitle generation failed or returned unexpected result: {result}")
            return None
    except Exception as e:
        logging.error(f"Error calling remote subtitle generation API: {e}", exc_info=True)
        return None

def main():
    logging.info(f"Using remote Gradio API at: {GRADIO_API_URL}")

    previous_clipboard_content = ""
    logging.info("Monitoring clipboard for YouTube links... (Press Ctrl+C to stop)")

    while True:
        try:
            current_clipboard_content = pyperclip.paste()
            if current_clipboard_content != previous_clipboard_content and current_clipboard_content:
                previous_clipboard_content = current_clipboard_content
                if is_youtube_url(current_clipboard_content):
                    logging.info(f"Detected YouTube link: {current_clipboard_content}")
                    audio_file_path = None
                    try:
                        audio_file_path = download_audio(current_clipboard_content, OUTPUT_DIR)

                        if audio_file_path and os.path.exists(audio_file_path):
                            logging.info(f"Audio downloaded to: {audio_file_path}")
                            base_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
                            output_srt_path = os.path.join(OUTPUT_DIR, f"{base_filename}.srt")

                            try:
                                remote_srt_content = generate_subtitles_remote(audio_file_path, language='ja')
                                if remote_srt_content:
                                    try:
                                        with open(output_srt_path, "w", encoding="utf-8") as f:
                                            f.write(remote_srt_content)
                                        logging.info(f"Subtitles generated successfully and saved to: {output_srt_path}")
                                        send_subtitles_http(output_srt_path)
                                    except IOError as e:
                                        logging.error(f"Failed to write SRT content to {output_srt_path}: {e}")
                                else:
                                    logging.error("Remote subtitle generation failed (returned None content).")

                            except Exception as gen_err:
                                logging.error(f"Unexpected error during remote subtitle generation: {gen_err}", exc_info=True)

                        else:
                            logging.error("Audio download failed or file not found.")

                    finally:
                        if audio_file_path and os.path.exists(audio_file_path):
                            pass
            time.sleep(1)

        except pyperclip.PyperclipException as clip_err:
            logging.warning(f"Could not access clipboard: {clip_err}. Retrying...")
            time.sleep(5)
        except KeyboardInterrupt:
            logging.info("Stopping clipboard monitoring.")
            break
        except Exception as loop_err:
            logging.error(f"Error in main loop: {loop_err}", exc_info=True)
            time.sleep(5)

if __name__ == "__main__":
    try:
        import yt_dlp
        import pyperclip
        from gradio_client import Client, handle_file
    except ImportError as e:
        print(f"Error: Missing dependency - {e.name}")
        print("Please install required libraries: pip install yt-dlp pyperclip gradio-client")
        exit(1)

    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: ffmpeg command not found or failed execution.")
        print("         Ensure ffmpeg is installed and in your system's PATH for audio extraction/conversion.")

    main()

    # End of the main.py script