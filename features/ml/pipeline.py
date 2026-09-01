"""Machine Learning Pipelines and Preprocessing Transformers for WaterTrack."""

from __future__ import annotations

from typing import Tuple
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Feature sets for the Hydration Target Regressor
HYDRATION_NUMERICAL_FEATURES = [
    "weight_kg",
    "age",
    "exercise_duration_min",
    "daily_steps",
    "caffeine_intake_mg",
    "ambient_temp_c",
    "humidity_pct",
    "past_adherence_rate",
    "streak_days",
]
HYDRATION_CATEGORICAL_FEATURES = ["gender", "activity_level", "season"]

# Feature sets for the Dehydration Risk Classifier
RISK_NUMERICAL_FEATURES = [
    "weight_kg",
    "age",
    "exercise_duration_min",
    "daily_steps",
    "ambient_temp_c",
    "humidity_pct",
    "current_hour",
    "intake_so_far_ml",
    "daily_goal_ml",
    "intake_deficit_ml",
    "hours_since_last_drink",
    "streak_days",
]
RISK_CATEGORICAL_FEATURES = ["gender", "activity_level"]

# Feature sets for the Smart Reminder Timing Model
REMINDER_NUMERICAL_FEATURES = [
    "weight_kg",
    "ambient_temp_c",
    "current_hour",
    "intake_so_far_ml",
    "daily_goal_ml",
    "intake_deficit_ml",
    "hours_since_last_drink",
]
REMINDER_CATEGORICAL_FEATURES = ["activity_level"]

# Feature sets for the Intake Forecaster
FORECAST_NUMERICAL_FEATURES = [
    "weight_kg",
    "ambient_temp_c",
    "current_hour",
    "intake_so_far_ml",
    "daily_goal_ml",
    "intake_deficit_ml",
    "past_adherence_rate",
    "streak_days",
]
FORECAST_CATEGORICAL_FEATURES = ["activity_level"]


def build_hydration_goal_pipeline() -> Pipeline:
    """Build scikit-learn pipeline for optimal daily hydration target regression."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                StandardScaler(),
                HYDRATION_NUMERICAL_FEATURES,
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                HYDRATION_CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    regressor = GradientBoostingRegressor(
        n_estimators=120,
        learning_rate=0.08,
        max_depth=4,
        random_state=42,
    )

    return Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])


def build_dehydration_risk_pipeline() -> Pipeline:
    """Build scikit-learn pipeline for real-time dehydration risk classification."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), RISK_NUMERICAL_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                RISK_CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    classifier = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42,
    )

    return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])


def build_smart_reminder_pipeline() -> Pipeline:
    """Build scikit-learn pipeline for dynamic reminder delay estimation."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), REMINDER_NUMERICAL_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                REMINDER_CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    regressor = GradientBoostingRegressor(
        n_estimators=80,
        learning_rate=0.1,
        max_depth=3,
        random_state=42,
    )

    return Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])


def build_intake_forecast_pipeline() -> Pipeline:
    """Build scikit-learn pipeline for day-end cumulative intake trajectory forecasting."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), FORECAST_NUMERICAL_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                FORECAST_CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    regressor = RandomForestRegressor(
        n_estimators=80,
        max_depth=6,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])
