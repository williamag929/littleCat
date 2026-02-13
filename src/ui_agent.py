"""
Senior UI Agent - Intelligent UI Enhancement System
Provides context-aware UI improvements, dialogue generation, and user guidance.
"""

import random
from datetime import datetime
from collections import deque


class SeniorUIAgent:
    """
    Senior UI Agent that enhances the user experience by:
    - Generating personality-driven dialogue and feedback
    - Providing contextual tooltips and hints
    - Monitoring game state for UI improvements
    - Creating engaging character interactions
    """
    
    def __init__(self):
        self.last_message_time = datetime.now()
        self.message_cooldown = 5  # seconds between messages
        self.recent_messages = deque(maxlen=20)
        self.hint_shown = set()
        
        # Message templates for different contexts
        self.action_responses = {
            'play': [
                "Yay! Playtime is the best! 🎾",
                "I love playing with you! ✨",
                "This is so much fun! 😸",
                "Best. Day. Ever! 🎉"
            ],
            'feed': [
                "Nom nom nom! So delicious! 🍖",
                "Thank you! I was getting hungry! 😋",
                "Mmm... my favorite! ❤️",
                "You're the best cook! 🐟"
            ],
            'pet': [
                "*purrs contentedly* 😊",
                "That feels wonderful! ✨",
                "I love you too! 💕",
                "*headbutts affectionately* 🥰"
            ],
            'sleep': [
                "*yawns* Time for a cat nap... 😴",
                "Zzz... dreaming of mice... 💤",
                "So cozy... 🌙",
                "*curls up and purrs* 😺"
            ],
            'groom': [
                "*licks paw* Must stay clean! ✨",
                "Grooming is important! 🧼",
                "Looking good, feeling good! 💅",
                "*bathes meticulously* 🐱"
            ],
            'talk': [
                "Meow! (I have so much to say!) 🗣️",
                "*meows excitedly* 😸",
                "Let me tell you about my day! 💬",
                "Mrow? Meow meow! 🎵"
            ],
            'train': [
                "Watch this trick! I'm learning! 🎓",
                "Am I doing it right? 🌟",
                "I'm getting better at this! 📚",
                "Teaching me makes me smarter! 🧠"
            ],
            'jump': [
                "Wheee! Look how high I can jump! 🦘",
                "Parkour! 🐈",
                "*lands gracefully* Perfect! ✨",
                "I'm a jumping champion! 🏆"
            ]
        }
        
        # State-based suggestions
        self.state_messages = {
            'very_happy': [
                "I'm so happy right now! 😊",
                "Life is wonderful with you! ✨",
                "Best owner ever! ❤️"
            ],
            'happy': [
                "I'm feeling good today! 😺",
                "Things are going well! 🌟"
            ],
            'sad': [
                "I could use some attention... 😿",
                "Feeling a bit lonely...",
                "Maybe we could play? 🥺"
            ],
            'very_sad': [
                "I miss you... 😢",
                "Please don't forget about me...",
                "I need some love..."
            ],
            'hungry': [
                "My tummy is rumbling... 🍖",
                "Food would be nice right now! 😋",
                "When's dinner time? 🐟"
            ],
            'very_hungry': [
                "I'm really hungry! 😿",
                "Please feed me soon! 🍽️",
                "So... hungry... 😰"
            ],
            'tired': [
                "*yawns* Getting sleepy... 😪",
                "Maybe a nap would be nice... 💤"
            ],
            'very_tired': [
                "So... tired... must... sleep... 😴",
                "Can barely keep my eyes open... 💤"
            ],
            'energetic': [
                "I'm full of energy! Let's play! ⚡",
                "Feeling great! Ready for action! 💪",
                "So much energy to burn! 🔥"
            ]
        }
        
        # Helpful hints for new users
        self.hints = {
            'controls': "💡 Tip: Press P to play, F to feed, T to pet, or click on me!",
            'happiness': "💡 Hint: I'm happier when you interact with me regularly!",
            'hunger': "💡 Tip: Don't forget to feed me when I'm hungry!",
            'energy': "💡 Hint: I need rest when my energy is low!",
            'trust': "💡 Tip: Building trust takes time and positive interactions!",
            'personality': "💡 Info: My personality develops based on how you treat me!",
            'save': "💡 Hint: Press E to export my brain and save my learning!",
            'overlay': "💡 Tip: Press U to toggle UI, C for click-through mode!"
        }
        
    def get_action_response(self, action, cat_brain):
        """
        Generate a personality-aware response to an action.
        
        Args:
            action: The action being performed
            cat_brain: CatBrain instance for personality context
            
        Returns:
            str: A contextual message
        """
        if action in self.action_responses:
            messages = self.action_responses[action]
            
            # Adjust message selection based on personality and state
            if cat_brain:
                # Happy cats are more enthusiastic
                if cat_brain.happiness > 70:
                    # Prefer more enthusiastic messages
                    message = random.choice(messages)
                elif cat_brain.happiness < 30:
                    # Tone down enthusiasm if sad
                    neutral_messages = [msg for msg in messages if '!' not in msg]
                    message = random.choice(neutral_messages) if neutral_messages else messages[0]
                else:
                    message = random.choice(messages)
            else:
                message = random.choice(messages)
                
            self.recent_messages.append(message)
            return message
        
        return None
    
    def get_state_message(self, cat_brain):
        """
        Generate a message based on the cat's current emotional state.
        
        Args:
            cat_brain: CatBrain instance
            
        Returns:
            str or None: A state-based message if appropriate
        """
        if not cat_brain:
            return None
        
        # Check cooldown
        now = datetime.now()
        if (now - self.last_message_time).total_seconds() < self.message_cooldown:
            return None
        
        # Priority: Address critical needs first
        if cat_brain.hunger > 80:
            message = random.choice(self.state_messages['very_hungry'])
        elif cat_brain.energy < 15:
            message = random.choice(self.state_messages['very_tired'])
        elif cat_brain.happiness < 20:
            message = random.choice(self.state_messages['very_sad'])
        elif cat_brain.hunger > 60:
            message = random.choice(self.state_messages['hungry'])
        elif cat_brain.energy < 30:
            message = random.choice(self.state_messages['tired'])
        elif cat_brain.happiness < 35:
            message = random.choice(self.state_messages['sad'])
        elif cat_brain.energy > 80:
            message = random.choice(self.state_messages['energetic'])
        elif cat_brain.happiness > 80:
            message = random.choice(self.state_messages['very_happy'])
        elif cat_brain.happiness > 60:
            message = random.choice(self.state_messages['happy'])
        else:
            return None
        
        # Avoid repeating recent messages
        if message in self.recent_messages:
            return None
        
        self.last_message_time = now
        self.recent_messages.append(message)
        return message
    
    def get_hint(self, game_state=None):
        """
        Provide helpful hints to improve user experience.
        
        Args:
            game_state: Optional dict with game state info
            
        Returns:
            str or None: A helpful hint
        """
        # Show each hint only once per session
        available_hints = [h for h in self.hints.keys() if h not in self.hint_shown]
        
        if not available_hints:
            return None
        
        # Context-based hint selection
        if game_state:
            cat_brain = game_state.get('cat_brain')
            if cat_brain:
                # Suggest based on needs
                if cat_brain.hunger > 70 and 'hunger' in available_hints:
                    hint_key = 'hunger'
                elif cat_brain.energy < 25 and 'energy' in available_hints:
                    hint_key = 'energy'
                elif cat_brain.happiness < 30 and 'happiness' in available_hints:
                    hint_key = 'happiness'
                elif cat_brain.trust < 40 and 'trust' in available_hints:
                    hint_key = 'trust'
                else:
                    hint_key = random.choice(available_hints)
            else:
                hint_key = random.choice(available_hints)
        else:
            hint_key = random.choice(available_hints)
        
        self.hint_shown.add(hint_key)
        return self.hints[hint_key]
    
    def get_thought_bubble(self, cat_brain):
        """
        Generate a thought bubble text based on cat's internal state.
        
        Args:
            cat_brain: CatBrain instance
            
        Returns:
            str or None: What the cat is thinking
        """
        if not cat_brain:
            return None
        
        # What is the cat thinking about?
        thoughts = []
        
        if cat_brain.hunger > 70:
            thoughts.extend(["🍖", "🐟", "🥛"])
        elif cat_brain.energy < 25:
            thoughts.extend(["💤", "😴", "🌙"])
        elif cat_brain.happiness > 75:
            thoughts.extend(["❤️", "✨", "😊"])
        elif cat_brain.happiness < 30:
            thoughts.extend(["😿", "💔", "🥺"])
        else:
            # Random thoughts
            thoughts.extend(["🐭", "🦋", "🌟", "🎾", "🧶"])
        
        return random.choice(thoughts) if thoughts else None
    
    def get_status_color(self, value):
        """
        Get a color code for status bars based on value.
        
        Args:
            value: 0-100 value
            
        Returns:
            tuple: RGB color
        """
        if value >= 70:
            return (144, 238, 144)  # Green
        elif value >= 40:
            return (255, 215, 0)    # Yellow/Gold
        elif value >= 20:
            return (255, 165, 0)    # Orange
        else:
            return (220, 50, 50)    # Red
    
    def format_status_text(self, cat_brain):
        """
        Format enhanced status text with emoji indicators.
        
        Args:
            cat_brain: CatBrain instance
            
        Returns:
            list: Formatted status lines
        """
        if not cat_brain:
            return []
        
        status_lines = []
        
        # Happiness with emoji
        happy_emoji = "😊" if cat_brain.happiness > 60 else "😐" if cat_brain.happiness > 30 else "😢"
        status_lines.append(f"{happy_emoji} Happiness: {cat_brain.happiness:.0f}")
        
        # Hunger with emoji
        hunger_emoji = "🍖" if cat_brain.hunger > 60 else "🍽️" if cat_brain.hunger > 30 else "✅"
        status_lines.append(f"{hunger_emoji} Hunger: {cat_brain.hunger:.0f}")
        
        # Energy with emoji
        energy_emoji = "⚡" if cat_brain.energy > 60 else "🔋" if cat_brain.energy > 30 else "💤"
        status_lines.append(f"{energy_emoji} Energy: {cat_brain.energy:.0f}")
        
        # Trust with emoji
        trust_emoji = "❤️" if cat_brain.trust > 60 else "💛" if cat_brain.trust > 30 else "🤍"
        status_lines.append(f"{trust_emoji} Trust: {cat_brain.trust:.0f}")
        
        return status_lines
    
    def suggest_interaction(self, cat_brain):
        """
        Suggest the best interaction based on current state.
        
        Args:
            cat_brain: CatBrain instance
            
        Returns:
            str: Suggested action
        """
        if not cat_brain:
            return "Play with me!"
        
        # Prioritize needs
        if cat_brain.hunger > 70:
            return "I'm hungry! Press F to feed me!"
        elif cat_brain.energy < 20:
            return "I'm tired... Press S to let me sleep!"
        elif cat_brain.happiness < 30:
            return "I'm sad... Press T to pet me or P to play!"
        elif cat_brain.energy > 70 and cat_brain.happiness < 60:
            return "I'm energetic! Press P to play!"
        else:
            return "Spend time with me! Click me or press any key!"
    
    def celebrate_achievement(self, achievement_name):
        """
        Generate a celebration message for achievements.
        
        Args:
            achievement_name: Name of the achievement
            
        Returns:
            str: Celebration message
        """
        celebrations = [
            f"🎉 Achievement Unlocked: {achievement_name}!",
            f"⭐ Wow! {achievement_name}!",
            f"🏆 Congratulations! {achievement_name}!",
            f"✨ Amazing! {achievement_name}!"
        ]
        return random.choice(celebrations)
    
    def get_personality_insight(self, cat_brain):
        """
        Provide insights into the cat's developing personality.
        
        Args:
            cat_brain: CatBrain instance
            
        Returns:
            str: Personality insight
        """
        if not cat_brain:
            return None
        
        insights = []
        
        # Based on trust level
        if cat_brain.trust > 80:
            insights.append("I trust you completely! We're best friends! 💕")
        elif cat_brain.trust < 30:
            insights.append("I'm still learning to trust you...")
        
        # Based on behavior patterns
        if hasattr(cat_brain, 'learned_behaviors'):
            top_behavior = max(cat_brain.learned_behaviors.items(), 
                             key=lambda x: x[1], default=(None, 0))
            if top_behavior[0] and top_behavior[1] > 0.5:
                insights.append(f"I really enjoy when we {top_behavior[0]} together!")
        
        # Based on happiness trend
        if cat_brain.happiness > 75:
            insights.append("I'm such a happy cat! Life is good! 😸")
        
        return random.choice(insights) if insights else None
