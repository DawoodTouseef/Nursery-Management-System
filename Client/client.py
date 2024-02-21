from werkzeug.security import  generate_password_hash,check_password_hash
from flask_socketio import SocketIO
from flask import *
from flask_wtf import FlaskForm
from flask_login import *
from wtforms import StringField, IntegerField, TextAreaField, HiddenField, SelectField
import sqlite3
from datetime import date



app=Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'mysecret'
# photos = UploadSet('photos', IMAGES)
socket = SocketIO(app)
#login Manger
login_manager = LoginManager()
login_manager.init_app(app)

DATABASE="./../plants.db"

class AddToCart(FlaskForm):
    quantity = IntegerField('Quantity')
    id = HiddenField('ID')

class Checkout(FlaskForm):
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    phone_number = StringField('Number')
    email = StringField('Email')
    address = StringField('Address')
    city = StringField('City')
    state = SelectField('State', choices=[('CA', 'California'), ('WA', 'Washington'), ('NV', 'Nevada')])
    country = SelectField('Country', choices=[('US', 'United States'), ('UK', 'United Kingdom'), ('FRA', 'France')])
    payment_type = SelectField('Payment Type',
                               choices=[('CK', 'Check'), ('WT', 'Wire Transfer'), ('UPI', 'Online Payment'),
                                        ('COD', 'Cash on Delivery')])

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



class User(UserMixin):
    def __init__(self, user_id, user_email):
        self.user_id = user_id
        self.user_email = user_email

    @staticmethod
    def get_by_id(user_id):
        db=get_db()
        user_data = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if user_data:
            return User(user_data['user_id'], user_data['user_email'])
        else:
            return None

    def get_id(self):
        return str(self.user_id)

# Define a user loader function
@login_manager.user_loader
def load_user(user_id):
    # Here, you'll load the user from your database based on the user_id
    # For demonstration purposes, let's assume your User class has a method `get_by_id`
    return User.get_by_id(user_id)
# Define route for index page
@app.route('/')
def index():
    db = get_db()
    cur = db.execute('SELECT * FROM Product')
    products = [{'id': row['p_id'], 'name': row['p_name'], 'price': row['price'], 'stock': row['stock_available'],
                 'description': row['description'], 'image': row['image']} for row in cur.fetchall()]
    db.close()
    return render_template('index.html', products=products,user=current_user)


@app.route('/product/image/<index>')
def product_image(index):
    # Assuming index is the position of the image in the list of product images
    # Retrieve the path to the image based on the index
    image_path = f"Product/{index}"  # Adjust the path based on your file naming convention
    return send_file(image_path)


# Define route for viewing a product
@app.route('/product/<int:id>')
def product(id):
    db = get_db()
    cur = db.execute('SELECT * FROM Product WHERE p_id=?',(id,))
    product = [{'id': row['p_id'], 'name': row['p_name'], 'price': row['price'], 'stock_available': row['stock_available'],
                 'description': row['description'], 'image': row['image']} for row in cur.fetchall()]

    cur=db.execute('SELECT s.s_contact, s.company_name, s.s_address FROM supplier AS s JOIN product AS p ON s.s_id = p.supplier_id WHERE p.p_id = ?;',(id,))
    supplier=[{'company_name': row['company_name'], 's_contact': row['s_contact'], 's_address': row['s_address']} for row in cur.fetchall()]

    db.close()
    form=AddToCart()

    return render_template('view-product.html', product=product[0],form=form,supplier=supplier[0],user=current_user)



@app.route('/quick-add/<id>')
def quick_add(id):
    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({'id' : id, 'quantity' : 1})
    session.modified = True

    return redirect(url_for('index'))

# Define route for adding a product to cart
@app.route('/add-to-cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({'id' : id, 'quantity' : request.form['quantity']})
    session.modified = True

    return redirect(url_for('index'))

# Define route for viewing cart
@app.route('/cart')
def cart():
    cart_items = []
    total_price = 0
    quantity_total=0
    if 'cart' in session:
        db = get_db()
        for item in session['cart']:
            cur = db.execute('SELECT * FROM Product WHERE p_id = ?', (item['id'],))
            product = cur.fetchone()
            if product:
                cart_item = {
                    'product': product,
                    'id':product['p_id'],
                    'quantity': item['quantity'],
                    'total_price': float(product['price']) * float(item['quantity'])

                }
                total_price += cart_item['total_price']
                quantity_total+=float(item['quantity'])
                cart_items.append(cart_item)
        db.close()

    grand_total_plus_shipping = total_price + 10
    return render_template('cart.html', products=cart_items, grand_total=total_price, quantity_total=quantity_total,grand_total_plus_shipping=grand_total_plus_shipping,user=current_user)

@app.route('/remove-from-cart/<int:id>')
def remove_from_cart(id):
    del session['cart'][int(id)]
    session.modified = True
    return redirect(url_for('cart'))

def handle_cart():
    cart_items = []
    total_price = 0
    quantity_total = 0
    grand_total = 0
    db = get_db()
    for item in session['cart']:
        cur = db.execute('SELECT * FROM Product WHERE p_id = ?', (item['id'],))
        product = cur.fetchone()
        if product:
            cart_item = {
                'product': product,
                'id': product['p_id'],
                'quantity': item['quantity'],
                'total_price': float(product['price']) * float(item['quantity'])

            }
            total = float(product['price']) * float(item['quantity'])
            grand_total += total
            total_price += cart_item['total_price']
            quantity_total += float(item['quantity'])
            cart_items.append(cart_item)
    db.close()
    grand_total_plus_shipping = total_price + 1000

    return cart_items, grand_total, grand_total_plus_shipping, quantity_total

# Define route for checkout
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    import random
    form = Checkout()

    products, grand_total, grand_total_plus_shipping, quantity_total = handle_cart()
    if form.validate_on_submit():
        db = get_db()

        user_id = current_user.user_id

        # Insert order items into order_item table
        for product in products:
            db.execute("INSERT INTO order_item ( p_id, u_id, quantity) VALUES ( ?, ?, ?);", (product['id'], user_id, product['quantity']))

            # Update product stock
            db.execute("UPDATE Product SET stock_available = stock_available - ? WHERE p_id = ?;", (product['quantity'], product['id']))
        reference = ''.join([random.choice('ABCDE') for _ in range(5)])
        # Insert order into Orders table
        db.execute("INSERT INTO Orders (reference,p_id, u_id, order_date, Delivery_date, status, total_amt, PaymentType,First_Name,last_Name,country,state,city,u_contact,u_address,user_email) VALUES (?,?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?);",
                   (reference,products[0]['id'], user_id, date.today(), None, 'PENDING', grand_total, form.payment_type.data,form.first_name.data,form.last_name.data,form.country.data,form.state.data,form.city.data,form.phone_number.data,form.address.data,form.email.data))
        db.commit()

        session['cart'] = []
        session.modified = True

        return redirect(url_for('index'))

    return render_template('checkout.html',user=current_user, form=form, grand_total=grand_total, grand_total_plus_shipping=grand_total_plus_shipping, quantity_total=quantity_total)

@app.route('/user_logout')
@login_required
def luser_ogout():
    logout_user()
    return redirect(url_for('user_login'))

@app.route('/user_login',methods=['GET','POST'])
def user_login():
    db = get_db()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Retrieve user information from the database
        user_sql = db.execute("SELECT  * FROM users WHERE user_email = ?", (email,))
        user = [dict(row) for row in user_sql.fetchall()]
        if user and check_password_hash(user[0]['password_hash'], password):
            flash('Logged in successfully!', category='success')
            login_user(User(user[0]['user_id'], user[0]['user_email']), remember=True)
            return redirect(url_for('index'))
        else:
            # Invalid credentials
            flash('Invalid email or password. Please try again.', 'error')  # Error message

    return render_template('login.html',user=current_user)


@app.route("/users_signup",methods=['GET','POST'])
def users_signup():
    db=get_db()
    if request.method=="POST":
        firstName=request.form.get('firstName')
        lastName=request.form.get('lastName')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        email_exits_sql = db.execute("SELECT  * FROM users WHERE user_email = ?", (email,))
        email_exits = [dict(row) for row in email_exits_sql.fetchall()]
        if email_exits:
            flash('Email already exists.', category='error')
            print("Email already exists.")
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(firstName) < 2:
            flash('First Name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            db.execute('INSERT INTO users(First_Name,last_Name,user_email,password_hash) VALUES(?,?,?,?)',
                       (firstName,lastName,email,generate_password_hash(password1,method='scrypt')))
            db.commit()
            user_sql = db.execute("SELECT  * FROM users WHERE user_email = ?", (email,))
            user = [dict(row) for row in user_sql.fetchall()]
            if user and check_password_hash(user[0]['password_hash'], password1):
                login_user(User(user[0]['user_id'], user[0]['user_email']), remember=True)
                return redirect(url_for('index'))
    return render_template("signup.html",user=current_user)


if __name__=="__main__":
    init_db()
    socket.run(app,host="0.0.0.0",port=2802,debug=True)