# Persistent faster-whisper ASR service (OpenAI-compatible HTTP API).
# Base image matches Lab2 README (Jetson L4T + CUDA).
FROM dustynv/faster-whisper:r36.4.0-cu128-24.04

WORKDIR /workspace

# Pure-Python deps: install from PyPI (Jetson mirror may be unavailable in some build environments).
RUN pip3 install --no-cache-dir \
    -i https://pypi.org/simple \
    fastapi "uvicorn[standard]" python-multipart

COPY api.py /workspace/api.py

EXPOSE 5092

ENV WHISPER_MODEL_SIZE=small.en \
    WHISPER_COMPUTE_TYPE=int8_float16

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "5092"]
