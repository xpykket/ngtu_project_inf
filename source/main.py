import os
import sqlite3
import json
import csv
import yaml
import xml.etree.ElementTree as ET


def main():
    DB_NAME = "internet_shop.db"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Category (
        category_id INTEGER PRIMARY KEY,
        name TEXT
    );

    CREATE TABLE IF NOT EXISTS Product (
        product_id INTEGER PRIMARY KEY,
        category_id INTEGER,
        name TEXT,
        price REAL,
        availability REAL,
        FOREIGN KEY(category_id) REFERENCES Category(category_id)
    );

    CREATE TABLE IF NOT EXISTS Customer (
        customer_id INTEGER PRIMARY KEY,
        name TEXT,
        password TEXT,
        phone TEXT
    );

    CREATE TABLE IF NOT EXISTS "Order" (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date TEXT,
        order_cost REAL,
        status TEXT,
        FOREIGN KEY(customer_id) REFERENCES Customer(customer_id)
    );

    CREATE TABLE IF NOT EXISTS Order_filling (
        Order_filling_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        price REAL,
        FOREIGN KEY(order_id) REFERENCES "Order"(order_id),
        FOREIGN KEY(product_id) REFERENCES Product(product_id)
    );

    CREATE TABLE IF NOT EXISTS Payment (
        payment_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        order_cost REAL,
        payment_date TEXT,
        p_status TEXT,
        FOREIGN KEY(order_id) REFERENCES "Order"(order_id)
    );
    """)

    Category = [
        (1, "Одежда"),
        (2, "Техника"),
        (3, "Мебель"),
        (4, "Продукты"),
    ]
    Product = [
        (1, 1, "Футболка archive y2k opium", 999, 15),
        (2, 1, "Джинсы с кружевом клеш jaded london type", 1699, 2),
        (3, 1, "Зип худи archive y2k opium vetmo balenciaga type", 4990, 20),
        (4, 1, "Бомбер Зимний Balenciaga Type", 6490, 0),
        (5, 2, "iPhone 6, 32 ГБ", 3999, 4),
        (6, 2, "iPhone X, 256 ГБ", 7490, 2),
        (7, 2, "iPhone 17 Pro Max, 256 ГБ", 102900, 100),
        (8, 2, "iPhone 17 Pro Max, 512 ГБ", 119900, 14),
        (9, 3, "Стул", 1500, 3),
        (10, 3, "Стол", 2500, 19),
        (11, 3, "Кресло", 4000, 23),
        (12, 3, "Кровать", 15000, 25),
        (13, 4, "Хлеб", 30, 250),
        (14, 4, "Молоко", 100, 150),
        (15, 4, "Кефир", 100, 200),
        (16, 4, "Квас", 50, 100),
    ]
    Customer = [
        (1, "Илья", "k27mrzjvod", "79999280780"),
        (2, "Дмитрий", "jlzvdvh38s", "79993350305"),
        (3, "Мария", "bhwl453j8g", "79997031194"),
        (4, "Глеб", "2w761ulb55", "79991360922")
    ]
    Order = [
        (1, 1, "13.11.2025", 999, "Оформлен"),
        (2, 2, "14.11.2025", 7490, "Ошибка оплаты"),
        (3, 3, "10.10.2025", 109390, "Оформлен"),
        (4, 4, "11.11.2025", 1500, "Оформлен")
    ]
    Order_filling = [
        (1, 1, 1, 999),
        (2, 2, 6, 7490),
        (3, 3, 7, 102900),
        (4, 3, 4, 6490),
        (5, 4, 9, 1500),
    ]

    Payment = [
        (1, 1, 999, "13.11.2025 15:22", "Оплата прошла успешно"),
        (2, 2, 7490, "14.11.2025 13:43", "Ошибка оплаты"),
        (3, 3, 109390, "10.10.2025 20:12", "Оплата прошла успешно"),
        (4, 4, 1500, "11.11.2025 0:43", "Оплата прошла успешно")
    ]

    cursor.executemany("INSERT INTO Category VALUES (?, ?)", Category)
    cursor.executemany("INSERT INTO Product VALUES (?, ?, ?, ?, ?)", Product)
    cursor.executemany("INSERT INTO Customer VALUES (?, ?, ?, ?)", Customer)
    cursor.executemany('INSERT INTO "Order" VALUES (?, ?, ?, ?, ?)', Order)
    cursor.executemany("INSERT INTO Order_filling VALUES (?, ?, ?, ?)", Order_filling)
    cursor.executemany("INSERT INTO Payment VALUES (?, ?, ?, ?, ?)", Payment)

    conn.commit()

    cursor.execute("""
    SELECT o.order_id, c.name, c.phone, o.order_cost, o.order_date, o.status,
           p.p_status, p.payment_date
    FROM "Order" o
    JOIN Payment p ON o.order_id = p.order_id
    JOIN Customer c ON o.customer_id = c.customer_id
    """)
    rows = cursor.fetchall()

    data = []
    for row in rows:
        data.append({
            "order_id": row[0],
            "Customer": {
                "name": row[1],
                "phone": row[2],
            },
            "order_cost": row[3],
            "order_date": row[4],
            "status": row[5],
            "payment": {
                "p_status": row[6],
                "payment_date": row[7]
            }
        })

    os.makedirs("out", exist_ok=True)

    with open("out/internet_shop.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open("out/internet_shop.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "order_id", "customer_name", "customer_phone", "order_cost",
            "order_date", "status", "payment_status", "payment_date"
        ])
        writer.writeheader()
        for d in data:
            writer.writerow({
                "order_id": d["order_id"],
                "customer_name": d["Customer"]["name"],
                "customer_phone": d["Customer"]["phone"],
                "order_cost": d["order_cost"],
                "order_date": d["order_date"],
                "status": d["status"],
                "payment_status": d["payment"]["p_status"],
                "payment_date": d["payment"]["payment_date"]
            })

    root = ET.Element("orders")
    for d in data:
        order_elem = ET.SubElement(root, "order")
        ET.SubElement(order_elem, "order_id").text = str(d["order_id"])
        customer_elem = ET.SubElement(order_elem, "customer")
        ET.SubElement(customer_elem, "name").text = d["Customer"]["name"]
        ET.SubElement(customer_elem, "phone").text = d["Customer"]["phone"]
        ET.SubElement(order_elem, "order_cost").text = str(d["order_cost"])
        ET.SubElement(order_elem, "order_date").text = d["order_date"]
        ET.SubElement(order_elem, "status").text = d["status"]
        payment_elem = ET.SubElement(order_elem, "payment")
        ET.SubElement(payment_elem, "p_status").text = d["payment"]["p_status"]
        ET.SubElement(payment_elem, "payment_date").text = d["payment"]["payment_date"]

    tree = ET.ElementTree(root)
    tree.write("out/internet_shop.xml", encoding="utf-8", xml_declaration=True)

    with open("out/internet_shop.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    conn.close()


if __name__ == "__main__":
    main()