import asyncio
import subprocess

from groq_sub_gen import local, remote

import yaml

def parse_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        default_config = {
            "LOCAL_OR_REMOTE": 2,
            "GROQ_API_KEY": "",
            "GRADIO_URL": "Nick088/Fast-Subtitle-Maker",
            "RUN_ASB_WEBSOCKET_SERVER": True
        }
        with open(file_path, 'w') as file:
            yaml.safe_dump(default_config, file)
        return default_config
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")

async def run_asb_websocket_go_server_nonblocking():
    process = await asyncio.create_subprocess_exec(
        "go", "run", "main.go",
        cwd="../asbplayer/scripts/web-socket-server",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("asbplayer WebSocket server started in the background.")
    return process

async def monitor_process(process):
    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        print("asbplayer WebSocket server finished successfully.")
    else:
        print(f"asbplayer WebSocket server exited with error code {process.returncode}:")
        if stdout:
            print(f"Stdout: {stdout.decode()}")
        if stderr:
            print(f"Stderr: {stderr.decode()}")

def is_go_installed():
    try:
        result = subprocess.run(["go", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        print(f"Go is installed: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("Go is not installed or not in PATH. Install it Here: https://go.dev/doc/install")
        raise FileNotFoundError("Go is not installed or not in PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error while checking Go installation: {e.stderr.strip()}")
        return False

async def main():
    config_path = "config.yaml"
    try:
        config = parse_config(config_path)
    except:
        config = {}


    local_or_remote = config.get("LOCAL_OR_REMOTE", 2)
    groq_api_key = config.get("GROQ_API_KEY", "")
    gradio_url = config.get("GRADIO_URL", "Nick088/Fast-Subtitle-Maker")
    run_asb_websocket_server = config.get("RUN_ASB_WEBSOCKET_SERVER", True)

    if run_asb_websocket_server and config.is_go_installed():
        asbplayer_wss = await run_asb_websocket_go_server_nonblocking()

    if local_or_remote not in [1, 2]:
        print("Invalid LOCAL_OR_REMOTE value in config.yaml. Defaulting to Remote Mode.")
        local_or_remote = 2
    if local_or_remote == 1:
        print("Running in Local Mode")
        local.main(groq_api_key)
    if local_or_remote == 2:
        remote.main(gradio_url)

    print("Exiting Groq Sub Gen")

if __name__ == '__main__':
    asyncio.run(main())
