# ML Module — Safe Driving Speed

## What's here
- `generate_data.py` — physics-informed synthetic dataset (braking-distance formula; see docstring for the full derivation)
- `train.py` — trains Decision Tree, Random Forest, Gradient Boosting, and XGBoost; picks the best by test-set R²/MAE; saves the winner + a SHAP explainer
- `evaluate.py` — buckets predictions into Low/Medium/High risk and reports accuracy, precision, recall, F1, and a confusion matrix on that classification
- `model_artifacts/` — output of running the above (already included, pre-trained)
- `data/driving_conditions.csv` — the generated dataset (already included)

## How to run it yourself
```bash
pip install -r requirements.txt
python generate_data.py     # optional — data/ already has a generated set
python train.py             # trains all 4 models, saves the winner
python evaluate.py          # risk-level classification report
```

## Results from this run

| Model | MAE (km/h) | RMSE | R² | 5-fold CV R² |
|---|---|---|---|---|
| Decision Tree | 2.73 | 3.46 | 0.9745 | 0.9742 |
| Random Forest | 2.54 | 3.18 | 0.9785 | 0.9793 |
| **Gradient Boosting (winner)** | **2.47** | **3.09** | **0.9797** | **0.9803** |
| XGBoost | 2.50 | 3.13 | 0.9791 | 0.9799 |

Derived risk-level classification (Low/Medium/High) on the same test set:
**95.4% accuracy**, weighted F1 0.953. The High-risk class (rarer, fewer examples) has the lowest F1 at 0.82 — worth mentioning honestly in your report rather than only citing the headline accuracy.

## How this plugs into the backend (Phase 2)
Copy or symlink this whole `ml_model/model_artifacts/` folder so the paths in `backend/app/core/config.py` resolve:
```
MODEL_ARTIFACT_PATH=ml_model/model_artifacts/best_model.joblib
SHAP_EXPLAINER_PATH=ml_model/model_artifacts/explainer.joblib
```
`app/services/ml_service.py` loads both once at startup and uses the exact same `FEATURE_ORDER` and encoding maps (`road_condition` → code, `traffic_density` → code) as `generate_data.py` — this consistency is what makes predictions valid; if you ever change the encoding in one file, change it in both.

## Retraining
Re-run `python train.py` any time — it regenerates `best_model.joblib`, `explainer.joblib`, and `comparison_report.json`. The Phase 2 admin endpoint (`POST /api/admin/model/retrain`, to be wired up in a later phase) will eventually call this pipeline automatically; for now it's manual.

## Honest limitations
- The dataset is synthetic (physics-derived, not from real accident/telemetry data). It's a defensible, explainable stand-in for a final-year project, but note this clearly in your report — don't present it as real-world collected data.
- Risk thresholds (Low ≥45 km/h, Medium ≥25, High <25) are simple fixed cutoffs, not learned. They're intentionally easy to justify in a viva but could be tuned later.
