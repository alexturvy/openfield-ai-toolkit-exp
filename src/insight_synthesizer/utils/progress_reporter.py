"""Progress reporting system for transparent pipeline execution."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
from rich.panel import Panel
try:
    from rich.tree import Tree
    from rich.text import Text
except Exception:  # Fallback if specific rich submodules are unavailable
    class Text:  # Minimal stub supporting append and str rendering
        def __init__(self):
            self._parts: List[str] = []
        def append(self, text: str, style: Optional[str] = None) -> None:
            self._parts.append(str(text))
        def __str__(self) -> str:
            return "".join(self._parts)

    class Tree:  # Minimal stub with add chaining
        def __init__(self, label: str):
            self.label = str(label)
            self.children: List[str] = []
        def add(self, text: str):
            self.children.append(str(text))
            return self
        def __str__(self) -> str:
            return self.label + "\n" + "\n".join(self.children)

console = Console()


class ProcessType(Enum):
    """Types of processing steps."""
    DOCUMENT_CLASSIFICATION = "Document classification"
    ADAPTIVE_CHUNKING = "Adaptive chunking"
    EMBEDDING_GENERATION = "Embedding generation"
    CLUSTERING_ANALYSIS = "Clustering analysis"
    INSIGHT_SYNTHESIS = "Insight synthesis"
    TENSION_ANALYSIS = "Tension analysis"
    VALIDATION = "Validation"


@dataclass
class ProcessStep:
    """Individual process step with details and rationale."""
    step_type: ProcessType
    details: Dict[str, Any]
    rationale: str
    confidence: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None


class ProgressReporter:
    """Manages progress reporting and transparency throughout the pipeline."""
    
    def __init__(self):
        self.steps: List[ProcessStep] = []
        self.current_step: Optional[ProcessStep] = None
    
    def start_process(self, step_type: ProcessType, details: Dict[str, Any], rationale: str, confidence: Optional[float] = None) -> None:
        """Start a new process step with details and rationale."""
        step = ProcessStep(
            step_type=step_type,
            details=details,
            rationale=rationale,
            confidence=confidence
        )
        self.steps.append(step)
        self.current_step = step
        self._display_process_start(step)
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update current step with metrics and results."""
        if self.current_step:
            self.current_step.metrics = metrics
            self._display_process_update(self.current_step)
    
    def complete_process(self, final_metrics: Optional[Dict[str, Any]] = None) -> None:
        """Complete the current process step."""
        if self.current_step and final_metrics:
            self.current_step.metrics = {**(self.current_step.metrics or {}), **final_metrics}
            self._display_process_complete(self.current_step)
        self.current_step = None
    
    def display_summary(self) -> None:
        """Display a summary of all processing steps."""
        if not self.steps:
            return
        
        console.print("\n[bold blue]═══ PIPELINE SUMMARY ═══[/]")
        
        tree = Tree("🔍 [bold]Analysis Pipeline[/]")
        
        for step in self.steps:
            step_node = tree.add(f"[cyan]{step.step_type.value}[/]")
            
            # Add details
            if step.details:
                details_node = step_node.add("📋 [dim]Details[/]")
                for key, value in step.details.items():
                    details_node.add(f"{key}: [white]{value}[/]")
            
            # Add rationale
            rationale_node = step_node.add("💭 [dim]Rationale[/]")
            rationale_node.add(f"[italic]{step.rationale}[/]")
            
            # Add metrics if available
            if step.metrics:
                metrics_node = step_node.add("📊 [dim]Results[/]")
                for key, value in step.metrics.items():
                    if isinstance(value, float):
                        metrics_node.add(f"{key}: [green]{value:.2f}[/]")
                    else:
                        metrics_node.add(f"{key}: [green]{value}[/]")
            
            # Add confidence if available
            if step.confidence is not None:
                confidence_color = "green" if step.confidence >= 0.8 else "yellow" if step.confidence >= 0.6 else "red"
                step_node.add(f"🎯 [dim]Confidence[/]: [{confidence_color}]{step.confidence:.2f}[/]")
        
        console.print(tree)
        console.print()
    
    def _display_process_start(self, step: ProcessStep) -> None:
        """Display the start of a process step."""
        title = f"PROCESS: {step.step_type.value}"
        
        content = Text()
        content.append("📋 Details:\n", style="bold")
        for key, value in step.details.items():
            content.append(f"  • {key}: ", style="dim")
            content.append(f"{value}\n", style="white")
        
        content.append("\n💭 Rationale:\n", style="bold")
        content.append(f"  {step.rationale}", style="italic")
        
        if step.confidence is not None:
            confidence_color = "green" if step.confidence >= 0.8 else "yellow" if step.confidence >= 0.6 else "red"
            content.append(f"\n\n🎯 Confidence: ", style="bold")
            content.append(f"{step.confidence:.2f}", style=confidence_color)
        
        panel = Panel(
            content,
            title=f"[bold blue]{title}[/]",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)
    
    def _display_process_update(self, step: ProcessStep) -> None:
        """Display an update for the current process step."""
        if not step.metrics:
            return
        
        content = Text()
        content.append("📊 Progress Update:\n", style="bold cyan")
        for key, value in step.metrics.items():
            content.append(f"  • {key}: ", style="dim")
            if isinstance(value, float):
                content.append(f"{value:.2f}\n", style="green")
            else:
                content.append(f"{value}\n", style="green")
        
        console.print(Panel(
            content,
            title="[cyan]UPDATE[/]",
            border_style="cyan",
            padding=(0, 2)
        ))
    
    def _display_process_complete(self, step: ProcessStep) -> None:
        """Display completion of a process step."""
        if not step.metrics:
            return
        
        content = Text()
        content.append("✅ Final Results:\n", style="bold green")
        for key, value in step.metrics.items():
            content.append(f"  • {key}: ", style="dim")
            if isinstance(value, float):
                content.append(f"{value:.2f}\n", style="bright_green")
            else:
                content.append(f"{value}\n", style="bright_green")
        
        console.print(Panel(
            content,
            title="[green]COMPLETE[/]",
            border_style="green",
            padding=(0, 2)
        ))
        console.print()  # Add spacing between process steps