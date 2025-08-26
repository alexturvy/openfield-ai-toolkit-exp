# Local Memory Vault - Detailed Implementation Plan

## Overview

The Local Memory Vault is a semantic search and knowledge management system designed to help teams instantly retrieve relevant past work, research findings, and project artifacts. Unlike traditional file search that relies on exact keywords, the Memory Vault understands the meaning behind queries and surfaces conceptually related content.

## Core Concept

Think of it as a "second brain" for your organization's collective knowledge - it remembers everything you've worked on and helps you find it when you need it, even if you can't remember the exact words used.

More importantly, it's a **"Serendipity Engine"** that surfaces connections you didn't know existed. Unlike traditional search (Google Drive, Dropbox) that only finds files with specific keywords, Memory Vault understands concepts and relationships, helping you discover relevant insights you didn't know to look for.

## MVP Scope

### What's In
1. **Document Ingestion Pipeline**
   - Support for common formats: TXT, MD, DOCX, PDF, RTF
   - Automatic text extraction and preprocessing
   - Metadata preservation (date, author, project tags)
   
2. **Semantic Indexing**
   - Vector embeddings using same model as Insight Synthesizer (all-MiniLM-L6-v2)
   - Efficient storage using FAISS for local-only operation
   - Chunking strategy that preserves context
   
3. **Search Interface**
   - Natural language queries ("onboarding friction in mobile apps")
   - Relevance scoring and ranking
   - Context preview with highlighted matches
   - Source attribution and file paths
   
4. **Project Organization**
   - Simple folder-based project structure
   - Project-scoped searches
   - Cross-project search capability

### What's Out (For Now)
- Real-time document monitoring
- Collaborative features
- Web UI (CLI only for MVP)
- Integration with other tools
- Advanced filtering/faceting

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Memory Vault CLI                        │
├─────────────────────────────────────────────────────────────┤
│                    Search Interface Layer                    │
│  - Query parsing & expansion                                │
│  - Result ranking & formatting                              │
│  - Context extraction                                       │
├─────────────────────────────────────────────────────────────┤
│                   Retrieval Engine (FAISS)                  │
│  - Vector similarity search                                 │
│  - K-nearest neighbor retrieval                            │
│  - Metadata filtering                                      │
├─────────────────────────────────────────────────────────────┤
│                    Indexing Pipeline                        │
│  - Document ingestion & parsing                            │
│  - Text chunking & preprocessing                          │
│  - Embedding generation                                    │
│  - Index building & updating                              │
├─────────────────────────────────────────────────────────────┤
│                  Storage Layer (SQLite)                     │
│  - Document metadata                                       │
│  - Chunk mappings                                         │
│  - Project configurations                                  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion Flow**
   ```
   Documents → Parser → Chunker → Embedder → Index Builder → Storage
                ↓         ↓          ↓            ↓
             Metadata  Chunks   Vectors    FAISS Index + SQLite
   ```

2. **Search Flow**
   ```
   Query → Embedder → FAISS Search → Result Reranking → Context Extraction → Display
              ↓            ↓               ↓                    ↓
           Vector    Similar Chunks   Scored Results    Full Context
   ```

### Key Design Decisions

1. **Hybrid Storage Approach**
   - FAISS for vector search (efficient, local)
   - SQLite for metadata and mappings (flexible, queryable)
   - Original files remain in place (no duplication)

2. **Chunking Strategy**
   - Sliding window with overlap (prevent context loss)
   - Adaptive chunk size based on document type
   - Preserve document structure markers

3. **Embedding Model**
   - Same as Insight Synthesizer for consistency
   - Small enough for CPU inference
   - Good balance of quality and speed

## Implementation Details

### Core Classes & Modules

```python
memory_vault/
├── __init__.py
├── cli.py                    # CLI entry point
├── indexing/
│   ├── __init__.py
│   ├── document_parser.py    # Multi-format parsing
│   ├── chunker.py           # Smart chunking logic
│   ├── embedder.py          # Vector generation
│   └── index_builder.py     # FAISS index management
├── storage/
│   ├── __init__.py
│   ├── metadata_store.py    # SQLite operations
│   ├── vector_store.py      # FAISS wrapper
│   └── project_manager.py   # Project organization
├── search/
│   ├── __init__.py
│   ├── query_processor.py   # Query parsing/expansion
│   ├── retriever.py         # Vector search
│   ├── reranker.py         # Result scoring
│   └── context_extractor.py # Snippet generation
└── utils/
    ├── __init__.py
    └── config.py           # Configuration management
```

### Key Algorithms

1. **Smart Chunking**
   ```python
   def chunk_document(text: str, doc_type: str) -> List[Chunk]:
       # Adaptive chunking based on document structure
       if doc_type == "interview":
           return chunk_by_speaker_turns(text)
       elif doc_type == "report":
           return chunk_by_sections(text)
       else:
           return sliding_window_chunk(text, size=512, overlap=128)
   ```

2. **Relevance Scoring**
   ```python
   def score_results(query_vec, result_vecs, metadata):
       # Combine vector similarity with metadata boosts
       base_scores = cosine_similarity(query_vec, result_vecs)
       recency_boost = calculate_recency_factor(metadata.dates)
       project_boost = calculate_project_relevance(metadata.projects)
       return base_scores * recency_boost * project_boost
   ```

3. **Context Extraction**
   ```python
   def extract_context(chunk, surrounding_chunks, query):
       # Expand chunk to include relevant surrounding context
       context = expand_to_sentence_boundaries(chunk)
       if needs_more_context(chunk, query):
           context = include_surrounding_chunks(context, surrounding_chunks)
       return highlight_relevant_portions(context, query)
   ```

4. **Concept Expansion & Discovery**
   ```python
   def expand_query_concepts(query: str) -> List[str]:
       # Find related concepts that user might not have searched for
       base_embedding = embed(query)
       
       # Find conceptually related terms from the corpus
       related_concepts = find_nearest_concepts(base_embedding, n=10)
       
       # Identify implicit themes
       implicit_themes = extract_latent_themes(related_concepts)
       
       # Return expanded search space
       return [query] + related_concepts + implicit_themes
   ```

5. **Cross-Document Pattern Recognition**
   ```python
   def find_hidden_connections(documents: List[Document]) -> List[Connection]:
       # Identify non-obvious relationships between documents
       connections = []
       
       for doc_a, doc_b in document_pairs:
           # Semantic similarity
           if semantic_similarity(doc_a, doc_b) > threshold:
               connections.append(ConceptualLink(doc_a, doc_b))
           
           # Contradictions
           if detect_contradiction(doc_a, doc_b):
               connections.append(Contradiction(doc_a, doc_b))
           
           # Evolution over time
           if is_temporal_evolution(doc_a, doc_b):
               connections.append(Evolution(doc_a, doc_b))
       
       return connections
   ```

## User Experience

### CLI Interface

```bash
# Index a project directory
memory-vault index --project "Mobile App Redesign" /path/to/project/docs

# Search within a project
memory-vault search --project "Mobile App Redesign" "user onboarding friction"

# Search across all projects
memory-vault search --all "accessibility compliance requirements"

# List indexed projects
memory-vault list-projects

# Update index for a project
memory-vault reindex --project "Mobile App Redesign"
```

### Example Output

```
$ memory-vault search --project "Mobile App Redesign" "onboarding friction"

Found 3 relevant results:

[1] user_interview_transcript_03.txt (95% match)
    Project: Mobile App Redesign
    Date: 2024-11-15
    
    "...the main friction point during onboarding was the number of 
    permission requests. Users felt overwhelmed when asked for camera,
    location, and notification access all at once..."
    
[2] usability_test_findings.docx (87% match)
    Project: Mobile App Redesign  
    Date: 2024-11-20
    
    "...participants consistently dropped off at the profile creation
    step. The form was too long and asked for information users didn't
    feel was necessary at that stage..."

[3] competitive_analysis.md (72% match)
    Project: Mobile App Redesign
    Date: 2024-11-10
    
    "...Competitor apps have simplified their onboarding to just email
    and password, deferring other data collection until after the user
    has experienced value..."

DISCOVERED CONNECTIONS:
- Related Pattern: "cognitive overload" appears in 4 other documents
  → accessibility_audit.pdf: Discussion of cognitive load in UI
  → design_principles.md: Team principles about progressive disclosure
  
- Potential Contradiction: 
  → product_requirements.docx mentions "collect all user data upfront"
  → This conflicts with user feedback about overwhelming onboarding

- Historical Context:
  → Similar issues in "Desktop App v2" project (2023)
  → Solution involved staged data collection
```

## Input Flexibility

### Supported File Types (MVP)
- **Text**: .txt, .md
- **Documents**: .docx, .pdf, .rtf
- **Future**: .json, .csv, .pptx

### Metadata Extraction
- Automatic extraction from file properties
- Convention-based parsing (e.g., `YYYY-MM-DD_interview_name.txt`)
- Optional metadata sidecar files (`.meta.json`)

### Project Structure Convention
```
projects/
├── mobile-app-redesign/
│   ├── research/
│   │   ├── interviews/
│   │   ├── surveys/
│   │   └── competitive-analysis/
│   ├── design/
│   │   ├── wireframes/
│   │   └── prototypes/
│   └── .memory-vault/
│       └── config.json
```

## Integration Points (Future)

### With Insight Synthesizer
- Index synthesizer outputs automatically
- Use Memory Vault to find related past research
- Surface historical patterns during analysis

### With PRD Generator  
- Pull relevant research from Memory Vault
- Find similar PRDs from past projects
- Auto-populate sections with historical context

### Shared Infrastructure
- Common embedding model
- Shared document processing pipeline
- Unified configuration system

## Performance Considerations

### Indexing Performance
- Batch processing for multiple files
- Incremental updates (only process changes)
- Parallel embedding generation
- Progress indicators for large datasets

### Search Performance
- Sub-second search for <100k documents
- Lazy loading of full document content
- Caching of frequent queries
- Approximate nearest neighbor search

### Storage Efficiency
- Vectors: ~1.5KB per chunk (384 dimensions × 4 bytes)
- Metadata: ~200 bytes per chunk
- 10,000 documents ≈ 500MB total storage

## Security & Privacy

### Data Protection
- All processing happens locally
- No external API calls
- Files remain in original locations
- Optional encryption for index files

### Access Control (Future)
- Project-level permissions
- User authentication
- Audit logging

## Success Metrics

### Quantitative
- Search latency < 1 second
- Precision @ 10 > 80%
- Index time < 1 minute per 1000 documents
- Storage overhead < 10% of original data

### Qualitative
- Users find relevant content they forgot existed
- Reduced time spent searching for past work
- Increased reuse of research insights
- Better institutional memory

## Implementation Timeline

### Week 1: Core Infrastructure
- Set up project structure
- Implement document parsing pipeline
- Create basic chunking algorithm
- Test with sample documents

### Week 2: Vector Search
- Integrate FAISS
- Implement embedding generation
- Build index creation pipeline
- Create basic search functionality

### Week 3: Search Quality
- Implement relevance scoring
- Add context extraction
- Create result formatting
- Build CLI interface

### Week 4: Polish & Testing
- Add progress indicators
- Implement error handling
- Create comprehensive tests
- Write user documentation

## Open Questions & Decisions

1. **Chunking Size**: What's the optimal balance between context and search precision?
2. **Update Strategy**: How often should we reindex? On-demand or scheduled?
3. **Project Definition**: Folder-based or explicit configuration?
4. **Result Count**: How many results by default? Pagination?
5. **Query Expansion**: Should we automatically expand queries with synonyms?

## Next Steps

1. Validate technical approach with small prototype
2. Test FAISS performance with realistic data volumes
3. Gather feedback on CLI interface design
4. Define integration APIs for other tools
5. Plan for future web UI