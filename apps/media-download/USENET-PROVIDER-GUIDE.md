# Usenet Provider Guide

Since you have **ProtonVPN**, here are the best Usenet provider options for your setup.

## 🎯 Quick Recommendation

### Best Choice: **Frugal Usenet** - $5.99/month
- ✅ Best value for money
- ✅ Unlimited downloads
- ✅ 1,100+ days retention
- ✅ Fast (up to 300 Mbps)
- ✅ Good for most content
- ✅ SSL/TLS support

**Sign up here:** https://www.frugalusenet.com/

---

## 📊 Detailed Comparison

### 1. Frugal Usenet ($5.99/month) ⭐ RECOMMENDED

**Retention:** 1,100+ days  
**Speed:** Up to 300 Mbps  
**Connections:** Unlimited  
**SSL:** ✅ Yes (port 563)

**Pros:**
- Best price-to-performance ratio
- Unlimited downloads
- Good for most content
- Reliable service
- Quick setup

**Cons:**
- Lower retention than premium providers
- May miss very old content

**Best For:**
- Most users
- Budget-conscious buyers
- Recent content (2020+)

**Setup Example:**
```
Server: us.frugalusenet.com
Port: 563 (SSL)
Username: your_username
Password: your_password
Connections: 20
```

---

### 2. Newshosting ($9.99/month)

**Retention:** 5,700+ days  
**Speed:** Up to 750 Mbps  
**Connections:** Unlimited  
**SSL:** ✅ Yes

**Pros:**
- Highest retention (15+ years!)
- Fastest speeds (750 Mbps)
- Excellent for very old content
- Professional service
- Browser included

**Cons:**
- More expensive ($9.99)
- Overkill for recent content only
- Annual discount available but higher upfront

**Best For:**
- Power users
- Need old content (2010+)
- Want maximum retention

**Setup Example:**
```
Server: news.newshosting.com
Port: 563 (SSL)
Username: your_username
Password: your_password
Connections: 20
```

---

### 3. Eweka ($7.99/month)

**Retention:** 5,690+ days  
**Speed:** Up to 300 Mbps  
**Connections:** Unlimited  
**SSL:** ✅ Yes

**Pros:**
- Excellent retention
- Good EU performance
- Unmetered bandwidth
- Reliable service

**Cons:**
- European server (slower in US)
- Slightly more expensive than Frugal

**Best For:**
- EU users
- Need high retention
- Don't need max speed

---

### 4. UsenetServer ($10/month)

**Retention:** 3,800+ days  
**Speed:** Up to 300 Mbps  
**Connections:** Unlimited  
**SSL:** ✅ Yes

**Pros:**
- Good retention
- Reliable service
- Customer support
- All features included

**Cons:**
- More expensive
- Lower retention than Eweka/Newshosting

**Best For:**
- Users wanting middle-ground
- Good all-around option

---

### 5. NewsDemon ($7.99/month)

**Retention:** 2,000+ days  
**Speed:** Up to 300 Mbps  
**Connections:** Unlimited  
**SSL:** ✅ Yes

**Pros:**
- Affordable
- Good retention
- Unlimited bandwidth
- No caps

**Cons:**
- Lower retention than others
- Fewer server locations

**Best For:**
- Budget users
- Recent content only

---

## 💰 Cost Comparison

| Provider | Price | Retention | Speed | Value |
|----------|-------|-----------|-------|-------|
| **Frugal** | $5.99 | 1,100 days | 300 Mbps | ⭐⭐⭐⭐⭐ |
| Newshosting | $9.99 | 5,700 days | 750 Mbps | ⭐⭐⭐⭐ |
| Eweka | $7.99 | 5,690 days | 300 Mbps | ⭐⭐⭐ |
| UsenetServer | $10.00 | 3,800 days | 300 Mbps | ⭐⭐⭐ |
| NewsDemon | $7.99 | 2,000 days | 300 Mbps | ⭐⭐⭐ |

---

## 🎯 My Recommendation for You

### Start with Frugal Usenet

Here's why:
1. **Best value** - Only $5.99/month
2. **Enough retention** - 1,100 days covers most content (2019+)
3. **Unlimited downloads** - No caps
4. **Fast enough** - 300 Mbps is plenty for automation
5. **Works with ProtonVPN** - No compatibility issues

**Total monthly cost:**
- ProtonVPN: $8/month (or you already have it)
- Frugal Usenet: $5.99/month
- NZBGeek indexer: $15 lifetime ($1.25/month)
- **Total: ~$6-9/month**

---

## 📋 Usenet Indexers (Required)

You also need an indexer. Top options:

### 1. NZBGeek - $15 lifetime OR $10/year ⭐ RECOMMENDED

**Why:**
- Most popular indexer
- Excellent automation support
- Great catalog
- Reliable API
- Easy to use

**Sign up:** https://nzbgeek.info/

### 2. DrunkenSlug - $10/year

**Why:**
- Open source ethos
- Good automation
- Solid catalog
- Community-driven

### 3. NZBPlanet - $10/year

**Why:**
- Affordable
- Good coverage
- Reliable

---

## 🚀 Quick Setup Steps

### 1. Sign Up for Frugal Usenet

1. Go to https://www.frugalusenet.com/
2. Click "Sign Up"
3. Choose monthly plan ($5.99)
4. Complete payment
5. Save your credentials

### 2. Configure in NZBGet

Edit `apps/media-download/nzbget/config/nzbget.conf` or use web UI:

```ini
Server1.Host=us.frugalusenet.com
Server1.Port=563
Server1.Username=your_username
Server1.Password=your_password
Server1.Encryption=yes
Server1.Connections=20
Server1.Retention=1100
```

### 3. Sign Up for NZBGeek

1. Go to https://nzbgeek.info/
2. Sign up for lifetime account ($15)
3. Get your API key from profile
4. Add to NZBHydra2 (http://localhost:5076)

### 4. Configure NZBHydra2

1. Open http://localhost:5076
2. Settings → Indexers → Generic Indexers
3. Add NZBGeek:
   - Name: NZBGeek
   - URL: https://api.nzbgeek.info/
   - API Key: (from step 3)
4. Test connection

### 5. Configure in Sonarr/Radarr

1. Open Sonarr (http://localhost:8989)
2. Settings → Indexers
3. Add indexer: NZBHydra2
   - URL: http://nzbhydra2:5076/nzbhydra2
   - API Key: (found in NZBHydra2 settings)
4. Repeat for Radarr

---

## ⚙️ Configuration Tips

### SSL/TLS Setup

**Always use SSL (port 563, not 119):**
- Encrypts your traffic
- Prevents ISP snooping
- Essential for privacy

### Connection Settings

**Optimal connections:**
- Start with 20 connections
- Increase to 30 if needed
- More than 30 rarely helps

### Retention

- **Recent content (2020+):** Any provider works
- **Old content (2010-2019):** Need 3,000+ day retention
- **Very old (pre-2010):** Need 5,000+ day retention

### Speed Optimization

1. Set connections to 20-30
2. Use SSL port (563)
3. Enable par2 repair
4. Set download speed limit if needed
5. Use SSD for faster disk I/O

---

## 🔒 Security with ProtonVPN

Since you have ProtonVPN:

1. **All downloads route through ProtonVPN** (automatic)
2. **DNS leak protection** (configured in WireGuard)
3. **Kill switch** (automatic via network_mode)
4. **SSL encryption** (configure Usenet with SSL)
5. **Swiss privacy laws** (ProtonVPN)

Your setup is secure! ✅

---

## ✅ Quick Start Checklist

- [ ] Sign up for Frugal Usenet ($5.99/month)
- [ ] Sign up for NZBGeek ($15 lifetime)
- [ ] Configure Frugal in NZBGet
- [ ] Add NZBGeek to NZBHydra2
- [ ] Configure NZBHydra2 in Sonarr/Radarr
- [ ] Test a download
- [ ] Verify download goes through ProtonVPN
- [ ] Monitor for DNS leaks

---

## 🧪 Test Your Setup

```powershell
# 1. Check VPN is working
docker exec media-download-wireguard curl ifconfig.me
# Should show ProtonVPN IP

# 2. Check DNS isn't leaking
.\verify-vpn.ps1

# 3. Test download in NZBGet
# Add a small test NZB and check it works

# 4. Check logs
docker-compose logs nzbget
```

---

## 💡 Pro Tips

1. **Start with Frugal** - Best value, upgrade later if needed
2. **Add multiple indexers** - More sources = better completion
3. **Use automation** - Let Sonarr/Radarr handle everything
4. **Monitor logs** - Check for failures
5. **Backup configs** - Run `.\backup-configs.ps1` regularly

---

## 📞 Support

- **Frugal:** support@frugalusenet.com
- **NZBGeek:** Check their forum at nzbgeek.info
- **General:** Check README.md for troubleshooting

Ready to start? Sign up for Frugal Usenet now! https://www.frugalusenet.com/

