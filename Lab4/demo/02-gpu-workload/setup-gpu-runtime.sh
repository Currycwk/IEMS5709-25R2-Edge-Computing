#!/bin/bash
# Configure K3s to use NVIDIA GPU on Jetson Orin (JetPack 6.x)
# Run this BEFORE installing K3s, or re-install K3s after running.
#
# Requires: JetPack 6.x with nvidia-container-toolkit installed.

set -e

echo "==> Checking prerequisites..."

if ! command -v nvidia-container-runtime &>/dev/null; then
    echo "ERROR: nvidia-container-runtime not found."
    echo "Please ensure JetPack is installed before running this script."
    exit 1
fi

echo "  nvidia-container-runtime: OK"

# Verify system containerd has NVIDIA runtime configured
if ! grep -q "nvidia" /etc/containerd/config.toml 2>/dev/null; then
    echo "  System containerd not configured for NVIDIA. Configuring now..."
    sudo nvidia-ctk runtime configure --runtime=containerd
    sudo systemctl restart containerd
    echo "  containerd restarted."
else
    echo "  System containerd NVIDIA config: OK"
fi

echo ""
echo "==> Installing K3s using system containerd..."
echo "    (Using /run/containerd/containerd.sock so K3s inherits NVIDIA runtime)"
echo ""

curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --container-runtime-endpoint unix:///run/containerd/containerd.sock \
  --kubelet-arg=container-log-max-files=5 \
  --kubelet-arg=container-log-max-size=10Mi" sh -

echo ""
echo "==> Waiting for K3s to be ready..."
sleep 10
sudo k3s kubectl wait --for=condition=Ready node --all --timeout=60s

echo ""
echo "==> Setting up kubectl access..."
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown "$USER:$USER" ~/.kube/config
echo "    KUBECONFIG written to ~/.kube/config"

echo ""
echo "==> Done! Verify with:"
echo "    kubectl get nodes"
echo "    kubectl describe node | grep -A5 'Capacity:'"
