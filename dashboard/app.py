import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
from pathlib import Path

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Customer Segmentation & Marketing Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# TITLE
# ============================================================

st.title("📊 Customer Segmentation & Marketing Analytics")

st.markdown(
    "Analyze customer behavior, purchasing patterns, customer value, "
    "and marketing segments using RFM analysis and K-Means clustering."
)

st.divider()


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    file_path = BASE_DIR / "data" / "raw" / "Online Retail.xlsx"

    return pd.read_excel(file_path)


try:

    df = load_data()

except Exception as e:

    st.error("Could not load the dataset.")
    st.exception(e)
    st.stop()


# ============================================================
# DATA CLEANING
# ============================================================

df = df.dropna(subset=["CustomerID"]).copy()

df = df[df["Quantity"] > 0].copy()

df = df[df["UnitPrice"] > 0].copy()

df["TotalAmount"] = (
    df["Quantity"] * df["UnitPrice"]
)

df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"],
    errors="coerce"
)

df = df.dropna(
    subset=["InvoiceDate"]
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🎛️ Dashboard Filters")

country_counts = (
    df.groupby("Country")["CustomerID"]
    .nunique()
    .sort_index()
)

# Only show countries with at least 5 customers
# because K-Means needs at least 5 customers for 5 clusters.

valid_countries = country_counts[
    country_counts >= 5
].index.tolist()

countries = [
    "All Countries"
] + valid_countries


selected_country = st.sidebar.selectbox(
    "🌍 Select Country",
    countries
)


if selected_country == "All Countries":

    filtered_df = df.copy()

else:

    filtered_df = df[
        df["Country"] == selected_country
    ].copy()


st.sidebar.divider()

st.sidebar.caption(
    f"Transactions: {len(filtered_df):,}\n\n"
    f"Customers: {filtered_df['CustomerID'].nunique():,}"
)

st.sidebar.info(
    "The selected country filter updates the dashboard analysis."
)


# ============================================================
# BUSINESS OVERVIEW
# ============================================================

st.header("📌 Business Overview")


total_customers = (
    filtered_df["CustomerID"].nunique()
)

total_revenue = (
    filtered_df["TotalAmount"].sum()
)

total_orders = (
    filtered_df["InvoiceNo"].nunique()
)

average_order_value = (
    total_revenue / total_orders
    if total_orders > 0
    else 0
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "👥 Customers",
        f"{total_customers:,}"
    )


with col2:

    st.metric(
        "💰 Revenue",
        f"£{total_revenue:,.2f}"
    )


with col3:

    st.metric(
        "🧾 Orders",
        f"{total_orders:,}"
    )


with col4:

    st.metric(
        "🛒 Average Order Value",
        f"£{average_order_value:,.2f}"
    )


st.divider()


# ============================================================
# RFM ANALYSIS
# ============================================================

st.header("🎯 Customer Segmentation")


analysis_date = (
    filtered_df["InvoiceDate"].max()
    + pd.Timedelta(days=1)
)


rfm = (
    filtered_df
    .groupby("CustomerID")
    .agg(
        Recency=(
            "InvoiceDate",
            lambda x:
            (analysis_date - x.max()).days
        ),

        Frequency=(
            "InvoiceNo",
            "nunique"
        ),

        Monetary=(
            "TotalAmount",
            "sum"
        )
    )
)


if len(rfm) < 5:

    st.warning(
        "The selected country contains fewer than 5 customers. "
        "Please select All Countries or another country."
    )

    st.stop()


# ============================================================
# RFM SCORING
# ============================================================

# Percentile-based scoring is more robust than qcut
# when filters contain repeated values.

recency_rank = (
    rfm["Recency"]
    .rank(method="average", pct=True)
)

frequency_rank = (
    rfm["Frequency"]
    .rank(method="average", pct=True)
)

monetary_rank = (
    rfm["Monetary"]
    .rank(method="average", pct=True)
)


rfm["R_Score"] = np.ceil(
    recency_rank * 5
).astype(int)

rfm["R_Score"] = (
    6 - rfm["R_Score"]
)


rfm["F_Score"] = np.ceil(
    frequency_rank * 5
).astype(int)


rfm["M_Score"] = np.ceil(
    monetary_rank * 5
).astype(int)


rfm["RFM_Score"] = (
    rfm["R_Score"].astype(str)
    + rfm["F_Score"].astype(str)
    + rfm["M_Score"].astype(str)
)


# ============================================================
# K-MEANS CLUSTERING
# ============================================================

features = rfm[
    [
        "Recency",
        "Frequency",
        "Monetary"
    ]
].copy()


# Log transformation
features["Recency"] = np.log1p(
    features["Recency"]
)

features["Frequency"] = np.log1p(
    features["Frequency"]
)

features["Monetary"] = np.log1p(
    features["Monetary"]
)


scaler = StandardScaler()

scaled_features = (
    scaler.fit_transform(features)
)


n_clusters = 5


kmeans = KMeans(
    n_clusters=n_clusters,
    random_state=42,
    n_init=10
)


rfm["Cluster"] = (
    kmeans.fit_predict(
        scaled_features
    )
)


# ============================================================
# ELBOW METHOD
# ============================================================

inertia = []

max_k = min(
    10,
    len(rfm) - 1
)


for k in range(
    2,
    max_k + 1
):

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    model.fit(
        scaled_features
    )

    inertia.append(
        model.inertia_
    )


k_range = list(
    range(
        2,
        max_k + 1
    )
)


# ============================================================
# SEGMENT NAMES
# ============================================================

cluster_summary = (
    rfm
    .groupby("Cluster")
    .agg(
        Recency=("Recency", "mean"),
        Frequency=("Frequency", "mean"),
        Monetary=("Monetary", "mean")
    )
    .reset_index()
)


cluster_summary["ValueScore"] = (

    cluster_summary["Frequency"]
    .rank(ascending=True)

    +

    cluster_summary["Monetary"]
    .rank(ascending=True)

    +

    cluster_summary["Recency"]
    .rank(ascending=False)
)


cluster_summary = (
    cluster_summary
    .sort_values(
        "ValueScore",
        ascending=False
    )
)


segment_names = [

    "🏆 Champions",

    "💎 Loyal Customers",

    "💰 Potential Customers",

    "⚠️ At Risk",

    "😴 Lost Customers"

]


cluster_to_segment = {}


for i, cluster in enumerate(
    cluster_summary["Cluster"]
):

    cluster_to_segment[
        cluster
    ] = segment_names[
        min(
            i,
            len(segment_names) - 1
        )
    ]


rfm["Segment"] = (
    rfm["Cluster"]
    .map(cluster_to_segment)
)


# ============================================================
# DOWNLOAD CUSTOMER SEGMENTATION
# ============================================================

st.subheader(
    "📥 Customer Segmentation Export"
)


download_data = (
    rfm
    .reset_index()
    .copy()
)


csv_data = (
    download_data
    .to_csv(index=False)
    .encode("utf-8")
)


st.download_button(

    label="⬇️ Download Segmented Customers CSV",

    data=csv_data,

    file_name="customer_segments.csv",

    mime="text/csv"
)


st.divider()


# ============================================================
# CUSTOMER SEGMENT DISTRIBUTION
# ============================================================

segment_counts = (

    rfm["Segment"]

    .value_counts()

    .rename_axis("Segment")

    .reset_index(
        name="Customers"
    )
)


fig_segment = px.bar(

    segment_counts,

    x="Segment",

    y="Customers",

    text="Customers",

    title="Customer Distribution by Segment"
)


fig_segment.update_layout(

    xaxis_title="Customer Segment",

    yaxis_title="Number of Customers"

)


st.plotly_chart(

    fig_segment,

    use_container_width=True

)


# ============================================================
# RFM VISUALIZATION
# ============================================================

st.header(
    "📈 RFM Analysis"
)


col1, col2 = st.columns(2)


with col1:

    fig_recency = px.histogram(

        rfm,

        x="Recency",

        nbins=30,

        title="Customer Recency Distribution"

    )

    fig_recency.update_layout(

        xaxis_title="Recency (Days)",

        yaxis_title="Customers"

    )

    st.plotly_chart(

        fig_recency,

        use_container_width=True

    )


with col2:

    fig_monetary = px.histogram(

        rfm,

        x="Monetary",

        nbins=30,

        title="Customer Spending Distribution"

    )

    fig_monetary.update_layout(

        xaxis_title="Customer Spending (£)",

        yaxis_title="Customers"

    )

    st.plotly_chart(

        fig_monetary,

        use_container_width=True

    )


# ============================================================
# FREQUENCY VS MONETARY
# ============================================================

st.subheader(
    "Purchase Frequency vs Customer Spending"
)


fig_scatter = px.scatter(

    rfm.reset_index(),

    x="Frequency",

    y="Monetary",

    size="Monetary",

    color="Segment",

    hover_data=[

        "CustomerID",

        "Recency",

        "Frequency",

        "Monetary"

    ],

    title="Customer Segmentation by Purchase Behavior"

)


fig_scatter.update_layout(

    xaxis_title="Purchase Frequency",

    yaxis_title="Customer Spending (£)"

)


st.plotly_chart(

    fig_scatter,

    use_container_width=True

)


# ============================================================
# REVENUE BY CUSTOMER SEGMENT
# ============================================================

customer_segments = (
    rfm[["Segment"]]
    .copy()
)


df_segmented = (
    filtered_df
    .merge(

        customer_segments,

        left_on="CustomerID",

        right_index=True,

        how="inner"

    )
)


revenue_by_segment = (

    df_segmented

    .groupby("Segment")[
        "TotalAmount"
    ]

    .sum()

    .reset_index()

    .rename(
        columns={
            "TotalAmount":
            "Revenue"
        }
    )

)


revenue_by_segment[
    "Revenue_Percentage"
] = (

    revenue_by_segment["Revenue"]

    /

    revenue_by_segment[
        "Revenue"
    ].sum()

    * 100

)


revenue_by_segment = (

    revenue_by_segment

    .sort_values(

        "Revenue",

        ascending=False

    )

)


col1, col2 = st.columns(2)


with col1:

    fig_revenue = px.bar(

        revenue_by_segment,

        x="Segment",

        y="Revenue",

        text="Revenue",

        color="Segment",

        title="Revenue Contribution by Customer Segment"

    )


    fig_revenue.update_traces(

        texttemplate="£%{text:,.0f}",

        textposition="outside"

    )


    fig_revenue.update_layout(

        xaxis_title="Customer Segment",

        yaxis_title="Revenue (£)",

        showlegend=False

    )


    st.plotly_chart(

        fig_revenue,

        use_container_width=True

    )


with col2:

    st.subheader(
        "📊 Revenue Share"
    )


    revenue_display = (
        revenue_by_segment
        .copy()
    )


    revenue_display[
        "Revenue"
    ] = revenue_display[
        "Revenue"
    ].apply(

        lambda x:
        f"£{x:,.2f}"

    )


    revenue_display[
        "Revenue_Percentage"
    ] = revenue_display[
        "Revenue_Percentage"
    ].apply(

        lambda x:
        f"{x:.2f}%"

    )


    st.dataframe(

        revenue_display,

        use_container_width=True,

        hide_index=True

    )


# ============================================================
# SEGMENT SUMMARY
# ============================================================

st.subheader(
    "📋 Customer Segment Summary"
)


segment_summary = (

    rfm

    .groupby("Segment")

    .agg(

        Customers=(
            "Recency",
            "count"
        ),

        Avg_Recency=(
            "Recency",
            "mean"
        ),

        Avg_Frequency=(
            "Frequency",
            "mean"
        ),

        Avg_Monetary=(
            "Monetary",
            "mean"
        )

    )

    .reset_index()

    .sort_values(

        "Avg_Monetary",

        ascending=False

    )

)


segment_summary[
    "Avg_Recency"
] = segment_summary[
    "Avg_Recency"
].round(1)


segment_summary[
    "Avg_Frequency"
] = segment_summary[
    "Avg_Frequency"
].round(1)


segment_summary[
    "Avg_Monetary"
] = segment_summary[
    "Avg_Monetary"
].round(2)


st.dataframe(

    segment_summary,

    use_container_width=True,

    hide_index=True

)


# ============================================================
# CUSTOMER VALUE / CLV
# ============================================================

st.header(
    "💎 Customer Value Analysis"
)


customer_value = (

    filtered_df

    .groupby("CustomerID")

    .agg(

        Total_Spend=(
            "TotalAmount",
            "sum"
        ),

        Total_Orders=(
            "InvoiceNo",
            "nunique"
        ),

        First_Purchase=(
            "InvoiceDate",
            "min"
        ),

        Last_Purchase=(
            "InvoiceDate",
            "max"
        )

    )

    .reset_index()

)


customer_value[
    "Average_Order_Value"
] = (

    customer_value[
        "Total_Spend"
    ]

    /

    customer_value[
        "Total_Orders"
    ]

)


customer_value[
    "Customer_Lifespan_Days"
] = (

    customer_value[
        "Last_Purchase"
    ]

    -

    customer_value[
        "First_Purchase"
    ]

).dt.days


customer_value[
    "Customer_Lifespan_Days"
] = (

    customer_value[
        "Customer_Lifespan_Days"
    ]

    .replace(0, 1)

)


customer_value[
    "Purchase_Frequency_Yearly"
] = (

    customer_value[
        "Total_Orders"
    ]

    /

    (

        customer_value[
            "Customer_Lifespan_Days"
        ]

        / 365

    )

)


customer_value[
    "Estimated_CLV"
] = (

    customer_value[
        "Average_Order_Value"
    ]

    *

    customer_value[
        "Purchase_Frequency_Yearly"
    ]

)


customer_value = (

    customer_value

    .merge(

        rfm[["Segment"]],

        left_on="CustomerID",

        right_index=True,

        how="left"

    )

)


median_clv = (
    customer_value[
        "Estimated_CLV"
    ].median()
)


high_value_customers = (

    customer_value[
        "Estimated_CLV"
    ]

    >=

    customer_value[
        "Estimated_CLV"
    ].quantile(0.75)

).sum()


col1, col2 = st.columns(2)


with col1:

    st.metric(

        "💎 Median Estimated Annual CLV",

        f"£{median_clv:,.2f}"

    )


with col2:

    st.metric(

        "🌟 High-Value Customers",

        f"{high_value_customers:,}"

    )


st.caption(

    "Estimated annual customer value based on historical purchase behavior; "
    "it is not a guaranteed future lifetime value."

)


clv_by_segment = (

    customer_value

    .groupby("Segment")[
        "Estimated_CLV"
    ]

    .median()

    .reset_index()

    .sort_values(

        "Estimated_CLV",

        ascending=False

    )

)


fig_clv = px.bar(

    clv_by_segment,

    x="Segment",

    y="Estimated_CLV",

    text="Estimated_CLV",

    color="Segment",

    title="Estimated Annual Customer Value by Segment"

)


fig_clv.update_traces(

    texttemplate="£%{text:,.0f}",

    textposition="outside"

)


fig_clv.update_layout(

    xaxis_title="Customer Segment",

    yaxis_title="Estimated Annual Value (£)",

    showlegend=False

)


st.plotly_chart(

    fig_clv,

    use_container_width=True

)


# ============================================================
# TOP HIGH-VALUE CUSTOMERS
# ============================================================

st.subheader(
    "🏆 Top 10 High-Value Customers"
)


top_customers_display = (

    customer_value

    .sort_values(

        "Estimated_CLV",

        ascending=False

    )

    .head(10)

    [

        [

            "CustomerID",

            "Segment",

            "Total_Spend",

            "Total_Orders",

            "Average_Order_Value",

            "Estimated_CLV"

        ]

    ]

    .copy()

)


for column in [

    "Total_Spend",

    "Average_Order_Value",

    "Estimated_CLV"

]:

    top_customers_display[
        column
    ] = (

        top_customers_display[
            column
        ].round(2)

    )


st.dataframe(

    top_customers_display,

    use_container_width=True,

    hide_index=True

)


# ============================================================
# SQL BUSINESS ANALYSIS
# ============================================================

st.header(
    "🗄️ SQL Business Analysis"
)


db_file = (
    BASE_DIR
    / "database"
    / "customer_segmentation.db"
)


try:

    conn = sqlite3.connect(
        db_file
    )


    # Create temporary filtered SQL table
    # so the country filter also affects SQL.

    filtered_df.to_sql(

        "filtered_retail",

        conn,

        if_exists="replace",

        index=False

    )


    # --------------------------------------------------------
    # SQL KPIs
    # --------------------------------------------------------

    sql_revenue = """

    SELECT
        ROUND(
            SUM(Quantity * UnitPrice),
            2
        ) AS total_revenue

    FROM filtered_retail;

    """


    sql_customers = """

    SELECT
        COUNT(
            DISTINCT CustomerID
        ) AS total_customers

    FROM filtered_retail;

    """


    sql_orders = """

    SELECT
        COUNT(
            DISTINCT InvoiceNo
        ) AS total_orders

    FROM filtered_retail;

    """


    sql_aov = """

    SELECT

        ROUND(

            SUM(
                Quantity * UnitPrice
            )

            /

            COUNT(
                DISTINCT InvoiceNo
            ),

            2

        ) AS average_order_value

    FROM filtered_retail;

    """


    revenue = pd.read_sql_query(

        sql_revenue,

        conn

    )[
        "total_revenue"
    ].iloc[0]


    customers = pd.read_sql_query(

        sql_customers,

        conn

    )[
        "total_customers"
    ].iloc[0]


    orders = pd.read_sql_query(

        sql_orders,

        conn

    )[
        "total_orders"
    ].iloc[0]


    aov = pd.read_sql_query(

        sql_aov,

        conn

    )[
        "average_order_value"
    ].iloc[0]


    st.caption(

        "SQL results use the same country filter "
        "selected in the sidebar."

    )


    col1, col2, col3, col4 = st.columns(4)


    col1.metric(

        "SQL Revenue",

        f"£{revenue:,.2f}"

    )


    col2.metric(

        "SQL Customers",

        f"{customers:,}"

    )


    col3.metric(

        "SQL Orders",

        f"{orders:,}"

    )


    col4.metric(

        "SQL AOV",

        f"£{aov:,.2f}"

    )


    # --------------------------------------------------------
    # MONTHLY REVENUE
    # --------------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        sql_monthly = """

        SELECT

            strftime(
                '%Y-%m',
                InvoiceDate
            ) AS month,

            ROUND(
                SUM(
                    Quantity * UnitPrice
                ),
                2
            ) AS revenue

        FROM filtered_retail

        GROUP BY month

        ORDER BY month;

        """


        monthly_revenue = (
            pd.read_sql_query(
                sql_monthly,
                conn
            )
        )


        fig_monthly = px.line(

            monthly_revenue,

            x="month",

            y="revenue",

            markers=True,

            title="Monthly Revenue Trend"

        )


        fig_monthly.update_layout(

            xaxis_title="Month",

            yaxis_title="Revenue (£)"

        )


        st.plotly_chart(

            fig_monthly,

            use_container_width=True

        )


    # --------------------------------------------------------
    # TOP COUNTRIES
    # --------------------------------------------------------

    with col2:

        sql_country = """

        SELECT

            Country,

            ROUND(

                SUM(
                    Quantity * UnitPrice
                ),

                2

            ) AS revenue

        FROM filtered_retail

        GROUP BY Country

        ORDER BY revenue DESC

        LIMIT 10;

        """


        country_revenue = (
            pd.read_sql_query(
                sql_country,
                conn
            )
        )


        fig_country = px.bar(

            country_revenue,

            x="revenue",

            y="Country",

            orientation="h",

            title="Top Countries by Revenue"

        )


        fig_country.update_layout(

            xaxis_title="Revenue (£)",

            yaxis_title="Country"

        )


        st.plotly_chart(

            fig_country,

            use_container_width=True

        )


    # --------------------------------------------------------
    # TOP CUSTOMERS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        sql_customers_top = """

        SELECT

            CustomerID,

            ROUND(

                SUM(
                    Quantity * UnitPrice
                ),

                2

            ) AS total_spending

        FROM filtered_retail

        GROUP BY CustomerID

        ORDER BY total_spending DESC

        LIMIT 10;

        """


        top_sql_customers = (
            pd.read_sql_query(
                sql_customers_top,
                conn
            )
        )


        st.subheader(
            "👑 Top Customers"
        )


        st.dataframe(

            top_sql_customers,

            use_container_width=True,

            hide_index=True

        )


    # --------------------------------------------------------
    # TOP PRODUCTS
    # --------------------------------------------------------

    with col2:

        sql_products = """

        SELECT

            Description,

            ROUND(

                SUM(
                    Quantity * UnitPrice
                ),

                2

            ) AS revenue

        FROM filtered_retail

        WHERE Description IS NOT NULL

        GROUP BY Description

        ORDER BY revenue DESC

        LIMIT 10;

        """


        top_products = (
            pd.read_sql_query(
                sql_products,
                conn
            )
        )


        fig_products = px.bar(

            top_products,

            x="revenue",

            y="Description",

            orientation="h",

            title="Top 10 Products by Revenue"

        )


        fig_products.update_layout(

            xaxis_title="Revenue (£)",

            yaxis_title="Product"

        )


        st.plotly_chart(

            fig_products,

            use_container_width=True

        )


    conn.close()


except Exception as e:

    st.warning(

        "SQL analysis could not be loaded. "
        "Make sure customer_segmentation.db has been created."

    )

    st.exception(e)


# ============================================================
# MODEL EVALUATION
# ============================================================

st.header(
    "🤖 Model Evaluation"
)


silhouette = silhouette_score(

    scaled_features,

    rfm["Cluster"]

)


col1, col2 = st.columns(2)


with col1:

    st.metric(

        "Number of Clusters",

        n_clusters

    )


with col2:

    st.metric(

        "Silhouette Score",

        f"{silhouette:.3f}"

    )


st.caption(

    "A higher Silhouette Score generally indicates better separation "
    "between customer clusters."

)


# ============================================================
# ELBOW METHOD
# ============================================================

st.subheader(
    "📉 Optimal Number of Customer Segments"
)


elbow_df = pd.DataFrame({

    "Number of Clusters":
        k_range,

    "Inertia":
        inertia

})


fig_elbow = px.line(

    elbow_df,

    x="Number of Clusters",

    y="Inertia",

    markers=True,

    title="Elbow Method for Optimal K"

)


st.plotly_chart(

    fig_elbow,

    use_container_width=True

)


# ============================================================
# BUSINESS INSIGHTS
# ============================================================

st.header(
    "💡 Key Business Insights"
)


largest_segment = (
    segment_summary.loc[
        segment_summary[
            "Customers"
        ].idxmax(),
        "Segment"
    ]
)


largest_segment_count = int(

    segment_summary[
        "Customers"
    ].max()

)


highest_value_segment = (
    segment_summary.loc[
        segment_summary[
            "Avg_Monetary"
        ].idxmax(),
        "Segment"
    ]
)


highest_value_amount = (
    segment_summary[
        "Avg_Monetary"
    ].max()
)


st.markdown(

    f"""

### 📊 Customer Segmentation

- **{largest_segment}** is the largest customer segment with
  **{largest_segment_count:,} customers**.

- **{highest_value_segment}** has the highest average customer spending,
  at approximately **£{highest_value_amount:,.2f}**.


### 🎯 Recommended Marketing Actions

- **🏆 Champions:** Reward loyal customers, provide VIP benefits,
  and encourage referrals.

- **💎 Loyal Customers:** Use loyalty programs, cross-selling,
  and personalized recommendations.

- **💰 Potential Customers:** Encourage repeat purchases with
  targeted promotions.

- **⚠️ At Risk:** Run win-back campaigns and personalized discounts.

- **😴 Lost Customers:** Test reactivation campaigns and avoid
  excessive marketing spend.

"""

)
# ============================================================
# BUSINESS INSIGHTS
# ============================================================

st.markdown("---")
st.header("💡 Business Insights")

st.markdown(
    """
    Customer segmentation helps the business understand different customer
    behaviors and design targeted marketing strategies instead of treating
    all customers the same.
    """
)

# Use the already-created segment_summary table.
# This avoids the previous KeyError because customer_segments only
# contained the Segment column, while segment_summary contains all
# required business metrics.

segment_insights = segment_summary.copy()

total_segment_customers = segment_insights["Customers"].sum()

for _, row in segment_insights.iterrows():

    segment = row["Segment"]
    customers = int(row["Customers"])
    percentage = (
        (customers / total_segment_customers) * 100
        if total_segment_customers > 0
        else 0
    )

    recency = row["Avg_Recency"]
    frequency = row["Avg_Frequency"]
    monetary = row["Avg_Monetary"]

    if segment == "🏆 Champions":

        st.subheader("🏆 Champions")

        st.markdown(
            f"""
            **What this segment means:**  
            These are the company's most valuable and engaged customers.
            They purchase relatively recently, purchase frequently, and
            have high overall spending.

            **Customer size:** {customers:,} ({percentage:.1f}% of customers)

            **Average Recency:** {recency:.1f} days  
            **Average Frequency:** {frequency:.1f} orders  
            **Average Spending:** £{monetary:,.2f}

            **Recommended business actions:**
            - Reward customers with VIP benefits and exclusive offers.
            - Encourage referrals and loyalty program participation.
            - Provide early access to new products.
            - Use personalized recommendations to increase spending.
            - Focus strongly on retention because losing these customers
              can have a significant revenue impact.
            """
        )

    elif segment == "💎 Loyal Customers":

        st.subheader("💎 Loyal Customers")

        st.markdown(
            f"""
            **What this segment means:**  
            These customers show consistent purchasing behavior and have
            a strong relationship with the company, although their spending
            may be lower than Champions.

            **Customer size:** {customers:,} ({percentage:.1f}% of customers)

            **Average Recency:** {recency:.1f} days  
            **Average Frequency:** {frequency:.1f} orders  
            **Average Spending:** £{monetary:,.2f}

            **Recommended business actions:**
            - Introduce loyalty and reward programs.
            - Use cross-selling and upselling strategies.
            - Recommend complementary products.
            - Offer personalized promotions.
            - Encourage these customers to move toward the Champions segment.
            """
        )

    elif segment == "💰 Potential Customers":

        st.subheader("💰 Potential Customers")

        st.markdown(
            f"""
            **What this segment means:**  
            These customers show potential for becoming more valuable.
            They may have purchased recently but do not yet have the
            frequency or spending level of loyal customers.

            **Customer size:** {customers:,} ({percentage:.1f}% of customers)

            **Average Recency:** {recency:.1f} days  
            **Average Frequency:** {frequency:.1f} orders  
            **Average Spending:** £{monetary:,.2f}

            **Recommended business actions:**
            - Encourage repeat purchases with targeted offers.
            - Provide product recommendations based on previous purchases.
            - Use limited-time promotions to increase purchase frequency.
            - Introduce loyalty benefits after additional purchases.
            - Move high-potential customers toward the Loyal Customers segment.
            """
        )

    elif segment == "⚠️ At Risk":

        st.subheader("⚠️ At Risk")

        st.markdown(
            f"""
            **What this segment means:**  
            These customers previously showed valuable purchasing behavior
            but have not purchased recently. They may be at risk of becoming
            inactive customers.

            **Customer size:** {customers:,} ({percentage:.1f}% of customers)

            **Average Recency:** {recency:.1f} days  
            **Average Frequency:** {frequency:.1f} orders  
            **Average Spending:** £{monetary:,.2f}

            **Recommended business actions:**
            - Launch win-back campaigns.
            - Send personalized discounts or special offers.
            - Recommend products based on previous purchases.
            - Use email reminders and targeted communication.
            - Prioritize customers with historically high spending.
            """
        )

    elif segment == "😴 Lost Customers":

        st.subheader("😴 Lost Customers")

        st.markdown(
            f"""
            **What this segment means:**  
            These customers have not purchased for a long period and show
            low recent engagement. They represent an opportunity for
            reactivation, but marketing spending should be carefully controlled.

            **Customer size:** {customers:,} ({percentage:.1f}% of customers)

            **Average Recency:** {recency:.1f} days  
            **Average Frequency:** {frequency:.1f} orders  
            **Average Spending:** £{monetary:,.2f}

            **Recommended business actions:**
            - Test reactivation and win-back campaigns.
            - Offer incentives only when economically justified.
            - Use low-cost email or automated campaigns first.
            - Identify previously high-value customers for special treatment.
            - Avoid spending heavily on customers with very low historical value.
            """
        )


# ============================================================
# OVERALL BUSINESS TAKEAWAYS
# ============================================================

st.markdown("---")
st.subheader("📌 Key Business Takeaways")

largest_segment_row = segment_insights.loc[
    segment_insights["Customers"].idxmax()
]

highest_spending_row = segment_insights.loc[
    segment_insights["Avg_Monetary"].idxmax()
]

st.markdown(
    f"""
    ### 1. Focus on customer retention
    **{highest_spending_row['Segment']}** has the highest average customer
    spending at approximately **£{highest_spending_row['Avg_Monetary']:,.2f}**.
    Retaining these customers should be a major priority.

    ### 2. Reactivate inactive customers
    **{largest_segment_row['Segment']}** is the largest customer segment with
    **{int(largest_segment_row['Customers']):,} customers**.
    The company should test targeted reactivation campaigns while controlling
    marketing costs.

    ### 3. Grow potential customers
    Potential Customers should receive personalized promotions and
    cross-selling recommendations to increase their purchase frequency.

    ### 4. Protect loyal customers
    Loyal Customers can be moved toward the Champions segment through
    loyalty rewards, personalized recommendations, and exclusive offers.

    ### 5. Use segment-specific marketing
    The analysis shows that different customer groups have different
    purchasing behaviors. Therefore, marketing strategies should be
    **segment-specific rather than one-size-fits-all**.
    """
)


# ============================================================
# TECHNICAL METHODOLOGY
# ============================================================

with st.expander(
    "🔎 View Technical Methodology"
):

    st.markdown(

        """

**Data Processing**

- Removed missing Customer IDs.
- Removed invalid quantities and prices.
- Calculated transaction-level revenue.


**RFM Analysis**

- **Recency:** Days since the customer's last purchase.
- **Frequency:** Number of unique orders.
- **Monetary:** Total customer spending.


**Customer Segmentation**

- K-Means clustering.
- Five customer segments.
- Elbow Method for cluster evaluation.
- Silhouette Score for validation.


**Additional Analytics**

- Revenue by customer segment.
- Estimated annual customer value.
- Monthly revenue.
- Country-level revenue.
- Top customers.
- Top products.
- SQL business analysis.

"""

    )


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(

    "Customer Segmentation & Marketing Analytics | "
    "Python • Pandas • SQL • Scikit-learn • K-Means • Plotly • Streamlit"

)