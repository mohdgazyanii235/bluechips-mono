# Bluechips Blog — Deployment Guide

This is the SEO-focused blog for Bluechips London, built with Astro. It deploys as a static site to Vercel at `blog.bluechips.live`.

## What's been built

- **5 long-form SEO blog posts** (1,500–2,500 words each), written for high-intent keywords
- **Static site generation** — pure HTML output, perfect for Google indexing
- **Full SEO stack**: JSON-LD Article schema, BreadcrumbList schema, Blog schema on index, Open Graph + Twitter Cards on every page, canonical URLs, RSS feed at `/rss.xml`, sitemap at `/sitemap-index.xml`
- **Matching design system** — same gold/ivory-on-black luxury theme as the main site (Playfair Display + Inter fonts, identical colour tokens)
- **Performance**: HTML compression, font preconnect, CSS inlining for above-the-fold styles, immutable cache headers on static assets
- **`robots.txt`** allowing all crawlers, declaring the sitemap
- **Internal linking** between posts and to `bluechips.live` for SEO authority transfer

## Local development

```bash
cd blog
npm install
npm run dev      # runs at http://localhost:4321
npm run build    # outputs to dist/
npm run preview  # preview the production build
```

## Deployment to `blog.bluechips.live` (manual steps)

### Step 1: Push the code to your existing repo

The blog lives at `blog/` in the `BluechipsLondon` repo. Already committed alongside the rest of the codebase.

### Step 2: Create a new Vercel project

1. Go to https://vercel.com/new
2. Click **Import Git Repository** and select the `BluechipsLondon` repo
3. On the configure screen:
   - **Project Name**: `bluechips-blog` (or your preference)
   - **Framework Preset**: Astro (auto-detected)
   - **Root Directory**: click "Edit" and set to `blog` ⚠️ This is the critical step — Vercel needs to know the blog is in a subdirectory of the monorepo
   - **Build Command**: leave default (`npm run build`)
   - **Output Directory**: leave default (`dist`)
   - **Install Command**: leave default (`npm install`)
4. Click **Deploy**

The first deployment will succeed and give you a URL like `bluechips-blog-xyz.vercel.app`. Verify the blog works there before the next step.

### Step 3: Add the custom domain `blog.bluechips.live`

1. In the Vercel project, go to **Settings → Domains**
2. Add the domain: `blog.bluechips.live`
3. Vercel will show you a DNS record to add. It will be either:
   - `CNAME blog → cname.vercel-dns.com`
   - or an `A record` pointing to a Vercel IP
4. Go to your domain registrar (wherever `bluechips.live` is registered) and add that DNS record exactly as Vercel specifies
5. Back in Vercel, click **Refresh** — it usually verifies within 1–5 minutes
6. Vercel will automatically issue a free Let's Encrypt SSL certificate

### Step 4: Enable Vercel Analytics on the blog (optional but recommended)

1. In the Vercel project, go to **Analytics**
2. Click **Enable Analytics**
3. The free tier includes 2,500 events/month, plenty for a blog

That's it. The blog will redeploy automatically every time you push to `main` (or whatever branch you choose).

---

## Vercel Analytics for the main app (`bluechips.live`)

The `@vercel/analytics` and `@vercel/speed-insights` packages have already been added to `frontend/package.json` and wired into `frontend/src/main.tsx`. To activate them:

1. Make sure your main app is deployed on Vercel (it appears to be — the `frontend/vercel.json` is set up for it)
2. Run `npm install` in the `frontend/` directory locally (or let Vercel install on next deploy)
3. Push a commit — Vercel will pick up the new packages on the next deploy
4. Go to your main app's Vercel project: **Settings → Analytics → Enable**
5. Go to **Settings → Speed Insights → Enable** (Web Vitals dashboard)

Both will show up automatically once enabled. No further code changes needed.

**Free tier limits:**
- Analytics: 25,000 events/month
- Speed Insights: 10,000 data points/month

If you exceed these, Vercel emails you and you can upgrade — there's no surprise billing.

---

## Where the sitemaps live

After deployment, you'll have three sitemaps:

| URL | Source | Contains |
|---|---|---|
| `https://bluechips.live/sitemap.xml` | Backend FastAPI endpoint (dynamic) | All escort profiles + borough pages + static pages |
| `https://blog.bluechips.live/sitemap-index.xml` | Astro build (static) | All blog posts + blog homepage |
| `https://bluechips.live/robots.txt` | Frontend static file | References both sitemaps |

⚠️ **The main sitemap requires backend routing.** I added a Vercel rewrite in `frontend/vercel.json` that proxies `/sitemap.xml` to `https://api.bluechips.live/sitemap.xml`. **If your production backend is on a different URL**, edit `frontend/vercel.json` and change the destination.

To check what your backend URL is, you can find it in:
- Your Docker host's reverse proxy config (nginx, Caddy, Traefik)
- Your DNS records for `api.bluechips.live` or whatever subdomain you use
- Your `.env` file's `BACKEND_URL` setting in production

Alternatively, after deploying the backend, you can test the dynamic sitemap directly: `curl https://api.bluechips.live/sitemap.xml`

---

## Submit the sitemaps to Google

Once everything is live:

1. Set up Google Search Console at https://search.google.com/search-console (if you haven't)
2. Add both properties:
   - `https://bluechips.live`
   - `https://blog.bluechips.live`
3. Verify ownership (DNS TXT record is the easiest method)
4. Submit both sitemaps:
   - For the main domain: submit `https://bluechips.live/sitemap.xml`
   - For the blog: submit `https://blog.bluechips.live/sitemap-index.xml`
5. Repeat the property verification + sitemap submission on Bing Webmaster Tools (https://www.bing.com/webmasters) — Bing also powers DuckDuckGo and Yahoo

Google will start crawling within hours; full indexing of all posts and profiles takes 1–4 weeks depending on existing site authority.

---

## Adding new blog posts

To add a new post, create a markdown file in `blog/src/content/blog/`:

```markdown
---
title: "Your Post Title"
description: "A meta description, ideally 140-160 characters, for SEO"
publishDate: 2025-06-01
author: "Bluechips London Editorial"
category: "Borough Guides"
tags: ["mayfair", "guide"]
keywords: ["target keyword 1", "target keyword 2"]
---

Your content here. Use ## for H2s, ### for H3s. Internal links to other
blog posts use relative paths like (/some-other-slug). Links to
the main site use absolute URLs (https://bluechips.live/...).
```

Push to git → Vercel auto-deploys → post is live with full SEO metadata, sitemap entry, and RSS update.

---

## Why subdomain instead of `/blog` subdirectory?

I chose `blog.bluechips.live` (subdomain) over `bluechips.live/blog` (subdirectory) because:

1. **Cleaner deployment** — independent Vercel project, independent caching, independent build pipeline
2. **No conflict with the SPA's catch-all routing** — your main app rewrites everything to `/index.html`, so a subdirectory blog would need a fragile rewrite chain
3. **Modern Google handles subdomains well** — the old "subdirectory consolidates link equity better" advice is mostly outdated for SEO done at this scale

If you later want maximum SEO consolidation under one domain, you can add a Vercel rewrite to your main `frontend/vercel.json` to proxy `/blog/*` to `blog.bluechips.live/*`. Reach out if you want help configuring that — it's a 5-minute job.

---

## Summary of manual steps

- [ ] Create new Vercel project for the `blog/` directory (root directory = `blog`)
- [ ] Add `blog.bluechips.live` domain in Vercel
- [ ] Add the DNS record at your domain registrar (CNAME or A record per Vercel's instructions)
- [ ] Enable Vercel Analytics on the blog project (optional)
- [ ] Run `npm install` in `frontend/` and redeploy main app to pick up `@vercel/analytics` and `@vercel/speed-insights`
- [ ] Enable Analytics + Speed Insights on the main Vercel project
- [ ] (If needed) Update `frontend/vercel.json` with the correct backend URL for `/sitemap.xml`
- [ ] Submit both sitemaps to Google Search Console
- [ ] Submit both sitemaps to Bing Webmaster Tools

Everything else has been done in code.
