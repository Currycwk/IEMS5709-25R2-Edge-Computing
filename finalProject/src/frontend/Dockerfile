FROM python:3.10-slim

WORKDIR /app

RUN python -m http.server --help >/dev/null

COPY . .

EXPOSE 9898

CMD ["python", "-m", "http.server", "9898"]
