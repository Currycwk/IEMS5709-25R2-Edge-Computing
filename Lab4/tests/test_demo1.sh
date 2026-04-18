#!/bin/bash
# Test: Demo 1 — hello-k3s deployment
# Deploys the demo, waits for it, curls the NodePort, then cleans up.
# Works on both Ubuntu workstation and Jetson.

set -e
PASS=0; FAIL=0
export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
DEMO_DIR="$(cd "$(dirname "$0")/../demo/01-hello-k3s" && pwd)"
NODE_PORT=30500
TIMEOUT=120

ok()   { echo "  [PASS] $1"; PASS=$((PASS+1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }

cleanup() {
    echo ""
    echo "==> Cleaning up..."
    kubectl delete -f "$DEMO_DIR/" --ignore-not-found=true &>/dev/null
    ok "Resources deleted"
}
trap cleanup EXIT

echo "========================================"
echo "  Test: Demo 1 — hello-k3s"
echo "========================================"

# 1. Apply manifests
echo ""
echo "[1] Applying manifests..."
kubectl apply -f "$DEMO_DIR/configmap.yaml"
kubectl apply -f "$DEMO_DIR/deployment.yaml"
kubectl apply -f "$DEMO_DIR/service.yaml"
ok "Manifests applied"

# 2. Wait for Deployment to be ready
echo ""
echo "[2] Waiting for Deployment to be Ready (timeout: ${TIMEOUT}s)..."
if kubectl rollout status deployment/hello-k3s --timeout="${TIMEOUT}s"; then
    ok "Deployment hello-k3s is Ready"
else
    fail "Deployment did not become Ready within ${TIMEOUT}s"
    kubectl describe pod -l app=hello-k3s
    exit 1
fi

# 3. Pod is Running
echo ""
echo "[3] Pod status..."
POD_STATUS=$(kubectl get pods -l app=hello-k3s --no-headers | awk '{print $3}' | head -1)
if [ "$POD_STATUS" = "Running" ]; then
    ok "Pod is Running"
else
    fail "Pod status: '${POD_STATUS}'"
fi

# 4. Service exists with correct NodePort
echo ""
echo "[4] Service NodePort..."
SVC_PORT=$(kubectl get svc hello-k3s -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
if [ "$SVC_PORT" = "$NODE_PORT" ]; then
    ok "NodePort is ${NODE_PORT}"
else
    fail "Expected NodePort ${NODE_PORT}, got '${SVC_PORT}'"
fi

# 5. HTTP response
echo ""
echo "[5] HTTP response from NodePort..."
sleep 2
RESPONSE=$(curl -sf --max-time 10 "http://localhost:${NODE_PORT}" 2>/dev/null || echo "")
if echo "$RESPONSE" | grep -q "Hello from K3s"; then
    ok "Got expected response: ${RESPONSE}"
else
    fail "Unexpected response: '${RESPONSE}'"
    echo "     Logs from pod:"
    kubectl logs -l app=hello-k3s --tail=20 || true
fi

# 6. Response includes pod hostname
echo ""
echo "[6] Response includes pod name..."
if echo "$RESPONSE" | grep -q "pod"; then
    ok "Response contains 'pod' field"
else
    fail "Response missing 'pod' field: ${RESPONSE}"
fi

echo ""
echo "========================================"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "========================================"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
