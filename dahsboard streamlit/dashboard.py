# import library
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style="dark")

# load data
data = pd.read_csv("data_main.csv")

st.header('Olist Store Dashboard')

# define helper function
def create_month_orders_df(df):
    daily_orders_df = df.resample(rule='M', on='order_approved_at').agg({
        "order_id": "nunique",
        "payment_value": "sum",
        "customer_id" : "count",
        "review_score" : "mean"
    })
    daily_orders_df.index = daily_orders_df.index.strftime('%Y-%m')
    daily_orders_df = daily_orders_df.reset_index()
    return daily_orders_df

def create_count_order_items_df(df):
    count_order_items_df = data.groupby("product_category_name").order_id.count().sort_values(ascending=False).reset_index()
    return count_order_items_df

def create_rfm_seller(df):
    rfm_df_seller = data.groupby(by="seller_id", as_index=False).agg({
        "order_approved_at" : "max", # mengambil tanggal order terakhir
        "order_id" : "count", # menghitung jumlah order
        "payment_value" : "sum" # menghitung jumlah revenue yang dihasilkan
    })

    rfm_df_seller.columns = ["seller_id", "max_sell_timestamp", "frequency", "monetary"]

    rfm_df_seller["max_sell_timestamp"] = rfm_df_seller["max_sell_timestamp"].dt.date
    recent_date = data["order_approved_at"].dt.date.max()
    rfm_df_seller["recency"] = rfm_df_seller["max_sell_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df_seller.drop("max_sell_timestamp", axis=1, inplace=True)
    return rfm_df_seller

def create_rfm_customer(df):
    rfm_df_customer = data.groupby(by="customer_id", as_index=False).agg({
        "order_approved_at" : "max",
        "order_id" : "count",
        "payment_value" : "sum"
    })

    rfm_df_customer.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df_customer["max_order_timestamp"] = rfm_df_customer["max_order_timestamp"].dt.date
    recent_date = data["order_approved_at"].dt.date.max()
    rfm_df_customer["recency"] = rfm_df_customer["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df_customer.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df_customer


datetime_columns = ["shipping_limit_date", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", 
"order_delivered_customer_date", "order_estimated_delivery_date", "review_creation_date","review_answer_timestamp"]
data.sort_values(by="order_purchase_timestamp", inplace=True)
data.reset_index(inplace=True)

for column in datetime_columns:
    data[column] = pd.to_datetime(data[column], errors='coerce', infer_datetime_format=True)

# membuat komponen filter
min_date = data["order_approved_at"].min()
max_date = data["order_approved_at"].max()

with st.sidebar:
    st.image("pict.png", width=15, use_column_width="auto")
    start_date, end_date = st.date_input(
        label = "Select Date",
        min_value = min_date,
        max_value = max_date,
        value=[min_date, max_date]
    )

# simpan tanggal yang dipilih
main_df = data[(data["order_approved_at"] >= str(start_date)) & (data["order_approved_at"] <= str(end_date))]
    
# panggil helper function
daily_orders_df = create_month_orders_df(main_df)
count_order_produk = create_count_order_items_df(main_df)
rfm_df_seller = create_rfm_seller(main_df)
rfm_df_customer = create_rfm_customer(main_df)



# visualisasi performa penjualan
st.subheader('Sales Performance')
col1, col2, col3, col4 = st.columns(4)
 
with col1:
    total_orders = daily_orders_df.order_id.sum()
    st.metric("Total orders", value=total_orders)
 
with col2:
    total_revenue = format_currency(daily_orders_df.payment_value.sum(), "USD", locale='en_US') 
    st.metric("Total Revenue", value=total_revenue)

 
with col3:
    total_customer = daily_orders_df.customer_id.sum() 
    st.metric("Total Customer", value=total_customer)

with col4:
    avg_score = round(daily_orders_df.review_score.mean(), 2)
    st.metric("Average of Review Score", value=avg_score)

col1, col2 = st.columns(2)
with col1:
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(
        daily_orders_df["order_approved_at"],
        daily_orders_df["order_id"],
        marker='o', 
        linewidth=2,
        color="#90CAF9"
    )
    ax.set_title("Total Orders by Month", size=40)
    ax.tick_params(axis='y', labelsize=20)
    ax.tick_params(axis='x', labelsize=15, rotation=90)
    
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(
        daily_orders_df["order_approved_at"],
        daily_orders_df["payment_value"],
        marker='o', 
        linewidth=2,
        color="#90CAF9"
    )
    ax.set_title("Total Revenue by Month", size=40)
    ax.tick_params(axis='y', labelsize=20)
    ax.tick_params(axis='x', labelsize=15, rotation=90)
    
    st.pyplot(fig)

# visualisasi produk
st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35,15))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(x="order_id", y="product_category_name", data=count_order_produk.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Order", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="order_id", y="product_category_name", data=count_order_produk.sort_values(by="order_id", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Order", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)
st.pyplot(fig)

# visualisasi Demografi Seller
st.subheader("Demografi Sellers")

total_seller = data.seller_id.nunique()
st.metric("Total Seller", value=total_seller)
fig, ax = plt.subplots(figsize=(8, 4))

bystate_seller = data.groupby(by="seller_state").seller_id.nunique().reset_index()
bystate_seller.rename(columns={"seller_id": "seller_count"}, inplace=True)

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
        y="seller_count",
        x="seller_state",
        data=bystate_seller.sort_values(by="seller_count", ascending=False).head(),
        palette=colors,
        ax=ax
)
    
# Customize the plot
ax.set_title("Number of Sellers by States", loc="left", fontsize=15)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)

# Show the Streamlit app
st.pyplot(fig)

# visualisasi Demografi Customer
st.subheader("Demografi Customer")
total_seller = data.order_id.nunique()
st.metric("Total Customer", value=total_seller)
fig, ax = plt.subplots(figsize= (8, 4))
    
bystate_customer = data.groupby(by="customer_state").customer_id.nunique().reset_index()
bystate_customer.rename(columns={"customer_id": "customer_count"}, inplace=True)

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    y="customer_count",
    x="customer_state",
    data=bystate_customer.sort_values(by="customer_count", ascending=False).head(),
    palette=colors,
    ax=ax
)
    
# Customize the plot
ax.set_title("Number of Customer by States", loc="left", fontsize=15)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)

# Show the Streamlit app
st.pyplot(fig)


# Visualisasi RFM Seller
st.subheader("Best Seller Based on RFM Parameters")
 
col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(rfm_df_seller.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_df_seller.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(rfm_df_seller.monetary.mean(), "USD", locale='en_US') 
    st.metric("Average Monetary", value=avg_frequency)
 
fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]
 
sns.barplot(x="recency", y="seller_id", data=rfm_df_seller.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_xlabel(None)
ax[0].set_ylabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)
 
sns.barplot(x="frequency", y="seller_id", data=rfm_df_seller.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_xlabel(None)
ax[1].set_ylabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)
 
sns.barplot(x="monetary", y="seller_id", data=rfm_df_seller.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_xlabel(None)
ax[2].set_ylabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)
 
plt.tight_layout()
st.pyplot(fig)

# Visualisasi RFM Customer
st.subheader("Best Customer Based on RFM Parameters")
 
col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(rfm_df_customer.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_df_customer.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(rfm_df_customer.monetary.mean(), "USD", locale='en_US') 
    st.metric("Average Monetary", value=avg_frequency)
 
fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]
 
sns.barplot(x="recency", y="customer_id", data=rfm_df_customer.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_xlabel(None)
ax[0].set_ylabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)
 
sns.barplot(x="frequency", y="customer_id", data=rfm_df_customer.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_xlabel(None)
ax[1].set_ylabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)
 
sns.barplot(x="monetary", y="customer_id", data=rfm_df_customer.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_xlabel(None)
ax[2].set_ylabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)
 
plt.tight_layout()
st.pyplot(fig)