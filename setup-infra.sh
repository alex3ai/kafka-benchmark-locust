#!/bin/bash
export PROJECT_ID=$(gcloud config get-value project)
export CLUSTER_NAME="kafka-bench"
export ZONE="us-central1-a"

echo "🔧 Ativando APIs..."
gcloud services enable container.googleapis.com monitoring.googleapis.com

echo "🚀 Criando GKE Zonal (Num Nodes: 3, Machine: e2-standard-4)..."
# NOTA: Ao usar --zone, criamos 3 nós no total. 
gcloud container clusters create $CLUSTER_NAME \
    --zone $ZONE \
    --num-nodes 3 \
    --machine-type e2-standard-4 \
    --disk-type pd-ssd \
    --disk-size 50 \
    --scopes "https://www.googleapis.com/auth/cloud-platform" \
    --release-channel "regular"

echo "🔌 Obtendo credenciais..."
# ALTERAÇÃO: Buscamos as credenciais da zona específica
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE

echo "📦 Configurando StorageClass SSD..."
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF