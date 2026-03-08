import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


# vLLM server URL (same as eval_llm.py in README)
API_URL = "http://localhost:8000/v1/chat/completions"

headers = {"Content-Type": "application/json"}

BASE_DATA = {
    "model": "/root/.cache/huggingface/Qwen3-4B-quantized.w4a16",
    "messages": [
        {
            "role": "user",
            "content": "Please provide a detailed introduction to the main features of Jetson Orin NX.",
        }
    ],
    "max_tokens": 512,
    "temperature": 0.7,
    "stream": False,  # Use non-streaming API for easier token counting
}


def send_one_request() -> int:
    """
    Send one request and return the number of completion tokens.
    Returns 0 on failure.
    """
    try:
        resp = requests.post(API_URL, headers=headers, json=BASE_DATA, timeout=120)
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] Request failed: {e}")
        return 0

    if resp.status_code != 200:
        print(f"[ERROR] Status code: {resp.status_code}, body: {resp.text}")
        return 0

    try:
        payload = resp.json()
    except json.JSONDecodeError:
        print(f"[ERROR] Failed to parse JSON response: {resp.text[:200]}")
        return 0

    usage = payload.get("usage", {}) or {}
    # OpenAI/vLLM response typically includes completion_tokens or total_tokens
    completion_tokens = usage.get("completion_tokens")
    if completion_tokens is None:
        completion_tokens = usage.get("total_tokens", 0)

    return int(completion_tokens or 0)


def run_throughput_test(concurrency: int) -> float:
    """
    At the given concurrency level, launch N concurrent requests,
    measure total tokens and wall-clock time, return overall throughput (tokens/sec).
    """
    print(f"\n=== Testing concurrency = {concurrency} ===")

    total_tokens = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_one_request) for _ in range(concurrency)]
        for fut in as_completed(futures):
            tokens = fut.result()
            total_tokens += tokens

    end_time = time.time()
    total_time = end_time - start_time

    if total_time <= 0:
        throughput = 0.0
    else:
        throughput = total_tokens / total_time

    print(f"Total tokens: {total_tokens}")
    print(f"Total time: {total_time:.2f} s")
    print(f"Throughput: {throughput:.2f} tokens/sec")

    return throughput


def main():
    # Warm up once to avoid first-request initialization overhead
    print("Warming up...")
    _ = send_one_request()

    # Adjust concurrency levels as needed
    concurrency_levels = [1, 2, 3, 4, 5]

    results = []
    for c in concurrency_levels:
        throughput = run_throughput_test(c)
        results.append(throughput)

    print("\n=== Summary ===")
    for c, t in zip(concurrency_levels, results, strict=True):
        print(f"Concurrency {c}: {t:.2f} tokens/sec")

    # Plot throughput curve and save to llm_throughput.png
    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(6, 4))
        plt.plot(concurrency_levels, results, marker="o")
        plt.xlabel("Concurrency")
        plt.ylabel("Throughput (tokens/sec)")
        plt.title("LLM Throughput vs Concurrency")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("llm_throughput.png", dpi=150)
        print('\nSaved throughput curve to "llm_throughput.png".')
    except ImportError:
        print(
            "\nmatplotlib not installed; only numeric results printed. "
            'To generate llm_throughput.png, run "pip install matplotlib" and re-run this script.'
        )


if __name__ == "__main__":
    main()

