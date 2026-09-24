from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)
app.secret_key = "ecospheresecretkey2026"

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
DATABASE = str(BASE_DIR / "database.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    conn = get_db_connection()

    # --------------------------------------------------------
    # PRODUCTS TABLE
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            ecoscore INTEGER DEFAULT 0,
            image TEXT,
            material_score INTEGER DEFAULT 0,
            recyclability_score INTEGER DEFAULT 0,
            reusability_score INTEGER DEFAULT 0,
            packaging_score INTEGER DEFAULT 0,
            transport_score INTEGER DEFAULT 0
        )
    """)

    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            preferred_category TEXT DEFAULT '',
            role TEXT DEFAULT 'customer'
        )
    """)

    # --------------------------------------------------------
    # ORDERS TABLE
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_name TEXT,
            customer_email TEXT,
            address TEXT,
            city TEXT,
            pincode TEXT,
            payment_method TEXT,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # --------------------------------------------------------
    # ORDER ITEMS TABLE
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # --------------------------------------------------------
    # CAMPAIGNS TABLE
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER,
            platform TEXT NOT NULL,
            marketing_goal TEXT NOT NULL,
            campaign_title TEXT NOT NULL,
            caption TEXT NOT NULL,
            hashtags TEXT NOT NULL,
            call_to_action TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # ========================================================
    # DATABASE MIGRATIONS
    # ========================================================

    # --------------------------------------------------------
    # PRODUCTS MIGRATION
    # --------------------------------------------------------

    product_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(products)"
        ).fetchall()
    ]

    if "image" not in product_columns:
        conn.execute("""
            ALTER TABLE products
            ADD COLUMN image TEXT
        """)

    if "material_score" not in product_columns:
        conn.execute("""
            ALTER TABLE products
            ADD COLUMN material_score INTEGER DEFAULT 0
        """)

    if "recyclability_score" not in product_columns:
        conn.execute("""
            ALTER TABLE products
            ADD COLUMN recyclability_score INTEGER DEFAULT 0
        """)

    if "reusability_score" not in product_columns:
        conn.execute("""
            ALTER TABLE products
            ADD COLUMN reusability_score INTEGER DEFAULT 0
        """)

    if "packaging_score" not in product_columns:
        conn.execute("""
            ALTER TABLE products
            ADD COLUMN packaging_score INTEGER DEFAULT 0
        """)

    if "transport_score" not in product_columns:
        conn.execute("""
            ALTER TABLE products
            ADD COLUMN transport_score INTEGER DEFAULT 0
        """)

    # --------------------------------------------------------
    # USERS MIGRATION
    # --------------------------------------------------------

    user_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    ]

    if "preferred_category" not in user_columns:
        conn.execute("""
            ALTER TABLE users
            ADD COLUMN preferred_category TEXT DEFAULT ''
        """)

    if "role" not in user_columns:
        conn.execute("""
            ALTER TABLE users
            ADD COLUMN role TEXT DEFAULT 'customer'
        """)

    # --------------------------------------------------------
    # ORDERS MIGRATION
    #
    # IMPORTANT:
    # These columns are added without NOT NULL because old
    # orders may already exist in database.db.
    # --------------------------------------------------------

    order_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(orders)"
        ).fetchall()
    ]

    if "customer_name" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN customer_name TEXT
        """)

    if "customer_email" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN customer_email TEXT
        """)

    if "address" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN address TEXT
        """)

    if "city" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN city TEXT
        """)

    if "pincode" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN pincode TEXT
        """)

    if "payment_method" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN payment_method TEXT
        """)

    if "total_amount" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN total_amount REAL DEFAULT 0
        """)

    if "status" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN status TEXT DEFAULT 'Placed'
        """)

    if "order_date" not in order_columns:
        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN order_date TIMESTAMP
        """)

    # --------------------------------------------------------
    # SAMPLE PRODUCTS
    # --------------------------------------------------------

    product_count = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if product_count == 0:

        sample_products = [
            (
                "Organic Cotton Tote Bag",
                "Bags",
                799.00,
                "Durable organic cotton tote for groceries, college and everyday sustainable shopping.",
                88,
                "/static/images/organic_cotton_tote_bag.jpg",
                96, 94, 95, 90, 92
            ),
            (
                "Recycled Paper Notebook",
                "Stationery",
                449.00,
                "Minimal recycled-paper notebook for notes, journaling and creative ideas.",
                95,
                "/static/images/recycled_paper_notebook.jpg",
                96, 98, 91, 94, 95
            ),
            (
                "Bamboo Cutlery Set",
                "Kitchen",
                699.00,
                "Reusable bamboo fork, spoon and knife set with a washable travel pouch.",
                90,
                "/static/images/bamboo_cutlery_set.jpg",
                92, 91, 96, 90, 91
            ),
            (
                "Indoor Plant Starter Kit",
                "Home & Garden",
                549.00,
                "Beginner-friendly indoor plant kit to bring a fresh green touch to your space.",
                87,
                "/static/images/indoor_plant_starter_kit.jpg",
                89, 87, 92, 82, 86
            ),
            (
                "Natural Soy Wax Candle",
                "Home & Living",
                399.00,
                "Hand-poured soy wax candle with a clean, calming fragrance and reusable jar.",
                89,
                "/static/images/natural_soy_wax_candle.jpg",
                92, 90, 88, 87, 89
            ),
            (
                "Reusable Produce Bags",
                "Kitchen",
                349.00,
                "Lightweight washable mesh bags that make plastic-free fruit and vegetable shopping easy.",
                94,
                "/static/images/reusable_produce_bags.jpg",
                95, 94, 98, 91, 92
            ),
            (
                "Cork Desk Organizer",
                "Stationery",
                649.00,
                "Natural cork organizer for pens, cards and everyday desk essentials.",
                86,
                "/static/images/cork_desk_organizer.jpg",
                90, 86, 90, 84, 85
            ),
            (
                "Jute Shopping Bag", "Fashion", 249.00,
                "Strong reusable jute shopping bag for groceries and everyday carrying.",
                93, "/static/images/jute_bag.jpg",
                95, 92, 96, 90, 91
            ),
            (
                "Recycled Fabric Backpack", "Fashion", 1299.00,
                "Durable everyday backpack made using recycled fabric for conscious travel and college use.",
                91, "/static/images/recycled_fabric_backpack.jpg",
                93, 96, 94, 88, 89
            ),
            (
                "Plantable Seed Pencils – Set of 10", "Stationery", 199.00,
                "Plantable pencils embedded with seeds that can grow into herbs or flowers after use.",
                98, "/static/images/plantable_seed_pencils.jpg",
                98, 99, 96, 97, 95
            ),
            (
                "Terracotta Plant Pot", "Home & Garden", 299.00,
                "Classic breathable terracotta pot for indoor plants, herbs and balcony gardening.",
                93, "/static/images/terracotta_plant_pot.jpg",
                96, 95, 92, 91, 90
            ),
            (
                "Coconut Shell Planter", "Home & Garden", 399.00,
                "Handcrafted coconut shell planter that gives natural waste material a second life.",
                95, "/static/images/coconut_shell_planter.jpg",
                98, 96, 94, 93, 91
            ),
            (
                "Natural Loofah Bath Sponge", "Personal Care", 199.00,
                "Plant-based natural loofah bath sponge for gentle exfoliation and plastic-free bathing.",
                96, "/static/images/natural_loofah_body_scrubber.jpg",
                97, 96, 95, 94, 93
            ),
            (
                "Bamboo Storage Basket", "Home & Garden", 699.00,
                "Handwoven bamboo storage basket for organizing home essentials with a natural look.",
                92, "/static/images/bamboo_storage_basket.jpg",
                94, 93, 94, 89, 90
            ),
            (
                "Handmade Herbal Soap", "Personal Care", 149.00,
                "Handmade herbal soap crafted with plant-based ingredients for a simple, gentle routine.",
                94, "/static/images/handmade_herbal_soap.jpg",
                95, 94, 90, 93, 91
            ),
            (
                "Coconut Fiber Dish Scrubber", "Cleaning", 149.00,
                "Biodegradable coconut-fiber scrubber for everyday dishwashing without plastic sponges.",
                97, "/static/images/coconut_dish_scrubber.jpg",
                98, 97, 96, 95, 94
            )
        ]

        conn.executemany("""
            INSERT INTO products (
                name,
                category,
                price,
                description,
                ecoscore,
                image,
                material_score,
                recyclability_score,
                reusability_score,
                packaging_score,
                transport_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_products)

    conn.commit()
    conn.close()


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    conn = get_db_connection()

    products = conn.execute("""
        SELECT *
        FROM products
        ORDER BY ecoscore DESC
        LIMIT 6
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        products=products
    )


# ============================================================
# PRODUCTS PAGE
# ============================================================

@app.route("/products")
def products():

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    conn = get_db_connection()

    category_rows = conn.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL
        AND category != ''
        ORDER BY category
    """).fetchall()

    categories = [
        row["category"]
        for row in category_rows
    ]

    query = """
        SELECT *
        FROM products
        WHERE 1 = 1
    """

    parameters = []

    if search:
        query += """
            AND (
                name LIKE ?
                OR category LIKE ?
                OR description LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value,
            search_value
        ])

    if category:
        query += """
            AND category = ?
        """

        parameters.append(category)

    query += """
        ORDER BY ecoscore DESC
    """

    products_list = conn.execute(
        query,
        parameters
    ).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=products_list,
        categories=categories,
        search=search,
        selected_category=category
    )


# ============================================================
# PRODUCT DETAILS
# ============================================================

@app.route("/product/<int:product_id>")
def product_details(product_id):

    conn = get_db_connection()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()

    if product is None:
        return redirect(url_for("products"))

    return render_template(
        "product_details.html",
        product=product
    )


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="Please fill all fields."
            )

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO users (
                    name,
                    email,
                    password,
                    preferred_category,
                    role
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                email,
                hashed_password,
                "",
                "customer"
            ))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            conn.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["cart"] = session.get("cart", {})

            return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ============================================================
# ADD TO CART
# ============================================================

@app.route("/add_to_cart/<int:product_id>", methods=["GET", "POST"])
def add_to_cart(product_id):

    conn = get_db_connection()

    product = conn.execute("""
        SELECT id
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()

    if product is None:
        return redirect(url_for("products"))

    cart = session.get("cart", {})

    # Make sure the cart is a dictionary
    if not isinstance(cart, dict):
        cart = {}

    product_key = str(product_id)

    if product_key in cart:
        cart[product_key] = int(cart[product_key]) + 1
    else:
        cart[product_key] = 1

    session["cart"] = cart
    session.modified = True

    # Go directly to cart so the user can see the added product.
    return redirect(url_for("cart"))


# ============================================================
# CART PAGE
# ============================================================

@app.route("/cart")
def cart():

    cart = session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    if not cart:
        return render_template(
            "cart.html",
            cart_items=[],
            total=0
        )

    product_ids = [
        int(product_id)
        for product_id in cart.keys()
    ]

    placeholders = ",".join(
        ["?"] * len(product_ids)
    )

    conn = get_db_connection()

    products = conn.execute(
        f"""
        SELECT *
        FROM products
        WHERE id IN ({placeholders})
        """,
        product_ids
    ).fetchall()

    conn.close()

    cart_items = []
    total = 0

    for product in products:

        quantity = int(
            cart.get(str(product["id"]), 0)
        )

        if quantity <= 0:
            continue

        subtotal = product["price"] * quantity
        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal
        })

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


# ============================================================
# INCREASE CART QUANTITY
# ============================================================

@app.route("/increase/<int:product_id>")
def increase(product_id):

    cart = session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    product_key = str(product_id)

    if product_key in cart:
        cart[product_key] = int(cart[product_key]) + 1

    session["cart"] = cart
    session.modified = True

    return redirect(url_for("cart"))


# ============================================================
# DECREASE CART QUANTITY
# ============================================================

@app.route("/decrease/<int:product_id>")
def decrease(product_id):

    cart = session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    product_key = str(product_id)

    if product_key in cart:

        cart[product_key] = int(cart[product_key]) - 1

        if cart[product_key] <= 0:
            del cart[product_key]

    session["cart"] = cart
    session.modified = True

    return redirect(url_for("cart"))


# ============================================================
# REMOVE FROM CART
# ============================================================

@app.route("/remove/<int:product_id>")
def remove(product_id):

    cart = session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    product_key = str(product_id)

    if product_key in cart:
        del cart[product_key]

    session["cart"] = cart
    session.modified = True

    return redirect(url_for("cart"))


# ============================================================
# CLEAR CART
# ============================================================

@app.route("/clear_cart")
def clear_cart():

    session["cart"] = {}
    session.modified = True

    return redirect(url_for("cart"))


# ============================================================
# CHECKOUT
# ============================================================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", {})

    if not isinstance(cart, dict) or not cart:
        return redirect(url_for("cart"))

    product_ids = [
        int(product_id)
        for product_id in cart.keys()
    ]

    placeholders = ",".join(
        ["?"] * len(product_ids)
    )

    conn = get_db_connection()

    products = conn.execute(
        f"""
        SELECT *
        FROM products
        WHERE id IN ({placeholders})
        """,
        product_ids
    ).fetchall()

    total = 0
    cart_items = []

    for product in products:

        quantity = int(
            cart.get(str(product["id"]), 0)
        )

        if quantity <= 0:
            continue

        subtotal = product["price"] * quantity
        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal
        })

    if not cart_items:
        conn.close()
        session["cart"] = {}
        session.modified = True
        return redirect(url_for("cart"))

    # --------------------------------------------------------
    # PLACE ORDER
    # --------------------------------------------------------

    if request.method == "POST":

        customer_name = request.form.get(
            "customer_name",
            ""
        ).strip()

        customer_email = request.form.get(
            "customer_email",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        city = request.form.get(
            "city",
            ""
        ).strip()

        pincode = request.form.get(
            "pincode",
            ""
        ).strip()

        payment_method = request.form.get(
            "payment_method",
            ""
        ).strip()

        if not all([
            customer_name,
            customer_email,
            address,
            city,
            pincode,
            payment_method
        ]):
            conn.close()

            return render_template(
                "checkout.html",
                cart_items=cart_items,
                total=total,
                error="Please fill all checkout fields."
            )

        try:

            cursor = conn.execute("""
                INSERT INTO orders (
                    user_id,
                    customer_name,
                    customer_email,
                    address,
                    city,
                    pincode,
                    payment_method,
                    total_amount,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                customer_name,
                customer_email,
                address,
                city,
                pincode,
                payment_method,
                total,
                "Placed"
            ))

            order_id = cursor.lastrowid

            for item in cart_items:

                product = item["product"]
                quantity = item["quantity"]

                conn.execute("""
                    INSERT INTO order_items (
                        order_id,
                        product_id,
                        product_name,
                        price,
                        quantity
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    order_id,
                    product["id"],
                    product["name"],
                    product["price"],
                    quantity
                ))

            conn.commit()
            conn.close()

            session["cart"] = {}
            session.modified = True

            return redirect(
                url_for(
                    "order_success",
                    order_id=order_id
                )
            )

        except sqlite3.Error as error:

            conn.rollback()
            conn.close()

            return render_template(
                "checkout.html",
                cart_items=cart_items,
                total=total,
                error=f"Could not place order: {error}"
            )

    conn.close()

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        total=total
    )


# ============================================================
# ORDER SUCCESS
# ============================================================

@app.route("/order_success/<int:order_id>")
def order_success(order_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    order = conn.execute("""
        SELECT *
        FROM orders
        WHERE id = ?
        AND user_id = ?
    """, (
        order_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if order is None:
        return redirect(url_for("orders"))

    return render_template(
        "order_success.html",
        order=order
    )


# ============================================================
# ORDERS
# ============================================================

@app.route("/orders")
def orders():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    orders_list = conn.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY order_date DESC, id DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "orders.html",
        orders=orders_list
    )


# ============================================================
# PERSONALIZED RECOMMENDATIONS
# ============================================================

@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    category_rows = conn.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL
        AND category != ''
        ORDER BY category
    """).fetchall()

    categories = [
        row["category"]
        for row in category_rows
    ]

    if request.method == "POST":

        selected_category = request.form.get(
            "category",
            ""
        ).strip()

        if selected_category in categories:

            conn.execute("""
                UPDATE users
                SET preferred_category = ?
                WHERE id = ?
            """, (
                selected_category,
                session["user_id"]
            ))

            conn.commit()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    preferred_category = (
        user["preferred_category"]
        or ""
    )

    if preferred_category:

        recommended_products = conn.execute("""
            SELECT *
            FROM products
            WHERE category = ?
            ORDER BY ecoscore DESC, price ASC
        """, (
            preferred_category,
        )).fetchall()

    else:

        recommended_products = conn.execute("""
            SELECT *
            FROM products
            ORDER BY ecoscore DESC, price ASC
            LIMIT 6
        """).fetchall()

    conn.close()

    return render_template(
        "recommendations.html",
        categories=categories,
        preferred_category=preferred_category,
        products=recommended_products
    )


# ============================================================
# SELLER DASHBOARD
# ============================================================

@app.route("/seller")
def seller_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    # For the college project demo, the logged-in user
    # can access the seller dashboard.
    conn.execute("""
        UPDATE users
        SET role = 'seller'
        WHERE id = ?
    """, (
        session["user_id"],
    ))

    conn.commit()

    seller = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    products = conn.execute("""
        SELECT *
        FROM products
        ORDER BY ecoscore DESC
    """).fetchall()

    campaigns = conn.execute("""
        SELECT
            campaigns.*,
            products.name AS product_name
        FROM campaigns
        LEFT JOIN products
        ON campaigns.product_id = products.id
        WHERE campaigns.user_id = ?
        ORDER BY campaigns.created_at DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "seller_dashboard.html",
        seller=seller,
        products=products,
        campaigns=campaigns
    )


# ============================================================
# DIGITAL MARKETING CAMPAIGN GENERATOR
# ============================================================

@app.route("/seller/campaign", methods=["GET", "POST"])
def seller_campaign():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    products = conn.execute("""
        SELECT *
        FROM products
        ORDER BY name
    """).fetchall()

    if request.method == "POST":

        product_id = request.form.get(
            "product_id",
            ""
        ).strip()

        platform = request.form.get(
            "platform",
            ""
        ).strip()

        marketing_goal = request.form.get(
            "marketing_goal",
            ""
        ).strip()

        product = conn.execute("""
            SELECT *
            FROM products
            WHERE id = ?
        """, (
            product_id,
        )).fetchone()

        if product is None:
            conn.close()

            return render_template(
                "seller_campaign.html",
                products=products,
                error="Please select a valid product."
            )

        if not platform or not marketing_goal:
            conn.close()

            return render_template(
                "seller_campaign.html",
                products=products,
                error="Please select platform and marketing goal."
            )

        product_name = product["name"]
        category = product["category"]
        ecoscore = product["ecoscore"]

        campaign_title = (
            f"Go Green with {product_name}"
        )

        caption = (
            f"Make a smarter and greener choice with "
            f"{product_name}! 🌱 "
            f"This sustainable {category.lower()} product "
            f"is designed for conscious consumers. "
            f"With an EcoScore of {ecoscore}/100, "
            f"you can shop better while caring for our planet. "
            f"Choose sustainability with EcoSphere!"
        )

        hashtags = (
            "#EcoSphere "
            "#SustainableLiving "
            "#GoGreen "
            "#EcoFriendly "
            "#SustainableProducts "
            "#SaveThePlanet"
        )

        if platform == "Instagram":
            hashtags += (
                " #InstagramGreen"
                " #EcoLifestyle"
            )

        elif platform == "Facebook":
            hashtags += " #GreenCommunity"

        elif platform == "LinkedIn":
            hashtags += (
                " #Sustainability"
                " #GreenBusiness"
            )

        if marketing_goal == "Brand Awareness":

            call_to_action = (
                "Discover EcoSphere and make your "
                "next purchase a sustainable one."
            )

        elif marketing_goal == "Product Promotion":

            call_to_action = (
                f"Explore {product_name} and "
                f"choose a greener alternative today."
            )

        else:

            call_to_action = (
                "Shop sustainably today and take "
                "a small step towards a greener future."
            )

        # IMPORTANT:
        # There are 9 columns, so there must be 9 ? placeholders.
        conn.execute("""
            INSERT INTO campaigns (
                user_id,
                product_id,
                platform,
                marketing_goal,
                campaign_title,
                caption,
                hashtags,
                call_to_action
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            product_id,
            platform,
            marketing_goal,
            campaign_title,
            caption,
            hashtags,
            call_to_action
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for("seller_dashboard")
        )

    conn.close()

    return render_template(
        "seller_campaign.html",
        products=products
    )


# ============================================================
# APPLICATION START
# ============================================================

# Initialize the database when the application starts
init_db()


if __name__ == "__main__":

    app.run(
        debug=True
    )