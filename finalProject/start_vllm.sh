#!/bin/bash
MODEL_PATH="/opt/models/Qwen3-4B-quantized.w4a16"
PORT=8000

if [ ! -d "$MODEL_PATH" ]; then
    echo "Error: Model not found at $MODEL_PATH"
    exit 1
fi

echo "Starting vLLM server with Qwen3-4B..."
docker run \
    -d -it \
    --network host \
    --shm-size=8g \
    --ulimit memlock=-1 \
    --ulimit stack=67108864 \
    --runtime=nvidia \
    --name=vllm-finalproject \
    -v "$MODEL_PATH:/root/.cache/huggingface/Qwen3-4B-quantized.w4a16" \
    ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
    vllm serve /root/.cache/huggingface/Qwen3-4B-quantized.w4a16 \
        --host 0.0.0.0 \
        --port $PORT \
        --gpu-memory-utilization 0.40 \
        --max-model-len 4096 \
        --max-num-batched-tokens 2048

echo "Health check: curl -s http://localhost:$PORT/v1/models"
