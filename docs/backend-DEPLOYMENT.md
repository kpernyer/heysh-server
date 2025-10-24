# Deployment Guide for hey.sh

## Domain & Subdomain Strategy

### Production (hey.sh)

```
┌─────────────────────────────────────────────────────────────┐
│  hey.sh Subdomains                                          │
├─────────────────────────────────────────────────────────────┤
│  www.hey.sh          → Frontend (React/Vite)                │
│  app.hey.sh          → Frontend (alternative)               │
│  api.hey.sh          → FastAPI Backend                      │
│  temporal.hey.sh     → Temporal UI (private/VPN)            │
│  neo4j.hey.sh        → Neo4j Browser (private/VPN)          │
│  admin.hey.sh        → Admin Dashboard                      │
│  docs.hey.sh         → API Documentation                    │
└─────────────────────────────────────────────────────────────┘
```

### Local Development (*.hey.local)

```
┌─────────────────────────────────────────────────────────────┐
│  Local Subdomains (via /etc/hosts)                         │
├─────────────────────────────────────────────────────────────┤
│  app.hey.local       → Frontend (port 8081)                 │
│  api.hey.local       → FastAPI Backend (port 8001)          │
│  temporal.hey.local  → Temporal UI (port 8090)              │
│  neo4j.hey.local     → Neo4j Browser (port 7474)            │
│  weaviate.hey.local  → Weaviate (port 8082)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Local Development Setup with Real Hostnames

### Option 1: /etc/hosts (Simplest)

Add these entries to `/etc/hosts`:

```bash
# Hey.sh local development
127.0.0.1  app.hey.local
127.0.0.1  api.hey.local
127.0.0.1  temporal.hey.local
127.0.0.1  neo4j.hey.local
127.0.0.1  weaviate.hey.local
```

**Limitations:**
- Still need to specify ports: `http://api.hey.local:8001`
- Can't use standard ports (80/443) without proxy

### Option 2: Local Proxy (Caddy/Traefik) - RECOMMENDED

Use Caddy to route subdomains to correct ports:

**Benefits:**
- ✅ Use port 80/443 locally
- ✅ Real URLs: `http://api.hey.local` (no ports!)
- ✅ Auto HTTPS with self-signed certs
- ✅ Matches production setup

**Setup:**

```bash
# Install Caddy
brew install caddy

# Create Caddyfile (see docker/Caddyfile below)
# Run Caddy
caddy run --config docker/Caddyfile
```

### Option 3: Docker Compose with Traefik

Full local environment with reverse proxy in Docker.

---

## Cloud Hosting Options Comparison

### Recommended: Hybrid (Supabase + GCP Managed Services)

#### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (Vercel or GCP Cloud Run)                          │
│  → www.hey.sh                                                │
└────────────────┬─────────────────────────────────────────────┘
                 │ HTTPS
                 ↓
┌──────────────────────────────────────────────────────────────┐
│  FastAPI Backend (GCP Cloud Run)                             │
│  → api.hey.sh                                                │
│  - Auto-scaling                                              │
│  - 0-N instances                                             │
│  - Pay per use                                               │
└────────────────┬─────────────────────────────────────────────┘
                 │
        ┌────────┴────────┬─────────────┬──────────────────┐
        ↓                 ↓             ↓                  ↓
┌───────────────┐  ┌─────────────┐  ┌──────────┐  ┌─────────────┐
│ Supabase      │  │ Temporal    │  │ Neo4j    │  │ Weaviate    │
│ (Managed)     │  │ Cloud       │  │ Aura     │  │ Cloud       │
│               │  │ (Managed)   │  │ (Managed)│  │ (Managed)   │
│ - Auth        │  │             │  │          │  │             │
│ - Storage     │  │ Workflows   │  │ Graph DB │  │ Vector DB   │
│ - PostgreSQL  │  │             │  │          │  │             │
└───────────────┘  └─────────────┘  └──────────┘  └─────────────┘
```

#### Cost Estimate (Monthly)

- Supabase Pro: **$25**
- Temporal Cloud: **$200** (or self-host on GKE: ~$50)
- Neo4j Aura: **$65** (2GB RAM)
- Weaviate Cloud: **$50-100** (Serverless)
- GCP Cloud Run: **$20-50** (with some traffic)
- GCP Load Balancer: **$18**

**Total: ~$378-458/month** (or ~$178-258 if self-hosting Temporal)

#### Setup Steps

1. **Domain DNS (Cloudflare or Google Cloud DNS)**
   ```
   A     www.hey.sh        → Vercel IP or Cloud Run IP
   A     api.hey.sh        → Cloud Run Load Balancer IP
   CNAME temporal.hey.sh   → Temporal Cloud URL (private)
   ```

2. **Supabase** (Already set up ✅)
   - No changes needed
   - Add production URL to allowed origins

3. **Temporal Cloud** (Sign up at temporal.io)
   ```bash
   # Get namespace URL and certificates
   TEMPORAL_CLOUD_NAMESPACE=your-namespace.tmprl.cloud
   TEMPORAL_CLOUD_CERT=cert.pem
   TEMPORAL_CLOUD_KEY=key.pem
   ```

4. **Neo4j Aura** (Sign up at neo4j.com/aura)
   ```bash
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=<generated>
   ```

5. **Weaviate Cloud** (Sign up at console.weaviate.cloud)
   ```bash
   WEAVIATE_URL=https://xxx.weaviate.network
   WEAVIATE_API_KEY=<generated>
   ```

6. **Deploy FastAPI to Cloud Run**
   ```bash
   # Build and push Docker image
   cd backend
   gcloud builds submit --tag gcr.io/YOUR-PROJECT/hey-sh-backend

   # Deploy to Cloud Run
   gcloud run deploy hey-sh-backend \
     --image gcr.io/YOUR-PROJECT/hey-sh-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars "TEMPORAL_ADDRESS=$TEMPORAL_CLOUD_NAMESPACE" \
     --set-env-vars "NEO4J_URI=$NEO4J_URI" \
     --set-env-vars "WEAVIATE_URL=$WEAVIATE_URL"

   # Map custom domain
   gcloud run domain-mappings create \
     --service hey-sh-backend \
     --domain api.hey.sh \
     --region us-central1
   ```

7. **Deploy Frontend**
   - **Option A: Vercel** (Easiest)
     ```bash
     # Connect GitHub repo to Vercel
     # Set environment variables in Vercel dashboard
     # Add custom domain: www.hey.sh
     ```

   - **Option B: Cloud Run**
     ```bash
     # Build static site
     cd ../ && npm run build

     # Create nginx Docker image serving /dist
     # Deploy to Cloud Run similar to backend
     ```

---

## Alternative: All-AWS Setup

If you prefer AWS (based on your experience):

#### Architecture

```
Frontend → CloudFront + S3
Backend → ECS Fargate (or Lambda)
Temporal → Self-hosted on ECS or EC2
Neo4j → Self-hosted on EC2 or DocumentDB
Weaviate → Self-hosted on ECS
Supabase → Migrate to RDS + Cognito + S3
```

**Pros:**
- You know AWS well
- Good for larger scale (>10k users)

**Cons:**
- More complex setup
- Need to migrate from Supabase
- More services to manage

**Cost**: Similar or slightly cheaper at scale (~$200-400/month)

---

## Comparison Table

| Aspect | Hybrid (Supabase+GCP) | All-GCP | All-AWS |
|--------|----------------------|---------|---------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ Easiest | ⭐⭐⭐ Moderate | ⭐⭐ Complex |
| **Operational Overhead** | ⭐⭐⭐⭐⭐ Minimal | ⭐⭐⭐ Moderate | ⭐⭐ High |
| **Cost (Small Scale)** | ⭐⭐⭐⭐ $300/mo | ⭐⭐⭐ $400/mo | ⭐⭐⭐ $350/mo |
| **Scalability** | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent |
| **Developer Experience** | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐⭐ Good | ⭐⭐⭐ Good |
| **Vendor Lock-in** | ⭐⭐⭐ Moderate | ⭐⭐ High | ⭐⭐ High |
| **Your Expertise** | ⭐⭐⭐ New | ⭐⭐⭐ New | ⭐⭐⭐⭐⭐ High |

---

## My Recommendation

**Start with Hybrid (Supabase + GCP Managed Services)** because:

1. ✅ **Fastest time to production** - Managed services = less ops
2. ✅ **Already using Supabase** - No migration needed
3. ✅ **Good developer experience** - Focus on product, not infrastructure
4. ✅ **Scales well** - Can handle 10k+ users easily
5. ✅ **Easy to migrate later** - If you outgrow it, move to GKE or AWS

**Future migration path** (if needed):
- Phase 1: Managed services (now)
- Phase 2: Move Temporal to self-hosted GKE (~$2k-5k users)
- Phase 3: Move to AWS or multi-cloud (~$10k+ users)

---

## DNS Configuration for hey.sh

### Cloudflare DNS (Recommended)

```
# Production subdomains
A     @               → Vercel/Cloud Run IP (www)
CNAME www             → Production frontend
CNAME app             → Production frontend (alternative)
A     api             → Cloud Run Load Balancer IP
CNAME temporal        → Temporal Cloud (access via VPN only)
A     neo4j           → Private IP (access via VPN only)
CNAME docs            → Vercel or GitHub Pages
```

### Security

- **Public**: www, app, api, docs
- **Private (VPN-only)**: temporal, neo4j, admin
- Use Cloudflare Access or Tailscale for secure admin access

---

## Next Steps

1. **Decide on hosting** (Hybrid recommended)
2. **Set up local proxy** with Caddy for nice local URLs
3. **Sign up for managed services** (Temporal Cloud, Neo4j Aura, Weaviate Cloud)
4. **Deploy to production** using provided scripts
5. **Configure DNS** for hey.sh subdomains

Ready to proceed with any of these options!
