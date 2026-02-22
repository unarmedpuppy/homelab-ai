#!/usr/bin/env python3
"""
Game process watcher — auto-enables gaming mode on llm-manager when games are detected.

Runs on the Windows gaming PC HOST (not in Docker) because it needs to see host processes.

Setup:
  pip install psutil requests
  pythonw game-watcher.py           # run headless (no console window)
  python game-watcher.py            # run with console for debugging

Auto-start (Task Scheduler):
  Trigger:  At log on
  Action:   pythonw.exe C:\path\to\game-watcher.py
  Settings: Run whether user is logged in or not → NO (needs desktop session for process list)
             Restart if fails: yes, every 1 minute

Config: edit the sections below.
"""

import time
import logging
import subprocess
import requests
import psutil

# --- Config ---

MANAGER_URL = "http://localhost:8000"

# Processes that mean "definitely gaming right now"
# Add specific game executables here as you install them.
GAME_PROCESSES = {
    # Launchers (open = probably about to game or mid-session)
    "steam.exe",
    "epicgameslauncher.exe",
    "battle.net.exe",
    "gog galaxy.exe",
    "eadesktop.exe",
    "origin.exe",
    "upc.exe",            # Ubisoft Connect
    "riotclientservices.exe",
    # Common game engines / sessions
    "gamebar.exe",        # Windows Game Bar (active during gameplay)
    "gamebarft.exe",
    # Add your specific games:
    # "cyberpunk2077.exe",
    # "eldenring.exe",
    # "r5apex.exe",
}

# GPU utilization % above this threshold also triggers gaming mode.
# Set to 101 to disable GPU-based detection.
GPU_UTILIZATION_THRESHOLD = 60  # percent

# How long (seconds) with NO game detected before disabling gaming mode.
# Prevents toggling off mid-loading-screen or brief pauses.
DISABLE_COOLDOWN = 300  # 5 minutes

# How often to scan processes (seconds).
POLL_INTERVAL = 30

# --- End config ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [game-watcher] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("game-watcher.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def get_running_processes() -> set[str]:
    return {p.name().lower() for p in psutil.process_iter(["name"])}


def get_gpu_utilization() -> int:
    """Returns GPU utilization % via nvidia-smi, or 0 on failure."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return int(result.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return 0


def is_gaming() -> tuple[bool, str]:
    """Returns (gaming, reason)."""
    procs = get_running_processes()
    matched = GAME_PROCESSES & procs
    if matched:
        return True, f"process: {', '.join(sorted(matched))}"

    gpu = get_gpu_utilization()
    if gpu >= GPU_UTILIZATION_THRESHOLD:
        return True, f"gpu utilization: {gpu}%"

    return False, ""


def set_gaming_mode(enable: bool) -> bool:
    try:
        r = requests.post(
            f"{MANAGER_URL}/gaming-mode",
            json={"enable": enable},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Failed to call /gaming-mode: {e}")
        return False


def get_current_mode() -> bool | None:
    try:
        r = requests.get(f"{MANAGER_URL}/status", timeout=5)
        if r.status_code == 200:
            return r.json().get("gaming_mode_active", False)
    except Exception:
        pass
    return None


def main():
    logger.info(f"Starting game watcher (poll={POLL_INTERVAL}s, cooldown={DISABLE_COOLDOWN}s, gpu_threshold={GPU_UTILIZATION_THRESHOLD}%)")
    logger.info(f"Watching processes: {', '.join(sorted(GAME_PROCESSES))}")

    gaming_mode_active = False
    last_game_seen = 0.0

    while True:
        detected, reason = is_gaming()

        if detected:
            last_game_seen = time.time()
            if not gaming_mode_active:
                logger.info(f"Game detected ({reason}) — enabling gaming mode")
                if set_gaming_mode(True):
                    gaming_mode_active = True
                    logger.info("Gaming mode ON")
        else:
            if gaming_mode_active:
                idle_for = time.time() - last_game_seen
                if idle_for >= DISABLE_COOLDOWN:
                    logger.info(f"No game detected for {int(idle_for)}s — disabling gaming mode")
                    if set_gaming_mode(False):
                        gaming_mode_active = False
                        logger.info("Gaming mode OFF")
                else:
                    remaining = int(DISABLE_COOLDOWN - idle_for)
                    logger.debug(f"No game detected — waiting cooldown ({remaining}s remaining)")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
