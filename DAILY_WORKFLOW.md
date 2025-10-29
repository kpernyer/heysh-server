# Daily Workflow

Your typical day using the justfile.

---

## 🌅 Morning: Start Working

```bash
# Start development environment
just dev
```

**What happens:**
- ✅ Checks if Docker is running
- ✅ Starts infrastructure if needed (Temporal, Neo4j, Weaviate, etc.)
- ✅ Starts backend API with hot reload
- ✅ Shows you URLs for all services

**Now you can:**
- Edit code in `src/workflow/` or `src/activity/`
- Changes auto-reload
- Focus on your real work: backend code

---

## ☕ Mid-Morning: Write Code

```bash
# Your code editor
vim src/workflow/my_workflow.py

# Backend automatically reloads
# No need to restart anything
```

**Infrastructure "just works":**
- Temporal handles workflows
- Neo4j stores graph data
- Weaviate handles embeddings
- You don't think about them

---

## 🧪 Before Lunch: Test Your Code

```bash
# Run tests
just test

# Quick API test
just test-quick

# Check everything is working
just check
```

**If something breaks:**
```bash
# Check what's wrong
just check

# Fix infrastructure
just fix

# View logs
just logs local temporal
```

---

## 🎬 Afternoon: Demo to Stakeholders

```bash
# Start clean demo mode
just demo
```

**Demo mode:**
- Same as dev, but cleaner logs
- Optimized for showing features
- No debug output cluttering the screen

Show them:
- Frontend: `https://www.hey.local`
- API: `https://api.hey.local`

---

## 🚀 Late Afternoon: Ship to Customers

```bash
# Deploy to production
just deploy v1.3.0 "Add search feature"

# Quick hotfix
just deploy-quick "Fix bug in search"
```

**What happens:**
1. Creates git commit + tag
2. Pushes to GitHub
3. Cloud Build deploys everything
4. Takes 5-10 minutes (automated)

**Monitor:**
```bash
# Check deployment status
just check production

# View backend logs
just logs production backend

# View worker logs
just logs production workers
```

---

## 📊 Evening: Learn from Production

```bash
# See how production is performing
just learn
```

**Shows you:**
- Backend health
- Recent deployments
- Worker status
- Performance metrics

**Use this to:**
- Understand user behavior
- Find performance bottlenecks
- Plan next features
- Debug issues

---

## 🌙 End of Day: Clean Up (Optional)

Usually not needed, but if you want:

```bash
# Stop all local services
docker-compose -f docker/docker-compose.yml down

# Or nuclear option (clean everything)
just clean
```

**Tomorrow morning:**
```bash
just dev
# Everything starts fresh
```

---

## 🎯 Common Tasks

### Local Development

```bash
just dev              # Start developing
just demo             # Demo mode
just test             # Run tests
just check            # Check everything is working
just logs local       # View logs
just workers          # Start workers manually (for testing)
```

### Production

```bash
just deploy v1.2.3 "Message"   # Deploy
just deploy-quick "Message"    # Quick deploy
just check production          # Check production health
just logs production backend   # Backend logs
just logs production workers   # Worker logs
just learn                     # Production insights
```

### Maintenance

```bash
just bootstrap           # Initial setup (once)
just bootstrap-production # Verify production setup
just fix                 # Fix broken infrastructure
just clean               # Clean everything
just migrate-db          # Run database migration
```

### Code Quality

```bash
just test           # All tests
just test-quick     # Just API tests
just fmt            # Format code
just lint           # Lint code
```

---

## 🔍 When Things Break

### Local Development Issues

```bash
# Step 1: Check what's wrong
just check

# Step 2: Try fixing it
just fix

# Step 3: If still broken, clean restart
just clean
just bootstrap
just dev
```

### Production Issues

```bash
# Step 1: Check production health
just check production

# Step 2: View logs
just logs production backend
just logs production workers

# Step 3: If needed, rollback
just deploy v1.2.2  # Deploy older version
```

---

## 💡 Pro Tips

### Tip 1: Check First

Always check status before assuming something is broken:

```bash
just check          # Local
just check production   # Production
```

### Tip 2: Use Tab Completion

Most shells support tab completion with `just`:

```bash
just d<tab>      # Shows: deploy, deploy-quick, demo
just l<tab>      # Shows: learn, lint, logs
```

### Tip 3: Read Error Messages

Error messages include helpful hints:

```
❌ Docker is not running
   Run: open -a Docker
```

Just follow the suggestion!

### Tip 4: Logs Tell You Everything

When stuck, check logs:

```bash
just logs local temporal      # Local
just logs production backend  # Production
```

### Tip 5: Bootstrap is Your Friend

If everything is broken and you don't know why:

```bash
just bootstrap-production  # Shows what's misconfigured
```

---

## 📅 Weekly/Monthly Tasks

### Weekly

```bash
# Check production health
just check production
just learn

# Review and clean up
git branch -d old-feature-branch
```

### Monthly

```bash
# Update dependencies
uv sync

# Check for outdated packages
uv pip list --outdated

# Verify production setup
just bootstrap-production
```

---

## 🎓 Philosophy Recap

Your workflow follows these principles:

1. **Infrastructure is invisible** - Bootstrap once, forget about it
2. **Code stays the same** - Local and production use same code (smart config)
3. **Focus on backend** - Your job is workflows and activities
4. **Everything else just works** - Or gives you clear errors to fix
5. **One command deploys** - No manual steps in production

**Daily commands you'll actually use:**

```bash
just dev           # Most of your day
just test          # Before deploying
just deploy        # Ship to customers
just check         # When unsure
just learn         # Understand usage
```

**That's it!** Everything else is infrastructure that stays out of your way.

---

**Last Updated:** 2025-01-29
**Use:** Print this and keep on your desk!
