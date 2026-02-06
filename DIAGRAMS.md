# LITTLE CAT - VISUAL SYSTEM DIAGRAM

## Complete System Architecture

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    LITTLE CAT AI GAME                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─────────────────────────────────────────────────────────────┐
│                     GAME LAYER (game.py)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  Player Input    │  │  Rendering       │              │
│  │  • Keyboard      │  │  • Cat Display   │              │
│  │  • Commands      │  │  • Stats UI      │              │
│  └────────┬─────────┘  │  • Instructions  │              │
│           │            └──────────────────┘              │
│           │                                              │
│           └─────────────────┐                           │
│                             │                           │
│                    ┌────────▼────────┐                 │
│                    │  Game Loop      │                 │
│                    │  (30 FPS)       │                 │
│                    └────────┬────────┘                 │
│                             │                           │
└─────────────────────────────┼───────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  CAT BRAIN LAYER   │
                    │  (cat_brain.py)    │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼──────┐    ┌──────▼─────┐    ┌──────▼──────┐
    │ EMOTIONAL  │    │ LEARNING   │    │  DECISION   │
    │  STATE     │    │  SYSTEM    │    │   MAKING    │
    │            │    │            │    │             │
    │ Happiness  │    │ Behaviors  │    │ Behavior    │
    │ Hunger     │    │ Weights    │    │ Weights +   │
    │ Energy     │    │ Memories   │    │ Emotions +  │
    │ Trust      │    │ Learning   │    │ Random      │
    │            │    │ Rate       │    │             │
    └────────────┘    └────────────┘    └─────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  MEMORY SYSTEM     │
                    │  (JSON Storage)    │
                    │                    │
                    │ • Saves learned    │
                    │   behaviors        │
                    │ • Stores memories  │
                    │ • Persists state   │
                    └────────────────────┘
```

## Interaction Flow

```
HUMAN PLAYER
     │
     │ (Presses Key)
     │
     ▼
┌─────────────────────────────┐
│   INPUT HANDLING            │
│   • Decode keystroke        │
│   • Validate action         │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   PERFORM ACTION            │
│   • Modify cat state        │
│   • Calculate reward        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   CAT LEARNS                │
│   • Process feedback        │
│   • Update weights          │
│   • Adjust emotions         │
│   • Store memory            │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   DECIDE NEXT ACTION        │
│   • Weigh behaviors         │
│   • Consider emotions       │
│   • Add randomness          │
│   • Choose action           │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   RENDER UPDATE             │
│   • Draw cat                │
│   • Show stats              │
│   • Display action          │
└──────────┬──────────────────┘
           │
           ▼
    LOOP BACK TO START
```

## Learning Algorithm Detail

```
┌────────────────────────────────────────────────────────┐
│           LEARNING CYCLE (Per Interaction)             │
└────────────────────────────────────────────────────────┘

    STEP 1: ACTION TAKEN
    ┌──────────────────────┐
    │ Cat performs action: │
    │ • play               │
    │ • eat                │
    │ • sleep              │
    │ • purr               │
    │ etc.                 │
    └──────────┬───────────┘
               │
               ▼
    STEP 2: RECEIVE REWARD
    ┌──────────────────────┐
    │ Human gives reward:  │
    │ -1.0 to +1.0        │
    │ Based on:           │
    │ • Appropriateness   │
    │ • Cat's state       │
    │ • Human preference  │
    └──────────┬───────────┘
               │
               ▼
    STEP 3: UPDATE WEIGHTS
    ┌────────────────────────────────────┐
    │ learned_behaviors[action]          │
    │    += reward * learning_rate       │
    │                                    │
    │ behavior_weights[action]           │
    │    += reward * adjustment_rate     │
    │                                    │
    │ Clamp values to valid ranges       │
    └──────────┬────────────────────────┘
               │
               ▼
    STEP 4: EMOTIONAL UPDATE
    ┌────────────────────────────────────┐
    │ IF reward > 0:                     │
    │    happiness += reward * 10        │
    │    trust += reward * 5             │
    │                                    │
    │ IF reward < 0:                     │
    │    happiness -= |reward| * 15      │
    │    trust -= |reward| * 3           │
    │                                    │
    │ Clamp emotions to 0-100 range      │
    └──────────┬────────────────────────┘
               │
               ▼
    STEP 5: STORE MEMORY
    ┌────────────────────────────────────┐
    │ memories.append({                  │
    │    action,                         │
    │    human_response,                 │
    │    reward,                         │
    │    age,                            │
    │    timestamp                       │
    │ })                                 │
    │                                    │
    │ IF len(memories) > max:            │
    │    Remove oldest memory (fade)     │
    └──────────┬────────────────────────┘
               │
               ▼
        LEARNING COMPLETE
        (Influences future decisions)
```

## Decision Making Process

```
┌──────────────────────────────────────────────────────────────┐
│             DECISION ALGORITHM (cat.decide_action)           │
└──────────────────────────────────────────────────────────────┘

    INPUT: Current Context (human_nearby, alone, etc.)
    
    ┌─────────────────────────────────────────┐
    │ STEP 1: Base Weights                    │
    │                                         │
    │ action_weights = behavior_weights.copy()│
    │                                         │
    │ Start with learned tendencies           │
    └──────────┬────────────────────────────┘
               │
               ▼
    ┌─────────────────────────────────────────┐
    │ STEP 2: Emotional Adjustments           │
    │                                         │
    │ if hunger > 70:                         │
    │     weights[eat] += 0.5                 │
    │                                         │
    │ if energy < 30:                         │
    │     weights[sleep] += 0.6               │
    │                                         │
    │ if trust > 60 and human_nearby:         │
    │     weights[play] += 0.3                │
    │     weights[purr] += 0.4                │
    │                                         │
    │ if trust < 40:                          │
    │     weights[hide] += 0.3                │
    │                                         │
    │ Emotions override learned behaviors     │
    └──────────┬────────────────────────────┘
               │
               ▼
    ┌─────────────────────────────────────────┐
    │ STEP 3: Add Personality (Randomness)    │
    │                                         │
    │ noise = random_gaussian(0, 0.1)         │
    │ weights_with_noise = weights + noise    │
    │                                         │
    │ Cats aren't 100% predictable!           │
    └──────────┬────────────────────────────┘
               │
               ▼
    ┌─────────────────────────────────────────┐
    │ STEP 4: Select Best Action              │
    │                                         │
    │ best_action = argmax(weights_with_noise)│
    │ confidence = weights[best_action]       │
    │                                         │
    │ Pick highest weighted action            │
    └──────────┬────────────────────────────┘
               │
               ▼
    OUTPUT: (action, confidence)
    
    Example outputs:
    • ("play", 0.72) - High confidence to play
    • ("sleep", 0.55) - Moderate confidence to sleep
    • ("hide", 0.38) - Low confidence to hide
```

## Emotional State Dynamics

```
┌─────────────────────────────────────────────────────┐
│           EMOTIONAL STATE CHANGES                   │
└─────────────────────────────────────────────────────┘

HAPPINESS
    │
100 │ ┏━━━━━━━━━━━━━━━━━━┓
    │ ┃ Very Happy       ┃
 80 │ ┣━━━━━━━━━━━━━━━━━━┫ Play + Affection increases
    │ ┃ Happy            ┃
 60 │ ┣━━━━━━━━━━━━━━━━━━┫ Neglect decreases
    │ ┃ Content          ┃
 40 │ ┣━━━━━━━━━━━━━━━━━━┫ 
    │ ┃ Unhappy          ┃ Punishment heavily decreases
 20 │ ┣━━━━━━━━━━━━━━━━━━┫
    │ ┃ Very Unhappy     ┃
  0 │ ┗━━━━━━━━━━━━━━━━━━┛
    └─────────────────────────────────────────────────


HUNGER
    │
100 │ ┏━━━━━━━━━━━━━━━━━━┓ Starving (cat must eat!)
    │ ┃ Very Hungry      ┃
 80 │ ┣━━━━━━━━━━━━━━━━━━┫ Hungry (priority is food)
    │ ┃ Hungry           ┃
 60 │ ┣━━━━━━━━━━━━━━━━━━┫ Moderate (can focus on play)
    │ ┃ Satisfied        ┃
 30 │ ┣━━━━━━━━━━━━━━━━━━┫ Just fed
    │ ┃ Full             ┃
  0 │ ┗━━━━━━━━━━━━━━━━━━┛ (Not possible - increases naturally)
    └─────────────────────────────────────────────────

    Natural increase: ~1.5 per game hour
    Feed action: -30 hunger


ENERGY
    │
100 │ ┏━━━━━━━━━━━━━━━━━━┓ Fully rested
    │ ┃ Energetic        ┃ Can play, run, explore
 70 │ ┣━━━━━━━━━━━━━━━━━━┫ 
    │ ┃ Normal           ┃ Balanced state
 40 │ ┣━━━━━━━━━━━━━━━━━━┫ Getting tired
    │ ┃ Tired            ┃ Prefers sleep
 10 │ ┣━━━━━━━━━━━━━━━━━━┫ Very exhausted
    │ ┃ Exhausted        ┃ (cat forces sleep)
  0 │ ┗━━━━━━━━━━━━━━━━━━┛ Sleeping
    └─────────────────────────────────────────────────

    Natural drain: ~2 per active hour
    Play action: -15 energy
    Sleep restores: +40 energy


TRUST
    │
100 │ ┏━━━━━━━━━━━━━━━━━━┓ Complete trust
    │ ┃ Total Trust      ┃ Cat seeks affection
 70 │ ┣━━━━━━━━━━━━━━━━━━┫ 
    │ ┃ Trusting         ┃ Cat plays with you
 50 │ ┣━━━━━━━━━━━━━━━━━━┫ Neutral
    │ ┃ Neutral          ┃ Cat is cautious
 30 │ ┣━━━━━━━━━━━━━━━━━━┫ Low trust
    │ ┃ Distrustful      ┃ Cat avoids you
  0 │ ┗━━━━━━━━━━━━━━━━━━┛ Complete distrust
    └─────────────────────────────────────────────────

    Builds slowly: +5 per positive interaction
    Decreases faster: -3 per negative interaction
    Pet/affection: +20 trust per action
```

## File I/O Flow

```
┌──────────────────────────────────────────────────┐
│            SAVE/LOAD SYSTEM                      │
└──────────────────────────────────────────────────┘

SAVING CAT BRAIN (Press E in game)
├── Export to: data/cat_brain.json
│
├── Saves:
│   ├── Cat name
│   ├── Age in days
│   ├── Emotional state (happiness, hunger, energy, trust)
│   ├── Behavior weights (all 6 behaviors)
│   ├── Learned behaviors (recent learning)
│   └── Last 20 memories
│
└── Can be backed up / transferred


LOADING CAT BRAIN (Press L in game)
├── Read from: data/cat_brain.json
│
├── Restores:
│   ├── Cat name
│   ├── Age in days
│   ├── Emotional state
│   ├── Behavior weights
│   ├── Learned behaviors
│   └── Memory history
│
└── Cat continues from where it left off


EXAMPLE JSON STRUCTURE:
{
  "name": "Whiskers",
  "age": 2.5,
  "emotional_state": {
    "happiness": 75,
    "hunger": 35,
    "energy": 60,
    "trust": 65
  },
  "behavior_weights": {
    "play": 0.65,
    "sleep": 0.35,
    "eat": 0.45,
    "purr": 0.72,
    "scratch": 0.38,
    "hide": 0.15
  },
  "learned_behaviors": {
    "play": 0.25,
    "purr": 0.35,
    "sleep": -0.10
  },
  "memories": [
    {
      "action": "play",
      "response": "Human played with cat",
      "reward": 0.8,
      "age": 2.4
    },
    ...
  ]
}
```

## Training Timeline Example

```
DAY 1: New Kitten
├── All behaviors equally weighted (0.3-0.5)
├── Random action selection
├── High variance in decisions
├── Building first memories
└── Trust: 30 (cautious)

DAY 3: Learning Phase
├── Patterns starting to form
├── Behaviors getting tweaked by rewards
├── More predictable actions
├── Emotional responses developing
└── Trust: 45 (warming up)

DAY 7: Personality Emerging
├── Clear behavioral preferences
├── Learned patterns visible
├── Consistent mood shifts
├── Emotional reactions established
└── Trust: 65 (friendly)

WEEK 2+: Mature Cat
├── Stable learned behaviors
├── Highly predictable patterns
├── Strong personality traits
├── Emotional depth
└── Trust: 80+ (bonded)

MONTH+: Evolved Companion
├── Optimized behavior strategy
├── Complex decision making
├── Unique individual personality
├── Deep emotional bonds
└── Trust: 90+ (best friend)
```

---

This visual guide helps understand how all the pieces of the Little Cat AI work together!
