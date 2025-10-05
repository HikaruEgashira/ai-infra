FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY server.py .

# Expose the HTTP port
EXPOSE 8000

# Run the FastMCP proxy server
CMD ["python", "server.py"]
