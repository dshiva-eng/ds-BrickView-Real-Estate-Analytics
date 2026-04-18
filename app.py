import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

USER = "postgres"
PASSWORD = "your_password"
HOST = "localhost"
PORT = "5432"
DB_NAME = "brickview"

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

st.title("BrickView: Real Estate Analytics Platform")
st.subheader("Real Estate Listings Dashboard")

# Load listings data
query = "SELECT * FROM listings"
df = pd.read_sql(query, engine)

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

# Apply filters
filtered_df = df.copy()

if selected_city != "All":
    filtered_df = filtered_df[filtered_df["city"] == selected_city]

if selected_property != "All":
    filtered_df = filtered_df[filtered_df["property_type"] == selected_property]

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
import plotly.express as px
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
map_df = pd.read_sql(map_query, engine).sample(500, random_state=42)

st.subheader("Property Listings Map")
st.map(map_df[["latitude", "longitude"]])
st.subheader("SQL Queries Display")

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

st.write("### SQL Query")
st.code(queries[selected_query_name], language="sql")

query_result = pd.read_sql(queries[selected_query_name], engine)

st.write("### Query Output")
st.dataframe(query_result)
st.subheader("Agents CRUD Operations")

crud_action = st.selectbox(
    "Choose Action",
    ["View", "Add", "Update", "Delete"],
    key="agents_crud_action"
)

if crud_action == "View":
    agents_df = pd.read_sql("SELECT * FROM agents", engine)
    st.dataframe(agents_df)

elif crud_action == "Add":
    with st.form("add_agent_form"):
        agent_id = st.text_input("Agent ID")
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        commission_rate = st.number_input("Commission Rate", min_value=0.0, step=0.1)
        deals_closed = st.number_input("Deals Closed", min_value=0, step=1)
        rating = st.number_input("Rating", min_value=0.0, max_value=5.0, step=0.1)
        experience_years = st.number_input("Experience Years", min_value=0, step=1)
        avg_closing_days = st.number_input("Average Closing Days", min_value=0, step=1)

        submit_add = st.form_submit_button("Add Agent")

        if submit_add:
            insert_query = text("""
                INSERT INTO agents (
                    agent_id, name, phone, email,
                    commission_rate, deals_closed, rating,
                    experience_years, avg_closing_days
                )
                VALUES (
                    :agent_id, :name, :phone, :email,
                    :commission_rate, :deals_closed, :rating,
                    :experience_years, :avg_closing_days
                )
            """)

            with engine.begin() as connection:
                connection.execute(insert_query, {
                    "agent_id": agent_id,
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "commission_rate": commission_rate,
                    "deals_closed": deals_closed,
                    "rating": rating,
                    "experience_years": experience_years,
                    "avg_closing_days": avg_closing_days
                })

            st.success("Agent added successfully!")

elif crud_action == "Update":
    agent_ids = pd.read_sql("SELECT agent_id FROM agents ORDER BY agent_id", engine)["agent_id"].tolist()
    selected_agent_id = st.selectbox("Select Agent ID to Update", agent_ids, key="update_agent_id")

    agent_data = pd.read_sql(
        f"SELECT * FROM agents WHERE agent_id = '{selected_agent_id}'",
        engine
    ).iloc[0]

    with st.form("update_agent_form"):
        name = st.text_input("Name", value=agent_data["name"])
        phone = st.text_input("Phone", value=agent_data["phone"])
        email = st.text_input("Email", value=agent_data["email"])
        commission_rate = st.number_input("Commission Rate", min_value=0.0, step=0.1, value=float(agent_data["commission_rate"]))
        deals_closed = st.number_input("Deals Closed", min_value=0, step=1, value=int(agent_data["deals_closed"]))
        rating = st.number_input("Rating", min_value=0.0, max_value=5.0, step=0.1, value=float(agent_data["rating"]))
        experience_years = st.number_input("Experience Years", min_value=0, step=1, value=int(agent_data["experience_years"]))
        avg_closing_days = st.number_input("Average Closing Days", min_value=0, step=1, value=int(agent_data["avg_closing_days"]))

        submit_update = st.form_submit_button("Update Agent")

        if submit_update:
            update_query = text("""
                UPDATE agents
                SET name = :name,
                    phone = :phone,
                    email = :email,
                    commission_rate = :commission_rate,
                    deals_closed = :deals_closed,
                    rating = :rating,
                    experience_years = :experience_years,
                    avg_closing_days = :avg_closing_days
                WHERE agent_id = :agent_id
            """)

            with engine.begin() as connection:
                connection.execute(update_query, {
                    "agent_id": selected_agent_id,
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "commission_rate": commission_rate,
                    "deals_closed": deals_closed,
                    "rating": rating,
                    "experience_years": experience_years,
                    "avg_closing_days": avg_closing_days
                })

            st.success("Agent updated successfully!")
elif crud_action == "Delete":
    agent_ids = pd.read_sql("SELECT agent_id FROM agents ORDER BY agent_id", engine)["agent_id"].tolist()
    selected_agent_id = st.selectbox("Select Agent ID to Delete", agent_ids, key="delete_agent_id")

    if st.button("Delete Agent"):
        delete_query = text("DELETE FROM agents WHERE agent_id = :agent_id")

        with engine.begin() as connection:
            connection.execute(delete_query, {"agent_id": selected_agent_id})

        st.success("Agent deleted successfully!")


