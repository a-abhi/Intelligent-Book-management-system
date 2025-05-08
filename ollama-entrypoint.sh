#!/bin/bash

# Install curl if not present
if ! command -v curl &> /dev/null; then
    echo "Installing curl..."
    apt-get update && apt-get install -y curl
fi

# Start Ollama server in the background
ollama serve &

# Wait for the server to be ready
echo "Waiting for Ollama server to start..."
sleep 10

# Function to pull model with retries
pull_model() {
    local max_retries=5
    local retry_count=0
    local success=false
    local model="llama3.2"

    while [ $retry_count -lt $max_retries ] && [ "$success" = false ]; do
        echo "Attempting to pull $model model (attempt $((retry_count + 1))/$max_retries)..."
        
        if ollama pull $model; then
            success=true
            echo "Successfully pulled $model model"
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                echo "Failed to pull model. Retrying in 30 seconds..."
                sleep 30
            else
                echo "Failed to pull model after $max_retries attempts"
                exit 1
            fi
        fi
    done
}

# Pull the model
pull_model

# Keep the container running
wait 