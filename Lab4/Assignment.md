# Lab 4 Assignment

## Task 1: Write K3s Manifests for the AI Stack

Skeleton YAML files are provided in the `Lab4/` directory. Each file contains `# TODO` comments marking the sections you must complete. Your goal is to deploy the same four services from Lab 3 (`vllm`, `asr`, `tts`, `open-webui`) on K3s.

Apply all manifests with:

```bash
kubectl apply -f vllm.yaml
kubectl apply -f asr.yaml
kubectl apply -f tts.yaml
kubectl apply -f open-webui.yaml
```

Watch the pods start up:

```bash
kubectl get pods --watch
```

All four pods should reach `Running` status before you proceed to Task 2. If a pod gets stuck, use `kubectl describe pod <pod-name>` and `kubectl logs <pod-name>` to diagnose.

Key points to consider for each service:

**`vllm.yaml`**
- vLLM requires `hostNetwork: true` (same reason as `network_mode: host` in Lab 3 — low-latency GPU memory access).
- Mount the quantized model from the host: `/opt/models/Qwen3-4B-quantized.w4a16` → `/root/.cache/huggingface/Qwen3-4B-quantized.w4a16`
- Replace `shm_size: "8g"` with an `emptyDir` volume of type `Memory` and `sizeLimit: 8Gi`, mounted at `/dev/shm`.
- Request GPU access via `resources.limits: {nvidia.com/gpu: 1}`.
- Keep `--gpu-memory-utilization 0.50` in the vLLM startup command to leave GPU memory for ASR and TTS.

> **Note on `hostNetwork`:** Because vLLM uses `hostNetwork: true`, its port 8000 is bound directly on the Jetson's network interface. Other pods cannot reach it via a ClusterIP Service DNS name (`http://vllm:8000`). They must use the Jetson's IP address instead: `http://<jetson-ip>:8000`. You will need this in Task 2.

**`asr.yaml`**
- Create a `Deployment` and a `ClusterIP` `Service` (port 5092).
- Request GPU access via `resources.limits: {nvidia.com/gpu: 1}`.
- Other pods will reach ASR at `http://asr:5092` via K3s DNS.

**`tts.yaml`**
- Create a `Deployment` and a `ClusterIP` `Service` (port 8880).
- Request GPU access via `resources.limits: {nvidia.com/gpu: 1}`.
- Other pods will reach TTS at `http://tts:8880` via K3s DNS.

**`open-webui.yaml`**
- Create a `Deployment` and a `NodePort` `Service` that maps external port `30000` → pod port `8080`.
- Replace the named Docker volume with a `PersistentVolumeClaim` (2 Gi, `ReadWriteOnce`) mounted at `/app/backend/data`.

> **Shared GPU memory:** Jetson Orin NX has 16 GiB of shared CPU/GPU memory. `vllm` is configured with `--gpu-memory-utilization 0.50`, reserving half for `asr` and `tts`. If you encounter OOM errors, try reducing `--max-model-len`.

---

## Task 2: Configure Open WebUI

Once all pods are `Running`, open your browser and go to `http://<jetson-ip>:30000`.

First-time users will be asked to create an admin account. If the page is not shown, your groupmate may have already created one on the same port — change the `nodePort` in `open-webui.yaml` to an unused value (e.g. `30001`) and re-apply.

### 2.1 Connect LLM (vLLM)

Because vLLM uses `hostNetwork: true`, you must use the Jetson's IP address — not the service name.

1. Click the **avatar** (bottom-left) → **Admin Panel**
2. Go to **Settings** → **Connections**
3. Under **OpenAI API**, set:
   - API URL: `http://<jetson-ip>:8000/v1`
   - API Key: `not-needed`
4. Click the **refresh icon** next to the URL — you should see the Qwen3 model appear.

### 2.2 Configure Speech-to-Text (ASR)

ASR is a ClusterIP service and is reachable by its K3s DNS name from within the cluster. However, Open WebUI resolves backend URLs server-side (inside its own pod), so the DNS name works here.

1. In Admin Panel, go to **Settings** → **Audio**
2. Under **STT Settings**, set:
   - STT Engine: `OpenAI`
   - API Base URL: `http://asr:5092/v1`
   - API Key: `not-needed`
   - STT Model: `faster-whisper`

### 2.3 Configure Text-to-Speech (TTS)

1. Still in **Settings** → **Audio**
2. Under **TTS Settings**, set:
   - TTS Engine: `OpenAI`
   - API Base URL: `http://tts:8880/v1`
   - API Key: `not-needed`
   - TTS Voice: `af_bella`
   - TTS Model: `kokoro`
3. Click **Save** at the bottom.

---

## Task 3: Voice Call Recording

### Browser Microphone Permission

Chrome blocks microphone access on non-HTTPS pages (except `localhost`). If you are accessing the Jetson remotely via its IP address, you need to make the browser see `localhost`. Here are three options:

**Option A — VS Code / Cursor Port Forwarding (easiest):**

If you are connected to the Jetson via VS Code or Cursor Remote-SSH:

1. Open the **Ports** panel (bottom bar → **Ports**, or `Ctrl+Shift+P` → "Ports: Focus on Ports View")
2. Click **Forward a Port**, enter `30000`
3. Open `http://localhost:30000` in your browser — the connection is automatically tunneled to the Jetson.

**Option B — SSH Port Forwarding:**

```bash
ssh -L 30000:localhost:30000 <user>@<jetson-ip>
```

Then open `http://localhost:30000` in your browser.

**Option C — Chrome Insecure Origins Flag:**

1. Open `chrome://flags/#unsafely-treat-insecure-origin-as-secure` in Chrome
2. Add `http://<jetson-ip>:30000` to the list
3. Click **Relaunch**

### Start the Voice Call

1. Select the Qwen3-4B model in the chat page.
2. Click the **phone icon** (top-right of the chat area) to start a voice call.
3. Allow microphone access when prompted by the browser.
4. Conduct at least **2 complete rounds** of voice dialogue.
5. Record your screen and save as `screen-record.mp4`.

---

## Submission

Please submit your work to Blackboard by uploading the following files:

```
vllm.yaml
asr.yaml
tts.yaml
open-webui.yaml
screen-record.mp4
```
