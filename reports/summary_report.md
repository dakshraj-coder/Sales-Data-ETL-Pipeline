# Sales ETL Summary Report

Generated on: 2026-11-13 23:53

## Pipeline run
- Rows extracted from CSV files: 735
- Exact duplicates removed: 15
- Duplicate order IDs removed: 0
- Invalid rows rejected: 38
- Clean rows: 682
- New rows inserted into the database: 682
- Rows skipped (already in the database): 0

## Key results (from SQL queries)
- Total revenue: INR 814,337.45
- Total orders: 682
- Average order value: INR 1,194.04
- Highest-revenue category: Electronics (INR 294,675.55)

## Top 10 products by units sold
```
product_id          product_name       category  units_sold   revenue
      P016         Skipping Rope        Fitness          84  20069.40
      P019      SQL Basics Guide          Books          80  30663.15
      P006    Spiral Notebook A5     Stationery          77   8796.00
      P012         LED Desk Lamp Home & Kitchen          74  64053.75
      P014              Yoga Mat        Fitness          74  57168.45
      P010 Steel Water Bottle 1L Home & Kitchen          74  43068.10
      P004   Power Bank 10000mAh    Electronics          72 103431.00
      P015  Resistance Bands Set        Fitness          72  38402.55
      P009       Highlighter Set     Stationery          69  14564.00
      P017     Dumbbell Pair 5kg        Fitness          64  80278.20
```

## Revenue by category
```
      category  units_sold   revenue
   Electronics         274 294675.55
Home & Kitchen         258 207901.05
       Fitness         294 195918.60
         Books         160  66509.75
    Stationery         248  49332.50
```

## Monthly sales
```
order_month  orders  units_sold   revenue
    2024-01      66         118  87718.45
    2024-02      80         135  81675.85
    2024-03      65         100  71696.85
    2024-04      72         122  76241.05
    2024-05      81         142  96451.65
    2024-06      78         154  90967.85
    2024-07      93         176 113373.90
    2024-08      80         179 109777.40
    2024-09      67         108  86434.45
```

## Top 10 customers by revenue
```
customer_id customer_name      city  orders  total_revenue
      C1044   Rohan Kumar   Kolkata      24       33164.20
      C1019 Sanjana Gupta     Kochi      19       27534.70
      C1032   Vivaan Iyer Hyderabad      20       26331.55
      C1039     Neha Nair     Kochi      20       25387.45
      C1030  Ananya Kumar    Jaipur      17       24309.25
      C1024   Nisha Kumar      Pune      18       23838.95
      C1006  Karthik Iyer    Jaipur      23       22932.90
      C1045 Sanjana Reddy   Kolkata      15       22327.95
      C1001    Sai Sharma   Chennai      12       21703.55
      C1011   Rohan Joshi   Kolkata      16       21116.65
```

Note: if the sample dataset is used, all figures come from synthetic data.
