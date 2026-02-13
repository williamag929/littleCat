# 🤖 LITTLE CAT AGENT GUIDE

## What Are the Agents in Little Cat?

Little Cat includes **TWO** different types of agents, each with unique capabilities:

1. **AI Cat Agent** - A learning pet that adapts to your behavior
2. **Screen Agent** - An automated player that can control games using computer vision

---

## 🐱 AGENT 1: AI Cat Learning Agent

### What It Does
The AI Cat is an **autonomous learning agent** that:
- Learns from your interactions using reinforcement learning
- Makes its own decisions based on emotional state
- Develops a unique personality over time
- Remembers past interactions and adapts behavior
- Operates similar to a simple neural network

### How It Works
```
You interact → Cat receives reward/punishment → Cat learns → Behavior changes
```

The cat agent continuously:
1. **Observes** its emotional state (happiness, hunger, energy, trust)
2. **Decides** what action to take based on learned patterns
3. **Learns** from your feedback (rewards increase behavior weights)
4. **Adapts** its personality over time

### Key Capabilities
- ✅ Autonomous decision-making
- ✅ Learning from feedback
- ✅ Memory storage (up to 100 interactions)
- ✅ Emotional state management
- ✅ Personality development
- ✅ Save/Load state persistence

### How to Use
```bash
# Run the AI cat game
python src/game.py

# Train the AI cat using scripts
python src/trainer.py
```

### Use Cases
- Educational tool for learning AI/ML concepts
- Interactive pet simulation
- Reinforcement learning demonstration
- Game AI development practice
- Behavioral psychology experiments

---

## 🎮 AGENT 2: Screen Agent (Computer Vision Player)

### What It Does
The Screen Agent is an **automated gameplay agent** that:
- Uses computer vision to detect game elements on your screen
- Automatically controls keyboard inputs to play games
- Learns optimal control parameters through adaptive algorithms
- Works with any game that has visible colored objects

### How It Works
```
Calibrate → Detect objects via color → Calculate error → Control keys → Learn timing
```

The screen agent:
1. **Captures** screen regions using MSS (screen capture)
2. **Detects** objects using color-based computer vision (OpenCV)
3. **Calculates** positioning errors between objects
4. **Controls** keyboard to correct errors
5. **Adapts** timing parameters for better performance

### Key Capabilities
- ✅ Real-time screen capture and analysis
- ✅ Color-based object detection
- ✅ Adaptive control with learning
- ✅ Keyboard automation (PyAutoGUI)
- ✅ Calibration system for different games
- ✅ Visual preview window

### How to Use

#### Step 1: Calibrate the Agent
```bash
python src/screen_agent_poc.py --calibrate
```

**Calibration Process:**
1. Move mouse to **TOP-LEFT** of game area → Press Enter
2. Move mouse to **BOTTOM-RIGHT** of game area → Press Enter
3. Hover over the **BALL** → Press Enter to sample color
4. Hover over the **PADDLE** → Press Enter to sample color
5. Preview window appears - Press **Q** to accept, **R** to redo, **X** to exit

#### Step 2: Play Automatically
```bash
# Use saved calibration
python src/screen_agent_poc.py --play

# Or calibrate and play in one go
python src/screen_agent_poc.py
```

#### Advanced Options
```bash
# Disable preview window for better performance
python src/screen_agent_poc.py --play --no-preview

# Recalibrate
python src/screen_agent_poc.py --calibrate
```

### Configuration
The agent automatically saves calibration to `data/screen_agent.json` which includes:

- **Game region** (screen coordinates)
- **Object colors** (ball and paddle RGB values)
- **Control parameters**:
  - `tolerance`: Color detection sensitivity (default: 30)
  - `move_key`: Keys to control left/right (default: ["left", "right"])
  - `deadzone`: Minimum error before moving (default: 6 pixels)
  - `kp`: Proportional gain for control speed (default: 0.001)
  - `adaptive_rate`: Learning rate for auto-tuning (default: 0.03)

### Technical Details

**Computer Vision:**
- Color masking with tolerance
- Morphological operations (erosion/dilation)
- Contour detection
- Centroid calculation

**Control Algorithm:**
```python
error = ball_x - paddle_x
if error > deadzone:
    press_key("right", adaptive_duration(error))
elif error < -deadzone:
    press_key("left", adaptive_duration(error))
```

**Adaptive Learning:**
- Tracks average error over 120 frames
- Increases control gain if error is high
- Decreases control gain if error is low
- Self-optimizes for different game speeds

### Use Cases
- Automated game playing (Pong, Breakout, similar games)
- Computer vision demonstrations
- Control system experimentation
- Bot development practice
- Game testing automation

---

## 🆚 Comparison: Little Cat Agents vs VS Code Agents

### VS Code Agents (like GitHub Copilot)
**What they do:**
- Code completion and suggestions
- Code understanding and explanation
- Automated refactoring
- Bug detection and fixes
- Work **within your IDE**

**How they work:**
- Large language models (LLMs)
- Code context analysis
- Pattern recognition from massive datasets

### Little Cat AI Agent
**What it does:**
- Learning pet simulation
- Behavioral adaptation
- Decision-making based on emotional state
- Work **as a standalone game**

**How it works:**
- Reinforcement learning
- Weighted behavior system
- Memory and state management

### Little Cat Screen Agent
**What it does:**
- Automated gameplay
- Computer vision detection
- Adaptive control
- Work **with any on-screen game**

**How it works:**
- Screen capture + OpenCV
- Color-based detection
- Proportional control with learning

### Key Differences

| Feature | VS Code Agents | Little Cat AI Agent | Little Cat Screen Agent |
|---------|---------------|-------------------|----------------------|
| **Purpose** | Code assistance | Pet simulation | Game automation |
| **Technology** | LLMs | Reinforcement learning | Computer vision |
| **Learning** | Pre-trained | Real-time adaptive | Adaptive control |
| **Interface** | IDE integration | Game window | Screen capture |
| **Autonomy** | Suggests actions | Makes decisions | Full automation |

---

## 🎯 What You Can Do With Little Cat Agents

### With the AI Cat Agent

**Learning & Education:**
- ✅ Learn reinforcement learning concepts
- ✅ Understand state machines
- ✅ Explore behavioral psychology
- ✅ Study neural network basics
- ✅ Practice AI algorithm implementation

**Experimentation:**
- ✅ Train different cat personalities
- ✅ Compare training approaches
- ✅ Modify learning parameters
- ✅ Add new behaviors
- ✅ Create custom reward systems

**Development:**
- ✅ Extend the game with new features
- ✅ Implement advanced AI algorithms
- ✅ Add multiplayer cat interactions
- ✅ Create cat breeding systems
- ✅ Build web-based versions

### With the Screen Agent

**Game Automation:**
- ✅ Auto-play Pong-like games
- ✅ Auto-play Breakout-like games
- ✅ Test game difficulty
- ✅ Demonstrate AI control
- ✅ Create game bots

**Learning & Research:**
- ✅ Study computer vision techniques
- ✅ Learn control systems
- ✅ Practice OpenCV
- ✅ Understand adaptive algorithms
- ✅ Explore screen automation

**Extension Ideas:**
- ✅ Add more sophisticated AI (neural networks)
- ✅ Support multiple object types
- ✅ Implement game state recognition
- ✅ Add predictive movement
- ✅ Create multi-game profiles

---

## 🚀 Quick Start Guide

### For AI Cat Agent
```bash
# Install dependencies
pip install -r requirements.txt

# Play the game
python src/game.py

# Train automatically
python src/trainer.py
```

### For Screen Agent
```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Setup and play
python src/screen_agent_poc.py --calibrate
python src/screen_agent_poc.py --play
```

---

## 📚 Learning Path

### Beginner (Just Want to Use It)
1. Run `python src/game.py` → Play with AI cat
2. Run `python src/screen_agent_poc.py` → Auto-play games
3. Experiment with different approaches
4. Save your favorite cats

### Intermediate (Understand How It Works)
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for AI cat details
2. Study `src/cat_brain.py` for learning algorithm
3. Study `src/screen_agent_poc.py` for CV algorithm
4. Modify `src/config.py` to change parameters
5. Run `src/trainer.py` to see learning patterns

### Advanced (Extend and Improve)
1. Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
2. Implement new AI algorithms
3. Add neural networks (TensorFlow/PyTorch)
4. Improve computer vision (deep learning detection)
5. Create new game modes
6. Add multiplayer features

---

## 🔧 Configuration Examples

### AI Cat Agent
Edit `src/config.py`:
```python
# Make cat learn faster
LEARNING_RATE = 0.2  # Default: 0.1

# Make cat more trusting
INITIAL_TRUST = 50  # Default: 30

# Add new behaviors
BEHAVIOR_WEIGHTS = {
    'play': 0.5,
    'sleep': 0.3,
    # Add your own...
}
```

### Screen Agent
Edit `data/screen_agent.json`:
```json
{
  "config": {
    "tolerance": 30,      // Color detection sensitivity
    "deadzone": 6,        // Minimum error before action
    "kp": 0.001,         // Control speed
    "adaptive_rate": 0.03 // Learning speed
  }
}
```

---

## 🎮 Compatible Games for Screen Agent

The screen agent works best with games that have:
- ✅ Clear, solid-colored objects (ball, paddle)
- ✅ Horizontal movement control
- ✅ Predictable physics
- ✅ Visible game area

**Recommended games:**
- Pong
- Breakout
- Arkanoid
- Simple paddle games
- Any game with colored moving objects

**To adapt for new games:**
1. Calibrate with `--calibrate`
2. Sample the object colors accurately
3. Adjust `move_key` in config if needed
4. Fine-tune `tolerance` and `deadzone`

---

## 💡 Tips for Success

### AI Cat Agent
- Be consistent with interactions
- Give clear positive/negative feedback
- Wait several days for personality to emerge
- Save regularly (Press E in game)
- Try different training styles

### Screen Agent
- Choose games with high contrast colors
- Calibrate in good lighting conditions
- Start with slower-paced games
- Monitor the preview window initially
- Let it learn - performance improves over time

---

## 🐛 Troubleshooting

### AI Cat Not Learning
- Ensure 50+ consistent interactions
- Check that rewards are appropriate
- Verify `LEARNING_RATE` in config
- Review console output for errors

### Screen Agent Not Detecting
- Recalibrate colors
- Increase `tolerance` in config
- Check lighting conditions
- Verify game window is visible
- Ensure colors are distinct

### Screen Agent Not Moving Correctly
- Adjust `deadzone` (too sensitive? increase it)
- Modify `kp` (too slow? increase it)
- Check `move_key` matches game controls
- Verify game window has focus

---

## 🎓 Educational Value

### What You Learn

**From AI Cat Agent:**
- Reinforcement learning principles
- State machine design
- Behavioral adaptation
- Memory systems
- Decision-making algorithms

**From Screen Agent:**
- Computer vision basics
- Color detection and masking
- Control systems
- Adaptive algorithms
- Screen automation

**Programming Skills:**
- Python game development (Pygame)
- OpenCV image processing
- PyAutoGUI automation
- JSON data persistence
- Object-oriented design

---

## 🔮 Extension Ideas

### AI Cat Agent
- [ ] Multiple cats that interact
- [ ] Neural network decision-making
- [ ] Genetic algorithm breeding
- [ ] Complex emotional models
- [ ] Voice/sound interaction

### Screen Agent
- [ ] Deep learning object detection (YOLO, etc.)
- [ ] Predictive movement (anticipate ball position)
- [ ] Multi-object tracking
- [ ] Game state recognition
- [ ] Strategy learning (not just reactive control)

---

## 📖 Related Documentation

- [README.md](README.md) - Main project documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - AI system details
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Code explanation
- [QUICKSTART.txt](QUICKSTART.txt) - Quick start guide
- [INDEX.md](INDEX.md) - Documentation index

---

## 🎉 Summary

**You have TWO powerful agents:**

1. **AI Cat** - An autonomous learning pet that adapts to your behavior
2. **Screen Agent** - An automated player using computer vision

**Both agents demonstrate different AI techniques:**
- Learning from experience (Cat)
- Vision and control (Screen Agent)

**Both are fully functional and ready to use!**

### Get Started Now:
```bash
# Try the AI cat
python src/game.py

# Try the screen agent (automated gameplay)
python src/screen_agent_poc.py --calibrate
python src/screen_agent_poc.py --play
```

---

**🤖 Welcome to the world of AI agents!** 

Unlike VS Code agents that help you write code, Little Cat agents are **complete AI systems** you can **learn from**, **experiment with**, and **extend**. They're educational projects that teach you how AI really works, from the ground up!

Happy experimenting! 🐱🎮
