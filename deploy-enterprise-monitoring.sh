#!/bin/bash
# GuardianShield Enterprise-Grade Monitoring Deployment
# Deploys comprehensive AlertManager Helm chart for complete ecosystem monitoring

echo "🚀 ===== GUARDIANSHIELD ENTERPRISE MONITORING DEPLOYMENT ====="
echo ""
echo "📊 Deploying comprehensive monitoring for:"
echo "   ✅ ERC-8055 Shield Token System"
echo "   ✅ Complete Blockchain Infrastructure"  
echo "   ✅ Website & API Performance"
echo "   ✅ Multi-chain Infrastructure"
echo "   ✅ Kubernetes & Security"
echo ""

# Check if running on Kubernetes
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not accessible. Please ensure:"
    echo "   1. kubectl is installed and configured"
    echo "   2. You're connected to the correct cluster"
    echo "   3. You have cluster-admin privileges"
    exit 1
fi

echo "✅ Kubernetes cluster accessible"

# Check if Helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm not found. Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

echo "✅ Helm ready"

# Create namespace
echo "🏗️  Creating monitoring namespace..."
kubectl create namespace guardianshield-monitoring --dry-run=client -o yaml | kubectl apply -f -

# Label namespace for monitoring
kubectl label namespace guardianshield-monitoring monitoring=enabled --overwrite

# Create monitoring network policies (if supported)
echo "🔒 Setting up network security policies..."
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: alertmanager-network-policy
  namespace: guardianshield-monitoring
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: dhi-alertmanager-chart
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: prometheus
    - podSelector:
        matchLabels:
          app: grafana
    ports:
    - protocol: TCP
      port: 9093
  - from: []
    ports:
    - protocol: TCP
      port: 9094
  egress:
  - {}
EOF

# Install/upgrade the chart
echo "📈 Deploying GuardianShield AlertManager Chart..."

helm upgrade --install guardianshield-alerts ./charts/dhi-alertmanager-chart \
  --namespace guardianshield-monitoring \
  --create-namespace \
  --wait \
  --timeout 300s \
  --set global.environment=production \
  --set global.clusterName=$(kubectl config current-context) \
  --set alertmanager.replicaCount=3 \
  --set alertmanager.resources.requests.memory=512Mi \
  --set alertmanager.resources.limits.memory=2Gi

# Wait for deployment to be ready
echo "⏳ Waiting for AlertManager pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=dhi-alertmanager-chart -n guardianshield-monitoring --timeout=300s

# Get deployment status
echo ""
echo "📊 ===== DEPLOYMENT STATUS ====="
kubectl get pods -n guardianshield-monitoring -o wide
kubectl get services -n guardianshield-monitoring
kubectl get ingresses -n guardianshield-monitoring

# Get external access information
EXTERNAL_IP=$(kubectl get svc guardianshield-alerts -n guardianshield-monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$EXTERNAL_IP" ]; then
    EXTERNAL_IP=$(kubectl get svc guardianshield-alerts -n guardianshield-monitoring -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

echo ""
echo "🎉 ===== GUARDIANSHIELD MONITORING DEPLOYED SUCCESSFULLY! ====="
echo ""
echo "🚨 AlertManager Dashboard:"
if [ ! -z "$EXTERNAL_IP" ]; then
    echo "   External URL: http://$EXTERNAL_IP:9093"
fi
echo "   Port Forward: kubectl port-forward svc/guardianshield-alerts 9093:9093 -n guardianshield-monitoring"
echo "   Local URL: http://localhost:9093"
echo ""
echo "📋 Monitoring Capabilities:"
echo "   🛡️  ERC-8055 Shield Token burn/remint monitoring"
echo "   💎 Guard Token (ERC-20) transaction tracking"
echo "   ⛓️  Multi-chain blockchain node monitoring"
echo "   🌐 Website performance and uptime tracking"
echo "   🏗️  Kubernetes infrastructure health"
echo "   🔒 Security and compliance monitoring"
echo ""
echo "📞 Alert Routing:"
echo "   🚨 Critical: ERC-8055 failures, system outages"
echo "   ⚠️  Warning: Performance degradation, resource issues"
echo "   ℹ️  Info: Maintenance, configuration changes"
echo ""
echo "🛠️  Management Commands:"
echo "   View logs: kubectl logs -l app.kubernetes.io/name=dhi-alertmanager-chart -n guardianshield-monitoring"
echo "   Scale up:  kubectl scale deployment guardianshield-alerts --replicas=5 -n guardianshield-monitoring"
echo "   Restart:   kubectl rollout restart deployment guardianshield-alerts -n guardianshield-monitoring"
echo "   Upgrade:   helm upgrade guardianshield-alerts ./charts/dhi-alertmanager-chart -n guardianshield-monitoring"
echo ""
echo "🔧 Configuration:"
echo "   Chart: ./charts/dhi-alertmanager-chart"
echo "   Values: ./charts/dhi-alertmanager-chart/values.yaml"
echo "   Rules: ERC-8055, blockchain, website, infrastructure"
echo ""

# Display next steps
echo "📋 NEXT STEPS:"
echo "   1. Configure your SMTP settings in values.yaml"
echo "   2. Add Slack webhook URLs for team notifications"
echo "   3. Set up PagerDuty integration for critical alerts"
echo "   4. Configure ingress with your domain name"
echo "   5. Test alert firing with sample incidents"
echo ""
echo "🎯 Your GuardianShield ecosystem now has ENTERPRISE-GRADE MONITORING!"
echo "   This covers everything from ERC-8055 tokens to the entire blockchain infrastructure!"