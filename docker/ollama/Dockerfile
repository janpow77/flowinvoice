# Pfad: /docker/ollama/Dockerfile
#
# FlowAudit Ollama Container
# Lokaler LLM-Inferenz-Server für Seminar-Betrieb
#

FROM ollama/ollama:latest

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Pre-pull recommended model (optional, can be done at runtime)
# RUN ollama pull llama3.1:8b-instruct-q4

# Default port
EXPOSE 11434

# Run Ollama serve
CMD ["serve"]
