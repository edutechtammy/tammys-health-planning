# 🌿 Family Health Planning Hub

A personal health reference and meal planning tool built around genetic and autoimmune conditions shared in our family. Shared here so adult children can access the same information, ask their doctors the right questions, and make informed choices early.

**Live site:** [View on GitHub Pages](https://YOUR-USERNAME.github.io/tammys-health-planning/)
*(Update this link after enabling GitHub Pages — see setup instructions below)*

---

## 📋 What's in Here

| File | Purpose |
|------|---------|
| `index.html` | Landing page with family context and condition summaries |
| `health-reference.html` | Full guidelines for all six conditions — supplements, food rules, labs, interactions |
| `weekly-meal-plan.html` | 7-day whole-foods meal plan (GF, low-oxalate, glucose-friendly, anti-inflammatory) |
| `health-tracker.html` | Daily logging for weight, glucose (×3), Dawn Phenomenon delta, stress, sleep, mood |

---

## 🧬 Conditions Covered

- **MTHFR C677T** — Methylation impairment; requires methylated B-vitamins (methylfolate, methylcobalamin). Both parents carry this variant.
- **Celiac Disease** — Autoimmune gluten intolerance; strict GF diet is non-negotiable. Both parents have Celiac.
- **APOE4 carrier** — Elevated cognitive risk modifier; managed through glucose control, omega-3s, sleep, stress reduction.
- **Pre-diabetes / Dawn Phenomenon** — Morning fasting glucose spike driven by liver cortisol signalling; manageable with diet, timing, and berberine.
- **Kidney Stone (oxalate)** — 9mm calcium oxalate stone; low-oxalate diet, high hydration, magnesium citrate.
- **Klebsiella UTI history** — Gut colonisation risk; targeted probiotic protocol, hydration, low-starch phases.

---

## 👨‍👩‍👧‍👦 For Family Members

**Why this is relevant to you:**

Both parents carry **MTHFR C677T** and **Celiac Disease** — both autosomal conditions with meaningful inheritance probability. Dad carries **APOE3/APOE3** (the neutral form); Mom carries one **APOE4** copy, giving each child a ~50% chance of e3/e4.

**Simplest first step — ask your GP for one blood draw:**
- `tTG-IgA` — Celiac screening *(must be eating gluten at time of test — do NOT go GF before testing)*
- `Homocysteine` — MTHFR impact marker (target < 8 µmol/L)
- `MTHFR genotype` — confirms C677T carrier status
- `Fasting insulin + glucose` — HOMA-IR (insulin resistance / pre-diabetes early warning)

Optional: **APOE genotype** via 23andMe or ask your GP. Knowing in your 30s–40s allows decades of brain-protective habits before risk materialises.

---

## 🖥️ How to Use

This is a static HTML site — no server, no database, no installation required.

**Option 1 — View online via GitHub Pages** (recommended for sharing):
1. Fork or clone this repository
2. Go to Settings → Pages → Source: `main` branch, `/ (root)`
3. GitHub will publish it at `https://YOUR-USERNAME.github.io/tammys-health-planning/`

**Option 2 — Run locally:**
```bash
git clone https://github.com/YOUR-USERNAME/tammys-health-planning.git
cd tammys-health-planning
open index.html   # macOS
# or just double-click index.html in Finder
```

**Option 3 — Download ZIP:**  
GitHub → Code → Download ZIP → open `index.html`

---

## 🔒 Privacy Note

The **Health Tracker** stores all data locally in your browser's `localStorage` — nothing is sent to any server. Each person who opens the tracker on their own device has their own completely separate data.

---

## ⚠️ Disclaimer

This is a personal health reference, not medical advice. All supplement protocols, dietary recommendations, and lab suggestions should be reviewed with your own physician or registered dietitian before acting on them. Individual health situations vary.

---

*Built May 2026 · Maintained with care for family health*
