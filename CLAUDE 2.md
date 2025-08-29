# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Openfield AI Toolkit is a suite of local-first AI tools designed to enhance the team's ability to focus on high-value strategic work. The toolkit streamlines various aspects of the design and research process while maintaining privacy, security, and control over client intellectual property.

### Three Core Tools

1. **Insight Synthesizer** (Current Focus)
   - Processes raw research data (interviews, transcripts, notes) into thematic outlines
   - Uses hybrid approach: semantic embeddings → statistical clustering → LLM synthesis
   - Outputs structured Markdown reports with source-anchored quotes

2. **PRD Generator** (Planned)
   - Processes diverse inputs (surveys, interviews, research) into structured PRDs
   - Supports problem statement validation workflows
   - Outputs comprehensive Product Requirements Documents with customizable templates

3. **Local Memory Vault** (Planned)
   - Semantic search over past project artifacts and research findings
   - Uses FAISS or SQLite vectors for fully offline operation
   - Enables instant retrieval of relevant past work by meaning, not keywords

### Strategic Vision
This toolkit creates a durable competitive advantage by leveraging AI to accelerate foundational work, freeing experts to focus on interpretation, narrative building, and strategic guidance. The modular design allows for future upgrades including internal model servers, persona builders, and journey-map composers.

## Development Commands

### Environment Setup
```bash
# Create virtual environment (if not exists)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Current Implementation (Insight Synthesizer)
```bash
# Run the main synthesizer
python3 synthesizer.py

# Run with virtual environment activated
source .venv/bin/activate && python3 synthesizer.py

# Run tests
python -m pytest tests/

# Run specific test suites
python -m pytest tests/test_speaker_attribution.py
python -m pytest tests/test_theme_validator.py
```

### Planned Module Structure
```bash
# Future CLI interfaces (not yet implemented)
python -m insight_synthesizer --input data/ --lens pain_points
python -m prd_generator --inputs survey.csv,interviews/ --template standard
python -m memory_vault --query "user onboarding research" --project-id ABC123
```

### Testing
```bash
# Test Insight Synthesizer with sample data
python3 synthesizer.py
# When prompted, enter: sample_notes
```

### Deployment Target
The ultimate goal is a standalone, single-file executable for macOS using PyInstaller. All code should be self-contained and avoid dependencies problematic for packaging.

## Architecture

### Shared Architecture Principles

- **Local-First**: All processing happens locally, no cloud dependencies in production
- **Source-Anchored**: Every insight must be traceable to original data
- **Modular Design**: Each tool exposes both CLI entry and importable Python API
- **Model Flexibility**: Development may use frontier models (GPT-4o), production uses local Ollama

### Current: Insight Synthesizer ✅ **MVP Complete**

**Core Components:**
1. **Document Processing** (`src/insight_synthesizer/document_processing/`):
   - File handlers for TXT, RTF, DOCX, PDF
   - Structure classifier for document type detection
   - Adaptive chunking with speaker attribution
2. **Analysis Pipeline** (`src/insight_synthesizer/pipeline.py`):
   - Stage 1: Document processing & adaptive chunking
   - Stage 2: Semantic embedding generation (sentence-transformers)
   - Stage 3: Statistical clustering (UMAP + HDBSCAN)
   - Stage 4: LLM synthesis via Ollama API
   - Stage 5: Tension analysis for contradictions
   - Stage 6: Theme validation with quote extraction
   - Stage 7: Report generation with speaker statistics
3. **Key Features Implemented**:
   - File selection (all, ranges, specific files)
   - Speaker attribution throughout pipeline
   - Progress indicators with Rich library
   - Theme validation with source quotes
   - Comprehensive test coverage (47 tests)

### Planned: PRD Generator

**Purpose**: Create comprehensive Product Requirements Documents from diverse inputs
**Inputs**: Survey results, interview transcripts, research findings, stakeholder feedback
**Outputs**: Structured PRD documents following best practices and templates
**Architecture**: Multi-format input processor + LLM synthesis + template engine

### Planned: Local Memory Vault

**Purpose**: Semantic search over project artifacts and institutional knowledge
**Technology**: FAISS or SQLite vector database for offline operation
**Features**: Document indexing, semantic retrieval, project-based organization
**Integration**: CLI search interface + Python API for other tools

### Key Dependencies

- **Local LLM**: Ollama with Mistral model (automatically installed/managed)
- **ML Stack**: sentence-transformers, UMAP, HDBSCAN, scikit-learn
- **Vector Search**: FAISS (planned for Memory Vault)
- **File Processing**: python-docx, PyPDF2, striprtf
- **UI**: Rich console library for interactive CLI

## Development Guidelines

### Code Style (From .cursor/rules/)
- Python 3.10+ with full type hints and Google-style docstrings
- Modular, readable, and well-commented for teammates unfamiliar with ML
- No external SaaS dependencies in runtime code
- Design every model call so model name/base URL is easily swappable

### Deployment Strategy
- **Development**: May call frontier cloud models (e.g., GPT-4o) for speed
- **Runtime**: Must call local open-source models (Mistral/Llama via Ollama)
- **Packaging**: Target standalone executable via PyInstaller for non-technical users

### Module Requirements
Each tool must expose:
- A CLI entry point (`python -m <module> ...`)
- A minimal importable Python API (`from module import ...`)
- Full offline operation (no SaaS dependencies)

### Project Philosophy
- **Augment, don't replace**: Free researchers for higher-value thinking
- **Client trust**: Maintain privacy and control over intellectual property
- **Durable advantage**: Build capabilities that remain effective as AI landscape evolves

### File Structure
```
├── synthesizer.py              # Current: Insight Synthesizer
├── requirements.txt            # Python dependencies
├── sample_notes/              # Test data (RTF interviews)
├── docs/                      # Product requirements and specs
├── .cursor/rules/             # Development guidelines
└── src/                       # Future: Modular structure
    ├── insight_synthesizer/   # Planned refactor
    ├── prd_generator/
    └── memory_vault/
```

## Common Development Tasks

### For Insight Synthesizer (Current)

**Adding New File Handlers:**
1. Implement the `FileHandler` protocol in `src/insight_synthesizer/document_processing/file_handlers.py`
2. Add to `FILE_HANDLERS` registry
3. Update `find_supported_files()` if needed

**Adding New Analysis Lenses:**
1. Add to `ANALYSIS_LENSES` in `src/insight_synthesizer/cli.py`
2. Update synthesis prompts in `src/insight_synthesizer/analysis/synthesis.py`
3. Consider lens-specific output fields in report generator

**Modifying Clustering Parameters:**
- UMAP settings: `src/insight_synthesizer/analysis/clustering.py`
- HDBSCAN settings: `src/insight_synthesizer/analysis/clustering.py`
- Chunk size limits: `src/insight_synthesizer/document_processing/adaptive_chunking.py`

**Working with Speaker Attribution:**
- Speaker patterns: `src/insight_synthesizer/document_processing/adaptive_chunking.py`
- Metadata flow: Preserved via `_adaptive_metadata` attribute
- Report formatting: `src/insight_synthesizer/output/report_generator.py`

### For Future Tools

**PRD Generator:**
- Input processing for multiple data formats (CSV, JSON, text)
- PRD template system with customizable sections
- Validation framework for problem statements and requirements
- Integration with survey tools and research platforms

**Local Memory Vault:**
- Document indexing pipelines for various file types
- Vector database management (FAISS/SQLite)
- Query expansion and relevance scoring
- Project-based data organization and access controls

## Recent Development (December 2024)

### Completed MVP Features
1. **Theme Validation System**:
   - Implemented quote extraction from source documents
   - Added confidence scoring and speaker attribution
   - Created comprehensive validation reports

2. **Speaker Attribution Pipeline**:
   - Fixed regex patterns for robust speaker detection
   - Preserved speaker metadata through all pipeline stages
   - Added speaker statistics to reports

3. **File Selection Interface**:
   - Flexible selection: all, ranges (1-3), specific (1,3,5)
   - Clear file listing with indices
   - Validation of user input

4. **Progress Indicators**:
   - Unified progress manager with Rich library
   - Stage-based progress tracking
   - Real-time status updates and logging

5. **Test Coverage**:
   - 47 comprehensive tests
   - Speaker attribution end-to-end tests
   - Theme validation unit and integration tests
   - Edge case handling

### Key Patterns Established
- Use `_adaptive_metadata` to preserve chunking metadata
- Progress tracking via context managers
- Two-phase synthesis: themes first, quotes separately
- Graceful degradation for missing data

## Troubleshooting

### Ollama Issues
- Tool automatically installs/manages Ollama and Mistral model
- Timeout settings: `OLLAMA_TIMEOUT`, `OLLAMA_RETRY_DELAY`, `OLLAMA_MAX_RETRIES`
- Server management: `start_ollama_server()`, `ensure_ollama_ready()`

### Clustering Problems
- No clusters formed: Adjust `min_cluster_size` and `min_samples` in HDBSCAN
- Too many small clusters: Increase `min_cluster_size`
- Poor quality clusters: Modify UMAP `n_neighbors` and `min_dist`

### Memory/Performance
- Large datasets: Adjust `MAX_CHUNK_SIZE` and `MIN_CHUNK_SIZE`
- Embedding model: Currently uses 'all-MiniLM-L6-v2' (lightweight)