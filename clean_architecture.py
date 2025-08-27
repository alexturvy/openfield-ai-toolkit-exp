x"""
Clean Architecture for Insight Synthesizer
This is what I'd build if starting from scratch
"""

from dataclasses import dataclass
from typing import List, Dict, Protocol, Optional
from pathlib import Path
from enum import Enum

# =============================================================================
# 1. CLEAR DATA MODELS (No more dicts!)
# =============================================================================

@dataclass
class ResearchPlan:
    """What we're trying to answer."""
    questions: List[str]
    background: Optional[str] = None
    assumptions: List[str] = None
    methodology: Optional[str] = None

@dataclass  
class Document:
    """A source document."""
    path: Path
    content: str
    doc_type: 'DocumentType'
    metadata: Dict

@dataclass
class Chunk:
    """A semantic unit of text."""
    text: str
    source: Document
    chunk_type: str
    speaker: Optional[str] = None
    embedding: Optional[List[float]] = None

@dataclass
class Theme:
    """An identified pattern."""
    name: str
    summary: str
    supporting_chunks: List[Chunk]
    confidence: float
    addresses_questions: List[int]  # Indices of research questions

@dataclass
class Report:
    """Final output."""
    research_plan: ResearchPlan
    themes: List[Theme]
    coverage_analysis: Dict
    tensions: List[Dict]
    markdown: str

# =============================================================================
# 2. PROMPT REGISTRY (All prompts in ONE place)
# =============================================================================

class PromptRegistry:
    """Single source of truth for all LLM prompts."""
    
    # Document classification
    CLASSIFY_DOCUMENT = """
    Analyze this document and identify its type...
    {document_sample}
    Return JSON with: type, confidence, chunking_strategy
    """
    
    # Research plan extraction  
    EXTRACT_RESEARCH_PLAN = """
    Extract research questions and context from this document...
    {content}
    Return JSON with: questions, background, assumptions
    """
    
    # Theme synthesis
    SYNTHESIZE_THEME = """
    Analyze these text chunks for {lens}...
    {chunks}
    Return JSON with: theme_name, summary, key_insights
    """
    
    # Quote extraction
    EXTRACT_QUOTES = """
    Find quotes supporting this theme: {theme_name}
    From content: {content}
    Return JSON with: quotes, confidence
    """
    
    @classmethod
    def get(cls, prompt_name: str, **kwargs) -> str:
        """Get a prompt with variables filled in."""
        prompt = getattr(cls, prompt_name)
        return prompt.format(**kwargs)

# =============================================================================
# 3. CLEAN PIPELINE WITH CLEAR STAGES
# =============================================================================

class Pipeline:
    """Main coordinator - simple and clear."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.llm = UnifiedLLMClient(config.llm_config)
        self.embedder = EmbeddingService(config.embedding_model)
        
    def run(self, 
            research_plan_path: Path,
            document_paths: List[Path],
            lens: str = "pain_points") -> Report:
        """
        Simple, clear pipeline with defined stages.
        Each stage has ONE responsibility.
        """
        
        # Stage 1: Parse research plan
        research_plan = self._parse_research_plan(research_plan_path)
        
        # Stage 2: Process documents into chunks
        chunks = []
        for doc_path in document_paths:
            document = self._load_document(doc_path)
            doc_chunks = self._chunk_document(document)
            chunks.extend(doc_chunks)
        
        # Stage 3: Generate embeddings
        chunks = self._embed_chunks(chunks)
        
        # Stage 4: Cluster into themes
        clusters = self._cluster_chunks(chunks)
        
        # Stage 5: Synthesize themes
        themes = []
        for cluster in clusters:
            theme = self._synthesize_theme(cluster, lens, research_plan)
            themes.append(theme)
        
        # Stage 6: Validate with quotes
        themes = self._validate_themes(themes, document_paths)
        
        # Stage 7: Generate report
        report = self._generate_report(research_plan, themes)
        
        return report
    
    def _parse_research_plan(self, path: Path) -> ResearchPlan:
        """Parse research plan with LLM assistance."""
        content = path.read_text()
        
        # Try pattern extraction first
        questions = self._extract_questions_with_patterns(content)
        
        # Enhance with LLM if needed
        if len(questions) < 2:
            prompt = PromptRegistry.get('EXTRACT_RESEARCH_PLAN', content=content)
            response = self.llm.generate_json(prompt)
            questions.extend(response.get('questions', []))
        
        return ResearchPlan(questions=questions)
    
    def _chunk_document(self, document: Document) -> List[Chunk]:
        """Smart chunking based on document type."""
        strategy = ChunkingStrategy.for_document_type(document.doc_type)
        return strategy.chunk(document)

# =============================================================================
# 4. PLUGIN SYSTEM FOR EXTENSIBILITY
# =============================================================================

class DocumentHandler(Protocol):
    """Interface for document handlers."""
    
    def can_handle(self, path: Path) -> bool:
        """Check if this handler can process the file."""
        ...
    
    def load(self, path: Path) -> Document:
        """Load and classify the document."""
        ...
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Chunk the document appropriately."""
        ...

class InterviewHandler:
    """Handles interview transcripts."""
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix in ['.txt', '.docx']
    
    def chunk(self, document: Document) -> List[Chunk]:
        # Smart speaker-turn chunking
        return chunk_by_speaker_turns(document)

class NotesHandler:
    """Handles meeting notes."""
    
    def chunk(self, document: Document) -> List[Chunk]:
        # Paragraph-based chunking
        return chunk_by_paragraphs(document)

# Registry of handlers
DOCUMENT_HANDLERS = [
    InterviewHandler(),
    NotesHandler(),
    SurveyHandler(),
    # Easy to add more...
]

# =============================================================================
# 5. CONFIGURATION IN ONE PLACE
# =============================================================================

@dataclass
class PipelineConfig:
    """All configuration in one place."""
    
    # LLM settings
    llm_provider: str = "ollama"  # or "openai"
    llm_model: str = "mistral"
    llm_temperature: float = 0.1
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Clustering settings
    min_cluster_size: int = 3
    max_cluster_size: int = 20
    
    # Processing settings
    max_chunk_size: int = 1500
    min_chunk_size: int = 200
    
    @classmethod
    def from_env(cls) -> 'PipelineConfig':
        """Load config from environment."""
        config = cls()
        
        if os.getenv('USE_COMMERCIAL_MODEL') == 'true':
            config.llm_provider = 'openai'
            config.llm_model = 'gpt-4o-mini'
        
        return config
    
    def to_dict(self) -> Dict:
        """Export config for logging."""
        return asdict(self)

# =============================================================================
# 6. SIMPLE CLI THAT JUST ORCHESTRATES
# =============================================================================

def main():
    """Simple CLI - just orchestration, no business logic."""
    import click
    
    @click.command()
    @click.option('--research-plan', type=click.Path(exists=True), required=True)
    @click.option('--documents', type=click.Path(exists=True), required=True)
    @click.option('--lens', default='pain_points')
    @click.option('--output', default='report.md')
    @click.option('--config', type=click.Path(exists=True))
    def synthesize(research_plan, documents, lens, output, config):
        """Run synthesis pipeline."""
        
        # Load config
        if config:
            pipeline_config = PipelineConfig.from_file(config)
        else:
            pipeline_config = PipelineConfig.from_env()
        
        # Find documents
        doc_paths = list(Path(documents).glob("**/*.txt"))
        
        # Run pipeline
        pipeline = Pipeline(pipeline_config)
        report = pipeline.run(
            research_plan_path=Path(research_plan),
            document_paths=doc_paths,
            lens=lens
        )
        
        # Save report
        Path(output).write_text(report.markdown)
        click.echo(f"✅ Report saved to {output}")
    
    synthesize()

# =============================================================================
# 7. EASY TESTING
# =============================================================================

def test_pipeline():
    """Everything is testable because it's decoupled."""
    
    # Can test each stage independently
    config = PipelineConfig(llm_provider="mock")
    pipeline = Pipeline(config)
    
    # Test document chunking
    doc = Document(path=Path("test.txt"), content="...", doc_type=DocumentType.INTERVIEW)
    chunks = pipeline._chunk_document(doc)
    assert len(chunks) > 0
    
    # Test theme synthesis with mock LLM
    mock_cluster = [Chunk(text="test", source=doc)]
    theme = pipeline._synthesize_theme(mock_cluster, "pain_points", ResearchPlan(questions=["Q1"]))
    assert theme.name != ""
    
    # Each component is independently testable!

# =============================================================================
# 8. CLEAR PACKAGE STRUCTURE
# =============================================================================

"""
insight_synthesizer/
├── __main__.py           # Entry point
├── cli.py               # CLI interface
├── pipeline.py          # Main coordinator
├── models.py            # Data models
├── prompts.py           # Prompt registry
├── config.py            # Configuration
├── llm/
│   └── client.py        # UnifiedLLMClient
├── documents/
│   ├── handlers.py      # Document handlers
│   ├── chunking.py      # Chunking strategies
│   └── classifiers.py   # Document classification
├── analysis/
│   ├── embeddings.py    # Embedding service
│   ├── clustering.py    # Clustering logic
│   └── synthesis.py     # Theme synthesis
├── validation/
│   └── quotes.py        # Quote extraction
└── reports/
    └── generator.py     # Report generation
"""