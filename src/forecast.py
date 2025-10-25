# src/forecast.py
import numpy as np
import pandas as pd
from typing import Literal, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

# Optional Holt-Winters
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing  # optional
    _HAS_SM = True
except Exception:
    _HAS_SM = False

# ------------------ generic series forecast utilities -----------------------
def _fit_linear(y: np.ndarray) -> Tuple[LinearRegression, float]:
    """Fit linear regression with improved error handling."""
    X = np.arange(len(y)).reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    preds = model.predict(X)
    # Use RMSE for standard error
    mse = np.mean((y - preds) ** 2)
    se = float(np.sqrt(mse)) if len(y) > 1 else float(np.std(y)) if len(y) > 0 else 0.0
    return model, se

def _fit_polynomial(y: np.ndarray, degree: int = 2) -> Tuple[Pipeline, float]:
    """Fit polynomial regression for non-linear trends."""
    if len(y) < degree + 2:
        return _fit_linear(y)
    
    X = np.arange(len(y)).reshape(-1, 1)
    poly_model = Pipeline([
        ('poly', PolynomialFeatures(degree=degree)),
        ('linear', LinearRegression())
    ])
    poly_model.fit(X, y)
    preds = poly_model.predict(X)
    mse = np.mean((y - preds) ** 2)
    se = float(np.sqrt(mse)) if len(y) > 1 else float(np.std(y)) if len(y) > 0 else 0.0
    return poly_model, se

def _predict_linear(n_hist: int, steps: int, model: LinearRegression):
    Xf = np.arange(n_hist, n_hist + steps).reshape(-1, 1)
    return model.predict(Xf)

def _predict_polynomial(n_hist: int, steps: int, model: Pipeline):
    Xf = np.arange(n_hist, n_hist + steps).reshape(-1, 1)
    return model.predict(Xf)

def _smooth_data(values: np.ndarray, window: int = 3) -> np.ndarray:
    """Apply moving average smoothing to reduce noise."""
    if len(values) < window:
        return values
    smoothed = np.convolve(values, np.ones(window)/window, mode='same')
    # Keep edges original to avoid edge effects
    smoothed[0] = values[0]
    smoothed[-1] = values[-1]
    return smoothed

def forecast_series(values: np.ndarray, steps: int, algo: Literal["auto","holt","linear","poly"] = "auto"):
    """
    Improved univariate forecast with multiple algorithms.
    - auto: choose best method based on data characteristics
    - holt: Holt-Winters exponential smoothing
    - linear: linear regression
    - poly: polynomial regression (degree 2)
    Returns (future_preds, stderr).
    """
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return np.array([]), 0.0
    
    # Remove outliers using IQR method for better accuracy
    if len(values) > 4:
        q1, q3 = np.percentile(values, [25, 75])
        iqr = q3 - q1
        if iqr > 0:  # Only filter if there's variation
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            filtered = values[(values >= lower_bound) & (values <= upper_bound)]
            if len(filtered) > 0:
                values = filtered

    # Apply smoothing for noisy data
    if len(values) >= 5:
        values = _smooth_data(values, window=min(3, len(values) // 2))

    # Auto mode: choose best algorithm
    if algo == "auto":
        if _HAS_SM and len(values) >= 6:
            algo = "holt"
        elif len(values) >= 4:
            # Check if data is non-linear
            X = np.arange(len(values))
            linear_model = LinearRegression().fit(X.reshape(-1, 1), values)
            linear_preds = linear_model.predict(X.reshape(-1, 1))
            linear_mse = np.mean((values - linear_preds) ** 2)
            
            poly_model, _ = _fit_polynomial(values, degree=2)
            poly_preds = poly_model.predict(X.reshape(-1, 1))
            poly_mse = np.mean((values - poly_preds) ** 2)
            
            # Use polynomial if it's significantly better
            if poly_mse < linear_mse * 0.8:
                algo = "poly"
            else:
                algo = "linear"
        else:
            algo = "linear"

    # Holt-Winters
    if algo == "holt" and _HAS_SM and len(values) >= 6:
        try:
            model = ExponentialSmoothing(
                values, 
                trend="add", 
                seasonal=None,
                initialization_method="estimated"
            ).fit(optimized=True)
            preds_in = model.fittedvalues
            se = float(np.sqrt(np.mean((values - preds_in) ** 2))) if len(values) > 1 else float(np.std(values)) if len(values) > 0 else 0.0
            preds_out = model.forecast(steps)
            # Clip predictions to reasonable bounds
            min_val, max_val = np.min(values), np.max(values)
            range_val = max_val - min_val
            preds_out = np.clip(preds_out, min_val - 0.5 * range_val, max_val + 0.5 * range_val)
            return np.asarray(preds_out), se
        except Exception:
            pass  # fall back to linear

    # Polynomial regression
    if algo == "poly" and len(values) >= 4:
        try:
            poly_model, se = _fit_polynomial(values, degree=min(2, len(values) - 2))
            preds_out = _predict_polynomial(len(values), steps, poly_model)
            # Clip to reasonable bounds
            min_val, max_val = np.min(values), np.max(values)
            range_val = max_val - min_val
            preds_out = np.clip(preds_out, min_val - 0.5 * range_val, max_val + 0.5 * range_val)
            return np.asarray(preds_out), se
        except Exception:
            pass  # fall back to linear

    # Linear regression (fallback)
    lr, se = _fit_linear(values)
    preds_out = _predict_linear(len(values), steps, lr)
    # Clip to reasonable bounds
    min_val, max_val = np.min(values), np.max(values)
    range_val = max_val - min_val
    preds_out = np.clip(preds_out, min_val - 0.5 * range_val, max_val + 0.5 * range_val)
    return np.asarray(preds_out), se

# ------------------ 1RM forecast (weekly) -----------------------------------
def forecast_1rm(weekly_best_df: pd.DataFrame, steps: int = 8,
                 algo: Literal["auto","holt","linear"] = "auto") -> pd.DataFrame:
    df = weekly_best_df.dropna(subset=["best_1rm"]).reset_index(drop=True).copy()
    if df.empty:
        return pd.DataFrame(columns=["t","value","kind"])
    y = df["best_1rm"].to_numpy()
    actual = pd.DataFrame({"t": np.arange(len(df)), "value": y, "kind": "actual"})
    preds, se = forecast_series(y, steps, algo=("holt" if algo=="holt" else ("linear" if algo=="linear" else "auto")))
    future = pd.DataFrame({
        "t": np.arange(len(df), len(df) + steps),
        "value": preds,
        "lower": preds - 1.96 * se,
        "upper": preds + 1.96 * se,
        "kind": "pred",
    })
    return pd.concat([actual, future], ignore_index=True)

# ------------------ weight forecasts ----------------------------------------
def forecast_weight_confidence(bw_df: pd.DataFrame, horizon_weeks: int = 12,
                               algo: Literal["auto","holt","linear"] = "auto") -> pd.DataFrame:
    if bw_df.empty or "body_weight_lbs" not in bw_df.columns:
        return pd.DataFrame()
    d = bw_df.dropna(subset=["body_weight_lbs"]).copy().sort_values("date").reset_index(drop=True)
    y = d["body_weight_lbs"].to_numpy()
    preds, se = forecast_series(y, steps=horizon_weeks, algo=algo)
    last_date = d["date"].iloc[-1]
    future_dates = [last_date + pd.Timedelta(days=7 * i) for i in range(1, horizon_weeks + 1)]
    actual = pd.DataFrame({"date": d["date"], "value": y, "lower": y, "upper": y, "kind": "actual"})
    future = pd.DataFrame({
        "date": future_dates, "value": preds,
        "lower": preds - 1.96 * se, "upper": preds + 1.96 * se, "kind": "pred",
    })
    return pd.concat([actual, future], ignore_index=True)

def forecast_weight_realistic(
    bw_df: pd.DataFrame,
    horizon_weeks: int = 12,
    target_rate_pct: float | None = None,   # -0.7 lose / 0 maintain / +0.5 gain, etc.
    recent_weeks: int = 6,
    max_abs_rate_pct: float = 1.5
) -> pd.DataFrame:
    """Improved weight forecasting with better trend detection and confidence intervals."""
    if bw_df.empty or "body_weight_lbs" not in bw_df.columns or "date" not in bw_df.columns:
        return pd.DataFrame(columns=["date","value","lower","upper","kind"])

    d = bw_df.dropna(subset=["date","body_weight_lbs"]).copy().sort_values("date").reset_index(drop=True)
    if d.empty:
        return pd.DataFrame(columns=["date","value","lower","upper","kind"])

    # Use more data points for better trend estimation
    t = (d["date"] - d["date"].iloc[0]).dt.days.to_numpy() / 7.0
    y = d["body_weight_lbs"].to_numpy(dtype=float)
    curr = float(y[-1])

    # Use weighted regression giving more weight to recent data
    n = min(len(y), max(3, recent_weeks))
    recent_indices = np.arange(max(0, len(y) - n), len(y))
    t_recent = t[recent_indices]
    y_recent = y[recent_indices]
    
    # Exponential weights (more recent = higher weight)
    weights = np.exp(np.linspace(-2, 0, len(y_recent)))
    weights = weights / weights.sum()
    
    # Weighted least squares
    X = np.vstack([np.ones(len(t_recent)), t_recent]).T
    W = np.diag(weights)
    beta = np.linalg.solve(X.T @ W @ X, X.T @ W @ y_recent)
    slope_est = float(beta[1])  # lbs/week

    if target_rate_pct is not None and abs(target_rate_pct) > 1e-9:
        slope = curr * (target_rate_pct / 100.0)
    else:
        slope = slope_est

    # Clamp to realistic rates
    max_abs_lbs_per_week = max_abs_rate_pct / 100.0 * curr
    slope = float(np.clip(slope, -max_abs_lbs_per_week, max_abs_lbs_per_week))

    last_date = d["date"].iloc[-1]
    future_dates = [last_date + pd.Timedelta(days=7*i) for i in range(1, horizon_weeks + 1)]
    t_last = t[-1]
    tf = np.arange(t_last + 1, t_last + horizon_weeks + 1)
    preds = curr + slope * (tf - t_last)

    # Improved confidence intervals using weighted residuals
    resid = y_recent - (beta[0] + beta[1] * t_recent)
    weighted_resid = resid * np.sqrt(weights)
    mse = np.mean(weighted_resid**2)
    se = float(np.sqrt(mse)) if len(resid) > 1 else float(np.std(y)) if len(y) > 1 else 1.0
    
    # Expand CI for longer horizons (uncertainty increases with time)
    horizon_multiplier = 1.0 + 0.1 * np.arange(1, horizon_weeks + 1)
    lower = preds - 1.96 * se * horizon_multiplier
    upper = preds + 1.96 * se * horizon_multiplier

    actual = pd.DataFrame({"date": d["date"], "value": y, "lower": y, "upper": y, "kind": "actual"})
    future = pd.DataFrame({"date": future_dates, "value": preds, "lower": lower, "upper": upper, "kind": "pred"})
    return pd.concat([actual, future], ignore_index=True)

# -------- energy-based helpers & forecast -----------------------------------
def estimate_tdee_msj(sex: str, age: int, height_cm: float, weight_kg: float, activity: str) -> float:
    s = 5 if sex.lower().startswith("m") else -161
    bmr = 10*weight_kg + 6.25*height_cm - 5*age + s
    mult = {"sedentary":1.2,"light":1.375,"moderate":1.55,"active":1.725,"very active":1.9}.get(activity.lower(), 1.55)
    return float(bmr * mult)

def calories_to_weight_change_kg(deficit_kcal: float, adapt: float = 0.75) -> float:
    return (deficit_kcal / 7700.0) * adapt

def daily_kcal_vs_tdee(meals_df: pd.DataFrame, tdee_kcal: float) -> pd.DataFrame:
    if meals_df.empty:
        return pd.DataFrame(columns=["date","intake_kcal","tdee_kcal","balance_kcal"])
    d = meals_df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce").dt.date
    g = d.groupby("date", as_index=False)["calories"].sum().rename(columns={"calories":"intake_kcal"})
    g["tdee_kcal"] = tdee_kcal
    g["balance_kcal"] = g["intake_kcal"] - g["tdee_kcal"]  # negative => deficit
    g["date"] = pd.to_datetime(g["date"])
    return g.sort_values("date")

def forecast_weight_energy(
    bw_df: pd.DataFrame,
    daily_balance: pd.DataFrame,
    horizon_weeks: int = 12,
    smooth_days: int = 7,
    max_abs_rate_pct: float = 1.5
) -> pd.DataFrame:
    if bw_df.empty or daily_balance.empty:
        return pd.DataFrame()
    d_w = bw_df.dropna(subset=["date","body_weight_lbs"]).copy().sort_values("date")
    d_w["date"] = pd.to_datetime(d_w["date"])
    curr_w_lbs = float(d_w["body_weight_lbs"].iloc[-1])
    curr_w_kg = curr_w_lbs / 2.20462

    db = daily_balance.copy().sort_values("date")
    db["balance_kcal_smooth"] = db["balance_kcal"].rolling(smooth_days, min_periods=1).mean()

    last_bal = float(db["balance_kcal_smooth"].iloc[-1])
    daily_kg = calories_to_weight_change_kg(last_bal)

    max_weekly_kg = (max_abs_rate_pct/100.0)*curr_w_kg
    daily_kg = float(np.clip(daily_kg, -max_weekly_kg/7.0, max_weekly_kg/7.0))

    last_date = d_w["date"].iloc[-1]
    future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 7*horizon_weeks + 1)]

    daily_vals_kg = curr_w_kg + daily_kg * np.arange(1, len(future_dates)+1)
    daily_vals_lbs = daily_vals_kg * 2.20462

    recent = d_w.tail(14)["body_weight_lbs"]
    sd = float(recent.std(ddof=1)) if len(recent) >= 2 else 1.0
    lower = daily_vals_lbs - 1.96*sd
    upper = daily_vals_lbs + 1.96*sd

    actual = pd.DataFrame({
        "date": d_w["date"], "value": d_w["body_weight_lbs"],
        "lower": d_w["body_weight_lbs"], "upper": d_w["body_weight_lbs"], "kind":"actual"
    })
    future = pd.DataFrame({
        "date": future_dates, "value": daily_vals_lbs,
        "lower": lower, "upper": upper, "kind":"pred"
    })
    wk = future.iloc[::7].reset_index(drop=True)
    return pd.concat([actual, wk], ignore_index=True)

# --------- optional multifeature forecast (calories + volume) ---------------
def _year_week_index(d: pd.Series) -> pd.Series:
    iso = d.dt.isocalendar()
    return iso.year.astype(int).astype(str) + "-W" + iso.week.astype(int).astype(str)

def forecast_weight_multifeature(
    bw_df: pd.DataFrame,
    meals_df: pd.DataFrame,
    workouts_df: pd.DataFrame,
    horizon_weeks: int = 12,
    future_calories: float | None = None,
    future_volume: float | None = None,
):
    if bw_df.empty or "body_weight_lbs" not in bw_df.columns:
        return pd.DataFrame()

    d_bw = bw_df.dropna(subset=["date","body_weight_lbs"]).copy()
    d_bw["date"] = pd.to_datetime(d_bw["date"])
    d_bw["yw"] = _year_week_index(d_bw["date"])
    y = d_bw.groupby("yw", as_index=False).agg(
        date=("date","max"),
        weight=("body_weight_lbs","mean")
    )

    if meals_df is not None and not meals_df.empty and "calories" in meals_df.columns:
        m = meals_df.copy()
        m["date"] = pd.to_datetime(m["date"], errors="coerce")
        m = m.dropna(subset=["date"])
        m["yw"] = _year_week_index(m["date"])
        wk_cals = m.groupby("yw", as_index=False)["calories"].sum().rename(columns={"calories":"weekly_calories"})
    else:
        wk_cals = pd.DataFrame(columns=["yw","weekly_calories"])

    if workouts_df is not None and not workouts_df.empty and "volume" in workouts_df.columns:
        w = workouts_df.copy()
        w["date"] = pd.to_datetime(w["date"], errors="coerce")
        w = w.dropna(subset=["date"])
        w["yw"] = _year_week_index(w["date"])
        wk_vol = w.groupby("yw", as_index=False)["volume"].sum().rename(columns={"volume":"weekly_volume"})
    else:
        wk_vol = pd.DataFrame(columns=["yw","weekly_volume"])

    df = y.merge(wk_cals, on="yw", how="left").merge(wk_vol, on="yw", how="left")
    df[["weekly_calories","weekly_volume"]] = df[["weekly_calories","weekly_volume"]].fillna(0.0)

    if len(df) < 4:
        last = df.iloc[-1]
        future_dates = [last["date"] + pd.Timedelta(days=7*i) for i in range(1, horizon_weeks+1)]
        out = pd.DataFrame({
            "date": pd.concat([df["date"], pd.Series(future_dates)]),
            "value": np.r_[df["weight"].to_numpy(), np.full(horizon_weeks, last["weight"])],
            "lower": np.r_[df["weight"].to_numpy(), np.full(horizon_weeks, last["weight"])],
            "upper": np.r_[df["weight"].to_numpy(), np.full(horizon_weeks, last["weight"])],
            "kind":  ["actual"]*len(df) + ["pred"]*horizon_weeks,
        })
        return out

    X = df[["weekly_calories","weekly_volume"]].to_numpy()
    yv = df["weight"].to_numpy()
    model = LinearRegression().fit(X, yv)
    preds_in = model.predict(X)
    se = float(np.sqrt(np.mean((yv - preds_in) ** 2))) if len(yv) > 1 else 0.0

    last_date = df["date"].iloc[-1]
    future_dates = [last_date + pd.Timedelta(days=7*i) for i in range(1, horizon_weeks+1)]

    if future_calories is None:
        future_calories = float(df["weekly_calories"].tail(4).mean())
    if future_volume is None:
        future_volume = float(df["weekly_volume"].tail(4).mean())

    Xf = np.c_[np.full(horizon_weeks, future_calories), np.full(horizon_weeks, future_volume)]
    preds_out = model.predict(Xf)

    actual = pd.DataFrame({"date": df["date"], "value": yv, "lower": yv, "upper": yv, "kind": "actual"})
    future = pd.DataFrame({"date": future_dates, "value": preds_out, "lower": preds_out - 1.96*se,
                           "upper": preds_out + 1.96*se, "kind": "pred"})
    return pd.concat([actual, future], ignore_index=True)
