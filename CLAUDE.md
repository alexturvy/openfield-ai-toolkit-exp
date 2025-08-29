# CLAUDE.md - AI Assistant Guidelines for openfield-ai-toolkit

## Project Context

This is a research insight extraction tool designed for trustworthy, traceable analysis of interview transcripts. The project prioritizes **quote verification** and **transparency** over complex AI features.

## Core Principles

### 1. Quote Verification is Sacred
- **NEVER** generate or paraphrase quotes
- Every quote must be traceable to source line numbers
- If you can't find it in the source, it doesn't exist
- This is our competitive advantage - researchers can trust our output

### 2. Simple > Clever
- Start with working code, not architecture
- Avoid premature abstractions
- Make the happy path work first
- Refactor only when patterns emerge from real usage

### 3. Transparency Over Intelligence
- Show your work at every step
- Users should understand what's happening
- Progress indicators and clear status messages
- Fail loudly with actionable error messages

## Code Guidelines

### DO:
```python
# Simple, obvious functions
def verify_quote(quote: str, source: str) -> bool:
    """Check if quote exists verbatim in source"""
    return quote in source

# Clear progress messages
print(f"Processing {len(interviews)} interviews...")
print(f"Found {len(quotes)} relevant quotes")
print(f"Verified {verified_count} quotes against source")
```

### DON'T:
```python
# Over-engineered abstractions
class AbstractAnalysisFrameworkFactory:
    def create_pipeline_strategy(self):
        pass

# Black box operations
print("Analyzing with advanced AI...")
```

## Current State (Main Branch)

The main branch contains:
- `neuro_transcripts/` - Interview transcripts for NeuroQuest project
- `modo_transcripts/` - Interview transcripts for Modo project
- Basic repository files

The complete v1 implementation is archived in branch: `archive/insight-synthesizer-v1`

## Development Priorities

### Phase 1: Core Quote Extraction (Build First)
1. Load interview transcripts
2. Parse research questions
3. Extract relevant quotes with LLM
4. **Verify every quote against source**
5. Generate traceable report

### Phase 2: Insights Layer
- Unexpected findings detection
- Contradiction/tension analysis
- Pattern recognition (JTBD, mental models)

### Phase 3: Intelligence Layer
- Cross-study comparisons
- Historical patterns
- Methodology evolution

## What NOT to Build

1. **Complex Pipelines** - The archived v1 had 7 stages. Start simpler.
2. **Embedding Caches** - Not needed until processing 100s of interviews
3. **Universal Processors** - Just handle interview transcripts well
4. **Abstract Frameworks** - Build concrete solutions first

## Testing Requirements

```python
def test_quote_verification():
    """This is our core value prop - MUST work"""
    source = "Participant: I love this feature"
    quote = "I love this feature"
    assert verify_quote(quote, source) == True
    
def test_no_hallucination():
    """This MUST always fail"""
    source = "Participant: I love this"
    fake = "I hate this"
    assert verify_quote(fake, source) == False
```

## File Structure Conventions

```
openfield-ai-toolkit/
├── synthesizer.py          # Main entry point (when built)
├── requirements.txt        # Python dependencies
├── tests/                  # Test files
│   └── test_verification.py # Quote verification tests
├── neuro_transcripts/      # Interview data (gitignored)
├── modo_transcripts/       # Interview data (gitignored)
└── output/                # Generated reports (gitignored)
```

## Key Metrics

Track what matters:
- Quote verification rate (must be 100%)
- Questions answered (target 80%+)
- Processing time (<30 seconds for 10 interviews)
- Researcher trust (only metric that really matters)

## Common Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run synthesizer (when built)
python synthesizer.py --interviews neuro_transcripts/ --questions research_plan.md
```

## Error Handling

Always fail gracefully:
```python
try:
    content = load_interview(path)
except FileNotFoundError:
    print(f"WARNING: Skipping {path} - file not found")
    continue
    
# Never silent failures
if not quotes:
    print("No quotes found. Try:")
    print("  - Rephrasing the research question")
    print("  - Checking if topic was discussed")
```

## Remember

We're building a tool that helps researchers **trust their deliverables**, not a technology showcase. Every feature should make quote verification more reliable or the process more transparent.

If you're unsure whether to add a feature, ask: "Does this help verify quotes or make the process clearer?" If not, skip it.