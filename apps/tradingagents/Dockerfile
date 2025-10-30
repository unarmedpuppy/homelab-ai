FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
	git \
	build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone TradingAgents
RUN git clone https://github.com/TauricResearch/TradingAgents.git /workspace/TradingAgents

WORKDIR /workspace/TradingAgents

# Install dependencies
RUN pip install -r requirements.txt

# Default to the interactive CLI
CMD ["python", "-m", "cli.main"]
