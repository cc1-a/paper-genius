import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, g, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from flask_migrate import Migrate
import cloudinary
import cloudinary.uploader
import cloudinary.api
from sqlalchemy import or_

from functions import calculate_total_price
from auth import authenticate
from ai_routes import ai_bp
from models import db, items, users, cart, orders
from wa_api import send_admin_order_alert, send_customer_order_confirmation, send_contact_message

load_dotenv()

app = Flask(__name__)
app.register_blueprint(ai_bp)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')

db.init_app(app)
migrate = Migrate(app, db)

cloudinary.config(secure=True)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('is_admin') is not True:
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(users, user_id)

@app.route('/robots.txt')
def robots():
    response = make_response("User-agent: *\nAllow: /\n\nSitemap: https://papergenius.vercel.app/sitemap.xml")
    response.headers["Content-Type"] = "text/plain"
    return response

@app.route('/sitemap.xml')
def sitemap():
    try:
        base_url = "https://papergenius.vercel.app"
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        static_pages = [
            {"loc": f"{base_url}/", "pri": "1.0"},
            {"loc": f"{base_url}/Shop", "pri": "0.9"},
            {"loc": f"{base_url}/About", "pri": "0.8"},
            {"loc": f"{base_url}/Contact", "pri": "0.7"}
        ]
        for page in static_pages:
            xml_content += f"<url><loc>{page['loc']}</loc><priority>{page['pri']}</priority></url>"
        
        try:
            all_shop_items = items.query.all()
            for item in all_shop_items:
                xml_content += f"<url><loc>{base_url}/Product/{item.id}</loc><priority>0.8</priority></url>"
        except:
            pass
            
        xml_content += '</urlset>'
        response = make_response(xml_content.strip())
        response.headers["Content-Type"] = "application/xml; charset=utf-8"
        return response
    except Exception as e:
        return make_response(str(e), 500)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/Login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('Email')
        password = request.form.get('Password')
        error = None
        user_check = users.query.filter_by(email=email).first()
        if user_check is None or not check_password_hash(user_check.password, password):
            error = "Invalid email or password."
        if error is None:
            session['user_id'] = user_check.id
            return redirect(url_for('home'))
        return render_template("log_in.html", error=error)
    return render_template("log_in.html")

@app.route("/Logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/Register", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        name = request.form.get('Name')
        password = request.form.get('Password')
        email = request.form.get('Email')
        school = request.form.get('School')
        level = request.form.get('level')
        number = request.form.get('phone_number')
        address = request.form.get('address')
        town = request.form.get('town')
        existing_user = users.query.filter_by(email=email).first()
        if existing_user:
            return render_template("sign_up.html", error="Email already registered")
        hashed_pw = generate_password_hash(password)
        new_user = users(name=name, password=hashed_pw, email=email, school=school, level=level, number=number, address=address, town=town)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("sign_up.html")

@app.route("/Profile", methods=["GET", "POST"])
def profile():
    if g.user is None: return redirect(url_for('login'))
    if request.method == "POST":
        g.user.name = request.form.get('name')
        g.user.number = request.form.get('number')
        g.user.school = request.form.get('school')
        g.user.address = request.form.get('address')
        g.user.town = request.form.get('town')
        new_pass = request.form.get('new_password')
        if new_pass:
            g.user.password = generate_password_hash(new_pass)
        try:
            db.session.commit()
            return render_template("profile.html", success="Profile Updated Successfully!")
        except Exception:
            db.session.rollback()
            return render_template("profile.html", error="Update Failed.")
    return render_template("profile.html")

@app.route("/MyOrders")
def my_orders():
    if g.user is None: return redirect(url_for('login'))
    user_orders = orders.query.filter_by(user_id=g.user.id).order_by(orders.order_date.desc()).all()
    return render_template("my_orders.html", orders=user_orders)

@app.route("/Shop", methods=["POST", "GET"])
def shop():
    all_items = items.query.all()
    if request.method == "POST":
        if g.user is None: return redirect(url_for('login'))
        item_id = request.form.get('item_id')
        design_type = request.form.get('cover_type')
        start_year = request.form.get('selected_year_from')
        end_year = request.form.get('selected_year_to')
        item_obj = db.session.get(items, int(item_id))
        if item_obj and item_obj.years_available:
            years_list = sorted(list(item_obj.years_available.keys()))
            try:
                s_idx = years_list.index(start_year)
                e_idx = years_list.index(end_year)
                if s_idx > e_idx: s_idx, e_idx = e_idx, s_idx
                selected_years = years_list[s_idx : e_idx+1]
                price = calculate_total_price(item_obj, design_type, selected_years)
                new_cart = cart(
                    user_id=g.user.id, original_item_id=item_obj.id, name=item_obj.name,
                    img=item_obj.img, years_available=item_obj.years_available,
                    selected_years=selected_years, design_type=design_type, price=price
                )
                db.session.add(new_cart)
                db.session.commit()
                return redirect(url_for('carts'))
            except ValueError:
                return redirect(url_for('shop'))
    return render_template("shop.html", items=all_items)

@app.route("/Cart")
def carts():
    if g.user is None: return redirect(url_for('login'))
    user_carts = cart.query.filter_by(user_id=g.user.id).all()
    return render_template("cart.html", cart=user_carts)

@app.route("/Cart/Edit/<int:cart_id>", methods=["GET", "POST"])
def edit_cart_item(cart_id):
    if g.user is None: return redirect(url_for('login'))
    cart_item = db.session.get(cart, cart_id)
    if not cart_item or cart_item.user_id != g.user.id:
        return redirect(url_for('carts'))
    if request.method == "POST":
        design_type = request.form.get('cover_type')
        start_year = request.form.get('selected_year_from')
        end_year = request.form.get('selected_year_to')
        item_obj = db.session.get(items, cart_item.original_item_id)
        if item_obj:
            years_list = sorted(list(item_obj.years_available.keys()))
            try:
                s_idx = years_list.index(start_year)
                e_idx = years_list.index(end_year)
                if s_idx > e_idx: s_idx, e_idx = e_idx, s_idx
                selected_years = years_list[s_idx : e_idx+1]
                cart_item.design_type = design_type
                cart_item.selected_years = selected_years
                cart_item.price = calculate_total_price(item_obj, design_type, selected_years)
                db.session.commit()
                return redirect(url_for('carts'))
            except Exception:
                pass
    return render_template("edit_cart.html", cart_item=cart_item)

@app.route("/Cart/Delete/<int:cart_id>")
def delete_cart_item(cart_id):
    if g.user is None: return redirect(url_for('login'))
    cart_item = db.session.get(cart, cart_id)
    if cart_item and cart_item.user_id == g.user.id:
        db.session.delete(cart_item)
        db.session.commit()
    return redirect(url_for('carts'))

@app.route("/Checkout", methods=["POST"])
def checkout():
    if g.user is None: return redirect(url_for('login'))
    selected_ids = request.form.getlist('selected_cart_ids')
    user_comments = request.form.get('user_comments', '')
    if not selected_ids: return redirect(url_for('carts'))
    cart_items = cart.query.filter(cart.user_id == g.user.id, cart.id.in_(selected_ids)).all()
    if not cart_items: return redirect(url_for('carts'))
    total_price = sum(item.price for item in cart_items if item.price)
    items_summary = [f"{item.name} [{item.design_type}] ({item.selected_years[0]}-{item.selected_years[-1]})" for item in cart_items]
    items_text = ", ".join(items_summary)
    new_order = orders(
        user_id=g.user.id, customer_name=g.user.name, contact_number=g.user.number,
        order_items=items_text, total_price=total_price, status="Pending", additional_info=user_comments
    )
    try:
        db.session.add(new_order)
        db.session.commit()
        send_admin_order_alert(new_order.id, g.user.name, g.user.number, cart_items, total_price, user_comments)
        send_customer_order_confirmation(g.user.number, cart_items, total_price)
        for item in cart_items: db.session.delete(item)
        db.session.commit()
        return render_template("index.html", order_success=True, order_id=new_order.id, total_price=total_price)
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('carts'))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username_input = request.form.get('username')
        password_input = request.form.get('password')
        user = users.query.filter((users.email == username_input) | (users.name == username_input)).first()
        if user:
            if check_password_hash(user.password, password_input):
                if user.level == "Admin":
                    session['is_admin'] = True
                    session['user_id'] = user.id
                    return redirect(url_for('admin_dashboard'))
                else:
                    return render_template('/admin/admin.html', error="Access Denied.")
        authenticated, is_admin = authenticate(username_input, password_input)
        if authenticated and is_admin:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('/admin/admin.html', error="Invalid credentials.")
    return render_template('/admin/admin.html')

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    all_items = items.query.all()
    return render_template('/admin/admin_dashboard.html', items=all_items)

@app.route("/admin/users")
@admin_required
def admin_users():
    all_users = users.query.all()
    return render_template('/admin/users.html', users=all_users)

@app.route("/admin/orders")
@admin_required
def admin_orders():
    all_orders = orders.query.order_by(orders.order_date.desc()).all()
    return render_template('/admin/orders.html', orders=all_orders)

@app.route("/admin/update_order/<int:order_id>", methods=["POST"])
@admin_required
def update_order_status(order_id):
    order = db.session.get(orders, order_id)
    if order:
        new_status = request.form.get('status')
        if new_status:
            order.status = new_status
            db.session.commit()
    return redirect(url_for('admin_orders'))

@app.route("/admin/delete_item/<int:item_id>", methods=["POST"])
@admin_required
def delete_item(item_id):
    item_to_delete = db.session.get(items, item_id)
    if item_to_delete:
        db.session.delete(item_to_delete)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    user_to_delete = db.session.get(users, user_id)
    if user_to_delete:
        cart.query.filter(cart.user_id == user_id).delete()
        db.session.delete(user_to_delete)
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/admin/add_item", methods=["GET", "POST"])
@admin_required
def add_item():
    if request.method == "POST":
        item_name = request.form.get('item_name')
        img_url = ""
        file = request.files.get('img_file')
        if file:
            try:
                upload_result = cloudinary.uploader.upload(file)
                img_url = upload_result['secure_url']
            except Exception as e:
                img_url = request.form.get('img_url') 
        else:
            img_url = request.form.get('img_url')
        year_months = request.form.getlist('year_month[]')
        page_counts = request.form.getlist('page_count[]')
        years_available = {}
        for year, pages in zip(year_months, page_counts):
            if year.strip() and pages.isdigit():
                years_available[year.strip()] = int(pages)
        if item_name and img_url and years_available:
            new_item = items(name=item_name, img=img_url, years_available=years_available)
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
    return render_template('/admin/add_item.html')

@app.route("/admin/reset_password/<int:user_id>", methods=["POST"])
@admin_required
def reset_user_password(user_id):
    user = db.session.get(users, user_id)
    new_password = request.form.get('new_password')
    if user and new_password:
        user.password = generate_password_hash(new_password)
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.route("/admin/edit_item/<int:item_id>", methods=["GET", "POST"])
@admin_required
def edit_item(item_id):
    item = db.session.get(items, item_id)
    if not item: return redirect(url_for('admin_dashboard'))
    if request.method == "POST":
        item.name = request.form.get('item_name')
        item.img = request.form.get('img_url')
        year_months = request.form.getlist('year_month[]')
        page_counts = request.form.getlist('page_count[]')
        updated_years = {}
        for year, pages in zip(year_months, page_counts):
            if year.strip() and pages.isdigit():
                updated_years[year.strip()] = int(pages)
        if updated_years: item.years_available = updated_years
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    years_list = list(item.years_available.items())
    return render_template('/admin/edit_item.html', item=item, years_list=years_list)

@app.route("/About")
def about(): return render_template("about.html")

@app.route("/Contact", methods=["GET", "POST"])
def contact():
    success = False
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        send_contact_message(name, email, subject, message)
        success = True
    return render_template("contact.html", success=success)

@app.route("/Product/<int:item_id>")
def product_detail(item_id):
    item_obj = db.session.get(items, item_id)
    if not item_obj:
        return redirect(url_for('shop'))
    return render_template("product_detail.html", item=item_obj)

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
