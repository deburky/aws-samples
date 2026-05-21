FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:/usr/local/bin:$PATH"

# System deps + Node.js 20
RUN apt-get update && apt-get install -y \
    curl wget git ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ttyd
RUN curl -fsSL https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64 \
    -o /usr/local/bin/ttyd && chmod +x /usr/local/bin/ttyd

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app
COPY . .

# Python venv + deps
RUN uv venv app/.venv && \
    uv pip install --python app/.venv marimo boto3 python-dotenv

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# marimo on 2718, ttyd on 7681
EXPOSE 2718 7681

ENTRYPOINT ["/docker-entrypoint.sh"]
