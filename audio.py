# audio.py

import os
try:
    import pygame
except ImportError:
    pygame = None
from settings import SOUNDS_DIR

# ============================================================
# INITIALISE AUDIO
# ============================================================

sounds = {}
audio_enabled = pygame is not None


def init_audio():
    """Initialise pygame mixer and load all sounds safely."""
    global audio_enabled

    if pygame is None:
        audio_enabled = False
        return

    try:
        pygame.mixer.init()
    except Exception:
        print("⚠ Audio device not available — sound disabled.")
        audio_enabled = False
        return

    load_all_sounds()


# ============================================================
# LOAD SOUNDS
# ============================================================

def load_sound(filename):
    """Load a single sound file safely."""
    if not audio_enabled:
        return None

    path = os.path.join(SOUNDS_DIR, filename)

    if not os.path.exists(path):
        print(f"⚠ Missing sound file: {filename}")
        return None

    try:
        return pygame.mixer.Sound(path)
    except Exception:
        print(f"⚠ Failed to load sound: {filename}")
        return None


def load_all_sounds():
    """Load all game sound effects."""
    global sounds

    sounds = {
        "click": load_sound("click.wav"),
        "correct": load_sound("correct.wav"),
        "incorrect": load_sound("incorrect.wav"),
        "level_up": load_sound("level_up.wav"),
        "reward": load_sound("reward.wav"),
        "error": load_sound("error.wav")
    }


# ============================================================
# PLAY SOUND
# ============================================================

def play(name):
    """Play a sound by name if it exists."""
    if not audio_enabled:
        return

    sound = sounds.get(name)
    if sound:
        try:
            sound.play()
        except Exception:
            pass


# ============================================================
# SHORTCUT FUNCTIONS
# ============================================================

def play_click():
    play("click")


def play_correct():
    play("correct")


def play_incorrect():
    play("incorrect")


def play_level_up():
    play("level_up")


def play_reward():
    play("reward")


def play_error():
    play("error")
