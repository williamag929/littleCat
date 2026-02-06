"""
Simple test script to verify everything works before running the game.
Run this to check that all dependencies are installed correctly.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...\n")
    
    tests = [
        ("pygame", "Graphics library"),
        ("numpy", "Numerical computing"),
        ("sklearn", "Machine learning"),
        ("json", "Data serialization"),
        ("datetime", "Time handling"),
    ]
    
    failed = []
    
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"✓ {module_name:15s} - {description}")
        except ImportError:
            print(f"✗ {module_name:15s} - {description} [FAILED]")
            failed.append(module_name)
    
    return len(failed) == 0, failed


def test_cat_brain():
    """Test that the cat brain system works."""
    print("\n" + "="*50)
    print("Testing Cat Brain...\n")
    
    try:
        from src.cat_brain import CatBrain
        
        # Create a test cat
        cat = CatBrain("TestCat")
        print(f"✓ Created cat: {cat.name}")
        
        # Test decision making
        action, confidence = cat.decide_action("human_nearby")
        print(f"✓ Cat decided to: {action} (confidence: {confidence:.2f})")
        
        # Test learning
        cat.learn_from_interaction("play", "Human played with cat", 0.8)
        print(f"✓ Cat learned from interaction")
        
        # Test state update
        cat.update_state(1)
        print(f"✓ Cat state updated")
        
        # Test status
        status = cat.get_status()
        print(f"✓ Cat status retrieved")
        print(f"  - Happiness: {status['happiness']}/100")
        print(f"  - Hunger: {status['hunger']}/100")
        print(f"  - Energy: {status['energy']}/100")
        print(f"  - Mood: {status['mood']}")
        
        return True
    except Exception as e:
        print(f"✗ Cat brain test failed: {e}")
        return False


def test_game_components():
    """Test game components (without full game loop)."""
    print("\n" + "="*50)
    print("Testing Game Components...\n")
    
    try:
        import pygame
        pygame.init()
        print("✓ Pygame initialized")
        
        # Test screen creation
        screen = pygame.display.set_mode((800, 600))
        print("✓ Game window created (800x600)")
        
        # Test fonts
        font = pygame.font.Font(None, 28)
        text = font.render("Test", True, (0, 0, 0))
        print("✓ Font rendering works")
        
        pygame.quit()
        print("✓ Pygame shutdown successful")
        
        return True
    except Exception as e:
        print(f"✗ Game component test failed: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    print("\n" + "="*50)
    print("Testing File Structure...\n")
    
    required_files = [
        ("src/cat_brain.py", "Cat brain system"),
        ("src/game.py", "Main game file"),
        ("src/trainer.py", "Training script"),
        ("src/config.py", "Configuration"),
        ("requirements.txt", "Dependencies list"),
        ("README.md", "Documentation"),
    ]
    
    all_exist = True
    base_path = os.path.dirname(__file__)
    
    for filepath, description in required_files:
        full_path = os.path.join(base_path, filepath)
        if os.path.exists(full_path):
            print(f"✓ {filepath:25s} - {description}")
        else:
            print(f"✗ {filepath:25s} - {description} [MISSING]")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("LITTLE CAT - SYSTEM TEST")
    print("="*50 + "\n")
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    sys.path.insert(0, project_dir)
    
    results = []
    
    # Run tests
    import_ok, failed_imports = test_imports()
    results.append(("Imports", import_ok))
    
    file_ok = test_file_structure()
    results.append(("File Structure", file_ok))
    
    cat_ok = test_cat_brain()
    results.append(("Cat Brain", cat_ok))
    
    game_ok = test_game_components()
    results.append(("Game Components", game_ok))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50 + "\n")
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20s} - {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("\n✓ All tests passed! You're ready to play!")
        print("\nNext step: Run 'python src/game.py' to start the game")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        if failed_imports:
            print(f"\nMissing packages: {', '.join(failed_imports)}")
            print("Run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
