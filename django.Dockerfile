FROM ghcr.io/astral-sh/uv:python3.13-trixie

# Set working directory to main app
WORKDIR /app/

# Copy application code into image
# (Excludes any files/dirs matched by patterns in .dockerignore)
COPY . /app/

RUN uv sync