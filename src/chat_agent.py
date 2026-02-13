"""
LARY Agent - Chat AI Assistant for Little Cat Pet Game
Uses OpenAI Vision API for context-aware help on-demand.
Screenshots captured ONLY when user requests intervention.
"""

import os
import threading
import time
import base64
import json
from typing import Optional, List, Dict
from queue import Queue, Empty
from io import BytesIO

try:
    from PIL import ImageGrab, Image
except ImportError:
    ImageGrab = None
    Image = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class ChatAgent:
    """AI assistant for context-aware game help using GPT-4 Vision."""
    
    def __init__(self, api_key: Optional[str] = None, config: Dict = None):
        """
        Initialize chat agent.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            config: Configuration dict with model, max_tokens, timeout, etc.
        
        Raises:
            ValueError: If OpenAI library not installed or API key missing
        """
        if not OpenAI:
            raise ImportError("openai package required. Install: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable or .env file"
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.config = config or {}
        self.model = self.config.get("model", "gpt-4-vision-preview")
        self.max_tokens = self.config.get("max_tokens", 500)
        self.timeout = self.config.get("timeout", 5.0)
        
        # Chat history (session-based only)
        self.history: List[Dict[str, str]] = []
        self.max_history = self.config.get("max_history", 10)
        
        # API usage tracking
        self.total_tokens = 0
        self.api_calls = 0
        self.rate_limit_window = []
        
        # Threading
        self.response_queue: Queue = Queue()
        self.is_processing = False
        self.current_response = ""
        self.current_error = ""
    
    def capture_screenshot(self) -> tuple[str, bool]:
        """
        Capture current screen and encode as base64.
        ⚠️ ONLY CALLED ON-DEMAND when user requests help
        
        Returns:
            Tuple of (base64_image_string, success_bool)
        """
        if not ImageGrab:
            return "", False
        
        try:
            screenshot = ImageGrab.grab()
            
            # Optimize: resize to reduce token usage
            screenshot.thumbnail((1024, 768), Image.Resampling.LANCZOS)
            
            # Encode as JPEG (smaller than PNG)
            buffer = BytesIO()
            screenshot.save(buffer, format="JPEG", quality=75)
            buffer.seek(0)
            
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return base64_image, True
        except Exception as e:
            print(f"⚠️ Screenshot failed: {e}")
            return "", False
    
    def build_game_context(self, game_state: Dict) -> str:
        """
        Build JSON context from game state.
        Injected into prompt for agent awareness.
        
        Args:
            game_state: Dict with cat stats, personality, etc.
        
        Returns:
            JSON formatted context string
        """
        context = {
            "cat_name": game_state.get("cat_name", "Unknown"),
            "age_days": round(game_state.get("age", 0), 1),
            "emotional_state": {
                "hunger": game_state.get("hunger", 50),
                "energy": game_state.get("energy", 50),
                "happiness": game_state.get("happiness", 50),
                "trust": game_state.get("trust", 50),
            },
            "personality_traits": game_state.get("personality", []),
            "last_action": game_state.get("last_action", "idle"),
            "learned_tricks": game_state.get("learned_tricks", []),
            "achievements": len(game_state.get("achievements", [])),
        }
        return json.dumps(context, indent=2)
    
    def request_help(self, user_query: str, game_state: Dict, include_screenshot: bool = True) -> str:
        """
        Request AI help for user query.
        
        Args:
            user_query: User's question/request
            game_state: Current game state
            include_screenshot: Whether to capture and include screenshot
        
        Returns:
            Status message (will be updated async via get_response())
        """
        if self.is_processing:
            return "⏳ Agent still processing previous request..."
        
        if self.is_rate_limited():
            return "❌ Rate limited. Too many requests. Wait a moment."
        
        # Start async processing
        self.is_processing = True
        self.current_error = ""
        
        thread = threading.Thread(
            target=self._process_request,
            args=(user_query, game_state, include_screenshot)
        )
        thread.daemon = True
        thread.start()
        
        return "⏳ LARY is thinking..."
    
    def _process_request(self, user_query: str, game_state: Dict, include_screenshot: bool):
        """
        Async thread worker for API request.
        
        Args:
            user_query: User's question
            game_state: Current game state
            include_screenshot: Capture screenshot for vision
        """
        try:
            # ⚠️ SCREENSHOT ONLY CAPTURED HERE (on demand)
            screenshot_b64 = ""
            screenshot_included = False
            
            if include_screenshot:
                screenshot_b64, screenshot_included = self.capture_screenshot()
            
            # Build context
            context_json = self.build_game_context(game_state)
            
            # Add to history
            self.history.append({
                "role": "user",
                "content": user_query
            })
            
            # Trim history if needed
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
            
            # Build message for API
            message_content = [
                {
                    "type": "text",
                    "text": (
                        f"Game Context:\n{context_json}\n\n"
                        f"User Query: {user_query}"
                    )
                }
            ]
            
            # Add screenshot if captured
            if screenshot_included:
                message_content.insert(0, {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{screenshot_b64}"
                    }
                })
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are LARY, an AI assistant for a virtual pet game. "
                        "Be concise, helpful, and contextual. Reference the cat by name. "
                        "Explain game mechanics clearly. Keep responses under 300 words."
                    )
                },
                {
                    "role": "user",
                    "content": message_content
                }
            ]
            
            # Call OpenAI API
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
            error_msg = f"❌ Error: {str(e)[:150]}"
            self.current_error = error_msg
            self.response_queue.put(error_msg)
        finally:
            self.is_processing = False
    
    def get_response(self) -> Optional[str]:
        """
        Non-blocking: Get response if ready.
        Call this every frame to check for new responses.
        
        Returns:
            Response string if ready, None otherwise
        """
        try:
            return self.response_queue.get_nowait()
        except Empty:
            return None
    
    def is_rate_limited(self) -> bool:
        """Check if rate limit exceeded (10 req/min)."""
        if len(self.rate_limit_window) < 10:
            return False
        
        oldest = self.rate_limit_window[0]
        if time.time() - oldest < 60:
            return True
        
        # Prune old timestamps
        self.rate_limit_window = [
            ts for ts in self.rate_limit_window
            if time.time() - ts < 60
        ]
        return False
    
    def get_usage_stats(self) -> str:
        """Return usage metrics for display."""
        return f"API Calls: {self.api_calls} | Tokens: {self.total_tokens}"
    
    def clear_history(self):
        """Clear chat history (useful for new topic)."""
        self.history = []
    
    def is_available(self) -> bool:
        """Check if agent is ready to accept new requests."""
        return not self.is_processing


def create_chat_agent(config: Dict = None) -> Optional[ChatAgent]:
    """
    Factory function to safely create chat agent.
    Returns None if API key unavailable.
    
    Args:
        config: Optional config dict
    
    Returns:
        ChatAgent instance or None
    """
    try:
        return ChatAgent(config=config)
    except (ValueError, ImportError) as e:
        print(f"ℹ️  Chat agent skipped: {e}")
        return None
