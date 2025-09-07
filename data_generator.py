# data_generator.py
import numpy as np
import pandas as pd

def generate_dummy_orders(n=15000, seed=42, start="2024-01-01", end="2025-08-31"):
    np.random.seed(seed)
    products = ["Milk","Bread","Eggs","Bananas","Rice","Oil","Maggi","Curd",
                "Toothpaste","Soap","Detergent","Chicken","Paneer","Butter","Soda"]
    cities = ["Mumbai","Delhi","Bengaluru","Hyderabad","Kolkata","Chennai","Pune","Ahmedabad"]
    date_range = pd.to_datetime(np.random.randint(
        pd.Timestamp(start).value//10**9,
        pd.Timestamp(end).value//10**9,
        n), unit="s")
    product = np.random.choice(products, n)
    city = np.random.choice(cities, n, p=[0.18,0.16,0.15,0.12,0.11,0.10,0.10,0.08])
    qty = np.random.randint(1,5, n)
    base_price = {p: float(20 + 10*idx) for idx,p in enumerate(products)}  # simple base price
    sales = [round(base_price[p]*q * np.random.uniform(0.85,1.3), 2) for p,q in zip(product, qty)]
    # Make delivery times vary by city
    city_base = {"Mumbai":30,"Delhi":35,"Bengaluru":28,"Hyderabad":32,"Kolkata":40,"Chennai":33,"Pune":27,"Ahmedabad":36}
    delivery_time = [max(8, int(np.random.normal(city_base[c], 8))) for c in city]
    df = pd.DataFrame({
        "Order_ID": [f"ORD{100000+i}" for i in range(n)],
        "Product": product,
        "Order_Date": pd.to_datetime(date_range),
        "City": city,
        "Quantity": qty,
        "Sales": sales,
        "Delivery_Time_min": delivery_time
    })
    # tidy
    df = df.sort_values("Order_Date").reset_index(drop=True)
    return df

if __name__ == "__main__":
    df = generate_dummy_orders()
    df.to_csv("blinkit_dummy_orders.csv", index=False)
    print("Saved blinkit_dummy_orders.csv")
