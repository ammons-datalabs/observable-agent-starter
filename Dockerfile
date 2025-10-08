FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install faster installer (uv) and latest pip
RUN pip install -U pip uv

# Copy project files and install package (from pyproject.toml)
COPY . .
RUN uv pip install --system -e .

# Default command runs the package entrypoint
CMD ["python", "-m", "agents.triage"]
