INSTALLATION & SETUP GUIDE
==========================

## MINIMUM REQUIREMENTS

- Windows 10/11 (or any OS with Python)
- Python 3.8 or higher
- 100MB free disk space
- No special graphics card needed

## STEP-BY-STEP INSTALLATION

### STEP 1: INSTALL PYTHON

1. Go to https://www.python.org/downloads/
2. Download Python 3.10+ (latest version recommended)
3. Run the installer
4. **IMPORTANT: Check "Add Python to PATH"**
5. Click Install Now
6. Verify installation:
   - Open PowerShell or Command Prompt
   - Type: python --version
   - Should show: Python 3.10.x (or higher)

### STEP 2: NAVIGATE TO PROJECT

1. Open PowerShell
2. Navigate to project:
   ```
   cd c:\projects\littleCat
   ```

### STEP 3: INSTALL DEPENDENCIES

Choose ONE method:

**METHOD A: Using Batch Script (Easiest)**
1. Double-click: run_littlecat.bat
2. Select option 1: "Install Dependencies"
3. Wait for installation to complete

**METHOD B: Manual Installation**
1. Open PowerShell in littleCat folder
2. Run command:
   ```
   pip install -r requirements.txt
   ```
3. Wait for completion

**METHOD C: Individual Installation**
1. Open PowerShell in littleCat folder
2. Run each command:
   ```
   pip install pygame==2.5.2
   pip install numpy==1.24.3
   pip install scikit-learn==1.3.0
   ```

### STEP 4: VERIFY INSTALLATION

Run the system test:
```
python test_system.py
```

Expected output:
- ✓ pygame imported
- ✓ numpy imported
- ✓ sklearn imported
- ✓ Cat brain created
- ✓ Game components working

If all show ✓, you're ready to play!

## RUNNING THE GAME

### METHOD 1: Batch Script (Recommended)
1. Double-click: run_littlecat.bat
2. Select option 2: "Run Game"
3. Game launches!

### METHOD 2: PowerShell Command
```
cd c:\projects\littleCat
python src/game.py
```

### METHOD 3: Direct File
1. Navigate to: c:\projects\littleCat\src
2. Right-click game.py
3. Select "Open with Python"

## YOUR FIRST GAME SESSION

1. Game window opens (800x600)
2. You see your cat "Whiskers" on screen
3. Stats display on the left
4. Instructions at the bottom

### GETTING STARTED:

**First 5 minutes (Tutorial):**
1. Press P to Play - See cat play and energy decrease
2. Press F to Feed - See hunger decrease
3. Press T to Pet - See trust increase and cat purr
4. Press S to Sleep - See cat rest and energy restore
5. Watch the stats change in real-time

**First 30 minutes (Exploration):**
1. Try all interactions (P, F, T, S, H, R)
2. Watch how cat reacts
3. Notice mood changes
4. Save your progress (Press E)

**First Hours (Learning):**
1. Interact consistently
2. Watch for pattern changes
3. Try different interaction styles
4. Reload a save (Press L) to see persistence

## KEYBOARD CONTROLS QUICK REFERENCE

INTERACTION KEYS:
- P = Play
- F = Feed
- T = Pet/Affection
- S = Sleep
- H = Hide (punishment)
- R = Rest

GAME KEYS:
- E = Export/Save cat
- L = Load saved cat
- ESC = Exit game

## TROUBLESHOOTING INSTALLATION

### "Python not found" / "python: command not found"

Solution:
1. Python not installed - Install from python.org
2. Python not in PATH:
   - Uninstall Python
   - Reinstall and CHECK "Add Python to PATH"

### "ModuleNotFoundError: pygame not found"

Solution:
```
pip install pygame --upgrade
```

### "pip: command not found"

Solution:
- Reinstall Python
- Check "Add Python to PATH" during installation
- Or use: python -m pip install pygame

### Game window doesn't open

Solution:
1. Check errors in console
2. Make sure pygame is installed: pip install pygame --upgrade
3. Try reducing FPS in src/game.py if slow
4. Update graphics drivers

### Game is very slow

Solution:
1. Close other programs
2. Edit src/game.py, find "FPS = 30", change to "FPS = 20"
3. Check your graphics drivers

## POST-INSTALLATION

### Useful Next Steps:

1. **Read Documentation**
   - QUICKSTART.txt - Fast start guide
   - README.md - Full features
   - ARCHITECTURE.md - How AI works

2. **Run Training Script**
   ```
   python src/trainer.py
   ```
   This shows AI learning without graphics

3. **Customize Your Cat**
   - Edit src/config.py to change settings
   - Edit src/game.py to change appearance

4. **Experiment**
   - Create multiple cats
   - Try different training styles
   - Export and reload saves

## FILE STRUCTURE AFTER INSTALLATION

```
littleCat/
├── src/
│   ├── game.py              ← Main game executable
│   ├── cat_brain.py         ← AI system
│   ├── trainer.py           ← Training script
│   └── config.py            ← Settings
│
├── data/
│   └── cat_brain.json       ← Auto-created on first save
│
├── run_littlecat.bat        ← Quick launcher (Windows)
├── requirements.txt         ← Dependency list
├── test_system.py           ← Verification script
├── README.md                ← Full documentation
├── QUICKSTART.txt           ← Quick start guide
├── ARCHITECTURE.md          ← AI explanation
├── DIAGRAMS.md              ← Visual diagrams
└── PROJECT_SUMMARY.md       ← Project overview
```

## UNINSTALLING

To completely remove Little Cat:

1. Delete the littleCat folder
2. (Optional) Uninstall Python from Control Panel

To keep Python but remove just the game:
1. Delete c:\projects\littleCat

## COMMON ISSUES & SOLUTIONS

| Issue | Solution |
|-------|----------|
| Game won't start | pip install pygame --upgrade |
| Python not found | Reinstall Python with PATH option |
| AttributeError | Make sure you're in the right directory |
| Game is slow | Reduce FPS in src/game.py |
| Cat won't load | Delete data/cat_brain.json |
| ModuleNotFoundError | Run: pip install -r requirements.txt |

## GETTING HELP

1. Check QUICKSTART.txt for quick answers
2. Check README.md for feature questions
3. Check ARCHITECTURE.md for AI questions
4. Check DIAGRAMS.md for system understanding
5. Review error messages in console
6. Try running test_system.py to diagnose

## NEXT STEPS AFTER SETUP

1. **Play the game!**
   ```
   python src/game.py
   ```

2. **Train your cat**
   ```
   python src/trainer.py
   ```

3. **Customize settings**
   - Edit src/config.py
   - Adjust learning rate, emotions, etc.

4. **Understand the AI**
   - Read ARCHITECTURE.md
   - Review src/cat_brain.py
   - Study the learning algorithm

5. **Extend the game**
   - Add new behaviors
   - New interactions
   - Visual improvements
   - Sound effects

## PERFORMANCE TIPS

For best performance:

1. Close unnecessary programs
2. Update graphics drivers
3. Run on latest Python 3.10+
4. Use SSD (faster file I/O)
5. Reduce FPS if on old computer

## BACKUP YOUR SAVES

Your cat's data is in: data/cat_brain.json

To backup:
1. Copy data/cat_brain.json
2. Save to external drive/cloud
3. Can restore by copying back

## UPDATING IN THE FUTURE

To update the project with new features:

1. Backup your saves:
   - Copy data/cat_brain.json to safe location

2. Download new version

3. Copy your data/cat_brain.json back

4. Your cats will continue learning!

---

**YOU'RE ALL SET!**

Ready to create your AI companion? Run the game and start training your cat!

```
python src/game.py
```

Happy gaming! 🐱
