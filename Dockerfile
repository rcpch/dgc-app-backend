FROM ghcr.io/astral-sh/uv:python3.13-trixie

# Set working directory to main app
WORKDIR /app/

# Add pyproject.toml
COPY pyproject.toml /app/pyproject.toml

# Install dependencies
RUN uv sync