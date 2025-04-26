# ASB Groq Sub

ASB Groq Sub (Name Pending)is a tool for generating subtitles from YouTube videos using a remote Gradio API. It monitors the clipboard for YouTube links, downloads the audio, and generates subtitles in `.srt` format. The project also integrates with the ASBPlayer WebSocket server for automatically loading subtitles.

Currently Hard-coded for japanese, but you can change it in `groq_sub_gen/local.py` or `groq_sub_gen/remote.py` to any language you want.

## Getting Started

### Clone the Repository

To get started, clone this repository:

```bash
git clone --recurse-submodules https://github.com/bpwhelan/asb-groq-sub.git
cd asb-groq-sub
```

### Requirements

- Python 3.8+
- `ffmpeg` installed and available in your system's PATH
- Required Python libraries (install via `pip`):
  ```bash
  pip install -r requirements.txt
  ```

### Configure `config.yaml`

Before running the project, you need to configure the `config.yaml` file. This file contains essential settings such as the Gradio API URL and other parameters.

This will be generated on first run if it doesn't exist (idk where).

1. Open the `config.yaml` file in a text editor .
2. Update the configuration values as needed. For example:
   ```yaml
   LOCAL_OR_REMOTE: 2 # 1 for "Local", 2 for "Remote"
   GROQ_API_KEY: ""
   GRADIO_URL: "Nick088/Fast-Subtitle-Maker"
   RUN_ASB_WEBSOCKET_SERVER: true
   hf_token: ""
   model: "whisper-large-v3-turbo"
   # model: "whisper-large-v3"
   output_dir: "output"
   ```
3. Save the file.



## Duplicate the Space

**I HIGHLY RECOMMEND THIS.**

### Where to get Groq API Key?

Can sign up here https://console.groq.com/ and after sign up it will ask you to generate an api key.

### How to duplicate the spacee?

Go here https://huggingface.co/spaces/Nick088/Fast-Subtitle-Maker

In the top right menu hit "Duplicate Space", sign up for an account, and it will eventually ask you for your groq api key, enter it there.

Once you are done with that, copy the space name, and put it in your `config.yaml`. I might need to implement one more step to make this work, but in the mean time, you can use the local versioln by setting `LOCAL_OR_REMOTE` to 1 and providing that groq api key.

You also will need to make an access token (hf_token in config), you can do that [here](https://huggingface.co/settings/tokens/new?tokenType=read).

## Run the Script

The script monitors your clipboard for YouTube links. When a valid YouTube link is detected, it automatically downloads the audio, generates subtitles, saves them, and then sends them to the ASBPlayer WebSocket server.

To start the script:

```bash
python groq_sub_gen/main.py
```

## ASBPlayer WebSocket Server

This project integrates with the ASBPlayer WebSocket server for subtitle synchronization. You can find more information about ASBPlayer and its WebSocket server [here](https://github.com/killergerbah/asbplayer).

## Contact

If you run into issues ask in my [Discord](https://discord.gg/yP8Qse6bb8), or make an issue here.

## Credits

- https://github.com/killergerbah/asbplayer
- https://huggingface.co/spaces/Nick088/Fast-Subtitle-Maker/tree/main
- https://github.com/m1guelpf/yt-whisper for the yt-download logic/idea

## Donations

If you've benefited from this or any of my other projects, please consider supporting my work
via [Github Sponsors](https://github.com/sponsors/bpwhelan) or [Ko-fi.](https://ko-fi.com/beangate)
