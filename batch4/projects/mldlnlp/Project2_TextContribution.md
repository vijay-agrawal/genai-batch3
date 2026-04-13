# Text Contribution Analysis

The text contributes most where symptoms are described in notes but have no corresponding column in the structured data. Here is the breakdown per archetype:

---

## Archetype-by-Archetype Analysis

| Archetype | Structured Signal Strength | What Notes Add | Text Contribution |
|---|---|---|---|
| Autoimmune Dysregulation | Medium (WBC↑ + CRP paradox — distinctive but subtle) | Rash, joint stiffness, "ANA ordered" — zero structured equivalents | High |
| Mitochondrial Disorder | High (lactate × 1.8–2.8, glucose × 0.70–0.85) | Exercise intolerance, muscle weakness, "cognitive fog" — no column for these | Medium |
| Rare Cardiac Syndrome | High (troponin × 3–8×, HR–BP dissociation) | Syncope, "ST changes", palpitations | Low–Medium |
| Hematologic Anomaly | High (HGB × 0.60–0.78, WBC × 1.5–2.2) | Night sweats, weight loss (B-symptoms), "flow cytometry ordered" | Medium–High |

---

## Where Text Matters Most: The Autoimmune Case

Look at the generator ([generate_dataset.py:94-100](generate_dataset.py#L94)):

```python
"modifiers": lambda f: {
    "wbc":     f["wbc"]     * RNG.uniform(1.4, 1.9),   # elevated WBC
    "crp":     f["crp"]     * RNG.uniform(0.8, 1.2),   # paradoxically NORMAL CRP
    "hr":      f["hr"]      * RNG.uniform(1.05, 1.15),
    "lactate": f["lactate"] * RNG.uniform(1.1, 1.4),
}
```

The WBC–CRP paradox is real but noisy — WBC × 1.4–1.9 with CRP unchanged is subtle. Meanwhile the notes say ([line 88-92](generate_dataset.py#L88)):

> "Rash noted on arms. CBC shows mild leukocytosis. Autoimmune w/u initiated."

> "Joint stiffness in mornings. Inflammatory markers borderline. Refer rheumatology."

"Rash", "joint stiffness", "ANA ordered", "rheumatology referral" — none of these map to any column. A PCA detector operating on structured features alone sees `wbc=10.5, crp=3.2` and has to detect the paradox. The embedding picks up vocabulary that is absent in all 10 healthy note templates.

---

## Where Text Matters Least: Rare Cardiac

Troponin is elevated 3–8× baseline ([line 131](generate_dataset.py#L131)):

```python
"troponin": f["troponin"] * RNG.uniform(3.0, 8.0),
```

This is a massive structured signal. Isolation Forest and OC-SVM will already catch this easily. The notes add "atypical chest pain" and "syncope" — useful clinically, but the model doesn't need them because the lab feature is already loudly anomalous.

---

## The Critical Design Pattern in This Dataset

The notes are not random — they are archetype-specific ([lines 71-149](generate_dataset.py#L71)):

- **Healthy notes:** generic vocabulary — "VS stable", "labs WNL", "routine", "no acute complaints"
- **Disease notes:** medically specific — "leukocytosis", "pallor", "syncope", "night sweats", "haematology referral", "genetics referral"

This means even TF-IDF will work well here — the rare medical terms are highly discriminative tokens. A sentence transformer adds value mainly for semantic equivalence (e.g., "haematology referral" ≈ "flow cytometry ordered") but isn't strictly necessary for good AUROC.

---

## Predicted Ablation Result

When you run Experiment 1 from the README:

| Configuration | Expected AUROC |
|---|---|
| Structured features only | ~0.82–0.87 |
| + Interaction features (shock index, MAP) | +0.02–0.04 |
| + TF-IDF notes | +0.03–0.06 |
| + Sentence transformer embeddings | +0.01–0.02 over TF-IDF |

The notes boost should be most visible in **recall for autoimmune and hematologic archetypes** — exactly the ones where symptoms (rash, night sweats, weight loss) appear in text but have no structured column. Cardiac syndrome recall will barely change because troponin already dominates.

---

## Summary Principle

> **Text matters when the disease manifests in symptoms a clinician would write down but a lab machine would not measure.**

- **Autoimmune:** rash, joint stiffness → no column.
- **Hematologic:** night sweats, weight loss (B-symptoms) → no column.
- **Mitochondrial:** exercise intolerance, cognitive fog → no column.
- **Cardiac:** troponin speaks for itself → text is redundant.
