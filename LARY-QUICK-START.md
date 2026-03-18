# LARY Chat Agent - Quick Start Guide

## ✨ What is LARY?

**LARY** (Learning Agent with Reasoning Y) is an AI assistant integrated into Little Cat that provides context-aware help using OpenAI's GPT-4 Vision API. The agent can see your screen and analyze your cat's state to answer questions intelligently.

**Key Feature**: Screenshots are captured **ONLY when you ask for help** - not continuously. This saves API costs and improves privacy.

---

## 🚀 Getting Started

### 1. Set Up Your OpenAI API Key

Get your API key from: https://platform.openai.com/account/api-keys

Then set it in the `.env` file:

```bash
# In .env (already created)
OPENAI_API_KEY=sk-your-api-key-here
```

### 2. Install Dependencies

```bash
pip install openai pillow python-dotenv
```

**Already installed?** They were added automatically when you ran `pip install` above.

### 3. Run the Game

```bash
python run_littlecat.py
# or
./run_littlecat.bat
```

---

## 💬 How to Use LARY

### In Game:

1. **Press `?` (question mark)** to open the chat panel
2. **Type your question** (max 100 characters per message)
3. **Press ENTER** to send
   - 📸 Screenshot captured and sent to OpenAI
   - ⏳ LARY analyzes the screenshot + your cat's stats
   - 💭 Response appears in 1-3 seconds (usually)
4. **Press ESC** to close chat and continue playing

### Example Questions:

- "Why is my cat sleeping?"
- "How can I increase my cat's happiness?"
- "What does the personality 'curious' mean?"
- "Explain how Q-learning works in this game"
- "What's the difference between young and adult cats?"

---

## ⚙️ Configuration

Edit `src/config.py` to customize:

```python
# Model choice (trade-off: quality vs speed/cost)
CHAT_MODEL = "gpt-4-vision-preview"    # Best quality, ~$0.03 per image
# CHAT_MODEL = "gpt-3.5-turbo"         # Faster, ~$0.001 per image

# Response length
CHAT_MAX_TOKENS = 500      # Max response characters

# History
CHAT_HISTORY_LENGTH = 10   # Remember last 10 messages

# API timeout
CHAT_API_TIMEOUT = 5.0     # Seconds to wait for response

# Disable if you want (no API calls)
CHAT_ENABLED = False       # Set to False to disable
```

---

## 📊 API Cost

**Pricing** (as of Feb 2025):
- gpt-4-vision: ~$0.03 per image + $0.03 per 1K tokens output
- gpt-3.5-turbo: ~$0.001 per image + $0.0005 per 1K tokens output

**Example**: 
- 1 question with vision → ~$0.04 (gpt-4) or $0.0015 (gpt-3.5)
- 10 questions/session → ~$0.40 (gpt-4) or $0.015 (gpt-3.5)

**Monitor usage**: https://platform.openai.com/account/usage/overview

---

## 🎯 How It Works (Under the Hood)

```
User presses '?'
    ↓
Chat panel opens
    ↓
User types message & presses ENTER
    ↓
[ASYNC THREAD - Non-blocking]
    ├─ Screenshot captured (ONLY NOW)
    ├─ Converted to JPEG, optimized
    ├─ Sent to OpenAI API with:
    │   ├─ Screenshot image
    │   ├─ Cat stats (hunger, energy, etc.)
    │   ├─ Game context (age, personality, tricks)
    │   └─ Chat history (last 10 messages)
    ├─ GPT-4 Vision analyzes and responds
    └─ Response queued in memory
    ↓
Game continues (not blocked)
    ↓
Response appears in chat panel
    ↓
User can ask another question or press ESC to close
```

---

## 🔒 Privacy & Security

- **Screenshots uploaded**: YES, to OpenAI for analysis
- **Stored by OpenAI**: 30 days (per OpenAI privacy policy)
- **User data persisted locally**: NO (chat history cleared on exit)
- **API key**: Stored in `.env` (never committed to git)
- **Rate limited**: 10 requests/minute to prevent abuse

---

## ⚠️ Limitations

1. **API Cost**: gpt-4-vision is expensive for frequent use
2. **Hallucination**: Agent might give slightly incorrect info
3. **Screenshot timing**: Screenshot taken AT THE MOMENT of question send
4. **Internet required**: Must be online for API calls
5. **No offline mode**: Set `CHAT_ENABLED=False` to disable

---

## 🐛 Troubleshooting

### "ℹ️ Chat agent skipped: OpenAI API key not found"
**Solution**: Create `.env` file with `OPENAI_API_KEY=sk-...`

### "❌ Rate limited. Too many requests."
**Solution**: Wait 60 seconds, then try again (max 10 questions/min)

### "❌ Error: 401"
**Solution**: Check API key is valid and has funds

### "⏳ Thinking..." message never disappears
**Solution**: Check internet connection, may have timed out (5 sec default)

### Chat UI doesn't appear
**Solution**: Press `?` key. Make sure `CHAT_ENABLED=True` in config.py

---

## 📝 Example Interaction

```
[User presses ?]
Chat opens with prompt: "What's wrong with my cat?"

[User types]
You: Why is my kitty so sleepy?

[Presses ENTER - screenshot captured]
⏳ LARY is thinking...

[After 2 seconds...]
LARY: Your cat appears to have low energy (25/100). 
This could mean:
- It's been playing too much recently
- It needs food (hunger at 65)
- It's naturally a sleepy personality
Try feeding your cat or letting it rest in a quiet spot!

[User can ask follow-up]
You: How do I train tricks better?

[Continues...]
```

---

## 🚀 Future Enhancements

- [ ] Voice input/output (Whisper + TTS)
- [ ] Persistent chat history (save/load)
- [ ] Local LLM fallback (Ollama) for offline mode
- [ ] Fine-tuned model trained on game data only
- [ ] Custom LARY personality/accent

---

## 📞 Support

If LARY agent isn't working:

1. Check `.env` has correct API key
2. Verify internet connection
3. Check OpenAI account has active subscription
4. Look at OpenAI error message (appears in chat UI)
5. Review implementation notes in `FEATURE-LARY-AGENT.md`

---

**Happy chatting with LARY!** 🤖✨
