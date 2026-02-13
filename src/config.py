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

# Adult and busy behavior
ADULT_AGE_DAYS = 199
BUSY_THRESHOLD_SECONDS = 20
ADULT_SLEEP_MULTIPLIER = 2.5
ADULT_REST_MULTIPLIER = 1.8
ADULT_FIXED_SPOT = True
FIXED_SPOT_MARGIN_X = 140
FIXED_SPOT_MARGIN_Y = 160
YOUNG_FOLLOW_CURSOR = True
YOUNG_PLAY_DISTANCE = 45
YOUNG_PLAY_COOLDOWN = 6.0

# ===== CHAT AGENT CONFIGURATION =====
# LARY Agent (AI helper chat integrated into game)
# Screenshot captured ON-DEMAND only (when user requests help)

CHAT_ENABLED = True                      # Enable/disable chat feature
CHAT_TOGGLE_KEY = "?"                    # Press '?' to open chat
CHAT_MODEL = "gpt-4-vision-preview"      # OpenAI model (+ vision capability)
CHAT_MAX_TOKENS = 500                    # Max response length
CHAT_HISTORY_LENGTH = 10                 # Context history (messages)
CHAT_API_TIMEOUT = 5.0                   # Seconds to wait for API response
CHAT_MAX_REQUESTS_PER_MINUTE = 10        # Rate limit (10 req/min)
CHAT_UI_WIDTH = 760                      # Chat box width (pixels)
CHAT_UI_HEIGHT = 280                     # Chat box height (pixels)

# Optional: Use cheaper/faster model (less quality)
# CHAT_MODEL = "gpt-3.5-turbo"
# CHAT_MAX_TOKENS = 300

# Cost Warning: gpt-4-vision is ~$0.03 per image + tokens
# Monitor OPENAI_API_KEY usage in dashboard

print("Config loaded successfully!")
