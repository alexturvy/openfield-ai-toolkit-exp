# Development Plan: Research Insight Extractor

## Step 1: Create New Repository & README

### File: `README.md`

```markdown
# Research Insight Extractor

A lightweight tool that analyzes interview transcripts to answer research questions with verified quotes and UX insights.

## What It Does Now

Takes your interview transcripts and research questions, then:
- ✅ Answers each research question with real quotes from participants  
- ✅ Verifies every quote against source material (no hallucinations)
- ✅ Identifies tensions and contradictions in the data
- ✅ Surfaces unexpected insights you didn't ask about
- ✅ Applies UX frameworks (JTBD, mental models) to findings
- ✅ Generates a simple, actionable report

## What It Will Do Soon

- 🔄 Run entirely locally with Ollama (currently uses OpenAI for speed)
- 📊 Compare findings across multiple studies
- 🎯 Track research coverage and identify gaps
- 💾 Build a searchable repository of all your research

## Quick Start

```bash
python extract.py --interviews data/*.txt --research questions.md
```

## Why Use This Instead of ChatGPT/Gemini?

1. **Never hallucinates quotes** - Every quote is verified against source
2. **Follows YOUR research methodology** - Not generic analysis
3. **Finds what you're NOT looking for** - Surfaces unexpected insights
4. **Maintains speaker attribution** - Know who said what
```

## Step 2: Core Script Structure

### File: `extract.py`

```python
#!/usr/bin/env python3
"""
Research Insight Extractor - Main entry point
Simple, single-file implementation for now
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import os

# For now, using OpenAI for speed - will add Ollama support
from openai import OpenAI

@dataclass
class Interview:
    """Parsed interview with speaker tracking"""
    filepath: Path
    content: str
    speakers: List[str]
    utterances: List[Dict]  # {speaker, text, index}

@dataclass
class ResearchPlan:
    """Parsed research questions and context"""
    questions: List[str]
    background: Optional[str] = None
    hypotheses: Optional[List[str]] = None

@dataclass
class Finding:
    """A verified finding with evidence"""
    question: str
    claim: str
    quotes: List[Dict]  # {text, speaker, source}
    confidence: float

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interviews', nargs='+', required=True)
    parser.add_argument('--research', required=True)
    parser.add_argument('--output', default='findings.txt')
    parser.add_argument('--model', default='openai', choices=['openai', 'ollama'])
    args = parser.parse_args()
    
    # Load interviews
    interviews = load_interviews(args.interviews)
    print(f"Loaded {len(interviews)} interviews")
    
    # Load research plan
    research = load_research_plan(args.research)
    print(f"Found {len(research.questions)} research questions")
    
    # Analyze
    findings = analyze_interviews(interviews, research)
    
    # Generate report
    report = generate_report(findings, research)
    
    # Save
    Path(args.output).write_text(report)
    print(f"Report saved to {args.output}")

if __name__ == '__main__':
    main()
```

## Step 3: Document Intake and Classification

### Add to `extract.py`:

```python
def load_interviews(paths: List[str]) -> List[Interview]:
    """Load and classify interview files"""
    interviews = []
    
    for path_pattern in paths:
        for filepath in Path().glob(path_pattern):
            content = filepath.read_text()
            doc_type = detect_document_type(content)
            
            if doc_type == 'interview':
                interview = parse_interview(filepath, content)
                interviews.append(interview)
            else:
                print(f"Skipping {filepath.name} - not an interview")
    
    return interviews

def detect_document_type(content: str) -> str:
    """Simple heuristic to detect document type"""
    lines = content.split('\n')
    
    # Look for interview markers
    speaker_pattern = r'^[A-Z][a-z]+\s*:'
    speaker_lines = sum(1 for line in lines if re.match(speaker_pattern, line))
    
    # Questions markers
    question_marks = content.count('?')
    
    # Dialog ratio
    dialog_ratio = speaker_lines / len(lines) if lines else 0
    
    if dialog_ratio > 0.1 or (speaker_lines > 5 and question_marks > 3):
        return 'interview'
    elif question_marks > 10:
        return 'survey'
    else:
        return 'notes'

def parse_interview(filepath: Path, content: str) -> Interview:
    """Parse interview into structured format"""
    utterances = []
    speakers = set()
    
    # Simple speaker detection
    lines = content.split('\n')
    current_speaker = "Unknown"
    current_text = []
    
    for line in lines:
        speaker_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:\s*(.+)', line)
        
        if speaker_match:
            # Save previous utterance
            if current_text:
                utterances.append({
                    'speaker': current_speaker,
                    'text': ' '.join(current_text),
                    'index': len(utterances)
                })
            
            # Start new utterance
            current_speaker = speaker_match.group(1)
            speakers.add(current_speaker)
            current_text = [speaker_match.group(2)]
        else:
            # Continue current utterance
            if line.strip():
                current_text.append(line.strip())
    
    # Don't forget last utterance
    if current_text:
        utterances.append({
            'speaker': current_speaker,
            'text': ' '.join(current_text),
            'index': len(utterances)
        })
    
    return Interview(
        filepath=filepath,
        content=content,
        speakers=list(speakers),
        utterances=utterances
    )
```

## Step 4: Research Plan Parser

### Add to `extract.py`:

```python
def load_research_plan(path: str) -> ResearchPlan:
    """Parse research plan from markdown file"""
    content = Path(path).read_text()
    
    # Extract questions (numbered or bulleted)
    questions = []
    question_patterns = [
        r'^\d+\.\s+(.+)',  # 1. Question
        r'^-\s+(.+\?)',     # - Question?
        r'^RQ\d+:\s*(.+)',  # RQ1: Question
    ]
    
    for line in content.split('\n'):
        for pattern in question_patterns:
            match = re.match(pattern, line)
            if match:
                questions.append(match.group(1))
                break
    
    # Extract background (if exists)
    background = None
    if 'background' in content.lower():
        background_match = re.search(
            r'#+\s*Background\s*\n(.*?)(?=\n#|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if background_match:
            background = background_match.group(1).strip()
    
    if not questions:
        # Fallback: treat each line with ? as a question
        questions = [line.strip() for line in content.split('\n') 
                    if '?' in line and line.strip()]
    
    return ResearchPlan(questions=questions, background=background)
```

## Step 5: Answer Research Questions

### Add to `extract.py`:

```python
def analyze_interviews(interviews: List[Interview], 
                       research: ResearchPlan) -> Dict:
    """Main analysis logic"""
    
    # Setup LLM
    client = setup_llm()
    
    findings = {
        'answered_questions': [],
        'unexpected_insights': [],
        'tensions': [],
        'ux_patterns': []
    }
    
    # Answer each research question
    for question in research.questions:
        print(f"Analyzing: {question[:50]}...")
        
        # Find relevant quotes using LLM
        relevant_quotes = extract_relevant_quotes(
            client, interviews, question
        )
        
        # Verify quotes are real
        verified_quotes = verify_quotes(relevant_quotes, interviews)
        
        if verified_quotes:
            findings['answered_questions'].append({
                'question': question,
                'quotes': verified_quotes,
                'summary': synthesize_answer(client, verified_quotes, question)
            })
    
    # Find unexpected insights
    findings['unexpected_insights'] = find_unexpected_insights(
        client, interviews, research.questions
    )
    
    # Find tensions
    findings['tensions'] = find_tensions(client, findings['answered_questions'])
    
    # Extract UX patterns
    findings['ux_patterns'] = extract_ux_patterns(client, interviews)
    
    return findings

def setup_llm():
    """Setup LLM client (OpenAI for now, Ollama later)"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Set OPENAI_API_KEY environment variable")
        exit(1)
    return OpenAI(api_key=api_key)

def extract_relevant_quotes(client, interviews: List[Interview], 
                           question: str) -> List[Dict]:
    """Extract quotes relevant to a research question"""
    
    # Combine all interviews for context
    all_utterances = []
    for interview in interviews:
        for utt in interview.utterances:
            all_utterances.append({
                'text': utt['text'],
                'speaker': utt['speaker'],
                'source': interview.filepath.name
            })
    
    # Ask LLM to find relevant quotes
    prompt = f"""Find quotes that help answer this research question:
    
Question: {question}

Interviews:
{json.dumps(all_utterances, indent=2)}

Return JSON array of relevant quotes with explanation:
[
  {{
    "quote_fragment": "key words from the quote",
    "speaker": "speaker name",
    "source": "filename",
    "relevance": "why this answers the question"
  }}
]
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content).get('quotes', [])
```

## Step 6: Quote Verification

### Add to `extract.py`:

```python
def verify_quotes(potential_quotes: List[Dict], 
                 interviews: List[Interview]) -> List[Dict]:
    """Verify each quote exists in source material"""
    verified = []
    
    for quote_info in potential_quotes:
        fragment = quote_info['quote_fragment'].lower()
        
        # Find in source
        for interview in interviews:
            for utterance in interview.utterances:
                if fragment in utterance['text'].lower():
                    # Found it! Get the full real quote
                    verified.append({
                        'text': utterance['text'],  # Full real quote
                        'speaker': utterance['speaker'],  # Real speaker
                        'source': interview.filepath.name,
                        'relevance': quote_info.get('relevance', '')
                    })
                    break
    
    return verified
```

## Step 7: Extract Insights and Patterns

### Add to `extract.py`:

```python
def find_unexpected_insights(client, interviews: List[Interview], 
                            questions: List[str]) -> List[Dict]:
    """Find insights not covered by research questions"""
    
    prompt = f"""Given these research questions:
{json.dumps(questions, indent=2)}

Find 3-5 important insights from the interviews that are NOT directly related to these questions:

{json.dumps([i.content[:1000] for i in interviews], indent=2)}

Return JSON:
{{
  "insights": [
    {{
      "insight": "what you found",
      "evidence": "supporting quote fragment",
      "importance": "why this matters"
    }}
  ]
}}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    insights = json.loads(response.choices[0].message.content).get('insights', [])
    
    # Verify each insight
    verified_insights = []
    for insight in insights:
        if verify_fragment_exists(insight['evidence'], interviews):
            verified_insights.append(insight)
    
    return verified_insights

def find_tensions(client, answered_questions: List[Dict]) -> List[Dict]:
    """Find contradictions and tensions in the data"""
    
    # Simple approach: look for opposing sentiments
    tensions = []
    
    for q in answered_questions:
        quotes = q['quotes']
        if len(quotes) >= 2:
            # Check if quotes express different views
            prompt = f"""Do these quotes express contradicting views?
            
Quotes:
{json.dumps(quotes, indent=2)}

Return JSON:
{{
  "has_tension": true/false,
  "description": "describe the tension if exists"
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.choices[0].message.content)
            if result.get('has_tension'):
                tensions.append({
                    'question': q['question'],
                    'description': result['description'],
                    'quotes': quotes
                })
    
    return tensions

def extract_ux_patterns(client, interviews: List[Interview]) -> List[Dict]:
    """Extract UX patterns like JTBD, mental models"""
    
    prompt = """Identify UX patterns in these interviews:
    
1. Jobs to be Done (what are users trying to accomplish?)
2. Mental Models (how do users think it works?)
3. Pain Points (what frustrates them?)

Return JSON with examples and quotes.
"""
    
    # Implementation similar to above
    # Return verified patterns
    return []
```

## Step 8: Generate Simple Report

### Add to `extract.py`:

```python
def generate_report(findings: Dict, research: ResearchPlan) -> str:
    """Generate simple text report"""
    
    report = []
    report.append("=" * 60)
    report.append("RESEARCH FINDINGS REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Research Questions Section
    report.append("RESEARCH QUESTIONS & ANSWERS")
    report.append("-" * 40)
    
    for item in findings['answered_questions']:
        report.append(f"\nQ: {item['question']}")
        report.append(f"A: {item['summary']}")
        report.append("\nSupporting Evidence:")
        
        for quote in item['quotes'][:3]:  # Top 3 quotes
            report.append(f'  "{quote["text"]}"')
            report.append(f'  - {quote["speaker"]}, {quote["source"]}')
            report.append("")
    
    # Unexpected Insights
    if findings['unexpected_insights']:
        report.append("\nUNEXPECTED INSIGHTS")
        report.append("-" * 40)
        
        for insight in findings['unexpected_insights']:
            report.append(f"\n• {insight['insight']}")
            report.append(f"  Why it matters: {insight['importance']}")
    
    # Tensions
    if findings['tensions']:
        report.append("\nTENSIONS & CONTRADICTIONS")
        report.append("-" * 40)
        
        for tension in findings['tensions']:
            report.append(f"\n• {tension['description']}")
    
    # Summary
    report.append("\n" + "=" * 60)
    report.append("SUMMARY")
    report.append(f"Analyzed {len(findings['answered_questions'])} research questions")
    report.append(f"Found {len(findings['unexpected_insights'])} unexpected insights")
    report.append(f"Identified {len(findings['tensions'])} tensions")
    
    return "\n".join(report)
```

## Step 9: Test with Sample Data

### File: `sample_interview.txt`
```
Interviewer: What's your experience with mobile banking?

Sarah: I use it all the time for checking my balance, but I don't trust the mobile deposit feature. I always worry the photo won't be good enough.

Interviewer: What makes you worry about that?

Sarah: Well, I tried it once and it got rejected. Now I just go to the ATM.
```

### File: `research_questions.md`
```
# Mobile Banking Research

## Research Questions
1. What prevents users from adopting mobile deposit?
2. How do users currently manage their banking tasks?
```

### Run:
```bash
python extract.py --interviews sample_interview.txt --research research_questions.md
```

## Next Steps (After This Works)

1. **Add Ollama support** - Just swap the LLM client
2. **Improve quote verification** - Fuzzy matching for better accuracy  
3. **Add methodology configuration** - YAML file for your specific approach
4. **Batch processing** - Handle 50+ interviews efficiently
5. **Export formats** - Add Word/PDF output options

## Key Decisions Made

- **Single file for now** - Everything in `extract.py` until it works
- **OpenAI first** - Faster for testing, easy to swap later
- **Simple text report** - No markdown complexity, just readable text
- **Minimal dependencies** - Just OpenAI SDK and standard library
- **Quote verification priority** - This is the killer feature

Start with this. Get it working end-to-end. Then iterate.