#!/usr/bin/env python3
"""
Fix: inject the nutr-panel HTML into recipes where CSS landed but the panel div did not.
Inserts immediately before the <!-- INGREDIENTS --> comment (or equivalent anchors).
"""
import os, re

BASE = "/Volumes/LaCie 2/00_Development/01_Repositories/tammys-health-planning"

def nutr_row(name, why, amount, pct_float, color):
    pct = min(pct_float, 100)
    pct_label = round(pct_float)
    extra = " ← exceeds daily target (bar capped)" if pct_float > 100 else ""
    return f"""
      <div class="nutr-row">
        <div class="nutr-label-row">
          <span class="nutr-name">{name} <span class="nutr-why">— {why}</span></span>
          <span class="nutr-amount">{amount}</span>
        </div>
        <div class="nutr-track"><div class="nutr-fill" style="width:{pct:.0f}%;background:{color}"></div></div>
        <div class="nutr-pct">{pct_label}% of daily target{extra}</div>
      </div>"""

def panel(title, serving, rows, note):
    return f"""
  <div class="nutr-panel">
    <div class="nutr-panel-header">📊 Targeted nutrients — per serving {title} <span>{serving}</span></div>
    <div class="nutr-grid">{"".join(rows)}
    </div>
    <div class="nutr-note">⚠️ {note}</div>
  </div>
"""

RECIPES = {
"recipe-afternoon-mct-coffee.html": panel(
    "(1 cup)", "estimates · coffee + MCT + cinnamon",
    [nutr_row("Choline","APOE4 · Fatty Liver","~7 mg",7/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~0.3 g",0.3/80*100,"#16a34a"),
     nutr_row("Folate","MTHFR","~5 µg",5/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","trace",0.5,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","trace",0.5,"#0891b2")],
    "Nutritional value is minimal — this drink is therapeutic, not nutritive. MCT oil provides C8/C10 medium-chain fatty acids that convert to ketones without full hepatic processing. Ceylon cinnamon contributes cinnamaldehyde for glucose response. Neither shows in standard micronutrient databases. Pair with trail mix for zinc."
),
"recipe-bone-broth-soup-base.html": panel(
    "(1 cup / 240ml)", "estimates · chicken-based broth · 9 cups per batch",
    [nutr_row("Choline","APOE4 · Fatty Liver","~15 mg",15/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~4 g",4/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.3 µg",0.3/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~5 µg",5/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1 mg",1/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~5 µg",5/55*100,"#0891b2")],
    "Used as a cooking liquid — nutrient contribution scales every time it replaces water. Primary value is glycine, proline, and collagen precursors (not tracked in standard databases) plus minerals leached from bones during long simmering. Each cup of broth used in millet, sauce, or soup adds to daily totals."
),
"recipe-carrot-celebration-cake.html": panel(
    "(1 slice, 1 of 10–12)", "estimates · GF flours + eggs + carrots + labneh frosting",
    [nutr_row("Choline","APOE4 · Fatty Liver","~50 mg",50/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~4 g",4/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.1 µg",0.1/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~18 µg",18/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.6 mg",0.6/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~12 µg",12/55*100,"#0891b2")],
    "This is a celebration food — nutrient density is secondary to being a safe treat. The moderate Selenium from GF flours and the choline from eggs are a useful side effect. Not a primary nutrient source; pair with a protein-rich meal or eat after a high-choline day."
),
"recipe-cassava-crackers.html": panel(
    "(~5 crackers / 20g)", "estimates · cassava flour + EVOO + rosemary",
    [nutr_row("Choline","APOE4 · Fatty Liver","~2 mg",2/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~0.5 g",0.5/80*100,"#16a34a"),
     nutr_row("Folate","MTHFR","~5 µg",5/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.1 mg",0.1/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid","trace",0.5,"#0891b2")],
    "Cassava flour is low in micronutrients — this cracker is a GF vehicle for high-nutrient toppings (labneh, guacamole, smoked salmon, hard-boiled eggs). The resistant starch in cassava feeds gut bacteria. Load the toppings, not the base — what you put on it transforms the nutrient profile."
),
"recipe-chop-chop-salad.html": panel(
    "(1 main serve, 1 of 2)", "estimates · vegetables + labneh/feta + EVOO",
    [nutr_row("Choline","APOE4 · Fatty Liver","~42 mg",42/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~8 g",8/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.5 µg",0.5/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~107 µg",107/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.2 mg",1.2/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~4 µg",4/55*100,"#0891b2")],
    "Strong folate source — parsley (30g) alone contributes ~75µg DFE, and the bell peppers add more. B12 comes from labneh or feta. Add a protein side (hard-boiled eggs, chicken, sardines) to make this a nutritionally complete main. Best eaten same-day after dressing."
),
"recipe-ginger-carrot-slaw.html": panel(
    "(1 serve, 1 of 4)", "estimates · carrots + apple + bell pepper + ginger",
    [nutr_row("Choline","APOE4","~13 mg",13/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~1.3 g",1.3/80*100,"#16a34a"),
     nutr_row("Folate","MTHFR","~24 µg",24/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.3 mg",0.3/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid","trace",0.5,"#0891b2")],
    "Light nutrient profile — valued as a raw enzyme-rich side, not a primary nutrient source. Beta-carotene from carrots and vitamin C from peppers are high but not tracked here. Ginger's anti-inflammatory gingerols don't appear in standard databases. Serve alongside protein-rich dishes."
),
"recipe-ginger-garlic-chicken-stirfry.html": panel(
    "(1 serve, 1 of 2)", "estimates · 190g chicken breast + mushrooms + cabbage",
    [nutr_row("Choline","APOE4 · Fatty Liver","~111 mg",111/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~43 g",43/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.3 µg",0.3/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~50 µg",50/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~2 mg",2/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~45 µg",45/55*100,"#0891b2")],
    "One of the highest-selenium meals in the collection, driven by the chicken breast. Mushrooms contribute meaningful zinc — cremini/shiitake are the best mushroom zinc sources. High protein density makes this an excellent Dawn Phenomenon-stabilising dinner. The folate comes primarily from the cabbage."
),
"recipe-ginger-garlic-millet-bowl.html": panel(
    "(1 serve, 1 of 2 — with chicken)", "estimates · millet + chicken breast + broccoli",
    [nutr_row("Choline","APOE4 · Fatty Liver","~68 mg",68/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~26 g",26/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.2 µg",0.2/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~55 µg",55/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.8 mg",1.8/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~23 µg",23/55*100,"#0891b2")],
    "Millet is the best grain source of zinc and magnesium in this collection. Folate comes largely from the broccoli topping — don't skip it. Values assume chicken breast protein; sardines as the protein choice would add significant B12 (~4µg) and Omega-3 — the bowl adapts well."
),
"recipe-golden-paste-chicken-thighs.html": panel(
    "(1 serve, 1 of 2 — 2 thighs)", "estimates · ~200g chicken thigh meat + golden paste",
    [nutr_row("Choline","APOE4 · Fatty Liver","~100 mg",100/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~35 g",35/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.4 µg",0.4/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~8 µg",8/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~2 mg",2/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~32 µg",32/55*100,"#0891b2")],
    "Thighs are higher in choline than breast (~100mg vs ~90mg per serve). The turmeric/black pepper combination is not reflected here but is the primary therapeutic driver — curcumin bioavailability is nearly zero without piperine; the two must be used together. Pair with a high-folate vegetable side."
),
"recipe-golden-paste-salmon.html": panel(
    "(1 serve, 1 of 2 — ~165g fillet)", "estimates · salmon + golden paste + EVOO",
    [nutr_row("Choline","APOE4 · Fatty Liver","~130 mg",130/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~34 g",34/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~3.8 µg",3.8/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~28 µg",28/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~0.7 mg",0.7/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~50 µg",50/55*100,"#0891b2"),
     nutr_row("Omega-3 (EPA+DHA)","APOE4 · cardiovascular · anti-inflammatory","~3000 mg",3000/1000*100,"#059669")],
    "Highest B12 source in the collection — one serving exceeds the daily target (bar capped at 100%). Omega-3 EPA+DHA of ~3000mg is 3× the general daily target; APOE4 specifically benefits from high EPA+DHA intake. The turmeric golden paste enhances the anti-inflammatory synergy between omega-3 and curcumin."
),
"recipe-guacamole.html": panel(
    "(1 serve, 1 of 2 — 1 avocado)", "estimates · avocado + garlic + lemon",
    [nutr_row("Choline","APOE4","~25 mg",25/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~2 g",2/80*100,"#16a34a"),
     nutr_row("Folate","MTHFR","~45 µg",45/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.6 mg",0.6/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid","trace",1,"#0891b2")],
    "Avocado's primary value is monounsaturated fat (oleic acid, same as EVOO) and potassium (~485mg per avocado) — neither is tracked here. The folate at 11% from a condiment-scale serve is noteworthy. Pair with crackers + protein (smoked salmon, hard-boiled eggs) for a complete snack."
),
"recipe-hard-boiled-eggs.html": panel(
    "(1 egg)", "estimates · 1 large egg · multiply for actual serve",
    [nutr_row("Choline","APOE4 · Fatty Liver","~147 mg",147/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~6.3 g",6.3/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.6 µg",0.6/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~22 µg",22/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~0.5 mg",0.5/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~15 µg",15/55*100,"#0891b2")],
    "Gram for gram, eggs are the most efficient choline source in the collection. One egg covers 35% of the daily choline target — 2 eggs covers 69%. All the choline is in the yolk; do not discard. A daily hard-boiled egg kept in the fridge is the lowest-effort insurance against a choline shortfall day."
),
"recipe-herb-crusted-chicken.html": panel(
    "(1 serve, 1 of 2 — ~190g breast)", "estimates · chicken breast + parsley + millet crumb",
    [nutr_row("Choline","APOE4 · Fatty Liver","~130 mg",130/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~42 g",42/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.3 µg",0.3/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~41 µg",41/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.7 mg",1.7/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~42 µg",42/55*100,"#0891b2")],
    "Parsley is the folate booster here — 3 tbsp fresh flat-leaf parsley per serve contributes ~35µg DFE, which is unusually high for an herb quantity. This is why the recipe specifies do not skip the parsley. Chicken breast is a clean high-selenium, high-choline protein."
),
"recipe-homemade-mozzarella.html": panel(
    "(~62g, 1 of 4 serves from 250g)", "estimates · from 1 litre part-skim pasteurised milk",
    [nutr_row("Choline","APOE4","~40 mg",40/425*100,"#f59e0b"),
     nutr_row("Protein","satiety · glucose stability","~8 g",8/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~1.1 µg",1.1/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~12 µg",12/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1 mg",1/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~5 µg",5/55*100,"#0891b2")],
    "Calcium is the headline nutrient here (~300mg per serve = 30% of daily target) but is not shown on this panel. Homemade from part-skim milk gives lower sodium than store-bought. B12 at 46% per serve makes this a meaningful MTHFR support ingredient, used across multiple recipes in the collection."
),
"recipe-kale-fruit-salad.html": panel(
    "(1 serve, 1 of 4)", "estimates · kale + blueberries + mozzarella + walnuts",
    [nutr_row("Choline","APOE4 · Fatty Liver","~32 mg",32/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~9 g",9/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.4 µg",0.4/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~48 µg",48/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1 mg",1/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~4 µg",4/55*100,"#0891b2")],
    "Kale is the folate anchor — 50g raw kale provides ~38µg DFE. Walnuts add ALA omega-3 (~1.3g per serve). Mozzarella brings B12 and calcium. Massaging kale with lemon and salt before assembling substantially improves palatability and mildly improves iron absorption from the greens."
),
"recipe-kefir-marinated-chicken.html": panel(
    "(1 serve, 1 of 2 — ~190g breast)", "estimates · chicken breast + kefir marinade",
    [nutr_row("Choline","APOE4 · Fatty Liver","~95 mg",95/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~41 g",41/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.5 µg",0.5/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~6 µg",6/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.2 mg",1.2/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~40 µg",40/55*100,"#0891b2")],
    "Nutritionally nearly identical to other chicken breast recipes. The kefir marinade tenderises the protein via lactic acid — it's a texture technique, not a nutrient addition. Probiotic benefit from the kefir is destroyed by heat; the live culture value is in uncooked kefir consumption. Pair with a high-folate vegetable side."
),
"recipe-kefir-overnight-porridge.html": panel(
    "(1 serving)", "estimates · millet + kefir + blueberries",
    [nutr_row("Choline","APOE4 · Fatty Liver","~35 mg",35/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~7 g",7/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.9 µg",0.9/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~30 µg",30/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.6 mg",1.6/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~4.5 µg",4.5/55*100,"#0891b2")],
    "B12 comes entirely from the kefir — this is one of the few breakfast options in the collection with meaningful B12 without eggs or meat. Millet provides zinc and magnesium (not tracked). Cold-soaking overnight in kefir partially ferments the grain, reducing phytic acid and improving mineral bioavailability above raw millet values."
),
"recipe-labneh-berry-parfait.html": panel(
    "(1 serve, 1 of 2)", "estimates · 100g labneh + blueberries + walnuts",
    [nutr_row("Choline","APOE4","~35 mg",35/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~7.5 g",7.5/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.4 µg",0.4/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~24 µg",24/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1 mg",1/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~4 µg",4/55*100,"#0891b2")],
    "Walnuts add ALA omega-3 (~1.7g per serve). Blueberries are low in standard micronutrients but are the primary source of anthocyanins — directly relevant to APOE4 neuroprotection and insulin signalling, but not captured in any nutrient database. The labneh provides calcium (~200mg per 100g)."
),
"recipe-labneh-yogurt-cheese.html": panel(
    "(~2 tbsp / 25g)", "estimates · strained Sugar Shift yogurt",
    [nutr_row("Choline","APOE4","~5 mg",5/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~2 g",2/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.1 µg",0.1/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~2 µg",2/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.15 mg",0.15/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid","trace",1,"#0891b2")],
    "Used as a condiment and spread across the collection — nutrient contribution per 2 tbsp is small but consistent. Primary value is live probiotic cultures (if base yogurt is not heated) and as a low-sodium, protein-dense replacement for commercial cream cheese or sour cream in sauces and dips."
),
"recipe-lemon-blueberry-cheesecake.html": panel(
    "(1 slice, 1 of 10–12)", "estimates · labneh filling + eggs + sorghum crust",
    [nutr_row("Choline","APOE4 · Fatty Liver","~57 mg",57/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~11 g",11/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.43 µg",0.43/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~13 µg",13/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.5 mg",0.5/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~8 µg",8/55*100,"#0891b2")],
    "For a dessert, the protein content (11g from labneh + eggs) is unusually high — significantly better than conventional cheesecake. The blueberry topping adds anthocyanins which don't appear in nutrient databases. Lower carb per slice than the celebration cakes because the filling contains no flour."
),
"recipe-lemon-garlic-pan-chicken.html": panel(
    "(1 serve, 1 of 2 — ~190g breast)", "estimates · chicken breast + bone broth sauce",
    [nutr_row("Choline","APOE4 · Fatty Liver","~92 mg",92/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~42 g",42/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.3 µg",0.3/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~6 µg",6/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.7 mg",1.7/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~42 µg",42/55*100,"#0891b2")],
    "Standard chicken breast nutrient profile. The bone broth deglazing adds a small collagen/glycine contribution not reflected here. Folate is low — chicken breast is not a folate source. Pair with asparagus, broccoli, or kale to fill the folate gap for the day."
),
"recipe-olive-cheese-bread.html": panel(
    "(1 slice, 1 of 8)", "estimates · millet/sorghum flour + 3 eggs + feta + kefir",
    [nutr_row("Choline","APOE4 · Fatty Liver","~58 mg",58/425*100,"#f59e0b"),
     nutr_row("Protein","satiety · glucose stability","~6 g",6/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.65 µg",0.65/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~13 µg",13/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~0.7 mg",0.7/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~9.5 µg",9.5/55*100,"#0891b2")],
    "For a baked bread, the B12 and choline are unusually strong — driven by 3 eggs and feta together. Kalamata olives add polyphenols (hydroxytyrosol) not in nutrient databases. Best consumed same-day or toasted from freezer. Two slices with eggs would push choline and B12 toward strong daily coverage."
),
"recipe-pumpkin-celebration-cake.html": panel(
    "(1 slice, 1 of 10–12)", "estimates · GF flours + pumpkin purée + eggs",
    [nutr_row("Choline","APOE4 · Fatty Liver","~52 mg",52/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~5 g",5/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.3 µg",0.3/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~13 µg",13/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.6 mg",0.6/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~10 µg",10/55*100,"#0891b2")],
    "Pumpkin purée adds beta-carotene and potassium not tracked here. Like the carrot cake — a celebration food, not a primary nutrient vehicle. The egg content gives this cake a better choline profile than conventional sponge cake. Pair with a high-protein meal on cake days."
),
"recipe-purple-sauerkraut.html": panel(
    "(~2 tbsp / 30g)", "estimates · fermented purple cabbage",
    [nutr_row("Choline","APOE4","~5 mg",5/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~0.8 g",0.8/80*100,"#16a34a"),
     nutr_row("Folate","MTHFR","~19 µg",19/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.1 mg",0.1/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid","trace",0.5,"#0891b2")],
    "Primary value is probiotic Lactobacillus bacteria and vitamin K2 — neither tracked in standard nutrient databases. Folate from fermented purple cabbage is noteworthy at condiment scale. Eat consistently as a side to accumulate benefit. Fermentation increases bioavailability of remaining nutrients compared to raw cabbage."
),
"recipe-rice-paper-bagels.html": panel(
    "(1 bagel, 1 of 4)", "estimates · 4 rice paper sheets + herbs",
    [nutr_row("Choline","APOE4","~2 mg",2/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~0.8 g",0.8/80*100,"#16a34a"),
     nutr_row("Folate","MTHFR","~1 µg",1/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.05 mg",0.05/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid","~1 µg",1/55*100,"#0891b2")],
    "Rice paper is a near-zero-nutrient vehicle — its value is a low-GI starch form, GF safety, and as a neutral base for nutrient-dense toppings. What matters here is what you put on it: labneh + smoked salmon + capers would push choline past 150mg, B12 past 3µg, and Omega-3 past 2000mg for this snack alone."
),
"recipe-rice-paper-potstickers.html": panel(
    "(4 potstickers, 1 of 4 serves)", "estimates · 75g shrimp + rice paper + cabbage",
    [nutr_row("Choline","APOE4 · Fatty Liver","~64 mg",64/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~17 g",17/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~1.1 µg",1.1/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~19 µg",19/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1 mg",1/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~32 µg",32/55*100,"#0891b2")],
    "Shrimp is an outstanding selenium and B12 source — better per gram than most land-based proteins. Four potstickers is a side serve; eight makes a protein-complete main with 34g protein. Iodine from shrimp (not tracked) is also meaningful for thyroid function."
),
"recipe-rice-paper-pouches.html": panel(
    "(4 pouches, 1 of 3 serves)", "estimates · 167g ground turkey + rice paper + napa cabbage",
    [nutr_row("Choline","APOE4 · Fatty Liver","~87 mg",87/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~39 g",39/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.6 µg",0.6/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~28 µg",28/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~3.5 mg",3.5/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~26 µg",26/55*100,"#0891b2")],
    "Ground turkey provides 3x the zinc of chicken breast at equivalent weight — this is the strongest zinc source among the poultry recipes. Zinc at 44% of daily target makes these pouches useful on days when immune or wound healing support is needed. Pair with a high-folate side for a complete meal."
),
"recipe-roasted-artichoke.html": panel(
    "(1 whole artichoke)", "estimates · globe artichoke + EVOO + garlic",
    [nutr_row("Choline","APOE4 · Fatty Liver","~54 mg",54/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~4 g",4/80*100,"#16a34a"),
     nutr_row("Folate","MTHFR","~68 µg",68/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","~0.5 mg",0.5/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid","trace",0.5,"#0891b2")],
    "Artichoke is one of the best plant sources of folate in this collection and the primary prebiotic fibre food (inulin). Inulin feeds the Lactobacillus and Bifidobacterium from kefir and sauerkraut — eating artichoke alongside fermented foods compounds the probiotic benefit. Cynarin in artichoke supports bile production and liver function."
),
"recipe-roasted-asparagus.html": panel(
    "(1 serve, 1 of 2 — ~200g spears)", "estimates · asparagus + Parmesan + capers",
    [nutr_row("Choline","APOE4 · Fatty Liver","~36 mg",36/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~7.5 g",7.5/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.4 µg",0.4/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~88 µg",88/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.6 mg",1.6/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~9 µg",9/55*100,"#0891b2")],
    "Asparagus has the highest folate of any vegetable in this collection — 22% of daily target per serve. Combined with the Parmesan's B12, this makes the strongest single MTHFR support side dish. Capers add quercetin and a small B-vitamin contribution. An essential side for any day where B12 or folate needs coverage."
),
"recipe-roasted-broccoli-cheese-sauce.html": panel(
    "(1 serve, 1 of 2)", "estimates · 250g broccoli + mozzarella + bone broth sauce",
    [nutr_row("Choline","APOE4 · Fatty Liver","~71 mg",71/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~19 g",19/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.6 µg",0.6/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~100 µg",100/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.5 mg",1.5/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~9 µg",9/55*100,"#0891b2")],
    "Broccoli is the folate and choline anchor — 250g covers 25% of daily folate alone. The 40-minute resting protocol before cooking maximises sulforaphane yield (myrosinase activation); this is not captured in any nutrient database but is the primary therapeutic mechanism of the dish. Do not skip the rest step."
),
"recipe-roasted-zucchini-parmesan.html": panel(
    "(1 side serve, 1 of 2)", "estimates · 200g zucchini + Parmesan",
    [nutr_row("Choline","APOE4","~14 mg",14/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~7.8 g",7.8/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.5 µg",0.5/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~28 µg",28/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.2 mg",1.2/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~5.4 µg",5.4/55*100,"#0891b2")],
    "Parmesan punches well above its weight for B12 and zinc relative to the small quantity used. Zucchini is a low-oxalate, low-GI vehicle that adds hydration and some folate. Good as a low-carb side to anchor a meal when the protein component (chicken, salmon) is the primary nutrient driver."
),
"recipe-shakshuka.html": panel(
    "(1 serve, 1 of 2 — 2 eggs)", "estimates · 2 eggs + tomatoes + feta + bell pepper",
    [nutr_row("Choline","APOE4 · Fatty Liver","~329 mg",329/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~24.5 g",24.5/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~2.2 µg",2.2/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~89 µg",89/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~3.4 mg",3.4/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~35 µg",35/55*100,"#0891b2")],
    "Shakshuka is the highest-choline recipe in the collection — 2 eggs provide 294mg choline alone. This is the go-to rescue meal when a daily choline shortfall is apparent. B12 at 92% means this single meal nearly covers the full daily requirement. Eat this whenever the meatloaf or salmon aren't on the menu."
),
"recipe-salmon-rice-paper-rolls.html": panel(
    "(4 rolls, 1 of 2 serves)", "estimates · 130g salmon + avocado + carrots + cabbage + rice paper",
    [nutr_row("Choline","APOE4 · Fatty Liver","~122 mg",122/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~30 g",30/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~3.1 µg",3.1/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~87 µg",87/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~0.85 mg",0.85/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~40 µg",40/55*100,"#0891b2"),
     nutr_row("Omega-3 (EPA+DHA)","APOE4 · cardiovascular · anti-inflammatory","~2500 mg",2500/1000*100,"#059669")],
    "Second-highest B12 source in the collection after golden paste salmon — bar capped at 100% as a single serve exceeds the daily target. The avocado+carrots+cabbage combination makes this one of the highest-folate protein mains. The CGM test confirmed a strong glucose profile."
),
"recipe-slow-braised-pork-apple.html": panel(
    "(1 serve, 1 of 4 — ~300g pork shoulder)", "estimates · bone-in pork shoulder + fennel + apple",
    [nutr_row("Choline","APOE4 · Fatty Liver","~127 mg",127/425*100,"#f59e0b"),
     nutr_row("Protein","glucose stability","~38 g",38/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~1.3 µg",1.3/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~25 µg",25/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~4 mg",4/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~32 µg",32/55*100,"#0891b2")],
    "Pork is the highest-zinc meat in the collection — 4mg per serve (50% of daily target) is the strongest single-meal zinc source. Important for days when immune or wound healing support is needed. Collagen from the bone-in shoulder is not tracked but is significant after slow braising. Fennel adds prebiotic inulin."
),
"recipe-sugar-shift-yogurt.html": panel(
    "(1 cup / ~240ml)", "estimates · whole milk + cream + probiotic cultures",
    [nutr_row("Choline","APOE4","~40 mg",40/425*100,"#f59e0b"),
     nutr_row("Protein","satiety · glucose stability","~6 g",6/80*100,"#16a34a"),
     nutr_row("B12","MTHFR","~0.75 µg",0.75/2.4*100,"#7c3aed"),
     nutr_row("Folate","MTHFR","~8 µg",8/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~0.9 mg",0.9/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~4 µg",4/55*100,"#0891b2")],
    "The probiotic value of this yogurt is not captured in any nutrient database — it is the primary therapeutic driver. The Sugar Shift strains specifically target glucose metabolism. Nutritionally similar to full-fat Greek yogurt; the cream addition increases fat density for longer satiety and slower glucose response."
),
"recipe-therapeutic-teas.html": panel(
    "(1 cup)", "estimates · brewed herb/green tea",
    [nutr_row("Choline","APOE4","~1 mg",1/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~0 g",0,"#16a34a"),
     nutr_row("Folate","MTHFR","~5 µg",5/400*100,"#db2777"),
     nutr_row("Zinc","metabolic","trace",0.5,"#0284c7"),
     nutr_row("Selenium","thyroid","trace",0.5,"#0891b2")],
    "Tea nutrients are negligible — the entire therapeutic value is in phytochemicals that do not appear in standard USDA data. Chamomile: apigenin (GABA-A receptor agonist). Ginger: gingerols and shogaols (anti-inflammatory, COX inhibition). Green tea: EGCG (Nrf2 activation, APOE4-targeted). Nettle: quercetin and silica."
),
"recipe-trail-mix.html": panel(
    "(~30g serve, 1 of 10)", "estimates · pumpkin seeds + walnuts + sunflower seeds + dark chocolate",
    [nutr_row("Choline","APOE4","~21 mg",21/425*100,"#f59e0b"),
     nutr_row("Protein","satiety","~4.3 g",4.3/80*100,"#16a34a"),
     nutr_row("Folate","MTHFR","~11 µg",11/400*100,"#db2777"),
     nutr_row("Zinc","metabolic · immune","~1.7 mg",1.7/8*100,"#0284c7"),
     nutr_row("Selenium","thyroid · antioxidant","~3.5 µg",3.5/55*100,"#0891b2")],
    "Zinc from pumpkin seeds is the standout — the most consistent daily zinc contributor in the collection for a snack-sized portion. Walnuts provide ALA omega-3 (~1.4g per serve). Dark chocolate adds magnesium (~13mg) and flavanols. This is a reliable daily micro-dose of zinc, magnesium, and plant omega-3."
),
}

ANCHORS = [
    "<!-- INGREDIENTS -->",
    "<!-- MAIN LAYOUT -->",
    "<!-- RECIPE LAYOUT -->",
    "<!-- METHOD -->",
    "<!-- INGREDIENTS + STEPS -->",
    "<!-- INGREDIENTS + METHOD -->",
    "<!-- INGREDIENT SPOTLIGHT -->",
    "<!-- RECIPE -->",
    "<!-- GOLDEN PASTE vs SALMON COMPARISON -->",
    "<!-- CRUST COMPARISON -->",
    "<!-- WHAT YOU NEED CALLOUT -->",
    "<!-- HOW KEFIR MARINADE WORKS -->",
    "<!-- STRAINING TIME REFERENCE -->",
    "<!-- OXALATE COMPARISON TABLE -->",
    "<!-- QUICK REFERENCE TABLE -->",
]

modified = []
warnings = []
for fname, panel_html in RECIPES.items():
    fpath = os.path.join(BASE, fname)
    if not os.path.exists(fpath):
        warnings.append(f"NOT FOUND: {fname}")
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        html = f.read()
    # Check if panel div is already in body (not just CSS)
    # Count actual div occurrences after </style>
    body_start = html.find("</style>")
    body_part = html[body_start:] if body_start > 0 else html
    if '<div class="nutr-panel">' in body_part:
        print(f"SKIP (panel already in body): {fname}")
        continue
    inserted = False
    for anchor in ANCHORS:
        if anchor in html:
            html = html.replace(anchor, panel_html + "\n  " + anchor, 1)
            inserted = True
            break
    if not inserted:
        warnings.append(f"NO ANCHOR FOUND: {fname}")
        continue
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(html)
    modified.append(fname)
    print(f"OK: {fname}")

print(f"\nModified: {len(modified)}")
if warnings:
    print("WARNINGS:")
    for w in warnings:
        print(" ", w)
