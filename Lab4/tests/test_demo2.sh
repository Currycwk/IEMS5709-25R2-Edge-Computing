#!/bin/bash
# Test: Demo 2 — GPU workload verification
# Jetson Orin only. Skips gracefully on non-GPU nodes.

set -e
PASS=0; FAIL=0
export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
DEMO_DIR="$(cd "$(dirname "$0")/../demo/02-gpu-workload" && pwd)"
TIMEOUT=120

ok()   { echo "  [PASS] $1"; PASS=$((PASS+1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }
skip() { echo "  [SKIP] $1"; }

cleanup() {
    echo ""
    echo "==> Cleaning up..."
    kubectl delete pod gpu-test --ignore-not-found=true &>/dev/null
    ok "Pod deleted"
}
trap cleanup EXIT

echo "========================================"
echo "  Test: Demo 2 — GPU Workload (Jetson)"
echo "========================================"

# 1. Check GPU is advertised by the node
echo ""
echo "[1] Checking nvidia.com/gpu capacity on node..."
GPU_COUNT=$(kubectl get nodes -o jsonpath='{.items[0].status.capacity.nvidia\.com/gpu}' 2>/dev/null || echo "")
if [ -z "$GPU_COUNT" ] || [ "$GPU_COUNT" = "0" ]; then
    skip "No nvidia.com/gpu capacity found on node."
    echo ""
    echo "  This test requires:"
    echo "    1. K3s installed with NVIDIA container runtime (run setup-gpu-runtime.sh)"
    echo "    2. NVIDIA device plugin deployed (apply nvidia-device-plugin.yaml)"
    echo ""
    echo "  To set up GPU support:"
    echo "    bash $DEMO_DIR/setup-gpu-runtime.sh"
    echo "    kubectl apply -f $DEMO_DIR/nvidia-device-plugin.yaml"
    exit 0
fi
ok "Node reports ${GPU_COUNT} GPU(s)"

# 2. Device plugin pod is running
echo ""
echo "[2] NVIDIA device plugin status..."
PLUGIN_STATUS=$(kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds \
    --no-headers 2>/dev/null | awk '{print $3}' | head -1)
if [ "$PLUGIN_STATUS" = "Running" ]; then
    ok "Device plugin pod is Running"
else
    fail "Device plugin status: '${PLUGIN_STATUS}' — apply nvidia-device-plugin.yaml first"
fi

# 3. Deploy gpu-test pod
echo ""
echo "[3] Deploying gpu-test pod..."
kubectl delete pod gpu-test --ignore-not-found=true &>/dev/null
kubectl apply -f "$DEMO_DIR/gpu-test-pod.yaml"
ok "gpu-test pod created"

# 4. Wait for pod to complete
echo ""
echo "[4] Waiting for pod to complete (timeout: ${TIMEOUT}s)..."
if kubectl wait --for=condition=Succeeded pod/gpu-test --timeout="${TIMEOUT}s" 2>/dev/null; then
    ok "Pod completed successfully"
else
    POD_PHASE=$(kubectl get pod gpu-test -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    fail "Pod did not succeed (phase: ${POD_PHASE})"
    kubectl describe pod gpu-test | tail -20
    exit 1
fi

# 5. Check nvidia-smi output in logs
echo ""
echo "[5] Verifying nvidia-smi output..."
LOGS=$(kubectl logs gpu-test 2>/dev/null || echo "")
if echo "$LOGS" | grep -q "GPU test passed"; then
    ok "nvidia-smi ran and reported GPU successfully"
    echo ""
    echo "  --- GPU Info ---"
    echo "$LOGS" | head -20
    echo "  ----------------"
else
    fail "Expected 'GPU test passed' in pod logs"
    echo "  Logs: $LOGS"
fi

echo ""
echo "========================================"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "========================================"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
