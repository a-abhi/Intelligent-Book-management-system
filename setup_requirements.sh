#!/bin/bash

# List of services
services=("book_service" "review_service" "llama3_service" "recommendation_service" "shared_service")

# Copy requirements.txt to each service directory
for service in "${services[@]}"; do
    echo "Copying requirements.txt to $service..."
    cp requirements.txt "$service/requirements.txt"
done

echo "Done copying requirements.txt to all services." 