# 🐱 Little Cat - AI Pet Learning Game

A Python-based virtual pet game featuring an artificial intelligence cat that **learns and grows** from your interactions!

## 🤖 Two AI Agents in One Project!

This project includes **two different AI agents**:

1. **🐱 AI Cat Agent** - An autonomous learning pet that adapts to your behavior using reinforcement learning
2. **🎮 Screen Agent** - An automated game player using computer vision to control games

**📌 [WHAT_CAN_I_DO.md](WHAT_CAN_I_DO.md) - Quick overview of what you can do with these agents!**  
**📖 [AGENT_GUIDE.md](AGENT_GUIDE.md) - Complete agent documentation and capabilities**

## 🎮 Game Concept

Meet your digital cat companion that:
- **Learns** from your interactions using a neural-inspired brain system
- **Makes decisions** based on learned behaviors and emotional state
- **Grows over time** with an age system
- **Remembers** previous interactions and builds trust
- **Adapts** its behavior based on positive and negative feedback
- **Has emotions**: happiness, hunger, energy, and trust levels

## 🧠 How the AI Works

### Learning System
The cat has a learning brain with:

1. **State Memory** - Emotional states (happiness, hunger, energy, trust)
2. **Behavioral Learning** - Learns which actions are rewarded by the human
3. **Pattern Recognition** - Adapts behavior based on past interactions
4. **Decision Making** - Chooses actions based on current needs and learned patterns
5. **Memory System** - Stores up to 100 memories of interactions that fade over time

### The Cat Brain Algorithm
```
1. Observe current emotional state
2. Receive feedback from human interaction
3. Update behavior weights based on reward
4. Decide next action using:
   - Learned behavior patterns
   - Current emotional needs (hunger, fatigue)
   - Trust level in the human
   - Random personality traits
5. Repeat and improve over time
```

## 🎮 Screen Agent (Automated Game Player)

In addition to the AI cat, this project includes a **Screen Agent** that can automatically play games!

**Key Features:**
- **Computer vision** using OpenCV to detect game elements
- **Automated keyboard control** to play the game
- **Adaptive learning** to improve performance over time
- **Works with any Pong/Breakout-style game**

**Quick Start:**
```bash
# Calibrate the agent for your game
python src/screen_agent_poc.py --calibrate

# Let it play automatically
python src/screen_agent_poc.py --play
```

**See [AGENT_GUIDE.md](AGENT_GUIDE.md) for complete screen agent documentation!**

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. **Clone/Navigate to the project:**
```bash
cd c:\projects\littleCat
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the game:**
```bash
python src/game.py
```

## 🎮 How to Play

### Controls

| Key | Action | Effect |
|-----|--------|--------|
| **P** | Play | Increases happiness, costs energy |
| **F** | Feed | Reduces hunger, increases happiness |
| **S** | Sleep | Restores energy, increases hunger |
| **T** | Pet/Affection | Increases trust and happiness |
| **H** | Hide | Cat hides (punishment decreases happiness) |
| **R** | Rest | Slight energy restore |
| **E** | Export Brain | Saves cat's learned state |
| **L** | Load Brain | Loads previously saved cat |
| **ESC** | Quit | Exit game (auto-saves) |

### Cat Emotional States

**Happiness** 😸
- Increases when played with, fed, and petted
- Decreases when lonely or ignored

**Hunger** 🍖
- Increases over time naturally
- Decreases when fed
- Affects ability to play

**Energy** ⚡
- Decreases when active
- Restores through sleep
- Low energy forces sleep

**Trust** 💕
- Increases through affection and positive interactions
- Decreases through neglect or punishment
- Affects cat's willingness to interact

## 📊 Learning Progress

Watch your cat's behavior change as it learns:

1. **Day 1-3**: Random exploration phase
2. **Day 4-7**: Pattern recognition begins
3. **Week 2+**: Predictable learned behavior emerges
4. **Month 1+**: Personality solidifies, stronger trust bonds form

## 💾 Saving and Loading

The game automatically saves your cat's brain to `data/cat_brain.json` when you exit.

**Your cat retains:**
- Age and development stage
- Emotional state
- Learned behavior weights
- Recent memory (last 20 interactions)

When you load the game again, your cat will remember you!

## 🏗️ Project Structure

```
littleCat/
├── src/
│   ├── game.py           # Main game loop and UI (Pygame)
│   └── cat_brain.py      # AI learning system
├── data/
│   └── cat_brain.json    # Saved cat state (auto-generated)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Customization

### Modify Cat Parameters

Edit `src/cat_brain.py`:

```python
# Initial emotional state
self.happiness = 50
self.hunger = 30
self.energy = 70
self.trust = 30

# Learning rate
self.learned_behaviors[action] += reward * 0.1  # Increase 0.1 for faster learning

# Emotional decay
self.happiness = max(40, self.happiness - (0.5 * time_delta))  # Adjust values
```

### Change Visual Appearance

Edit `src/game.py` - `GameDisplay.draw_cat()` method to modify cat appearance.

## 📈 Future Enhancements

- [ ] Multiple cats that interact with each other
- [ ] Breeding system to create "kittens"
- [ ] More complex neural network (TensorFlow integration)
- [ ] Evolved behaviors through genetic algorithms
- [ ] Sound effects and animations
- [x] Cat toys and interactive items
- [ ] Achievement system
- [ ] Leaderboard for "smartest cats"
- [ ] Web-based multiplayer version

## 🐛 Troubleshooting

**Game won't start:**
```bash
# Make sure pygame is installed
pip install pygame --upgrade
```

**Cat memory not loading:**
- Check that `data/` folder exists
- Delete `cat_brain.json` and start fresh

**Low FPS:**
- Reduce `FPS` value in `src/game.py`
- Close other applications

## 📚 Learning Resources

This project demonstrates:
- **Reinforcement Learning**: Reward-based behavior training
- **State Machines**: Emotional and behavioral states
- **Pattern Recognition**: Learning from past interactions
- **Game Development**: Pygame basics
- **AI Decision Making**: Simple neural-inspired algorithms

## 🎓 Educational Value

Perfect for learning:
- Python game development
- Basic AI/ML concepts
- Behavioral simulation
- State management in games
- File I/O and data persistence

## 📝 License

This project is open source and free to use for educational purposes.

---

**Happy playing! 🐱** Your cat is waiting to learn and bond with you!

*Remember: The more you interact with your cat, the smarter and more personalized it becomes!*
