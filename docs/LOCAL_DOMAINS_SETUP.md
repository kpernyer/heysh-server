# Local Development with Real Hostnames

Stop using `localhost:8001`, `localhost:8081`, etc. Use real subdomains like production!

## Quick Setup

```bash
cd backend

# 1. Setup local domains (installs Caddy, updates /etc/hosts)
just setup-domains

# 2. Start all services (if not already running)
just dev

# 3. In a new terminal, start the reverse proxy
just proxy
```

## Access Your Services

Instead of remembering port numbers:

| Old (Ports) | New (Domains) |
|-------------|---------------|
| `http://localhost:8081` | `http://app.hey.local` |
| `http://localhost:8001` | `http://api.hey.local` |
| `http://localhost:8090` | `http://temporal.hey.local` |
| `http://localhost:7474` | `http://neo4j.hey.local` |
| `http://localhost:8082` | `http://weaviate.hey.local` |

## How It Works

1. **`/etc/hosts`** - Maps `*.hey.local` to `127.0.0.1`
2. **Caddy** - Reverse proxy that routes domains to ports
3. **Your services** - Still run on their respective ports

## Production Subdomains (hey.sh)

When you deploy to production, you'll use:

| Service | Local | Production |
|---------|-------|------------|
| Frontend | `app.hey.local` | `www.hey.sh` or `app.hey.sh` |
| API | `api.hey.local` | `api.hey.sh` |
| Temporal UI | `temporal.hey.local` | `temporal.hey.sh` (private) |
| Neo4j | `neo4j.hey.local` | `neo4j.hey.sh` (private) |
| Docs | - | `docs.hey.sh` |

See `backend/DEPLOYMENT.md` for full production setup guide.

## Benefits

✅ **Realistic** - Matches production setup
✅ **Clean URLs** - No port numbers to remember
✅ **CORS-friendly** - Subdomains work better than ports
✅ **Professional** - Real domain-based development

## Troubleshooting

**Caddy not found?**
```bash
brew install caddy
```

**Port already in use?**
- Caddy uses port 80. Stop other services on port 80.
- Or modify `docker/Caddyfile` to use other ports (e.g., `:8080`)

**Can't access `*.hey.local`?**
- Check `/etc/hosts` has entries
- Try `ping app.hey.local` - should resolve to 127.0.0.1
- Restart browser to clear DNS cache
