FROM python:3.11-alpine
WORKDIR /app
COPY app.py config.json ./
# Pre-create target file so Podman file bind-mount works correctly on macOS
RUN mkdir -p /metrics && echo '{}' > /metrics/host.json
EXPOSE 9090
CMD ["python", "app.py"]
