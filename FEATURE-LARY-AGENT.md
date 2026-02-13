# Feature: LARY Agent - AI Chat Assistant

**Branch**: `/feature/lary-agent`  
**Status**: Design Phase  
**Risk Level**: High (LLM integration, API dependency, real-time vision)  
**Implementation Priority**: Long-term enhancement  

---

## 1. Overview

**LARY** (Learning Agent with Reasoning Y) is an integrated AI chat assistant that leverages OpenAI's GPT-4 Vision API to provide real-time help understanding the game state, cat behavior, and general questions. The agent sees what the user sees and can explain game mechanics, provide advice, and answer questions contextually.

### Core Value Proposition
- **Screen-Aware Help**: Agent analyzes cat status, game UI, and stats to provide contextual answers
- **Learning Support**: Explain AI behavior, personality traits, achievements, trick training
- **Interactive Guidance**: Ask questions about anything on screen, get intelligent responses
- **Personal Agent**: Remembers conversation context within a session to provide continuity

---

## 2. Requirements

### 2.1 Functional Requirements

| Requirement | Description | Priority |
|---|---|---|
| FR1 | Chat UI overlay that doesn't block game interaction | HIGH |
| FR2 | Screenshot capture of current screen state | HIGH |
| FR3 | OpenAI GPT-4 Vision API integration | HIGH |
| FR4 | User input field for chat messages | HIGH |
| FR5 | Real-time response streaming or typed output | HIGH |
| FR6 | Game state context injection (cat info, stats, brain state) | MEDIUM |
| FR7 | Chat history within session | MEDIUM |
| FR8 | Keyboard shortcut to toggle chat (e.g., `?` or `Ctrl+H`) | HIGH |
| FR9 | Error handling & graceful fallback if API down | MEDIUM |
| FR10 | Token usage tracking and rate limit warnings | MEDIUM |

### 2.2 Non-Functional Requirements

| Requirement | Spec |
|---|---|
| **Response Time** | <3 seconds (ideal), <5 seconds (acceptable) |
| **Token Budget** | Max 1000 tokens per request (vision + history + response) |
| **Async Behavior** | API calls must not block game loop (threading/asyncio) |
| **Memory** | Chat history in RAM only (session-based, <2MB) |
| **API Cost** | Warn if cumulative usage exceeds threshold (auto-configurable) |
| **Offline Mode** | Graceful degradation if API unavailable |

### 2.3 Security & Configuration

| Aspect | Requirement |
|---|---|
| **API Key** | Stored in environment variable `OPENAI_API_KEY` |
| **No Hardcoding** | All secrets in `.env` (add to .gitignore) |
| **Rate Limiting** | Max 10 requests/minute per session |
| **Data Privacy** | Screenshots + context transmitted to OpenAI; no persistence beyond session |

---

## 3. Architecture

### 3.1 System Design

```
┌─────────────────────────────────────────┐
│        Game Main Loop (game.py)         │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Input Handler                    │  │
│  │ - Check for chat toggle key (?)  │  │
│  │ - Pass chat input if active      │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Game Logic Update                │  │
│  │ (runs normally, independent)     │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Rendering                        │  │
│  │ - Draw game                      │  │
│  │ - Draw chat overlay if active    │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         │ Chat Request (threaded)
         └──> ChatAgent (chat_agent.py)
                 │
                 ├─> Screenshot Capture (PIL)
                 ├─> Context Builder
                 │   ├─ Current cat state
                 │   ├─ Game stats
                 │   └─ Q-learning brain info
                 │
                 └─> OpenAI API Client
                     ├─ gpt-4-vision request
                     ├─ Token counting
                     └─ Response handling
```

### 3.2 Module Structure

```
src/
├── chat_agent.py          # NEW: Main chat agent logic
│   ├── ChatAgent class
│   ├── OpenAI API wrapper
│   ├── Screenshot capturer
│   ├── Context builder
│   └── Response formatter
│
├── game.py                # MODIFIED: Add chat UI integration
│   ├── Chat toggle handler
│   ├── Chat UI renderer (overlay)
│   └── Chat thread management
│
└── config.py              # MODIFIED: Add chat config
    ├── CHAT_ENABLED = True
    ├── CHAT_MODEL = "gpt-4-vision-preview"
    ├── CHAT_MAX_TOKENS = 500
    ├── CHAT_HISTORY_LENGTH = 10
    ├── CHAT_TOGGLE_KEY = "?"
    └── CHAT_API_TIMEOUT = 5.0
```

### 3.3 Data Flow

```
User presses '?' key
    │
    ├─> Game pauses chat focus
    │   (game continues in background)
    │
    ├─> User types message: "Why is my cat sleeping?"
    │
    ├─> ChatAgent.get_response(user_msg)
    │   │
    │   ├─> Capture screenshot (PIL ImageGrab)
    │   ├─> Build context:
    │   │   {
    │   │     "cat_name": "Whiskers",
    │   │     "age": 466.1,
    │   │     "energy": 25,
    │   │     "hunger": 60,
    │   │     "happiness": 80,
    │   │     "trust": 75,
    │   │     "last_actions": ["hunt", "feed", "sleep"],
    │   │     "personality": "playful, curious",
    │   │     "learning_status": "Q-learning active"
    │   │   }
    │   │
    │   ├─> Construct prompt:
    │   │   <system>You are LARY, a helpful AI assistant for a virtual pet game...</system>
    │   │   <image>[screenshot]</image>
    │   │   <context>[cat state JSON]</context>
    │   │   <history>[last 5 messages]</history>
    │   │   <user_message>Why is my cat sleeping?</user_message>
    │   │
    │   └─> Send to OpenAI API (async thread)
    │
    ├─> API Response: "Your cat is sleeping because its energy..."
    │
    └─> Render response in chat overlay
        User can continue chatting or press ESC to close
```

---

## 4. Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

#### 4.1.1 Create `src/chat_agent.py`

```python
"""
Chat agent module using OpenAI Vision API.
Provides real-time AI assistance for understanding game state.
"""

import os
import threading
from typing import Optional, List, Dict
from queue import Queue
import base64
from io import BytesIO
from PIL import ImageGrab, Image
import json

try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai package not installed. Run: pip install openai")
    OpenAI = None


class ChatAgent:
    """AI assistant for game help using GPT-4 Vision."""
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        """
        Initialize chat agent.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            config: Configuration dict with model, max_tokens, timeout, etc.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )
        
        self.client = OpenAI(api_key=self.api_key) if OpenAI else None
        self.config = config or {}
        self.model = self.config.get("model", "gpt-4-vision-preview")
        self.max_tokens = self.config.get("max_tokens", 500)
        self.timeout = self.config.get("timeout", 5.0)
        
        # Chat history (in-memory, session only)
        self.history: List[Dict[str, str]] = []
        self.max_history = self.config.get("max_history", 10)
        
        # API usage tracking
        self.total_tokens = 0
        self.api_calls = 0
        self.rate_limit_window = []  # Track timestamps for rate limiting
        
        # Thread safety
        self.response_queue: Queue = Queue()
        self.is_waiting = False
    
    def capture_screenshot(self) -> str:
        """
        Capture current screen and encode as base64 for API.
        
        Returns:
            Base64-encoded image string
        """
        try:
            screenshot = ImageGrab.grab()
            # Resize for efficiency (max 1024x768)
            screenshot.thumbnail((1024, 768), Image.Resampling.LANCZOS)
            
            # Encode as JPEG to reduce size
            buffer = BytesIO()
            screenshot.save(buffer, format="JPEG", quality=80)
            buffer.seek(0)
            
            base64_image = base64.b64encode(buffer.getvalue()).decode()
            return base64_image
        except Exception as e:
            print(f"Screenshot capture failed: {e}")
            return ""
    
    def build_context(self, game_state: Dict) -> str:
        """
        Build context string from game state.
        
        Args:
            game_state: Dict with cat info, stats, etc.
        
        Returns:
            Formatted context string
        """
        context = {
            "timestamp": game_state.get("timestamp", "unknown"),
            "cat_name": game_state.get("cat_name", "Unknown"),
            "age_days": round(game_state.get("age", 0), 1),
            "emotional_state": {
                "hunger": game_state.get("hunger", 50),
                "energy": game_state.get("energy", 50),
                "happiness": game_state.get("happiness", 50),
                "trust": game_state.get("trust", 50),
            },
            "personality_traits": game_state.get("personality", {}),
            "last_actions": game_state.get("last_actions", []),
            "learned_tricks": game_state.get("learned_tricks", []),
            "brain_status": game_state.get("brain_status", "idle"),
            "achievements": len(game_state.get("achievements", [])),
        }
        return json.dumps(context, indent=2)
    
    def get_response(self, user_message: str, game_state: Dict) -> str:
        """
        Get AI response to user query with game context.
        
        Args:
            user_message: User's chat input
            game_state: Current game state dict
        
        Returns:
            AI response string (or error message)
        """
        if not self.client:
            return "ERROR: OpenAI client not initialized. Check API key."
        
        if self.is_waiting:
            return "WAIT: Agent is processing a request..."
        
        # Rate limiting check
        if len(self.rate_limit_window) >= 10:
            oldest_call = self.rate_limit_window[0]
            if time.time() - oldest_call < 60:
                return "RATE_LIMIT: Too many requests. Wait a moment."
            self.rate_limit_window.pop(0)
        
        # Start async request
        self.is_waiting = True
        thread = threading.Thread(
            target=self._request_thread,
            args=(user_message, game_state)
        )
        thread.daemon = True
        thread.start()
        
        return "⏳ Agent thinking..."
    
    def _request_thread(self, user_message: str, game_state: Dict):
        """
        Async thread for API request (non-blocking).
        
        Args:
            user_message: User query
            game_state: Game context
        """
        try:
            import time
            
            # Capture screenshot
            screenshot_b64 = self.capture_screenshot()
            
            # Build context
            context = self.build_context(game_state)
            
            # Add to history
            self.history.append({
                "role": "user",
                "content": user_message
            })
            
            # Trim history if too long
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
            
            # Build message history for API
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are LARY, a helpful AI assistant integrated into a virtual pet game. "
                        "You have vision of the game screen and access to the cat's emotional state. "
                        "Be concise, friendly, and contextual. Help the user understand their cat's behavior "
                        "and game mechanics. Reference the cat by name when possible."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{screenshot_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Game Context:\n{context}\n\nUser Query: {user_message}"
                        }
                    ]
                }
            ]
            
            # Call API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            # Extract response
            reply = response.choices[0].message.content
            
            # Track usage
            self.total_tokens += response.usage.total_tokens
            self.api_calls += 1
            self.rate_limit_window.append(time.time())
            
            # Add to history
            self.history.append({
                "role": "assistant",
                "content": reply
            })
            
            # Queue response
            self.response_queue.put(reply)
            
        except Exception as e:
            error_msg = f"ERROR: {str(e)[:100]}"
            self.response_queue.put(error_msg)
        finally:
            self.is_waiting = False
    
    def get_queued_response(self) -> Optional[str]:
        """
        Check if response is ready (non-blocking).
        
        Returns:
            Response string if ready, None otherwise
        """
        try:
            return self.response_queue.get_nowait()
        except:
            return None
    
    def get_usage_stats(self) -> str:
        """
        Return current API usage for warning/display.
        
        Returns:
            Formatted usage string
        """
        return f"API Calls: {self.api_calls} | Tokens: {self.total_tokens}"


# Factory function for safe initialization
def create_chat_agent(config: Dict = None) -> Optional[ChatAgent]:
    """
    Safely create chat agent with error handling.
    
    Args:
        config: Optional config dict
    
    Returns:
        ChatAgent instance or None if API key missing
    """
    try:
        return ChatAgent(config=config)
    except ValueError as e:
        print(f"Chat agent initialization skipped: {e}")
        return None
```

#### 4.1.2 Modify `src/config.py`

Add at the end:

```python
# ===== CHAT AGENT CONFIGURATION =====
CHAT_ENABLED = True
CHAT_TOGGLE_KEY = pygame.K_QUESTION  # Press '?' to open chat
CHAT_MODEL = "gpt-4-vision-preview"
CHAT_MAX_TOKENS = 500
CHAT_HISTORY_LENGTH = 10
CHAT_API_TIMEOUT = 5.0
CHAT_MAX_REQUESTS_PER_MINUTE = 10
```

#### 4.1.3 Update `.env` Template

Create `.env.example` in root:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here

# Chat Agent Settings (optional overrides)
CHAT_MAX_TOKENS=500
CHAT_HISTORY_LENGTH=10
CHAT_MODEL=gpt-4-vision-preview
```

---

### Phase 2: UI Integration (Weeks 3-4)

#### 4.2.1 Modify `src/game.py` - Add Chat UI

```python
# In LittleCatGame.__init__():
self.chat_agent = None
self.chat_active = False
self.chat_input_text = ""
self.chat_response = ""
self.chat_cursor_blink = 0
self.chat_input_visible = True

# Try to initialize chat agent
try:
    from chat_agent import create_chat_agent
    self.chat_agent = create_chat_agent({
        "model": config.CHAT_MODEL,
        "max_tokens": config.CHAT_MAX_TOKENS,
        "timeout": config.CHAT_API_TIMEOUT,
        "max_history": config.CHAT_HISTORY_LENGTH
    })
except ImportError:
    print("Chat agent module not available.")

# In update() method, add:
self.update_chat_input()

# In handle_key_press():
if event.key == config.CHAT_TOGGLE_KEY and self.chat_agent:
    self.chat_active = not self.chat_active
    self.chat_input_text = ""
    self.chat_response = ""

# In handle_text_input():
if self.chat_active and event.unicode.isprintable():
    self.chat_input_text += event.unicode

# Add new methods:
def update_chat_input(self):
    """Process chat input and API responses."""
    if not self.chat_active or not self.chat_agent:
        return
    
    # Update cursor blink
    self.chat_cursor_blink = (self.chat_cursor_blink + 1) % 60
    
    # Check for queued API response
    response = self.chat_agent.get_queued_response()
    if response:
        self.chat_response = response

def render_chat_ui(self, display):
    """Render chat overlay on screen."""
    if not self.chat_active or not self.chat_agent:
        return
    
    # Dims background slightly
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    display.blit(overlay, (0, 0))
    
    # Chat box background (bottom half)
    chat_rect = pygame.Rect(20, 300, 760, 280)
    pygame.draw.rect(display, (30, 30, 30), chat_rect)
    pygame.draw.rect(display, (100, 150, 255), chat_rect, 2)
    
    # Agent response display area
    if self.chat_response:
        response_lines = self.display.word_wrap(self.chat_response, 750)
        y = 310
        for line in response_lines[:8]:  # Max 8 lines
            text_surf = self.display.font_small.render(line, True, (255, 255, 255))
            display.blit(text_surf, (30, y))
            y += 20
    
    # Input line
    input_y = 550
    display.blit(
        self.display.font_small.render("You: ", True, (100, 200, 255)),
        (30, input_y)
    )
    
    # Input text
    input_surf = self.display.font_small.render(
        self.chat_input_text,
        True,
        (200, 200, 200)
    )
    display.blit(input_surf, (80, input_y))
    
    # Blinking cursor
    if self.chat_cursor_blink > 30:
        cursor_x = 80 + input_surf.get_width() + 2
        pygame.draw.line(display, (255, 255, 255), (cursor_x, input_y), (cursor_x, input_y + 16))
    
    # Status/help text
    status_text = "Press ENTER to send | ESC to close | BACKSPACE to delete"
    status_surf = self.display.font_tiny.render(status_text, True, (150, 150, 150))
    display.blit(status_surf, (30, 575))
```

#### 4.2.2 Modify `src/game.py` - Key handling

```python
# In handle_key_press(), add:
if self.chat_active and self.chat_agent:
    if event.key == pygame.K_RETURN:
        # Send message
        if self.chat_input_text.strip():
            game_state = self.get_game_state_for_agent()
            self.chat_agent.get_response(self.chat_input_text, game_state)
            self.chat_input_text = ""
    
    elif event.key == pygame.K_BACKSPACE:
        self.chat_input_text = self.chat_input_text[:-1]
    
    elif event.key == pygame.K_ESCAPE:
        self.chat_active = False

def get_game_state_for_agent(self) -> Dict:
    """Get current game state snapshot for chat context."""
    cat = self.get_current_cat()
    return {
        "timestamp": datetime.now().isoformat(),
        "cat_name": cat.name,
        "age": cat.age,
        "hunger": cat.hunger,
        "energy": cat.energy,
        "happiness": cat.happiness,
        "trust": cat.trust,
        "personality": cat.brain.personality,
        "last_actions": cat.recent_actions[-5:],  # Last 5 actions
        "learned_tricks": [t for t, l in cat.brain.tricks.items() if l > 0],
        "brain_status": "learning" if hasattr(cat.brain, 'is_learning') else "idle",
        "achievements": [a for a, _ in cat.achievements],
    }
```

#### 4.2.3 Modify `GameDisplay.update()` - Add chat rendering

```python
# In display() method, after drawing everything else:
if self.chat_active:
    self.render_chat_ui(self.screen)
```

---

### Phase 3: Testing & Validation (Week 5)

#### 4.3.1 Unit Tests

Create `tests/test_chat_agent.py`:

```python
import pytest
from src.chat_agent import ChatAgent, create_chat_agent
import os


def test_chat_agent_initialization():
    """Test agent initializes with valid API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    
    agent = ChatAgent(api_key=api_key)
    assert agent.client is not None
    assert agent.history == []


def test_chat_agent_safe_creation():
    """Test safe creation returns None without API key."""
    # Temporarily unset env var
    original_key = os.getenv("OPENAI_API_KEY")
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    
    agent = create_chat_agent()
    assert agent is None
    
    # Restore
    if original_key:
        os.environ["OPENAI_API_KEY"] = original_key


def test_context_building():
    """Test game state context formatting."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    
    agent = ChatAgent(api_key=api_key)
    game_state = {
        "cat_name": "Whiskers",
        "age": 100.5,
        "hunger": 50,
        "energy": 75,
        "happiness": 85,
        "trust": 70,
    }
    
    context = agent.build_context(game_state)
    assert "Whiskers" in context
    assert "100.5" in context


def test_rate_limiting():
    """Test rate limit detection."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    
    agent = ChatAgent(api_key=api_key)
    import time
    
    # Simulate 10 rapid calls
    for _ in range(10):
        agent.rate_limit_window.append(time.time())
    
    # Next call should be rate limited
    response = agent.get_response("test", {})
    assert "RATE_LIMIT" in response
```

#### 4.3.2 Integration Test

Create `tests/test_game_chat_integration.py`:

```python
def test_chat_toggle():
    """Test chat activation/deactivation."""
    # Mock game setup
    game = LittleCatGame()
    
    assert not game.chat_active
    # Simulate '?' press
    game.chat_active = True
    assert game.chat_active


def test_game_state_snapshot():
    """Test game state capture for agent."""
    game = LittleCatGame()
    game_state = game.get_game_state_for_agent()
    
    assert "cat_name" in game_state
    assert "hunger" in game_state
    assert "energy" in game_state
```

---

## 5. Usage Guide

### 5.1 Initial Setup

```bash
# 1. Create .env file
echo "OPENAI_API_KEY=sk-..." > .env

# 2. Install dependencies
pip install openai pillow

# 3. Create feature branch
git checkout -b feature/lary-agent

# 4. Implement phases 1-3
```

### 5.2 In-Game Usage

```
Press '?' key to open chat panel
         │
         ├─> Type a question
         │   Examples:
         │   - "Why is my cat sleeping?"
         │   - "What does the personality 'curious' mean?"
         │   - "How can I train my cat faster?"
         │   - "Explain the Q-learning in this game"
         │
         ├─> Press ENTER to send
         │   (Agent analyzes screenshot + game state)
         │
         └─> Read response
             (can continue chatting)
         
         Press ESC to close chat
```

### 5.3 Configuration Tuning

In `config.py`:

```python
# Faster responses, lower quality
CHAT_MAX_TOKENS = 300
CHAT_MODEL = "gpt-3.5-turbo-vision"  # Cheaper, faster

# Slower responses, higher quality
CHAT_MAX_TOKENS = 1000
CHAT_MODEL = "gpt-4-vision-preview"  # Expensive, best quality

# Rate limiting
CHAT_MAX_REQUESTS_PER_MINUTE = 5  # Stricter limit for cost control
```

---

## 6. Risk Assessment & Mitigation

### 6.1 High-Risk Areas

| Risk | Impact | Mitigation |
|---|---|---|
| **API Cost Overruns** | Can exceed budget quickly | Token tracking, rate limits, clear warnings |
| **API Downtime** | Chat unavailable | Graceful fallback to "Agent offline" message |
| **Privacy/Data Leakage** | Screenshots sent to OpenAI | Warn users, use .env for secrets, no history persistence |
| **Game Performance** | Blocking API calls | Use threading/async for requests |
| **Hallucination** | Agent gives wrong game info | Inject real game state; user can verify vs screen |
| **Rate Limiting by OpenAI** | Quota exhausted | Monitor usage, enforce per-minute limits |

### 6.2 Safeguards

✓ API key in environment variable (not hardcoded)  
✓ Chat history in memory only (no disk persistence)  
✓ Threading prevents game loop blocking  
✓ Token counting per request  
✓ Rate limiting per minute (10 req/min default)  
✓ Graceful error messages  
✓ Warning thresholds for usage  

---

## 7. Success Metrics

### 7.1 Technical KPIs

| Metric | Target | Threshold |
|---|---|---|
| Chat Response Time | <3s | <5s acceptable |
| Game FPS Impact | <5% slowdown | <10% acceptable |
| API Success Rate | >95% | >90% minimum |
| Memory Usage (history) | <1MB | <2MB max |

### 7.2 User Experience KPIs

| Metric | Target |
|---|---|
| Chat accuracy (context-aware answers) | >80% helpful |
| User engagement (questions per session) | >2 average |
| Feature adoption | >50% of users try chat |

---

## 8. Future Enhancements (Post-MVP)

- [ ] Fine-tuned model trained on game-specific data
- [ ] Voice input/output (Whisper + TTS)
- [ ] Multi-turn conversation with memory persistence
- [ ] Chat history export
- [ ] Local LLM fallback (Ollama) for offline mode
- [ ] Custom LARY personality/voice
- [ ] Integration with cat learning (agent suggests actions)
- [ ] Chat widget in separate window (PyQt/Kivy UI)

---

## 9. Branch Management

```bash
# Create feature branch
git checkout -b feature/lary-agent

# Development workflow
git add src/chat_agent.py
git add src/game.py
git add src/config.py
git add .env.example
git commit -m "feat: implement LARY chat agent foundation"

# Testing
git add tests/test_chat_agent.py
git commit -m "test: add chat agent unit tests"

# When complete
git push origin feature/lary-agent
# Create Pull Request for review

# Merge to main when validated
git checkout main
git merge feature/lary-agent
```

---

## 10. Known Limitations & Disclaimers

⚠️ **This is a high-risk experimental feature.**

- Requires active OpenAI subscription and API key
- Vision API usage is expensive (~$0.01-0.03 per screenshot)
- Screenshots are transmitted to OpenAI servers (privacy consideration)
- Agent responses may be incorrect or hallucinated
- Game doesn't pause while waiting for API response (can feel laggy)
- Requires internet connection (offline mode not available in MVP)
- API changes by OpenAI may require code updates

---

**Document Version**:  2.0  
**Last Updated**: 2025-02-13  
**Status**: Design Approved - Ready for Phase 1 Implementation
