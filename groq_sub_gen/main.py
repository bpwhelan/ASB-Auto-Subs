import asyncio
import subprocess
from pathlib import Path

import asbplayer

from groq_sub_gen import watcher
from groq_sub_gen.shared import config

def _asb_websocket_server_dir() -> Path:
    packaged_path = Path(asbplayer.__file__).resolve().parent / "scripts" / "web-socket-server"
    if (packaged_path / "main.go").exists():
        return packaged_path

    repo_path = Path(__file__).resolve().parents[1] / "asbplayer" / "scripts" / "web-socket-server"
    if (repo_path / "main.go").exists():
        return repo_path

    raise FileNotFoundError(
        "Could not find asbplayer web-socket-server files. "
        "Rebuild/install the package so asbplayer assets are included."
    )

async def run_asb_websocket_go_server_nonblocking():
    server_dir = _asb_websocket_server_dir()
    process = await asyncio.create_subprocess_exec(
        "go", "run", "main.go",
        cwd=str(server_dir),
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
    print("Checking for Go installation...")
    if config.RUN_ASB_WEBSOCKET_SERVER and is_go_installed():
        asbplayer_wss = await run_asb_websocket_go_server_nonblocking()
        
    print("Starting Groq Sub Gen...")

    await watcher.main()

    print("Exiting Groq Sub Gen")

if __name__ == '__main__':
    asyncio.run(main())
