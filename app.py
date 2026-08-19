from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

DATABASE = "restaurant.db"

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# ---------------- DATABASE CONNECTION ----------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE DATABASE ----------------

def init_db():

    conn = get_db_connection()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Menu items table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT
        )
    """)

    # Orders table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL,
            status TEXT DEFAULT 'Order Placed',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Order items table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            menu_item_id INTEGER,
            quantity INTEGER,
            price REAL
        )
    """)

    conn.commit()

    # Check whether menu already has items
    count = conn.execute(
        "SELECT COUNT(*) FROM menu_items"
    ).fetchone()[0]

    # Add sample food items
    if count == 0:

        sample_items = [

         # PIZZA
         ("Margherita Pizza", "Cheese and tomato pizza", 199, "Pizza"),
         ("Farmhouse Pizza", "Loaded with fresh vegetables", 249, "Pizza"),
         ("Veggie Supreme Pizza", "Vegetables and cheese", 279, "Pizza"),
         ("Chicken Tikka Pizza", "Chicken tikka with cheese", 299, "Pizza"),
         ("Pepperoni Pizza", "Pepperoni and mozzarella cheese", 319, "Pizza"),

         # BURGERS
         ("Veg Burger", "Fresh vegetable burger", 120, "Burger"),
         ("Cheese Burger", "Burger with extra cheese", 150, "Burger"),
         ("Chicken Burger", "Delicious chicken burger", 160, "Burger"),
         ("Double Chicken Burger", "Double chicken patty", 220, "Burger"),

         # BIRYANI
         ("Veg Biryani", "Traditional vegetable biryani", 180, "Biryani"),
         ("Paneer Biryani", "Spicy paneer biryani", 220, "Biryani"),
         ("Chicken Biryani", "Spicy chicken biryani", 250, "Biryani"),
         ("Mutton Biryani", "Traditional mutton biryani", 350, "Biryani"),

         # SOUTH INDIAN
         ("Plain Dosa", "Traditional crispy dosa", 80, "South Indian"),
         ("Masala Dosa", "Dosa with potato masala", 110, "South Indian"),
         ("Paneer Dosa", "Dosa with paneer filling", 140, "South Indian"),
         ("Idli Sambar", "Soft idli with sambar", 70, "South Indian"),
         ("Vada Sambar", "Crispy vada with sambar", 80, "South Indian"),

         # SNACKS
         ("French Fries", "Crispy potato fries", 90, "Snacks"),
         ("Veg Sandwich", "Fresh vegetable sandwich", 100, "Snacks"),
         ("Chicken Sandwich", "Grilled chicken sandwich", 150, "Snacks"),
         ("Veg Spring Roll", "Crispy vegetable spring rolls", 120, "Snacks"),
         ("Chicken Nuggets", "Crispy chicken nuggets", 180, "Snacks"),

         # CHINESE
         ("Veg Fried Rice", "Fried rice with vegetables", 160, "Chinese"),
         ("Chicken Fried Rice", "Fried rice with chicken", 200, "Chinese"),
         ("Veg Noodles", "Stir fried vegetable noodles", 150, "Chinese"),
         ("Chicken Noodles", "Chicken noodles with vegetables", 200, "Chinese"),
         ("Veg Manchurian", "Crispy vegetable Manchurian", 160, "Chinese"),

         # DRINKS
         ("Coke", "Cold soft drink", 40, "Drinks"),
         ("Sprite", "Refreshing lemon drink", 40, "Drinks"),
         ("Fresh Lime Soda", "Fresh lime and soda", 60, "Drinks"),
         ("Mango Juice", "Fresh mango juice", 80, "Drinks"),
         ("Cold Coffee", "Chilled coffee drink", 100, "Drinks"),

         # DESSERTS
         ("Chocolate Cake", "Sweet chocolate cake", 100, "Dessert"),
         ("Ice Cream", "Vanilla ice cream", 80, "Dessert"),
         ("Brownie", "Chocolate brownie", 120, "Dessert"),
         ("Gulab Jamun", "Traditional Indian sweet", 70, "Dessert")
         ]

        conn.executemany("""
            INSERT INTO menu_items
            (name, description, price, category)
            VALUES (?, ?, ?, ?)
        """, sample_items)

        conn.commit()

    conn.close()


# ---------------- HOME PAGE ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:

            conn.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, hashed_password))

            conn.commit()

            flash("Registration successful! Please login.")

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("Email already exists!")

        finally:

            conn.close()

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            flash("Login successful!")

            return redirect(url_for("menu"))

        else:

            flash("Invalid email or password!")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("index"))


# ---------------- MENU ----------------

@app.route("/menu")
def menu():

    conn = get_db_connection()

    items = conn.execute(
        "SELECT * FROM menu_items"
    ).fetchall()

    conn.close()

    return render_template("menu.html", items=items)
# ---------------- ADD TO CART ----------------

@app.route("/add_to_cart/<int:item_id>")
def add_to_cart(item_id):

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    item_id = str(item_id)

    if item_id in cart:
        cart[item_id] += 1
    else:
        cart[item_id] = 1

    session["cart"] = cart

    flash("Item added to cart!")

    return redirect(url_for("menu")) 

# ---------------- CART ----------------

@app.route("/cart")
def cart():

    cart = session.get("cart", {})

    cart_items = []
    total = 0

    conn = get_db_connection()

    for item_id, quantity in cart.items():

        item = conn.execute(
            "SELECT * FROM menu_items WHERE id = ?",
            (item_id,)
        ).fetchone()

        if item:

            subtotal = item["price"] * quantity

            total += subtotal

            cart_items.append({
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "quantity": quantity,
                "subtotal": subtotal
            })

    conn.close()

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )   

# ---------------- PLACE ORDER ----------------

@app.route("/place_order")
def place_order():

    # User must login first
    if "user_id" not in session:

        flash("Please login before placing an order.")

        return redirect(url_for("login"))

    cart = session.get("cart", {})

    if not cart:

        flash("Your cart is empty!")

        return redirect(url_for("menu"))

    conn = get_db_connection()

    total = 0
    order_items = []

    # Calculate total and collect items
    for item_id, quantity in cart.items():

        item = conn.execute(
            "SELECT * FROM menu_items WHERE id = ?",
            (item_id,)
        ).fetchone()

        if item:

            subtotal = item["price"] * quantity

            total += subtotal

            order_items.append(
                (item["id"], quantity, item["price"])
            )

    # Create new order
    cursor = conn.execute("""
        INSERT INTO orders
        (user_id, total_amount, status)
        VALUES (?, ?, ?)
    """, (
        session["user_id"],
        total,
        "Order Placed"
    ))

    order_id = cursor.lastrowid

    # Store all food items in this order
    for item_id, quantity, price in order_items:

        conn.execute("""
            INSERT INTO order_items
            (order_id, menu_item_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (
            order_id,
            item_id,
            quantity,
            price
        ))

    conn.commit()

    conn.close()

    # Clear cart after placing order
    session["cart"] = {}

    flash(f"Order placed successfully! Order ID: #{order_id}")

    return redirect(url_for("orders"))


# ---------------- MY ORDERS ----------------

@app.route("/orders")
def orders():

    if "user_id" not in session:

        flash("Please login first.")

        return redirect(url_for("login"))

    conn = get_db_connection()

    user_orders = conn.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY order_date DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "orders.html",
        orders=user_orders
    )   
# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):

        flash("Please login as administrator.")

        return redirect(url_for("admin_login"))

    conn = get_db_connection()

    items = conn.execute(
        "SELECT * FROM menu_items"
    ).fetchall()

    all_orders = conn.execute("""
        SELECT orders.*, users.name AS customer_name
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY order_date DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        items=items,
        orders=all_orders
    )

# ---------------- ADD FOOD ----------------

@app.route("/add_food", methods=["POST"])
def add_food():

    name = request.form["name"]
    description = request.form["description"]
    price = request.form["price"]
    category = request.form["category"]

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO menu_items
        (name, description, price, category)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        description,
        price,
        category
    ))

    conn.commit()

    conn.close()

    flash("Food item added successfully!")

    return redirect(url_for("admin"))


# ---------------- DELETE FOOD ----------------

@app.route("/delete_food/<int:item_id>")
def delete_food(item_id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM menu_items WHERE id = ?",
        (item_id,)
    )

    conn.commit()

    conn.close()

    flash("Food item deleted successfully!")

    return redirect(url_for("admin"))         

# ================= ADMIN LOGIN =================

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:

            session["admin_logged_in"] = True

            flash("Admin login successful!")

            return redirect(url_for("admin"))

        else:

            flash("Invalid admin email or password!")

    return render_template("admin_login.html")


# ================= ADMIN LOGOUT =================

@app.route("/admin_logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    flash("Admin logged out successfully!")

    return redirect(url_for("index"))


# ================= RUN APPLICATION =================

if __name__ == "__main__":
    app.run(debug=True)