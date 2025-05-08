FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python files explicitly
COPY main.py .
COPY db.py .
COPY models.py .
COPY routes.py .
COPY schemas.py .
COPY utils/ ./utils/

# Add debugging
RUN ls -la /app

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"] 