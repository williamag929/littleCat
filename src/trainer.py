"""
Advanced Training Script for Little Cat AI
Use this to train/test your cat's learning without the game interface.
Useful for testing learning algorithms and behavior patterns.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from cat_brain import CatBrain
import random
import json
from datetime import datetime


class CatTrainer:
    """Automated training system for the cat AI."""
    
    def __init__(self, cat_name="TestCat"):
        self.cat = CatBrain(cat_name)
        self.training_log = []
        
    def simulate_human_interaction(self, num_iterations=100, interaction_type="mixed"):
        """
        Simulate human-cat interactions to train the AI.
        
        Args:
            num_iterations: Number of training cycles
            interaction_type: 'positive', 'negative', 'mixed', or 'neglect'
        """
        print(f"\n{'='*60}")
        print(f"Training {self.cat.name} with {num_iterations} interactions")
        print(f"Interaction type: {interaction_type}")
        print(f"{'='*60}\n")
        
        for iteration in range(num_iterations):
            # Update time
            self.cat.update_state(time_delta=0.5)
            
            # Decide action
            context = random.choice(['human_nearby', 'alone', 'food_available'])
            action, confidence = self.cat.decide_action(context)
            
            # Generate interaction based on type
            if interaction_type == "positive":
                reward = self.positive_interaction(action, context)
            elif interaction_type == "negative":
                reward = self.negative_interaction(action, context)
            elif interaction_type == "neglect":
                reward = self.neglect_interaction(action, context)
            else:  # mixed
                rand = random.random()
                if rand < 0.6:
                    reward = self.positive_interaction(action, context)
                elif rand < 0.8:
                    reward = self.negative_interaction(action, context)
                else:
                    reward = self.neglect_interaction(action, context)
            
            # Learn from interaction
            human_action = self.describe_interaction(action, reward)
            self.cat.learn_from_interaction(action, human_action, reward)
            
            # Log progress
            status = self.cat.get_status()
            log_entry = {
                'iteration': iteration + 1,
                'action': action,
                'confidence': round(confidence, 3),
                'reward': round(reward, 2),
                'happiness': status['happiness'],
                'trust': status['trust'],
                'age_days': round(status['age_days'], 2),
            }
            self.training_log.append(log_entry)
            
            # Print progress every 10 iterations
            if (iteration + 1) % 10 == 0:
                print(f"Iteration {iteration + 1}:")
                print(f"  Action: {action} (confidence: {confidence:.2f})")
                print(f"  Happiness: {status['happiness']:.0f}/100")
                print(f"  Trust: {status['trust']:.0f}/100")
                print(f"  Age: {status['age_days']:.1f} days")
                print()
        
        print(f"\nTraining Complete! {self.cat.name} learned from {num_iterations} interactions.")
        self.print_summary()
    
    def positive_interaction(self, action, context):
        """Human rewards the cat's action."""
        if action == 'play' and context == 'human_nearby':
            return 1.0
        elif action == 'eat' and self.cat.hunger > 50:
            return 1.0
        elif action == 'purr':
            return 0.8
        elif action == 'sleep':
            return 0.6
        else:
            return 0.5
    
    def negative_interaction(self, action, context):
        """Human discourages the cat's action."""
        if action == 'hide':
            return -0.8
        elif action == 'scratch':
            return -0.7
        else:
            return -0.3
    
    def neglect_interaction(self, action, context):
        """Human ignores the cat."""
        return -0.1
    
    def describe_interaction(self, action, reward):
        """Create a human-readable description of the interaction."""
        if reward > 0.7:
            return f"Human praised the cat for {action}ing!"
        elif reward > 0.3:
            return f"Human acknowledged the cat {action}ing"
        elif reward < -0.5:
            return f"Human discouraged {action}ing"
        else:
            return f"Human ignored the {action} behavior"
    
    def print_summary(self):
        """Print training summary and learning metrics."""
        print(f"\n{'='*60}")
        print("TRAINING SUMMARY")
        print(f"{'='*60}\n")
        
        status = self.cat.get_status()
        print(f"Cat Name: {status['name']}")
        print(f"Age: {status['age_days']:.1f} days")
        print(f"Mood: {status['mood']}")
        print(f"\nEmotional State:")
        print(f"  Happiness: {status['happiness']}/100")
        print(f"  Hunger: {status['hunger']}/100")
        print(f"  Energy: {status['energy']}/100")
        print(f"  Trust: {status['trust']}/100")
        
        print(f"\nLearned Behaviors:")
        behaviors = status['behavior_patterns']
        for behavior, weight in sorted(behaviors.items(), key=lambda x: x[1], reverse=True):
            stars = "★" * max(1, int(abs(weight) * 5))
            print(f"  {behavior:10s}: {weight:6.2f} {stars}")
        
        print(f"\nMemories Stored: {status['memories_count']}/100")
        
        # Analyze learning progress
        avg_reward = sum(e['reward'] for e in self.training_log) / len(self.training_log)
        print(f"\nLearning Metrics:")
        print(f"  Average Reward: {avg_reward:.3f}")
        print(f"  Final Happiness: {status['happiness']}")
        print(f"  Trust Development: {status['trust']:.0f}")
    
    def test_decision_making(self, test_count=10):
        """Test the cat's decision-making in various contexts."""
        print(f"\n{'='*60}")
        print(f"Decision-Making Test ({test_count} scenarios)")
        print(f"{'='*60}\n")
        
        contexts = ['human_nearby', 'alone', 'food_available']
        
        for i in range(test_count):
            context = contexts[i % len(contexts)]
            action, confidence = self.cat.decide_action(context)
            
            status = self.cat.get_status()
            print(f"Test {i+1} - Context: {context}")
            print(f"  Decision: {action} (confidence: {confidence:.2f})")
            print(f"  Cat state: Happy={status['happiness']}, "
                  f"Hungry={status['hunger']}, Energy={status['energy']}")
            print()
    
    def export_training_log(self, filename='training_log.json'):
        """Export training log to JSON."""
        filepath = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
        with open(filepath, 'w') as f:
            json.dump(self.training_log, f, indent=2)
        print(f"Training log exported to {filepath}")
    
    def save_trained_cat(self, filename='trained_cat.json'):
        """Save the trained cat."""
        filepath = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
        self.cat.save_brain(filepath)
        print(f"Trained cat saved to {filepath}")


def main():
    """Main training script."""
    
    # Example 1: Train a cat with positive reinforcement
    print("\n" + "="*60)
    print("EXAMPLE 1: Positive Training")
    print("="*60)
    trainer1 = CatTrainer("PositiveCat")
    trainer1.simulate_human_interaction(num_iterations=50, interaction_type="positive")
    trainer1.test_decision_making(5)
    
    # Example 2: Train a cat with mixed interactions (realistic)
    print("\n" + "="*60)
    print("EXAMPLE 2: Mixed Training (Realistic)")
    print("="*60)
    trainer2 = CatTrainer("RealisticCat")
    trainer2.simulate_human_interaction(num_iterations=100, interaction_type="mixed")
    trainer2.test_decision_making(5)
    trainer2.save_trained_cat('realistic_cat.json')
    
    # Example 3: Compare two different training approaches
    print("\n" + "="*60)
    print("EXAMPLE 3: Comparison - Positive vs Neglect")
    print("="*60)
    
    trainer3 = CatTrainer("LuckyPositiveCat")
    trainer3.simulate_human_interaction(num_iterations=50, interaction_type="positive")
    final_positive = trainer3.cat.get_status()
    
    trainer4 = CatTrainer("NeglectedCat")
    trainer4.simulate_human_interaction(num_iterations=50, interaction_type="neglect")
    final_neglected = trainer4.cat.get_status()
    
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    print(f"\nPositively Trained Cat:")
    print(f"  Happiness: {final_positive['happiness']}")
    print(f"  Trust: {final_positive['trust']}")
    print(f"  Mood: {final_positive['mood']}")
    
    print(f"\nNeglected Cat:")
    print(f"  Happiness: {final_neglected['happiness']}")
    print(f"  Trust: {final_neglected['trust']}")
    print(f"  Mood: {final_neglected['mood']}")


if __name__ == "__main__":
    main()
