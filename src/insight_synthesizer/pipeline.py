"""Main pipeline orchestration for Insight Synthesizer."""

from typing import List, Dict
from pathlib import Path
import numpy as np
from rich.console import Console

from .document_processing import (
    extract_text_from_file, 
    find_supported_files,
    check_dependencies,
    StructureClassifier,
    AdaptiveChunker
)
from .analysis import (
    generate_embeddings,
    perform_clustering,
    synthesize_insights,
    ensure_ollama_ready
)
from .analysis.embeddings import TextChunk
from .output import generate_markdown_report
from .utils import ProgressReporter, get_progress_manager, ProgressStage
from .validation import ThemeValidator

console = Console()


class InsightSynthesizer:
    """Main orchestrator for the insight synthesis pipeline."""
    
    def __init__(self):
        """Initialize the synthesizer with required components."""
        self.progress_reporter = ProgressReporter()
        self.classifier = StructureClassifier(progress_reporter=self.progress_reporter)
        self.chunker = AdaptiveChunker(progress_reporter=self.progress_reporter)
        self.validator = ThemeValidator(progress_reporter=self.progress_reporter)
        self.goal_manager = None  # Will be set when research goals are provided
        
    def analyze_directory(self, directory_path: str, lens: str, file_selection: str = "all", research_goals=None) -> str:
        """
        Analyze supported files in a directory based on selection criteria.
        
        Args:
            directory_path: Path to directory containing research files
            lens: Analysis lens to apply
            file_selection: File selection criteria ("all", ranges like "1-3", or indices like "1,3,5")
            research_goals: Optional ResearchGoal object for focused analysis
            
        Returns:
            Path to generated report
        """
        check_dependencies()
        
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")
        
        # Find supported files
        files = find_supported_files(directory)
        if not files:
            raise ValueError("No supported files found in directory")
        
        # Parse file selection and filter files
        try:
            from .cli import parse_file_selection
            selected_indices = parse_file_selection(file_selection, len(files))
            selected_files = [files[i-1] for i in selected_indices]
        except ValueError as e:
            raise ValueError(f"Invalid file selection '{file_selection}': {e}")
        
        console.print(f"[green]Processing {len(selected_files)} of {len(files)} files[/]")
        
        return self.analyze_files(selected_files, lens, research_goals)
    
    def analyze_files(self, file_paths: List[Path], lens: str, research_goals=None) -> str:
        """
        Analyze specific files using the complete pipeline.
        
        Args:
            file_paths: List of file paths to analyze
            lens: Analysis lens to apply
            research_goals: Optional ResearchGoal object for focused analysis
            
        Returns:
            Path to generated report
        """
        ensure_ollama_ready()
        
        # Initialize research goal manager if goals provided
        if research_goals:
            from .research.goal_manager import ResearchGoalManager
            self.goal_manager = ResearchGoalManager(research_goals)
            console.print(f"[green]Analyzing with {len(research_goals.primary_questions)} research questions[/]")
        
        # Initialize unified progress manager
        progress_manager = get_progress_manager()
        progress_manager.start_pipeline()
        
        try:
            console.print(f"[bold blue]Starting analysis with {lens} lens[/]")
            
            # Stage 1: Document processing and adaptive chunking
            with progress_manager.stage_context(ProgressStage.DOCUMENT_PROCESSING, len(file_paths), "Processing and chunking documents") as stage_task:
                all_chunks = []
                
                for i, file_path in enumerate(file_paths):
                    try:
                        progress_manager.set_stage_status(ProgressStage.DOCUMENT_PROCESSING, f"Processing {file_path.name}")
                        
                        # Extract text
                        text = extract_text_from_file(file_path)
                        
                        # Classify document structure
                        classification = self.classifier.classify_document(text, file_path.name)
                        
                        # Adaptive chunking
                        chunks = self.chunker.chunk_document(text, file_path, classification)
                        
                        # Convert to legacy format for compatibility with existing analysis pipeline
                        legacy_chunks = self._convert_to_legacy_chunks(chunks)
                        all_chunks.extend(legacy_chunks)
                        
                        progress_manager.log_info(f"Generated {len(legacy_chunks)} chunks from {file_path.name}")
                        
                    except Exception as e:
                        progress_manager.log_error(f"Error processing {file_path.name}: {e}")
                    finally:
                        progress_manager.update_stage(ProgressStage.DOCUMENT_PROCESSING, 1)
            
            progress_manager.log_success(f"Generated {len(all_chunks)} chunks from {len(file_paths)} files")
            
            # Stage 2: Embedding generation
            with progress_manager.stage_context(ProgressStage.EMBEDDING_GENERATION, len(all_chunks), "Generating embeddings") as stage_task:
                all_chunks = generate_embeddings(all_chunks, progress_manager)
            
            # Stage 3: Clustering
            with progress_manager.stage_context(ProgressStage.CLUSTERING, 1, "Performing clustering analysis") as stage_task:
                if self.goal_manager:
                    # Use research-aware clustering
                    from .analysis.research_clustering import create_research_aware_clusters
                    
                    # Extract embeddings from chunks
                    embeddings = np.array([chunk.embedding for chunk in all_chunks])
                    
                    progress_manager.set_stage_status(ProgressStage.CLUSTERING, "Performing research-aware clustering")
                    clusters = create_research_aware_clusters(
                        all_chunks, embeddings, self.goal_manager, self.progress_reporter
                    )
                    progress_manager.log_info(f"Created {len(clusters)} research-aware clusters")
                else:
                    # Use standard clustering
                    _, clusters = perform_clustering(all_chunks, self.progress_reporter, progress_manager)
                    
                progress_manager.update_stage(ProgressStage.CLUSTERING, 1)
            
            # Stage 4: LLM synthesis
            with progress_manager.stage_context(ProgressStage.INSIGHT_SYNTHESIS, len(clusters), "Synthesizing insights from clusters") as stage_task:
                synthesized_data = []
                
                for i, cluster in enumerate(clusters):
                    try:
                        progress_manager.set_stage_status(ProgressStage.INSIGHT_SYNTHESIS, f"Synthesizing cluster {cluster.cluster_id} ({i+1}/{len(clusters)})")
                        synthesis = synthesize_insights(cluster, lens)
                        synthesized_data.append(synthesis)
                        progress_manager.log_info(f"Synthesized theme: {synthesis.get('theme_name', 'Unnamed theme')}")
                    except Exception as e:
                        progress_manager.log_error(f"Error synthesizing cluster {cluster.cluster_id}: {e}")
                    finally:
                        progress_manager.update_stage(ProgressStage.INSIGHT_SYNTHESIS, 1)

            # Stage 5: Tension analysis
            tensions = []  # Default to empty list
            try:
                console.print("[bold blue]Analyzing tensions and contradictions[/]")
                from .analysis.tensions import detect_tensions
                tensions = detect_tensions(synthesized_data, self.progress_reporter)
            except Exception as e:
                progress_manager.log_warning(f"Tension analysis skipped due to error: {e}")
                tensions = []  # Continue with empty tensions list

            # Add research coverage validation if using goals
            coverage_report = None
            if self.goal_manager and synthesized_data:
                console.print("\n[bold blue]Analyzing research coverage[/]")
                from .validation.research_validator import ResearchCoverageValidator
                
                coverage_validator = ResearchCoverageValidator(self.goal_manager)
                coverage_report = coverage_validator.analyze_coverage(synthesized_data)
                
                # Display coverage summary
                coverage_validator.display_coverage_report(coverage_report)
            
            # Stage 6: Theme validation
            with progress_manager.stage_context(ProgressStage.VALIDATION, len(synthesized_data), "Validating theme coverage") as stage_task:
                validation_result = self.validator.validate_themes(synthesized_data, file_paths, progress_manager)
                progress_manager.update_stage(ProgressStage.VALIDATION, len(synthesized_data))
            
            # Stage 7: Report generation
            with progress_manager.stage_context(ProgressStage.REPORT_GENERATION, 1, "Generating markdown report") as stage_task:
                report_path = "synthesis_report.md"
                # Generate report with all components
                report_kwargs = {
                    'synthesized_data': synthesized_data,
                    'lens': lens,
                    'output_path': report_path,
                    'validation_result': validation_result,
                    'tensions': tensions,
                    'research_goals': research_goals
                }
                
                # Add coverage report if available
                if coverage_report:
                    report_kwargs['coverage_report'] = coverage_report
                    
                generate_markdown_report(**report_kwargs)
                progress_manager.update_stage(ProgressStage.REPORT_GENERATION, 1)
            
            # Display pipeline summary
            self.progress_reporter.display_summary()
            
            progress_manager.log_success(f"Analysis complete! Report saved to {report_path}")
            progress_manager.log_info(f"Validation: {validation_result.validation_summary}")
            
            return report_path
            
        finally:
            progress_manager.finish()
    
    def _convert_to_legacy_chunks(self, adaptive_chunks) -> List[TextChunk]:
        """Convert AdaptiveChunk objects to legacy TextChunk format."""
        legacy_chunks = []
        for chunk in adaptive_chunks:
            legacy_chunk = TextChunk(
                text=chunk.text,
                source_file=chunk.source_file,
                embedding=None,
                cluster_id=None
            )
            # Store adaptive metadata for later use
            legacy_chunk._adaptive_metadata = chunk.metadata
            legacy_chunks.append(legacy_chunk)
        return legacy_chunks