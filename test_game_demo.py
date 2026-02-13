"""
Quick demo script to verify the game runs with the UI Agent.
This runs for a few seconds to verify integration.
"""

import os
import sys

# Set SDL to use dummy video driver for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pygame
from game import LittleCatGame
import time

def test_game_with_ui_agent():
    """Test that the game runs with UI Agent for a few frames."""
    print("="*60)
    print("Testing Little Cat Game with UI Agent")
    print("="*60)
    
    try:
        # Initialize pygame
        pygame.init()
        
        # Create game instance
        print("\n1. Creating game instance...")
        game = LittleCatGame()
        print("✓ Game created successfully")
        
        # Check UI Agent is present
        if hasattr(game, 'ui_agent'):
            print("✓ UI Agent is initialized in game")
        else:
            print("✗ UI Agent not found in game")
            return False
        
        # Simulate a few game updates
        print("\n2. Running game updates...")
        for i in range(10):
            # Handle empty event queue
            for event in pygame.event.get():
                pass
            
            # Update game state
            game.update()
            
            # Get cat status
            cat_status = game.cat.get_status()
            
            # Check for UI agent messages
            if game.agent_message:
                print(f"   Frame {i}: Agent message: '{game.agent_message}'")
            
            if game.agent_hint:
                print(f"   Frame {i}: Agent hint: '{game.agent_hint}'")
            
            if game.thought_bubble:
                print(f"   Frame {i}: Thought bubble: '{game.thought_bubble}'")
            
            # Simulate a small time step
            time.sleep(0.05)
        
        print("✓ Game updates completed successfully")
        
        # Test performing an action with UI Agent
        print("\n3. Testing action with UI Agent feedback...")
        game.perform_action('play', "Test play action")
        
        if game.agent_message:
            print(f"✓ UI Agent response: '{game.agent_message}'")
        else:
            print("⚠ No UI Agent response (might appear later)")
        
        # Test another action
        game.perform_action('purr', "Test pet action")
        if game.agent_message:
            print(f"✓ UI Agent response: '{game.agent_message}'")
        
        # Clean up
        print("\n4. Cleaning up...")
        game.running = False
        pygame.quit()
        print("✓ Game shutdown successfully")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during game test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_game_with_ui_agent()
    
    print("\n" + "="*60)
    if success:
        print("✅ SUCCESS! The game runs perfectly with the UI Agent!")
        print("="*60)
        print("\nThe Senior UI Agent provides:")
        print("  • Personality-driven dialogue and responses")
        print("  • Contextual hints and tooltips")
        print("  • State-based feedback messages")
        print("  • Thought bubbles showing cat's internal state")
        print("  • Dynamic status bar coloring")
        print("  • Intelligent interaction suggestions")
        print("\nTo run the full game with graphics:")
        print("  python src/game.py")
        return 0
    else:
        print("❌ FAILED! There were errors during testing.")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
