import subprocess

from groq_sub_gen import local, remote

if __name__ == '__main__':
    user_input: int = int(input("Select mode:\n1. Local\n2. Remote\nEnter 1 or 2: "))

    if user_input not in [1, 2]:
        print("Invalid selection. Please enter 1 or 2.")
        exit(1)
    if user_input == 1:
        print("Running in Local Mode")
        local.main()
    if user_input == 2:
        remote.main()

    print("Exiting Groq Sub Gen")

def run_asb_websocket_go_server():
    try:
        subprocess.run(["go", "run", "asbplayer/scripts/web-socket-server/main.go"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running WebSocket server: {e}")

def is_go_installed():
    try:
        result = subprocess.run(["go", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        print(f"Go is installed: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("Go is not installed or not in PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error while checking Go installation: {e.stderr.strip()}")
        return False