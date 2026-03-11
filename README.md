
# A/B Testing & Experimentation (Senior Data Scientist Level)

This repository demonstrates **end-to-end experimentation ownership**
expected from a **Senior Data Scientist / Experimentation Scientist**.

It covers **design → power → analysis → uncertainty → decision** using both
**frequentist and Bayesian** approaches, with business-ready outputs.

---

## What This Project Demonstrates

✔ Hypothesis-driven experimentation  
✔ Power & minimum detectable effect (MDE) analysis  
✔ Frequentist and Bayesian inference  
✔ Effect size & uncertainty (not just p-values)  
✔ Decision thresholds aligned with business risk  

---

## Experiment Setup

- Metric: Conversion rate
- Control: Variant A
- Treatment: Variant B
- Randomized user-level assignment
- Binary outcome

---

## How to Run

```bash
pip install numpy pandas scipy pymc arviz matplotlib
python src/analysis/run_ab_test.py
```

---

## Key Outputs

- Lift (%) and absolute effect
- Confidence & credible intervals
- Probability treatment beats control
- Executive decision recommendation

---

## Data

Data is fully synthetic and safe for public sharing.
