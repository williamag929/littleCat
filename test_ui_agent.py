"""
Test script for the Senior UI Agent.
Verifies that the UI Agent properly integrates with the game.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ui_agent_import():
    """Test that UI Agent can be imported."""
    print("Testing UI Agent import...")
    try:
        from ui_agent import SeniorUIAgent
        print("✓ UI Agent imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import UI Agent: {e}")
        return False

def test_ui_agent_basic():
    """Test basic UI Agent functionality."""
    print("\nTesting UI Agent basic functionality...")
    try:
        from ui_agent import SeniorUIAgent
        from cat_brain import CatBrain
        
        # Create UI Agent
        agent = SeniorUIAgent()
        print("✓ UI Agent created successfully")
        
        # Create a test cat
        cat = CatBrain("TestCat")
        cat.happiness = 75
        cat.hunger = 40
        cat.energy = 60
        cat.trust = 50
        print("✓ Test cat created")
        
        # Test action response
        response = agent.get_action_response('play', cat)
        if response:
            print(f"✓ Action response: '{response}'")
        else:
            print("✗ No action response generated")
            return False
        
        # Test state message
        state_msg = agent.get_state_message(cat)
        if state_msg:
            print(f"✓ State message: '{state_msg}'")
        else:
            print("  (No state message - this is normal)")
        
        # Test thought bubble
        thought = agent.get_thought_bubble(cat)
        if thought:
            print(f"✓ Thought bubble: '{thought}'")
        else:
            print("✗ No thought bubble generated")
            return False
        
        # Test hint
        hint = agent.get_hint({'cat_brain': cat})
        if hint:
            print(f"✓ Hint: '{hint}'")
        else:
            print("✗ No hint generated")
            return False
        
        # Test status color
        color = agent.get_status_color(75)
        print(f"✓ Status color for 75: {color}")
        
        # Test formatted status
        status_lines = agent.format_status_text(cat)
        if status_lines:
            print(f"✓ Formatted status: {len(status_lines)} lines")
            for line in status_lines:
                print(f"  - {line}")
        else:
            print("✗ No formatted status generated")
            return False
        
        # Test suggestion
        suggestion = agent.suggest_interaction(cat)
        if suggestion:
            print(f"✓ Interaction suggestion: '{suggestion}'")
        else:
            print("✗ No interaction suggestion generated")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_agent_states():
    """Test UI Agent with different cat states."""
    print("\nTesting UI Agent with various cat states...")
    try:
        from ui_agent import SeniorUIAgent
        from cat_brain import CatBrain
        
        agent = SeniorUIAgent()
        
        # Test with very hungry cat
        cat = CatBrain("HungryCat")
        cat.hunger = 85
        cat.happiness = 30
        cat.energy = 50
        
        msg = agent.get_state_message(cat)
        print(f"✓ Very hungry cat message: '{msg}'")
        
        suggestion = agent.suggest_interaction(cat)
        print(f"✓ Suggestion for hungry cat: '{suggestion}'")
        
        # Test with tired cat
        cat2 = CatBrain("TiredCat")
        cat2.energy = 15
        cat2.happiness = 50
        cat2.hunger = 40
        
        agent.last_message_time = agent.last_message_time.__class__(2020, 1, 1)  # Reset cooldown
        msg2 = agent.get_state_message(cat2)
        print(f"✓ Tired cat message: '{msg2}'")
        
        suggestion2 = agent.suggest_interaction(cat2)
        print(f"✓ Suggestion for tired cat: '{suggestion2}'")
        
        # Test with happy cat
        cat3 = CatBrain("HappyCat")
        cat3.happiness = 90
        cat3.energy = 80
        cat3.hunger = 20
        
        agent.last_message_time = agent.last_message_time.__class__(2020, 1, 1)  # Reset cooldown
        msg3 = agent.get_state_message(cat3)
        print(f"✓ Happy cat message: '{msg3}'")
        
        return True
    except Exception as e:
        print(f"✗ Error during state testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_game_integration():
    """Test that the game can be initialized with UI Agent."""
    print("\nTesting game integration...")
    try:
        # We can't fully run the game (needs display), but we can check imports
        from game import LittleCatGame
        print("✓ Game imports successfully with UI Agent")
        
        # Check that ui_agent is imported in game
        import game
        if hasattr(game, 'SeniorUIAgent'):
            print("✓ SeniorUIAgent is available in game module")
        else:
            print("✗ SeniorUIAgent not found in game module")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error during game integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("Senior UI Agent Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Import Test", test_ui_agent_import()))
    results.append(("Basic Functionality", test_ui_agent_basic()))
    results.append(("State Handling", test_ui_agent_states()))
    results.append(("Game Integration", test_game_integration()))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("="*60)
    print(f"Total: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! UI Agent is ready to use!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
