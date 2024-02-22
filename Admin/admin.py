from werkzeug.security import  generate_password_hash,check_password_hash
from flask_socketio import SocketIO
from flask import *
from flask_wtf import FlaskForm
from flask_login import *
from wtforms import StringField, IntegerField, TextAreaField,FileField
import sqlite3
from wtforms.validators import DataRequired
import socket


def get_ip_address():
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Connect to any IP address and port (here, Google's public DNS server)
        s.connect(('8.8.8.8', 80))

        # Get the local IP address bound to the socket
        ip_address = s.getsockname()[0]

        return ip_address
    except Exception as e:
        print(f"Error: {e}")
        return "127.0.0.1"


app=Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'mysecret'
#Path where the image is stored
app.config['UPLOAD_FOLDER'] = '/media/lenovo/Windows 10/Nursery-Management-System/Client/Product'
common_url=f'http://{get_ip_address()}:2802'
sockets = SocketIO(app)
#login Manger
login_manager = LoginManager()
login_manager.init_app(app)
DATABASE="./../plants.db"

class AddProduct(FlaskForm):
    name = StringField('Name')
    price = IntegerField('Price')
    stock = IntegerField('Stock')
    description = TextAreaField('Description')
    #image=StringField("image")
    image = FileField('Image', validators=[DataRequired()])

class EditProduct(FlaskForm):
    name = StringField('Name')
    price = IntegerField('Price')
    stock = IntegerField('Stock')
    description = TextAreaField('Description')
    #image=StringField("image")
    image = FileField('Image', validators=[DataRequired()])

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

# Initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('./../schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


class Admin(UserMixin):
    def __init__(self, user_id, email):
        self.s_id = user_id
        self.email = email
    @staticmethod
    def get_by_id(user_id):
        db=get_db()
        user_data = db.execute("SELECT * FROM supplier WHERE s_id = ?", (user_id,)).fetchone()
        if user_data:
            return Admin(user_data['s_id'], user_data['s_email'])
        else:
            return None
    def get_id(self):
        return str(self.s_id)
# Define a Admin loader function
@login_manager.user_loader
def load_user(user_id):
    # Here, you'll load the user from your database based on the user_id
    # For demonstration purposes, let's assume your User class has a method `get_by_id`
    return Admin.get_by_id(user_id)


# Modify your Admin class to inherit from UserMixin
class Admin(UserMixin):
    def __init__(self, user_id, email):
        self.s_id = user_id
        self.email = email
    @staticmethod
    def get_by_id(user_id):
        db=get_db()
        user_data = db.execute("SELECT * FROM supplier WHERE s_id = ?", (user_id,)).fetchone()
        if user_data:
            return Admin(user_data['s_id'], user_data['s_email'])
        else:
            return None
    def get_id(self):
        return str(self.s_id)

@app.route('/add_stock/<pid>/<sid>')
def add_stock(pid,sid):
    db=get_db()
    db.execute("UPDATE Product SET stock_available = stock_available + ? WHERE p_id = ? AND supplier_id= ?;",
               (1,pid,sid))
    db.commit()
    return redirect(url_for('admin',index=sid))


@app.route('/delete_stock/<pid>/<sid>')
def delete_stock(pid,sid):
    db=get_db()
    db.execute("UPDATE Product SET stock_available = stock_available -  ? WHERE p_id = ? AND supplier_id= ?;",
               (1,pid,sid))
    db.commit()
    return redirect(url_for('admin',index=sid))
# Define route for admin
@app.route('/admin/<index>')
@login_required
def admin(index):
    db = get_db()
    products_cursor = db.execute('SELECT * FROM Product WHERE supplier_id=?',(index))
    products = [dict(row) for row in products_cursor.fetchall()]
    products_in_stock_cursor = db.execute("SELECT * FROM Product WHERE stock_available > 0;")
    products_in_stock = ([dict(row) for row in products_in_stock_cursor.fetchall()])
    orders_cursor = db.execute("SELECT * FROM Orders o ,Product p WHERE o.p_id=p.p_id AND supplier_id=?",(index))
    orders = [dict(row) for row in orders_cursor.fetchall()]
    order_totals = []
    for order in orders:
        order_total_cursor = db.execute(
            "SELECT SUM(oi.quantity * p.price)   AS order_total FROM order_item oi JOIN Product p ON oi.p_id = p.p_id WHERE oi.order_item_id = ?;",
            (order['order_id'],))
        order_total = [dict(row) for row in order_total_cursor.fetchall()]
        order_totals.append(order_total)
    user = []
    for order in orders:
        users_cursor = db.execute('SELECT First_Name, last_Name FROM users WHERE user_id=?', (order['u_id'],))
        user.append([dict(row) for row in users_cursor.fetchall()])
    orders_info = []

    for order_dict, user_list in zip(orders, user):
        order_info = {}
        for key in ['order_id', 'status', 'reference','First_Name', 'last_Name']:
            order_info[key] = order_dict[key]
        orders_info.append(order_info)
    order_information=[]
    for order_dict,order_total in zip(orders_info,order_totals):
        order_info = {}
        for key in ['order_id', 'status', 'reference']:
            order_info[key] = order_dict[key]

        for key in ['First_Name', 'last_Name']:
            order_info[key] =order_dict[key]
        for key in ['First_Name', 'last_Name']:
            order_info[key] =order_dict[key]
        for key in ['order_total']:
            order_info[key] =order_total[0][key]
        order_information.append(order_info)
    return render_template('index.html', admin=True, products=products, products_in_stock=len(products_in_stock), orders=order_information, user=user,admin_log=current_user,home=url_for('admin',index=index))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    import os
    form = AddProduct()
    db=get_db()
    if form.validate_on_submit():
        user_id = None
        if isinstance(current_user, Admin):
            user_id = current_user.s_id
        image = form.image.data
        filename = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.execute("INSERT INTO Product(p_name,price,stock_available,Description,supplier_id,image) VALUES(?,?,?,?,?,?);",(form.name.data, form.price.data, form.stock.data, form.description.data,user_id,filename))

        db.commit()

        return redirect(url_for('admin',index=current_user.s_id))

    return render_template('add-product.html', admin=True, form=form,admin_log=current_user,home=url_for('admin',index=current_user.s_id))

# Route to edit an existing product
@app.route('/edit_product/<int:id>/<int:sid>', methods=['GET', 'POST'])
def edit_product(id,sid):
    conn = get_db()
    product = conn.execute('SELECT * FROM Product WHERE p_id = ?', (id,)).fetchone()
    conn.close()
    form = EditProduct(obj=product)
    if form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        stock = form.stock.data
        description = form.description.data
        conn = get_db()
        conn.execute('UPDATE Product SET p_name = ?, price = ?, stock_available = ?, Description = ? WHERE p_id = ?', (name, price, stock, description, id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin',index=sid))
    return render_template('edit_product.html', form=form, product=product,user=current_user)

@app.route('/order/<order_id>')
@login_required
def order(order_id):
    db=get_db()
    order = db.execute("SELECT * FROM Orders WHERE order_id=?",(order_id))
    orders=[dict(row) for row in order.fetchall()]
    order_totals = []
    for order in orders:
        order_total_cursor = db.execute(
            "SELECT SUM(oi.quantity * p.price)  AS order_total FROM order_item oi JOIN Product p ON oi.p_id = p.p_id WHERE oi.order_item_id = ?;",
            (order['order_id'],))
        order_total = [dict(row) for row in order_total_cursor.fetchall()]
        order_totals.append(order_total)
    order_totals=order_totals[0][0]['order_total']
    user = []
    for order in orders:
        users_cursor = db.execute('SELECT First_Name, last_Name,u_address,u_contact,user_email,state,city,country FROM Orders WHERE u_id=?', (order['u_id'],))
        user.append([dict(row) for row in users_cursor.fetchall()])
    orders_info = []

    for order_dict, user_list in zip(orders, user):
        order_info = {}
        for key in ['order_id', 'status', 'reference','PaymentType']:
            order_info[key] = order_dict[key]

        for key in ['First_Name', 'last_Name','u_address','u_contact','user_email','city','user_email','city','country','state']:
            order_info[key] = user_list[0][key]
        orders_info.append(order_info)
    quantity_total=db.execute("SELECT SUM(oi.quantity) FROM order_item oi WHERE oi.order_item_id = ?;",(order_id))
    quantity_total=[{"quantity_total":row['SUM(oi.quantity)']} for row in quantity_total.fetchall()]
    product=db.execute('SELECT p.p_id,p.p_name,p.price,oi.quantity,p.price FROM Product as p,order_item as oi WHERE p.p_id=oi.p_id ;')
    products=[dict(row) for row in product.fetchall()]
    return render_template('view-order.html',product=products, order=orders_info[0], admin=True,order_total=order_totals,quantity_total=quantity_total[0]['quantity_total'],admin_log=current_user,home=current_user.s_id)

@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    db=get_db()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Retrieve user information from the database
        user_sql = db.execute("SELECT  * FROM supplier WHERE s_email = ?", (email,))
        user = [dict(row) for row in user_sql.fetchall()]
        if user and check_password_hash(user[0]['password_hash'],password):
            flash('Logged in successfully!', category='success')
            admin_login_c=Admin(user[0]['s_id'], user[0]['s_email'])
            login_user(admin_login_c, remember=True,force=True)
            return redirect(url_for('admin',index=user[0]['s_id']))
        else:
            # Invalid credentials
            flash('Invalid email or password. Please try again.', 'error')  # Error message

    return render_template('login.html',user=current_user,common_url=common_url)

@app.route('/admin_logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))


@app.route("/admin_signup",methods=['GET','POST'])
def admin_signup():
    db=get_db()
    if request.method=="POST":
        email = request.form.get('email')
        cname = request.form.get('cname')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        address=request.form.get('address')
        contact=request.form.get('contact')
        email_exits_sql = db.execute("SELECT  * FROM supplier WHERE s_email = ?", (email,))
        email_exits = [dict(row) for row in email_exits_sql.fetchall()]
        if email_exits:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(cname) < 2:
            flash('Company Name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            db.execute('INSERT INTO supplier(company_name,s_email,password_hash,s_contact,s_address) VALUES(?,?,?,?,?)',(cname,email,generate_password_hash(password1,method='scrypt'),contact,address))
            db.commit()
            user_sql = db.execute("SELECT  * FROM supplier WHERE s_email = ?", (email,))
            user = [dict(row) for row in user_sql.fetchall()]
            if user and check_password_hash(user[0]['password_hash'], password1):
                admin_signup=Admin(user[0]['s_id'], user[0]['s_email'])
                login_user(user=admin_signup, remember=True)
                return redirect(url_for('admin',index=user[0]['s_id']))
    return render_template("signup.html",user=current_user,common_url=common_url)

if __name__=="__main__":
    init_db()
    sockets.run(app,host=get_ip_address(),port=2003,debug=True)