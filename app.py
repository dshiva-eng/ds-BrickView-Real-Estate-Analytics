import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
USER = "postgres"
PASSWORD = "258963"
HOST = "localhost"
PORT = "5432"
DB_NAME = "brickview"

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

st.set_page_config(page_title="BrickView Real Estate", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f7fb;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    h1, h2, h3 {
        color: #263238;
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #e83e6f;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown(
    """
    <div style="text-align:center; padding: 10px 0 20px 0;">
        <div style="font-size:42px;">&#127968;</div>
        <h2 style="margin-bottom:0; color:#e83e6f;">BrickView</h2>
        <p style="font-size:14px; color:#6c757d;">Real Estate Intelligence</p>
    </div>
    """,
    unsafe_allow_html=True
)

menu = st.sidebar.radio(
    "Navigation",
    [
        "1. Intro",
        "2. Query",
        "3. Visualization",
        "4. CRUD Operation",
        "5. SQL Query"
    ]
)

st.title("BrickView Real Estate")

# Load listings data
query = """
SELECT l.*,
       p.bedrooms,
       p.bathrooms,
       p.furnishing_status,
       p.metro_distance_km,
       p.parking_available,
       p.power_backup
FROM listings l
JOIN property_attributes p
ON l.listing_id = p.listing_id
"""
df = pd.read_sql(query, engine)
if menu == "1. Intro":
    st.header("Welcome to BrickView Real Estate")
    st.write("""
    A next-generation real estate analytics platform designed to transform raw property data
    into actionable business insights. BrickView helps real estate professionals track property
    listings, monitor sales trends, analyze buyer behavior, and evaluate agent performance —
    all through interactive dashboards and live database-driven analytics.
    """)
elif menu == "2. Query":
    st.header("Query")

    # Sidebar filters
    st.sidebar.header("Filter Listings")
    
    city_options = df["city"].dropna().unique()
    selected_city = st.sidebar.selectbox(
        "Select City",
        ["All"] + sorted(city_options.tolist())
    )
    
    property_options = df["property_type"].dropna().unique()
    selected_property = st.sidebar.selectbox(
        "Select Property Type",
        ["All"] + sorted(property_options.tolist())
    )
    
    min_price = int(df["price"].min())
    max_price = int(df["price"].max())
    selected_price = st.sidebar.slider(
        "Select Price Range",
        min_price,
        max_price,
        (min_price, max_price)
    )
    st.sidebar.markdown("### Optional Comfort Filters")

    bedroom_options = sorted(df["bedrooms"].dropna().unique().tolist())
    selected_bedrooms = st.sidebar.selectbox(
        "Select Bedrooms",
        ["All"] + bedroom_options
    )

    furnishing_options = sorted(df["furnishing_status"].dropna().unique().tolist())
    selected_furnishing = st.sidebar.selectbox(
        "Furnishing Status",
        ["All"] + furnishing_options
    )

    max_metro_distance = float(df["metro_distance_km"].max())
    selected_metro_distance = st.sidebar.slider(
        "Maximum Distance from Metro (km)",
        0.0,
        max_metro_distance,
        max_metro_distance
    )

    selected_parking = st.sidebar.selectbox(
        "Parking Available",
        ["All", "Yes", "No"]
    )

    selected_power_backup = st.sidebar.selectbox(
        "Power Backup",
        ["All", "Yes", "No"]
    )
    # Apply filters
    filtered_df = df.copy()
    
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["city"] == selected_city]
    
    if selected_property != "All":
        filtered_df = filtered_df[filtered_df["property_type"] == selected_property]
        
    if selected_bedrooms != "All":
        filtered_df = filtered_df[filtered_df["bedrooms"] == selected_bedrooms]

    if selected_furnishing != "All":
        filtered_df = filtered_df[filtered_df["furnishing_status"] == selected_furnishing]

    filtered_df = filtered_df[
        filtered_df["metro_distance_km"] <= selected_metro_distance
    ]

    if selected_parking == "Yes":
        filtered_df = filtered_df[filtered_df["parking_available"] == True]
    elif selected_parking == "No":
        filtered_df = filtered_df[filtered_df["parking_available"] == False]

    if selected_power_backup == "Yes":
        filtered_df = filtered_df[filtered_df["power_backup"] == True]
    elif selected_power_backup == "No":
        filtered_df = filtered_df[filtered_df["power_backup"] == False]
        
    filtered_df = filtered_df[
        (filtered_df["price"] >= selected_price[0]) &
        (filtered_df["price"] <= selected_price[1])
    ]
    
    # KPI metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Listings", len(filtered_df))
    col2.metric("Average Price", f"${filtered_df['price'].mean():,.2f}")
    col3.metric("Average Sqft", f"{filtered_df['sqft'].mean():,.2f}")
    # Show filtered data
    st.write("Filtered Listings Data")
    st.dataframe(filtered_df)

elif menu == "3. Visualization":
    st.header("Visualization")

    city_price_query = """
    SELECT city, ROUND(AVG(price), 2) AS avg_listing_price
    FROM listings
    GROUP BY city
    ORDER BY avg_listing_price DESC
    """
    city_price_df = pd.read_sql(city_price_query, engine)
    
    fig = px.bar(
        city_price_df,
        x="city",
        y="avg_listing_price",
        title="Average Listing Price by City",
        color="city"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    property_type_query = """
    SELECT property_type, COUNT(*) AS total_properties
    FROM listings
    GROUP BY property_type
    ORDER BY total_properties DESC
    """
    property_type_df = pd.read_sql(property_type_query, engine)
    
    fig2 = px.pie(
        property_type_df,
        names="property_type",
        values="total_properties",
        title="Property Type Distribution"
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    sales_trend_query = """
    SELECT DATE_TRUNC('month', date_sold) AS sale_month,
           COUNT(*) AS total_sales
    FROM sales
    GROUP BY sale_month
    ORDER BY sale_month
    """
    sales_trend_df = pd.read_sql(sales_trend_query, engine)
    
    fig3 = px.line(
        sales_trend_df,
        x="sale_month",
        y="total_sales",
        title="Monthly Sales Trend",
        markers=True
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    map_query = """
    SELECT city, latitude, longitude, price, property_type
    FROM listings
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    map_df = pd.read_sql(map_query, engine)
    map_df = map_df.sample(min(500, len(map_df)), random_state=42)
        
    st.subheader("Property Listings Map")
    st.map(map_df[["latitude", "longitude"]])
elif menu == "5. SQL Query":
    st.header("SQL Query")
    
    queries = {
        "Average Listing Price by City": """
            SELECT city, ROUND(AVG(price), 2) AS avg_listing_price
            FROM listings
            GROUP BY city
            ORDER BY avg_listing_price DESC
        """,
    
        "Average Price per Square Foot by Property Type": """
            SELECT property_type,
                   ROUND(AVG(price / sqft), 2) AS avg_price_per_sqft
            FROM listings
            GROUP BY property_type
            ORDER BY avg_price_per_sqft DESC
        """,
    
        "Furnishing Status Impact on Price": """
            SELECT p.furnishing_status,
                   ROUND(AVG(l.price), 2) AS avg_price
            FROM listings l
            JOIN property_attributes p
            ON l.listing_id = p.listing_id
            GROUP BY p.furnishing_status
            ORDER BY avg_price DESC
        """,
    
        "Metro Distance vs Price": """
            SELECT 
                CASE
                    WHEN p.metro_distance_km <= 2 THEN '0-2 km'
                    WHEN p.metro_distance_km <= 5 THEN '2-5 km'
                    WHEN p.metro_distance_km <= 10 THEN '5-10 km'
                    ELSE '10+ km'
                END AS metro_distance_bucket,
                ROUND(AVG(l.price), 2) AS avg_price
            FROM listings l
            JOIN property_attributes p
            ON l.listing_id = p.listing_id
            GROUP BY metro_distance_bucket
            ORDER BY avg_price DESC
        """,
    
        "Rented vs Non-Rented Pricing": """
            SELECT p.is_rented,
                   ROUND(AVG(l.price), 2) AS avg_price
            FROM listings l
            JOIN property_attributes p
            ON l.listing_id = p.listing_id
            GROUP BY p.is_rented
            ORDER BY avg_price DESC
        """,
    
        "Bedrooms and Bathrooms vs Pricing": """
            SELECT p.bedrooms,
                   p.bathrooms,
                   ROUND(AVG(l.price), 2) AS avg_price
            FROM listings l
            JOIN property_attributes p
            ON l.listing_id = p.listing_id
            GROUP BY p.bedrooms, p.bathrooms
            ORDER BY avg_price DESC
        """,
    
        "Parking and Power Backup vs Price": """
            SELECT p.parking_available,
                   p.power_backup,
                   ROUND(AVG(l.price), 2) AS avg_price
            FROM listings l
            JOIN property_attributes p
            ON l.listing_id = p.listing_id
            GROUP BY p.parking_available, p.power_backup
            ORDER BY avg_price DESC
        """,
    
        "Year Built vs Listing Price": """
            SELECT p.year_built,
                   ROUND(AVG(l.price), 2) AS avg_price
            FROM listings l
            JOIN property_attributes p
            ON l.listing_id = p.listing_id
            GROUP BY p.year_built
            ORDER BY p.year_built
        """,
    
        "Median Property Prices by City": """
            SELECT city,
                   ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)::numeric, 2) AS median_price
            FROM listings
            GROUP BY city
            ORDER BY median_price DESC
        """,
    
        "Property Distribution Across Price Buckets": """
            SELECT 
                CASE
                    WHEN price < 200000 THEN 'Below 200K'
                    WHEN price < 500000 THEN '200K - 500K'
                    WHEN price < 1000000 THEN '500K - 1M'
                    ELSE 'Above 1M'
                END AS price_bucket,
                COUNT(*) AS property_count
            FROM listings
            GROUP BY price_bucket
            ORDER BY property_count DESC
        """,
    
        "Average Days on Market by City": """
            SELECT l.city,
                   ROUND(AVG(s.days_on_market), 2) AS avg_days_on_market
            FROM listings l
            JOIN sales s
            ON l.listing_id = s.listing_id
            GROUP BY l.city
            ORDER BY avg_days_on_market DESC
        """,
    
        "Fastest-Selling Property Types": """
            SELECT l.property_type,
                   ROUND(AVG(s.days_on_market), 2) AS avg_days_on_market
            FROM listings l
            JOIN sales s
            ON l.listing_id = s.listing_id
            GROUP BY l.property_type
            ORDER BY avg_days_on_market ASC
        """,
    
        "Percentage Sold Above Listing Price": """
            SELECT 
                ROUND(
                    100.0 * SUM(CASE WHEN s.sale_price > l.price THEN 1 ELSE 0 END) / COUNT(*),
                    2
                ) AS percent_sold_above_listing
            FROM listings l
            JOIN sales s
            ON l.listing_id = s.listing_id
        """,
    
        "Sale-to-List Price Ratio by City": """
            SELECT l.city,
                   ROUND(AVG(s.sale_price / l.price), 2) AS sale_to_list_ratio
            FROM listings l
            JOIN sales s
            ON l.listing_id = s.listing_id
            GROUP BY l.city
            ORDER BY sale_to_list_ratio DESC
        """,
    
        "Listings Taking More Than 90 Days to Sell": """
            SELECT l.listing_id,
                   l.city,
                   l.property_type,
                   s.sale_price,
                   s.days_on_market
            FROM listings l
            JOIN sales s
            ON l.listing_id = s.listing_id
            WHERE s.days_on_market > 90
            ORDER BY s.days_on_market DESC
        """,
    
        "Metro Distance vs Time on Market": """
            SELECT 
                CASE
                    WHEN p.metro_distance_km <= 2 THEN '0-2 km'
                    WHEN p.metro_distance_km <= 5 THEN '2-5 km'
                    WHEN p.metro_distance_km <= 10 THEN '5-10 km'
                    ELSE '10+ km'
                END AS metro_distance_bucket,
                ROUND(AVG(s.days_on_market), 2) AS avg_days_on_market
            FROM property_attributes p
            JOIN sales s
            ON p.listing_id = s.listing_id
            GROUP BY metro_distance_bucket
            ORDER BY avg_days_on_market
        """,
    
        "Top Agents by Total Sales Revenue": """
            SELECT a.name,
                   ROUND(SUM(s.sale_price), 2) AS total_sales_revenue
            FROM agents a
            JOIN listings l
            ON a.agent_id = l.agent_id
            JOIN sales s
            ON l.listing_id = s.listing_id
            GROUP BY a.name
            ORDER BY total_sales_revenue DESC
            LIMIT 10
        """,
    
        "Unsold Properties": """
            SELECT l.listing_id, l.city, l.property_type, l.price, l.date_listed
            FROM listings l
            LEFT JOIN sales s
            ON l.listing_id = s.listing_id
            WHERE s.listing_id IS NULL
        """,
    
        "Buyer Type Percentage": """
            SELECT buyer_type,
                   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
            FROM buyers
            GROUP BY buyer_type
            ORDER BY percentage DESC
        """,
    
        "Monthly Sales Trend": """
            SELECT DATE_TRUNC('month', date_sold) AS sale_month,
                   COUNT(*) AS total_sales
            FROM sales
            GROUP BY sale_month
            ORDER BY sale_month
        """,
    
           "Agents with Most Sales": """
            SELECT a.name,
                   COUNT(s.listing_id) AS total_sales
            FROM agents a
            JOIN listings l
            ON a.agent_id = l.agent_id
            JOIN sales s
            ON l.listing_id = s.listing_id
            GROUP BY a.name
            ORDER BY total_sales DESC
            LIMIT 10
        """,
    
        "Agents Closing Deals Fastest": """
            SELECT a.name,
                   ROUND(AVG(s.days_on_market), 2) AS avg_closing_time
            FROM agents a
            JOIN listings l
            ON a.agent_id = l.agent_id
            JOIN sales s
            ON l.listing_id = s.listing_id
            GROUP BY a.name
            ORDER BY avg_closing_time ASC
            LIMIT 10
        """,
    
        "Experience vs Deals Closed": """
            SELECT experience_years,
                   ROUND(AVG(deals_closed), 2) AS avg_deals_closed
            FROM agents
            GROUP BY experience_years
            ORDER BY experience_years
        """,
    
        "Ratings vs Closing Speed": """
            SELECT rating,
                   ROUND(AVG(avg_closing_days), 2) AS avg_closing_days
            FROM agents
            GROUP BY rating
            ORDER BY rating DESC
        """,
    
        "Average Commission Earned by Agent": """
            SELECT a.name,
                   ROUND(AVG(s.sale_price * a.commission_rate / 100), 2) AS avg_commission_earned
            FROM agents a
            JOIN listings l
            ON a.agent_id = l.agent_id
            JOIN sales s
            ON l.listing_id = s.listing_id
            GROUP BY a.name
            ORDER BY avg_commission_earned DESC
        """,
    
        "Agents with Most Active Listings": """
            SELECT a.name,
                   COUNT(l.listing_id) AS active_listings
            FROM agents a
            JOIN listings l
            ON a.agent_id = l.agent_id
            LEFT JOIN sales s
            ON l.listing_id = s.listing_id
            WHERE s.listing_id IS NULL
            GROUP BY a.name
            ORDER BY active_listings DESC
            LIMIT 10
        """,
    
        "Cities with Highest Loan Uptake Rate": """
            SELECT l.city,
                   ROUND(
                       100.0 * SUM(CASE WHEN b.loan_taken = TRUE THEN 1 ELSE 0 END) / COUNT(*),
                       2
                   ) AS loan_uptake_rate
            FROM buyers b
            JOIN sales s
            ON b.sale_id = s.listing_id
            JOIN listings l
            ON s.listing_id = l.listing_id
            GROUP BY l.city
            ORDER BY loan_uptake_rate DESC
        """,
    
        "Average Loan Amount by Buyer Type": """
            SELECT buyer_type,
                   ROUND(AVG(loan_amount), 2) AS avg_loan_amount
            FROM buyers
            WHERE loan_taken = TRUE
            GROUP BY buyer_type
            ORDER BY avg_loan_amount DESC
        """,
    
        "Most Common Payment Mode": """
            SELECT payment_mode,
                   COUNT(*) AS total_transactions
            FROM buyers
            GROUP BY payment_mode
            ORDER BY total_transactions DESC
        """,
    
        "Loan-Backed Purchases vs Closing Time": """
            SELECT b.loan_taken,
                   ROUND(AVG(s.days_on_market), 2) AS avg_days_on_market
            FROM buyers b
            JOIN sales s
            ON b.sale_id = s.listing_id
            GROUP BY b.loan_taken
            ORDER BY avg_days_on_market DESC
        """,
     
    }
    
    selected_query_name = st.selectbox("Select a SQL Query", list(queries.keys()))
    query_result = pd.read_sql(queries[selected_query_name], engine)
    
    st.write("### Query Output")
    st.dataframe(query_result)

elif menu == "4. CRUD Operation":
    st.header("CRUD Operation")
    st.subheader("Database Table Operations")

    table_config = {
        "agents": "agent_id",
        "listings": "listing_id",
        "property_attributes": "attribute_id",
        "buyers": "buyer_id",
        "sales": "listing_id"
    }

    selected_table = st.selectbox(
        "Select Table",
        list(table_config.keys()),
        key="crud_table_select"
    )

    primary_key = table_config[selected_table]

    table_df = pd.read_sql(f"SELECT * FROM {selected_table}", engine)
    st.write(f"### {selected_table.title()} Table")
    st.dataframe(table_df)

    crud_action = st.selectbox(
        "Choose Action",
        ["View", "Add", "Update", "Delete"],
        key="crud_action"
    )

    columns = table_df.columns.tolist()

    if crud_action == "View":
        st.dataframe(table_df)

    elif crud_action == "Add":
        st.subheader(f"Add New Record to {selected_table}")

        with st.form("add_record_form"):
            new_values = {}
            for col in columns:
                if pd.api.types.is_integer_dtype(table_df[col]):
                    new_values[col] = st.number_input(col, value=0, step=1)
                elif pd.api.types.is_float_dtype(table_df[col]):
                    new_values[col] = st.number_input(col, value=0.0)
                elif pd.api.types.is_bool_dtype(table_df[col]):
                    new_values[col] = st.checkbox(col)
                else:
                    new_values[col] = st.text_input(col)

            submit_add = st.form_submit_button("Add Record")

            if submit_add:
                column_names = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])

                insert_query = text(
                    f"INSERT INTO {selected_table} ({column_names}) VALUES ({placeholders})"
                )

                with engine.begin() as connection:
                    connection.execute(insert_query, new_values)
                    
                st.success("Record added successfully!")
                
    elif crud_action == "Update":
        st.subheader(f"Update Record in {selected_table}")

        ids = table_df[primary_key].tolist()
        selected_id = st.selectbox(
            f"Select {primary_key} to Update",
            ids,
            key="update_record_id"
        )

        record_data = pd.read_sql(
            f"SELECT * FROM {selected_table} WHERE {primary_key} = '{selected_id}'",
            engine
        ).iloc[0]

        with st.form("update_record_form"):
            updated_values = {}

            for col in columns:
                if col == primary_key:
                    st.text_input(col, value=str(record_data[col]), disabled=True)
                    updated_values[col] = record_data[col]
                elif pd.api.types.is_numeric_dtype(table_df[col]):
                    updated_values[col] = st.number_input(
                        col,
                        value=float(record_data[col]) if pd.notna(record_data[col]) else 0.0
                    )
                elif pd.api.types.is_bool_dtype(table_df[col]):
                    updated_values[col] = st.checkbox(
                        col,
                        value=bool(record_data[col])
                    )
                else:
                    updated_values[col] = st.text_input(
                        col,
                        value=str(record_data[col]) if pd.notna(record_data[col]) else ""
                    )

            submit_update = st.form_submit_button("Update Record")

            if submit_update:
                set_clause = ", ".join(
                    [f"{col} = :{col}" for col in columns if col != primary_key]
                )
                update_query = text(
                    f"UPDATE {selected_table} SET {set_clause} WHERE {primary_key} = :{primary_key}"
                )

                for col in columns:
                    if pd.api.types.is_integer_dtype(table_df[col]):
                        updated_values[col] = int(updated_values[col])
                    elif pd.api.types.is_float_dtype(table_df[col]):
                        updated_values[col] = float(updated_values[col])
                    elif pd.api.types.is_bool_dtype(table_df[col]):
                        updated_values[col] = bool(updated_values[col])

                with engine.begin() as connection:
                    connection.execute(update_query, updated_values)     

                st.success("Record updated successfully!")

    elif crud_action == "Delete":
        st.subheader(f"Delete Record from {selected_table}")

        ids = table_df[primary_key].tolist()
        selected_id = st.selectbox(
            f"Select {primary_key} to Delete",
            ids,
            key="delete_record_id"
        )

        if st.button("Delete Record"):
            delete_query = text(
                f"DELETE FROM {selected_table} WHERE {primary_key} = :selected_id"
            )

            with engine.begin() as connection:
                connection.execute(delete_query, {"selected_id": selected_id})

            st.success("Record deleted successfully!")
