# ASB Auto Subs

ASB Auto Subs is a tool for generating subtitles from YouTube videos using whisper locally, or groq remotely. It monitors the clipboard for YouTube links, as well as file path (shift right click "copy as path" on windows), gets the audio, and generates subtitles in `.srt` format. The project also integrates with the ASBPlayer WebSocket server for automatically loading subtitles.

## Getting Started

### Install the Package

To get started, pip install the package:

pip
```bash
pip install asb_auto_subgen
```

OR
```bash
uv tool install asb_auto_subgen
```

If you want to run whisper locally...

```bash
pip install asb_auto_subgen[local]
```
OR
```bash
uv tool install asb_auto_subgen[local]
```


### Requirements

- Python 3.11+
- `ffmpeg` installed and available in your system's PATH
- `go` installed and available in your system's PATH (for the asbplayer websocket server)

### Configure `config.yaml`

Before running the project, you need to configure the `config.yaml` file. This file contains essential settings, changing how asb-auto-subs will behave.

This will be generated on first run if it doesn't exist (idk where).

1. Open the `config.yaml` file in a text editor .
2. Update the configuration values as needed. For example:
   ```yaml
   process_locally: true
   whisper_model: "small"
   GROQ_API_KEY: ""
   RUN_ASB_WEBSOCKET_SERVER: true
   model: "whisper-large-v3-turbo"
   # model: "whisper-large-v3"
   output_dir: "output"
   language: "ja"
   skip_language_check: false
   cookies: ""
   ```
3. Save the file.

#### What Each Config Does:

- `process_locally`: Determines if the transcription is done locally or via the groq API.
- `whisper_model`: The whisper model to use for local transcription.
- `GROQ_API_KEY`: Your API key for accessing Groq's services.
- `RUN_ASB_WEBSOCKET_SERVER`: Whether to run the ASBPlayer WebSocket server.
- `model`: The groq transcription model to use.
- `output_dir`: Directory where output files are saved.
- `language`: Language code for transcription. Also used to check if the video's language is what we want.
- `skip_language_check`: When `true`, bypasses YouTube metadata language validation entirely.
- `cookies`: Cookies for authenticated yt-dlp requests.

## Setup API Usage

### Where to get Groq API Key? (REQUIRED)

Can sign up here https://console.groq.com/ and after sign up it will ask you to generate an api key.

## Run the Script

The script monitors your clipboard for YouTube links. When a valid YouTube link is detected, it automatically downloads the audio, generates subtitles, saves them, and then sends them to the ASBPlayer WebSocket server.

To start the script:

```bash
asb_auto_subgen
```

## ASBPlayer WebSocket Server

This project integrates with the ASBPlayer WebSocket server for subtitle synchronization. You can find more information about ASBPlayer and its WebSocket server [here](https://github.com/killergerbah/asbplayer).

## Contact

If you run into issues, you can make an issue [here](https://github.com/bpwhelan/ASB-Auto-Subs/issues).

## Credits

- https://github.com/killergerbah/asbplayer
- https://huggingface.co/spaces/Nick088/Fast-Subtitle-Maker/tree/main
- https://github.com/m1guelpf/yt-whisper for the yt-download logic/idea

## Donations

If you've benefited from this or any of my other projects, please consider supporting my work
via [Github Sponsors](https://github.com/sponsors/bpwhelan) or [Ko-fi.](https://ko-fi.com/beangate)



