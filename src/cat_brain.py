"""
Cat Brain - Learning and Decision Making System
Simulates a cat's learning capacity and decision-making based on interactions.
"""

import numpy as np
from collections import defaultdict, deque
import json
from datetime import datetime
import hashlib


class CatBrain:
    """Neural-inspired learning system for the cat pet."""
    
    def __init__(self, name="Whiskers"):
        self.name = name
        self.age = 0  # Days
        
        # Emotional states (0-100 scale)
        self.happiness = 50
        self.hunger = 30
        self.energy = 70
        self.trust = 30
        
        # Learning system - memories and patterns
        self.max_memory = 100  # Limit learning buffer
        self.memories = deque(maxlen=self.max_memory)  # Store interactions with automatic size limit
        self.learned_behaviors = defaultdict(float)  # action -> success rate
        self.action_history = []  # Track recent actions

        # Q-learning (lightweight RL)
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.alpha = 0.2
        self.gamma = 0.9
        self.epsilon = 0.2
        self.last_state = None
        self.last_action = None

        # Personality traits (0-1 range)
        self.personality = self._generate_personality(self.name)

        # Trick training progression
        self.trick_level = 1
        self.trick_xp = 0

        # Achievements (stored as a set for efficiency)
        self.achievements = set()
        
        # Brain weights (simple neural-inspired weights)
        self.behavior_weights = {
            'play': 0.5,
            'sleep': 0.3,
            'eat': 0.4,
            'purr': 0.5,
            'scratch': 0.4,
            'hide': 0.2,
            'groom': 0.3,
            'talk': 0.3,
            'train': 0.35,
            'rest': 0.25,
        }
        
        # Cache personality modifiers for performance
        self._personality_modifiers = None
        
    def learn_from_interaction(self, action, human_response, reward):
        """
        Learn from human interactions.
        
        Args:
            action: What the cat did (str)
            human_response: What the human did in response (str)
            reward: Positive/negative feedback (-1 to 1)
        """
        # Record memory
        memory = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'response': human_response,
            'reward': reward,
            'age': self.age
        }
        self.memories.append(memory)
        # deque automatically maintains maxlen, no manual pop needed
        
        # Update learned behavior weights
        self.learned_behaviors[action] += reward * 0.1
        self.learned_behaviors[action] = np.clip(self.learned_behaviors[action], -1, 1)
        
        # Update behavior weights based on learning
        if action in self.behavior_weights:
            self.behavior_weights[action] += reward * 0.05
            self.behavior_weights[action] = np.clip(self.behavior_weights[action], 0, 1)
        
        # Emotional update based on reward
        if reward > 0:
            self.happiness = min(100, self.happiness + reward * 10)
            self.trust = min(100, self.trust + reward * 5)
        else:
            self.happiness = max(0, self.happiness + reward * 15)
            self.trust = max(0, self.trust + reward * 3)

        # Trick training progression
        if action == 'train':
            self._apply_trick_progress(reward)

        # Q-learning update
        current_state = self._get_state()
        if self.last_state is not None and self.last_action is not None:
            self._update_q(self.last_state, self.last_action, reward, current_state)
        self.last_state = current_state
        self.last_action = action
    
    def decide_action(self, context="neutral"):
        """
        Decide what action to take based on current state and learning.
        Uses learned behaviors and emotional state.
        
        Args:
            context: Current situation (str) - 'human_nearby', 'alone', 'food_available'
        
        Returns:
            Next action (str) and confidence (float)
        """
        # Adjust weights based on emotional state
        action_weights = self.behavior_weights.copy()
        
        # Apply cached personality influences (subtle bias)
        personality_mods = self._get_personality_modifiers()
        for action, modifier in personality_mods.items():
            if action in action_weights:
                action_weights[action] = min(1.0, action_weights.get(action, 0.2) + modifier)

        # Hunger influences eating behavior
        if self.hunger > 70:
            action_weights['eat'] = min(1.0, action_weights['eat'] + 0.5)
        
        # Low energy influences sleep
        if self.energy < 30:
            action_weights['sleep'] = min(1.0, action_weights['sleep'] + 0.6)
        
        # Trust and happiness influence play/purr
        if self.trust > 60 and context == 'human_nearby':
            action_weights['play'] = min(1.0, action_weights['play'] + 0.3)
            action_weights['purr'] = min(1.0, action_weights['purr'] + 0.4)
            action_weights['talk'] = min(1.0, action_weights.get('talk', 0.2) + 0.2)
            action_weights['train'] = min(1.0, action_weights.get('train', 0.2) + 0.15)
        
        # Fear/low trust influences hiding
        if self.trust < 40:
            action_weights['hide'] = min(1.0, action_weights['hide'] + 0.3)
        
        # Add some randomness (cats are unpredictable!) - optimized to avoid unnecessary array
        weighted_actions = {
            action: weight + np.random.normal(0, 0.1)
            for action, weight in action_weights.items()
        }
        
        # Q-learning: epsilon-greedy action selection
        state = self._get_state(context)
        actions = list(action_weights.keys())
        use_explore = np.random.random() < self.epsilon

        if not use_explore:
            q_values = self.q_table.get(state, {})
            if q_values:
                best_action = max(actions, key=lambda a: q_values.get(a, 0.0))
                confidence = np.clip(q_values.get(best_action, 0.0), 0, 1)
            else:
                best_action = max(weighted_actions, key=weighted_actions.get)
                confidence = np.clip(weighted_actions[best_action], 0, 1)
        else:
            best_action = np.random.choice(actions)
            confidence = 0.2

        self.last_state = state
        self.last_action = best_action
        return best_action, confidence
    
    def update_state(self, time_delta=1):
        """Update cat's internal state over time."""
        # Age increases
        self.age += time_delta / 24  # time_delta in hours
        
        # Natural decrease in energy when not sleeping
        if self.energy > 0:
            self.energy = max(0, self.energy - (2 * time_delta))
        
        # Hunger increases over time
        self.hunger = min(100, self.hunger + (1.5 * time_delta))
        
        # Happiness slightly decreases if lonely
        if self.happiness > 40:
            self.happiness = max(40, self.happiness - (0.5 * time_delta))
        
        # Energy recovery during sleep (handled in game loop)
    
    def get_status(self):
        """Get current cat status."""
        return {
            'name': self.name,
            'age_days': round(self.age, 1),
            'happiness': round(self.happiness),
            'hunger': round(self.hunger),
            'energy': round(self.energy),
            'trust': round(self.trust),
            'mood': self._get_mood(),
            'behavior_patterns': dict(self.learned_behaviors),
            'memories_count': len(self.memories),
            'personality': self.personality,
            'trick_level': self.trick_level,
            'trick_xp': round(self.trick_xp, 1),
            'achievements_count': len(self.achievements)
        }

    def _generate_personality(self, name):
        """Generate deterministic personality traits from the cat's name."""
        digest = hashlib.md5(name.encode("utf-8")).hexdigest()
        values = [int(digest[i:i+2], 16) / 255 for i in range(0, 8, 2)]
        return {
            'playful': values[0],
            'calm': values[1],
            'curious': values[2],
            'social': values[3],
        }
    
    def _get_personality_modifiers(self):
        """Get cached personality modifiers for performance.
        
        Personality is immutable after initialization (only changes on load_brain),
        so caching these computed values is safe. Cache is invalidated on load_brain.
        """
        if self._personality_modifiers is None:
            playful = self.personality.get('playful', 0.5)
            calm = self.personality.get('calm', 0.5)
            curious = self.personality.get('curious', 0.5)
            social = self.personality.get('social', 0.5)
            
            self._personality_modifiers = {
                'play': playful * 0.15,
                'sleep': calm * 0.1,
                'rest': calm * 0.1,
                'talk': social * 0.12,
                'purr': social * 0.1,
                'train': (social + curious) * 0.08,
                'groom': calm * 0.08,
            }
        return self._personality_modifiers

    def _apply_trick_progress(self, reward):
        """Progress trick training based on reward."""
        if reward <= 0:
            return
        self.trick_xp += reward * 5
        needed = max(5, self.trick_level * 8)
        if self.trick_xp >= needed:
            self.trick_level += 1
            self.trick_xp = 0
    
    def _get_mood(self):
        """Determine cat's mood based on emotional state."""
        if self.happiness > 75:
            return "HAPPY 😸"
        elif self.happiness > 50:
            return "CONTENT 😼"
        elif self.happiness > 25:
            return "NEUTRAL 😿"
        else:
            return "GRUMPY 😾"

    def _get_state(self, context="neutral"):
        """Discretize emotional state into a compact RL state."""
        return (
            self._bin(self.happiness),
            self._bin(self.hunger),
            self._bin(self.energy),
            self._bin(self.trust),
            context,
        )

    def _bin(self, value, bins=4):
        """Bucket a 0-100 value into bins."""
        step = 100 / bins
        return int(min(bins - 1, value // step))

    def _update_q(self, state, action, reward, next_state):
        """Q-learning update step."""
        current_q = self.q_table[state][action]
        next_best = 0.0
        if self.q_table.get(next_state):
            next_best = max(self.q_table[next_state].values())
        td_target = reward + self.gamma * next_best
        self.q_table[state][action] = current_q + self.alpha * (td_target - current_q)
    
    def save_brain(self, filepath):
        """Save cat's learned state to file."""
        data = {
            'name': self.name,
            'age': self.age,
            'emotional_state': {
                'happiness': self.happiness,
                'hunger': self.hunger,
                'energy': self.energy,
                'trust': self.trust,
            },
            'behavior_weights': self.behavior_weights,
            'learned_behaviors': dict(self.learned_behaviors),
            'memories': list(self.memories)[-20:],  # Convert deque to list, keep last 20 memories
            'personality': self.personality,
            'trick_level': self.trick_level,
            'trick_xp': self.trick_xp,
            'achievements': list(self.achievements),
            'q_learning': {
                'alpha': self.alpha,
                'gamma': self.gamma,
                'epsilon': self.epsilon,
                'q_table': {json.dumps(k): dict(v) for k, v in self.q_table.items()},
            }
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_brain(self, filepath):
        """Load cat's learned state from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.name = data.get('name', self.name)
            self.age = data.get('age', 0)
            
            emotional = data.get('emotional_state', {})
            self.happiness = emotional.get('happiness', 50)
            self.hunger = emotional.get('hunger', 30)
            self.energy = emotional.get('energy', 70)
            self.trust = emotional.get('trust', 30)
            
            self.behavior_weights = data.get('behavior_weights', self.behavior_weights)
            self.learned_behaviors = defaultdict(float, data.get('learned_behaviors', {}))
            # Convert loaded memories list to deque with maxlen
            loaded_memories = data.get('memories', [])
            self.memories = deque(loaded_memories, maxlen=self.max_memory)
            self.personality = data.get('personality', self.personality)
            # Invalidate cached personality modifiers after loading
            self._personality_modifiers = None
            self.trick_level = data.get('trick_level', 1)
            self.trick_xp = data.get('trick_xp', 0)
            self.achievements = set(data.get('achievements', []))

            q_learning = data.get('q_learning', {})
            self.alpha = q_learning.get('alpha', self.alpha)
            self.gamma = q_learning.get('gamma', self.gamma)
            self.epsilon = q_learning.get('epsilon', self.epsilon)
            q_raw = q_learning.get('q_table', {})
            self.q_table = defaultdict(lambda: defaultdict(float))
            for k, v in q_raw.items():
                try:
                    # Use json.loads instead of eval for safety and performance
                    # json.loads returns a list, so convert to tuple for dict key
                    state = tuple(json.loads(k))
                except (ValueError, TypeError):
                    continue
                self.q_table[state] = defaultdict(float, v)
        except FileNotFoundError:
            print("No saved brain found - starting fresh!")
