# Why Students Order Out

IDHV 2026M project (Group 7): a survey of hostel students on mess food
satisfaction and outside food ordering habits.

Group members:

- Arwapalli Durga Siva Koti Raghava Kumar - S20240010015
- Mothukuri Sai Teja - S20240010151
- Padarthy Sailesh Sai - S20240010170

## Files

| File | Description |
|------|-------------|
| `raw_data.csv` | Survey responses exactly as exported from Google Forms (59 responses, 23 questions). Not edited. |
| `cleaned_data.csv` | Cleaned and preprocessed dataset, produced by the analysis script. |
| `01_preprocess_and_eda.py` | Cleaning, preprocessing, descriptive statistics, EDA, regression and the chi-square test. |
| `requirements.txt` | Package versions needed to run the analysis. |
| `IDHV_Project_Report.pdf` | Final report. |
| `questionnaire.pdf` | The final questionnaire, also included as the report's appendix. |

## Running

```
pip install -r requirements.txt
python 01_preprocess_and_eda.py
```

The script takes no arguments and reads `raw_data.csv` from the project folder.
It writes `cleaned_data.csv`, the summary statistics, and the charts used in
the report.

## Note on the data

`raw_data.csv` is the untouched export. All cleaning decisions, including the
two consistency rules, are applied in `01_preprocess_and_eda.py` and documented
in Section 3 of the report. Values changed by a rule are preserved alongside the
corrected ones in `cleaned_data.csv` (`orders_as_stated`,
`orders_after_skip_as_stated`, `disliked_days_imputed`).
