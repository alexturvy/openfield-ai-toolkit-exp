Product Requirements Document: Insight Synthesizer v1.0
Document Owner: Alex Turvy

Status: Draft

Last Updated: June 10, 2025

1. The Opportunity: Unlocking Our Strategic Edge
At Openfield, one of our core strengths is our ability to translate deep user understanding into actionable product strategy. This process sometimes begins with qualitative research—interviews, focus groups, and usability sessions—that generates a wealth of raw data.

Currently, the initial processing of this data can be a manual, time-intensive task. Researchers need to spend meticulously reading, organizing, and coding transcripts line-by-line to produce a "first draft" of thematic insights. While essential, this foundational work creates a bottleneck, delaying the transition to the high-value strategic analysis where Openfield truly excels.

We have an opportunity to accelerate this foundational step, empowering our team to move faster from raw data to robust, evidence-based strategy, further solidifying our competitive advantage.

2. Our Vision: An AI-Powered Research Assistant
We will build the Insight Synthesizer: an internal, secure, AI-powered tool that acts as a skilled research assistant.

By pointing the tool at a collection of raw research notes, our team will receive a structured, synthesized report in minutes, not days. This report will surface key themes, highlight tensions in user feedback, and trace every single insight directly back to the source data.

The goal is not to replace the researcher, but to augment their capabilities—automating the laborious task of initial coding to free up our experts to focus on what matters most: interpreting findings, building compelling narratives, and guiding clients toward decisive action.

3. Core Audience
The primary user of the Insight Synthesizer is a UX Researcher at Openfield. This individual is a deeply analytical thinker who values rigor, conceptual precision, and evidence-based arguments. They are adept at navigating complex information and are comfortable with technology, but demand transparency and control over their analytical process.

4. Features & Functionality (MVP v1.0)
The initial version of the Insight Synthesizer will be a command-line tool that is powerful, secure, and flexible.

4.1. Input & Output
Input: The tool will accept a folder of plain text (.txt) files (e.g., interview transcripts, user notes).

Output: The tool will generate a single, beautifully formatted Markdown (.md) file. This "synthesis report" is designed to be easily shared, or copied into presentations and client deliverables.

4.2. Our Hybrid Analysis Engine: A Defensible, Triangulated Approach

To ensure our analysis is rigorous, transparent, and insightful, the tool uses a unique, multi-stage process that combines the strengths of modern computational linguistics with the explainability of statistical analysis. This hybrid approach is explicitly designed to overcome the weaknesses of using a single methodology in isolation.

| Methodology | Strength | Weakness | Our Solution |
| :--- | :--- | :--- | :--- |
| **Traditional Statistics** (e.g., keyword counting) | Repeatable & Explainable | Lacks semantic nuance; misunderstands context. | We use statistical methods on top of semantic data, not raw text. |
| **Pure LLM Synthesis** | High Semantic Nuance | "Black box" process; difficult to source findings. | We use the LLM only for the final synthesis of pre-identified, tightly-scoped data clusters. |

Our pipeline synthesizes these approaches into five distinct stages:

**Stage 1: Adaptive Document Processing**
* **What:** The tool begins by intelligently processing documents based on their structure and content type. Using a `StructureClassifier`, it identifies document patterns and applies appropriate chunking strategies.
* **Rationale:** This adaptive approach ensures we maintain semantic coherence while processing different types of research data. The `AdaptiveChunker` creates meaningful chunks that preserve context and relationships within the text.

**Stage 2: Semantic Embedding (Capturing Meaning)**
* **What:** The tool converts all text chunks into high-dimensional numerical vectors, or "embeddings," using a state-of-the-art Sentence-Transformer model.
* **Rationale:** This is the foundation of modern natural language understanding. Unlike simple keyword matching, embeddings capture the semantic *meaning* of the text. Phrases like "the app kept crashing" and "the software was unstable" are understood as being conceptually similar.

**Stage 3: Statistical Clustering (Finding Structure)**
* **What:** We apply proven unsupervised machine learning algorithms (UMAP for dimensionality reduction and HDBSCAN for density-based clustering) to the embeddings.
* **Rationale:** This stage mathematically identifies dense groups of semantically similar user quotes without any human or AI bias. It provides a defensible, empirical "scaffolding" of what themes exist in the data, based purely on their content.

**Stage 4: LLM-Powered Synthesis (Generating Insight)**
* **What:** The tool iterates through each statistically-verified cluster and uses a large language model (LLM) for a highly-focused task: to act as a qualitative coder. For each small, coherent group of quotes, the LLM's job is to generate a theme name, write a concise summary, and extract the most representative verbatim quotes as evidence.
* **Rationale:** This is "structured qualitative coding at scale." By constraining the LLM to synthesize small, pre-identified clusters, we eliminate the risk of hallucination and ensure every insight is directly and verifiably **source-anchored**.

**Stage 5: Quality Validation & Report Generation**
* **What:** The final stage validates the quality of our analysis using configurable thresholds and generates a structured report.
* **Rationale:** This ensures our output meets quality standards and provides actionable insights in a clear, consistent format.

4.3. Configurable Analysis "Lenses"

A researcher's focus changes based on the project's goals. The Insight Synthesizer allows users to direct the analysis through different "lenses" to surface the most relevant insights. Each lens is configured with:

* A clear description of its purpose
* A focused prompt for the LLM
* A specific extra field for additional insight
* A consistent output structure

The MVP includes these lenses:

| Lens Name | Purpose | Extra Field |
| :--- | :--- | :--- |
| pain_points | Identify user frustrations and challenges | Severity (low/medium/high) |
| opportunities | Find potential improvements and enhancements | Potential Impact (low/medium/high) |
| jobs_to_be_done | Understand core user motivations and goals | User Context (when/why needed) |
| mental_models | Uncover user assumptions and beliefs | Accuracy (accurate/partially/inaccurate) |
| decision_factors | Identify key adoption/abandonment factors | Influence Level (low/medium/high) |
| feature_focus | Analyze feedback about specific features | User Sentiment (positive/neutral/negative) |

Each lens maintains a consistent structure while focusing on different aspects of the data, ensuring both flexibility and reliability in our analysis.

4.4. Source-Anchored Evidence
Every insight in the final report will be non-negotiably tied to its source. Each theme and summary will be immediately followed by the verbatim user quotes that support it, ensuring complete traceability and building trust in the output.

4.5. Highlighting Tensions & Contradictions
To provide a truly holistic view, the report will include a dedicated "Tensions & Contradictions" section. This feature surfaces areas where user feedback is polarized or contradictory, framing insights as complex decision frameworks rather than simple "truths."

5. End-User Experience & Deployment

To ensure broad adoption and ease of use for the Openfield team, the Insight Synthesizer will be delivered as a standalone, double-clickable application.

The end-user will not be required to perform any command-line setup, install dependencies, or manage a Python environment. The development process will use standard tools like virtual environments for reliability, but the final product will be a self-contained executable, providing a seamless "one-click" user experience.

6. What's Not in Scope for This Version
To ensure a focused and rapid initial launch, the following will not be included in the MVP:

A graphical user interface (GUI). The tool will be operated via the command line.

Support for other file types like audio, PDF, or images.

Real-time or continuous analysis.

7. Measuring Success
We will measure the success of the Insight Synthesizer based on its ability to:

Accelerate Workflow: Reduce the time to produce a "first draft" synthesis from a standard research project by at least 50%.

Enhance Quality: Achieve a high satisfaction score (>8/10) from our research team on the usefulness, clarity, and reliability of the generated reports.

Drive Adoption: Be actively used by the research team for their next client project.

8. Future Vision
If this MVP proves successful, we envision expanding the toolkit's capabilities to include direct audio transcription, support for PDF reports, and integration into a shared, searchable "Memory Vault" that houses all of Openfield's institutional knowledge. This project is the first step toward building a durable, proprietary advantage in how we deliver strategic work.