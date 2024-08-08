import subprocess
import sys

def start():
    try:
        # Start all services using Docker Compose
        subprocess.run(["docker-compose", "up", "--build"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Stopping all processes...")
        subprocess.run(["docker-compose", "down"])
        sys.exit(0)

if __name__ == "__main__":
    start()