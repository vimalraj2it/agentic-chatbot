FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy and install dependencies
COPY pyproject.toml .
RUN uv pip install --system -r pyproject.toml

# Copy source code and static files
COPY src/ ./src/
COPY static/ ./static/

EXPOSE 8000
EXPOSE 8501

# Scripts can be used to run both, but here we update for Streamlit primary
CMD ["uv", "run", "streamlit", "run", "src/ui.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
