FROM python:3.11-alpine
WORKDIR /app
COPY app.py config.json ./
RUN mkdir -p /hosttmp
EXPOSE 9090
CMD ["python", "app.py"]
