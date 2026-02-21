FROM searxng/searxng:latest

# Install pip and requests (needed by handler.py)
RUN python3 -m ensurepip && \
    python3 -m pip install --no-cache-dir requests>=2.31

# Copy tool files — leave /usr/local/searxng intact as SearXNG's working directory
COPY handler.py runner.py /tool/
COPY entrypoint.sh /tool/entrypoint.sh
RUN chmod +x /tool/entrypoint.sh

ENTRYPOINT ["/tool/entrypoint.sh"]
