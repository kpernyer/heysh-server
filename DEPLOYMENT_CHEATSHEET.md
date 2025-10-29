# Deployment Cheat Sheet

Quick reference for cloud deployments.

---

## 🚀 Deploy to Production

```bash
just deploy-production v1.2.3 "Add new feature"
```

**What it does:**
1. Stages all changes
2. Creates commit
3. Creates git tag `v1.2.3`
4. Pushes to GitHub
5. Cloud Build automatically deploys everything

**Time:** 5-10 minutes

---

## ⚡ Quick Deploy

```bash
just deploy-quick "Hotfix: Fix bug"
```

Auto-generates version from git hash (e.g., `v0.0.0-abc1234`)

---

## 🧪 Deploy to Staging

```bash
just deploy-staging v1.2.3-beta "Test feature"
```

⚠️ **Note:** Requires staging environment setup (see `DEPLOYMENT_WORKFLOW.md`)

---

## 📊 Monitor Deployment

```bash
# Check status
just deploy-status

# View specific build logs
just deploy-logs <build-id>

# Check backend health
just deploy-check-health

# Test API
just deploy-check-api
```

---

## ⏪ Rollback

```bash
just deploy-rollback v1.2.2
```

Re-deploys a previous version.

---

## 🛠️ Manual Commands (Rarely Needed)

### Check Cloud Run Status
```bash
gcloud run services describe api --region=europe-west3
```

### Check Worker Pods
```bash
kubectl get pods -n temporal-workers
```

### View Backend Logs
```bash
gcloud run logs read api --region=europe-west3 --limit=50
```

### View Worker Logs
```bash
kubectl logs -n temporal-workers -l worker-type=general -f
```

---

## 📋 Deployment Checklist

Before deploying to production:

- [ ] Test locally: `just dev`
- [ ] Run tests: `just test`
- [ ] Test API: `just test-api`
- [ ] Check code quality: `just lint && just format`
- [ ] Deploy to staging (if available)
- [ ] Deploy to production
- [ ] Monitor deployment: `just deploy-status`
- [ ] Verify health: `just deploy-check-health`
- [ ] Check logs if needed

---

## 🎯 Commands You'll Use Daily

```bash
# Deploy
just deploy-production v1.2.3 "Message"
just deploy-quick "Quick fix"

# Monitor
just deploy-status
just deploy-check-health

# Rollback (rare)
just deploy-rollback v1.2.2
```

---

## ❌ What NOT to Run

You should **NOT** need these for normal deployments:

```bash
# ❌ DON'T: Manual infrastructure
terraform apply
gcloud run deploy
helm upgrade
kubectl apply

# ✅ DO: Use justfile commands
just deploy-production v1.2.3 "Message"
```

---

## 🔗 Quick Links

- **Backend URL:** https://api-blwol5d45q-ey.a.run.app
- **Cloud Build:** https://console.cloud.google.com/cloud-build/builds
- **Cloud Run:** https://console.cloud.google.com/run
- **GKE Cluster:** https://console.cloud.google.com/kubernetes

---

**Last Updated:** 2025-01-29
