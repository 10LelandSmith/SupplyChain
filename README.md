# Supply Chain Carbon Intensity Dashboard

An interactive Streamlit dashboard based on the accompanying Jupyter notebook and the EPA USEEIO v1.3 NAICS-6 supply-chain greenhouse-gas emission-factor dataset.

## Files

```text
.
├── app.py
├── requirements.txt
├── Supply_Chain_Carbon_Intensity_Dashboard_Data.csv
└── README.md
```

## Run locally

1. Clone your repository:
   ```bash
   git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   cd YOUR-REPOSITORY
   ```
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the dashboard:
   ```bash
   streamlit run app.py
   ```

The CSV must be in the same folder as `app.py`.

## Deploy with Streamlit Community Cloud

1. Push `app.py`, `requirements.txt`, and the CSV file to the root of your GitHub repository.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select **Create app**, choose your GitHub repository and branch.
4. Set the **Main file path** to `app.py`.
5. Deploy.

If you store the CSV in a subfolder, update `DATA_FILE` near the top of `app.py` to point to that relative path.

## Dashboard features

- Filters for macro-economic category, broad NAICS sector, carbon-intensity tier, total emission-factor range, and industry name or NAICS code.
- KPI metrics that respond to the active filters.
- Top 15 industry intensity horizontal bar chart.
- Broad-sector carbon-intensity box plot.
- Stacked comparison of mean direct and margin-related emission factors by broad sector.
- Expandable sector statistics and industry-level data table.
- CSV download for the filtered industry records.

## Data and units

Emission factors are expressed in kg CO2e per 2022 USD. The dataset contains 1,016 industry records and the exported fields created by the notebook's feature-engineering pipeline.
