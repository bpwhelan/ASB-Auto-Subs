import base64
import logging
import os
from dataclasses import dataclass

import requests
import yaml


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


@dataclass
class Config:
    LOCAL_OR_REMOTE: int = 2
    GROQ_API_KEY: str = ""
    GRADIO_URL: str = "Nick088/Fast-Subtitle-Maker"
    RUN_ASB_WEBSOCKET_SERVER: bool = True
    hf_token: str = ""
    model: str = "whisper-large-v3-turbo"

def parse_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        config = {
            "LOCAL_OR_REMOTE": 2,
            "GROQ_API_KEY": "",
            "GRADIO_URL": "Nick088/Fast-Subtitle-Maker",
            "RUN_ASB_WEBSOCKET_SERVER": True,
            "hf_token": "",
            "model": "whisper-large-v3-turbo"
        }
        with open(file_path, 'w') as file:
            yaml.safe_dump(config, file)
    return Config(
        LOCAL_OR_REMOTE=config["LOCAL_OR_REMOTE"],
        GROQ_API_KEY=config["GROQ_API_KEY"],
        GRADIO_URL=config["GRADIO_URL"],
        RUN_ASB_WEBSOCKET_SERVER=config["RUN_ASB_WEBSOCKET_SERVER"],
        hf_token=config["hf_token"],
        model=config['model']
    )

config = parse_config('config.yaml')