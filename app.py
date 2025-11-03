from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session
from flask_mysqldb import MySQL
import pandas as pd
import io
import MySQLdb.cursors
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'users'  # Change this to a secure secret key

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'inventory'
mysql = MySQL(app)


# ---------------- LOGIN & LOGOUT ----------------
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('people_list'))
        else:
            return render_template('login.html', error='Wrong username or password')
    return render_template('login.html')



# ---------------- PRODUCTS ----------------
@app.route('/products')
def product_list():
    cur = mysql.connection.cursor()
    search = request.args.get('search')
    if search:
        cur.execute(
            "SELECT * FROM products WHERE name LIKE %s OR category LIKE %s ORDER BY id DESC",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cur.execute("SELECT * FROM products ORDER BY id DESC")
    products = cur.fetchall()
    cur.close()
    return render_template('product_list.html', products=products, search=search)


# app product
@app.route('/products/add', methods=['GET','POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO products(name, category, price, stock) VALUES (%s,%s,%s,%s)",
                    (name, category, price, stock))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('product_list'))
    return render_template('add.html')

# edit product
@app.route('/products/edit/<int:id>', methods=['GET','POST'])
def edit_product(id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        cur.execute("UPDATE products SET name=%s, category=%s, price=%s, stock=%s WHERE id=%s",
                    (name, category, price, stock, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('product_list'))
    cur.execute("SELECT * FROM products WHERE id=%s", (id,))
    product = cur.fetchone()
    cur.close()
    return render_template('edit.html', product=product)

# delete product
@app.route('/products/delete/<int:id>')
def delete_product(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('product_list'))

# view product
@app.route('/products/view/<int:id>')
def view_product(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id=%s", (id,))
    product = cur.fetchone()
    cur.close()
    if not product:
        return render_template('error.html', message="Product not found"), 404

    product_data = {
        "id": product[0],
        "name": product[1],
        "category": product[2],
        "price": float(product[3]),
        "stock": int(product[4]),
        "date": product[5].strftime('%Y-%m-%d %H:%M:%S')
    }
    return render_template('view_product.html', product=product_data)

# report
@app.route('/view')
def view():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]
    cur.execute("SELECT SUM(stock) FROM products")
    total_stock = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(price*stock) FROM products")
    total_value = cur.fetchone()[0] or 0
    cur.close()
    return render_template('view.html',
                           products=products,
                           total_products=total_products,
                           total_stock=total_stock,
                           total_value=total_value)

# show about graph
@app.route('/category_quantity')
def category_quantity():
    cur = mysql.connection.cursor()
    cur.execute("SELECT category, SUM(stock) FROM products GROUP BY category")
    data = cur.fetchall()
    cur.close()
    categories = [row[0] for row in data]
    quantities = [row[1] for row in data]
    return jsonify({'categories': categories, 'quantities': quantities})

# download excel
@app.route('/download/excel')
def download_excel():
    cur = mysql.connection.cursor()
    cur.execute("SELECT name, category, price, stock FROM products ORDER BY id ASC")
    data = cur.fetchall()
    cur.close()
    # Add automatic numbering
    numbered_data = [(i+1, *row) for i, row in enumerate(data)]  # i+1 = 1,2,3...
    # Create DataFrame
    df = pd.DataFrame(numbered_data, columns=['No', 'Name', 'Category', 'Price', 'Stock'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')
    output.seek(0)
    return send_file(output, download_name="products.xlsx", as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# download pdf
@app.route('/download/pdf')
def download_pdf():
    cur = mysql.connection.cursor()
    cur.execute("SELECT name, category, price, stock FROM products ORDER BY id ASC")
    data = cur.fetchall()
    cur.close()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "Product List Report")
    # Headers and positions
    headers = ["No", "Name", "Category", "Price", "Stock"]
    x_pos = [50, 100, 250, 400, 470]
    y = 720
    # Draw header
    p.setFont("Helvetica-Bold", 12)
    for h, x in zip(headers, x_pos):
        p.drawString(x, y, h)
    y -= 20
    # Draw rows with automatic numbering
    p.setFont("Helvetica", 12)
    for i, row in enumerate(data, start=1):  # i = 1,2,3...
        if y < 50:
            p.showPage()
            y = 750
            p.setFont("Helvetica", 12)
        p.drawString(x_pos[0], y, str(i))  # Number column
        for val, x in zip(row, x_pos[1:]):  # Other columns
            p.drawString(x, y, str(val))
        y -= 20
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="products.pdf", mimetype="application/pdf")


# ---------------- PEOPLE ----------------
@app.route('/people')
def people_list():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM people ORDER BY id DESC")
    people = cur.fetchall()
    cur.close()
    return render_template('about.html', people=people)


# profile
@app.route('/profile')
def profile():
    # Prefer session values to avoid querying columns that may not exist in DB
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    user = {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'email': session.get('email', 'N/A'),
        'created_at': session.get('created_at', 'N/A')}
    # Try to enrich from DB if available, but handle missing columns gracefully
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT id, username FROM users WHERE id=%s", (user['id'],))
        row = cur.fetchone()
        cur.close()
        if row:
            user['username'] = row.get('username', user['username'])
    except Exception:
        # ignore DB errors (such as missing columns) and use session values
        pass
    return render_template('profile.html', user=user)


# add people
@app.route('/add')
def add_person_form():
    return render_template('add_people.html')

@app.route('/add_person', methods=['POST'])
def add_person():
    name = request.form['name']
    sex = request.form['sex']
    phone = request.form['phone']
    gmail = request.form['email']
    position = request.form['position']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO people(name, sex, phone, gmail, position) VALUES (%s,%s,%s,%s,%s)",
                (name, sex, phone, gmail, position))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('people_list'))


# delete people
@app.route('/delete_person/<int:id>', methods=['POST'])
def delete_person(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM people WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('people_list'))


# view people
@app.route('/person/<int:id>')
def view_person(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM people WHERE id=%s", (id,))
    person = cur.fetchone()
    cur.close()
    if not person:
        return render_template('error.html', message="Person not found"), 404
    person.pop('id', None)
    return render_template('view_people.html', person=person)


# ---------------- ORDERS ----------------
@app.route('/orders')
def orders_list():
    filter_status = request.args.get('status', '')
    cur = mysql.connection.cursor()
    if filter_status in ('Waiting', 'Complete'):
        cur.execute("SELECT * FROM orders WHERE status=%s ORDER BY id ASC", (filter_status,))
    else:
        cur.execute("SELECT * FROM orders ORDER BY id ASC")
    orders = cur.fetchall()
    cur.close()
    return render_template('orders.html', orders=orders, filter_status=filter_status)


# delete order
@app.route('/orders/delete/<int:id>')
def delete_order(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM orders WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('orders_list'))


# edit order
@app.route('/orders/edit/<int:id>')
def edit_order(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM orders WHERE id=%s", (id,))
    order = cur.fetchone()
    cur.close()
    return render_template('edit_order.html', order=order)

# update order
@app.route('/orders/update/<int:id>', methods=['POST'])
def update_order(id):
    name = request.form['name']
    category = request.form['category']
    stock = request.form['stock']
    status = request.form['status']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE orders SET name=%s, category=%s, stock=%s, status=%s WHERE id=%s",
                (name, category, stock, status, id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('orders_list'))

# ---------------- RUN APP ----------------
if __name__ == '__main__':
    app.run(debug=True)
