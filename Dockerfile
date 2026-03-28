# Use python:3.11-slim as base image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy requirements.txt first to leverage Docker's layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the API port
EXPOSE 7860

# Command to run the FastAPI application using uvicorn
CMD ["uvicorn", "env.main:app", "--host", "0.0.0.0", "--port", "7860"]
