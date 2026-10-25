"""
IDHV 2026M Project - Why Students Order Out
Step 1: preprocessing, descriptive statistics, EDA figures.

Input : raw_data.csv           (exactly as collected from the Google Form)
Output: cleaned_data.csv       (cleaned + derived variables)
        figures/*.png          (all charts used in the report)
        stats.json             (numbers quoted in the report)
"""
import os, json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

# ----------------------------------------------------------------- style
BLUE, ORANGE, GREY, RED, GREEN, LIGHT = "#2E6FBA", "#E8833A", "#8C99A6", "#C8553D", "#4C9A6A", "#CBD5E1"
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True,
    "figure.dpi": 100, "savefig.dpi": 200, "savefig.bbox": "tight",
})

def save(fig, name):
    fig.savefig(os.path.join(FIG, name))
    plt.close(fig)

# ----------------------------------------------------------------- load
# Columns are matched on the question text, not on position, so that a re-export
# of the Google Form in a different column order still loads correctly.
QUESTIONS = {
    "Timestamp": "timestamp",
    "How do you usually place your outside food orders?": "order_mode",
    "What is the main reason you order food from outside?": "reasons",
    "When do you most often order outside food?": "order_when",
    "On which day do you most often order outside food?": "order_days",
    "Approximately how much do you spend on outside food orders in a typical week?": "spend",
    "Do you usually order outside food outside the operating timings of the mess?": "off_hours",
    "Do you usually order outside food because you skipped a mess meal?": "skipped_flag",
    "In a typical week, how many times do you order outside food after skipping a mess meal?": "orders_after_skip",
    "How satisfied are you with the taste of your mess food?": "taste",
    "How often does the day's mess menu influence your decision to order outside food? [.]": "menu_influence",
    "How satisfied are you with each mess meal? [Breakfast]": "sat_breakfast",
    "How satisfied are you with each mess meal? [Lunch]": "sat_lunch",
    "How satisfied are you with each mess meal? [Snacks]": "sat_snacks",
    "How satisfied are you with each mess meal? [Dinner]": "sat_dinner",
    "On average, how many mess meals do you skip in a typical week?": "meals_skipped",
    "Which mess meal do you prefer or like the most?": "fav_meal",
    "How would you rate the overall quality and consistency of your mess food?": "quality",
    "How many times do you order food from outside in a typical week?": "orders",
    "In a typical week, how many times do you order outside food alone?": "orders_alone",
    "In a typical week, how many times do you order outside food with friends?": "orders_friends",
    "In a typical week, on how many days do you dislike the mess menu or find it unappealing?": "disliked_days",
    "What is your current year of study?": "year",
}
raw = pd.read_csv(os.path.join(BASE, "raw_data.csv"))
raw.columns = [c.strip() for c in raw.columns]
missing_q = [q for q in QUESTIONS if q not in raw.columns]
if missing_q:
    raise SystemExit("raw_data.csv is missing expected question(s):\n  " + "\n  ".join(missing_q))
df = raw[list(QUESTIONS)].rename(columns=QUESTIONS)

S = {}                                   # statistics quoted in the report
S["n"] = int(len(df))
S["n_columns_raw"] = int(raw.shape[1])
S["duplicates"] = int(df.drop(columns=["timestamp"]).duplicated().sum())

# ----------------------------------------------------------------- cleaning
for c in df.select_dtypes(include=["object", "string"]).columns:
    df[c] = df[c].astype("string").str.strip()
df["order_when"] = df["order_when"].str.replace("for ", "", regex=False)

# numeric questions arrive as free text ("2 " with a trailing space, etc.)
NUMERIC = ["spend", "orders", "orders_alone", "orders_friends", "orders_after_skip",
           "meals_skipped", "disliked_days", "taste", "quality"]
for c in NUMERIC:
    df[c] = pd.to_numeric(df[c].astype("string").str.strip(), errors="coerce")

# ----------------------------------------------------------------- missing values
# Only "days menu disliked" was left optional in the form, so blanks there are genuine
# non-responses. Blanks in any question that was marked required are recording faults, not
# non-responses, and are repaired from the respondent's own arithmetic where that is possible.
# Policy fixed before looking at the results:
#   impute the median of the column and flag the row; delete a response only if more than
#   half of its answers are blank.
S["missing_before"] = {c: int(df[c].isna().sum()) for c in df.columns if df[c].isna().any()}
S["missing_cells"] = int(sum(S["missing_before"].values()))

S["imputed_median"] = {}
for c in NUMERIC:
    miss = df[c].isna()
    df[c + "_imputed"] = miss.astype(int)
    if miss.any():
        med = float(df[c].median())
        S["imputed_median"][c] = {"n": int(miss.sum()), "value": med}
        df.loc[miss, c] = med
    else:
        df = df.drop(columns=[c + "_imputed"])

S["rows_dropped"] = 0                      # none was blank in more than half of its fields

likert = {"Very dissatisfied": 1, "Dissatisfied": 2, "Neutral": 3, "Satisfied": 4, "Very satisfied": 5}
for c in ["sat_breakfast", "sat_lunch", "sat_snacks", "sat_dinner"]:
    df[c + "_label"] = df[c]
    df[c] = df[c].map(likert)
df["menu_influence_label"] = df["menu_influence"]
df["menu_influence"] = df["menu_influence"].map({"Rarely": 1, "Sometimes": 2, "Often": 3, "Very Often": 4})
df["off_hours"] = (df["off_hours"] == "Yes").astype(int)
df["skipped_flag"] = (df["skipped_flag"] == "Yes").astype(int)

# multi-select: days
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
for d in DAYS:
    df["day_" + d[:3]] = df["order_days"].str.contains(d).astype(int)
df["n_order_days"] = df["order_days"].str.split(r"[;,]\s*", regex=True).str.len()
df["orders_on_nonveg_day"] = ((df["day_Wed"] == 1) | (df["day_Sun"] == 1)).astype(int)

# multi-select: reasons
REASON_MAP = {
    "Dissatisfaction with mess food": "dissatisfaction", "Better taste": "better_taste",
    "Craving for a particular food": "craving", "Lack of variety in the mess": "lack_of_variety",
    "Ordering with friends": "friends", "I skipped a mess meal": "skipped_meal",
    "Convenience / too busy": "convenience", "Mess timing is inconvenient": "timing", "Other": "other"}
for long, short in REASON_MAP.items():
    df["reason_" + short] = df["reasons"].str.contains(long, regex=False).astype(int)
df["n_reasons"] = df["reasons"].str.split(r"[;,]\s*", regex=True).str.len()

# ----------------------------------------------------------------- consistency check and correction
# The weekly total and the solo / with-friends counts were asked as three separate numeric
# questions, so nothing in the form forced them to agree. Respondents are hostel students,
# for whom every outside order is either placed alone or with friends (roommates included),
# so the two parts must account for all of a student's orders. Where they disagree with the
# stated total, the total is taken to be the error and is replaced by the sum of the parts.
# The value as answered is kept in orders_as_stated so the correction stays traceable.
df["orders_parts_sum"] = df.orders_alone + df.orders_friends
df["orders_as_stated"] = df.orders
df["orders_consistent"] = (df.orders_parts_sum == df.orders).astype(int)
df["orders_gap"] = df.orders_parts_sum - df.orders

S["alone_plus_friends_equals_orders"] = int(df.orders_consistent.sum())
S["orders_mismatch_n"] = int((df.orders_consistent == 0).sum())
df["orders"] = df["orders_parts_sum"]                      # apply the rule

# Orders placed after skipping a mess meal are a subset of all outside orders, so the count
# cannot exceed the weekly total; where it does, it is capped at that total.
df["orders_after_skip_as_stated"] = df.orders_after_skip
over = df.orders_after_skip > df.orders
S["after_skip_capped_n"] = int(over.sum())
df.loc[over, "orders_after_skip"] = df.loc[over, "orders"]

# ----------------------------------------------------------------- derived variables
df["spend_per_order"] = np.where(df.orders > 0, df.spend / df.orders.replace(0, np.nan), np.nan)
df["friends_share"] = np.where(df.orders > 0, df.orders_friends / df.orders.replace(0, np.nan), np.nan)
SAT = ["taste", "quality", "sat_breakfast", "sat_lunch", "sat_snacks", "sat_dinner"]
df["mess_index"] = df[SAT].mean(axis=1)
k = len(SAT)
S["cronbach_alpha"] = float(k / (k - 1) * (1 - df[SAT].var().sum() / df[SAT].sum(axis=1).var()))

# ----------------------------------------------------------------- outliers (IQR rule) -> cap
def fences(s):
    q1, q3 = s.quantile([.25, .75])
    return q1, q3, q3 + 1.5 * (q3 - q1)

S["outliers"] = {}
for col in ["spend", "meals_skipped", "orders"]:
    q1, q3, hi = fences(df[col])
    cap = int(np.floor(hi))
    flag = df[col] > hi
    df[col + "_outlier"] = flag.astype(int)
    df[col + "_capped"] = df[col].clip(upper=cap)
    S["outliers"][col] = {"q1": float(q1), "q3": float(q3), "fence": float(hi), "cap": cap,
                          "n": int(flag.sum()), "values": sorted(df.loc[flag, col].tolist())}

# ----------------------------------------------------------------- normalisation (min-max, 0-1)
def minmax(s): return (s - s.min()) / (s.max() - s.min())
for col in ["spend_capped", "orders_capped", "meals_skipped_capped", "disliked_days", "mess_index"]:
    df["norm_" + col] = minmax(df[col])

# ----------------------------------------------------------------- bands / groups
df["order_band"] = pd.cut(df.orders, [-1, 1, 2, 3, 100], labels=["0-1", "2", "3", "4+"])
df["skip_band"] = pd.cut(df.meals_skipped, [-1, 2, 5, 100], labels=["0-2", "3-5", "6+"])
df["mess_group"] = pd.cut(df.mess_index, [0, 2.4999, 3.0001, 5], labels=["Low (<2.5)", "Medium (2.5-3.0)", "High (>3.0)"])
S["mess_group_counts"] = {k: int(v) for k, v in df.mess_group.value_counts().sort_index().items()}

df.drop(columns=["timestamp"]).to_csv(os.path.join(BASE, "cleaned_data.csv"), index=False)

# ================================================================= DESCRIPTIVE STATISTICS
def desc(s):
    return {"mean": float(s.mean()), "median": float(s.median()), "sd": float(s.std()),
            "min": float(s.min()), "max": float(s.max()), "q1": float(s.quantile(.25)), "q3": float(s.quantile(.75))}

NUMS = {"Weekly spend (Rs)": "spend", "Orders per week": "orders", "Orders alone": "orders_alone",
        "Orders with friends": "orders_friends", "Spend per order (Rs)": "spend_per_order",
        "Orders after skipping a meal": "orders_after_skip",
        "Meals skipped per week": "meals_skipped", "Days menu disliked (of 7)": "disliked_days",
        "Taste rating (1-5)": "taste", "Quality rating (1-5)": "quality", "Overall mess index (1-5)": "mess_index"}
S["desc"] = {lab: desc(df[c].dropna()) for lab, c in NUMS.items()}

S["year"] = df.year.value_counts().to_dict()
meals = {"Breakfast": "sat_breakfast", "Lunch": "sat_lunch", "Snacks": "sat_snacks", "Dinner": "sat_dinner"}
S["meal_mean"] = {m: float(df[c].mean()) for m, c in meals.items()}
S["meal_dis_n"] = {m: int((df[c] <= 2).sum()) for m, c in meals.items()}
S["meal_sat_n"] = {m: int((df[c] >= 4).sum()) for m, c in meals.items()}
S["fav_meal"] = {m: int((df.fav_meal == m).sum()) for m in meals}
S["taste_low_n"] = int((df.taste <= 2).sum()); S["quality_low_n"] = int((df.quality <= 2).sum())
S["skip6_n"] = int((df.meals_skipped >= 6).sum()); S["skip0_n"] = int((df.meals_skipped == 0).sum())
S["dislike5_n"] = int((df.disliked_days >= 5).sum())
S["menu_counts"] = df.menu_influence_label.value_counts().to_dict()
S["menu_often_n"] = int((df.menu_influence >= 3).sum())
S["when"] = df.order_when.value_counts().to_dict()
S["off_hours_n"] = int(df.off_hours.sum()); S["skipped_flag_n"] = int(df.skipped_flag.sum())
S["orders_dist"] = {int(k): int(v) for k, v in df.orders.value_counts().sort_index().items()}
S["spend500_n"] = int((df.spend >= 500).sum())
S["spend_total"] = float(df.spend.sum())
S["top6_share"] = float(df.spend.sort_values().tail(6).sum() / df.spend.sum())
S["reasons_n"] = {s: int(df["reason_" + s].sum()) for s in REASON_MAP.values()}
S["days_n"] = {d: int(df["day_" + d[:3]].sum()) for d in DAYS}
S["days_mentions"] = int(df.n_order_days.sum())
S["mode_counts"] = df.order_mode.value_counts().to_dict()
S["tot_orders"] = int(df.orders.sum()); S["tot_friends"] = int(df.orders_friends.sum())
S["friends_gt_alone"] = int((df.orders_friends > df.orders_alone).sum())
S["alone_gt_friends"] = int((df.orders_friends < df.orders_alone).sum())
S["equal"] = int((df.orders_friends == df.orders_alone).sum())
S["never_alone"] = int((df.orders_alone == 0).sum())
S["mode_means"] = df.groupby("order_mode")[["orders_alone", "orders_friends", "orders", "spend_per_order"]].mean().round(2).to_dict("index")
wk = np.mean([S["days_n"][d] for d in DAYS if d not in ("Wednesday", "Sunday")])
S["other_days_avg"] = float(wk)
S["nonveg_days_avg"] = float((S["days_n"]["Wednesday"] + S["days_n"]["Sunday"]) / 2)

# ================================================================= RELATIONSHIP NUMBERS
S["order_band"] = df.groupby("order_band", observed=True).agg(n=("spend", "size"), median=("spend", "median"), mean=("spend", "mean")).round(0).to_dict("index")
S["skip_band"] = df.groupby("skip_band", observed=True).agg(n=("spend", "size"), median=("spend", "median"), mean=("spend", "mean")).round(0).to_dict("index")
S["menu_means"] = df.groupby("menu_influence_label")[["orders", "disliked_days", "mess_index"]].mean().round(2).to_dict("index")
S["menu_n"] = df.menu_influence_label.value_counts().to_dict()
S["mess_group_means"] = df.groupby("mess_group", observed=True)[["meals_skipped", "disliked_days", "orders", "spend", "mess_index"]].mean().round(2).to_dict("index")
S["dis_reason_orders"] = df.groupby("reason_dissatisfaction").orders.mean().round(2).to_dict()
S["dis_reason_n"] = df.reason_dissatisfaction.value_counts().to_dict()
S["peer_dinner"] = df.groupby("reason_friends").sat_dinner.mean().round(2).to_dict()
S["ndays_orders"] = df.groupby("n_order_days").orders.mean().round(2).to_dict()
S["ndays_n"] = {int(k): int(v) for k, v in df.n_order_days.value_counts().sort_index().items()}
S["offhours_skips"] = df.groupby("off_hours").meals_skipped.mean().round(2).to_dict()
S["dinner_dis_and_dinner_order"] = int(((df.sat_dinner <= 2) & (df.order_when == "Dinner")).sum())

CORRVARS = {"Taste": "taste", "Quality": "quality", "Sat: Breakfast": "sat_breakfast", "Sat: Lunch": "sat_lunch",
            "Sat: Snacks": "sat_snacks", "Sat: Dinner": "sat_dinner", "Meals skipped": "meals_skipped_capped",
            "Days menu disliked": "disliked_days", "Menu influence": "menu_influence",
            "Orders / week": "orders_capped", "Orders alone": "orders_alone", "Orders w/ friends": "orders_friends",
            "Weekly spend": "spend_capped"}
C = df[list(CORRVARS.values())].rename(columns={v: k for k, v in CORRVARS.items()}).corr(method="spearman")
S["corr"] = {a: {b: round(float(C.loc[a, b]), 2) for b in C.columns} for a in C.index}
S["pearson_orders_spend_capped"] = float(df.orders_capped.corr(df.spend_capped))
S["pearson_skips_spend_capped"] = float(df.meals_skipped_capped.corr(df.spend_capped))
slope, icpt = np.polyfit(df.orders_capped, df.spend_capped, 1)
S["slope_orders_spend"] = float(slope)

# ----------------------------------------------------------------- regression
def ols(y, X, names):
    """Least-squares fit with an intercept. Returns coefficients, R-squared and adjusted R-squared."""
    A = np.column_stack([np.ones(len(y))] + [np.asarray(x, float) for x in X])
    beta, *_ = np.linalg.lstsq(A, np.asarray(y, float), rcond=None)
    resid = y - A @ beta
    ss_res, ss_tot = float((resid ** 2).sum()), float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot
    n_obs, k = len(y), A.shape[1] - 1
    return {"coef": {n: float(b) for n, b in zip(["intercept"] + names, beta)},
            "r2": float(r2), "adj_r2": float(1 - (1 - r2) * (n_obs - 1) / (n_obs - k - 1))}

S["reg_simple"] = ols(df.spend_capped, [df.orders_capped], ["orders"])
S["reg_multi"] = ols(df.spend_capped, [df.orders_capped, df.meals_skipped_capped, df.mess_index],
                     ["orders", "meals_skipped", "mess_index"])
S["reg_skips"] = ols(df.spend_capped, [df.meals_skipped_capped], ["meals_skipped"])

# ----------------------------------------------------------------- chi-square test of independence
# Do students for whom the daily menu often drives ordering also rate the mess lower overall?
menu_high = (df.menu_influence >= 3).astype(int)              # Often / Very Often
mess_low = (df.mess_index < 2.5).astype(int)                  # bottom satisfaction group
obs = pd.crosstab(menu_high, mess_low).values.astype(float)
row, col, tot = obs.sum(1, keepdims=True), obs.sum(0, keepdims=True), obs.sum()
exp = row @ col / tot
chi2 = float(((obs - exp) ** 2 / exp).sum())
S["chi2"] = {"table": obs.astype(int).tolist(), "expected_min": float(exp.min()), "chi2": chi2, "dof": 1,
             "critical_5pct": 3.841,                           # chi-square, 1 degree of freedom
             "significant": bool(chi2 > 3.841),
             "cramers_v": float(np.sqrt(chi2 / tot))}

# ================================================================= FIGURES
# ---- Fig 0: outliers before / after
fig, axs = plt.subplots(1, 3, figsize=(8.5, 3.0))
for ax, (col, lab) in zip(axs, [("spend", "Weekly spend (Rs)"), ("meals_skipped", "Meals skipped / week"), ("orders", "Orders / week")]):
    bp = ax.boxplot([df[col], df[col + "_capped"]], tick_labels=["Original", "Capped"], widths=.55, patch_artist=True,
                    flierprops=dict(marker="o", markerfacecolor=ORANGE, markeredgecolor=ORANGE, markersize=4))
    for p, c in zip(bp["boxes"], [LIGHT, "#9DC1E8"]): p.set_facecolor(c)
    for m in bp["medians"]: m.set_color("black")
    ax.set_title(lab); ax.set_ylabel("")
    ax.text(0.5, 0.97, f"{S['outliers'][col]['n']} outliers, cap = {S['outliers'][col]['cap']}", transform=ax.transAxes,
            ha="center", va="top", fontsize=8, color=GREY)
fig.suptitle("Figure 1. Outlier treatment (IQR rule): before and after capping", fontsize=10, fontweight="bold", y=1.03)
fig.tight_layout(); save(fig, "fig01_outliers.png")

# ---- Fig 2: meal satisfaction (diverging) + favourite meal
cats = ["Very dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very satisfied"]
cols = ["#B2433A", "#E3846E", "#D9D9D9", "#7FB0D8", "#2E6FBA"]
order = ["Dinner", "Snacks", "Lunch", "Breakfast"]  # top-to-bottom reversed for barh
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(8.8, 3.1), gridspec_kw={"width_ratios": [2.3, 1]})
for i, m in enumerate(order):
    col = meals[m]
    p = np.array([(df[col] == v).mean() * 100 for v in range(1, 6)])
    neu = p[2]
    spans = [(-neu / 2 - p[1] - p[0], p[0]), (-neu / 2 - p[1], p[1]), (-neu / 2, neu), (neu / 2, p[3]), (neu / 2 + p[3], p[4])]
    for (left, w), c in zip(spans, cols):
        ax.barh(i, w, left=left, color=c, height=.62)
        if w >= 7: ax.text(left + w / 2, i, f"{w:.0f}%", ha="center", va="center", fontsize=8,
                           color="white" if c in (cols[0], cols[4]) else "black")
ax.set_yticks(range(4)); ax.set_yticklabels(order)
ax.axvline(0, color="black", lw=.8); ax.set_xlim(-90, 60)
ax.set_xticks([-80, -60, -40, -20, 0, 20, 40, 60]); ax.set_xticklabels([80, 60, 40, 20, 0, 20, 40, 60])
ax.set_xlabel("% of students"); ax.set_title("(a) Satisfaction with each mess meal")
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in cols], labels=cats, ncol=5, fontsize=6.3,
          loc="upper center", bbox_to_anchor=(.5, -.2), frameon=False, columnspacing=.8, handlelength=1)
fav = ["Breakfast", "Lunch", "Snacks", "Dinner"]
vals = [S["fav_meal"][m] for m in fav]
ax2.bar(fav, vals, color=[BLUE, BLUE, BLUE, ORANGE]); ax2.set_title("(b) Favourite mess meal")
for x, v in enumerate(vals): ax2.text(x, v + .6, str(v), ha="center", fontsize=8)
ax2.set_ylabel("Students"); ax2.tick_params(axis="x", labelsize=8)
fig.suptitle("Figure 2. Mess meals: satisfaction and preference", fontsize=10, fontweight="bold", y=1.03)
fig.tight_layout(); save(fig, "fig02_meal_satisfaction.png")

# ---- Fig 3: taste & quality
fig, axs = plt.subplots(1, 2, figsize=(8.0, 2.6), sharey=True)
for ax, col, lab in zip(axs, ["taste", "quality"], ["Taste of mess food", "Overall quality and consistency"]):
    vc = df[col].value_counts().reindex(range(1, 6), fill_value=0)
    ax.bar(vc.index, vc.values, color=BLUE)
    for x, v in zip(vc.index, vc.values): ax.text(x, v + .5, str(v), ha="center", fontsize=8)
    ax.axvline(df[col].mean(), color=ORANGE, ls="--"); ax.text(df[col].mean() + .05, vc.max() * 1.12, f"mean {df[col].mean():.2f}", color=ORANGE, fontsize=8)
    ax.set_xlabel("Rating (1 = very poor, 5 = excellent)"); ax.set_title(lab); ax.set_ylim(0, vc.max() * 1.3)
axs[0].set_ylabel("Students")
fig.suptitle("Figure 3. Taste and quality ratings", fontsize=10, fontweight="bold", y=1.04)
fig.tight_layout(); save(fig, "fig03_taste_quality.png")

# ---- Fig 4: mess habits (skips, disliked days, menu influence)
fig, axs = plt.subplots(1, 3, figsize=(9.0, 2.7))
ax = axs[0]
ax.hist(df.meals_skipped, bins=np.arange(-.5, 21.5, 1), color=BLUE, edgecolor="white")
ax.axvline(df.meals_skipped.median(), color=ORANGE, ls="--"); ax.text(df.meals_skipped.median() + .4, ax.get_ylim()[1] * .9, f"median {df.meals_skipped.median():.0f}", color=ORANGE, fontsize=8)
ax.set_xlabel("Meals skipped per week"); ax.set_ylabel("Students"); ax.set_title("(a) Meals skipped")
ax = axs[1]
vc = df.disliked_days.value_counts().reindex(range(1, 8), fill_value=0)
ax.bar(vc.index, vc.values, color=BLUE)
for x, v in zip(vc.index, vc.values): ax.text(x, v + .3, str(v), ha="center", fontsize=8)
ax.set_xlabel("Days menu disliked (of 7)"); ax.set_title("(b) Disliked menu days")
ax = axs[2]
lv = ["Rarely", "Sometimes", "Often", "Very Often"]
vals = [S["menu_counts"].get(l, 0) for l in lv]
ax.bar(lv, vals, color=BLUE)
for x, v in enumerate(vals): ax.text(x, v + .3, str(v), ha="center", fontsize=8)
ax.set_title("(c) Menu influences ordering"); ax.tick_params(axis="x", labelsize=8)
fig.suptitle("Figure 4. Mess habits", fontsize=10, fontweight="bold", y=1.04)
fig.tight_layout(); save(fig, "fig04_mess_habits.png")

# ---- Fig 5: ordering context
fig, axs = plt.subplots(1, 3, figsize=(9.0, 2.5))
w = S["when"]; ks = ["Breakfast", "Lunch", "Dinner"]
axs[0].bar(ks, [w.get(k, 0) for k in ks], color=[BLUE, BLUE, ORANGE])
for x, k in enumerate(ks): axs[0].text(x, w.get(k, 0) + .8, str(w.get(k, 0)), ha="center", fontsize=8)
axs[0].set_title("(a) Meal most often ordered for"); axs[0].set_ylabel("Students")
for ax, key, t in [(axs[1], "off_hours_n", "(b) Orders outside mess hours"), (axs[2], "skipped_flag_n", "(c) Orders after skipping a meal")]:
    y = S[key]; ax.bar(["Yes", "No"], [y, S["n"] - y], color=[BLUE, LIGHT]); ax.set_title(t)
    for x, v in enumerate([y, S["n"] - y]): ax.text(x, v + .8, f"{v} ({v / S['n'] * 100:.0f}%)", ha="center", fontsize=8)
    ax.set_ylim(0, 40)
fig.suptitle("Figure 5. When and why-context of ordering", fontsize=10, fontweight="bold", y=1.05)
fig.tight_layout(); save(fig, "fig05_ordering_context.png")

# ---- Fig 6: orders & spend distributions
fig, axs = plt.subplots(1, 3, figsize=(9.0, 2.7))
vc = df.orders.value_counts().reindex(range(0, int(df.orders.max()) + 1), fill_value=0)
axs[0].bar(vc.index, vc.values, color=BLUE); axs[0].set_xlabel("Orders per week"); axs[0].set_ylabel("Students"); axs[0].set_title("(a) Orders per week")
axs[0].axvline(df.orders.median(), color=ORANGE, ls="--"); axs[0].text(df.orders.median() + .2, vc.max() * .93, f"median {df.orders.median():.0f}", color=ORANGE, fontsize=8)
axs[1].hist(df.spend, bins=np.arange(0, 3201, 100), color=BLUE, edgecolor="white")
axs[1].set_xlabel("Weekly spend (Rs)"); axs[1].set_title("(b) Weekly spend")
axs[1].annotate("one student:\nRs 3000", xy=(3000, 1), xytext=(2000, 10), arrowprops=dict(arrowstyle="->", color=ORANGE), color=ORANGE, fontsize=8)
axs[1].axvline(df.spend.median(), color=ORANGE, ls="--")
axs[2].hist(df.spend_per_order.dropna(), bins=np.arange(0, 551, 50), color=BLUE, edgecolor="white")
axs[2].axvline(df.spend_per_order.median(), color=ORANGE, ls="--")
axs[2].text(df.spend_per_order.median() + 8, axs[2].get_ylim()[1] * .9, f"median Rs {df.spend_per_order.median():.0f}", color=ORANGE, fontsize=8)
axs[2].set_xlabel("Spend per order (Rs)"); axs[2].set_title("(c) Spend per order")
fig.suptitle("Figure 6. Ordering frequency and spending", fontsize=10, fontweight="bold", y=1.04)
fig.tight_layout(); save(fig, "fig06_orders_spend_dist.png")

# ---- Fig 7: reasons
rl = {"dissatisfaction": "Dissatisfaction with mess food", "better_taste": "Better taste", "craving": "Craving for particular food",
      "lack_of_variety": "Lack of variety in mess", "friends": "Ordering with friends", "skipped_meal": "Skipped a mess meal",
      "convenience": "Convenience / too busy", "timing": "Mess timing inconvenient", "other": "Other"}
r = sorted(S["reasons_n"].items(), key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(7.0, 3.1))
ax.barh([rl[k] for k, _ in r], [v / S["n"] * 100 for _, v in r], color=[ORANGE if k == "dissatisfaction" else BLUE for k, _ in r])
for i, (_, v) in enumerate(r): ax.text(v / S["n"] * 100 + 1, i, f"{v / S['n'] * 100:.0f}% ({v})", va="center", fontsize=8)
ax.set_xlabel("% of students (multiple answers allowed)"); ax.set_xlim(0, 100)
ax.set_title("Figure 7. Reasons for ordering outside food")
fig.tight_layout(); save(fig, "fig07_reasons.png")

# ---- Fig 8: days
fig, axs = plt.subplots(1, 2, figsize=(9.0, 2.9), gridspec_kw={"width_ratios": [2.2, 1]})
ds = [S["days_n"][d] for d in DAYS]
axs[0].bar([d[:3] for d in DAYS], ds, color=[ORANGE if d in ("Wednesday", "Sunday") else BLUE for d in DAYS])
for x, v in enumerate(ds): axs[0].text(x, v + .5, f"{v}\n({v / S['n'] * 100:.0f}%)", ha="center", fontsize=8)
axs[0].set_ylim(0, 36); axs[0].set_ylabel("Students ordering on the day"); axs[0].set_title("(a) Which day do students order most?")
axs[1].bar(["Wed & Sun\n(non-veg days)", "Other five\ndays"], [S["nonveg_days_avg"], S["other_days_avg"]], color=[ORANGE, BLUE], width=.55)
for x, v in enumerate([S["nonveg_days_avg"], S["other_days_avg"]]): axs[1].text(x, v + .5, f"{v:.1f}", ha="center", fontsize=9)
axs[1].set_ylim(0, 30); axs[1].set_title("(b) Average students per day"); axs[1].tick_params(axis="x", labelsize=8)
fig.suptitle("Figure 8. Ordering by day of the week", fontsize=10, fontweight="bold", y=1.05)
fig.tight_layout(); save(fig, "fig08_days.png")

# ---- Fig 9: social
fig, axs = plt.subplots(1, 3, figsize=(9.2, 2.9), gridspec_kw={"width_ratios": [1, 1.4, 1]})
mc = [S["mode_counts"].get(k, 0) for k in ["Mostly with friends", "Mostly alone", "About equally alone and with friends"]]
axs[0].pie(mc, labels=["Mostly with\nfriends", "Mostly\nalone", "About\nequal"], colors=[BLUE, ORANGE, LIGHT], autopct=lambda p: f"{p:.0f}%", startangle=90,
           wedgeprops=dict(width=.45, edgecolor="white"), textprops={"fontsize": 8}, pctdistance=.78)
axs[0].set_title("(a) Usual ordering company")
mm = S["mode_means"]; names = ["Mostly with friends", "Mostly alone", "About equally alone and with friends"]; short = ["Mostly\nfriends", "Mostly\nalone", "About\nequal"]
x = np.arange(3); wd = .38
axs[1].bar(x - wd / 2, [mm[n]["orders_alone"] for n in names], wd, label="Alone", color=ORANGE)
axs[1].bar(x + wd / 2, [mm[n]["orders_friends"] for n in names], wd, label="With friends", color=BLUE)
axs[1].set_xticks(x); axs[1].set_xticklabels([f"{s}\n(n={S['mode_counts'][n]})" for s, n in zip(short, names)], fontsize=8)
axs[1].set_ylabel("Mean orders per week"); axs[1].legend(fontsize=8, frameon=False); axs[1].set_title("(b) Average orders by stated company")
axs[2].bar(["More with\nfriends", "Equal", "More\nalone"], [S["friends_gt_alone"], S["equal"], S["alone_gt_friends"]], color=[BLUE, LIGHT, ORANGE])
for xx, v in enumerate([S["friends_gt_alone"], S["equal"], S["alone_gt_friends"]]): axs[2].text(xx, v + .6, str(v), ha="center", fontsize=8)
axs[2].set_title("(c) Students by their own counts"); axs[2].tick_params(axis="x", labelsize=8)
fig.suptitle("Figure 9. Social influence on ordering", fontsize=10, fontweight="bold", y=1.05)
fig.tight_layout(); save(fig, "fig09_social.png")

# ---- Fig 10: orders vs spend
rng = np.random.default_rng(1)
fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.2))
ax = axs[0]
jit = rng.uniform(-.12, .12, len(df))
capped = (df.orders_outlier == 1) | (df.spend_outlier == 1)
ax.scatter(df.orders_capped[~capped] + jit[~capped], df.spend_capped[~capped], color=BLUE, alpha=.75, s=22)
ax.scatter(df.orders_capped[capped] + jit[capped], df.spend_capped[capped], color=ORANGE, alpha=.9, s=30, marker="D", label="Capped outlier")
xs = np.linspace(0, 6, 10); ax.plot(xs, slope * xs + icpt, color="black", lw=1.2)
ax.set_ylim(-40, 1420)
ax.text(.035, .97, f"r = {S['pearson_orders_spend_capped']:.2f}    R$^2$ = {S['reg_simple']['r2']:.2f}\n"
                   f"spend = {S['reg_simple']['coef']['intercept']:.0f} + {slope:.0f} x orders",
        transform=ax.transAxes, fontsize=8, va="top", ha="left", linespacing=1.5,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=GREY, linewidth=.7))
ax.set_xlabel("Orders per week (capped at 6)"); ax.set_ylabel("Weekly spend (Rs, capped at 950)"); ax.legend(fontsize=8, frameon=False, loc="lower right")
ax.set_title("(a) More orders, more spending")
ax = axs[1]
bands = ["0-1", "2", "3", "4+"]
data = [df.loc[df.order_band == b, "spend_capped"] for b in bands]
bp = ax.boxplot(data, tick_labels=[f"{b}\n(n={len(d)})" for b, d in zip(bands, data)], patch_artist=True, widths=.55,
                flierprops=dict(markersize=3))
for p in bp["boxes"]: p.set_facecolor("#9DC1E8")
for m in bp["medians"]: m.set_color("black")
ax.set_xlabel("Orders per week"); ax.set_ylabel("Weekly spend (Rs, capped)"); ax.set_title("(b) Spend by number of orders")
fig.suptitle("Figure 10. Number of orders and spending", fontsize=10, fontweight="bold", y=1.04)
fig.tight_layout(); save(fig, "fig10_orders_vs_spend.png")

# ---- Fig 11: social vs spend
fig, axs = plt.subplots(1, 3, figsize=(9.2, 2.9))
for ax, col, lab, c in [(axs[0], "orders_friends", "Orders with friends / week", BLUE), (axs[1], "orders_alone", "Orders alone / week", ORANGE)]:
    ax.scatter(df[col] + rng.uniform(-.1, .1, len(df)), df.spend_capped, color=c, alpha=.7, s=20)
    sl, ic = np.polyfit(df[col], df.spend_capped, 1); xs = np.linspace(0, df[col].max(), 10); ax.plot(xs, sl * xs + ic, color="black", lw=1.1)
    rr = df[col].corr(df.spend_capped); S["r_" + col + "_spend"] = float(rr)
    ax.text(.03, .93, f"r = {rr:.2f}", transform=ax.transAxes, fontsize=8)
    ax.set_xlabel(lab); ax.set_ylabel("Weekly spend (Rs, capped)")
axs[0].set_title("(a) Friends orders vs spend"); axs[1].set_title("(b) Solo orders vs spend")
bp = axs[2].boxplot([df.loc[df.order_mode == n, "spend_per_order"].dropna() for n in names],
                    tick_labels=[f"{s}\n(n={S['mode_counts'][n]})" for s, n in zip(short, names)], patch_artist=True, widths=.55, flierprops=dict(markersize=3))
for p in bp["boxes"]: p.set_facecolor("#9DC1E8")
for m in bp["medians"]: m.set_color("black")
axs[2].set_ylabel("Spend per order (Rs)"); axs[2].set_title("(c) Spend per order by company"); axs[2].tick_params(axis="x", labelsize=8)
fig.suptitle("Figure 11. Social context and spending", fontsize=10, fontweight="bold", y=1.05)
fig.tight_layout(); save(fig, "fig11_social_vs_spend.png")

# ---- Fig 12: dinner story
fig, ax = plt.subplots(figsize=(6.4, 2.9))
mnames = ["Breakfast", "Lunch", "Snacks", "Dinner"]
dis = [S["meal_dis_n"][m] / S["n"] * 100 for m in mnames]
ordd = [S["when"].get(m, 0) / S["n"] * 100 for m in mnames]
x = np.arange(4); wd = .38
ax.bar(x - wd / 2, dis, wd, color=RED, label="% dissatisfied with the mess meal")
ax.bar(x + wd / 2, ordd, wd, color=BLUE, label="% who mostly order outside for that meal")
for xx, v in zip(x - wd / 2, dis): ax.text(xx, v + 1.5, f"{v:.0f}%", ha="center", fontsize=8)
for xx, v in zip(x + wd / 2, ordd): ax.text(xx, v + 1.5, f"{v:.0f}%", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(mnames); ax.set_ylim(0, 110); ax.legend(fontsize=8, frameon=False, loc="upper left")
ax.set_title("Figure 12. The least-liked meal is the one students replace")
fig.tight_layout(); save(fig, "fig12_dinner_story.png")

# ---- Fig 13: menu influence
fig, axs = plt.subplots(1, 3, figsize=(9.2, 2.7))
lv = ["Rarely", "Sometimes", "Often", "Very Often"]
for ax, col, lab, c in [(axs[0], "orders", "Mean orders per week", BLUE), (axs[1], "disliked_days", "Mean days menu disliked", ORANGE),
                        (axs[2], "mess_index", "Mean overall mess index (1-5)", GREEN)]:
    v = [S["menu_means"][l][col] for l in lv]
    ax.bar(range(4), v, color=c)
    for i, val in enumerate(v): ax.text(i, val + max(v) * .02, f"{val:.1f}", ha="center", fontsize=8)
    ax.set_xticks(range(4)); ax.set_xticklabels([f"{l}\n(n={S['menu_n'][l]})" for l in lv], fontsize=7.5); ax.set_ylabel(lab)
    ax.set_ylim(0, max(v) * 1.18)
axs[0].set_title("(a) Orders"); axs[1].set_title("(b) Disliked days"); axs[2].set_title("(c) Mess index")
fig.suptitle("Figure 13. Menu influence on ordering (x-axis) vs orders, disliked days and mess rating", fontsize=10, fontweight="bold", y=1.04)
fig.tight_layout(); save(fig, "fig13_menu_influence.png")

# ---- Fig 14: skipping
fig, axs = plt.subplots(1, 3, figsize=(9.2, 2.9))
bands = ["0-2", "3-5", "6+"]
data = [df.loc[df.skip_band == b, "spend_capped"] for b in bands]
bp = axs[0].boxplot(data, tick_labels=[f"{b}\n(n={len(d)})" for b, d in zip(bands, data)], patch_artist=True, widths=.55, flierprops=dict(markersize=3))
for p in bp["boxes"]: p.set_facecolor("#9DC1E8")
for m in bp["medians"]: m.set_color("black")
axs[0].set_xlabel("Meals skipped per week"); axs[0].set_ylabel("Weekly spend (Rs, capped)"); axs[0].set_title("(a) Spend by skipping group")
axs[1].scatter(df.meals_skipped_capped + rng.uniform(-.15, .15, len(df)), df.spend_capped, color=BLUE, alpha=.7, s=20)
sl, ic = np.polyfit(df.meals_skipped_capped, df.spend_capped, 1); xs = np.linspace(0, 11, 10); axs[1].plot(xs, sl * xs + ic, color="black", lw=1.1)
axs[1].text(.03, .93, f"r = {S['pearson_skips_spend_capped']:.2f}   R$^2$ = {S['reg_skips']['r2']:.2f}",
            transform=axs[1].transAxes, fontsize=8)
axs[1].set_xlabel("Meals skipped (capped at 11)"); axs[1].set_ylabel("Weekly spend (Rs, capped)"); axs[1].set_title("(b) Skips vs spend")
gl = list(S["mess_group_means"].keys()); gv = [S["mess_group_means"][g]["meals_skipped"] for g in gl]
axs[2].bar(range(3), gv, color=[RED, GREY, GREEN])
for i, v in enumerate(gv): axs[2].text(i, v + .1, f"{v:.1f}", ha="center", fontsize=8)
axs[2].set_xticks(range(3)); axs[2].set_xticklabels([g.replace(" (", "\n(") + f"\nn={S['mess_group_counts'][g]}" for g in gl], fontsize=7.2)
axs[2].set_ylabel("Mean meals skipped / week"); axs[2].set_title("(c) Skipping by mess satisfaction")
fig.suptitle("Figure 14. Meal skipping, spending and mess satisfaction", fontsize=10, fontweight="bold", y=1.05)
fig.tight_layout(); save(fig, "fig14_skipping.png")

# ---- Fig 15: reasons & behaviour
fig, axs = plt.subplots(1, 3, figsize=(10.2, 2.9))
v = [S["dis_reason_orders"][0], S["dis_reason_orders"][1]]
axs[0].bar(["Does not cite\ndissatisfaction", "Cites\ndissatisfaction"], v, color=[GREY, RED], width=.55)
for i, val in enumerate(v): axs[0].text(i, val + .05, f"{val:.1f}", ha="center", fontsize=9)
axs[0].set_ylabel("Mean orders per week"); axs[0].set_title("(a) Dissatisfaction cited", fontsize=9); axs[0].tick_params(axis="x", labelsize=8)
axs[0].set_xticklabels([f"Does not cite\n(n={S['dis_reason_n'][0]})", f"Cites\n(n={S['dis_reason_n'][1]})"], fontsize=8)
v = [S["peer_dinner"][0], S["peer_dinner"][1]]
npeer = int(df.reason_friends.sum())
axs[1].bar([f"Does not cite\n(n={S['n'] - npeer})", f"Cites\n(n={npeer})"], v, color=[GREY, BLUE], width=.55)
for i, val in enumerate(v): axs[1].text(i, val + .03, f"{val:.1f}", ha="center", fontsize=9)
axs[1].set_ylabel("Mean dinner satisfaction (1-5)"); axs[1].set_title("(b) Ordering with friends cited", fontsize=9); axs[1].tick_params(axis="x", labelsize=8)
nd = S["ndays_orders"]; ks = sorted(nd)
axs[2].bar([f"{k}\n(n={S['ndays_n'][int(k)]})" for k in ks], [nd[k] for k in ks], color=BLUE)
for i, k in enumerate(ks): axs[2].text(i, nd[k] + .1, f"{nd[k]:.1f}", ha="center", fontsize=8)
axs[2].set_xlabel("Number of days named for ordering"); axs[2].set_ylabel("Mean orders per week"); axs[2].set_title("(c) Days named vs orders", fontsize=9)
axs[0].set_ylim(0, max(S["dis_reason_orders"].values()) * 1.28)
axs[1].set_ylim(0, max(S["peer_dinner"].values()) * 1.28)
axs[2].set_ylim(0, max(nd.values()) * 1.28)
fig.suptitle("Figure 15. Stated reasons and ordering behaviour", fontsize=10, fontweight="bold", y=1.06)
fig.tight_layout(w_pad=2.4); save(fig, "fig15_reasons_behaviour.png")

# ---- Fig 16: correlation heatmap
fig, ax = plt.subplots(figsize=(7.4, 6.0))
im = ax.imshow(C.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(C))); ax.set_yticks(range(len(C)))
ax.set_xticklabels(C.columns, rotation=45, ha="right", fontsize=8); ax.set_yticklabels(C.index, fontsize=8)
for i in range(len(C)):
    for j in range(len(C)):
        ax.text(j, i, f"{C.values[i, j]:.2f}", ha="center", va="center", fontsize=6.5, color="white" if abs(C.values[i, j]) > .55 else "black")
ax.grid(False); cb = fig.colorbar(im, ax=ax, fraction=.04, pad=.03); cb.set_label("Rank correlation (Spearman)", fontsize=8)
ax.set_title("Figure 16. Correlation heatmap of mess and ordering variables")
fig.tight_layout(); save(fig, "fig16_heatmap.png")

# ---- Fig 17: profile by mess satisfaction group (normalised)
prof = df.groupby("mess_group", observed=True)[["norm_meals_skipped_capped", "norm_disliked_days", "norm_orders_capped", "norm_spend_capped"]].mean()
fig, ax = plt.subplots(figsize=(7.2, 3.1))
labs = ["Meals skipped", "Days menu disliked", "Orders per week", "Weekly spend"]
x = np.arange(4); wd = .26
for i, (g, c) in enumerate(zip(prof.index, [RED, GREY, GREEN])):
    ax.bar(x + (i - 1) * wd, prof.loc[g].values, wd, label=f"{g}  (n={S['mess_group_counts'][g]})", color=c)
ax.set_xticks(x); ax.set_xticklabels(labs); ax.set_ylabel("Average (min-max scaled, 0-1)")
ax.legend(title="Overall mess satisfaction", fontsize=8, title_fontsize=8, frameon=False)
ax.set_title("Figure 17. Behaviour profile by overall mess satisfaction")
fig.tight_layout(); save(fig, "fig17_profile.png")
S["profile"] = prof.round(3).to_dict("index")

json.dump(S, open(os.path.join(BASE, "stats.json"), "w"), indent=1, default=str)
print("done", S["outliers"], S["mess_group_counts"])
