import os
import time
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///plastic_world.db')
app.config['DEBUG'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# تعديل مسار مجلد الصور
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# التأكد من وجود المجلد
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    # إضافة العلاقة مع المنتج
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    background_image = db.Column(db.String(200), default='/static/images/default-background.jpg')
    primary_color = db.Column(db.String(20), default='#139694')
    secondary_color = db.Column(db.String(20), default='#ffffff')
    accent_color = db.Column(db.String(20), default='#ff0000')
    text_color = db.Column(db.String(20), default='#333333')
    header_text = db.Column(db.String(200), default='شركة عالم البلاستك')
    header_description = db.Column(db.String(500), default='نقدم أفضل المنتجات البلاستيكية والورقية بجودة عالية')
    # معلومات التواصل
    phone1 = db.Column(db.String(20), default='+965 1234 5678')
    phone2 = db.Column(db.String(20), default='+965 8765 4321')
    whatsapp = db.Column(db.String(20), default='+965 1234 5678')
    email = db.Column(db.String(100), default='info@example.com')
    address = db.Column(db.Text, default='الكويت - شارع ...')
    location_url = db.Column(db.String(500), default='https://goo.gl/maps/youraddress')
    facebook_url = db.Column(db.String(200), default='https://facebook.com/yourpage')
    instagram_url = db.Column(db.String(200), default='https://instagram.com/yourpage')
    twitter_url = db.Column(db.String(200), default='https://twitter.com/yourpage')
    # إضافة حقول صفحة من نحن
    about_title = db.Column(db.String(200), default='من نحن')
    about_description = db.Column(db.Text, default='شركة عالم البلاستك هي شركة رائدة في مجال توريد المنتجات البلاستيكية والورقية في الكويت')
    about_services = db.Column(db.Text, default='توريد منتجات بلاستيكية عالية الجودة\nتوفير منتجات ورقية متنوعة\nخدمة توصيل سريعة وموثوقة\nأسعار تنافسية')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    product = db.relationship('Product')
    # إضافة المجموع الكلي للمنتج
    @property
    def total(self):
        return self.quantity * self.price

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    full_name = db.Column(db.String(100))
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    total = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    items = db.relationship('OrderItem', backref='order', lazy=True)
    
    @property
    def items_list(self):
        return [{'name': item.product.name, 
                'quantity': item.quantity,
                'price': item.price} for item in self.items]

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    date_sent = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(20), default='unread')  # unread, read

# Routes
@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('عذراً، ليس لديك صلاحية الوصول إلى لوحة التحكم')
        return redirect(url_for('home'))
    return render_template('admin.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.password == request.form.get('password'):
            login_user(user)
            return redirect(url_for('home'))
        flash('خطأ في اسم المستخدم أو كلمة المرور')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    if not current_user.is_admin:
        return redirect(url_for('home'))

    if request.method == 'POST':
        if 'image' not in request.files:
            flash('لم يتم اختيار صورة')
            return redirect(request.url)

        file = request.files['image']
        if file.filename == '':
            flash('لم يتم اختيار صورة')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            try:
                # إنشاء اسم فريد للملف
                filename = secure_filename(file.filename)
                timestamp = int(time.time())
                unique_filename = f"{timestamp}_{filename}"
                # حفظ الصورة
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                # إنشاء المنتج مع المسار الصحيح للصورة
                new_product = Product(
                    name=request.form.get('name'),
                    description=request.form.get('description'),
                    price=float(request.form.get('price')),
                    image_url=f"/static/uploads/{unique_filename}"
                )
                db.session.add(new_product)
                db.session.commit()
                flash('تم إضافة المنتج بنجاح')
                return redirect(url_for('admin_products'))
            except Exception as e:
                flash(f'حدث خطأ أثناء رفع الصورة: {str(e)}')
                return redirect(request.url)

    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash('تمت إضافة المنتج إلى السلة')
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        return redirect(url_for('cart'))

    quantity = int(request.form.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
    else:
        db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        flash('تم حذف المنتج من السلة')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return redirect(url_for('cart'))
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return redirect(url_for('cart'))
    
    try:
        # إنشاء الطلب
        total = sum(item.product.price * item.quantity for item in cart_items)
        order = Order(
            user_id=current_user.id,
            full_name=request.form.get('full_name'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            total=total,
            status='pending'
        )
        db.session.add(order)
        
        # حفظ المنتجات في الطلب
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
            db.session.delete(cart_item)
        
        db.session.commit()
        flash('تم تأكيد طلبك بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تأكيد الطلب', 'error')
        print(f"Error: {str(e)}")
        
    return redirect(url_for('home'))

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

def is_valid_phone(phone):
    # تبسيط التحقق ليقبل الأرقام بشكل أسهل
    import re
    # يقبل +965 متبوعاً بـ 8 أرقام، مع أو بدون مسافة
    pattern = r'^\+965\s*\d{8}$'
    return bool(re.match(pattern, phone))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        return redirect(url_for('home'))

    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        try:
            print("Received data:", request.form)  # للتحقق من البيانات المستلمة

            # تحديث الإعدادات الأساسية
            for field in ['phone1', 'phone2', 'whatsapp', 'email', 'address', 
                         'location_url', 'facebook_url', 'instagram_url', 
                         'twitter_url', 'primary_color', 'secondary_color', 
                         'accent_color', 'text_color', 'header_text', 
                         'header_description', 'about_title', 'about_description', 
                         'about_services']:
                if field in request.form:
                    setattr(settings, field, request.form[field])

            # معالجة تحميل الصورة الخلفية
            if 'background' in request.files:
                file = request.files['background']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    timestamp = int(time.time())
                    unique_filename = f"background_{timestamp}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    settings.background_image = f"/static/uploads/{unique_filename}"

            db.session.commit()
            flash('تم حفظ الإعدادات بنجاح', 'success')
            return redirect(url_for('admin_settings'))

        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            db.session.rollback()
            flash('حدث خطأ أثناء حفظ الإعدادات', 'error')

    return render_template('admin_settings.html', settings=settings)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    orders = Order.query.order_by(Order.date_created.desc()).all()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        new_message = ContactMessage(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            message=request.form.get('message')
        )
        db.session.add(new_message)
        db.session.commit()
        flash('تم إرسال رسالتك بنجاح، سنتواصل معك قريباً')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin/messages')
@login_required
def admin_messages():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    messages = ContactMessage.query.order_by(ContactMessage.date_sent.desc()).all()
    return render_template('admin_messages.html', messages=messages)

# إضافة context processor لتوفير الإعدادات لجميع القوالب
@app.context_processor
def inject_settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    return dict(settings=settings)

@app.route('/admin/update-password', methods=['POST'])
@login_required
def update_admin_password():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    if current_user.password == current_password:
        current_user.password = new_password
        db.session.commit()
        flash('تم تحديث كلمة المرور بنجاح')
    else:
        flash('كلمة المرور الحالية غير صحيحة')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/create-user', methods=['POST'])
@login_required
def create_new_user():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'
    
    if User.query.filter_by(username=username).first():
        flash('اسم المستخدم موجود بالفعل')
    else:
        new_user = User(
            username=username,
            password=password,
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        flash('تم إنشاء المستخدم بنجاح')
    
    return redirect(url_for('admin_settings'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    order.status = data.get('status')
    db.session.commit()
    return {'success': True}

@app.route('/admin/orders/<int:order_id>/print')
@login_required
def print_order(order_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    return render_template('print_order.html', order=order)

@app.route('/admin/orders/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return {'success': True}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
