import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_weekly_volume(vol_df: pd.DataFrame):
    if vol_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=20))
        return fig

    grouped = (vol_df.groupby(["year_week"], as_index=False)["weekly_volume"].sum())

    fig = px.bar(grouped, x="year_week", y="weekly_volume",
                 title="Weekly Training Volume (all exercises)",
                 labels={"year_week": "Week", "weekly_volume": "kg-reps"})
    fig.update_layout(
        height=360,
        xaxis_tickangle=-35,
        bargap=0.2,
        template="plotly_dark",
        margin=dict(l=10, r=10, t=50, b=20),
    )
    return fig


def plot_1rm_actual_forecast(series_df: pd.DataFrame, title: str = "1RM (actual vs forecast)"):
    fig = go.Figure()
    if series_df.empty:
        fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=20))
        return fig

    actual = series_df[series_df["kind"] == "actual"]
    pred = series_df[series_df["kind"] == "pred"]

    fig.add_trace(go.Scatter(x=actual["t"], y=actual["value"], mode="lines+markers", name="Actual"))
    fig.add_trace(go.Scatter(x=pred["t"], y=pred["value"], mode="lines+markers", name="Forecast", line=dict(dash="dash")))

    # optional CI if present
    if {"lower","upper"}.issubset(pred.columns):
        fig.add_traces([
            go.Scatter(
                x=pd.concat([pred["t"], pred["t"][::-1]]),
                y=pd.concat([pred["upper"], pred["lower"][::-1]]),
                fill="toself",
                fillcolor="rgba(56, 189, 248, 0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                hoverinfo="skip",
                name="±95%",
            )
        ])

    fig.update_layout(
        title=title,
        xaxis_title="Time (weeks)",
        yaxis_title="Estimated 1RM (kg)",
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=50, b=20),
    )
    return fig