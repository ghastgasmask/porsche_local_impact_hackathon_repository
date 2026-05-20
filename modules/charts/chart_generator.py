
# Suraganov's true
# Chart Generator
# Converts validated chart instructions into Plotly figure objcts
# THIS Handles "aggregation", grouping, and chart-specific STUFF
# THIS DOES NOT USE exec(), NO eval(), NO arbitrary code generation

import pandas as pd
import plotly.express as px
import streamlit as st

from .chart_registry import DATAFRAME_MAP


def generate_chart(instruction: dict):
    chart_type = instruction["chart_type"]
    df_key = instruction["dataframe"]
    title = instruction.get("title", "Treasury Chart")
    aggregation = instruction.get("aggregation", "none")
    color = instruction.get("color", None)

    # Retrieve the dataframe from session state
    session_key = DATAFRAME_MAP.get(df_key)
    if not session_key or session_key not in st.session_state:
        return None

    df = st.session_state[session_key].copy()

    if df.empty:
        return None

    try:
        if chart_type == "pie":
            return _build_pie(df, instruction, title)
        elif chart_type == "bar":
            return _build_bar(df, instruction, title, aggregation, color)
        elif chart_type == "line":
            return _build_line(df, instruction, title, aggregation, color)
        elif chart_type == "scatter":
            return _build_scatter(df, instruction, title, color)
    except Exception:
        return None

    return None


def _apply_aggregation(df: pd.DataFrame, x: str, y: str, agg: str) -> pd.DataFrame:
    # apply aggregation
    if agg == "none" or not agg:
        return df

    agg_map = {
        "sum": "sum",
        "mean": "mean",
        "count": "count",
        "min": "min",
        "max": "max",
        "median": "median",
    }

    agg_func = agg_map.get(agg)
    if not agg_func:
        return df

    # Group by x column and aggregate y column
    grouped = df.groupby(x, as_index=False).agg({y: agg_func})
    return grouped


def _build_pie(df, instruction, title):
    #pie chart
    values_col = instruction["values"]
    names_col = instruction["names"]
    aggregation = instruction.get("aggregation", "sum")

    # For pie charts, always aggregate (sum)
    if aggregation and aggregation != "none":
        agg_func = aggregation if aggregation in ["sum", "mean", "count", "min", "max", "median"] else "sum"
        df = df.groupby(names_col, as_index=False).agg({values_col: agg_func})

    fig = px.pie(
        df,
        values=values_col,
        names=names_col,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        template="plotly_white",
        font=dict(size=13),
        title_font_size=16,
    )
    return fig


def _build_bar(df, instruction, title, aggregation, color):
    #build bar chart
    x = instruction["x"]
    y = instruction["y"]

    if aggregation and aggregation != "none":
        df = _apply_aggregation(df, x, y, aggregation)

    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=color if color and color in df.columns else None,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(size=13),
        title_font_size=16,
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
    )
    return fig


def _build_line(df, instruction, title, aggregation, color):
    #build line chart
    x = instruction["x"]
    y = instruction["y"]

    # Sort by x if it looks like a date column
    if "date" in x.lower() or "time" in x.lower():
        df[x] = pd.to_datetime(df[x], errors="coerce")
        df = df.sort_values(x)

    if aggregation and aggregation != "none":
        df = _apply_aggregation(df, x, y, aggregation)

    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        color=color if color and color in df.columns else None,
        markers=True,
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(size=13),
        title_font_size=16,
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
    )
    return fig


def _build_scatter(df, instruction, title, color):
    """Builds a scatter plot."""
    x = instruction["x"]
    y = instruction["y"]

    fig = px.scatter(
        df,
        x=x,
        y=y,
        title=title,
        color=color if color and color in df.columns else None,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(size=13),
        title_font_size=16,
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
    )
    return fig
