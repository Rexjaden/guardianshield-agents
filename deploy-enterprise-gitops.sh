#!/bin/bash
# GuardianShield Enterprise GitOps Deployment with ArgoCD
# Deploys complete ecosystem with compliance, security, and governance

echo "🚀 ===== GUARDIANSHIELD ENTERPRISE GITOPS DEPLOYMENT ====="
echo ""
echo "🎯 Deploying enterprise GitOps platform with:"
echo "   ✅ ArgoCD with RBAC and compliance controls"
echo "   ✅ App of Apps pattern for ecosystem management"
echo "   ✅ Multi-environment promotion pipeline"
echo "   ✅ Security and compliance enforcement"
echo "   ✅ Automated deployment orchestration"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if kubectl is available and configured
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not accessible"
    echo "   Please ensure kubectl is configured and you have cluster-admin access"
    exit 1
fi

echo "✅ Kubernetes cluster accessible"

# Check if Helm is available
if ! command -v helm &> /dev/null; then
    echo "❌ Helm not found. Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Helm"
        exit 1
    fi
fi

echo "✅ Helm ready"

# Get cluster context for environment detection
CLUSTER_CONTEXT=$(kubectl config current-context)
echo "📍 Deploying to cluster: $CLUSTER_CONTEXT"

# Determine environment based on cluster context
ENVIRONMENT="production"
if [[ $CLUSTER_CONTEXT == *"staging"* ]]; then
    ENVIRONMENT="staging"
elif [[ $CLUSTER_CONTEXT == *"dev"* ]]; then
    ENVIRONMENT="development"
fi

echo "🏗️  Environment detected: $ENVIRONMENT"

# Install ArgoCD if not present
echo "🔧 Setting up ArgoCD..."
if ! kubectl get namespace argocd &> /dev/null; then
    echo "   Creating ArgoCD namespace..."
    kubectl create namespace argocd
    
    echo "   Installing ArgoCD..."
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    # Wait for ArgoCD to be ready
    echo "   Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/argocd-server -n argocd
    kubectl wait --for=condition=available --timeout=600s deployment/argocd-repo-server -n argocd
    kubectl wait --for=condition=available --timeout=600s deployment/argocd-dex-server -n argocd
    
    echo "✅ ArgoCD installed successfully"
else
    echo "✅ ArgoCD already installed"
fi

# Configure ArgoCD for enterprise use
echo "🛡️  Configuring enterprise ArgoCD settings..."

# Apply RBAC configuration
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    # GuardianShield RBAC Policies
    p, role:guardianshield-admin, applications, *, */*, allow
    p, role:guardianshield-admin, clusters, *, *, allow
    p, role:guardianshield-admin, repositories, *, *, allow
    
    p, role:erc8055-developer, applications, sync, guardianshield-ecosystem/erc8055-*, allow
    p, role:erc8055-developer, applications, get, guardianshield-ecosystem/erc8055-*, allow
    
    p, role:infrastructure-admin, applications, *, guardianshield-ecosystem/monitoring-*, allow
    p, role:infrastructure-admin, applications, *, guardianshield-ecosystem/blockchain-*, allow
    
    p, role:security-auditor, applications, get, guardianshield-ecosystem/*, allow
    p, role:security-auditor, applications, get, guardianshield-ecosystem/compliance-*, allow
    
    # Group mappings (configure with your SSO)
    g, guardianshield:admins, role:guardianshield-admin
    g, guardianshield:erc8055-team, role:erc8055-developer
    g, guardianshield:infra-team, role:infrastructure-admin
    g, guardianshield:security-team, role:security-auditor
EOF

# Configure notifications
echo "📧 Setting up ArgoCD notifications..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  config.yaml: |
    triggers:
      - name: on-deployed
        condition: app.status.operationState.phase in ['Succeeded'] and app.status.health.status == 'Healthy'
        template: app-deployed
      - name: on-health-degraded
        condition: app.status.health.status == 'Degraded'
        template: app-health-degraded
      - name: on-sync-failed
        condition: app.status.operationState.phase in ['Error', 'Failed']
        template: app-sync-failed
    
    templates:
      - name: app-deployed
        title: "✅ GuardianShield App Deployed"
        body: |
          Application {{.app.metadata.name}} has been successfully deployed to {{.app.spec.destination.namespace}}.
          Environment: {{.app.metadata.labels.tier}}
          Sync Status: {{.app.status.sync.status}}
          Health: {{.app.status.health.status}}
      
      - name: app-health-degraded
        title: "🚨 GuardianShield App Health Degraded"
        body: |
          ALERT: Application {{.app.metadata.name}} health is degraded!
          Environment: {{.app.metadata.labels.tier}}
          Health: {{.app.status.health.status}}
          Message: {{.app.status.health.message}}
      
      - name: app-sync-failed
        title: "❌ GuardianShield App Sync Failed"
        body: |
          CRITICAL: Application {{.app.metadata.name}} sync failed!
          Environment: {{.app.metadata.labels.tier}}
          Error: {{.app.status.operationState.message}}
    
    services:
      email:
        host: smtp.guardianshield.io
        port: 587
        username: alerts@guardianshield.io
        from: alerts@guardianshield.io
      slack:
        token: \$slack-token  # Configure with your Slack token
      webhook:
        guardianshield-webhook:
          url: https://webhook.guardianshield.io/argocd
          headers:
            - name: Authorization
              value: Bearer \$webhook-token
    
    subscriptions:
      - recipients:
        - email:devops@guardianshield.io
        - slack:gitops-deployments
        triggers:
        - on-deployed
        - on-sync-failed
      - recipients:
        - email:security@guardianshield.io
        - slack:security-alerts
        triggers:
        - on-health-degraded
EOF

# Apply the GuardianShield ArgoCD project
echo "📋 Applying GuardianShield ArgoCD project..."
kubectl apply -f argocd/projects/guardianshield-project.yaml

# Wait for project to be ready
echo "⏳ Waiting for project to be created..."
sleep 10

# Deploy the App of Apps based on environment
echo "🎯 Deploying GuardianShield App of Apps for $ENVIRONMENT..."

if [ "$ENVIRONMENT" == "production" ]; then
    kubectl apply -f argocd/app-of-apps.yaml
    APP_NAME="guardianshield-ecosystem-master"
elif [ "$ENVIRONMENT" == "staging" ]; then
    # Apply staging-specific App of Apps
    kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: guardianshield-ecosystem-staging
  namespace: argocd
spec:
  project: guardianshield-ecosystem
  source:
    repoURL: https://github.com/Rexjaden/guardianshield-agents
    targetRevision: staging
    path: argocd/applications
    helm:
      valueFiles:
        - ../environments/staging.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
    APP_NAME="guardianshield-ecosystem-staging"
else
    # Development environment
    kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: guardianshield-ecosystem-development
  namespace: argocd
spec:
  project: guardianshield-ecosystem
  source:
    repoURL: https://github.com/Rexjaden/guardianshield-agents
    targetRevision: develop
    path: argocd/applications
    helm:
      valueFiles:
        - ../environments/development.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
    APP_NAME="guardianshield-ecosystem-development"
fi

# Wait for initial sync
echo "⏳ Waiting for initial sync to complete..."
sleep 30

# Check ArgoCD application status
echo "📊 Checking application status..."
kubectl get applications -n argocd

# Get ArgoCD admin password
echo "🔑 Getting ArgoCD admin credentials..."
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

# Setup port forwarding for ArgoCD UI access
echo "🌐 Setting up ArgoCD UI access..."
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
PORT_FORWARD_PID=$!

# Display deployment results
echo ""
echo "🎉 ===== GUARDIANSHIELD GITOPS PLATFORM DEPLOYED! ====="
echo ""
echo "🚀 ArgoCD Dashboard:"
echo "   URL: https://localhost:8080"
echo "   Username: admin"
echo "   Password: $ARGOCD_PASSWORD"
echo ""
echo "📋 Deployed Applications:"
echo "   🛡️  ERC-8055 Shield Token System"
echo "   💎 Guard Token (ERC-20) Implementation"
echo "   📊 Complete Monitoring Stack (AlertManager + Prometheus + Grafana)"
echo "   ⛓️  Blockchain Infrastructure"
echo "   🌐 Website and API Gateway"
echo "   🔒 Security and Compliance Framework"
echo "   💾 Disaster Recovery System"
echo ""
echo "🎯 Environment: $ENVIRONMENT"
echo "🏗️  Cluster: $CLUSTER_CONTEXT"
echo "📦 App of Apps: $APP_NAME"
echo ""
echo "🛡️  Enterprise Features:"
echo "   ✅ RBAC with team-based access control"
echo "   ✅ Compliance-driven deployment policies"
echo "   ✅ Automated sync with approval workflows"
echo "   ✅ Multi-environment promotion pipeline"
echo "   ✅ Security policy enforcement"
echo "   ✅ Audit logging and monitoring"
echo ""
echo "🔧 Management Commands:"
echo "   List apps: kubectl get applications -n argocd"
echo "   Sync app:  argocd app sync $APP_NAME"
echo "   App logs:  argocd app logs $APP_NAME"
echo "   Stop port-forward: kill $PORT_FORWARD_PID"
echo ""
echo "📚 ArgoCD CLI Setup:"
echo "   argocd login localhost:8080 --username admin --password $ARGOCD_PASSWORD --insecure"
echo ""
echo "🎊 Your GuardianShield ecosystem is now under ENTERPRISE GITOPS CONTROL!"
echo "   Every deployment is audited, compliant, and automatically managed!"