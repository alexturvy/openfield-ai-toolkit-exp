# openfield-ai-toolkit
Internal AI tools for the Openfield team

This project will contain three initial tools: an Insight Synthesizer, a Local Memory Vault, and a Heuristic Evaluator.

## Overview
The Openfield AI Toolkit is designed to enhance the team's ability to focus on high-value work by providing lightweight, local-first tools that streamline various aspects of the design and research process. The toolkit aims to leverage AI capabilities while maintaining privacy, security, and control over client intellectual property.

## Tools

### 1. Insight Synthesizer ✅ **MVP Complete**
- **Problem**: Researchers spend significant time manually organizing raw interviews, session notes, and workshops into thematic outlines.
- **Solution**: A local tool that ingests raw notes and produces draft thematic outlines with source-verified quotes, providing researchers with a reliable starting point for deeper analysis.
- **How**: Seven-stage pipeline processes documents through adaptive chunking, semantic embeddings, statistical clustering, quote-free LLM synthesis, tension analysis, and source validation.
- **Status**: Fully functional MVP with all critical features implemented and tested.

#### Quick Start
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or .venv\Scripts\activate  # Windows

# Run the synthesizer
python3 synthesizer.py

# When prompted:
# 1. Choose analysis lens (e.g., pain_points, opportunities)
# 2. Enter directory path or use default (sample_notes)
# 3. Select files to analyze (all, specific numbers, or ranges)
```

#### Key Features Implemented
- 📁 **Multi-format Support**: TXT, RTF, DOCX, PDF
- 🎯 **Smart File Selection**: Choose all files or select specific ones
- 🗣️ **Speaker Attribution**: Tracks who said what throughout analysis
- 📊 **Progress Indicators**: Real-time status for long operations
- ✅ **Theme Validation**: Verifies insights with source quotes
- ⚡ **Tension Detection**: Identifies contradictions in feedback
- 📈 **Comprehensive Reports**: Markdown output with statistics

#### How the Pipeline Works

The Insight Synthesizer uses a **seven-stage analysis pipeline** designed for reliability and transparency:

**Stage 1: Document Processing & Chunking**
- Automatically detects document structure (interviews, notes, reports)
- Uses adaptive chunking strategies to preserve semantic context
- Supports TXT, RTF, DOCX, and PDF formats

**Stage 2: Semantic Embedding Generation** 
- Converts text chunks into vector representations using sentence transformers
- Enables mathematical comparison of semantic similarity

**Stage 3: Statistical Clustering**
- Groups semantically similar content using UMAP dimensionality reduction + HDBSCAN clustering
- Identifies natural themes without researcher bias

**Stage 4: Quote-Free LLM Synthesis**
- Synthesizes insights and patterns from each cluster using local LLM (Mistral via Ollama)
- Focuses purely on thematic understanding without generating quotes
- Applies chosen analysis lens (pain_points, opportunities, mental_models, etc.)

**Stage 5: Tension Analysis**
- Detects opposing sentiments or contradictions between themes
- Summarizes the most relevant tensions to inform design trade-offs

**Stage 6: Source Validation & Quote Verification**
- Independently finds supporting quotes from original source material
- Validates each theme against original transcripts for accuracy
- Provides confidence scores and source attribution

**Stage 7: Report Generation**
- Produces comprehensive Markdown report with all findings
- Includes speaker statistics, theme distribution, and validation metrics
- Formats output for easy sharing and further analysis

#### Output Format

The synthesizer generates a comprehensive **Markdown report** containing:

- **Theme summaries** with key insights organized by analysis lens
- **Source-verified quotes** with confidence scores and speaker attribution  
- **Validation metrics** showing theme coverage and quality scores
- **Transparency data** including file sources and speaker distribution
- **Tensions & Contradictions** section outlining conflicting user feedback

This approach ensures **quote accuracy** while maintaining **analytical depth** - themes are based on statistical patterns, but all supporting evidence is traced directly to source material.

### 2. PRD Generator 🚧 **Planned**
- **Problem**: Creating comprehensive Product Requirements Documents (PRDs) requires synthesizing diverse inputs from surveys, interviews, research findings, and stakeholder feedback into a coherent structured format.
- **Solution**: A local tool that takes diverse inputs and assembles them into a structured PRD format, supporting the broader validation process for problem statements.
- **How**: Process various input types (survey results, interview transcripts, research insights) and generate a structured PRD document following best practices and customizable templates.
- **Status**: Not yet implemented. See [NEXT_STEPS.md](NEXT_STEPS.md) for roadmap.

### 3. Local Memory Vault 🚧 **Planned**
- **Problem**: Past research findings, client deliverables, and project notes are often difficult to retrieve and can be lost over time.
- **Solution**: A local, lightweight semantic search tool that indexes documents by meaning, enabling instant retrieval of relevant past work.
- **How**: Use a simple folder structure convention for each project. FAISS or SQLite vector index runs locally to embed documents for semantic retrieval. A local command surfaces prior insights linked to the phrase's underlying meaning.
- **Status**: Not yet implemented. See [NEXT_STEPS.md](NEXT_STEPS.md) for roadmap.

## Long-term Vision
The toolkit is designed to be modular and adaptable, allowing for future upgrades and extensions based on team needs. This includes deploying an internal model server, adding persona builders and journey-map composers, and layering smart disclosure workflows into deliverables.

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/alexturvy/openfield-ai-toolkit.git
cd openfield-ai-toolkit

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run tests to verify setup
python -m pytest tests/
```

## Development

For technical details about the architecture, code organization, and development guidelines, see:
- [DEVELOPMENT.md](DEVELOPMENT.md) - Architecture and implementation details
- [CLAUDE.md](CLAUDE.md) - Guidance for AI-assisted development
- [NEXT_STEPS.md](NEXT_STEPS.md) - Roadmap and future enhancements

## Key Principles
- **Start Small**: Begin with a simple, low-risk MVP to test the effectiveness of the tools.
- **Stay Adaptable**: Build a flexible system that can evolve with new models and techniques.
- **Protect What Matters**: Ensure client trust and intellectual property are safeguarded.
- **Build a Durable Advantage**: Create a toolkit that remains effective as the external AI ecosystem evolves.
