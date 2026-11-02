from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Supply Chain Carbon Intensity Dashboard",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).parent / "Supply_Chain_Carbon_Intensity_Dashboard_Data.csv"

# Consistent field names from the notebook's exported dashboard dataset.
NAICS_CODE = "naics_code"
NAICS_TITLE = "naics_title"
BROAD_SECTOR = "broad_sector"
MACRO_CATEGORY = "macro_category"
DIRECT_EF = "direct_ef_kg_co2e_per_usd"
MARGIN_EF = "margin_ef_kg_co2e_per_usd"
TOTAL_EF = "total_ef_kg_co2e_per_usd"
MARGIN_SHARE = "margin_pct_share"
TIER = "carbon_intensity_tier"
RANK = "intensity_rank"
USEEIO_CODE = "useeio_code"

REQUIRED_COLUMNS = [
    NAICS_CODE, NAICS_TITLE, BROAD_SECTOR, MACRO_CATEGORY,
    DIRECT_EF, MARGIN_EF, TOTAL_EF, MARGIN_SHARE, TIER, RANK,
    USEEIO_CODE,
]


@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    data = pd.read_csv(file_path)
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(
            "The CSV is missing required columns: " + ", ".join(missing)
        )

    for column in [DIRECT_EF, MARGIN_EF, TOTAL_EF, MARGIN_SHARE, RANK, NAICS_CODE]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data[NAICS_TITLE] = data[NAICS_TITLE].fillna("Unknown industry")
    data[BROAD_SECTOR] = data[BROAD_SECTOR].fillna("Unclassified")
    data[MACRO_CATEGORY] = data[MACRO_CATEGORY].fillna("Unclassified")
    data[TIER] = data[TIER].fillna("Unclassified")
    data = data.dropna(subset=[TOTAL_EF, DIRECT_EF, MARGIN_EF])
    return data


# ---------------------------------------------------------------------
# Load and validate data
# ---------------------------------------------------------------------
st.title("🌎 Supply Chain Carbon Intensity Dashboard")
st.markdown(
    """
    **Industry emission benchmarks | EPA USEEIO v1.3 | 2017 NAICS-6**

    Explore direct supply chain emissions, margin-related emissions, and total
    greenhouse gas (GHG) emission factors across U.S. industries. Emission
    factors are expressed in **kg CO₂e per 2022 USD**.
    """
)

if not DATA_FILE.exists():
    st.error(
        f"Could not find `{DATA_FILE.name}`. Place the CSV in the same GitHub "
        "repository folder as `app.py`, then redeploy the app."
    )
    st.stop()

try:
    df = load_data(str(DATA_FILE))
except Exception as exc:
    st.error(f"Unable to load the dashboard dataset: {exc}")
    st.stop()

# ---------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------
st.sidebar.header("Dashboard filters")
st.sidebar.caption("Filters update the KPIs, charts, and industry tables.")

macro_options = sorted(df[MACRO_CATEGORY].dropna().unique().tolist())
selected_macros = st.sidebar.multiselect(
    "Macro-economic category",
    options=macro_options,
    default=macro_options,
)

available_sectors = sorted(
    df.loc[df[MACRO_CATEGORY].isin(selected_macros), BROAD_SECTOR]
    .dropna().unique().tolist()
)
selected_sectors = st.sidebar.multiselect(
    "Broad NAICS sector",
    options=available_sectors,
    default=available_sectors,
)

tier_order = [
    "1. Low Carbon Intensity",
    "2. Moderate Carbon Intensity",
    "3. High Carbon Intensity",
    "4. Very High Carbon Intensity",
]
available_tiers = [tier for tier in tier_order if tier in df[TIER].unique()]
other_tiers = sorted(set(df[TIER].dropna().unique()) - set(available_tiers))
tier_options = available_tiers + other_tiers
selected_tiers = st.sidebar.multiselect(
    "Carbon intensity tier",
    options=tier_options,
    default=tier_options,
)

minimum = float(df[TOTAL_EF].min())
maximum = float(df[TOTAL_EF].max())
if minimum == maximum:
    intensity_range = (minimum, maximum)
else:
    intensity_range = st.sidebar.slider(
        "Total emission factor range (kg CO₂e / USD)",
        min_value=minimum,
        max_value=maximum,
        value=(minimum, maximum),
        format="%.3f",
    )

search_text = st.sidebar.text_input(
    "Search industry name or NAICS code",
    placeholder="e.g. soybean, 111110",
)

filtered = df[
    df[MACRO_CATEGORY].isin(selected_macros)
    & df[BROAD_SECTOR].isin(selected_sectors)
    & df[TIER].isin(selected_tiers)
    & df[TOTAL_EF].between(intensity_range[0], intensity_range[1])
].copy()

if search_text.strip():
    query = search_text.strip().lower()
    filtered = filtered[
        filtered[NAICS_TITLE].str.lower().str.contains(query, na=False)
        | filtered[NAICS_CODE].astype("Int64").astype(str).str.contains(query, na=False)
    ]

st.sidebar.divider()
st.sidebar.caption(f"Showing {len(filtered):,} of {len(df):,} industries.")

# ---------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------
if filtered.empty:
    st.warning("No industries match the selected filters. Adjust the sidebar filters.")
    st.stop()

total_industries = len(filtered)
avg_total = filtered[TOTAL_EF].mean()
avg_direct = filtered[DIRECT_EF].mean()
avg_margin_share = filtered[MARGIN_SHARE].mean()
highest_row = filtered.loc[filtered[TOTAL_EF].idxmax()]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Industries in view", f"{total_industries:,}")
k2.metric("Average total emission factor", f"{avg_total:.4f}", "kg CO₂e / USD")
k3.metric("Average direct emission factor", f"{avg_direct:.4f}", "kg CO₂e / USD")
k4.metric("Average margin contribution", f"{avg_margin_share:.2f}%")

st.caption(
    f"Highest-intensity industry in the current selection: "
    f"**{highest_row[NAICS_TITLE]}** "
    f"(NAICS {int(highest_row[NAICS_CODE])}, "
    f"{highest_row[TOTAL_EF]:.4f} kg CO₂e / USD)."
)

st.divider()

# ---------------------------------------------------------------------
# Notebook visualization 1: Top 15 industries
# ---------------------------------------------------------------------
st.subheader("1. Top 15 Highest Carbon Intensity Industries")
st.caption(
    "Ranks industries in the current filtered selection by total supply chain "
    "emission factor, including margins."
)
top_n = filtered.nlargest(min(15, len(filtered)), TOTAL_EF).sort_values(TOTAL_EF)
fig_top = px.bar(
    top_n,
    x=TOTAL_EF,
    y=NAICS_TITLE,
    orientation="h",
    color=TOTAL_EF,
    color_continuous_scale="Reds",
    hover_data={
        NAICS_CODE: True,
        BROAD_SECTOR: True,
        DIRECT_EF: ":.4f",
        MARGIN_EF: ":.4f",
        MARGIN_SHARE: ":.2f",
        TOTAL_EF: ":.4f",
    },
    labels={
        TOTAL_EF: "Total emission factor (kg CO₂e / USD)",
        NAICS_TITLE: "Industry",
        NAICS_CODE: "2017 NAICS code",
        BROAD_SECTOR: "Broad sector",
    },
)
fig_top.update_layout(height=max(450, 28 * len(top_n)), coloraxis_showscale=False)
st.plotly_chart(fig_top, use_container_width=True)

# ---------------------------------------------------------------------
# Notebook visualization 2: Distribution across broad sectors
# ---------------------------------------------------------------------
st.subheader("2. Carbon Intensity Distribution Across Broad Economic Sectors")
st.caption(
    "Box plots show the spread, median, and potential outliers of total emission "
    "factors for the industries in each selected broad sector."
)
sector_order = (
    filtered.groupby(BROAD_SECTOR)[TOTAL_EF]
    .median()
    .sort_values(ascending=False)
    .index.tolist()
)
fig_box = px.box(
    filtered,
    x=TOTAL_EF,
    y=BROAD_SECTOR,
    category_orders={BROAD_SECTOR: sector_order},
    color=BROAD_SECTOR,
    points="outliers",
    hover_data=[NAICS_TITLE, NAICS_CODE, DIRECT_EF, MARGIN_EF, MARGIN_SHARE],
    labels={
        TOTAL_EF: "Total emission factor (kg CO₂e / USD)",
        BROAD_SECTOR: "Broad NAICS sector",
    },
)
fig_box.update_layout(
    height=max(500, 48 * len(sector_order)),
    showlegend=False,
)
st.plotly_chart(fig_box, use_container_width=True)

# ---------------------------------------------------------------------
# Notebook visualization 3: Direct vs. margin-related emissions
# ---------------------------------------------------------------------
st.subheader("3. Direct vs. Margin-Related Emission Factors by Broad Sector")
st.caption(
    "Compares mean direct supply chain emission factors with mean margin-related "
    "emission factors. The chart displays up to the 10 highest-total sectors "
    "within the current selection."
)
sector_means = (
    filtered.groupby(BROAD_SECTOR)[[DIRECT_EF, MARGIN_EF]]
    .mean()
    .assign(_total=lambda x: x[DIRECT_EF] + x[MARGIN_EF])
    .nlargest(10, "_total")
    .drop(columns="_total")
    .sort_values(by=DIRECT_EF)
    .reset_index()
)
sector_long = sector_means.melt(
    id_vars=BROAD_SECTOR,
    value_vars=[DIRECT_EF, MARGIN_EF],
    var_name="Emission component",
    value_name="Mean emission factor",
)
sector_long["Emission component"] = sector_long["Emission component"].map({
    DIRECT_EF: "Direct supply chain EF",
    MARGIN_EF: "Margin EF (transport / wholesale / retail)",
})
fig_stack = px.bar(
    sector_long,
    x="Mean emission factor",
    y=BROAD_SECTOR,
    color="Emission component",
    orientation="h",
    barmode="stack",
    color_discrete_map={
        "Direct supply chain EF": "#2b5c8f",
        "Margin EF (transport / wholesale / retail)": "#e76f51",
    },
    labels={
        "Mean emission factor": "Mean emission factor (kg CO₂e / USD)",
        BROAD_SECTOR: "Broad sector",
    },
)
fig_stack.update_layout(height=max(450, 48 * len(sector_means)), legend_title_text="")
st.plotly_chart(fig_stack, use_container_width=True)

# ---------------------------------------------------------------------
# Supporting summaries and data explorer
# ---------------------------------------------------------------------
with st.expander("Explore sector summary statistics", expanded=False):
    sector_summary = (
        filtered.groupby(BROAD_SECTOR)
        .agg(
            Industry_Count=(NAICS_CODE, "count"),
            Mean_Intensity=(TOTAL_EF, "mean"),
            Median_Intensity=(TOTAL_EF, "median"),
            Std_Dev=(TOTAL_EF, "std"),
            Max_Intensity=(TOTAL_EF, "max"),
            Min_Intensity=(TOTAL_EF, "min"),
            Avg_Margin_Share_Pct=(MARGIN_SHARE, "mean"),
        )
        .sort_values("Mean_Intensity", ascending=False)
        .reset_index()
    )
    st.dataframe(
        sector_summary.style.format({
            "Mean_Intensity": "{:.4f}",
            "Median_Intensity": "{:.4f}",
            "Std_Dev": "{:.4f}",
            "Max_Intensity": "{:.4f}",
            "Min_Intensity": "{:.4f}",
            "Avg_Margin_Share_Pct": "{:.2f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Explore industry records", expanded=False):
    display_columns = [
        NAICS_CODE, NAICS_TITLE, BROAD_SECTOR, MACRO_CATEGORY,
        DIRECT_EF, MARGIN_EF, TOTAL_EF, MARGIN_SHARE, TIER, RANK, USEEIO_CODE,
    ]
    st.dataframe(
        filtered.sort_values(TOTAL_EF, ascending=False)[display_columns],
        use_container_width=True,
        hide_index=True,
    )
    csv_bytes = filtered[display_columns].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered industries as CSV",
        data=csv_bytes,
        file_name="filtered_supply_chain_carbon_intensity.csv",
        mime="text/csv",
    )

st.divider()
st.markdown(
    """
    **Data and methodology**

    Dataset: EPA USEEIO v1.3 NAICS-6 greenhouse gas emission factors, covering
    1,016 U.S. industries. Broad sectors, macro-economic categories, margin
    contribution percentages, intensity ranks, and quartile-based carbon
    intensity tiers follow the feature-engineering logic in the accompanying
    analysis notebook.

    *Margin contribution (%) = margin emission factor ÷ total emission factor × 100.*
    """
)
