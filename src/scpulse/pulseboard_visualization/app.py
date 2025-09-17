import streamlit as st
import polars as pl
import altair as alt
from pathlib import Path

GOLD_DIR = Path("data/gold")

st.set_page_config(
    page_title="SupplyChain Pulse",
    page_icon="📊",
    layout="wide",
)

st.title("📊 SupplyChain Pulse Dashboard")
st.caption(
    "Monitoramento em tempo real da cadeia de suprimentos (Orders, Delays, Inventory)"
)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📦 Orders", "⏳ Delays", "⚠️ Inventory"])


# ------------------- ORDERS -------------------
with tab1:
    st.header("📦 Pedidos Criados")
    df_orders = pl.read_parquet(
        GOLD_DIR / "events_2025-09-17" / "gold_orders_created.parquet"
    )

    # KPIs
    total_orders = int(df_orders["total_orders"].sum())
    total_qty = int(df_orders["total_qty"].sum())
    avg_per_supplier = (
        df_orders.group_by("supplier")
        .agg(pl.sum("total_orders").alias("supplier_orders"))[
            "supplier_orders"
        ]
        .mean()
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Pedidos", total_orders)
    col2.metric("Quantidade Total de Produtos x Pedido", total_qty)
    col3.metric("Média por Fornecedor", f"{avg_per_supplier:.1f}")

    # Evolução temporal
    st.subheader("📈 Evolução de Pedidos por Fornecedor")
    chart = (
        alt.Chart(df_orders.to_pandas())
        .mark_line(point=True)
        .encode(
            x="date:T",
            y="total_orders:Q",
            color="supplier:N",
            tooltip=["supplier", "date", "total_orders", "total_qty"],
        )
        .properties(width="container", height=400)
    )
    st.altair_chart(chart, use_container_width=True)


# ------------------- DELAYS -------------------
with tab2:
    st.header("⏳ Pedidos Atrasados")
    df_delays = pl.read_parquet(
        GOLD_DIR / "events_2025-09-17" / "gold_orders_delayed.parquet"
    )

    # KPIs
    total_delayed = int(df_delays["delayed_orders"].sum())
    avg_delay = float(df_delays["avg_delay_days"].mean())

    col1, col2 = st.columns(2)
    col1.metric("Pedidos Atrasados", total_delayed)
    col2.metric("Atraso Médio (dias)", f"{avg_delay:.1f}")

    # Ranking de fornecedores mais críticos
    st.subheader("🏭 Ranking de Fornecedores com Mais Atrasos")
    st.bar_chart(df_delays.to_pandas(), x="supplier", y="delayed_orders")


# ------------------- INVENTORY -------------------
with tab3:
    st.header("⚠️ Alertas de Estoque")
    df_inventory = pl.read_parquet(
        GOLD_DIR / "events_2025-09-17" / "gold_inventory_alerts.parquet"
    )

    total_alerts = int(df_inventory["low_stock_alerts"].sum())
    min_threshold = int(df_inventory["min_threshold"].min())

    col1, col2 = st.columns(2)
    col1.metric("Total de Alertas", total_alerts)
    col2.metric("Threshold Mínimo", min_threshold)

    st.subheader("📊 Alertas por SKU")
    chart_inv = (
        alt.Chart(df_inventory.to_pandas())
        .mark_bar()
        .encode(
            x="sku:N",
            y="low_stock_alerts:Q",
            color="sku:N",
            tooltip=["sku", "low_stock_alerts", "min_threshold"],
        )
        .properties(width="container", height=400)
    )
    st.altair_chart(chart_inv, use_container_width=True)
