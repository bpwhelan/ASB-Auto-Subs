import asyncio
import subprocess

from groq_sub_gen import local, remote
from groq_sub_gen.shared import config

async def run_asb_websocket_go_server_nonblocking():
    process = await asyncio.create_subprocess_exec(
        "go", "run", "main.go",
        cwd="./asbplayer/scripts/web-socket-server",
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
    if config.RUN_ASB_WEBSOCKET_SERVER and is_go_installed():
        asbplayer_wss = await run_asb_websocket_go_server_nonblocking()

    print(config)

    if config.LOCAL_OR_REMOTE not in [1, 2]:
        print("Invalid LOCAL_OR_REMOTE value in config.yaml. Defaulting to Remote Mode.")
        return
    if config.LOCAL_OR_REMOTE == 1:
        print("Running in Local Mode")
        local.main()
    if config.LOCAL_OR_REMOTE == 2:
        remote.main()

    print("Exiting Groq Sub Gen")

if __name__ == '__main__':
    asyncio.run(main())
