# DEVELOPER'S GUIDE - Little Cat AI Pet Game

## For Developers and Learners

This guide explains the codebase in detail so you can modify, extend, and improve the Little Cat project.

---

## PROJECT OVERVIEW

**Little Cat** is an AI pet simulator that demonstrates:
- Reinforcement learning concepts
- State machine architecture
- Game development patterns
- Persistent data systems
- Neural network basics

**Tech Stack:**
- Python 3.8+
- Pygame (graphics and game loop)
- NumPy (mathematical operations)
- JSON (data persistence)

---

## CODEBASE STRUCTURE

### File: `src/cat_brain.py` (Core AI)

**Purpose:** Implements the cat's learning brain and decision-making system

**Key Classes:**

#### `CatBrain` - Main AI class

**Attributes:**
```python
# Identification
self.name          # Cat's name (string)
self.age           # Age in days (float)

# Emotional state (0-100 scale)
self.happiness     # How satisfied the cat is
self.hunger        # Food need level
self.energy        # Tiredness level
self.trust         # Bond with human

# Learning system
self.memories      # List of past interactions
self.learned_behaviors    # Dict of learned weights
self.behavior_weights     # Dict of innate behaviors
self.action_history       # Recent actions tracking
self.max_memory           # Memory buffer size (default: 100)
```

**Key Methods:**

```python
def learn_from_interaction(self, action, human_response, reward):
    """
    Train the cat from an interaction
    
    Args:
        action (str): What cat did (play, eat, sleep, etc)
        human_response (str): Human's description of response
        reward (float): Feedback from -1 (bad) to +1 (good)
    
    How it works:
    1. Stores interaction in memory
    2. Updates behavior weights based on reward
    3. Modifies emotional state
    4. Limits memory to max_memory size
    """
```

```python
def decide_action(self, context="neutral"):
    """
    Decide what action to take next
    
    Args:
        context (str): "human_nearby", "alone", "food_available"
    
    Returns:
        (action, confidence): Best action and how sure (-1 to 1)
    
    Algorithm:
    1. Start with learned behavior weights
    2. Adjust based on emotional state:
       - High hunger → prefer eating
       - Low energy → prefer sleeping
       - High trust + human nearby → prefer playing
    3. Add random noise (personality)
    4. Select action with highest weight
    """
```

```python
def update_state(self, time_delta=1):
    """
    Update cat's internal state over time
    
    Args:
        time_delta (float): Hours passed in game time
    
    Affects:
    - Age increases
    - Energy decreases if awake
    - Hunger increases naturally
    - Happiness may decrease if lonely
    """
```

```python
def get_status(self):
    """
    Get complete cat status snapshot
    
    Returns:
        dict: All emotional states, mood, learned behaviors, etc
    
    Used for UI display and debugging
    """
```

```python
def save_brain(self, filepath):
def load_brain(self, filepath):
    """
    Persist cat state to/from JSON file
    
    Saves: Name, age, emotions, behavior weights, recent memories
    Allows: Resuming a cat's learning between sessions
    """
```

**Important Constants:**

```python
MAX_INITIAL_BEHAVIORS = 6     # Number of action types
LEARNING_RATE = 0.1            # How much each reward affects behavior
EMOTION_CLIP_RANGE = (0, 100)  # Emotions stay within this range
```

---

### File: `src/game.py` (Game Engine & UI)

**Purpose:** Main game loop, rendering, and player input handling

**Key Classes:**

#### `GameDisplay` - Rendering system

**Attributes:**
```python
self.screen          # Pygame display surface
self.clock           # Frame rate controller
self.font_*          # Various font sizes for UI
self.cat_x, self.cat_y    # Cat position on screen
```

**Key Methods:**

```python
def draw_cat(self, action, mood):
    """
    Render the cat character
    
    Draws:
    - Orange cat body and head
    - Ears and facial features
    - Eyes that reflect mood
    - Action indicator above cat
    
    TODO: Make more cute! Add animations!
    """
```

```python
def draw_stats(self, cat_status):
    """
    Display all stat information
    
    Shows:
    - Cat name and age
    - Emotional state bars
    - Current mood emoji
    - Behavior learning progress
    """
```

```python
def render(self, cat_status, current_action):
    """
    Complete frame rendering
    
    Calls:
    1. Clear screen (white background)
    2. Draw cat
    3. Draw stats
    4. Draw instructions
    5. Flip display
    """
```

#### `LittleCatGame` - Game Controller

**Attributes:**
```python
self.cat              # The CatBrain instance
self.display          # GameDisplay instance
self.running          # Game loop flag
self.game_time        # In-game time tracker
self.current_action   # What cat is currently doing
self.action_timer     # How long to display current action
self.save_path        # Where to save cat brain
```

**Key Methods:**

```python
def handle_input(self):
    """
    Process player keyboard input
    
    Checks for:
    - Interaction keys (P, F, T, S, etc)
    - Game control keys (ESC, E for save, L for load)
    - Converts keys to actions
    - Calls perform_action()
    """
```

```python
def perform_action(self, action, message):
    """
    Execute a player-initiated action
    
    Does:
    1. Calculate reward based on cat state
    2. Call cat.learn_from_interaction()
    3. Update cat's emotional state
    4. Display action to player
    5. Set action timer for animation
    """
```

```python
def calculate_reward(self, action):
    """
    Determine reward value for an action
    
    Returns:
    - +1.0: Perfect action (cat needed exactly this)
    - +0.5: Good action (helps but not priority)
    - -0.5: Bad action (cat didn't want this)
    - -1.0: Wrong action (cat wanted something else)
    
    Examples:
    - Feed when hungry > 50 → +1.0
    - Feed when not hungry → -0.5
    - Play when tired → -0.5
    - Hide when scared → +0.8
    """
```

```python
def update(self):
    """
    Main game update logic (called each frame)
    
    Does:
    1. Update cat internal state
    2. Decrease action timer
    3. Periodically let AI decide actions
    4. Call cat.decide_action()
    5. Auto-perform actions if confident
    """
```

```python
def run(self):
    """
    Main game loop
    
    Pattern:
    while running:
        handle_input()
        update()
        render()
        sleep(1/FPS)
    """
```

---

### File: `src/config.py` (Settings)

**Purpose:** Centralized configuration for easy tweaking

**Key Settings:**

```python
# Performance
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 30
GAME_SPEED = 0.1  # 1 = real-time, 0.1 = 10x slower

# Initial emotional state (0-100)
INITIAL_HAPPINESS = 50
INITIAL_HUNGER = 30
INITIAL_ENERGY = 70
INITIAL_TRUST = 30

# Learning parameters
LEARNING_RATE = 0.1           # 0.05 = slow, 0.2 = fast
BEHAVIOR_ADJUSTMENT = 0.05    # Weight change per interaction

# Memory settings
MAX_MEMORY_SIZE = 100         # Keep last 100 interactions
MEMORY_RETENTION = 0.9        # Weight for old memories

# Emotional dynamics
HAPPINESS_DECAY = 0.5         # Loss per hour when lonely
HUNGER_RATE = 1.5             # Increase per hour
ENERGY_DRAIN = 2.0            # Drain per active hour

# Action effects
PLAY_HAPPINESS_GAIN = 20
PLAY_ENERGY_COST = 15
PLAY_HUNGER_COST = 10

FEED_HUNGER_REDUCTION = 30
FEED_HAPPINESS_GAIN = 5

# ... and many more
```

**How to use:**
```python
# In your code:
from config import FPS, LEARNING_RATE, INITIAL_HAPPINESS

# Modify values here to tune behavior
```

---

### File: `src/trainer.py` (Testing & Analysis)

**Purpose:** Train and analyze cats without the game interface

**Key Classes:**

#### `CatTrainer` - Training automation

**Methods:**

```python
def simulate_human_interaction(self, num_iterations, interaction_type):
    """
    Run automated training
    
    Args:
        num_iterations: How many interactions to simulate
        interaction_type:
            - "positive": Always reward
            - "negative": Always punish
            - "neglect": Ignore cat
            - "mixed": Random mix (realistic)
    
    Useful for:
    - Testing learning algorithms
    - Comparing training styles
    - Analyzing AI behavior
    - Benchmarking speed
    """
```

```python
def test_decision_making(self, test_count):
    """
    Test decision-making in various contexts
    
    Shows:
    - What cat decides in each situation
    - Confidence levels
    - Emotional influences
    """
```

**Usage Example:**
```python
trainer = CatTrainer("TestCat")
trainer.simulate_human_interaction(100, "positive")
trainer.test_decision_making(10)
trainer.print_summary()
trainer.save_trained_cat("trained_cat.json")
```

---

## KEY ALGORITHMS

### Learning Algorithm

```python
# Located in: cat_brain.py -> learn_from_interaction()

for each interaction:
    # 1. Store memory
    memory = {
        'action': what_cat_did,
        'response': what_human_did,
        'reward': feedback (-1 to +1),
        'age': cat.age,
        'timestamp': now
    }
    memories.append(memory)
    
    # 2. Update behavior weight
    learned_behaviors[action] += reward * learning_rate
    
    # 3. Update emotional state
    if reward > 0:
        happiness += reward * 10
        trust += reward * 5
    else:
        happiness -= abs(reward) * 15
        trust -= abs(reward) * 3
    
    # 4. Manage memory (prevent too many memories)
    if len(memories) > max_memory:
        remove_oldest_memory()
```

**Effect:** Over time, rewarded behaviors have higher weights and are chosen more often.

### Decision Algorithm

```python
# Located in: cat_brain.py -> decide_action()

def decide_action(context):
    # 1. Start with learned weights
    weights = behavior_weights.copy()
    
    # 2. Emotional modulation
    if hunger > 70:
        weights['eat'] += 0.5
    if energy < 30:
        weights['sleep'] += 0.6
    if trust > 60 and context == 'human_nearby':
        weights['play'] += 0.3
        weights['purr'] += 0.4
    if trust < 40:
        weights['hide'] += 0.3
    
    # 3. Add personality (randomness)
    noise = random(mean=0, std=0.1)
    
    # 4. Select best action
    best_action = argmax(weights + noise)
    confidence = weights[best_action]
    
    return best_action, confidence
```

**Effect:** Creates behaviors that are:
- Based on learning (consistent)
- Responsive to needs (hungry cats eat)
- Influenced by emotion (scared cats hide)
- Unpredictable (random factor)

---

## EXTENDING THE PROJECT

### Add New Behavior

1. **Add to behavior_weights in cat_brain.py:**
```python
self.behavior_weights = {
    # ... existing behaviors
    'chase': 0.4,  # New behavior
}
```

2. **Handle in game.py:**
```python
elif event.key == pygame.K_c:  # C for chase
    self.perform_action('chase', "Cat chases toy!")
```

3. **Add effects in perform_action():**
```python
elif action == 'chase':
    self.cat.energy = max(0, self.cat.energy - 20)
    self.cat.happiness = min(100, self.cat.happiness + 10)
```

### Add New Emotional State

1. **Add to CatBrain.__init__():**
```python
self.affection = 50  # New emotional state
```

2. **Update in learn_from_interaction():**
```python
if reward > 0:
    self.affection = min(100, self.affection + reward * 8)
```

3. **Use in decide_action():**
```python
if self.affection > 70:
    action_weights['cuddle'] += 0.4
```

4. **Display in game:**
```python
def draw_stats(self, cat_status):
    # Add affection bar display
```

### Change Learning Speed

In `config.py`:
```python
# Make cat learn faster
LEARNING_RATE = 0.2  # Was 0.1
BEHAVIOR_ADJUSTMENT = 0.1  # Was 0.05

# Or slower
LEARNING_RATE = 0.05
BEHAVIOR_ADJUSTMENT = 0.025
```

### Improve Graphics

In `game.py`, `draw_cat()` method:
```python
def draw_cat(self, action, mood):
    # Current: Simple circles and shapes
    # TODO: Load PNG images for professional look
    # TODO: Add animation frames
    # TODO: Different expressions for moods
    # TODO: Tail animation based on mood
    
    # Example with images:
    cat_image = pygame.image.load(f"assets/cat_{mood}.png")
    self.screen.blit(cat_image, (self.cat_x, self.cat_y))
```

### Add Sound Effects

```python
# In __init__:
self.sounds = {
    'meow': pygame.mixer.Sound('assets/meow.wav'),
    'purr': pygame.mixer.Sound('assets/purr.wav'),
    'play': pygame.mixer.Sound('assets/play.wav'),
}

# When playing:
def perform_action(self, action, message):
    if action in self.sounds:
        self.sounds[action].play()
```

### Add Multiple Cats

```python
# In game.py:
class LittleCatGame:
    def __init__(self):
        self.cats = {}  # Dict of cat name -> CatBrain
        self.active_cat = "Whiskers"  # Currently viewing
    
    def add_cat(self, name):
        self.cats[name] = CatBrain(name)
    
    def switch_cat(self, name):
        self.active_cat = name
```

### Save Multiple Saves

```python
# Instead of single save file, use folder:
def save_cat(self, cat_name):
    os.makedirs("data/saves", exist_ok=True)
    filepath = f"data/saves/{cat_name}.json"
    self.cat.save_brain(filepath)

def load_cat(self, cat_name):
    filepath = f"data/saves/{cat_name}.json"
    self.cat.load_brain(filepath)
```

---

## DEBUGGING TIPS

### Print Debug Information

```python
# In cat_brain.py:
def decide_action(self, context):
    print(f"Context: {context}")
    print(f"Hunger: {self.hunger}, Energy: {self.energy}")
    print(f"Weights before: {self.behavior_weights}")
    # ... rest of logic
    print(f"Selected: {best_action} (confidence: {confidence})")
```

### Monitor Learning

```python
# In trainer.py:
for i in range(iterations):
    # ...
    if i % 10 == 0:
        print(f"Iteration {i}:")
        print(f"  Happiness: {cat.happiness}")
        print(f"  Trust: {cat.trust}")
        print(f"  Learned: {dict(cat.learned_behaviors)}")
```

### Check Memory

```python
# In any file:
from src.cat_brain import CatBrain

cat = CatBrain("Debug")
cat.learn_from_interaction("play", "Good!", 0.8)
cat.learn_from_interaction("sleep", "OK", 0.5)

print(f"Memories: {cat.memories}")
print(f"Learned behaviors: {dict(cat.learned_behaviors)}")
print(f"Status: {cat.get_status()}")
```

### Performance Profiling

```python
import time

start = time.time()

# Your code here
cat.decide_action()

elapsed = time.time() - start
print(f"Took {elapsed:.4f} seconds")
```

---

## CODE STYLE GUIDELINES

Follow these to keep code clean:

```python
# 1. Use descriptive names
# Good:
if cat.hunger > HUNGER_THRESHOLD:
    cat.eat()

# Bad:
if h > 70:
    c.e()

# 2. Add docstrings
def learn_from_interaction(self, action, response, reward):
    """
    Learn from human interaction.
    
    Args:
        action: What cat did
        response: Human's response
        reward: Feedback (-1 to +1)
    """

# 3. Use constants
MAX_HAPPINESS = 100  # Not magic number 100

# 4. Comment complex logic
# Adjust play weight based on energy and trust
if self.energy > 50 and self.trust > 60:
    weights['play'] += 0.3

# 5. Keep functions focused
# Do one thing well
```

---

## TESTING

### Unit Tests

```python
# Test cat brain independently
from src.cat_brain import CatBrain

def test_learning():
    cat = CatBrain()
    initial_weight = cat.learned_behaviors.get('play', 0)
    
    cat.learn_from_interaction('play', 'Good!', 1.0)
    
    final_weight = cat.learned_behaviors['play']
    assert final_weight > initial_weight, "Learning failed!"
    
    print("✓ Learning test passed")

def test_decision():
    cat = CatBrain()
    cat.hunger = 90  # Very hungry
    
    action, confidence = cat.decide_action()
    
    assert action == 'eat', f"Expected eat, got {action}"
    print("✓ Decision test passed")

if __name__ == "__main__":
    test_learning()
    test_decision()
    print("\n✓ All tests passed!")
```

### Integration Tests

```python
# Test full game flow
from src.game import LittleCatGame

def test_full_game():
    game = LittleCatGame()
    
    # Simulate interaction
    game.perform_action('play', "Played with cat!")
    
    # Check cat state changed
    status = game.cat.get_status()
    assert status['happiness'] > 50, "Happiness should increase!"
    
    print("✓ Full game test passed")
```

---

## PERFORMANCE CONSIDERATIONS

### Optimization Opportunities

```python
# 1. Vectorize calculations with NumPy
# Current (slow):
for i in range(len(weights)):
    weights[i] += noise[i]

# Better (fast):
weights = weights + noise  # NumPy arrays

# 2. Cache expensive computations
cached_action = None
cached_context = None

def decide_action(self, context):
    if context == cached_context:
        return cached_action
    # ... compute ...

# 3. Limit memory operations
# Instead of full list search:
latest_memories = memories[-20:]  # Last 20

# 4. Use local variables
# Instead of:
self.cat.brain.behaviors.weights['play'] += 0.1

# Do:
weights = self.behavior_weights
weights['play'] += 0.1
```

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code
game.run()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 functions
```

---

## VERSION HISTORY

- **v1.0** - Initial release
  - Basic cat AI
  - Simple game UI
  - Save/load system
  - Training script

- **v1.1** - Future improvements
  - Multiple cats
  - Better graphics
  - Sound effects
  - More behaviors

---

## REFERENCES & RESOURCES

### Learning Resources

1. **Reinforcement Learning**: https://en.wikipedia.org/wiki/Reinforcement_learning
2. **Pygame Documentation**: https://www.pygame.org/docs/
3. **NumPy Tutorial**: https://numpy.org/doc/stable/user/
4. **Game Loop Pattern**: Game Programming Patterns by Robert Nystrom

### Similar Projects

- OpenAI Gym - RL environments
- AI Pet Tamagotchi clones
- Neural network pet simulators

---

## CONTRIBUTING

To improve Little Cat:

1. Fork/copy the project
2. Make changes in a new branch
3. Test thoroughly
4. Document your changes
5. Submit improvements!

---

## LICENSE

This educational project is free to use and modify.

---

**Happy coding! 🐱 Build something amazing!**

For questions, check the docstrings in the source code.
Every function is documented with what it does and why.
