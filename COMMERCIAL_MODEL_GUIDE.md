# Using Commercial Models for Faster Testing

The Insight Synthesizer can use OpenAI's API for much faster synthesis during development and testing. The local Ollama model remains the default for production use.

## Setup

1. **Install OpenAI package** (if not already installed):
   ```bash
   pip install openai
   ```

2. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

3. **Enable commercial model**:
   ```bash
   export USE_COMMERCIAL_MODEL=true
   ```

## Usage

### Quick Toggle Script

Use the provided script to switch between modes:

```bash
# Switch to commercial (OpenAI)
source switch_model.sh commercial

# Switch back to local (Ollama)
source switch_model.sh local

# Check current mode
source switch_model.sh
```

### Manual Toggle

```bash
# Enable commercial model
export USE_COMMERCIAL_MODEL=true

# Disable (back to local)
unset USE_COMMERCIAL_MODEL
```

### Running Analysis

Once enabled, just run the synthesizer normally:

```bash
python synthesizer.py
```

You'll see a cyan message: `"Using OpenAI for synthesis (faster)"` when commercial mode is active.

## Benefits

- **Speed**: 10-20x faster synthesis (seconds vs minutes)
- **No Local Resources**: Doesn't use your laptop's CPU/GPU
- **Same Output**: Produces identical report structure
- **Automatic Fallback**: Falls back to Ollama if API fails

## Costs

Using GPT-4o-mini (default):
- ~$0.001 per theme synthesized
- Full analysis of 20 themes ≈ $0.02

## Configuration

The commercial model uses GPT-4o-mini by default. To change:

1. Edit `src/insight_synthesizer/synthesis_openai.py`
2. Change `model="gpt-4o-mini"` to your preferred model:
   - `gpt-4o` - More capable but slower/expensive
   - `gpt-3.5-turbo` - Faster but less capable

## Troubleshooting

### "OPENAI_API_KEY environment variable not set"
Set your API key:
```bash
export OPENAI_API_KEY='sk-...'
```

### "Commercial model failed, falling back to Ollama"
Check:
- API key is valid
- You have credits in your OpenAI account
- Internet connection is working

### Rate Limits
If you hit rate limits, the system automatically falls back to Ollama.

## Production Note

**Always use local Ollama for production** to ensure:
- No external dependencies
- Complete data privacy
- Predictable costs
- Consistent availability

The commercial option is purely for development speed.