# Development Guide

This document provides technical details about the OpenField AI Toolkit architecture, implementation patterns, and development guidelines.

## Project Structure

```
openfield-ai-toolkit/
├── src/
│   └── insight_synthesizer/          # Main synthesizer module
│       ├── __init__.py
│       ├── cli.py                   # Command-line interface
│       ├── pipeline.py              # Main pipeline orchestration
│       ├── analysis/                # Analysis components
│       │   ├── clustering.py        # UMAP + HDBSCAN clustering
│       │   ├── embeddings.py        # Semantic embedding generation
│       │   ├── synthesis.py         # LLM synthesis
│       │   └── tensions.py          # Tension detection
│       ├── document_processing/     # Document handling
│       │   ├── adaptive_chunking.py # Smart chunking strategies
│       │   ├── file_handlers.py     # Multi-format file support
│       │   └── structure_classifier.py # Document structure detection
│       ├── output/                  # Report generation
│       │   └── report_generator.py  # Markdown report creation
│       ├── utils/                   # Utilities
│       │   ├── progress_manager.py  # Unified progress tracking
│       │   └── progress_reporter.py # Legacy progress reporting
│       └── validation/              # Theme validation
│           └── theme_validator.py   # Quote extraction & verification
├── tests/                           # Comprehensive test suite
├── sample_notes/                    # Example data for testing
├── docs/                           # Product requirements
└── synthesizer.py                  # Legacy entry point (wraps CLI)
```

## Architecture Overview

### Core Design Principles

1. **Modular Pipeline**: Each stage is independent and can be enhanced/replaced
2. **Source Anchoring**: Every insight must be traceable to original data
3. **Local-First**: No cloud dependencies in production (Ollama for LLM)
4. **Progressive Enhancement**: Start with statistical methods, enhance with LLM

### Key Components

#### 1. Document Processing Layer
- **Structure Classifier**: Detects document type (interview, notes, report)
- **Adaptive Chunker**: Uses document-aware chunking strategies
  - Speaker turns for interviews
  - Semantic boundaries for narratives
  - Section-based for structured documents
- **File Handlers**: Extensible system for multiple formats

#### 2. Analysis Pipeline
- **Embeddings**: Sentence transformers for semantic similarity
- **Clustering**: UMAP dimensionality reduction + HDBSCAN clustering
- **Synthesis**: LLM generates themes without fabricating quotes
- **Tensions**: Detects contradictions between themes
- **Validation**: Extracts real quotes from source material

#### 3. Progress & Reporting
- **Progress Manager**: Unified progress tracking with Rich library
- **Report Generator**: Comprehensive Markdown output
- **Speaker Attribution**: Tracks contributions throughout pipeline

## Key Implementation Details

### Speaker Attribution System
```python
# Speaker patterns are preserved from chunking through synthesis
chunk.metadata = {
    'speaker': 'Sarah Johnson',
    'is_interviewer': False,
    'content_type': 'dialogue'
}

# Flows through clustering
cluster.speaker_metadata = {
    'speakers': ['Sarah', 'Mike'],
    'speaker_count': 2,
    'is_participant_focused': True
}

# Into synthesis and reports
theme['speaker_distribution'] = {
    'Sarah Johnson': 3,
    'Mike Chen': 2
}
```

### Quote Extraction & Validation
```python
# Two-phase approach ensures accuracy:
# 1. LLM synthesizes themes WITHOUT quotes
# 2. Separate extraction finds real quotes from source

validator = ThemeValidator()
validation_result = validator.validate_themes(
    synthesized_data,  # Themes from LLM
    file_paths         # Original documents
)
```

### Progress Tracking
```python
# Unified progress manager for all stages
with progress_manager.stage_context(
    ProgressStage.DOCUMENT_PROCESSING,
    total_items=len(files),
    description="Processing documents"
):
    # Stage work here
    progress_manager.update_stage(ProgressStage.DOCUMENT_PROCESSING, 1)
```

## Testing Strategy

### Test Coverage
- **Unit Tests**: Individual components (chunking, clustering, validation)
- **Integration Tests**: Pipeline stages working together
- **Speaker Attribution Tests**: End-to-end speaker tracking
- **Edge Cases**: Unicode, malformed data, empty inputs

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_speaker_attribution.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Key Test Files
- `test_theme_validator.py`: Quote extraction and validation
- `test_speaker_attribution.py`: Speaker tracking through pipeline
- `test_progress_indicators.py`: Progress tracking functionality
- `test_pipeline_file_selection.py`: File selection logic

## Development Workflow

### Adding New Features

1. **File Format Support**
   ```python
   # Implement FileHandler protocol
   class NewFormatHandler:
       def can_handle(self, file_path: Path) -> bool
       def extract_text(self, file_path: Path) -> str
   
   # Register in FILE_HANDLERS
   ```

2. **Analysis Lenses**
   ```python
   # Add to ANALYSIS_LENSES in cli.py
   # Update synthesis prompts in synthesis.py
   ```

3. **Chunking Strategies**
   ```python
   # Add to ChunkingStrategy enum
   # Implement in AdaptiveChunker
   ```

### Code Style Guidelines

- **Type Hints**: Use everywhere for clarity
- **Docstrings**: Google style for all public functions
- **Error Handling**: Graceful degradation, informative messages
- **Logging**: Use progress_manager for user-facing status

### Common Patterns

```python
# Progress tracking pattern
with progress_manager.stage_context(...) as stage:
    for item in items:
        try:
            # Process item
            progress_manager.update_stage(stage, 1)
        except Exception as e:
            progress_manager.log_error(f"Error: {e}")

# Speaker attribution pattern
if hasattr(chunk, '_adaptive_metadata'):
    speaker = chunk._adaptive_metadata.get('speaker')
    is_interviewer = chunk._adaptive_metadata.get('is_interviewer', False)

# Validation pattern
if validation_result.avg_coverage_score < 0.5:
    console.print("[yellow]Warning: Low theme coverage[/]")
```

## Debugging Tips

### Common Issues

1. **No clusters formed**: Adjust HDBSCAN min_cluster_size
2. **Poor speaker detection**: Check regex patterns in adaptive_chunking.py
3. **Slow performance**: Reduce embedding model size or chunk count
4. **Quote extraction fails**: Verify Ollama is running and responsive

### Useful Debug Commands

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Test file processing
python -c "from src.insight_synthesizer.document_processing import extract_text_from_file; print(extract_text_from_file('test.txt'))"

# Test clustering parameters
python -c "from src.insight_synthesizer.analysis.clustering import perform_clustering; help(perform_clustering)"
```

## Performance Considerations

### Optimization Points
- **Embedding Generation**: Batch processing for efficiency
- **Clustering**: UMAP parameters affect speed/quality tradeoff
- **LLM Calls**: Parallel synthesis for multiple clusters
- **File I/O**: Lazy loading for large documents

### Resource Usage
- **Memory**: ~2GB for typical analysis (100 chunks)
- **CPU**: Embedding generation is CPU-intensive
- **Disk**: Minimal, only for report output
- **Network**: None (all local processing)

## Future Architecture Considerations

### Planned Improvements
- **Streaming Processing**: Handle very large documents
- **Incremental Analysis**: Add new documents to existing analysis
- **Plugin System**: Extensible file handlers and analysis modules
- **Caching Layer**: Reuse embeddings and classifications

### Integration Points
- **Memory Vault**: Share embedding infrastructure
- **PRD Generator**: Reuse synthesis and validation capabilities
- **External Tools**: Export to Miro, Figma, etc.

## Contributing

### Pull Request Process
1. Create feature branch from main
2. Add tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Submit PR with clear description

### Code Review Checklist
- [ ] Type hints added
- [ ] Docstrings complete
- [ ] Tests comprehensive
- [ ] Progress tracking integrated
- [ ] Error handling robust
- [ ] Documentation updated