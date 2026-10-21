"""Basic automated checks for the cleaning transformation."""
import pandas as pd
from src.clean_data import clean_sales

def sample_data():
    return pd.DataFrame([
        {"order_id":"ORD1","order_line_id":"L1","order_date":"2024-01-01","customer_id":"C1",
         "customer_segment":"Retail","product_id":"SKU1","product_name":"Notebook","category":"stationery",
         "quantity":"2","unit_price_kes":"100","discount_pct":"0.1","payment_method":"m-pesa",
         "sales_channel":"Store","county":"nairobi","town":"Nairobi","sales_rep":"REP1"},
        {"order_id":"ORD2","order_line_id":"L2","order_date":"not-a-date","customer_id":"C2",
         "customer_segment":"Retail","product_id":"SKU2","product_name":"Pen","category":"Stationery",
         "quantity":"1","unit_price_kes":"10","discount_pct":"0","payment_method":"Cash",
         "sales_channel":"Store","county":"Nairobi","town":"Nairobi","sales_rep":"REP1"},
    ])

def test_invalid_date_is_rejected():
    clean, rejected, stats = clean_sales(sample_data())
    assert len(clean) == 1
    assert len(rejected) == 1
    assert "invalid_date" in rejected.iloc[0]["rejection_reason"]

def test_net_sales_calculated_correctly():
    clean, _, _ = clean_sales(sample_data())
    assert clean.iloc[0]["net_sales_kes"] == 180.0
