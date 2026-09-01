"""ML Model Trainer, Cross-Validation, and Serialization Engine for WaterTrack."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from app.features.ml.dataset import (
    generate_hydration_dataset,
    generate_intake_trajectory_dataset,
)
from app.features.ml.pipeline import (
    HYDRATION_CATEGORICAL_FEATURES,
    HYDRATION_NUMERICAL_FEATURES,
    build_dehydration_risk_pipeline,
    build_hydration_goal_pipeline,
    build_intake_forecast_pipeline,
    build_smart_reminder_pipeline,
)

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def train_all_models(
    n_samples: int = 5000,
    save_artifacts: bool = True,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    """Train all 4 hydration ML models, evaluate test performance metrics, and

    optionally save joblib artifacts to disk.
    """
    target_dir = artifacts_dir or ARTIFACTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Beginning ML model training with %d synthetic physiological samples...",
        n_samples,
    )

    # 1. Dataset Generation
    daily_df = generate_hydration_dataset(n_samples=n_samples, random_state=42)
    trajectory_df = generate_intake_trajectory_dataset(
        n_samples=n_samples, random_state=42
    )

    results: dict[str, Any] = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": n_samples,
        "models": {},
    }

    # ==========================================
    # Model 1: Hydration Goal Regressor
    # ==========================================
    goal_features = (
        HYDRATION_NUMERICAL_FEATURES + HYDRATION_CATEGORICAL_FEATURES
    )
    X_goal = daily_df[goal_features]
    y_goal = daily_df["optimal_daily_intake_ml"]

    X_train_g, X_test_g, y_train_g, y_test_g = train_test_split(
        X_goal, y_goal, test_size=0.2, random_state=42
    )

    goal_pipeline = build_hydration_goal_pipeline()
    goal_pipeline.fit(X_train_g, y_train_g)
    y_pred_g = goal_pipeline.predict(X_test_g)

    r2_g = float(r2_score(y_test_g, y_pred_g))
    mae_g = float(mean_absolute_error(y_test_g, y_pred_g))
    rmse_g = float(np.sqrt(mean_squared_error(y_test_g, y_pred_g)))

    # Extract feature importances
    preprocessor_g = goal_pipeline.named_steps["preprocessor"]
    regressor_g = goal_pipeline.named_steps["regressor"]
    ohe_names = (
        preprocessor_g.named_transformers_["cat"]
        .get_feature_names_out(HYDRATION_CATEGORICAL_FEATURES)
        .tolist()
    )
    all_feature_names_g = HYDRATION_NUMERICAL_FEATURES + ohe_names
    importances_g = regressor_g.feature_importances_
    top_features_g = sorted(
        [
            {"feature": f, "importance": round(float(imp), 4)}
            for f, imp in zip(all_feature_names_g, importances_g)
        ],
        key=lambda x: x["importance"],
        reverse=True,
    )[:8]

    results["models"]["hydration_goal"] = {
        "type": "GradientBoostingRegressor",
        "metrics": {
            "r2_score": round(r2_g, 4),
            "mae_ml": round(mae_g, 2),
            "rmse_ml": round(rmse_g, 2),
        },
        "top_features": top_features_g,
    }

    # ==========================================
    # Model 2: Dehydration Risk Classifier
    # ==========================================
    from app.features.ml.pipeline import (
        RISK_CATEGORICAL_FEATURES,
        RISK_NUMERICAL_FEATURES,
    )

    risk_features = RISK_NUMERICAL_FEATURES + RISK_CATEGORICAL_FEATURES
    X_risk = trajectory_df[risk_features]
    y_risk = trajectory_df["risk_label"]

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X_risk, y_risk, test_size=0.2, random_state=42, stratify=y_risk
    )

    risk_pipeline = build_dehydration_risk_pipeline()
    risk_pipeline.fit(X_train_r, y_train_r)
    y_pred_r = risk_pipeline.predict(X_test_r)

    acc_r = float(accuracy_score(y_test_r, y_pred_r))
    f1_r = float(f1_score(y_test_r, y_pred_r, average="weighted"))
    prec_r = float(precision_score(y_test_r, y_pred_r, average="weighted"))
    rec_r = float(recall_score(y_test_r, y_pred_r, average="weighted"))

    results["models"]["dehydration_risk"] = {
        "type": "GradientBoostingClassifier",
        "classes": risk_pipeline.classes_.tolist(),
        "metrics": {
            "accuracy": round(acc_r, 4),
            "f1_score": round(f1_r, 4),
            "precision": round(prec_r, 4),
            "recall": round(rec_r, 4),
        },
    }

    # ==========================================
    # Model 3: Smart Reminder Timing Model
    # ==========================================
    from app.features.ml.pipeline import (
        REMINDER_CATEGORICAL_FEATURES,
        REMINDER_NUMERICAL_FEATURES,
    )

    rem_features = (
        REMINDER_NUMERICAL_FEATURES + REMINDER_CATEGORICAL_FEATURES
    )
    X_rem = trajectory_df[rem_features]
    y_rem = trajectory_df["next_reminder_min"]

    X_train_rem, X_test_rem, y_train_rem, y_test_rem = train_test_split(
        X_rem, y_rem, test_size=0.2, random_state=42
    )

    reminder_pipeline = build_smart_reminder_pipeline()
    reminder_pipeline.fit(X_train_rem, y_train_rem)
    y_pred_rem = reminder_pipeline.predict(X_test_rem)

    r2_rem = float(r2_score(y_test_rem, y_pred_rem))
    mae_rem = float(mean_absolute_error(y_test_rem, y_pred_rem))

    results["models"]["smart_reminder"] = {
        "type": "GradientBoostingRegressor",
        "metrics": {
            "r2_score": round(r2_rem, 4),
            "mae_minutes": round(mae_rem, 2),
        },
    }

    # ==========================================
    # Model 4: Intake Trajectory Forecaster
    # ==========================================
    from app.features.ml.pipeline import (
        FORECAST_CATEGORICAL_FEATURES,
        FORECAST_NUMERICAL_FEATURES,
    )

    fc_features = FORECAST_NUMERICAL_FEATURES + FORECAST_CATEGORICAL_FEATURES
    X_fc = trajectory_df[fc_features]
    y_fc = trajectory_df["end_of_day_forecast_ml"]

    X_train_fc, X_test_fc, y_train_fc, y_test_fc = train_test_split(
        X_fc, y_fc, test_size=0.2, random_state=42
    )

    forecast_pipeline = build_intake_forecast_pipeline()
    forecast_pipeline.fit(X_train_fc, y_train_fc)
    y_pred_fc = forecast_pipeline.predict(X_test_fc)

    r2_fc = float(r2_score(y_test_fc, y_pred_fc))
    mae_fc = float(mean_absolute_error(y_test_fc, y_pred_fc))

    results["models"]["intake_forecast"] = {
        "type": "RandomForestRegressor",
        "metrics": {
            "r2_score": round(r2_fc, 4),
            "mae_ml": round(mae_fc, 2),
        },
    }

    # ==========================================
    # Save Artifacts to Disk
    # ==========================================
    if save_artifacts:
        joblib.dump(
            goal_pipeline, target_dir / "hydration_goal_model.joblib", compress=3
        )
        joblib.dump(
            risk_pipeline,
            target_dir / "dehydration_risk_model.joblib",
            compress=3,
        )
        joblib.dump(
            reminder_pipeline,
            target_dir / "smart_reminder_model.joblib",
            compress=3,
        )
        joblib.dump(
            forecast_pipeline,
            target_dir / "intake_forecast_model.joblib",
            compress=3,
        )

        with open(target_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        logger.info(
            "Successfully serialized all 4 ML models to %s", str(target_dir)
        )

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = train_all_models(n_samples=5000)
    print(json.dumps(res, indent=2))
