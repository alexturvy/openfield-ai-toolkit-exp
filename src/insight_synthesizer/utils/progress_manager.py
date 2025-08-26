"""Unified progress management system for the Insight Synthesizer pipeline."""

from typing import Dict, Optional, Any, List
import time
from contextlib import contextmanager
from rich.console import Console
from rich.progress import (
    Progress, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn, 
    TimeRemainingColumn,
    SpinnerColumn,
    MofNCompleteColumn,
    TimeElapsedColumn
)
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from dataclasses import dataclass
from enum import Enum


class ProgressStage(Enum):
    """Main pipeline stages for progress tracking."""
    INITIALIZATION = "Initialization"
    DOCUMENT_PROCESSING = "Document Processing"
    EMBEDDING_GENERATION = "Embedding Generation"
    CLUSTERING = "Clustering Analysis"
    INSIGHT_SYNTHESIS = "Insight Synthesis"
    VALIDATION = "Theme Validation"
    REPORT_GENERATION = "Report Generation"


@dataclass
class StageProgress:
    """Progress information for a pipeline stage."""
    stage: ProgressStage
    current_step: str
    progress: float  # 0.0 to 1.0
    total_steps: int
    completed_steps: int
    estimated_time_remaining: Optional[float] = None
    details: Optional[str] = None


class UnifiedProgressManager:
    """Manages progress indicators across the entire pipeline with Rich integration."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the progress manager."""
        self.console = console or Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )
        self.stage_tasks: Dict[ProgressStage, int] = {}
        self.current_stage: Optional[ProgressStage] = None
        self.stage_start_times: Dict[ProgressStage, float] = {}
        self.overall_task: Optional[int] = None
        self.is_active = False
        
    def start_pipeline(self, total_stages: int = 7) -> None:
        """Start the overall pipeline progress tracking."""
        self.is_active = True
        self.progress.start()
        self.overall_task = self.progress.add_task(
            "[bold blue]Overall Pipeline Progress", 
            total=total_stages
        )
        
    def start_stage(self, stage: ProgressStage, total_items: int, description: str = "") -> int:
        """
        Start progress tracking for a specific stage.
        
        Args:
            stage: The pipeline stage
            total_items: Total number of items to process in this stage
            description: Optional description for the stage
            
        Returns:
            Task ID for this stage
        """
        self.current_stage = stage
        self.stage_start_times[stage] = time.time()
        
        stage_description = f"[bold cyan]{stage.value}[/]"
        if description:
            stage_description += f": {description}"
            
        task_id = self.progress.add_task(stage_description, total=total_items)
        self.stage_tasks[stage] = task_id
        
        return task_id
        
    def update_stage(self, stage: ProgressStage, advance: int = 1, description: str = "") -> None:
        """Update progress for a specific stage."""
        if stage in self.stage_tasks:
            task_id = self.stage_tasks[stage]
            if description:
                self.progress.update(task_id, description=f"[bold cyan]{stage.value}[/]: {description}")
            self.progress.advance(task_id, advance)
            
    def complete_stage(self, stage: ProgressStage) -> None:
        """Mark a stage as complete and advance overall progress."""
        if stage in self.stage_tasks:
            task_id = self.stage_tasks[stage]
            self.progress.update(task_id, completed=self.progress.tasks[task_id].total)
            
        if self.overall_task is not None:
            self.progress.advance(self.overall_task, 1)
            
    def add_substage(self, parent_stage: ProgressStage, name: str, total_items: int) -> int:
        """Add a substage within a main stage."""
        description = f"  └─ {name}"
        return self.progress.add_task(description, total=total_items)
        
    def update_substage(self, task_id: int, advance: int = 1, description: str = "") -> None:
        """Update a substage progress."""
        if description:
            self.progress.update(task_id, description=f"  └─ {description}")
        self.progress.advance(task_id, advance)
        
    def complete_substage(self, task_id: int) -> None:
        """Complete a substage."""
        # Rich's tasks are stored in a list, indexed by task_id
        if 0 <= task_id < len(self.progress.tasks):
            task = self.progress.tasks[task_id]
            if task:
                self.progress.update(task_id, completed=task.total)
            
    def set_stage_status(self, stage: ProgressStage, status: str) -> None:
        """Set a status message for a stage."""
        if stage in self.stage_tasks:
            task_id = self.stage_tasks[stage]
            current_task = self.progress.tasks[task_id]
            description = f"[bold cyan]{stage.value}[/]: {status}"
            self.progress.update(task_id, description=description)
            
    def log_info(self, message: str) -> None:
        """Log an info message without interrupting progress."""
        self.console.print(f"[dim]ℹ {message}[/]")
        
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.console.print(f"[yellow]⚠ {message}[/]")
        
    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.console.print(f"[red]✗ {message}[/]")
        
    def log_success(self, message: str) -> None:
        """Log a success message."""
        self.console.print(f"[green]✓ {message}[/]")
        
    def finish(self) -> None:
        """Finish all progress tracking."""
        if self.is_active:
            # Complete any remaining tasks
            if self.overall_task is not None:
                self.progress.update(self.overall_task, completed=self.progress.tasks[self.overall_task].total)
            
            self.progress.stop()
            self.is_active = False
            
    @contextmanager
    def stage_context(self, stage: ProgressStage, total_items: int, description: str = ""):
        """Context manager for stage progress tracking."""
        task_id = self.start_stage(stage, total_items, description)
        try:
            yield task_id
        finally:
            self.complete_stage(stage)
            
    @contextmanager
    def substage_context(self, parent_stage: ProgressStage, name: str, total_items: int):
        """Context manager for substage progress tracking."""
        task_id = self.add_substage(parent_stage, name, total_items)
        try:
            yield task_id
        finally:
            self.complete_substage(task_id)
            
    def get_stage_progress(self, stage: ProgressStage) -> Optional[float]:
        """Get progress percentage for a stage (0.0 to 1.0)."""
        if stage in self.stage_tasks:
            task_id = self.stage_tasks[stage]
            # Rich's tasks are stored in a list, indexed by task_id
            if 0 <= task_id < len(self.progress.tasks):
                task = self.progress.tasks[task_id]
                if task and task.total:
                    return task.completed / task.total
        return None
        
    def get_elapsed_time(self, stage: ProgressStage) -> Optional[float]:
        """Get elapsed time for a stage in seconds."""
        if stage in self.stage_start_times:
            return time.time() - self.stage_start_times[stage]
        return None


# Global instance for use across the pipeline
_global_progress_manager: Optional[UnifiedProgressManager] = None


def get_progress_manager() -> UnifiedProgressManager:
    """Get the global progress manager instance."""
    global _global_progress_manager
    if _global_progress_manager is None:
        _global_progress_manager = UnifiedProgressManager()
    return _global_progress_manager


def set_progress_manager(manager: UnifiedProgressManager) -> None:
    """Set a custom progress manager instance."""
    global _global_progress_manager
    _global_progress_manager = manager


def reset_progress_manager() -> None:
    """Reset the global progress manager."""
    global _global_progress_manager
    if _global_progress_manager and _global_progress_manager.is_active:
        _global_progress_manager.finish()
    _global_progress_manager = None