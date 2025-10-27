# Provider Recommendations

This document provides recommendations for VPN and Usenet providers that work well with this setup.

## 🔒 VPN Providers

All VPN providers listed below support WireGuard and provide excellent privacy features.

### Top Recommendations

#### 1. Mullvad VPN ($5/month)
- **Why:** No logging, anonymous payment, WireGuard support, fast speeds
- **Privacy:** Accepts cash payments, no email required
- **Download:** https://mullvad.net/
- **Setup:** Download WireGuard config from website
- **DNS:** Provides DNS servers (can also use 1.1.1.1 for Cloudflare DNS)

#### 2. IVPN ($8/month)
- **Why:** Strong privacy commitment, multi-hop VPN, excellent security
- **Privacy:** Based in Gibraltar, strict no-logging policy
- **Download:** https://www.ivpn.net/
- **Setup:** Download WireGuard config from website
- **DNS:** Provides DNS + option to use custom DNS

#### 3. ProtonVPN ($8/month, free tier available)
- **Why:** Swiss privacy laws, free tier, good features
- **Privacy:** Based in Switzerland, strong privacy laws
- **Download:** https://protonvpn.com/
- **Setup:** Download WireGuard config from website
- **DNS:** Provides secure DNS servers

#### 4. Perfect Privacy ($9.99/month)
- **Why:** Advanced features, port forwarding, port randomization
- **Privacy:** Located in Switzerland
- **Download:** https://www.perfect-privacy.com/
- **Setup:** Download WireGuard config from website
- **DNS:** Provides DNS + DoH support

### How to Choose

1. **Privacy-focused:** Mullvad or IVPN
2. **Budget-friendly:** Mullvad ($5) or ProtonVPN free tier
3. **Feature-rich:** Perfect Privacy
4. **Easy setup:** All of them support WireGuard with simple config files

## 📰 Usenet Providers

Quality Usenet providers offer excellent retention, fast speeds, and reliability.

### Top Recommendations

#### 1. Frugal Usenet ($5.99/month)
- **Retention:** 1,100+ days
- **Speed:** Up to 300 Mbps
- **Why:** Best value, unlimited downloads, good support
- **URL:** https://www.frugalusenet.com/
- **Setup:** Simple server config, SSL supported
- **Best for:** Budget-conscious users who want good performance

#### 2. Newshosting ($9.99/month)
- **Retention:** 5,700+ days
- **Speed:** Up to 750 Mbps
- **Why:** High retention, very reliable, excellent speeds
- **URL:** https://www.newshosting.com/
- **Setup:** Professional setup, includes browser
- **Best for:** Heavy users who need maximum retention

#### 3. Eweka ($7.99/month)
- **Retention:** 5,690+ days
- **Speed:** Up to 300 Mbps
- **Why:** Excellent retention, good EU performance
- **URL:** https://eweka.nl/
- **Setup:** Simple configuration
- **Best for:** EU-based users or those needing maximum retention

#### 4. UsenetServer ($10/month)
- **Retention:** 3,800+ days
- **Speed:** Up to 300 Mbps
- **Why:** Good all-around performance
- **URL:** https://usenetserver.com/
- **Setup:** Easy to configure
- **Best for:** Users wanting reliable middle-ground option

#### 5. NewsDemon ($7.99/month)
- **Retention:** 2,000+ days
- **Speed:** Up to 300 Mbps
- **Why:** Affordable, unlimited downloads
- **URL:** https://www.newsdemon.com/
- **Setup:** Simple server configuration
- **Best for:** Budget users who don't need extreme retention

### How to Choose

1. **Budget:** Frugal Usenet or NewsDemon ($5.99-$7.99)
2. **Retention:** Eweka or Newshosting (5000+ days)
3. **Speed:** Newshosting (750 Mbps)
4. **Value:** Frugal Usenet (best balance)

### Configuration Tips

- Use **SSL/TLS** (port 563, not 119)
- Set **20-30 connections** for best performance
- Enable **par2 repair** in downloader
- Check retention for your content type

## 🔍 Usenet Indexers (Required)

You need an indexer to search and find content. These aggregate NZB files from various sources.

### Top Recommendations

#### 1. NZBGeek (Lifetime $15 or $10/year)
- **Content:** Comprehensive coverage
- **API:** Excellent, works great with automation
- **Why:** Most popular, reliable, great for automation
- **URL:** https://nzbgeek.info/
- **Best for:** Most users, easiest to set up

#### 2. NZBPlanet ($10/year)
- **Content:** Good coverage, especially new releases
- **API:** Good automation support
- **Why:** Affordable, reliable
- **URL:** https://www.nzbplanet.net/
- **Best for:** Budget-conscious users

#### 3. DrunkenSlug ($10/year)
- **Content:** Excellent catalog, fast updates
- **API:** Great API with strong automation
- **Why:** Open source ethos, good community
- **URL:** https://drunkenslug.com/
- **Best for:** Automation-focused users

#### 4. Slug (Free tier + $10/year premium)
- **Content:** Solid coverage
- **API:** Works well for automation
- **Why:** Open source indexer, free tier available
- **URL:** https://www.slug.su/
- **Best for:** Open source enthusiasts

### Indexer Setup

1. Sign up for 1-2 indexers
2. Get your API key from indexer settings
3. Add to NZBHydra2 in this system
4. Configure in Sonarr/Radarr/Lidarr

**Tip:** Start with NZBGeek as it's the easiest and most reliable.

## 🧲 Torrent Indexers (Optional, Legal Only)

### Recommendations

- **Linux Distributions:** Use official distro torrents
- **Legal Content:** Public domain, Creative Commons
- **Educational:** MIT OpenCourseWare, Khan Academy
- **Software:** Open source projects (GitHub releases often have torrents)

**Important:** Only use legitimate, legal torrent trackers and sources.

## 💰 Cost Breakdown

### Minimum Setup (Basic User)
- VPN: Mullvad ($5/month)
- Usenet: Frugal Usenet ($5.99/month)
- Indexer: NZBGeek ($15 lifetime)
- **Total: ~$11/month + $15 one-time**

### Recommended Setup (Normal User)
- VPN: Mullvad ($5/month)
- Usenet: Frugal Usenet or Newshosting ($5.99-$9.99/month)
- Indexer: NZBGeek or DrunkenSlug ($10/year)
- **Total: ~$11-$15/month**

### Premium Setup (Power User)
- VPN: IVPN or ProtonVPN ($8/month)
- Usenet: Newshosting or Eweka ($9.99/month)
- Indexer: Multiple ($10-20/year combined)
- **Total: ~$18-$20/month**

## ✅ Verification Checklist

After setting up providers:

- [ ] VPN connected and working
- [ ] VPN DNS leak protection enabled
- [ ] Usenet provider configured in NZBGet/SABnzbd
- [ ] Indexer added to NZBHydra2
- [ ] Indexer configured in Sonarr/Radarr
- [ ] Test download successful
- [ ] All traffic routes through VPN
- [ ] No DNS leaks detected
- [ ] Kill switch working (test by stopping VPN)

## 🛡️ Security Best Practices

1. **Use paid providers only** - avoid public/free indexers
2. **Enable SSL/TLS** - always encrypt your Usenet connections
3. **Set up VPN kill switch** - already configured in this system
4. **Prevent DNS leaks** - configured in WireGuard
5. **Use strong passwords** - for all indexer accounts
6. **Keep providers updated** - use latest WireGuard configs
7. **Test regularly** - check for VPN drops and DNS leaks
8. **Backup configs** - save your configuration files

## 📞 Support Resources

### VPN Providers
- Mullvad: support@mullvad.net
- IVPN: https://www.ivpn.net/support/
- ProtonVPN: https://protonvpn.com/support/

### Usenet Providers
- Frugal: support@frugalusenet.com
- Newshosting: https://www.newshosting.com/support/
- Eweka: https://eweka.nl/support

### Indexers
- NZBGeek: Check their forum
- NZBPlanet: Check their forum
- DrunkenSlug: Check their wiki

## ⚖️ Legal Notice

This system is designed for downloading content you have the legal right to download, including:
- Content in the public domain
- Creative Commons licensed content
- Content you own or have rights to
- Linux distributions and open source software
- Educational content
- Content with proper licensing

**Always respect copyright laws** and only use reputable, legal providers and indexers.

