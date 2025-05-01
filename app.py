import os
import uuid
import string
import psycopg2
import psycopg2.extras

from xhtml2pdf import pisa
from flask import send_file
import time
from uuid import uuid4
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from flask import make_response

import smtplib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from flask import jsonify
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from db import get_db_connection
import hashlib
SESSION_TIMEOUT = 900
app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route("/")
def home():
    return render_template("index.html")
@app.before_request
def check_session_timeout():
    if "user_id" in session:
        last_activity = session.get("last_activity", time.time())
        if time.time() - last_activity > SESSION_TIMEOUT:
            session.clear()
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for("login"))
        session["last_activity"] = time.time()

from werkzeug.security import check_password_hash, generate_password_hash
import hashlib

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Check for admin login with hardcoded credentials
        if email == "admin@gmail.com" and password == "hari":
            session["user_id"] = "admin"
            session["name"] = "Admin"
            session["role"] = "admin"
            session["last_activity"] = time.time()
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))

        # Check for customer login
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
    "SELECT id, name, password, role FROM customers WHERE email = %s",
    (email,)
)


        user = cursor.fetchone()
        conn.close()

        if user:
            user_id, name, stored_password, role = user

            # Check if the password matches (old SHA256 password or new hashed password)
            # For older customers with SHA256 password hashing
            hashed_password_sha256 = hashlib.sha256(password.encode()).hexdigest()

            # Check against the stored password in the database
            if stored_password == hashed_password_sha256 or check_password_hash(stored_password, password):
                session["user_id"] = user_id
                session["name"] = name
                session["role"] = role  # Set the role from the database
                session["last_activity"] = time.time()
                flash(f"Login successful! Welcome {name}.", "success")

                # Redirect based on role
                if role == "admin":
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("home"))
            else:
                flash("Invalid email or password!", "danger")
        else:
            flash("Invalid email or password!", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))
    return render_template("admin.html")

@app.route("/admin/customers", methods=["GET", "POST"])
def admin_customers():
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, email, address FROM customers")  # Fetch all customers, no filtering by id
    customers = cursor.fetchall()
    conn.close()

    if request.method == "POST":
        selected_role = request.form.get("role")
        if selected_role == "admin":
            return redirect(url_for("admin_dashboard"))  # Redirect to admin page
        elif selected_role == "user":
            return redirect(url_for("index"))  # Redirect to index page

    return render_template("customers.html", customers=customers)

@app.route("/admin/customers/update_role/<int:id>", methods=["POST"])
def update_role(id):
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))
    
    new_role = request.form["role"]

    # Validate the new role (optional but good practice)
    if new_role not in ["admin", "user"]:
        flash("Invalid role selected!", "danger")
        return redirect(url_for("admin_customers"))
    
    try:
        # Update the role in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE customers SET role = %s WHERE id = %s", (new_role, id))
        conn.commit()
        conn.close()

        flash(f"Customer role updated to {new_role}!", "success")
    except Exception as e:
        # Handle exceptions (e.g., database errors)
        flash(f"An error occurred: {str(e)}", "danger")
        conn.rollback()  # In case of an error, rollback the transaction
    return redirect(url_for("admin_customers"))


def send_welcome_email(to_email):
    from_email = "birundhatextiles@gmail.com"
    password = "dzqf jank cyee wrod"
    
    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = "Welcome to Brindha Textiles!"

    body = "Welcome to Brindha Textiles! We are glad to have you with us. Enjoy shopping!"
    message.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = message.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_otp_email(recipient_email, otp):
    
    sender_email = "birundhatextiles@gmail.com"
    sender_password = "dzqf jank cyee wrod"  # Use Gmail App Password!

    subject = "Your Email Verification OTP"
    body = f"Your OTP for verification is: {otp}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("OTP email sent successfully.")
    except Exception as e:
        print("Failed to send OTP email:", e)
        raise

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("signup"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM customers WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered!", "danger")
            conn.close()
            return redirect(url_for("signup"))

        # ✅ Generate OTP
        otp = str(random.randint(100000, 999999))
        try:
            send_otp_email(email, otp)
        except Exception as e:
            flash("Failed to send verification email.", "danger")
            return redirect(url_for("signup"))

        # ✅ Store user data and OTP in session, include role as 'user'
        session["signup_data"] = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "otp": otp,
            "role": "user"  # 👈 default role assigned
        }

        flash("OTP sent to your email. Please verify.", "info")
        return redirect(url_for("verify_otp"))

    return render_template("signup.html")
@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp_page():  # Renamed the function to avoid conflicts
    if request.method == "POST":
        entered_otp = request.form["otp"]
        signup_data = session.get("signup_data")

        if not signup_data:
            flash("Session expired. Please signup again.", "danger")
            return redirect(url_for("signup"))

        if entered_otp == signup_data["otp"]:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
               INSERT INTO customers (name, email, phone, address, password, role)
VALUES (%s, %s, %s, %s, %s, 'user')

            """, (
                signup_data["name"],
                signup_data["email"],
                signup_data["phone"],
                signup_data["address"],
                signup_data["password"]
            ))
            conn.commit()
            conn.close()

            session.pop("signup_data", None)
            flash("Email verified and signup complete! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template("verify_otp.html")


@app.route("/admin/products", methods=["GET", "POST"])
def admin_products():
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        price = request.form["price"]
        stock = request.form["stock"]
        description = request.form["description"]
        pieces = request.form["pieces"]
        file = request.files["image"]
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = f"uploads/{filename}"
        else:
            image_url = "uploads/default.png"
        
        cursor.execute("""
           INSERT INTO products (name, category, price, stock, description, image_url, pieces)
VALUES (%s, %s, %s, %s, %s, %s, %s)
""", (name, category, price, stock, description, image_url, pieces))
        conn.commit()
        flash("Product added successfully!", "success")

    cursor.execute("SELECT id, name, category, price, stock, pieces, description, image_url FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template("products.html", products=products)

def send_confirmation_email(order_id, customer_email):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ✅ Fetch tracking number and estimated delivery date (PostgreSQL syntax)
        cursor.execute(
            "SELECT tracking_number, estimated_delivery FROM shipments WHERE order_id = %s",
            (order_id,)
        )
        shipment_info = cursor.fetchone()

        tracking_number = shipment_info[0] if shipment_info and shipment_info[0] else "N/A"
        estimated_delivery = shipment_info[1] if shipment_info and shipment_info[1] else "N/A"

        sender_email = "birundhatextiles@gmail.com"
        sender_password = "dzqf jank cyee wrod"
        subject = "Order Confirmation"

        body = f"""
        Dear Customer,

        Your order with ID {order_id} has been confirmed.

        📦 Tracking Number: {tracking_number}
        🚚 Estimated Delivery Date: {estimated_delivery}

        Thank you for shopping with Birundha Textiles.

        Best Regards,  
        Birundha Textiles
        """

        # ✅ Send the email using your existing helper
        send_email(customer_email, subject, body)

    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        cursor.close()
        conn.close()
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = customer_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, customer_email, msg.as_string())
        server.quit()
        flash("Confirmation email sent successfully!", "success")
    except Exception as e:
        flash("Failed to send email: " + str(e), "danger")
@app.route("/admin/shipments/add", methods=["GET", "POST"])
def add_shipment():
    # Your logic for adding a shipment
    return render_template("add_shipment.html")
@app.route('/admin/shipments/update/<int:shipment_id>', methods=['GET', 'POST'])
def update_shipment_status(shipment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_status = request.form.get('status')

        try:
            # Use %s placeholders for PostgreSQL
            cursor.execute("UPDATE shipments SET status = %s WHERE id = %s", (new_status, shipment_id))
            conn.commit()
            flash("Shipment status updated successfully!", "success")
        except Exception as e:
            flash(f"Error updating shipment status: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('admin_shipments'))

    # Handle GET request - display current shipment status
    try:
        cursor.execute("SELECT * FROM shipments WHERE id = %s", (shipment_id,))
        shipment = cursor.fetchone()
    except Exception as e:
        flash(f"Error fetching shipment: {e}", "danger")
        shipment = None
    finally:
        cursor.close()
        conn.close()

    if shipment is None:
        flash("Shipment not found.", "danger")
        return redirect(url_for('admin_shipments'))

    return render_template('update_shipment_status.html', shipment=shipment, shipment_id=shipment_id)


from datetime import datetime, timedelta

def send_payment_confirmation_email(to_email, order_id, transaction_id):
    sender_email = "birundhatextiles@gmail.com"
    sender_password = "dzqf jank cyee wrod"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = f"Payment Confirmation for Order #{order_id}"

    body = f"""
    Dear Customer,<br><br>
    We have received your payment for <strong>Order #{order_id}</strong>.<br>
    <strong>Transaction ID:</strong> {transaction_id}<br><br>
    Thank you for shopping with us!<br><br>
    Regards,<br>
    Sri Birundha Textiles
    """

    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        raise Exception("Email send failed: " + str(e))

def send_payment_failed_email(to_email, order_id, transaction_id):
    subject = f"Payment Failed for Order #{order_id}"
    body = f"""
    Dear Customer,<br><br>
    Unfortunately, the payment for <strong>Order #{order_id}</strong> was not successful.<br>
    <strong>Transaction ID:</strong> {transaction_id}<br><br>
    Please try again or contact support if the amount was deducted.<br><br>
    Regards,<br>
    Sri Birundha Textiles
    """
    send_email(subject, body, to_email)

def send_delivery_issue_email(to_email, order_id, estimated_delivery):
    subject = f"Delivery Issue for Order #{order_id}"
    body = f"""
    Dear Customer,<br><br>
    Our records show that your order <strong>#{order_id}</strong> was scheduled for delivery on {estimated_delivery} 
    but it has not been marked as delivered.<br>
    If you have not received your order, please contact us as soon as possible for assistance.<br><br>
    Regards,<br>
    Sri Birundha Textiles
    """
    send_email(subject, body, to_email)

def send_delivery_success_email(to_email, order_id, estimated_delivery):
    subject = f"Order #{order_id} Delivered"
    body = f"""
    Dear Customer,<br><br>
    We are pleased to inform you that your order <strong>#{order_id}</strong> has been delivered on {estimated_delivery}.<br>
    Thank you for shopping with us!<br><br>
    Regards,<br>
    Sri Birundha Textiles
    """
    send_email(subject, body, to_email)

@app.route("/admin/orders")
def admin_orders():
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    status_filter = request.args.get("status", "")
    shipment_status_filter = request.args.get("shipment_status", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    confirm_order_id = request.args.get("confirm", None)
    update_payment_id = request.args.get("update_payment", None)
    new_payment_status = request.args.get("status_value", None)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ✅ Confirm order, update shipment status, and send email
        if confirm_order_id:
            cursor.execute("UPDATE orders SET status = 'Confirmed' WHERE id = %s", (confirm_order_id,))
            cursor.execute("UPDATE shipments SET status = 'Shipped' WHERE order_id = %s", (confirm_order_id,))
            conn.commit()

            cursor.execute("""
                SELECT c.email 
                FROM orders o 
                JOIN customers c ON o.customer_id = c.id 
                WHERE o.id = %s
            """, (confirm_order_id,))
            customer = cursor.fetchone()

            if customer:
                customer_email = customer[0]
                try:
                    send_confirmation_email(confirm_order_id, customer_email)
                    flash("Order confirmed, shipment marked as 'Shipped', and email sent!", "success")
                except Exception as mail_error:
                    flash("Order confirmed and shipment marked as 'Shipped', but failed to send email: " + str(mail_error), "warning")

        # ✅ Update payment status
        if update_payment_id and new_payment_status:
            cursor.execute(
                "UPDATE accounts SET payment_status = %s WHERE order_id = %s",
                (new_payment_status, update_payment_id)
            )
            conn.commit()
            flash("Payment status updated.", "success")

        # ✅ Fetch all order details with filters
        query = """
            SELECT o.id, c.name AS customer_name, o.order_date, o.total_price, o.status, 
                   c.email, c.address,
                   s.tracking_number, s.estimated_delivery, s.status AS shipment_status
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            LEFT JOIN shipments s ON o.id = s.order_id
        """

        conditions = []
        params = []

        if status_filter and status_filter.lower() != "all":
            conditions.append("o.status = %s")
            params.append(status_filter)

        if shipment_status_filter and shipment_status_filter.lower() != "all":
            conditions.append("s.status = %s")
            params.append(shipment_status_filter)

        if start_date:
            conditions.append("o.order_date::DATE >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("o.order_date::DATE <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY o.order_date DESC"

        cursor.execute(query, params)
        orders = cursor.fetchall()

        order_data = []
        for order in orders:
            order_id = order[0]

            cursor.execute(""" 
                SELECT oi.id, p.name AS product_name, oi.quantity, oi.price, p.image_url
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (order_id,))
            order_items = cursor.fetchall()

            cursor.execute(""" 
                SELECT payment_status, transaction_id 
                FROM accounts 
                WHERE order_id = %s
            """, (order_id,))
            account = cursor.fetchone()

            payment_status = account[0] if account else "Not Provided"
            transaction_id = account[1] if account and account[1] else "N/A"

            order_info = {
                "id": order_id,
                "customer_name": order[1],
                "order_date": order[2],
                "total_price": order[3],
                "status": order[4],
                "customer_email": order[5],
                "customer_address": order[6],
                "tracking_number": order[7],
                "estimated_delivery": order[8] if order[8] else "N/A",
                "shipment_status": order[9],
                "payment_status": payment_status,
                "transaction_id": transaction_id,
                "order_items": [
                    {
                        "id": item[0],
                        "product_name": item[1],
                        "quantity": item[2],
                        "price": item[3],
                        "image": item[4]
                    } for item in order_items
                ]
            }
            order_data.append(order_info)

    except Exception as e:
        flash("Database error: " + str(e), "danger")
        order_data = []

    finally:
        conn.close()

    return render_template(
        "admin_orders.html",
        orders=order_data,
        status_filter=status_filter,
        shipment_status_filter=shipment_status_filter,
        start_date=start_date,
        end_date=end_date
    )

from flask import request, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import sqlite3
@app.route("/generate_pdf_report")
def generate_pdf_report():
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO
    from flask import make_response, request

    order_date_from = request.args.get("order_date_from")
    order_date_to = request.args.get("order_date_to")
    status = request.args.get("status", "all")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT o.id, c.name, o.order_date, o.total_price, o.status
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE 1=1
    """
    params = []

    if order_date_from:
        query += " AND o.order_date >= %s"
        params.append(order_date_from)
    if order_date_to:
        query += " AND o.order_date <= %s"
        params.append(order_date_to)
    if status.lower() != "all":
        query += " AND o.status = %s"
        params.append(status)

    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()

    # Create PDF document
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Order Report", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Date Range: {order_date_from or 'N/A'} to {order_date_to or 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"Status: {status.capitalize()}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Table header
    data = [["Order ID", "Customer Name", "Order Date", "Total Price (₹)", "Status"]]
    total_sum = 0

    for order in orders:
        data.append([
            str(order[0]), order[1], str(order[2]), f"₹{order[3]:.2f}", order[4]
        ])
        total_sum += float(order[3])

    # Append total row
    data.append(["", "", "", f"Total: ₹{total_sum:.2f}", ""])

    # Create the table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (-2, -1), (-2, -1), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (-2, -1), (-2, -1), "Helvetica-Bold"),
    ]))

    elements.append(table)
    pdf.build(elements)

    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=order_report.pdf'
    return response
def send_payment_failed_email(to_email, order_id, transaction_id):
    sender_email = "birundhatextiles@gmail.com"
    sender_password = "dzqf jank cyee wrod"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = f"Payment Failed for Order #{order_id}"

    body = f"""
    Dear Customer,<br><br>
    Unfortunately, the payment for <strong>Order #{order_id}</strong> was not successful.<br>
    <strong>Transaction ID:</strong> {transaction_id}<br><br>
    Please try again or contact support if the amount was deducted.<br><br>
    Regards,<br>
    Sri Birundha Textiles
    """

    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        raise Exception("Failed to send email: " + str(e))
    
def send_email(subject, body, recipient):
    sender_email = "birundhatextiles@gmail.com"
       
    sender_password = "dzqf jank cyee wrod"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, msg.as_string())
    except Exception as e:
        print("Error sending email:", e)

def send_payment_email(order_id, recipient_email):
    subject = f"Payment Received for Order #{order_id}"
    message = f"""
    Dear Customer,

    Your payment for Order #{order_id} has been received successfully.
    We will proceed with your shipment soon.

    Thank you for shopping with us!

    Regards,
    Sri Birundha Textiles
    """
    send_email(subject, message, recipient_email)

@app.route("/update_payment_status/<int:order_id>", methods=["POST"])
def update_payment_status(order_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.get_json()
    new_status = data.get("status")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE accounts SET payment_status = ? WHERE order_id = ?", (new_status, order_id))
        conn.commit()

        cursor.execute("""
            SELECT c.email
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
        """, (order_id,))
        result = cursor.fetchone()

        if result and new_status == "Paid":
            customer_email = result[0]
            if customer_email:
                send_payment_email(order_id, customer_email)

        return jsonify({"success": True, "message": f"Payment status updated to {new_status}."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Step 1: Delete order items first
        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        conn.commit()

        # Step 2: Delete related shipments
        cursor.execute("DELETE FROM shipments WHERE order_id = ?", (order_id,))
        conn.commit()
        
        # Step 3: Now delete the order
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()

        return jsonify({"message": "Order deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/confirm_order/<int:order_id>', methods=['POST'])
def confirm_order(order_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed!"}), 500

    try:
        cursor = conn.cursor()

        # Fetch customer email
        cursor.execute("""
            SELECT c.email 
            FROM orders o 
            JOIN customers c ON o.customer_id = c.id 
            WHERE o.id = ?
        """, (order_id,))
        customer_email = cursor.fetchone()

        if not customer_email:
            return jsonify({"error": "Customer email not found!"}), 404

        # Fetch shipment status and ID
        cursor.execute("""
            SELECT id, status 
            FROM shipments 
            WHERE order_id = ?
        """, (order_id,))
        shipment = cursor.fetchone()

        if not shipment:
            return jsonify({"error": "Shipment record not found!"}), 404

        shipment_id, shipment_status = shipment

        if shipment_status != "Processing":
            return jsonify({"error": "Shipment status is not 'Processing', cannot confirm order."}), 400

        # Update shipment to 'Shipped'
        cursor.execute("UPDATE shipments SET status = ? WHERE id = ?", ("Shipped", shipment_id))
        conn.commit()

        # Update order to 'Confirmed'
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", ("Confirmed", order_id))
        conn.commit()

        # Send confirmation email
        send_confirmation_email(order_id, customer_email[0])

        return jsonify({"message": "Order confirmed, shipment updated from 'Processing' to 'Shipped', and email sent."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

def generate_transaction_id(length=13):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route("/account/<int:order_id>", methods=["GET", "POST"])
def account_details(order_id):
    if "user_id" not in session:
        flash("Please log in to access your account.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Default values for account details
    default_account_no = "6522940415987331"
    default_cvv = "879"
    default_expiry_month = "07"
    default_expiry_year = "2027"

    # Initialize transaction_id to None
    transaction_id = None

    if request.method == "POST":
        name = request.form["name"]
        account_no = request.form["account_no"]
        ifsc_no = request.form["ifsc_no"]
        cvv = request.form["cvv"]
        expiry_month = request.form["expiry_month"]
        expiry_year = request.form["expiry_year"]

        # Generate transaction ID only if default values are present
        if account_no == default_account_no and cvv == default_cvv and expiry_month == default_expiry_month and expiry_year == default_expiry_year:
            transaction_id = generate_transaction_id()
        else:
            # You may want to generate another transaction ID if you don't use the defaults
            transaction_id = generate_transaction_id()  # or keep it as None if needed

        payment_status = "Pending"

        cursor.execute(
    "SELECT id FROM accounts WHERE order_id = %s AND customer_id = %s",
    (order_id, session["user_id"])
)

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
    UPDATE accounts 
    SET name = %s, account_no = %s, ifsc_no = %s, transaction_id = %s, payment_status = %s,
        cvv = %s, expiry_month = %s, expiry_year = %s
    WHERE order_id = %s AND customer_id = %s
""", (
    name, account_no, ifsc_no, transaction_id, payment_status,
    cvv, expiry_month, expiry_year,
    order_id, session["user_id"]
))

        else:
            cursor.execute("""
    INSERT INTO accounts (
        customer_id, order_id, name, account_no, ifsc_no, transaction_id,
        payment_status, cvv, expiry_month, expiry_year
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    session["user_id"], order_id, name, account_no, ifsc_no, transaction_id,
    payment_status, cvv, expiry_month, expiry_year
))


        conn.commit()

        otp = str(random.randint(100000, 999999))

        cursor.execute("SELECT email FROM customers WHERE id = %s", (session["user_id"],))

        email = cursor.fetchone()[0]
        conn.close()

        subject = "OTP for Account Details Verification"
        body = f"Dear Customer,\n\nYour OTP for verifying account details is: {otp}\n\nThanks,\nSri Birundha Textiles"

        sender_email = "birundhatextiles@gmail.com"
        sender_password = "dzqf jank cyee wrod"  # Use app password
        receiver_email = email

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print(f"OTP sent to {receiver_email}")
        except Exception as e:
            print(f"Email error: {e}")
            flash("Failed to send OTP email. Please try again.", "danger")
            return redirect(url_for("account_details", order_id=order_id))

        session["otp_data"] = {
            "otp": otp,
            "order_id": order_id,
            "email": email,
            "transaction_id": transaction_id
        }

        return redirect(url_for("verify_account_otp"))

    # GET request
    cursor.execute("""
    SELECT name, account_no, ifsc_no, transaction_id, payment_status, cvv, expiry_month, expiry_year
    FROM accounts 
    WHERE order_id = %s AND customer_id = %s
""", (order_id, session["user_id"]))

    account = cursor.fetchone()

    cursor.execute(""" 
    SELECT SUM(quantity * price)
    FROM order_items
    WHERE order_id = %s
""", (order_id,))
    price_row = cursor.fetchone()
    total_price = price_row[0] if price_row and price_row[0] else 0.0

    conn.close()

    transaction_id = account[3] if account else "Not available"

    # Set default values from account data if available, else use hardcoded default values
    form_account_no = account[1] if account and account[1] else default_account_no
    form_cvv = account[5] if account and account[5] else default_cvv
    form_expiry_month = account[6] if account and account[6] else default_expiry_month
    form_expiry_year = account[7] if account and account[7] else default_expiry_year

    return render_template(
        "account_form.html",
        transaction_id=transaction_id,
        account=account,
        order_id=order_id,
        total_price=total_price,
        form_account_no=form_account_no,
        form_cvv=form_cvv,
        form_expiry_month=form_expiry_month,
        form_expiry_year=form_expiry_year
    )
@app.route("/verify_account_otp", methods=["GET", "POST"])
def verify_account_otp():
    if "otp_data" not in session:
        flash("OTP session expired. Please try again.", "warning")
        return redirect(url_for("home"))

    otp_data = session["otp_data"]
    order_id = otp_data["order_id"]
    email = otp_data["email"]

    if request.method == "POST":
        entered_otp = request.form["otp"]

        if entered_otp == otp_data["otp"]:
            conn = get_db_connection()
            cursor = conn.cursor()

            # ✅ Select the customer_id using the order_id (dynamic selection)
            cursor.execute("""
    SELECT c.id, c.name, c.email 
    FROM customers c
    JOIN orders o ON c.id = o.customer_id
    WHERE o.id = %s
""", (order_id,))

            result = cursor.fetchone()

            if not result:
                flash("Order or customer not found!", "danger")
                conn.close()
                return redirect(url_for("login"))

            customer_id, customer_name, customer_email = result

            # ✅ Get transaction_id from accounts table
            cursor.execute("""
    SELECT transaction_id FROM accounts
    WHERE order_id = %s AND customer_id = %s
            """, (order_id, customer_id))

            txn_result = cursor.fetchone()

            if not txn_result or not txn_result[0]:
                flash("Transaction not found!", "danger")
                conn.close()
                return redirect(url_for("account_details", order_id=order_id))

            transaction_id = txn_result[0]

            # ✅ Update payment status in accounts table
            cursor.execute("""
    UPDATE accounts SET payment_status = %s
    WHERE order_id = %s AND transaction_id = %s
""", ("Paid", order_id, transaction_id))


            # ✅ Get product names related to the order
            cursor.execute("""
    SELECT p.name 
    FROM products p
    JOIN order_items oi ON oi.product_id = p.id
    WHERE oi.order_id = %s
""", (order_id,))

            products = cursor.fetchall()
            product_names = ", ".join([p[0] for p in products]) if products else "your selected items"

            conn.commit()
            conn.close()

            session.pop("otp_data", None)

            # ✅ Compose and send email confirmation
            subject = "Your Order Has Been Placed Successfully"
            message = f"""
Dear {customer_name},

Thank you for your purchase! Your order has been successfully placed.

✅ Order ID: {order_id}
✅ Transaction ID: {transaction_id}
✅ Product(s): {product_names}

We appreciate your business and hope to serve you again soon.

- Sri Birundha Textiles
            """.strip()

            send_order_confirmation_email(customer_email, subject, message)

            flash("Payment verified and confirmation email sent!", "success")
            return render_template("order_success.html", order_id=order_id, transaction_id=transaction_id)
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template("verify_otp.html")
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_order_confirmation_email(to_email, subject, body):
    from_email = "birundhatextiles@gmail.com"
    password = "dzqfjankcyeewrod"  # App password (use .env file for security in production)

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
            print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", e)



import random
import smtplib
from flask import render_template, request, redirect, url_for, flash, session
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            flash("Please enter your email.", "danger")
            return render_template("forgot_password.html")

        conn = get_db_connection()
        if conn is None:
            flash("Database connection error.", "danger")
            return render_template("forgot_password.html")

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM customers WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user:
                otp = str(random.randint(100000, 999999))

                # Store OTP in session
                session["otp_data"] = {
                    "email": email,
                    "otp": otp,
                    "customer_id": user[0]
                }

                # Send email with OTP
                subject = "Sri Birundha Textiles - OTP for Password Reset"
                body = f"Your OTP for password reset is: {otp}"

                sender_email = "birundhatextiles@gmail.com"
                sender_password = "dzqf jank cyee wrod"  # Consider moving this to env variables
                receiver_email = email

                msg = MIMEMultipart()
                msg["From"] = sender_email
                msg["To"] = receiver_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                try:
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                        server.login(sender_email, sender_password)
                        server.send_message(msg)
                    flash("OTP has been sent to your email.", "success")
                    return redirect(url_for("verify_otp_reset"))
                except Exception as e:
                    print("Email error:", e)
                    flash("Failed to send OTP email.", "danger")
            else:
                flash("No account found with this email.", "danger")
        except Exception as e:
            print("Database error:", e)
            flash("Something went wrong. Please try again later.", "danger")
        finally:
            conn.close()

    return render_template("forgot_password.html")
@app.route("/verify_otp_reset", methods=["GET", "POST"])
def verify_otp_reset():
    otp_data = session.get("otp_data")

    if not otp_data:
        flash("Session expired or invalid access.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        new_password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if entered_otp != otp_data["otp"]:
            flash("❌ Incorrect OTP. Please try again.", "danger")
            return render_template("verify_otp_route.html")

        if new_password != confirm_password:
            flash("❗ Passwords do not match.", "danger")
            return render_template("verify_otp_route.html")

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        conn = get_db_connection()
        if conn is None:
            flash("Database connection error.", "danger")
            return render_template("verify_otp_route.html")

        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET password = %s WHERE email = %s",
                (hashed_password, otp_data["email"])
            )
            conn.commit()
            flash("✅ Password has been reset successfully!", "success")
            session.pop("otp_data", None)
            return redirect(url_for("login"))
        except Exception as e:
            conn.rollback()
            print("Database error:", e)
            flash("Something went wrong while resetting your password.", "danger")
        finally:
            conn.close()

    return render_template("verify_otp_route.html")
@app.route('/track', methods=['GET', 'POST'])
def track_order():
    tracking_info = None
    error = None

    conn = None
    cursor = None

    if request.method == 'POST':
        tracking_number = request.form.get('tracking_number', '').strip()

        if not tracking_number:
            error = "Please enter a tracking number."
            return render_template('track.html', tracking_info=tracking_info, error=error)

        try:
            conn = get_db_connection()
            if conn is None:
                raise Exception("Database connection failed.")

            cursor = conn.cursor()

            query = "SELECT status, estimated_delivery FROM shipments WHERE tracking_number = %s"
            cursor.execute(query, (tracking_number,))
            row = cursor.fetchone()

            if row:
                tracking_info = {
                    'status': row[0],
                    'estimated_delivery': row[1].strftime("%Y-%m-%d") if row[1] else "N/A"
                }
            else:
                error = "Tracking number not found."

        except Exception as e:
            error = f"Database error: {str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('track.html', tracking_info=tracking_info, error=error)

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    otp_data = session.get("otp_data")

    if not otp_data:
        flash("Session expired or invalid access.", "danger")
        return redirect(url_for("checkout"))

    if request.method == "POST":
        user_otp = request.form.get("otp")
        if user_otp == otp_data["otp"]:
            session.pop("otp_data", None)
            flash("✅ OTP verified successfully!", "success")
            return redirect(url_for("order_success", order_id=otp_data["order_id"]))
        else:
            flash("❌ Incorrect OTP. Please try again.", "danger")

    return render_template("verify_otp.html", email=otp_data["email"])



@app.route("/admin/order-details")
def admin_order_details():
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))
    return render_template("order_details.html")
@app.route('/admin/orders/confirm/<int:order_id>', methods=['POST'])
def confirm_order_status(order_id):
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ✅ Step 1: Update order status to "Confirmed"
        cursor.execute("UPDATE orders SET status = 'Confirmed' WHERE id = ?", (order_id,))
        conn.commit()  # Commit before fetching email
        
        # ✅ Step 2: Retrieve customer email
        cursor.execute("SELECT c.email FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.id = ?", (order_id,))
        customer_email = cursor.fetchone()

        if customer_email:
            send_confirmation_email(order_id, customer_email[0])  # ✅ Send email after update
            flash("Order confirmed and email sent.", "success")
        else:
            flash("Customer email not found.", "danger")

    except Exception as e:
        flash("Database error: " + str(e), "danger")
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for("admin_orders"))  # ✅ Redirect after completion

@app.route("/products")
def view_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, price, stock, pieces, description, image_url FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template("view_products.html", products=products)

# New route for product details
@app.route("/product/<int:product_id>")
def product_details(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, price, stock, pieces, description, image_url FROM products WHERE id = %s", (product_id,))

    product = cursor.fetchone()
    conn.close()

    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("view_products"))

    return render_template("product_detail.html", product=product)

@app.route("/admin/customers/edit/<int:id>", methods=["GET", "POST"])
def edit_customer(id):
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch customer data
    cursor.execute("SELECT id, name, phone, email, address FROM customers WHERE id = %s", (id,))
    customer = cursor.fetchone()

    if not customer:
        flash("Customer not found!", "danger")
        conn.close()
        return redirect(url_for("admin_customers"))

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        address = request.form["address"]  # ✅ add this line

        cursor.execute("""
            UPDATE customers 
            SET name = %s, phone = %s, email = %s, address = %s 
            WHERE id = %s
        """, (name, phone, email, address, id))  # ✅ use %s for PostgreSQL

        conn.commit()
        conn.close()

        flash("Customer updated successfully!", "success")
        return redirect(url_for("admin_customers"))

    conn.close()
    return render_template("edit_customer.html", customer=customer)



@app.route("/admin/customers/delete/<int:id>", methods=["POST"])
def delete_customer(id):
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = %s",
    (id,)
)
    conn.commit()
    conn.close()

    flash("Customer deleted successfully!", "success")
    return redirect(url_for("admin_customers"))

    conn.close()
    return render_template("edit_customer.html", customer=customer)
@app.route("/admin/products/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch product details
    cursor.execute("SELECT id, name, category, price, stock, pieces, description, image_url FROM products WHERE id = %s", (id,))

    product = cursor.fetchone()

    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("admin_products"))

    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        price = request.form["price"]
        stock = request.form["stock"]
        pieces = request.form["pieces"]
        description = request.form["description"]
        
        # Handle image upload
        file = request.files["image"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = f"uploads/{filename}"
        else:
            image_url = product[7]  # Keep existing image if not changed
        
        cursor.execute("""
    UPDATE products 
    SET name = %s, category = %s, price = %s, stock = %s, pieces = %s, description = %s, image_url = %s
    WHERE id = %s
""", (name, category, price, stock, pieces, description, image_url, id))

        conn.commit()
        conn.close()

        flash("Product updated successfully!", "success")
        return redirect(url_for("admin_products"))

    conn.close()
    return render_template("edit_product.html", product=product)
@app.route("/admin/products/delete/<int:id>", methods=["POST"])
def delete_product(id):
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Product deleted successfully!", "success")
    return redirect(url_for("admin_products"))
@app.route("/cart")
def view_cart():
    if "user_id" not in session:
        flash("Please log in to view your cart.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch customer details from the database using session user_id
    cursor.execute("SELECT id, name, email FROM customers WHERE id = %s", (session["user_id"],))

    customer = cursor.fetchone()

    if not customer:
        flash("Customer not found.", "danger")
        conn.close()
        return redirect(url_for("login"))

    # Get cart from session
    cart = session.get("cart", [])

    # Close DB connection
    conn.close()

    return render_template("cart.html", cart=cart, customer=customer)


@app.route("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch product details
    cursor.execute("SELECT id, name, price FROM products WHERE id = %s", (product_id,))

    product = cursor.fetchone()
    conn.close()

    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("view_products"))

    # Get user profile data (assuming stored in session)
    user_profile = session.get("user_profile", {})

    # Get or initialize the cart
    cart = session.get("cart", [])

    # Check if the product is already in the cart
    for item in cart:
        if item["product_id"] == product[0]:  
            flash(f"{product[1]} is already in your cart!", "info")
            return redirect(url_for("view_cart"))

    # Add the product only if it's not already in the cart
    cart.append({
        "product_id": product[0],
        "name": product[1],
        "price": product[2],
        "customer_id": user_profile.get("id"),
        "customer_name": user_profile.get("name"),
        "customer_email": user_profile.get("email"),
    })

    # Update session cart
    session["cart"] = cart

    flash(f"{product[1]} added to cart!", "success")
    return redirect(url_for("view_cart"))
@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", [])

    # Remove the item from cart
    cart = [item for item in cart if item["product_id"] != product_id]

    # Update session
    session["cart"] = cart
    flash("Item removed from cart!", "success")
    
    
    return redirect(url_for("view_cart"))

@app.route('/offline_orders', methods=['GET', 'POST'])
def offline_orders():
    # Establish a connection to PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor()

    # Handle POST request for placing an order
    if request.method == 'POST' and 'product_id[]' in request.form:
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        order_items = []
        total_order_price = 0
        order_group_id = str(uuid.uuid4())  # Unique ID for the order group

        # Loop through the selected products and quantities
        for i in range(len(product_ids)):
            product_id = product_ids[i]
            quantity = int(quantities[i])

            # Get product details (name, price, and available pieces)
            cursor.execute("SELECT name, price, pieces FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()

            if not product:
                flash("Invalid product selected!", "danger")
                return redirect(url_for('offline_orders'))

            name, price, current_pieces = product
            total = price * quantity
            total_order_price += total

            # Check if enough pieces are available
            new_pieces = current_pieces - quantity
            if new_pieces < 0:
                flash(f"Not enough pieces available for {name}. Only {current_pieces} left.", "danger")
                return redirect(url_for('offline_orders'))

            # Update the available stock in the products table
            cursor.execute("UPDATE products SET pieces = %s WHERE id = %s", (new_pieces, product_id))

            # Insert the order details into the offline_orders table
            cursor.execute(""" 
                INSERT INTO offline_orders (product_id, quantity, total_price, order_date, order_group_id)
                VALUES (%s, %s, %s, %s, %s)""",
                (product_id, quantity, total, datetime.now(), order_group_id)
            )

        # Commit the changes to the database
        conn.commit()
        flash("Order placed successfully!", "success")

    # Fetch the list of products for the form
    cursor.execute("SELECT id, name, price FROM products")
    products = cursor.fetchall()

    # 🔍 Handle search by order_group_id in the query parameters
    search_group_id = request.args.get('search')
    if search_group_id:
        cursor.execute(""" 
            SELECT o.id, o.product_id, o.quantity, o.total_price, o.order_date, o.order_group_id, p.name 
            FROM offline_orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.order_group_id = %s
            ORDER BY o.order_date DESC
        """, (search_group_id,))
    else:
        cursor.execute(""" 
            SELECT o.id, o.product_id, o.quantity, o.total_price, o.order_date, o.order_group_id, p.name 
            FROM offline_orders o
            JOIN products p ON o.product_id = p.id
            ORDER BY o.order_date DESC
        """)

    # Fetch the list of orders based on the search condition (if any)
    orders = cursor.fetchall()

    # Fetch the total value of all orders
    cursor.execute("SELECT SUM(total_price) FROM offline_orders")
    total_value = cursor.fetchone()[0] or 0

    # Close the cursor and the connection
    cursor.close()
    conn.close()

    # Return the rendered template with product data, orders, and total value
    return render_template('orders.html', products=products, orders=orders, total_value=total_value)


@app.route('/print_invoice/<int:order_id>')
def print_invoice(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the order_group_id for the given order_id
    cursor.execute("""
        SELECT o.order_group_id
        FROM offline_orders o
        WHERE o.id = %s
    """, (order_id,))
    order_group_id = cursor.fetchone()

    if not order_group_id:
        flash("Order not found!", "danger")
        return redirect(url_for('offline_orders'))

    order_group_id = order_group_id[0]  # Extract order_group_id from the tuple

    # Fetch all orders in the same order_group_id
    cursor.execute("""
        SELECT o.quantity, o.total_price, o.order_date, p.name, p.price
        FROM offline_orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.order_group_id = %s
        ORDER BY o.order_date DESC
    """, (order_group_id,))  # Correct parameter placeholder

    orders = cursor.fetchall()
    cursor.close()
    conn.close()

    if not orders:
        flash("No orders found for this group!", "danger")
        return redirect(url_for('offline_orders'))

    # Prepare the data to pass to the template
    order_details = []
    total_price = 0

    for order in orders:
        quantity, total_price_order, order_date, product_name, unit_price = order
        total_price += total_price_order  # Calculate total price for the group

        order_details.append({
            'product_name': product_name,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price_order,
            'order_date': order_date
        })

    # Passing order details and total price to the template
    return render_template('print_invoice.html',
                           order_details=order_details,
                           total_price=total_price,
                           order_group_id=order_group_id)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        flash("Please log in to proceed with checkout.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Send delivery emails and update status
    cursor.execute("""
    SELECT s.id, s.order_id, c.email
    FROM shipments s
    JOIN orders o ON s.order_id = o.id
    JOIN customers c ON o.customer_id = c.id
    WHERE DATE(s.estimated_delivery) = CURRENT_DATE
    AND s.status != 'Delivered';
""")


    deliveries_today = cursor.fetchall()

    for shipment_id, order_id, email in deliveries_today:
        subject = "Your Order Has Been Delivered"
        body = f"Hello,\n\nYour order with tracking number TRK{order_id}{session['user_id']} has been delivered today.\n\nThank you for shopping with us!"
        sender_email = "birundhatextiles@gmail.com"
        sender_password = "dzqf jank cyee wrod"
        receiver_email = email

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print(f"Email sent to {receiver_email}")
        except Exception as e:
            print(f"Email error: {e}")

        cursor.execute("UPDATE shipments SET status = 'Delivered' WHERE id = %s", (shipment_id,))

        conn.commit()

    # ✅ Fetch customer info (now includes address)
    cursor.execute("SELECT id, name, email, address FROM customers WHERE id = %s", (session["user_id"],))

    customer = cursor.fetchone()

    if not customer:
        flash("Customer details not found.", "danger")
        return redirect(url_for("login"))

    customer_id, customer_name, customer_email, customer_address = customer
    cart = session.get("cart", [])

    if request.method == "POST":
        # Update address
        new_address = request.form.get("address", "").strip()
        if new_address and new_address != customer_address:
           cursor.execute("UPDATE customers SET address = %s WHERE id = %s", (new_address, customer_id))

           conn.commit()
           customer_address = new_address

        # Process cart items
        updated_cart = []
        for item in cart:
            product_id = item["product_id"]
            selected_quantity = request.form.get(f"quantity_{product_id}")
            try:
                selected_quantity = int(selected_quantity)
                if selected_quantity < 1:
                    flash(f"Invalid quantity for {item['name']}.", "danger")
                    return redirect(url_for("checkout"))
            except ValueError:
                flash(f"Invalid input for {item['name']}.", "danger")
                return redirect(url_for("checkout"))

            updated_cart.append({
                "product_id": product_id,
                "name": item["name"],
                "price": item["price"],
                "quantity": selected_quantity,
            })

        total_price = sum(float(item["price"]) * item["quantity"] for item in updated_cart)

        # Insert into orders
        cursor.execute("""
    INSERT INTO orders (customer_id, total_price, order_date)
    VALUES (%s, %s, CURRENT_TIMESTAMP)
    RETURNING id;
""", (customer_id, total_price))

        order_id = cursor.fetchone()[0]
        conn.commit()

        # Insert order items and update stock
        for item in updated_cart:
            cursor.execute("""
    INSERT INTO order_items (order_id, product_id, quantity, price)
    VALUES (%s, %s, %s, %s);
""", (order_id, item["product_id"], item["quantity"], item["price"]))
        cursor.execute("UPDATE products SET pieces = pieces - %s WHERE id = %s", (item["quantity"], item["product_id"]))


        # Create shipment
        tracking_number = f"TRK{order_id}{customer_id}"
        cursor.execute("""
    INSERT INTO shipments (order_id, tracking_number, carrier, estimated_delivery, status)
    VALUES (%s, %s, %s, CURRENT_DATE + INTERVAL '5 days', 'Processing');
""", (order_id, tracking_number, 'FedEx'))

        conn.commit()
        session.pop("cart", None)
        flash("Order placed successfully! Please enter your account details for payment.", "success")
        return redirect(url_for("account_details", order_id=order_id))

    return render_template(
        "checkout.html",
        cart=cart,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_address=customer_address
    )





@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Please log in to access your profile.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone FROM customers WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("home"))

    return render_template("profile.html", user=user)


@app.route("/edit_profile", methods=["POST"])
def edit_profile():
    if "user_id" not in session:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name or not email or not phone:
        flash("All fields are required.", "danger")
        return redirect(url_for("profile"))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE customers SET name = %s, email = %s, phone = %s WHERE id = %s",
            (name, email, phone, user_id)
        )
        conn.commit()
        flash("Profile updated successfully!", "success")
    except Exception:
        conn.rollback()
        flash("Failed to update profile.", "danger")
    finally:
        conn.close()

    return redirect(url_for("profile"))


@app.route("/change_password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")

    if not old_password or not new_password:
        flash("All fields are required.", "danger")
        return redirect(url_for("profile"))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password FROM customers WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            flash("User not found!", "danger")
            return redirect(url_for("profile"))

        stored_password = user[0]
        hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()

        if stored_password == hashed_old_password or check_password_hash(stored_password, old_password):
            hashed_new_password = generate_password_hash(new_password)
            cursor.execute("UPDATE customers SET password = %s WHERE id = %s", (hashed_new_password, user_id))
            conn.commit()

            session.pop("user_id", None)
            session.pop("role", None)
            flash("Password updated successfully! Please log in again.", "success")
            return redirect(url_for("login"))
        else:
            flash("Incorrect current password!", "danger")
            return redirect(url_for("profile"))

    except Exception:
        conn.rollback()
        flash("Failed to change password.", "danger")
        return redirect(url_for("profile"))

@app.route("/view_orders")
def view_orders():
    if "user_id" not in session:
        flash("Please log in to view your orders.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    status_filter = request.args.get("status")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT o.id, o.order_date, o.total_price, o.status, 
           p.name, p.image_url, oi.quantity, oi.price,
           s.tracking_number, s.estimated_delivery, s.status AS shipment_status,
           a.payment_status,
           c.address AS customer_address
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    LEFT JOIN shipments s ON o.id = s.order_id
    LEFT JOIN accounts a ON o.id = a.order_id AND a.customer_id = o.customer_id
    JOIN customers c ON o.customer_id = c.id
    WHERE o.customer_id = %s
    """
    params = [user_id]

    if status_filter:
        query += " AND o.status = %s"
        params.append(status_filter)

    if start_date and end_date:
        query += " AND o.order_date BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    query += " ORDER BY o.order_date DESC"  # Optional: to show recent orders first

    cursor.execute(query, tuple(params))
    orders = cursor.fetchall()
    conn.close()

    return render_template("view_orders.html", orders=orders)






@app.route("/cancel_order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    if "user_id" not in session:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ensure the order belongs to the logged-in user
    cursor.execute("SELECT id, order_date, total_price, status FROM orders WHERE customer_id = %s AND id = %s", (user_id, order_id))

    order = cursor.fetchone()

    if not order:
        flash("Order not found!", "danger")
    elif order[3] == "Cancelled":
        flash("Order is already cancelled!", "info")
    else:
        cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE id = %s", (order_id,))

        conn.commit()
        flash("Order cancelled successfully!", "success")

    conn.close()
    return redirect(url_for("view_orders"))
@app.route("/admin/employees", methods=["GET", "POST"])
def admin_employees():
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        contact_number = request.form["contact_number"]
        salary = request.form["salary"]
        file = request.files["image"]

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            image_url = f"uploads/{filename}"  # Path relative to 'static' folder
        else:
            image_url = "uploads/default.png"

        # Insert new employee and return emp_id
        cursor.execute(
            "INSERT INTO employees (name, age, contact_number, salary, image_url) VALUES (%s, %s, %s, %s, %s) RETURNING emp_id;",
            (name, age, contact_number, salary, image_url),
        )
        emp_id = cursor.fetchone()['emp_id']
        emp_number = f"BITX{emp_id}"

        # Update emp_number
        cursor.execute("UPDATE employees SET emp_number = %s WHERE emp_id = %s;", (emp_number, emp_id))
        conn.commit()

        flash("Employee added successfully!", "success")

    # Fetch all employees
    cursor.execute("SELECT emp_id, name, age, contact_number, salary, image_url, emp_number FROM employees ORDER BY emp_id DESC;")
    employees = cursor.fetchall()
    conn.close()

    # Determine the next emp_number
    next_emp_number = f"BXTX{employees[0]['emp_id'] + 1}" if employees else "BXTX1"

    return render_template("employees.html", employees=employees, emp_number=next_emp_number)
@app.route("/admin/employees/edit/<int:emp_id>", methods=["GET", "POST"])
def edit_employee(emp_id):
    if session.get("role") != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Fetch existing employee details
    cursor.execute("SELECT * FROM employees WHERE emp_id = %s", (emp_id,))
    employee = cursor.fetchone()

    if not employee:
        flash("Employee not found!", "danger")
        conn.close()
        return redirect(url_for("admin_employees"))

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        contact_number = request.form["contact_number"]
        salary = request.form["salary"]

        # Handle file upload
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            image_url = f"static/uploads/{filename}"  # Store relative path
        else:
            image_url = employee['image_url']  # Keep the existing image if no new file uploaded

        cursor.execute("""
            UPDATE employees 
            SET name = %s, age = %s, contact_number = %s, salary = %s, image_url = %s 
            WHERE emp_id = %s
        """, (name, age, contact_number, salary, image_url, emp_id))

        conn.commit()
        conn.close()

        flash("Employee updated successfully!", "success")
        return redirect(url_for("admin_employees"))

    conn.close()
    return render_template("edit_employee.html", employee=employee)   

@app.route("/admin/employees/delete/<int:emp_id>", methods=["POST"])
def delete_employee(emp_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE emp_id = %s", (emp_id,))

    conn.commit()
    conn.close()
    return redirect(url_for("admin_employees"))

@app.route('/admin/suppliers')
def admin_suppliers():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # 👈 important
    cursor.execute("""
        SELECT id, 'BITXSN' || id::VARCHAR AS supplier_number, name, contact, email, address 
        FROM Suppliers
    """)
    suppliers = cursor.fetchall()
    conn.close()
    return render_template('admin_suppliers.html', suppliers=suppliers)

# 🟢 Add a Supplier
@app.route('/suppliers/add', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        email = request.form['email']
        address = request.form['address']

        conn = get_db_connection()
        cursor = conn.cursor()

        # 🔹 Get the next ID for supplier
        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM Suppliers")
        next_id = cursor.fetchone()[0]

        # 🔹 Generate supplier_number as BITXSN + ID
        supplier_number = f"BITXSN{next_id}"

        # 🔹 Insert into database
        cursor.execute("""
            INSERT INTO Suppliers (supplier_number, name, contact, email, address) 
            VALUES (%s, %s, %s, %s, %s)
        """, (supplier_number, name, contact, email, address))

        conn.commit()
        conn.close()

        flash("Supplier added successfully!", "success")
        return redirect(url_for('admin_suppliers'))

    return render_template('supplier_form.html', action="Add")

# 🟢 Edit a Supplier
@app.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch the supplier data by ID
            cursor.execute("SELECT * FROM Suppliers WHERE id = %s", (id,))
            supplier = cursor.fetchone()

            if not supplier:
                flash("Supplier not found!", "danger")
                return redirect(url_for('admin_suppliers'))

            # Handle POST request to update supplier details
            if request.method == 'POST':
                name = request.form['name']
                contact = request.form['contact']
                email = request.form['email']
                address = request.form['address']

                # Update the supplier details in the database
                cursor.execute("""
                    UPDATE Suppliers
                    SET name=%s, contact=%s, email=%s, address=%s
                    WHERE id=%s
                """, (name, contact, email, address, id))

                conn.commit()  # Commit the changes to the database
                flash("Supplier updated successfully!", "success")
                return redirect(url_for('admin_suppliers'))

    except Exception as e:
        conn.rollback()  # Rollback in case of error
        flash("Error updating supplier: " + str(e), "danger")
    finally:
        conn.close()  # Ensure the connection is closed

    # Render the form with existing supplier data
    return render_template('supplier_form.html', action="Edit", supplier=supplier)


# 🟢 Delete a Supplier
@app.route('/suppliers/delete/<int:id>')
def delete_supplier(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
    "SELECT * FROM suppliers WHERE id = %s",
    (id,)
)

    supplier = cursor.fetchone()

    if not supplier:
        flash("Supplier not found!", "danger")
        return redirect(url_for('admin_suppliers'))

    cursor.execute("DELETE FROM Suppliers WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    flash("Supplier deleted successfully!", "danger")
    return redirect(url_for('admin_suppliers'))
# ✅ Supplier Login
@app.route('/supplier_login', methods=['GET', 'POST'])
def supplier_login():
    if request.method == 'POST':
        supplier_number = request.form['supplier_number']
        contact = request.form['contact']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT supplier_number FROM Suppliers WHERE supplier_number = %s AND contact = %s", 
               (supplier_number, contact))

        supplier = cursor.fetchone()
        conn.close()

        if supplier:
            session.permanent = True  # Keep the session active
            session['supplier_number'] = supplier_number
            flash("Login successful!", "success")
            return redirect(url_for('add_supplier_item'))
        else:
            flash("Invalid supplier number or password!", "danger")

    return render_template('supplier_login.html')
@app.route('/view_supplier_items')
def view_supplier_items():
    items = SupplierItem.query.all()
    return render_template('view_supplier_items.html', items=items)
@app.route('/add_supplier_item', methods=['GET', 'POST'])
def add_supplier_item():
    if 'supplier_number' not in session:
        flash("You must be logged in as a supplier!", "danger")
        return redirect(url_for('supplier_login'))

    if request.method == 'POST':
        supplier_number = session['supplier_number']  # Get supplier from session
        shop_name = request.form['shop_name']
        shop_address = request.form['shop_address']
        contact = request.form['contact']
        item_name = request.form['item_name']
        item_quantity = request.form['item_quantity']
        item_value = request.form['item_value']
        
        # Handling file uploads
        photo = request.files.get('photo')
        video = request.files.get('video')

        photo_filename = None
        video_filename = None

        # Save photo if uploaded
        if photo and photo.filename:
            photo_filename = f"{supplier_number}_photo_{photo.filename}"
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        # Save video if uploaded
        if video and video.filename:
            video_filename = f"{supplier_number}_video_{video.filename}"
            video.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))

        # Save item in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO Supplier_goods (supplier_number, shop_name, shop_address, contact, item_name, item_quantity, item_value, photo_url, video_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (supplier_number, shop_name, shop_address, contact, item_name, item_quantity, item_value, photo_filename, video_filename))

        conn.commit()
        conn.close()

        flash("Item added successfully!", "success")
        return redirect(url_for('supplier_goods'))

    return render_template('add_supplier_item.html')
@app.route("/supplier_goods")
def supplier_goods():
    if "supplier_number" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("supplier_login"))

    conn = get_db_connection()
    if conn is None:
        flash("Database unavailable; please try again later.", "danger")
        return redirect(url_for("supplier_login"))

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM supplier_goods "
        "WHERE supplier_number = %s "
        "ORDER BY id DESC",
        (session["supplier_number"],)
    )
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("supplier_goods.html", items=items)

import os
from werkzeug.utils import secure_filename
from flask import current_app

@app.route('/edit_supplier_goods/<int:item_id>', methods=['GET', 'POST'])
def edit_supplier_goods(item_id):
    if 'supplier_number' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('supplier_login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get the item
    cursor.execute("SELECT * FROM supplier_goods WHERE id = %s AND supplier_number = %s", (item_id, session['supplier_number']))
    item = cursor.fetchone()

    if not item:
        cursor.close()
        conn.close()
        flash("Item not found!", "danger")
        return redirect(url_for('supplier_goods'))

    if request.method == 'POST':
        shop_name     = request.form.get('shop_name')
        shop_address  = request.form.get('shop_address')
        contact       = request.form.get('contact')
        item_name     = request.form.get('item_name')
        item_quantity = request.form.get('item_quantity')
        item_value    = request.form.get('item_value')

        # File uploads
        photo_file = request.files.get('photo')
        video_file = request.files.get('video')

        # Save files and update URLs if new ones are uploaded
        photo_url = save_file(photo_file) if photo_file and photo_file.filename else item['photo_url']
        video_url = save_file(video_file) if video_file and video_file.filename else item['video_url']

        # Update DB
        cursor.execute("""
            UPDATE supplier_goods SET
                shop_name = %s,
                shop_address = %s,
                contact = %s,
                item_name = %s,
                item_quantity = %s,
                item_value = %s,
                photo_url = %s,
                video_url = %s
            WHERE id = %s AND supplier_number = %s
        """, (
            shop_name, shop_address, contact,
            item_name, item_quantity, item_value,
            photo_url, video_url,
            item_id, session['supplier_number']
        ))

        conn.commit()
        cursor.close()
        conn.close()
        flash("Item updated successfully!", "success")
        return redirect(url_for('supplier_goods'))

    # GET
    cursor.close()
    conn.close()
    return render_template('edit_supplier_goods.html', item=item)


def save_file(file_storage):
    if not file_storage or file_storage.filename == '':
        return None

    if not allowed_file(file_storage.filename):
        return None

    filename = secure_filename(file_storage.filename)
    upload_path = os.path.join(current_app.static_folder, 'uploads', filename)
    file_storage.save(upload_path)
    return filename


@app.route('/delete_supplier_goods/<int:item_id>', methods=['POST'])
def delete_supplier_goods(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if item exists
    cursor.execute("SELECT * FROM SupplierGoods WHERE id=?", (item_id,))
    item = cursor.fetchone()
    
    if not item:
        flash("Item not found!", "danger")
        return redirect(url_for('supplier_goods'))

    # Delete associated files (photo & video) if they exist
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], item[6]) if item[6] else None
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], item[7]) if item[7] else None

    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)
    
    if video_path and os.path.exists(video_path):
        os.remove(video_path)

    # Delete item from database
    cursor.execute("DELETE FROM SupplierGoods WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    flash("Item deleted successfully!", "success")
    return redirect(url_for('supplier_goods'))
@app.route("/admin/shipments")
def admin_shipments():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, order_id, tracking_number, carrier, estimated_delivery, status 
        FROM shipments
        ORDER BY estimated_delivery DESC;
    """)
    shipments = [
        {
            "id": row[0],
            "order_id": row[1],
            "tracking_number": row[2],
            "carrier": row[3],
            "estimated_delivery": row[4],
            "status": row[5],
        }
        for row in cursor.fetchall()
    ]
    conn.close()

    return render_template("admin_shipments.html", shipments=shipments)
def process_deliveries():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.order_id, c.email
        FROM shipments s
        JOIN orders o ON s.order_id = o.id
        JOIN customers c ON o.customer_id = c.id
        WHERE s.estimated_delivery::date = CURRENT_DATE
        AND s.status != 'Delivered';
    """)
    deliveries_today = cursor.fetchall()

    for shipment_id, order_id, email in deliveries_today:
        subject = "Your Order Has Been Delivered"
        body = f"Hello,\n\nYour order with tracking number TRK{order_id}{shipment_id} has been delivered today.\n\nThank you for shopping with us!"
        sender_email = "birundhatextiles@gmail.com"
        sender_password = "your_app_specific_password"  # Replace with your actual app-specific password
        receiver_email = email

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print(f"[✅] Email sent to {receiver_email}")
        except Exception as e:
            print(f"[❌] Email error for {receiver_email}: {e}")

        cursor.execute("UPDATE shipments SET status = 'Delivered' WHERE id = %s;", (shipment_id,))
        conn.commit()

    cursor.close()
    conn.close()


@app.route("/order_success/<int:order_id>")
def order_success(order_id):
    if not order_id:
        flash("Order ID is missing!", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Get transaction_id from accounts table
    cursor.execute("SELECT transaction_id FROM accounts WHERE order_id = ?", (order_id,))
    result = cursor.fetchone()
    conn.close()

    transaction_id = result[0] if result and result[0] else "Not available"

    return render_template("order_success.html", order_id=order_id, transaction_id=transaction_id)


if __name__ == "__main__":
    process_deliveries()
    app.run(debug=True)
 