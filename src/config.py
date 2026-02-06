"""
Configuration and tuning parameters for Little Cat game
Modify these values to customize cat behavior and learning speed
"""

# Game Settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 30
GAME_SPEED = 0.005  # Time multiplier (higher = faster time progression)

# Cat Brain Settings
INITIAL_HAPPINESS = 50      # 0-100
INITIAL_HUNGER = 30         # 0-100
INITIAL_ENERGY = 70         # 0-100
INITIAL_TRUST = 30          # 0-100

# Learning Rate (how quickly cat learns from interactions)
LEARNING_RATE = 0.1         # 0.05 = slow learner, 0.2 = fast learner
BEHAVIOR_ADJUSTMENT = 0.05  # How much behavior weights change per interaction

# Memory Settings
MAX_MEMORY_SIZE = 100       # Number of memories to keep (older memories fade)
MEMORY_RETENTION = 0.9      # How much weight to give old memories (0.9 = remember well)

# Emotional Decay (how fast emotions change naturally)
HAPPINESS_DECAY = 0.5       # Happiness loss per hour when lonely
HUNGER_RATE = 1.5           # Hunger increase per hour
ENERGY_DRAIN = 2.0          # Energy drain per hour when awake

# Action Effects
PLAY_HAPPINESS_GAIN = 20
PLAY_ENERGY_COST = 15
PLAY_HUNGER_COST = 10

FEED_HUNGER_REDUCTION = 30
FEED_HAPPINESS_GAIN = 5

SLEEP_ENERGY_GAIN = 40
SLEEP_HUNGER_COST = 20

PET_HAPPINESS_GAIN = 15
PET_TRUST_GAIN = 20

# AI Decision Making
MIN_CONFIDENCE_FOR_AUTO_ACTION = 0.6  # Threshold for AI to perform actions
AUTO_ACTION_INTERVAL = 3               # Seconds between AI auto-actions

# Reward System
BASE_REWARD = 0.5
MATCHED_NEED_REWARD = 1.0   # Reward for addressing cat's actual need
MISMATCHED_NEED_REWARD = -0.5  # Penalty for ignoring needs

# Visual Settings
CAT_COLOR = (255, 165, 0)   # Orange
CAT_SIZE = 40               # Pixel radius
DISPLAY_STATS_UPDATE_RATE = 0.1  # Seconds between stat updates

print("Config loaded successfully!")
