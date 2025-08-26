#!/bin/bash
# Simple script to switch between local and commercial models

if [ "$1" = "commercial" ]; then
    echo "Switching to commercial model (OpenAI)..."
    export USE_COMMERCIAL_MODEL=true
    
    # Check if API key is set
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "⚠️  Warning: OPENAI_API_KEY not set!"
        echo "Set it with: export OPENAI_API_KEY='your-key-here'"
    else
        echo "✓ OpenAI API key found"
    fi
    
elif [ "$1" = "local" ]; then
    echo "Switching to local model (Ollama)..."
    unset USE_COMMERCIAL_MODEL
    
else
    echo "Usage: source switch_model.sh [commercial|local]"
    echo ""
    echo "Current mode:"
    if [ "$USE_COMMERCIAL_MODEL" = "true" ]; then
        echo "  Commercial (OpenAI)"
    else
        echo "  Local (Ollama)"
    fi
fi