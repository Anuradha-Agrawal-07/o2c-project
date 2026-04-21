from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
DATABASE_DIR = PROJECT_DIR / "database"
DB_PATH = DATABASE_DIR / "o2c.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(r) for r in rows]


def generate_doc_number(prefix, table_name, column_name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    count = cur.fetchone()["count"] + 1
    conn.close()
    return f"{prefix}{datetime.now().strftime('%Y%m%d')}{count:04d}"


def init_database():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "o2c-dashboard.html")


@app.route("/api/init", methods=["POST"])
def api_init():
    try:
        init_database()
        return jsonify({"message": "Database initialized successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def api_reset():
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("DELETE FROM payments")
        cur.execute("DELETE FROM invoices")
        cur.execute("DELETE FROM deliveries")
        cur.execute("DELETE FROM sales_orders")
        cur.execute("DELETE FROM products")
        cur.execute("DELETE FROM customers")

        conn.commit()
        conn.close()

        return jsonify({"message": "All O2C data deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    try:
        conn = get_db()
        cur = conn.cursor()

        stats = {}
        for label, table in [
            ("customers", "customers"),
            ("products", "products"),
            ("sales_orders", "sales_orders"),
            ("deliveries", "deliveries"),
            ("invoices", "invoices"),
            ("payments", "payments")
        ]:
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[label] = cur.fetchone()["count"]

        conn.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/customers", methods=["GET", "POST"])
def customers():
    try:
        conn = get_db()
        cur = conn.cursor()

        if request.method == "GET":
            cur.execute("""
                SELECT id, customer_code, customer_name, city, credit_limit
                FROM customers
                ORDER BY id DESC
            """)
            rows = cur.fetchall()
            conn.close()
            return jsonify(rows_to_list(rows))

        data = request.get_json(silent=True) or {}
        customer_code = (data.get("customer_code") or "").strip()
        customer_name = (data.get("customer_name") or "").strip()
        city = (data.get("city") or "").strip()
        credit_limit = data.get("credit_limit")

        if not customer_code or not customer_name:
            conn.close()
            return jsonify({"error": "Customer code and customer name are required"}), 400

        try:
            credit_limit = float(credit_limit)
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Valid credit limit is required"}), 400

        cur.execute("""
            INSERT INTO customers (customer_code, customer_name, city, credit_limit)
            VALUES (?, ?, ?, ?)
        """, (customer_code, customer_name, city, credit_limit))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()

        return jsonify({"message": "Customer added successfully", "id": new_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Customer code already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/products", methods=["GET", "POST"])
def products():
    try:
        conn = get_db()
        cur = conn.cursor()

        if request.method == "GET":
            cur.execute("""
                SELECT id, product_code, product_name, uom, price, stock
                FROM products
                ORDER BY id DESC
            """)
            rows = cur.fetchall()
            conn.close()
            return jsonify(rows_to_list(rows))

        data = request.get_json(silent=True) or {}
        product_code = (data.get("product_code") or "").strip()
        product_name = (data.get("product_name") or "").strip()
        uom = (data.get("uom") or "").strip()
        price = data.get("price")
        stock = data.get("stock")

        if not product_code or not product_name:
            conn.close()
            return jsonify({"error": "Product code and product name are required"}), 400

        try:
            price = float(price)
            stock = float(stock)
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Valid price and stock are required"}), 400

        cur.execute("""
            INSERT INTO products (product_code, product_name, uom, price, stock)
            VALUES (?, ?, ?, ?, ?)
        """, (product_code, product_name, uom, price, stock))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()

        return jsonify({"message": "Product added successfully", "id": new_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Product code already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sales-orders", methods=["GET", "POST"])
def sales_orders():
    try:
        conn = get_db()
        cur = conn.cursor()

        if request.method == "GET":
            cur.execute("""
                SELECT
                    so.id,
                    so.so_number,
                    c.customer_name,
                    p.product_name,
                    so.quantity,
                    so.total_amount,
                    so.credit_status,
                    so.status
                FROM sales_orders so
                JOIN customers c ON so.customer_id = c.id
                JOIN products p ON so.product_id = p.id
                ORDER BY so.id DESC
            """)
            rows = cur.fetchall()
            conn.close()
            return jsonify(rows_to_list(rows))

        data = request.get_json(silent=True) or {}
        customer_id = data.get("customer_id")
        product_id = data.get("product_id")
        quantity = data.get("quantity")

        try:
            customer_id = int(customer_id)
            product_id = int(product_id)
            quantity = float(quantity)
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Valid customer, product, and quantity are required"}), 400

        if quantity <= 0:
            conn.close()
            return jsonify({"error": "Quantity must be greater than 0"}), 400

        cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = cur.fetchone()
        if not customer:
            conn.close()
            return jsonify({"error": "Customer not found"}), 404

        cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cur.fetchone()
        if not product:
            conn.close()
            return jsonify({"error": "Product not found"}), 404

        total_amount = quantity * product["price"]
        credit_status = "PENDING_REVIEW"
        so_number = generate_doc_number("SO", "sales_orders", "so_number")

        cur.execute("""
            INSERT INTO sales_orders
            (so_number, customer_id, product_id, quantity, total_amount, credit_status, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            so_number,
            customer_id,
            product_id,
            quantity,
            total_amount,
            credit_status,
            "CREATED"
        ))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()

        return jsonify({
            "message": "Sales order created successfully",
            "id": new_id,
            "so_number": so_number,
            "credit_status": credit_status
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/credit-approve", methods=["POST"])
def credit_approve():
    try:
        conn = get_db()
        cur = conn.cursor()
        data = request.get_json(silent=True) or {}
        sales_order_id = data.get("sales_order_id")

        try:
            sales_order_id = int(sales_order_id)
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Valid sales order id is required"}), 400

        cur.execute("SELECT * FROM sales_orders WHERE id = ?", (sales_order_id,))
        so = cur.fetchone()
        if not so:
            conn.close()
            return jsonify({"error": "Sales order not found"}), 404

        cur.execute("""
            UPDATE sales_orders
            SET credit_status = 'APPROVED', status = 'APPROVED'
            WHERE id = ?
        """, (sales_order_id,))
        conn.commit()
        conn.close()

        return jsonify({"message": "Credit approved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/deliveries", methods=["GET", "POST"])
def deliveries():
    try:
        conn = get_db()
        cur = conn.cursor()

        if request.method == "GET":
            cur.execute("""
                SELECT
                    d.id,
                    d.delivery_number,
                    so.so_number,
                    c.customer_name,
                    p.product_name,
                    d.quantity_delivered,
                    d.status
                FROM deliveries d
                JOIN sales_orders so ON d.sales_order_id = so.id
                JOIN customers c ON so.customer_id = c.id
                JOIN products p ON so.product_id = p.id
                ORDER BY d.id DESC
            """)
            rows = cur.fetchall()
            conn.close()
            return jsonify(rows_to_list(rows))

        data = request.get_json(silent=True) or {}
        sales_order_id = data.get("sales_order_id")

        try:
            sales_order_id = int(sales_order_id)
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Valid sales order id is required"}), 400

        cur.execute("""
            SELECT so.*, p.stock, p.product_name
            FROM sales_orders so
            JOIN products p ON so.product_id = p.id
            WHERE so.id = ?
        """, (sales_order_id,))
        so = cur.fetchone()

        if not so:
            conn.close()
            return jsonify({"error": "Sales order not found"}), 404

        if so["credit_status"] != "APPROVED":
            conn.close()
            return jsonify({"error": "Sales order credit is not approved"}), 400

        if so["status"] == "DELIVERED":
            conn.close()
            return jsonify({"error": "Delivery already posted for this sales order"}), 400

        if so["stock"] < so["quantity"]:
            conn.close()
            return jsonify({"error": "Insufficient stock for delivery"}), 400

        delivery_number = generate_doc_number("DL", "deliveries", "delivery_number")

        cur.execute("""
            INSERT INTO deliveries (delivery_number, sales_order_id, quantity_delivered, status)
            VALUES (?, ?, ?, ?)
        """, (delivery_number, sales_order_id, so["quantity"], "DELIVERED"))

        cur.execute("""
            UPDATE products
            SET stock = stock - ?
            WHERE id = ?
        """, (so["quantity"], so["product_id"]))

        cur.execute("""
            UPDATE sales_orders
            SET status = 'DELIVERED'
            WHERE id = ?
        """, (sales_order_id,))

        conn.commit()
        conn.close()

        return jsonify({
            "message": "Delivery posted successfully",
            "delivery_number": delivery_number
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/invoices", methods=["GET", "POST"])
def invoices():
    try:
        conn = get_db()
        cur = conn.cursor()

        if request.method == "GET":
            cur.execute("""
                SELECT
                    i.id,
                    i.invoice_number,
                    so.so_number,
                    c.customer_name,
                    i.amount,
                    i.status
                FROM invoices i
                JOIN sales_orders so ON i.sales_order_id = so.id
                JOIN customers c ON so.customer_id = c.id
                ORDER BY i.id DESC
            """)
            rows = cur.fetchall()
            conn.close()
            return jsonify(rows_to_list(rows))

        data = request.get_json(silent=True) or {}
        sales_order_id = data.get("sales_order_id")

        try:
            sales_order_id = int(sales_order_id)
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Valid sales order id is required"}), 400

        cur.execute("""
            SELECT * FROM sales_orders WHERE id = ?
        """, (sales_order_id,))
        so = cur.fetchone()

        if not so:
            conn.close()
            return jsonify({"error": "Sales order not found"}), 404

        if so["status"] != "DELIVERED":
            conn.close()
            return jsonify({"error": "Invoice can only be created after delivery"}), 400

        cur.execute("SELECT id FROM invoices WHERE sales_order_id = ?", (sales_order_id,))
        existing = cur.fetchone()
        if existing:
            conn.close()
            return jsonify({"error": "Invoice already exists for this sales order"}), 400

        invoice_number = generate_doc_number("IV", "invoices", "invoice_number")

        cur.execute("""
            INSERT INTO invoices (invoice_number, sales_order_id, amount, status)
            VALUES (?, ?, ?, ?)
        """, (invoice_number, sales_order_id, so["total_amount"], "OPEN"))

        cur.execute("""
            UPDATE sales_orders
            SET status = 'INVOICED'
            WHERE id = ?
        """, (sales_order_id,))

        conn.commit()
        conn.close()

        return jsonify({
            "message": "Invoice created successfully",
            "invoice_number": invoice_number
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/payments", methods=["GET", "POST"])
def payments():
    try:
        conn = get_db()
        cur = conn.cursor()

        if request.method == "GET":
            cur.execute("""
                SELECT
                    p.id,
                    p.payment_number,
                    i.invoice_number,
                    c.customer_name,
                    p.amount,
                    p.status
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN sales_orders so ON i.sales_order_id = so.id
                JOIN customers c ON so.customer_id = c.id
                ORDER BY p.id DESC
            """)
            rows = cur.fetchall()
            conn.close()
            return jsonify(rows_to_list(rows))

        data = request.get_json(silent=True) or {}
        invoice_id = data.get("invoice_id")

        try:
            invoice_id = int(invoice_id)
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"error": "Valid invoice id is required"}), 400

        cur.execute("""
            SELECT i.*, so.id as sales_order_id
            FROM invoices i
            JOIN sales_orders so ON i.sales_order_id = so.id
            WHERE i.id = ?
        """, (invoice_id,))
        invoice = cur.fetchone()

        if not invoice:
            conn.close()
            return jsonify({"error": "Invoice not found"}), 404

        if invoice["status"] == "PAID":
            conn.close()
            return jsonify({"error": "Payment already recorded for this invoice"}), 400

        payment_number = generate_doc_number("PY", "payments", "payment_number")

        cur.execute("""
            INSERT INTO payments (payment_number, invoice_id, amount, status)
            VALUES (?, ?, ?, ?)
        """, (payment_number, invoice_id, invoice["amount"], "RECEIVED"))

        cur.execute("""
            UPDATE invoices
            SET status = 'PAID'
            WHERE id = ?
        """, (invoice_id,))

        cur.execute("""
            UPDATE sales_orders
            SET status = 'CLOSED'
            WHERE id = ?
        """, (invoice["sales_order_id"],))

        conn.commit()
        conn.close()

        return jsonify({
            "message": "Payment recorded successfully",
            "payment_number": payment_number
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/credit-pending-orders", methods=["GET"])
def credit_pending_orders():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                so.id,
                so.so_number,
                c.customer_name,
                p.product_name,
                so.quantity,
                so.total_amount,
                so.credit_status,
                so.status
            FROM sales_orders so
            JOIN customers c ON so.customer_id = c.id
            JOIN products p ON so.product_id = p.id
            WHERE so.credit_status = 'PENDING_REVIEW'
            ORDER BY so.id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return jsonify(rows_to_list(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/deliverable-orders", methods=["GET"])
def deliverable_orders():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                so_number
            FROM sales_orders
            WHERE credit_status = 'APPROVED'
              AND status IN ('CREATED', 'APPROVED')
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return jsonify(rows_to_list(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/invoiceable-orders", methods=["GET"])
def invoiceable_orders():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                so_number
            FROM sales_orders
            WHERE status = 'DELIVERED'
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return jsonify(rows_to_list(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/payable-invoices", methods=["GET"])
def payable_invoices():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                invoice_number
            FROM invoices
            WHERE status = 'OPEN'
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return jsonify(rows_to_list(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
