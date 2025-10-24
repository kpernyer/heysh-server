# Uppdatera /etc/hosts för .hey.local Domains

För att `.hey.local` domäner ska fungera behöver du lägga till dem i `/etc/hosts`.

## Steg 1: Öppna /etc/hosts

```bash
sudo nano /etc/hosts
```

## Steg 2: Lägg Till Dessa Entries

Rulla till slutet och lägg till:

```
# ==================== hey.sh Local Development ====================
127.0.0.1 hey.local
127.0.0.1 api.hey.local
127.0.0.1 temporal.hey.local
127.0.0.1 neo4j.hey.local
127.0.0.1 weaviate.hey.local
127.0.0.1 db.hey.local
127.0.0.1 supabase.hey.local

# ==================== Monitoring Stack ====================
127.0.0.1 monitoring.hey.local
127.0.0.1 grafana.hey.local
127.0.0.1 alertmanager.hey.local
127.0.0.1 jaeger.hey.local
127.0.0.1 loki.hey.local
```

## Steg 3: Spara och Avsluta

1. **Ctrl+X** för att avsluta
2. **Y** för att spara
3. **Enter** för att bekräfta

## Steg 4: Verifiera

```bash
# Test DNS resolution
ping -c 1 api.hey.local
ping -c 1 grafana.hey.local

# Eller bara öppna i browser
open http://api.hey.local
open http://grafana.hey.local
```

## Eller: Gör Det Med Script

Om du vill göra det automatiskt (enklare):

```bash
# Backup först
sudo cp /etc/hosts /etc/hosts.backup

# Lägg till entries
cat <<'EOF' | sudo tee -a /etc/hosts > /dev/null

# ==================== hey.sh Local Development ====================
127.0.0.1 hey.local
127.0.0.1 api.hey.local
127.0.0.1 temporal.hey.local
127.0.0.1 neo4j.hey.local
127.0.0.1 weaviate.hey.local
127.0.0.1 db.hey.local
127.0.0.1 supabase.hey.local

# ==================== Monitoring Stack ====================
127.0.0.1 monitoring.hey.local
127.0.0.1 grafana.hey.local
127.0.0.1 alertmanager.hey.local
127.0.0.1 jaeger.hey.local
127.0.0.1 loki.hey.local
EOF

# Verifiera
grep "hey.local" /etc/hosts
```

## Vad Gör Det?

`127.0.0.1` är localhost på din dator. Detta mappar alla `.hey.local` domäner till localhost, så:

- `http://api.hey.local` → `http://127.0.0.1:80` → Caddy → `http://localhost:8000`
- `http://grafana.hey.local` → `http://127.0.0.1:80` → Caddy → `http://localhost:3001`

## Om Du Vill Ändra

### Ta Bort alla hey.local entries

```bash
sudo sed -i '/hey\.local/d' /etc/hosts
```

### Verifiera Det Fungerar

```bash
# Kolla att domänen löses till 127.0.0.1
nslookup api.hey.local
dig api.hey.local

# Eller enkel test
curl http://api.hey.local/health
```

## DNS Cache

Om du ändrar /etc/hosts och det inte fungerar, kanske DNS cache behöver rensas:

```bash
# macOS
sudo dscacheutil -flushcache

# Linux
sudo systemctl restart systemd-resolved

# Eller bara vänta några sekunder
```

## Vad Redan Finns?

Kolla vad som redan är i /etc/hosts:

```bash
grep "hey.local" /etc/hosts
```

Du ser kanske duplicates - det är okej, fungerar ändå. Men om du vill städa upp:

```bash
# Backup
sudo cp /etc/hosts /etc/hosts.backup

# Ta bort duplicates
sudo sed -i '/hey\.local/d' /etc/hosts

# Lägg tillbaka clean version (se script ovan)
```

## Troubleshooting

### "Obestämd värd" eller "Name resolution failed"

1. Kolla /etc/hosts har entries:
   ```bash
   grep "api.hey.local" /etc/hosts
   ```

2. Kolla Caddy körs:
   ```bash
   docker-compose ps | grep caddy
   ```

3. Rensa DNS cache (se ovan)

4. Testa direkt mot localhost:
   ```bash
   curl http://localhost:8000/health  # Bör fungera
   curl http://api.hey.local/health   # Bör också fungera nu
   ```

### Caddy Returnar Error

```bash
# Se Caddy logs
docker-compose logs caddy

# Reload Caddy config
docker-compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### Bara Vissa Domäner Fungerar

Verifiera alla entries finns i /etc/hosts:

```bash
grep "hey.local" /etc/hosts | sort
```

Jämför med `docs/PORT_MAPPING.md` för att se vilka som borde finnas.
