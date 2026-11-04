"""
explain.py — SHAP-based explainability for the XGBoost failure model.
"""
from __future__ import annotations

from typing import List, Dict, Any

import pandas as pd

# SHAP is optional — if not installed, explain endpoint returns empty factors
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

from app.model import model, imputer, FEATURES


# ── Lazy singleton explainer ──────────────────────────────────────────────────
_explainer = None


def _get_explainer():
    global _explainer
    if _explainer is None and HAS_SHAP:
        _explainer = shap.TreeExplainer(model)
    return _explainer


# ── Public API ────────────────────────────────────────────────────────────────
def explain_prediction(features: dict, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Return top_k SHAP contributors for a single prediction.

    Parameters
    ----------
    features : dict   Raw feature dict (same as /predict input).
    top_k    : int    Number of top contributing features to return.

    Returns
    -------
    List of dicts: {feature, impact, direction, value}
    """
    df = pd.DataFrame([features]).reindex(columns=FEATURES)
    X = imputer.transform(df)

    explainer = _get_explainer()
    if explainer is None:
        # SHAP not available — return empty list
        return []

    shap_values = explainer.shap_values(X)

    # shap_values shape: (1, n_features)  — positive class values
    if hasattr(shap_values, "values"):
        sv = shap_values.values[0]
    elif isinstance(shap_values, list):
        # XGBoost binary: list of [neg_class, pos_class] or single array
        sv = shap_values[-1][0] if isinstance(shap_values[-1], list) else shap_values[0]
    else:
        sv = shap_values[0]

    # Build ranked list
    impacts = []
    for fname, shap_val, feat_val in zip(FEATURES, sv, df.values[0]):
        clean_val = None
        if feat_val is not None and not pd.isna(feat_val):
            try:
                clean_val = float(feat_val)
            except (ValueError, TypeError):
                clean_val = None

        direction = "Increases Risk" if shap_val > 0 else "Decreases Risk"
        effect = "increases risk" if shap_val > 0 else "decreases risk"
        impacts.append({
            "feature":        fname,
            "value":          clean_val if clean_val is not None else "N/A",
            "shap_value":     float(shap_val),
            "effect":         effect,
            "impact":         float(shap_val),
            "direction":      direction,
            "observed_value": clean_val,
        })

    # Sort by absolute impact descending
    impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)
    return impacts[:top_k]
