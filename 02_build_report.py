"""
Step 2: build the PDF report from stats.json, cleaned_data.csv and figures/*.png
Run 01_preprocess_and_eda.py first.
"""
import os, json
from xml.sax.saxutils import escape

import pandas as pd
import matplotlib
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
                                KeepTogether, PageBreak)

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "figures")
S = json.load(open(os.path.join(BASE, "stats.json")))
raw = pd.read_csv(os.path.join(BASE, "raw_data.csv"))
ts = pd.to_datetime(raw.iloc[:, 0], format="%m/%d/%Y %H:%M:%S")
DATE_FROM, DATE_TO = ts.min().strftime("%d %b %Y"), ts.max().strftime("%d %b %Y")

# ------------------------------------------------------------------ fonts
fdir = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
pdfmetrics.registerFont(TTFont("DV", os.path.join(fdir, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", os.path.join(fdir, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DV-I", os.path.join(fdir, "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DV-BI", os.path.join(fdir, "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

BLUE = colors.HexColor("#2E6FBA"); DARK = colors.HexColor("#1F2D3D"); GREYC = colors.HexColor("#6B7785")
LIGHT = colors.HexColor("#EEF3F9")

body = ParagraphStyle("body", fontName="DV", fontSize=8.6, leading=12.2, alignment=TA_JUSTIFY, textColor=DARK, spaceAfter=4)
small = ParagraphStyle("small", parent=body, fontSize=7.6, leading=10.4, textColor=GREYC, alignment=0)
h1 = ParagraphStyle("h1", fontName="DV-B", fontSize=13, leading=16, textColor=BLUE, spaceBefore=8, spaceAfter=5, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="DV-B", fontSize=10, leading=13, textColor=DARK, spaceBefore=6, spaceAfter=3, keepWithNext=1)
title = ParagraphStyle("title", fontName="DV-B", fontSize=19, leading=24, textColor=DARK, alignment=TA_CENTER, spaceAfter=4)
subtitle = ParagraphStyle("subtitle", fontName="DV", fontSize=10.5, leading=14, textColor=GREYC, alignment=TA_CENTER, spaceAfter=3)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=12, bulletIndent=2, spaceAfter=2.5, alignment=0)
cell = ParagraphStyle("cell", fontName="DV", fontSize=7.8, leading=10, textColor=DARK)
cellb = ParagraphStyle("cellb", parent=cell, fontName="DV-B", textColor=colors.white)

story = []
def P(t, st=body): story.append(Paragraph(t, st))
def H1(t): story.append(Paragraph(t, h1))
def H2(t): story.append(Paragraph(t, h2))
def B(t): story.append(Paragraph(t, bullet, bulletText="•"))
def SP(h=4): story.append(Spacer(1, h))

pending = []
def H2f(t): pending.append(Paragraph(t, h2))

def fig(name, width=16.6, note=None):
    im = PILImage.open(os.path.join(FIG, name)); w, h = im.size
    el = list(pending); pending.clear()
    el += [Image(os.path.join(FIG, name), width=width * cm, height=width * cm * h / w)]
    if note: el.append(Paragraph(note, body))
    story.append(KeepTogether(el))

def table(rows, widths, header=True, zebra=True, align_right_from=None):
    data = []
    for i, r in enumerate(rows):
        data.append([Paragraph(escape(str(c)), cellb if (header and i == 0) else cell) for c in r])
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#C9D3DF")),
          ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if header: st.append(("BACKGROUND", (0, 0), (-1, 0), BLUE))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0: st.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(st)); story.append(t); SP(5)

# ------------------------------------------------------------------ helpers for numbers
n = S["n"]
pc = lambda k: f"{k / n * 100:.0f}%"
npc = lambda k: f"{k} ({k / n * 100:.0f}%)"
C = S["corr"]
cr = lambda a, b: C[a][b]
D = S["desc"]
mm = S["meal_mean"]; mdn = S["meal_dis_n"]
mode_means = S["mode_means"]
MF, MA, ME = "Mostly with friends", "Mostly alone", "About equally alone and with friends"

# ================================================================== PAGE 1: title, abstract, introduction
P("Why Students Order Out", title)
P("Analysing Mess Food Habits and Outside Food Ordering Habits among Hostel Students", subtitle)
P("IDHV 2026M Project Report &nbsp;|&nbsp; Introduction to Data Handling and Visualization", subtitle)
SP(4)
table([["Group number", "[to be filled]"], ["Group members", "[names and roll numbers of all members]"],
       ["Data collected", f"Online survey, {DATE_FROM} to {DATE_TO}; {n} respondents"]], [4, 12.6], header=False, zebra=False)

H1("Abstract")
P(f"We surveyed {n} hostel students about two things: how they experience the mess, and how they order food from outside. "
  f"Using descriptive statistics and visual exploratory analysis, we found that dinner is the least-liked mess meal "
  f"({pc(mdn['Dinner'])} dissatisfied) and also the meal that {pc(S['when']['Dinner'])} of students order outside food for. "
  f"A typical student orders {D['Orders per week']['median']:.0f} times a week and spends about Rs {D['Weekly spend (Rs)']['median']:.0f}, roughly "
  f"Rs {D['Spend per order (Rs)']['median']:.0f} per order, and weekly spending rises steadily with the number of orders. Ordering is mostly social "
  f"({round(S['tot_friends'] * 100 / S['tot_orders'])}% of orders are with friends), and it is rare on Wednesdays and Sundays, the days the mess serves non-veg meals. "
  f"Skipping mess meals, disliking the menu and low mess ratings tend to go together with more ordering and higher spending, although these links are weaker "
  f"than the link between the number of orders and spending.")

H1("1. Introduction")
H2("1.1 Motivation")
P("Hostel students already pay for the mess, yet many of them regularly pay again for food from outside. For students this is a recurring "
  "expense, and for mess management it is a signal that something about the mess is not working. Understanding <i>when</i>, <i>how often</i>, "
  "<i>with whom</i> and <i>why</i> students order outside food is a first step to understanding where the mess falls short and how much money "
  "students spend as a result.")
H2("1.2 Research question")
P("<b>Main question:</b> How do students' mess food habits and outside food ordering habits look on their own, and how are the two related?")
B("<b>Mess habits alone:</b> How satisfied are students with each mess meal, with taste and quality? How many meals do they skip, and how often do they dislike the menu?")
B("<b>Outside ordering habits alone:</b> On which days, how often and with whom do students order? How much do they spend? What reasons do they give?")
B("<b>Relationships:</b> Is the least-liked meal the one students replace? Do more orders mean more spending? Do skipping meals, a disliked menu or low satisfaction go together with more ordering?")
H2("1.3 Objectives")
B("Design a short questionnaire and collect responses from more than 50 students (quantitative and qualitative variables).")
B("Clean and organise the raw data: encode, handle outliers, derive new variables and normalise where needed.")
B("Describe each habit with simple summary statistics and charts, and uncover relationships with visual exploratory data analysis.")

# ================================================================== METHODOLOGY
H1("2. Methodology")
H2("2.1 Research design and sampling")
P(f"We ran a cross-sectional online survey (Google Forms) among hostel students of IIITS who eat in the mess. The form was shared in student groups and "
  f"collected {n} responses between {DATE_FROM} and {DATE_TO}. We used <b>convenience sampling</b> because it is quick and free and fits the scale of a "
  f"course project. Its drawback is that respondents are not a random sample: {S['year']['3rd year']} of {n} ({S['year']['3rd year'] / n * 100:.0f}%) are third-year students, "
  f"so the results describe this group rather than the whole hostel. Ordering and mess habits were asked about a <i>typical week</i> to keep answers simple.")
P("<i>Context used in the analysis:</i> the mess serves non-veg meals (for example chicken curry and biryani) on Wednesdays and Sundays. "
  "This is the group's knowledge of the weekly menu; the survey did not ask about it directly.", body)
H2("2.2 Questionnaire and variables")
P("The questionnaire has three parts: (i) outside ordering behaviour, (ii) mess satisfaction and habits, and (iii) year of study. It mixes single-choice, "
  "multiple-choice, 5-point rating and numeric questions. The full list of questions is in the Appendix.")
table([["Variable group", "Variables", "Type"],
       ["Outside ordering (quantitative)", "Weekly spend (Rs); orders per week; orders alone; orders with friends", "Numeric (ratio / count)"],
       ["Outside ordering (qualitative)", "Usual ordering company; reasons (multi-select); meal ordered for; days ordered (multi-select); ordered outside mess hours; ordered after skipping a meal", "Nominal / binary"],
       ["Mess satisfaction", "Taste (1-5); quality and consistency (1-5); satisfaction with breakfast, lunch, snacks, dinner (5-point scale)", "Ordinal"],
       ["Mess habits", "Meals skipped per week; days menu disliked (of 7); how often the menu influences ordering (4 levels); favourite meal", "Count / ordinal / nominal"],
       ["Background", "Year of study", "Nominal"]], [4.2, 9.2, 3.2])
P(f"The survey therefore has 21 analysis variables and {n} respondents, which satisfies the project requirement of more than 50 data points and more than 3 variables with both quantitative and qualitative types.")

# ================================================================== PREPROCESSING
H1("3. Data Preprocessing")
o = S["outliers"]
table([["Step", "What was done", "Why"],
       ["1. Inspection", f"{n} rows and 22 columns checked. {S['missing_cells']} missing values and {S['duplicates']} duplicate rows found.", "No imputation or removal needed."],
       ["2. Tidying", "Columns renamed to short names; timestamp dropped from the cleaned file; text trimmed.", "Easier analysis."],
       ["3. Encoding", "Satisfaction answers coded 1 (very dissatisfied) to 5 (very satisfied); menu influence coded 1-4; Yes/No coded 1/0.", "Needed for averages and correlations."],
       ["4. Multi-select split", "Days ordered split into 7 binary columns; reasons split into 9 binary columns.", "A multi-select answer is not analysable as one text cell."],
       ["5. Validation", f"Orders alone + orders with friends equals total orders in {S['alone_plus_friends_equals_orders']} of {n} rows.", "Confirms respondents answered consistently."],
       ["6. Derived variables", "Spend per order; share of orders with friends; overall mess index (mean of taste, quality and four meal ratings); number of order days; ordered on a non-veg day; order, skip and mess-satisfaction groups.", f"Simple, interpretable measures. The six ratings are consistent with each other (Cronbach's alpha = {S['cronbach_alpha']:.2f})."],
       ["7. Outliers", f"IQR rule (above Q3 + 1.5 x IQR). Weekly spend: {o['spend']['n']} values above Rs {o['spend']['fence']:.0f} ({', '.join(str(int(v)) for v in o['spend']['values'])}). "
                       f"Meals skipped: {o['meals_skipped']['n']} above {o['meals_skipped']['fence']:.1f} ({', '.join(str(int(v)) for v in o['meals_skipped']['values'])}). "
                       f"Orders: {o['orders']['n']} above {o['orders']['fence']:.0f} ({', '.join(str(int(v)) for v in o['orders']['values'])}). "
                       "Values were capped at the fence in new columns ending in _capped; original columns were kept.",
        "With only 55 rows, deleting students would lose information. The Rs 3000 answer could be a typing error or a genuine heavy spender, so we limit its influence rather than drop it."],
       ["8. Normalisation", "Min-max scaling (0 to 1) of capped spend, capped orders, capped skips, disliked days and the mess index.", "Puts variables with different units on one scale so they can be compared in one chart (Figure 17)."]],
      [2.5, 9.0, 5.1])
P("Descriptive statistics in Section 4 use the <b>original</b> values; the scatter plots and the correlation heatmap use the <b>capped</b> values so that a few extreme answers do not dominate.")
fig("fig01_outliers.png", 14.5)

# ================================================================== RESULTS
H1("4. Results and Analysis")
H2("4.1 Summary statistics")
rows = [["Variable", "Mean", "Median", "Std dev", "Min", "Max"]]
for lab, d in D.items():
    f = (lambda v: f"{v:.2f}") if ("rating" in lab or "index" in lab) else (lambda v: f"{v:.1f}")
    rows.append([lab, f(d["mean"]), f(d["median"]), f(d["sd"]), f(d["min"]), f(d["max"])])
table(rows, [6.2, 2.0, 2.0, 2.2, 2.1, 2.1])
P(f"Weekly spend is strongly right-skewed: the mean (Rs {D['Weekly spend (Rs)']['mean']:.0f}) is well above the median (Rs {D['Weekly spend (Rs)']['median']:.0f}) because a few heavy "
  f"spenders pull it up, so we quote the <b>median</b> as the typical value. A typical student orders {D['Orders per week']['median']:.0f} times a week, skips {D['Meals skipped per week']['median']:.0f} mess meals and dislikes the menu on "
  f"{D['Days menu disliked (of 7)']['median']:.0f} of 7 days. Taste (mean {D['Taste rating (1-5)']['mean']:.2f}) and quality (mean {D['Quality rating (1-5)']['mean']:.2f}) are both below the mid-point of 3.")

H2f("4.2 Mess habits on their own")
fig("fig02_meal_satisfaction.png", 16.0,
    f"<b>Observation.</b> Satisfaction falls through the day: average rating {mm['Breakfast']:.2f} for breakfast, {mm['Lunch']:.2f} for lunch, {mm['Snacks']:.2f} for snacks and "
    f"{mm['Dinner']:.2f} for dinner. Only {npc(mdn['Breakfast'])} are dissatisfied with breakfast, but {npc(mdn['Dinner'])} are dissatisfied with dinner and just "
    f"{S['meal_sat_n']['Dinner']} are satisfied. Breakfast is the favourite meal of {npc(S['fav_meal']['Breakfast'])} students, lunch of {S['fav_meal']['Lunch']}, dinner of {S['fav_meal']['Dinner']}, and snacks of none.")
fig("fig03_taste_quality.png", 12.5,
    f"<b>Observation.</b> {npc(S['taste_low_n'])} students rate taste 1 or 2 and {npc(S['quality_low_n'])} rate quality and consistency 1 or 2. Nobody gave the top rating of 5. "
    f"The two ratings move together (rank correlation {cr('Taste', 'Quality'):.2f}).")
fig("fig04_mess_habits.png", 16.0,
    f"<b>Observation.</b> Skipping meals is common: the median is {D['Meals skipped per week']['median']:.0f} meals a week, {npc(S['skip6_n'])} skip six or more and only {S['skip0_n']} skip none. "
    f"The menu is disliked on {D['Days menu disliked (of 7)']['mean']:.1f} days a week on average, and {npc(S['dislike5_n'])} dislike it on five or more days. "
    f"{npc(S['menu_often_n'])} say the daily menu influences their decision to order Often or Very Often.")

H2f("4.3 Outside ordering habits on their own")
fig("fig05_ordering_context.png", 16.0,
    f"<b>Observation.</b> Ordering is overwhelmingly a dinner habit: {npc(S['when']['Dinner'])} order mostly for dinner, against {S['when']['Lunch']} for lunch and {S['when']['Breakfast']} for breakfast. "
    f"{npc(S['off_hours_n'])} usually order outside mess timings and {npc(S['skipped_flag_n'])} order because they skipped a mess meal.")
fig("fig06_orders_spend_dist.png", 16.0,
    f"<b>Observation.</b> Orders per week: {S['orders_dist']['0']} students order none, {S['orders_dist']['1']} order once, {S['orders_dist']['2']} twice, {S['orders_dist']['3']} three times and "
    f"{sum(v for k, v in S['orders_dist'].items() if int(k) >= 4)} four or more times. The typical student spends Rs {D['Weekly spend (Rs)']['median']:.0f} a week "
    f"(about Rs {D['Weekly spend (Rs)']['median'] * 4:.0f} over four weeks), or Rs {D['Spend per order (Rs)']['median']:.0f} per order. {npc(S['spend500_n'])} spend Rs 500 or more, and the top six spenders account for "
    f"{S['top6_share'] * 100:.0f}% of the Rs {S['spend_total']:.0f} spent by the whole group in a week.")
fig("fig07_reasons.png", 12.8,
    f"<b>Observation.</b> Dissatisfaction with mess food is by far the most common reason ({npc(S['reasons_n']['dissatisfaction'])}), followed by better taste ({pc(S['reasons_n']['better_taste'])}), "
    f"cravings ({pc(S['reasons_n']['craving'])}) and lack of variety ({pc(S['reasons_n']['lack_of_variety'])}). Practical reasons such as convenience ({S['reasons_n']['convenience']}) or mess timing ({S['reasons_n']['timing']}) are rare.")
dn = S["days_n"]
fig("fig08_days.png", 16.0,
    f"<b>Observation.</b> Monday ({dn['Monday']}) and Saturday ({dn['Saturday']}) are the most popular ordering days, followed by Tuesday ({dn['Tuesday']}) and Friday ({dn['Friday']}). "
    f"Wednesday ({dn['Wednesday']}) and Sunday ({dn['Sunday']}), the days the mess serves non-veg meals, account for only {dn['Wednesday'] + dn['Sunday']} of {S['days_mentions']} ordering-day mentions "
    f"({(dn['Wednesday'] + dn['Sunday']) / S['days_mentions'] * 100:.1f}%), an average of {S['nonveg_days_avg']:.1f} students per day against {S['other_days_avg']:.1f} on the other five days. "
    f"This is consistent with students not needing outside food when the mess serves something they like, although the survey cannot prove the reason.")
fig("fig09_social.png", 16.2,
    f"<b>Observation.</b> {npc(S['mode_counts'][MF])} students usually order with friends, {npc(S['mode_counts'][MA])} alone and {npc(S['mode_counts'][ME])} about equally. "
    f"Of the {S['tot_orders']} orders per week in the group, {S['tot_friends']} ({S['tot_friends'] / S['tot_orders'] * 100:.0f}%) are with friends. {S['friends_gt_alone']} students order more with friends than alone, "
    f"{S['equal']} equally and {S['alone_gt_friends']} more alone; {npc(S['never_alone'])} never order alone. Panel (b) confirms that the stated company matches the actual counts.")

H2("4.4 Relationships between mess habits and ordering habits")
P("Strength of association is described with the rule of thumb: correlation of 0.6 or more is strong, 0.3 to 0.6 moderate, below 0.3 weak. "
  "Correlation shows that two things move together, not that one causes the other.")
H2f("(a) Number of orders and spending")
ob = S["order_band"]
fig("fig10_orders_vs_spend.png", 15.0,
    f"<b>Observation.</b> More orders mean more spending. Median weekly spend is Rs {ob['0-1']['median']:.0f} for 0-1 orders, Rs {ob['2']['median']:.0f} for two, Rs {ob['3']['median']:.0f} for three and "
    f"Rs {ob['4+']['median']:.0f} for four or more (mean Rs {ob['4+']['mean']:.0f}, lifted by heavy spenders). The correlation is {S['pearson_orders_spend_capped']:.2f} (strong), with roughly "
    f"Rs {S['slope_orders_spend']:.0f} extra spend per additional weekly order, in line with the typical Rs {D['Spend per order (Rs)']['median']:.0f} per order.")
H2f("(b) Social influence and spending")
fig("fig11_social_vs_spend.png", 16.2,
    f"<b>Observation.</b> Orders with friends are more closely tied to spending (correlation {S['r_orders_friends_spend']:.2f}) than solo orders ({S['r_orders_alone_spend']:.2f}). "
    f"However, the company a student usually keeps does not change how much they order: average orders per week are {mode_means[MF]['orders']:.1f} (mostly friends), "
    f"{mode_means[MA]['orders']:.1f} (mostly alone) and {mode_means[ME]['orders']:.1f} (equal). Spend per order averages Rs {mode_means[MF]['spend_per_order']:.0f} for the friends group and Rs {mode_means[MA]['spend_per_order']:.0f} for the "
    f"solo group, but the solo and equal groups are small (n = {S['mode_counts'][MA]} and {S['mode_counts'][ME]}), so this is only indicative.")
H2f("(c) The least-liked meal is the meal students replace")
fig("fig12_dinner_story.png", 11.0,
    f"<b>Observation.</b> Dinner is where mess dissatisfaction ({pc(mdn['Dinner'])}) and outside ordering ({pc(S['when']['Dinner'])}) meet. {S['dinner_dis_and_dinner_order']} of the {mdn['Dinner']} students who are dissatisfied with dinner "
    f"mostly order outside for dinner. Breakfast, the best-rated meal, is almost never replaced.")
H2f("(d) Menu influence")
mn = S["menu_means"]
fig("fig13_menu_influence.png", 16.2,
    f"<b>Observation.</b> Students who say the menu influences their ordering more often order more: {mn['Rarely']['orders']:.1f} orders a week for 'Rarely', {mn['Sometimes']['orders']:.1f} for 'Sometimes' and "
    f"{mn['Often']['orders']:.1f} for 'Often'. The pattern is not perfectly steady, since the 'Very Often' group averages {mn['Very Often']['orders']:.1f}. The number of disliked days rises clearly with menu influence "
    f"({mn['Rarely']['disliked_days']:.1f} to {mn['Very Often']['disliked_days']:.1f}), and the 'Very Often' group also has the lowest overall mess rating ({mn['Very Often']['mess_index']:.1f} against about 2.8 for the others).")
H2f("(e) Meal skipping")
sb = S["skip_band"]
fig("fig14_skipping.png", 16.2,
    f"<b>Observation.</b> Students who skip more meals spend more. Median weekly spend is Rs {sb['0-2']['median']:.0f} for those skipping 0-2 meals, Rs {sb['3-5']['median']:.0f} for 3-5 and Rs {sb['6+']['median']:.0f} for 6 or more "
    f"(means Rs {sb['0-2']['mean']:.0f}, Rs {sb['3-5']['mean']:.0f} and Rs {sb['6+']['mean']:.0f}); the correlation is {S['pearson_skips_spend_capped']:.2f} (moderate). Skipping falls as mess satisfaction rises: students with low "
    f"overall ratings skip {S['mess_group_means']['Low (<2.5)']['meals_skipped']:.1f} meals a week, against {S['mess_group_means']['High (>3.0)']['meals_skipped']:.1f} for those with high ratings. "
    f"An unexpected pattern: students who usually order outside mess hours skip <i>fewer</i> meals ({S['offhours_skips']['1']:.1f}) than those who do not ({S['offhours_skips']['0']:.1f}), "
    f"so skipped meals are not always replaced by an order.")
H2f("(f) Stated reasons and behaviour")
fig("fig15_reasons_behaviour.png", 16.2,
    f"<b>Observation.</b> Students who give dissatisfaction as a reason order more ({S['dis_reason_orders']['1']:.1f} a week) than those who do not ({S['dis_reason_orders']['0']:.1f}). Students who order with friends as a reason "
    f"rate the mess dinner higher ({S['peer_dinner']['1']:.1f} against {S['peer_dinner']['0']:.1f}), which suggests that social ordering is driven by company rather than by unhappiness with the mess. "
    f"Panel (c) is a consistency check: students who name more ordering days order more times per week.")
H2f("(g) The whole picture: correlation heatmap and behaviour profile")
fig("fig16_heatmap.png", 12.6)
P(f"<b>Strongest links.</b> Orders per week and weekly spend ({cr('Orders / week', 'Weekly spend'):.2f}); orders per week with orders with friends ({cr('Orders / week', 'Orders w/ friends'):.2f}) and with orders alone ({cr('Orders / week', 'Orders alone'):.2f}); "
  f"taste and quality ({cr('Taste', 'Quality'):.2f}); disliked days and menu influence ({cr('Days menu disliked', 'Menu influence'):.2f}); quality and dinner satisfaction ({cr('Quality', 'Sat: Dinner'):.2f}). "
  f"<b>Mess side:</b> better ratings of breakfast, snacks and dinner go with fewer skipped meals (about {cr('Sat: Breakfast', 'Meals skipped'):.2f} to {cr('Sat: Dinner', 'Meals skipped'):.2f}). "
  f"<b>Weak links:</b> taste and orders per week ({cr('Taste', 'Orders / week'):.2f}) and dinner satisfaction and orders ({cr('Sat: Dinner', 'Orders / week'):.2f}) are close to zero. "
  f"In other words, the mess ratings explain <i>whether</i> a student is unhappy and skips meals better than they explain <i>how many</i> orders the student places.")
fig("fig17_profile.png", 11.8)
pf = S["profile"]; lo, hi = pf["Low (<2.5)"], pf["High (>3.0)"]
P(f"<b>Observation.</b> On the common 0-1 scale, students with low overall mess satisfaction skip more meals ({lo['norm_meals_skipped_capped']:.2f} vs {hi['norm_meals_skipped_capped']:.2f}), dislike the menu on more days "
  f"({lo['norm_disliked_days']:.2f} vs {hi['norm_disliked_days']:.2f}), order slightly more ({lo['norm_orders_capped']:.2f} vs {hi['norm_orders_capped']:.2f}) and spend slightly more ({lo['norm_spend_capped']:.2f} vs {hi['norm_spend_capped']:.2f}) "
  f"than students with high satisfaction. The gap is large for habits inside the mess (skipping, disliked days) and small for ordering and spending.")

# ================================================================== CONCLUSION
H1("5. Conclusion")
H2("5.1 Key findings")
table([["#", "Finding", "Evidence"],
       ["1", "Dinner is the weak spot of the mess.", f"{pc(mdn['Dinner'])} dissatisfied with dinner versus {pc(mdn['Breakfast'])} with breakfast (Fig. 2)."],
       ["2", "Outside ordering is a dinner habit.", f"{pc(S['when']['Dinner'])} mostly order for dinner; {S['dinner_dis_and_dinner_order']} of {mdn['Dinner']} dinner-dissatisfied students do so (Figs. 5, 12)."],
       ["3", "Spending follows the number of orders.", f"Median spend Rs {ob['0-1']['median']:.0f} to Rs {ob['4+']['median']:.0f} from 0-1 to 4+ orders; about Rs {D['Spend per order (Rs)']['median']:.0f} per order (Figs. 6, 10)."],
       ["4", "Ordering is social.", f"{round(S['tot_friends'] * 100 / S['tot_orders'])}% of orders are with friends; {npc(S['never_alone'])} never order alone (Fig. 9)."],
       ["5", "Wednesday and Sunday see almost no orders.", f"{dn['Wednesday'] + dn['Sunday']} of {S['days_mentions']} ordering-day mentions; both are non-veg days (Fig. 8)."],
       ["6", "Dissatisfaction is the main stated reason.", f"{pc(S['reasons_n']['dissatisfaction'])} cite it, and they order more ({S['dis_reason_orders']['1']:.1f} vs {S['dis_reason_orders']['0']:.1f} a week) (Figs. 7, 15)."],
       ["7", "Skipping and a disliked menu go with more ordering and spending.", f"Median spend Rs {sb['0-2']['median']:.0f} vs Rs {sb['6+']['median']:.0f} (0-2 vs 6+ skips); orders rise with menu influence (Figs. 13, 14)."],
       ["8", "Mess ratings relate more to skipping than to ordering.", "Satisfaction and skipping are moderately linked; satisfaction and order counts only weakly (Figs. 16, 17)."]],
      [0.8, 6.0, 9.8])
H2("5.2 What this means")
P("If mess management wants to reduce outside ordering, the data points first to <b>dinner</b>: improving its taste, quality and variety targets the meal that students are most unhappy with and most often replace. "
  "The low ordering on non-veg days suggests that menu appeal matters, and that a more appealing menu on other days could shift some of the ordering back to the mess. "
  "Because ordering is mostly done in groups, improvement may need to be visible to the whole friend circle to change habits.")
H2("5.3 Limitations")
B(f"Small, non-random sample ({n} students, convenience sampling, {S['year']['3rd year'] / n * 100:.0f}% third-year, one mess); results should not be generalised to all students.")
B("Spending, skipping and ordering are self-reported for a typical week and may be inaccurate.")
B("Some groups are small (for example only 9 students order mostly alone), so differences between them are indicative only.")
B("The Rs 3000 weekly spend and a few very high skip and order counts were capped rather than removed; this reduces their influence but is a judgement call.")
B("Correlations do not prove causation. The explanation for the low Wednesday and Sunday ordering is not tested by the survey.")
B("The survey did not record which days the menu was disliked or which meals were skipped, so day-level and meal-level links could not be tested.")
H2("5.4 Possible extensions")
P("A larger and more random sample, questions on the specific days and meals disliked, and the actual mess fees, would allow a direct comparison of what students pay the mess and what they pay outside.")

# ================================================================== APPENDIX
H1("Appendix: Questionnaire")
P("Questions used in the analysis (the original Google Form contained additional questions that were removed during cleaning).", small)
table([["#", "Question", "Answer format"],
       ["1", "How do you usually place your outside food orders?", "Mostly alone / About equally alone and with friends / Mostly with friends"],
       ["2", "What is the main reason you order food from outside?", "Multiple choice, select all: Dissatisfaction with mess food; Better taste; Craving for a particular food; Lack of variety in the mess; Ordering with friends; I skipped a mess meal; Convenience / too busy; Mess timing is inconvenient; Other"],
       ["3", "When do you most often order outside food?", "Breakfast / Lunch / Dinner"],
       ["4", "On which day do you most often order outside food?", "Multiple choice, select all: Monday to Sunday"],
       ["5", "Approximately how much do you spend on outside food orders in a typical week?", "Number (Rs)"],
       ["6", "Do you usually order outside food outside the operating timings of the mess?", "Yes / No"],
       ["7", "Do you usually order outside food because you skipped a mess meal?", "Yes / No"],
       ["8", "How satisfied are you with the taste of your mess food?", "Rating 1 to 5"],
       ["9", "How often does the day's mess menu influence your decision to order outside food?", "Rarely / Sometimes / Often / Very Often"],
       ["10", "How satisfied are you with each mess meal? (Breakfast, Lunch, Snacks, Dinner)", "Very dissatisfied / Dissatisfied / Neutral / Satisfied / Very satisfied, for each meal"],
       ["11", "On average, how many mess meals do you skip in a typical week?", "Number"],
       ["12", "Which mess meal do you prefer or like the most?", "Breakfast / Lunch / Snacks / Dinner"],
       ["13", "How would you rate the overall quality and consistency of your mess food?", "Rating 1 (very poor) to 5 (excellent / very consistent)"],
       ["14", "How many times do you order food from outside in a typical week?", "Number"],
       ["15", "In a typical week, how many times do you order outside food alone?", "Number"],
       ["16", "In a typical week, how many times do you order outside food with friends?", "Number"],
       ["17", "In a typical week, on how many days do you dislike the mess menu or find it unappealing?", "Number of days"],
       ["18", "What is your current year of study?", "2nd year / 3rd year / 4th year / Other"]],
      [0.8, 8.0, 7.8])

# ------------------------------------------------------------------ build
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5); canvas.setFillColor(GREYC)
    canvas.drawString(2 * cm, 1.1 * cm, "IDHV 2026M Project  |  Why Students Order Out")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")
    canvas.restoreState()

doc = SimpleDocTemplate(os.path.join(BASE, "IDHV_Project_Report.pdf"), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.7 * cm, bottomMargin=1.8 * cm, title="Why Students Order Out", author="IDHV 2026M Project Group")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("built")
