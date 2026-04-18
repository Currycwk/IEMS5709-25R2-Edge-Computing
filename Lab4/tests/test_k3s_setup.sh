#!/bin/bash
# Test: K3s installation and basic cluster health
# Works on both Ubuntu workstation and Jetson.

set -e
PASS=0; FAIL=0

# k3s kubectl symlink ignores ~/.kube/config; set KUBECONFIG explicitly.
export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"

ok()   { echo "  [PASS] $1"; PASS=$((PASS+1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }

echo "========================================"
echo "  Test: K3s Setup"
echo "========================================"

# 1. k3s binary / service
echo ""
echo "[1] K3s service..."
if systemctl is-active --quiet k3s; then
    ok "k3s.service is active"
else
    fail "k3s.service is not active — run: curl -sfL https://get.k3s.io | sh -"
fi

# 2. kubectl reachable
echo ""
echo "[2] kubectl connectivity..."
if kubectl get nodes &>/dev/null; then
    ok "kubectl can reach the cluster"
else
    fail "kubectl cannot reach the cluster — check KUBECONFIG: $KUBECONFIG"
fi

# 3. Node ready
echo ""
echo "[3] Node status..."
NODE_STATUS=$(kubectl get nodes --no-headers 2>/dev/null | awk '{print $2}' | head -1)
if [ "$NODE_STATUS" = "Ready" ]; then
    ok "Node is Ready"
else
    fail "Node status: '${NODE_STATUS}' (expected: Ready)"
fi

# 4. Core system pods running
echo ""
echo "[4] Core system pods (kube-system)..."
NOT_RUNNING=$(kubectl get pods -n kube-system --no-headers 2>/dev/null \
    | grep -v "Running\|Completed" | wc -l)
if [ "$NOT_RUNNING" -eq 0 ]; then
    ok "All kube-system pods are Running/Completed"
else
    fail "$NOT_RUNNING pod(s) in kube-system not yet Running:"
    kubectl get pods -n kube-system --no-headers | grep -v "Running\|Completed" || true
fi

# 5. kubectl version check
echo ""
echo "[5] kubectl version..."
SERVER_VER=$(kubectl version 2>/dev/null | grep "Server" | awk '{print $3}')
ok "Server version: ${SERVER_VER:-$(kubectl version 2>/dev/null | tail -1)}"

echo ""
echo "========================================"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "========================================"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
