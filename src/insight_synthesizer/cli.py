"""Command-line interface for Insight Synthesizer."""

import sys
from pathlib import Path
from typing import Set
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from .pipeline import InsightSynthesizer
from .config import ANALYSIS_LENSES
from .document_processing import find_supported_files
from .research.goal_manager import ResearchGoal
from .research.plan_parser import ResearchPlanParser, ParsedResearchPlan

console = Console()


def get_multiline_input(prompt: str, allow_empty: bool = False) -> str:
    """
    Get multi-line input from user. Stops on double-enter.
    Handles pasted content properly.
    
    Args:
        prompt: The prompt to display
        allow_empty: Whether to allow empty input
        
    Returns:
        The collected multi-line text
    """
    console.print(f"[bold]{prompt}[/]")
    console.print("[dim](Paste content or type. Press Enter twice to finish)[/]")
    
    lines = []
    consecutive_empty = 0
    
    while True:
        try:
            line = console.input()
            
            if not line:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    # Double enter detected - finish
                    break
                # Single empty line - keep it
                lines.append("")
            else:
                consecutive_empty = 0
                lines.append(line)
                
        except EOFError:
            # Handle Ctrl+D
            break
            
    result = "\n".join(lines).strip()
    
    if not result and not allow_empty:
        console.print("[yellow]Input cannot be empty. Please try again.[/]")
        return get_multiline_input(prompt, allow_empty)
        
    return result


def display_file_selection(files: list) -> None:
    """Display files for selection."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")
    
    for idx, file_path in enumerate(files, 1):
        size = file_path.stat().st_size
        table.add_row(str(idx), file_path.name, f"{size:,} bytes")
    
    console.print(table)


def parse_file_selection(selection: str, total_files: int) -> Set[int]:
    """Parse user file selection input."""
    if selection.lower() == "all":
        return set(range(1, total_files + 1))
    
    if "-" in selection:
        try:
            start, end = map(int, selection.split("-"))
            if 1 <= start <= end <= total_files:
                return set(range(start, end + 1))
        except ValueError:
            pass
    
    try:
        indices = {int(idx.strip()) for idx in selection.split(",")}
        if all(1 <= idx <= total_files for idx in indices):
            return indices
    except ValueError:
        pass
    
    raise ValueError("Invalid selection. Use numbers (1,3), ranges (1-3), or 'all'")


def edit_parsed_plan(parsed_plan: ParsedResearchPlan) -> ResearchGoal:
    """Allow user to edit a parsed research plan."""
    console.print("\n[bold cyan]Edit Research Plan[/]")
    console.print("Press Enter to keep existing value, or type new value\n")
    
    # Edit background
    if parsed_plan.background:
        console.print(f"[dim]Current background: {parsed_plan.background[:100]}...[/]")
    background = get_multiline_input("Background (or press Enter twice to keep)", allow_empty=True)
    if not background:
        background = parsed_plan.background
    
    # Edit research questions
    console.print("\n[bold]Research Questions[/]")
    if parsed_plan.research_questions:
        console.print("[dim]Current questions:[/]")
        for i, q in enumerate(parsed_plan.research_questions, 1):
            console.print(f"  {i}. {q}")
    
    keep_questions = Prompt.ask("\nKeep existing questions?", choices=["yes", "no"], default="yes")
    
    if keep_questions == "yes":
        questions = parsed_plan.research_questions
    else:
        console.print("Enter new questions (one per line, empty line to finish):")
        questions = []
        while True:
            q_num = len(questions) + 1
            q = console.input(f"[dim]Q{q_num}:[/] ").strip()
            if not q:
                if questions:
                    break
                console.print("[yellow]Please enter at least one research question[/]")
            else:
                questions.append(q)
    
    # Edit assumptions if present
    assumptions = parsed_plan.assumptions
    if assumptions:
        console.print(f"\n[dim]Current assumptions: {len(assumptions)} found[/]")
        edit_assumptions = Prompt.ask("Edit assumptions?", choices=["yes", "no"], default="no")
        
        if edit_assumptions == "yes":
            assumptions = []
            console.print("Enter assumptions (one per line, empty line to finish):")
            while True:
                a = console.input("[dim]Assumption:[/] ").strip()
                if not a:
                    break
                assumptions.append(a)
    
    return ResearchGoal(
        background=background,
        assumptions=assumptions,
        research_goal=parsed_plan.research_goal,
        research_questions=questions,
        methodology=parsed_plan.methodology,
        key_hypotheses=parsed_plan.hypotheses
    )


def collect_research_goals() -> ResearchGoal:
    """Interactively collect research goals from user."""
    console.print("\n[bold cyan]Research Context Setup[/]")
    console.print("Let's define your research context to focus the analysis.\n")
    
    # 1. Background
    background = get_multiline_input(
        "1. Background (context for this research)",
        allow_empty=True
    )
    
    # 2. Assumptions
    console.print("\n[bold]2. Assumptions[/] (one per line, empty line to finish):")
    assumptions = []
    while True:
        a_num = len(assumptions) + 1
        a = console.input(f"[dim]Assumption {a_num}:[/] ").strip()
        if not a:
            break
        assumptions.append(a)
    
    # 3. Research Goal  
    console.print("")  # Add spacing
    research_goal = get_multiline_input(
        "3. Research Goal (overall objective)",
        allow_empty=True
    )
    
    # 4. Research Questions
    console.print("\n[bold]4. Research Questions[/] (one per line, empty line to finish):")
    questions = []
    while True:
        q_num = len(questions) + 1
        q = console.input(f"[dim]Q{q_num}:[/] ").strip()
        if not q:
            if questions:
                break
            console.print("[yellow]Please enter at least one research question[/]")
        else:
            questions.append(q)
    
    # Optional: Ask if they want to add traditional fields
    add_more = Prompt.ask(
        "\nAdd methodology or hypotheses?",
        choices=["yes", "no"],
        default="no"
    )
    
    methodology = None
    hypotheses = None
    
    if add_more == "yes":
        # Optional: methodology
        console.print("")  # Add spacing
        methodology = get_multiline_input(
            "Methodology (optional)",
            allow_empty=True
        )
        
        # Optional: key hypotheses
        console.print("\n[bold]Hypotheses[/] (optional, one per line, empty to finish):")
        hypotheses = []
        while True:
            h = console.input("[dim]H:[/] ").strip()
            if not h:
                break
            hypotheses.append(h)
    
    return ResearchGoal(
        background=background if background else None,
        assumptions=assumptions if assumptions else None,
        research_goal=research_goal if research_goal else None,
        research_questions=questions,
        methodology=methodology if methodology else None,
        key_hypotheses=hypotheses if hypotheses else None
    )


def main() -> None:
    """Main CLI entry point."""
    console.print(Panel.fit(
        "[bold blue]Insight Synthesizer[/]\nAI-powered research assistant for qualitative data analysis",
        title="Welcome"
    ))
    
    # Show available lenses
    console.print("\n[bold]Available Analysis Lenses:[/]")
    lens_table = Table(show_header=True, header_style="bold blue")
    lens_table.add_column("Lens", style="cyan")
    lens_table.add_column("Description")
    
    for name, config in ANALYSIS_LENSES.items():
        lens_table.add_row(name, config['description'])
    console.print(lens_table)
    
    # Get lens selection
    while True:
        lens = Prompt.ask("\nSelect analysis lens", default="pain_points")
        if lens in ANALYSIS_LENSES:
            break
        console.print(f"[red]Invalid lens. Choose from: {', '.join(ANALYSIS_LENSES.keys())}[/]")
    
    # Get input directory
    while True:
        input_path = Prompt.ask("\nEnter path to research data folder")
        directory = Path(input_path)
        if directory.exists() and directory.is_dir():
            break
        console.print("[red]Directory not found. Please try again.[/]")
    
    # Find supported files and let user select which ones to analyze
    try:
        files = find_supported_files(directory)
        if not files:
            console.print("[red]No supported files found in the directory.[/]")
            sys.exit(1)
        
        console.print(f"\n[bold]Found {len(files)} supported files:[/]")
        display_file_selection(files)
        
        # Get file selection from user
        while True:
            selection = Prompt.ask(
                "\nSelect files to analyze",
                default="all",
                show_default=True
            ).strip()
            
            try:
                selected_indices = parse_file_selection(selection, len(files))
                selected_files = [files[i-1] for i in selected_indices]
                console.print(f"[green]Selected {len(selected_files)} files for analysis[/]")
                break
            except ValueError as e:
                console.print(f"[red]{e}[/]")
        
        # Ask about research plan document first
        research_goals = None
        use_research_plan = Prompt.ask(
            "\nDo you have a research plan document to import?",
            choices=["yes", "no"],
            default="yes"  # Changed default to yes
        )
        
        if use_research_plan == "yes":
            # Import research plan
            while True:
                plan_path = Prompt.ask("Path to research plan document")
                plan_file = Path(plan_path)
                
                if plan_file.exists() and plan_file.is_file():
                    try:
                        # Parse the research plan
                        parser = ResearchPlanParser()
                        parsed_plan = parser.parse_document(plan_file)
                        
                        # Display for confirmation
                        parser.display_parsed_plan(parsed_plan)
                        
                        # Ask for confirmation
                        confirm = Prompt.ask(
                            "\nUse this parsed research plan?",
                            choices=["yes", "edit", "retry"],
                            default="yes"
                        )
                        
                        if confirm == "yes":
                            # Convert to ResearchGoal
                            research_goals = ResearchGoal(
                                background=parsed_plan.background,
                                assumptions=parsed_plan.assumptions,
                                research_goal=parsed_plan.research_goal,
                                research_questions=parsed_plan.research_questions,
                                methodology=parsed_plan.methodology,
                                key_hypotheses=parsed_plan.hypotheses
                            )
                            console.print("[green]Research plan imported successfully![/]")
                            break
                        elif confirm == "edit":
                            # Allow manual editing of parsed content
                            research_goals = edit_parsed_plan(parsed_plan)
                            console.print("[green]Research plan edited and imported successfully![/]")
                            break
                        # else retry with different file
                        
                    except Exception as e:
                        console.print(f"[red]Error parsing research plan: {e}[/]")
                        retry = Prompt.ask("Try another file?", choices=["yes", "no"])
                        if retry == "no":
                            break
                else:
                    console.print("[red]File not found. Please try again.[/]")
        
        if use_research_plan == "no" or research_goals is None:
            # Fall back to manual entry
            manual_goals = Prompt.ask(
                "\nEnter research goals manually?",
                choices=["yes", "no"],
                default="no"
            )
            if manual_goals == "yes":
                research_goals = collect_research_goals()
                console.print("\n[green]Research goals collected successfully![/]")
        
        # Run analysis with selected files
        synthesizer = InsightSynthesizer()
        report_path = synthesizer.analyze_files(selected_files, lens, research_goals)
        console.print(f"\n[bold green]Success![/] Report generated: {report_path}")
        
    except Exception as e:
        console.print(f"[bold red]Analysis failed:[/] {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted. Exiting...[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/] {e}")
        sys.exit(1)