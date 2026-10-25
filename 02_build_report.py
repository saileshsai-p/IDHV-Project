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
                                KeepTogether)

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "figures")
S = json.load(open(os.path.join(BASE, "stats.json")))
raw = pd.read_csv(os.path.join(BASE, "raw_data.csv"))
ts = pd.to_datetime(raw.iloc[:, 0].astype(str).str.replace(r"\s*GMT[+-]\d+:\d+$", "", regex=True).str.strip(),
                    format="%Y/%m/%d %I:%M:%S %p")
DATE_FROM, DATE_TO = ts.min().strftime("%d %b %Y"), ts.max().strftime("%d %b %Y")

# ------------------------------------------------------------------ fonts
# Calibri (the Word default) where it is installed, DejaVu Sans otherwise so the
# script still runs on a machine without the Office fonts.
WINF = r"C:\Windows\Fonts"
MPLF = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
FACES = {"R": ("calibri.ttf", "DejaVuSans.ttf"), "B": ("calibrib.ttf", "DejaVuSans-Bold.ttf"),
         "I": ("calibrii.ttf", "DejaVuSans-Oblique.ttf"), "BI": ("calibriz.ttf", "DejaVuSans-BoldOblique.ttf")}
for tag, (win, mpl) in FACES.items():
    path = os.path.join(WINF, win)
    pdfmetrics.registerFont(TTFont("F-" + tag, path if os.path.exists(path) else os.path.join(MPLF, mpl)))
pdfmetrics.registerFontFamily("F-R", normal="F-R", bold="F-B", italic="F-I", boldItalic="F-BI")

BLACK = colors.black
GREYC = colors.HexColor("#444444")
RULE = colors.HexColor("#999999")

body = ParagraphStyle("body", fontName="F-R", fontSize=10, leading=13.2, alignment=TA_JUSTIFY, textColor=BLACK, spaceAfter=5)
small = ParagraphStyle("small", parent=body, fontSize=8.6, leading=11, textColor=GREYC, alignment=0)
h1 = ParagraphStyle("h1", fontName="F-B", fontSize=13, leading=16, textColor=BLACK, spaceBefore=10, spaceAfter=5, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="F-B", fontSize=10.5, leading=13.5, textColor=BLACK, spaceBefore=7, spaceAfter=3, keepWithNext=1)
title = ParagraphStyle("title", fontName="F-B", fontSize=17, leading=22, textColor=BLACK, alignment=TA_CENTER, spaceAfter=4)
subtitle = ParagraphStyle("subtitle", fontName="F-R", fontSize=11, leading=14, textColor=BLACK, alignment=TA_CENTER, spaceAfter=3)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=12, bulletIndent=2, spaceAfter=3, alignment=0,
                        bulletFontName="F-R", bulletFontSize=10)
cell = ParagraphStyle("cell", fontName="F-R", fontSize=8.8, leading=11, textColor=BLACK)
cellb = ParagraphStyle("cellb", parent=cell, fontName="F-B", textColor=BLACK)

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

# Cells are escaped so that stray "&" or "<" cannot break the XML parser, then the small set
# of tags used for emphasis and line breaks is restored.
RICH_TAGS = ("b", "/b", "i", "/i", "br/")
def rich(t):
    t = escape(str(t))
    for tag in RICH_TAGS:
        t = t.replace("&lt;%s&gt;" % tag, "<%s>" % tag)
    return t

def table(rows, widths, header=True):
    data = []
    for i, r in enumerate(rows):
        data.append([Paragraph(rich(c), cellb if (header and i == 0) else cell) for c in r])
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .5, RULE),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header: st.append(("LINEBELOW", (0, 0), (-1, 0), 1.0, BLACK))
    t.setStyle(TableStyle(st)); story.append(t); SP(6)

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
table([["Group number", "7"],
       ["Group members", "Arwapalli Durga Siva Koti Raghava Kumar - S20240010015<br/>"
                         "Mothukuri Sai Teja - S20240010151<br/>"
                         "Padarthy Sailesh Sai - S20240010170"],
       ["Data collected", f"Online survey, {DATE_FROM} to {DATE_TO}; {n} respondents"]], [4, 12.6], header=False)

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
  f"collected {n} responses between {DATE_FROM} and {DATE_TO}. The sampling method was <b>convenience sampling</b>, in which responses are obtained from members of the "
  f"target population who are readily accessible. It was adopted because no sampling frame listing hostel residents was available, and because the study had to be "
  f"completed within the duration of the course. The method does not yield a probability sample, and the achieved sample is concentrated in one cohort: "
  f"{S['year']['3rd year']} of {n} respondents ({S['year']['3rd year'] / n * 100:.0f}%) are third-year students. The findings therefore describe the respondents and should not be "
  f"generalised to the hostel population as a whole. Ordering and mess habits were asked about a <i>typical week</i> so that respondents could answer from routine rather than recall. "
  f"No personally identifying information was collected: participation was voluntary and all responses are anonymous.")
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
P(f"The survey therefore has 22 analysis variables and {n} respondents, which satisfies the project requirement of more than 50 data points and more than 3 variables with both quantitative and qualitative types.")

# ================================================================== PREPROCESSING
H1("3. Data Preprocessing")
o = S["outliers"]
table([["Step", "What was done", "Why"],
       ["1. Inspection", f"{n} responses and {S['n_columns_raw']} columns checked: {S['missing_cells']} blanks and {S['duplicates']} duplicate responses found.",
        "Establishes what has to be repaired before analysis."],
       ["2. Tidying", "Columns matched on question text and renamed to short names; timestamp dropped from the cleaned file; text and numeric answers trimmed (some were entered as \"2 \" with a trailing space).", "Easier analysis, and the script still loads a re-export whose columns are in a different order."],
       ["3. Encoding", "Satisfaction answers coded 1 (very dissatisfied) to 5 (very satisfied); menu influence coded 1-4; Yes/No coded 1/0.", "Needed for averages and correlations."],
       ["4. Missing values",
        f"{S['missing_cells']} blank entries were found, all in Question 18 (days on which the menu is disliked). No other question had a missing value. "
        f"Each blank was replaced by the median of that column ({S['imputed_median']['disliked_days']['value']:.0f} days) and marked in an indicator column, disliked_days_imputed. "
        f"No response was blank in more than half of its fields, so no response was removed ({S['rows_dropped']} deleted).",
        "Median imputation keeps the respondent's remaining answers available to the analysis, which deletion would discard. The median is preferred to the mean because the variable is a bounded day count (0-7) and mildly skewed. The indicator column allows the analysis to be repeated with the affected responses excluded."],
       ["5. Multi-select split",
        "Question 4 (days on which outside food is ordered) was split into 7 binary columns, one per day of the week. "
        "Question 2 (reasons for ordering) was split into 9 binary columns, one per listed reason.",
        "Both questions allow more than one answer, so a single cell may hold several options separated by semicolons. Binary indicator columns make each option countable and allow combinations to be compared."],
       ["6. Consistency rules",
        f"<b>Rule 1 (weekly order total).</b> Questions 15, 16 and 17 ask separately for the weekly total, the orders placed alone, and the orders placed with friends. "
        f"The three answers agree in {S['alone_plus_friends_equals_orders']} of {n} responses. In the remaining {S['orders_mismatch_n']}, the stated total was replaced by "
        f"(orders alone + orders with friends).<br/>"
        f"<b>Rule 2 (orders after skipping a meal).</b> Question 8 asks how many of those weekly orders followed a skipped mess meal. These are part of the weekly total and so "
        f"cannot exceed it. In {S['after_skip_capped_n']} responses the count was larger than the total, and it was reduced to that respondent's own total.<br/>"
        "The values as answered are retained in the columns orders_as_stated and orders_after_skip_as_stated.",
        "An outside order placed by a hostel student is either placed alone or with friends, so the two parts together must account for the weekly total. Where the three answers disagree, the two part-counts are the better supported figure, since each is given separately and the total is a summary the respondent has to work out. Rule 2 applies the same part-and-whole logic."],
       ["7. Derived variables", "Spend per order; share of orders with friends; overall mess index (mean of taste, quality and four meal ratings); number of order days; ordered on a non-veg day; order, skip and mess-satisfaction groups.", f"Simple, interpretable measures. The six ratings are consistent with each other (Cronbach's alpha = {S['cronbach_alpha']:.2f})."],
       ["8. Outliers", f"IQR rule (above Q3 + 1.5 x IQR). Weekly spend: {o['spend']['n']} values above Rs {o['spend']['fence']:.0f} ({', '.join(str(int(v)) for v in o['spend']['values'])}). "
                       f"Meals skipped: {o['meals_skipped']['n']} above {o['meals_skipped']['fence']:.1f} ({', '.join(str(int(v)) for v in o['meals_skipped']['values'])}). "
                       f"Orders: {o['orders']['n']} above {o['orders']['fence']:.0f} ({', '.join(str(int(v)) for v in o['orders']['values'])}). "
                       "Values were capped at the fence in new columns ending in _capped; original columns were kept.",
        f"With only {n} responses, deleting students would lose information. The Rs 3000 answer could be a typing error or a genuine heavy spender, so we limit its influence rather than drop it."],
       ["9. Normalisation", "Min-max scaling (0 to 1) of capped spend, capped orders, capped skips, disliked days and the mess index.", "Puts variables with different units on one scale so they can be compared in one chart (Figure 17)."]],
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
    f"<b>Observation.</b> Mean satisfaction falls across the day: {mm['Breakfast']:.2f} for breakfast, {mm['Lunch']:.2f} for lunch, {mm['Snacks']:.2f} for snacks and "
    f"{mm['Dinner']:.2f} for dinner. {npc(mdn['Breakfast'])} students are dissatisfied with breakfast, compared with {npc(mdn['Dinner'])} students for dinner; only "
    f"{S['meal_sat_n']['Dinner']} students are satisfied with dinner. Breakfast is the preferred meal of {npc(S['fav_meal']['Breakfast'])} students, lunch of {S['fav_meal']['Lunch']}, "
    f"dinner of {S['fav_meal']['Dinner']}, and snacks of none.")
fig("fig03_taste_quality.png", 12.5,
    f"<b>Observation.</b> {npc(S['taste_low_n'])} students rate the taste of mess food 1 or 2 on the 5-point scale, and {npc(S['quality_low_n'])} students rate overall quality "
    f"and consistency 1 or 2. No student awarded the highest rating of 5 to either. The two ratings move together (rank correlation {cr('Taste', 'Quality'):.2f}).")
fig("fig04_mess_habits.png", 16.0,
    f"<b>Observation.</b> Meal skipping is common: the median is {D['Meals skipped per week']['median']:.0f} meals a week, {npc(S['skip6_n'])} students skip six or more, and {S['skip0_n']} students skip none. "
    f"The menu is disliked on {D['Days menu disliked (of 7)']['mean']:.1f} days a week on average, and {npc(S['dislike5_n'])} students dislike it on five or more days. "
    f"{npc(S['menu_often_n'])} students report that the daily menu influences their decision to order outside food Often or Very Often.")

H2f("4.3 Outside ordering habits on their own")
fig("fig05_ordering_context.png", 16.0,
    f"<b>Observation.</b> Outside ordering is concentrated at dinner: {npc(S['when']['Dinner'])} students order mainly for dinner, compared with {S['when']['Lunch']} students for lunch "
    f"and {S['when']['Breakfast']} for breakfast. {npc(S['off_hours_n'])} students usually order outside mess timings, and {npc(S['skipped_flag_n'])} students order because they skipped a mess meal.")
fig("fig06_orders_spend_dist.png", 16.0,
    f"<b>Observation.</b> Weekly order counts are low for most students: {S['orders_dist']['0']} students order none, {S['orders_dist']['1']} order once, {S['orders_dist']['2']} twice, "
    f"{S['orders_dist']['3']} three times and {sum(v for k, v in S['orders_dist'].items() if int(k) >= 4)} four or more times. The typical student spends Rs {D['Weekly spend (Rs)']['median']:.0f} a week "
    f"(about Rs {D['Weekly spend (Rs)']['median'] * 4:.0f} over four weeks), or Rs {D['Spend per order (Rs)']['median']:.0f} per order. {npc(S['spend500_n'])} students spend Rs 500 or more, and the six highest "
    f"spenders account for {S['top6_share'] * 100:.0f}% of the Rs {S['spend_total']:.0f} spent by the whole group in one week.")
fig("fig07_reasons.png", 12.8,
    f"<b>Observation.</b> Dissatisfaction with mess food is the most frequently cited reason, given by {npc(S['reasons_n']['dissatisfaction'])} students, followed by better taste "
    f"({pc(S['reasons_n']['better_taste'])}), craving for a particular food ({pc(S['reasons_n']['craving'])}) and lack of variety ({pc(S['reasons_n']['lack_of_variety'])}). Practical reasons are rare: "
    f"convenience is cited by {S['reasons_n']['convenience']} students and inconvenient mess timing by {S['reasons_n']['timing']}.")
dn = S["days_n"]
fig("fig08_days.png", 16.0,
    f"<b>Observation.</b> Monday ({dn['Monday']} students) and Saturday ({dn['Saturday']}) are the most frequently named ordering days, followed by Tuesday ({dn['Tuesday']}) and Friday ({dn['Friday']}). "
    f"Wednesday ({dn['Wednesday']}) and Sunday ({dn['Sunday']}), the days on which the mess serves non-veg meals, together account for {dn['Wednesday'] + dn['Sunday']} of {S['days_mentions']} ordering-day mentions "
    f"({(dn['Wednesday'] + dn['Sunday']) / S['days_mentions'] * 100:.1f}%), an average of {S['nonveg_days_avg']:.1f} students per day against {S['other_days_avg']:.1f} on the other five days. "
    f"This is consistent with students ordering less when the mess menu is more appealing, although the survey does not test the reason.")
fig("fig09_social.png", 16.2,
    f"<b>Observation.</b> {npc(S['mode_counts'][MF])} students describe themselves as usually ordering with friends, {npc(S['mode_counts'][MA])} students as usually ordering alone, and "
    f"{npc(S['mode_counts'][ME])} students as doing both about equally. Of the {S['tot_orders']} orders placed by the group in a week, {S['tot_friends']} ({S['tot_friends'] / S['tot_orders'] * 100:.0f}%) are with friends. "
    f"{S['friends_gt_alone']} students place more orders with friends than alone, {S['equal']} students place equal numbers, and {S['alone_gt_friends']} students place more alone; {npc(S['never_alone'])} students never order alone. "
    f"Panel (b) compares the two counts within each self-described group, and the descriptions match the counts: students who say they order mostly with friends average "
    f"{mode_means[MF]['orders_friends']:.1f} social orders against {mode_means[MF]['orders_alone']:.1f} solo orders a week, those who say mostly alone average {mode_means[MA]['orders_alone']:.1f} solo against "
    f"{mode_means[MA]['orders_friends']:.1f} social, and the about-equally group averages {mode_means[ME]['orders_alone']:.1f} of each.")

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
    f"<b>Observation.</b> Orders with friends are more closely tied to spending (correlation {S['r_orders_friends_spend']:.2f}) than solo orders ({S['r_orders_alone_spend']:.2f}), "
    f"which is expected because most orders are social. The company a student usually keeps does not follow the same pattern: students who order mostly alone actually order "
    f"<i>more</i> often ({mode_means[MA]['orders']:.1f} a week) than those who order mostly with friends ({mode_means[MF]['orders']:.1f}) or about equally ({mode_means[ME]['orders']:.1f}), "
    f"and they spend more per order (Rs {mode_means[MA]['spend_per_order']:.0f} against Rs {mode_means[MF]['spend_per_order']:.0f}). "
    f"The solo and equal groups are small (n = {S['mode_counts'][MA]} and {S['mode_counts'][ME]}), so this is indicative only: social ordering accounts for most of the "
    f"<i>volume</i> of orders, but it is not what makes an individual student order frequently.")
H2f("(c) The least-liked meal is the meal students replace")
fig("fig12_dinner_story.png", 11.0,
    f"<b>Observation.</b> Dinner is where mess dissatisfaction ({pc(mdn['Dinner'])}) and outside ordering ({pc(S['when']['Dinner'])}) meet. {S['dinner_dis_and_dinner_order']} of the {mdn['Dinner']} students who are dissatisfied with dinner "
    f"mostly order outside for dinner. Breakfast, the best-rated meal, is almost never replaced.")
H2f("(d) Menu influence")
mn = S["menu_means"]
fig("fig13_menu_influence.png", 16.2,
    f"<b>Observation.</b> Mean orders per week rise with the stated influence of the menu: {mn['Rarely']['orders']:.1f} for Rarely, {mn['Sometimes']['orders']:.1f} for Sometimes and "
    f"{mn['Often']['orders']:.1f} for Often. The rise is not uniform, as the Very Often group averages {mn['Very Often']['orders']:.1f}. The number of disliked days rises steadily across the same groups "
    f"({mn['Rarely']['disliked_days']:.1f} to {mn['Very Often']['disliked_days']:.1f} days), and the Very Often group records the lowest overall mess rating ({mn['Very Often']['mess_index']:.1f} against about 2.8 for the other three groups).")
H2f("(e) Meal skipping")
sb = S["skip_band"]
fig("fig14_skipping.png", 16.2,
    f"<b>Observation.</b> Weekly spending rises with the number of meals skipped. Median spend is Rs {sb['0-2']['median']:.0f} for students skipping 0-2 meals, Rs {sb['3-5']['median']:.0f} for 3-5 and "
    f"Rs {sb['6+']['median']:.0f} for 6 or more (means Rs {sb['0-2']['mean']:.0f}, Rs {sb['3-5']['mean']:.0f} and Rs {sb['6+']['mean']:.0f}); the correlation is {S['pearson_skips_spend_capped']:.2f}, a moderate association. "
    f"Skipping falls as mess satisfaction rises: students in the low-satisfaction group skip {S['mess_group_means']['Low (<2.5)']['meals_skipped']:.1f} meals a week against "
    f"{S['mess_group_means']['High (>3.0)']['meals_skipped']:.1f} in the high-satisfaction group. One result runs against expectation: students who usually order outside mess hours skip <i>fewer</i> meals "
    f"({S['offhours_skips']['1']:.1f}) than those who do not ({S['offhours_skips']['0']:.1f}), indicating that a skipped meal is not always replaced by an outside order.")
H2f("(f) Stated reasons and behaviour")
fig("fig15_reasons_behaviour.png", 16.2,
    f"<b>Observation.</b> Students who cite dissatisfaction as a reason order more often ({S['dis_reason_orders']['1']:.1f} orders a week) than those who do not ({S['dis_reason_orders']['0']:.1f}). "
    f"Students who cite ordering with friends rate mess dinner higher ({S['peer_dinner']['1']:.1f} against {S['peer_dinner']['0']:.1f}), which indicates that social ordering is driven by company rather than by "
    f"dissatisfaction with the mess. Panel (c) serves as an internal consistency check: students who name more ordering days do place more orders per week, although the groups naming five or six days "
    f"contain only {S['ndays_n'].get(5, 0)} and {S['ndays_n'].get(6, 0)} students, so the upper end of that trend rests on very few responses.")
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

H2("4.5 Regression and a test of independence")
rs, rm, rk = S["reg_simple"], S["reg_multi"], S["reg_skips"]
P(f"<b>Regression.</b> Fitting weekly spend on the number of orders (both capped) gives "
  f"<b>spend = {rs['coef']['intercept']:.0f} + {rs['coef']['orders']:.0f} x orders</b>, with R&sup2; = {rs['r2']:.2f}. "
  f"Each additional weekly order is associated with about Rs {rs['coef']['orders']:.0f} more spending, close to the median of Rs {D['Spend per order (Rs)']['median']:.0f} per order, "
  f"and the number of orders alone explains {rs['r2'] * 100:.0f}% of the variation in what students spend. Meal skipping on its own explains much less (R&sup2; = {rk['r2']:.2f}).")
P(f"Adding meal skipping and the overall mess index to the model raises R&sup2; to {rm['r2']:.2f} (adjusted {rm['adj_r2']:.2f}): "
  f"spend = {rm['coef']['intercept']:.0f} + {rm['coef']['orders']:.0f} x orders + {rm['coef']['meals_skipped']:.0f} x meals skipped "
  f"{'-' if rm['coef']['mess_index'] < 0 else '+'} {abs(rm['coef']['mess_index']):.0f} x mess index. "
  f"Order count stays by far the strongest term; skipping adds a little, and the mess rating adds almost nothing once the other two are known. "
  f"This supports the pattern seen in the heatmap: mess satisfaction is linked to <i>whether</i> a student skips meals rather than to <i>how much</i> they spend.")
x2 = S["chi2"]; tb = x2["table"]
P(f"<b>Chi-square test.</b> We tested whether saying the daily menu often drives ordering is independent of being in the low mess-satisfaction group. "
  f"Of the {tb[1][0] + tb[1][1]} students who answered Often or Very Often, {tb[1][1]} fall in the low group; of the {tb[0][0] + tb[0][1]} who answered Rarely or Sometimes, only {tb[0][1]} do. "
  f"chi-square = {x2['chi2']:.2f} with 1 degree of freedom, above the 5% critical value of {x2['critical_5pct']:.2f}, so the two are "
  f"{'not independent' if x2['significant'] else 'independent'} at the 5% level (Cramer's V = {x2['cramers_v']:.2f}, a weak to moderate association). "
  f"All expected counts exceed 5 (smallest {x2['expected_min']:.1f}), so the test is valid here.")

# ================================================================== CONCLUSION
H1("5. Conclusion")
H2("5.1 Key findings")
table([["#", "Finding", "Evidence"],
       ["1", "Dinner is the weakest meal in the mess.",
        f"Dinner averages {mm['Dinner']:.2f} out of 5 against {mm['Breakfast']:.2f} for breakfast. {pc(mdn['Dinner'])} of students are dissatisfied with dinner, "
        f"against {pc(mdn['Breakfast'])} for breakfast (Fig. 2)."],
       ["2", "Students replace the meal they like least.",
        f"{pc(S['when']['Dinner'])} order outside mainly for dinner, and {S['dinner_dis_and_dinner_order']} of the {mdn['Dinner']} students dissatisfied with dinner do so. "
        f"Breakfast, the best-rated meal, is almost never replaced (Figs. 5, 12)."],
       ["3", "Spending is driven by how often a student orders, not by how much each order costs.",
        f"Median spend rises from Rs {ob['0-1']['median']:.0f} to Rs {ob['4+']['median']:.0f} between the 0-1 and 4+ order groups. Order count alone explains "
        f"{S['reg_simple']['r2'] * 100:.0f}% of the variation in spending, at about Rs {S['reg_simple']['coef']['orders']:.0f} per extra order (Figs. 6, 10)."],
       ["4", "Ordering is mostly a group activity.",
        f"{round(S['tot_friends'] * 100 / S['tot_orders'])}% of all orders are placed with friends and {npc(S['never_alone'])} students never order alone. "
        f"Group ordering drives the volume of orders, though students who order alone order slightly more often (Fig. 9)."],
       ["5", "Ordering almost stops on two days of the week.",
        f"Wednesday and Sunday account for {dn['Wednesday'] + dn['Sunday']} of {S['days_mentions']} ordering-day mentions, an average of {S['nonveg_days_avg']:.1f} students "
        f"per day against {S['other_days_avg']:.1f} on the other five days (Fig. 8)."],
       ["6", "Dissatisfaction with the mess is the main reason given, and it is reflected in behaviour.",
        f"{pc(S['reasons_n']['dissatisfaction'])} of students cite it, and they order {S['dis_reason_orders']['1']:.1f} times a week against {S['dis_reason_orders']['0']:.1f} "
        f"for those who do not (Figs. 7, 15)."],
       ["7", "Skipping mess meals and disliking the menu go with more ordering and higher spending.",
        f"Median weekly spend is Rs {sb['0-2']['median']:.0f} for students skipping 0-2 meals against Rs {sb['6+']['median']:.0f} for those skipping 6 or more. Students for whom "
        f"the menu often drives ordering are also more likely to be in the low-satisfaction group (chi-square = {S['chi2']['chi2']:.2f}, significant at 5%) (Figs. 13, 14)."],
       ["8", "Mess satisfaction explains skipping better than it explains ordering.",
        f"Satisfaction is moderately linked to meal skipping but only weakly to order counts, and adding the mess rating to the spending model changes little "
        f"(R-squared {S['reg_simple']['r2']:.2f} to {S['reg_multi']['r2']:.2f}) (Figs. 16, 17)."]],
      [0.8, 6.0, 9.8])
H2("5.2 What this means")
P("If mess management wants to reduce outside ordering, the data points first to <b>dinner</b>: improving its taste, quality and variety targets the meal that students are most unhappy with and most often replace. "
  "The low ordering on non-veg days suggests that menu appeal matters, and that a more appealing menu on other days could shift some of the ordering back to the mess. "
  "Because ordering is mostly done in groups, improvement may need to be visible to the whole friend circle to change habits.")
H2("5.3 Limitations")
B(f"The sample is small and non-random ({n} students, convenience sampling, {S['year']['3rd year'] / n * 100:.0f}% third-year, a single mess), so the findings describe the "
  f"respondents rather than the hostel population. Some subgroups are small (for example {S['mode_counts'][MA]} students order mostly alone), and comparisons between them are indicative only.")
B("All measures are self-reported for a typical week rather than recorded, so the counts carry reporting error. Some responses required the consistency corrections described in Section 3.")
B("Extreme values were capped rather than removed. This limits their influence on the correlations but retains responses whose accuracy cannot be verified.")
B("The analysis is observational, so the associations reported do not establish cause. In particular, the survey does not test why ordering is low on Wednesdays and Sundays.")
H2("5.4 Possible extensions")
P("A larger and more random sample, questions on the specific days and meals disliked, and the actual mess fees, would allow a direct comparison of what students pay the mess and what they pay outside.")

# ================================================================== APPENDIX
H1("Appendix: Questionnaire")
P("The complete set of questions in the Google Form. All of them are used in the analysis.", small)
QUESTIONNAIRE = [["#", "Question", "Answer format"],
       ["1", "How do you usually place your outside food orders?", "Mostly alone / About equally alone and with friends / Mostly with friends"],
       ["2", "What is the main reason you order food from outside?", "Multiple choice, select all: Dissatisfaction with mess food; Better taste; Craving for a particular food; Lack of variety in the mess; Ordering with friends; I skipped a mess meal; Convenience / too busy; Mess timing is inconvenient; Other"],
       ["3", "When do you most often order outside food?", "Breakfast / Lunch / Dinner"],
       ["4", "On which day do you most often order outside food?", "Multiple choice, select all: Monday to Sunday"],
       ["5", "Approximately how much do you spend on outside food orders in a typical week?", "Number (Rs)"],
       ["6", "Do you usually order outside food outside the operating timings of the mess?", "Yes / No"],
       ["7", "Do you usually order outside food because you skipped a mess meal?", "Yes / No"],
       ["8", "In a typical week, how many times do you order outside food after skipping a mess meal?", "Number"],
       ["9", "How satisfied are you with the taste of your mess food?", "Rating 1 to 5"],
       ["10", "How often does the day's mess menu influence your decision to order outside food?", "Rarely / Sometimes / Often / Very Often"],
       ["11", "How satisfied are you with each mess meal? (Breakfast, Lunch, Snacks, Dinner)", "Very dissatisfied / Dissatisfied / Neutral / Satisfied / Very satisfied, for each meal"],
       ["12", "On average, how many mess meals do you skip in a typical week?", "Number"],
       ["13", "Which mess meal do you prefer or like the most?", "Breakfast / Lunch / Snacks / Dinner"],
       ["14", "How would you rate the overall quality and consistency of your mess food?", "Rating 1 (very poor) to 5 (excellent / very consistent)"],
       ["15", "How many times do you order food from outside in a typical week?", "Number"],
       ["16", "In a typical week, how many times do you order outside food alone?", "Number"],
       ["17", "In a typical week, how many times do you order outside food with friends?", "Number"],
       ["18", "In a typical week, on how many days do you dislike the mess menu or find it unappealing?", "Number of days"],
       ["19", "What is your current year of study?", "2nd year / 3rd year / 4th year / Other"]]
table(QUESTIONNAIRE, [0.8, 8.0, 7.8])

# ------------------------------------------------------------------ build
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("F-R", 9); canvas.setFillColor(BLACK)
    canvas.drawCentredString(A4[0] / 2, 1.1 * cm, str(doc.page))
    canvas.restoreState()

doc = SimpleDocTemplate(os.path.join(BASE, "IDHV_Project_Report.pdf"), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.7 * cm, bottomMargin=1.8 * cm, title="Why Students Order Out", author="IDHV 2026M Project Group")
doc.build(story, onFirstPage=footer, onLaterPages=footer)

# ------------------------------------------------------------------ standalone questionnaire
# The brief lists the questionnaire as its own item, so the same table is also written
# to a separate file. The report keeps its appendix either way.
qstory = [Paragraph("Appendix: Final Questionnaire", title),
          Paragraph("IDHV 2026M Project &nbsp;|&nbsp; Why Students Order Out", subtitle), Spacer(1, 10),
          Paragraph("The complete set of questions as they appeared in the Google Form. "
                    "All of them are used in the analysis.", body), Spacer(1, 6)]
qdata = [[Paragraph(escape(str(c)), cellb if i == 0 else cell) for c in r] for i, r in enumerate(QUESTIONNAIRE)]
qt = Table(qdata, colWidths=[w * cm for w in (0.8, 8.0, 7.8)], repeatRows=1)
qt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .5, RULE),
                        ("LINEBELOW", (0, 0), (-1, 0), 1.0, BLACK),
                        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
qstory.append(qt)
SimpleDocTemplate(os.path.join(BASE, "questionnaire.pdf"), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                  topMargin=1.7 * cm, bottomMargin=1.8 * cm, title="Final Questionnaire",
                  author="IDHV 2026M Project Group").build(qstory, onFirstPage=footer, onLaterPages=footer)
print("built report + questionnaire")
