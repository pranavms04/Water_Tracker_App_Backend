"""Physiological and behavioral hydration dataset generator for ML model training.

Generates realistic hydration, environmental, and behavioral datasets based on
ACSM (American College of Sports Medicine) and EFSA (European Food Safety Authority)
hydration guidelines.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_hydration_dataset(
    n_samples: int = 5000, random_state: int = 42
) -> pd.DataFrame:
    """Generate a synthetic dataset of physiological, environmental, and behavioral
    metrics for training daily hydration regression and classification models.
    """
    rng = np.random.default_rng(random_state)

    # 1. Demographics & Physiology
    weight_kg = rng.uniform(45.0, 120.0, size=n_samples)
    age = rng.integers(16, 75, size=n_samples)
    gender_choices = ["male", "female", "other"]
    gender = rng.choice(gender_choices, p=[0.48, 0.48, 0.04], size=n_samples)
    activity_choices = ["sedentary", "light", "moderate", "very_active"]
    activity_level = rng.choice(
        activity_choices, p=[0.25, 0.35, 0.28, 0.12], size=n_samples
    )

    # 2. Activity & Lifestyle
    exercise_duration_min = np.where(
        activity_level == "sedentary",
        rng.uniform(0.0, 15.0, size=n_samples),
        np.where(
            activity_level == "light",
            rng.uniform(15.0, 45.0, size=n_samples),
            np.where(
                activity_level == "moderate",
                rng.uniform(30.0, 75.0, size=n_samples),
                rng.uniform(60.0, 150.0, size=n_samples),
            ),
        ),
    )
    daily_steps = np.clip(
        rng.normal(
            loc=np.where(
                activity_level == "sedentary",
                4000,
                np.where(
                    activity_level == "light",
                    7500,
                    np.where(activity_level == "moderate", 11000, 16000),
                ),
            ),
            scale=1800,
        ),
        1000,
        30000,
    ).astype(int)

    caffeine_intake_mg = np.clip(
        rng.exponential(scale=120.0, size=n_samples), 0, 600
    )

    # 3. Environment & Weather
    ambient_temp_c = rng.uniform(8.0, 42.0, size=n_samples)
    humidity_pct = rng.uniform(20.0, 95.0, size=n_samples)
    season_choices = ["winter", "spring", "summer", "fall"]
    season = rng.choice(season_choices, size=n_samples)

    # 4. Behavioral & Habit metrics
    past_adherence_rate = np.clip(
        rng.beta(a=5.0, b=2.0, size=n_samples), 0.1, 1.0
    )
    streak_days = rng.geometric(p=0.15, size=n_samples) - 1

    # 5. Scientific Formulation for Optimal Daily Water Intake (ml)
    # Base = weight_kg * 35.0 ml
    base_ml = weight_kg * 35.0

    # Gender adjustments: Male (+200ml), Female (-100ml), Other (0ml)
    gender_adj = np.where(
        gender == "male", 200.0, np.where(gender == "female", -100.0, 0.0)
    )

    # Age adjustment: Metabolic and kidney function variation
    age_adj = np.where(age > 60, -80.0, np.where(age < 25, 60.0, 0.0))

    # Activity adjustment: baseline activity multiplier
    act_adj = np.where(
        activity_level == "sedentary",
        0.0,
        np.where(
            activity_level == "light",
            250.0,
            np.where(activity_level == "moderate", 550.0, 900.0),
        ),
    )

    # Sweat loss replacement: ~10-12 ml per minute of elevated exercise
    exercise_adj = exercise_duration_min * 10.5

    # Step expenditure hydration: ~30 ml per 1,000 steps above 4,000
    step_adj = np.maximum(0.0, (daily_steps - 4000.0) / 1000.0) * 32.0

    # Ambient Temperature adjustment
    temp_adj = np.where(
        ambient_temp_c < 15.0,
        (ambient_temp_c - 15.0) * 12.0,
        np.where(
            ambient_temp_c <= 25.0,
            0.0,
            np.where(
                ambient_temp_c <= 32.0,
                (ambient_temp_c - 25.0) * 42.0,
                300.0 + (ambient_temp_c - 32.0) * 65.0,
            ),
        ),
    )

    # Humidity adjustment (evaporative cooling and respiratory loss)
    humidity_adj = np.where(
        humidity_pct < 30.0, 120.0, np.where(humidity_pct > 75.0, 180.0, 0.0)
    )

    # Caffeine mild diuretic compensation (0.4 ml water per mg caffeine)
    caffeine_adj = caffeine_intake_mg * 0.4

    # Raw intake target calculation
    raw_optimal_ml = (
        base_ml
        + gender_adj
        + age_adj
        + act_adj
        + exercise_adj
        + step_adj
        + temp_adj
        + humidity_adj
        + caffeine_adj
    )

    # Safety clamps: min 1200ml or 25ml/kg, max 6000ml or 55ml/kg
    min_safe = np.maximum(weight_kg * 25.0, 1200.0)
    max_safe = np.minimum(weight_kg * 55.0, 6000.0)

    # Add realistic physiological noise (Gaussian, std=30ml)
    noise = rng.normal(loc=0.0, scale=30.0, size=n_samples)
    clamped_optimal_ml = np.clip(raw_optimal_ml + noise, min_safe, max_safe)

    # Round to nearest 10 ml
    optimal_daily_intake_ml = np.round(clamped_optimal_ml, -1)

    df = pd.DataFrame(
        {
            "weight_kg": np.round(weight_kg, 1),
            "age": age,
            "gender": gender,
            "activity_level": activity_level,
            "exercise_duration_min": np.round(exercise_duration_min, 1),
            "daily_steps": daily_steps,
            "caffeine_intake_mg": np.round(caffeine_intake_mg, 1),
            "ambient_temp_c": np.round(ambient_temp_c, 1),
            "humidity_pct": np.round(humidity_pct, 1),
            "season": season,
            "past_adherence_rate": np.round(past_adherence_rate, 2),
            "streak_days": streak_days,
            "optimal_daily_intake_ml": optimal_daily_intake_ml,
        }
    )

    return df


def generate_intake_trajectory_dataset(
    n_samples: int = 8000, random_state: int = 42
) -> pd.DataFrame:
    """Generate intraday dataset for real-time dehydration risk classification and
    hourly trajectory forecasting.
    """
    rng = np.random.default_rng(random_state)

    # Base daily dataset
    daily_df = generate_hydration_dataset(
        n_samples=n_samples, random_state=random_state
    )

    # Current hour of observation (6 AM to 23 PM)
    current_hour = rng.integers(6, 24, size=n_samples)
    daily_goal_ml = daily_df["optimal_daily_intake_ml"].values

    # Active waking day elapsed ratio (from 7:00 to 22:00 = 15 active hours)
    active_start_hour = 7.0
    active_end_hour = 22.0
    active_hours_total = active_end_hour - active_start_hour
    elapsed_active_hours = np.clip(
        current_hour - active_start_hour, 0.0, active_hours_total
    )
    expected_fraction_consumed = elapsed_active_hours / active_hours_total

    # User pace factor (some users drink ahead, some lag behind)
    user_behavior_type = rng.choice(
        ["ahead", "on_track", "lagging", "critical_deficit"],
        p=[0.20, 0.45, 0.25, 0.10],
        size=n_samples,
    )

    pace_multipliers = np.where(
        user_behavior_type == "ahead",
        rng.uniform(1.10, 1.35, size=n_samples),
        np.where(
            user_behavior_type == "on_track",
            rng.uniform(0.90, 1.10, size=n_samples),
            np.where(
                user_behavior_type == "lagging",
                rng.uniform(0.55, 0.85, size=n_samples),
                rng.uniform(0.15, 0.50, size=n_samples),
            ),
        ),
    )

    # Actual intake consumed so far (ml)
    intake_so_far_ml = np.clip(
        daily_goal_ml * expected_fraction_consumed * pace_multipliers
        + rng.normal(0, 50, size=n_samples),
        0.0,
        daily_goal_ml * 1.4,
    )
    intake_so_far_ml = np.round(intake_so_far_ml, -1)

    # Deficit or surplus compared to linear schedule
    scheduled_intake_ml = daily_goal_ml * expected_fraction_consumed
    intake_deficit_ml = scheduled_intake_ml - intake_so_far_ml

    # Hours since last drink (0.2 to 6.0 hours)
    hours_since_last_drink = np.clip(
        np.where(
            user_behavior_type == "ahead",
            rng.uniform(0.2, 1.5, size=n_samples),
            np.where(
                user_behavior_type == "on_track",
                rng.uniform(0.5, 2.5, size=n_samples),
                np.where(
                    user_behavior_type == "lagging",
                    rng.uniform(2.0, 4.5, size=n_samples),
                    rng.uniform(3.5, 7.0, size=n_samples),
                ),
            ),
        ),
        0.1,
        8.0,
    )

    # Dehydration Risk Label:
    # 0 = "low" (Optimal hydration pace)
    # 1 = "moderate" (Slightly behind pace or warm weather deficit)
    # 2 = "high" (Significant deficit or long gap between drinks)
    safe_scheduled_ml = np.maximum(scheduled_intake_ml, 1.0)
    completion_ratio = np.where(
        scheduled_intake_ml > 0, intake_so_far_ml / safe_scheduled_ml, 1.0
    )

    risk_score = (
        (1.0 - np.clip(completion_ratio, 0.0, 1.5)) * 50.0
        + (hours_since_last_drink / 4.0) * 30.0
        + (
            np.maximum(0.0, daily_df["ambient_temp_c"].values - 25.0) / 15.0
        )
        * 20.0
    )

    risk_label = np.where(
        risk_score < 30.0, "low", np.where(risk_score < 60.0, "moderate", "high")
    )

    # Recommended next sip (ml)
    remaining_ml = np.maximum(0.0, daily_goal_ml - intake_so_far_ml)
    remaining_hours = np.maximum(1.0, active_end_hour - current_hour)
    recommended_sip_ml = np.clip(
        np.round((remaining_ml / remaining_hours) * (45.0 / 60.0) / 10.0) * 10,
        150.0,
        450.0,
    )

    # Recommended next reminder in minutes
    next_reminder_min = np.clip(
        np.round(
            np.where(
                risk_label == "high",
                rng.uniform(15.0, 30.0, size=n_samples),
                np.where(
                    risk_label == "moderate",
                    rng.uniform(35.0, 60.0, size=n_samples),
                    rng.uniform(60.0, 120.0, size=n_samples),
                ),
            )
        ),
        15,
        180,
    ).astype(int)

    # Predicted end-of-day total (ml)
    end_of_day_forecast_ml = np.clip(
        intake_so_far_ml
        + remaining_hours
        * (intake_so_far_ml / np.maximum(1.0, elapsed_active_hours))
        * (0.8 + 0.2 * daily_df["past_adherence_rate"].values),
        intake_so_far_ml,
        daily_goal_ml * 1.3,
    )
    end_of_day_forecast_ml = np.round(end_of_day_forecast_ml, -1)

    daily_df["current_hour"] = current_hour
    daily_df["intake_so_far_ml"] = intake_so_far_ml
    daily_df["daily_goal_ml"] = daily_goal_ml
    daily_df["intake_deficit_ml"] = np.round(intake_deficit_ml, 1)
    daily_df["hours_since_last_drink"] = np.round(hours_since_last_drink, 1)
    daily_df["risk_label"] = risk_label
    daily_df["recommended_sip_ml"] = recommended_sip_ml
    daily_df["next_reminder_min"] = next_reminder_min
    daily_df["end_of_day_forecast_ml"] = end_of_day_forecast_ml

    return daily_df
