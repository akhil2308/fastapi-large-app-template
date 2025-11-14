FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && \
    apt-get install -y python3-dev build-essential --no-install-recommends && \
    apt-get clean && rm -rf /tmp/* /var/tmp/* && rm -rf /var/lib/apt/lists/*

# Copy application source
COPY . /src
WORKDIR /src

# Install uv (Python package installer)
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Install project dependencies
RUN uv pip install --upgrade pip setuptools wheel
RUN uv pip install --system .

# Make run script executable
RUN [ -f run.sh ] && chmod +x run.sh || true

EXPOSE 8000

# Start the application
CMD ["sh", "run.sh"]