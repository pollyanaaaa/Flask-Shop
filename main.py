import os
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session
from sqlalchemy import or_
from flask_paginate import Pagination, get_page_args
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.future import engine
from werkzeug.utils import secure_filename
from flask import session, flash
from functools import wraps
from models import app, db, User, Product, Category, Brand, Basket, History, engine, Image
from flask import request, jsonify, render_template, send_file
from sqlalchemy.orm import Session
import hashlib

@app.route('/', methods=['POST', 'GET'])
def start():
    return redirect(url_for('login'))


""" Декоратор ^_^ """


def allow(permissions):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if session['role'] not in permissions:
                return "Нет прав доступа!"
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        new_user = User(login=request.form['login'], password=hashlib.md5(request.form['password'].encode()).hexdigest(), role=request.form['role'])
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect('/login')
        except:
            return render_template("registration.html", error='Не удалось зарегистрировать пользователя')
    else:
        return render_template("registration.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(login=request.form['login'], password=hashlib.md5(request.form['password'].encode()).hexdigest()).first()
        if user:
            session['user_id'] = user.user_id
            session['role'] = user.role
            return redirect('/products')
        return render_template("login.html", error='Неверное имя пользователя или пароль')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/user/add', methods=['POST', 'GET'])
def add_user():
    if request.method == 'POST':
        new_user = User(login=request.form['login'], password=hashlib.md5(request.form['password'].encode()).hexdigest(), role=request.form['role'])
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect('/users')
        except:
            return render_template("add_user.html", error='Не удалось зарегистрировать пользователя')
    else:
        return render_template("add_user.html")


@app.route('/users', methods=['POST', 'GET'])
def get_all_users():
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    query = User.query.order_by(User.user_id)
    users = query.paginate(page=page, per_page=3)
    pagination = Pagination(page=page, per_page=3, total=users.total, record_name='users',
                            format_total=True, format_number=True, inner_window=1)
    return render_template("users.html", users=users, pagination=pagination)


@app.route('/users/<int:id>/put', methods=['POST', 'GET'])
def put_user(id):
    user = User.query.get(id)

    if request.method == 'POST':
        try:
            user.login = request.form['login']
            user.password = hashlib.md5(request.form['password'].encode()).hexdigest()
            user.role = request.form['role']
            db.session.add(user)
            db.session.commit()
            return redirect('/users')
        except:
                return render_template("put_user.html", error='Ошибка при обновлении данных')
    else:
        return render_template("put_user.html", user=user)


@app.route('/users/<int:user_id>/delete')
def delete_user(user_id):
    with Session(autoflush=False, bind=engine) as table:
        try:
            user = table.query(User).filter(User.user_id == user_id).one()
            table.delete(user)
            table.commit()
            return redirect('/users')
        except:
            return "При удалении пользователя произошла ошибка"


@app.route('/products/<int:product_id>/basket_add', methods=['POST', 'GET'])
def add_to_basket(product_id):
            with Session(autoflush=False, bind=engine) as table:
                try:
                    user_id = session['user_id']
                    new_pos = Basket(user_id=user_id, product_id=product_id)
                    table.add(new_pos)
                    table.commit()
                    return redirect('/basket')
                except:
                    return "При добавлении товара в корзину произошла ошибка"


@app.route('/basket/<int:pr_id>/delete')
def delete_product_in_basket(pr_id):
    user = session['user_id']
    with Session(autoflush=False, bind=engine) as table:
        basket = table.query(Basket).filter(Basket.user_id == user).filter(Basket.product_id == pr_id).one()
        table.delete(basket)
        table.commit()
        return redirect('/basket')

@app.route('/basket')
def basket():
    user_id = session.get('user_id')
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')

    query = Basket.query.filter(Basket.user_id == user_id)
    basket_items = query.paginate(page=page, per_page=3)
    products = Product.query.all()
    pictures = Image.query.all()
    pagination = Pagination(page=page, per_page=3, total=basket_items.total, record_name='basket_items',
                            format_total=True, format_number=True, inner_window=1)
    return render_template('basket.html', basket_items=basket_items, names=products, pictures=pictures, pagination=pagination)

@app.route('/buy_all', methods=['POST', 'GET'])
def buy_all():
    user_id = session.get('user_id')
    try:
        with Session(autoflush=False, bind=engine) as table:
            basket_items = table.query(Basket).filter(Basket.user_id == user_id).all()
            for item in basket_items:
                history_item = History(user_id=item.user_id, product_id=item.product_id)
                table.add(history_item)
                table.delete(item)
            table.commit()
            return redirect('/history')
    except:
        return "При покупке товаров произошла ошибка"


@app.route('/buy_one/<int:pr_id>', methods=['POST', 'GET'])
def buy_one(pr_id):
    user_id = session.get('user_id')
    try:
        with Session(autoflush=False, bind=engine) as table:
            basket_item = table.query(Basket).filter(Basket.user_id == user_id).filter(Basket.product_id == pr_id).one()
            history_item = History(user_id=user_id, product_id=pr_id)
            table.add(history_item)
            table.delete(basket_item)
            table.commit()
            return redirect('/history')
    except:
        return "При покупке товаров произошла ошибка"

@app.route('/history')
def history():
    user_id = session.get('user_id')
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')

    query = History.query.filter(History.user_id == user_id)
    history_items = query.paginate(page=page, per_page=3)
    products = Product.query.all()
    pictures = Image.query.all()
    pagination = Pagination(page=page, per_page=3, total=history_items.total, record_name='basket_items',
                            format_total=True, format_number=True, inner_window=1)
    return render_template('history.html', history_items=history_items, names=products, pictures=pictures, pagination=pagination)
@app.route('/categories/add', methods=['POST', 'GET'])
def add_category():
    if request.method == 'POST':
        with Session(autoflush=False, bind=engine) as table:
            new_category = Category(name=request.form['name'])
            try:
                table.add(new_category)
                table.commit()
                return redirect('/categories')
            except IntegrityError:
                return render_template("add_category.html", error='Категория уже существует!')
    else:
        return render_template("add_category.html")


@app.route('/categories/<int:cat_id>/delete')
def delete_category(cat_id):
    with Session(autoflush=False, bind=engine) as table:
        try:
            category = table.query(Category).filter(Category.category_id == cat_id).one()
            products = table.query(Product).filter(Product.category == category.category_id).all()
            products_id = []
            images_id = []
            for i in products:
                products_id.append(i.product_id)
            for pr in products_id:
                images = table.query(Image).filter(Image.product_id == pr).all()
                for j in images:
                    images_id.append(j.image_id)
                for img in images_id:
                    delete_image(img)
                delete_product(pr)
                pass
            table.delete(category)
            table.commit()
            return redirect('/categories')
        except:
            return "При удалении категории произошла ошибка"


@app.route('/categories/<int:cat_id>/put', methods=['POST', 'GET'])
def put_category(cat_id):
    tek_category = Category.query.get(cat_id)
    if request.method == 'POST':
        with Session(autoflush=False, bind=engine) as table:
            try:
                category = table.query(Category).filter(Category.category_id == cat_id).one()
                category.name = request.form["name"]
                table.commit()
                return redirect('/categories')
            except IntegrityError:
                return render_template("put_category.html", error='Категория уже существует!')
            except:
                return "При редактировании категории произошла ошибка"
    else:
        return render_template("put_category.html", category=tek_category)


@app.route('/categories')
def get_all_categories():
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    query = Category.query.order_by(Category.category_id)
    categories = query.paginate(page=page, per_page=3)
    pagination = Pagination(page=page, per_page=3, total=categories.total, record_name='categories',
                            format_total=True, format_number=True, inner_window=1)
    return render_template("categories.html", categories=categories, pagination=pagination)


@app.route('/brands/add', methods=['POST', 'GET'])
def add_brand():
    if request.method == 'POST':
        with Session(autoflush=False, bind=engine) as table:
            new_brand = Brand(name=request.form['name'])
            try:
                table.add(new_brand)
                table.commit()
                return redirect('/brands')
            except IntegrityError:
                return render_template("add_brand.html", error='Бренд уже существует!')
            except:
                return "Ошибка в добавлении бренда!"
    else:
        return render_template("add_brand.html")


@app.route('/brands/<int:br_id>/delete')
def delete_brand(br_id):
    with Session(autoflush=False, bind=engine) as table:
        try:
            brand = table.query(Brand).filter(Brand.brand_id == br_id).one()
            products = table.query(Product).filter(Product.brand == brand.brand_id).all()
            products_id = []
            images_id = []
            for i in products:
                products_id.append(i.product_id)
            for pr in products_id:
                images = table.query(Image).filter(Image.product_id == pr).all()
                for j in images:
                    images_id.append(j.image_id)
                for img in images_id:
                    delete_image(img)
                delete_product(pr)
                pass
            table.delete(brand)
            table.commit()
            return redirect('/brands')
        except:
            return "При удалении бренда произошла ошибка"


@app.route('/brands/<int:br_id>/put', methods=['POST', 'GET'])
def put_brand(br_id):
    tek_brand = Brand.query.get(br_id)
    if request.method == 'POST':
        with Session(autoflush=False, bind=engine) as table:
            try:
                brand = table.query(Brand).filter(Brand.brand_id == br_id).one()
                brand.name = request.form['name']
                table.commit()
                return redirect('/brands')
            except IntegrityError:
                return render_template("put_brand.html", error='Бренд уже существует!')
            except:
                return "При редактировании бренда произошла ошибка"
    else:
        return render_template("put_brand.html", brand=tek_brand)


@app.route('/brands')
def get_all_brands():
    page, per_page, offset = get_page_args()
    query = Brand.query.order_by(Brand.brand_id)
    brands = query.paginate(page=page, per_page=3)
    pagination = Pagination(page=page, per_page=3, total=brands.total, record_name='brands',
                            format_total=True, format_number=True, inner_window=1)
    return render_template("brands.html", brands=brands, pagination=pagination)


@app.route('/products/add', methods=['POST', 'GET'])
def add_product():
    categories = Category.query.order_by(Category.category_id.desc())
    brands = Brand.query.order_by(Brand.brand_id.desc())
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        brand = request.form['brand']

        if request.files.getlist('image[]'):
            images = request.files.getlist('image[]')
            pictures = []
            item = Product(name=name, category=category, brand=brand)
            db.session.add(item)
            db.session.commit()
            for image in images:
                if image:
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    picture = Image(image_name=filename, product_id=item.product_id)
                    db.session.add(picture)
                    db.session.commit()
                    pictures.append(picture)

            item.images.extend(pictures)
        else:
            pictures = []
            product = Product(name=name, category=category, brand=brand)
            db.session.add(product)
            db.session.commit()
        return redirect('/products')


    else:
        return render_template("add_product.html", categories=categories, brands=brands)


@app.route('/products')
def products():
    page, per_page, offset = get_page_args()
    per_page = 3
    search = request.args.get('search'.lower(), type=str, default='')
    query = Product.query.order_by(Product.product_id.desc())

    if search:
        query = query.filter(or_(Product.name.contains(search)))

    products = query.paginate(page=page, per_page=per_page)
    pictures = Image.query.all()
    cats = Category.query.all()
    brands = Brand.query.all()
    pagination = Pagination(page=page, per_page=per_page, total=products.total, record_name='products',
                            format_total=True, format_number=True, inner_window=1)

    return render_template("products.html", products=products, pagination=pagination, search=search, pictures=pictures, cats=cats, brands=brands)


@app.route('/products/<int:pr_id>/delete')
def delete_product(pr_id):
    with Session(autoflush=False, bind=engine) as table:
        try:
            product = table.query(Product).filter(Product.product_id == pr_id).one()
            table.delete(product)
            table.commit()
            return redirect('/products')
        except:
            return "При удалении товара произошла ошибка"


def del_product(pr_id):
    with Session(autoflush=False, bind=engine) as table:
        try:
            product = table.query(Product).filter(Product.product_id == pr_id).one()
            table.delete(product)
            table.commit()
        except:
            return "При удалении товара произошла ошибка"


@app.route('/products/<int:id>/post', methods=['POST', 'GET'])
def put_product(id):
    product = Product.query.get(id)
    categories = Category.query.order_by(Category.category_id.desc())
    brands = Brand.query.order_by(Brand.brand_id.desc())

    if request.method == 'POST':
        product.name = request.form['name']
        product.category = request.form['category']
        product.brand = request.form['brand']
        db.session.add(product)
        db.session.commit()
        try:
            # Обновление изображений товара
            if request.files.getlist('image'):
                images = request.files.getlist('image')
                pics = []

                for image in images:
                    if image:
                        filename = secure_filename(image.filename)
                        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        picture = Image(image_name=filename, product=product)
                        db.session.add(picture)
                        pics.append(picture)

                product.images.extend(pics)
                db.session.commit()

            return redirect('/products')
        except:
            return "При редактировании товара произошла ошибка"
    else:
        return render_template("put_product.html", product=product, categories=categories, brands=brands)


@app.route('/posts/<int:pr_id>/upd/<int:img_id>/del')
def picture_in_post_delete(pr_id, img_id):
    with Session(autoflush=False, bind=engine) as table:
        try:
            image = table.query(Image).filter(Image.product_id == pr_id).filter(Image.image_id == img_id).one()
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.image_name))
            table.delete(image)
            table.commit()
            return redirect(url_for('post_update', id=pr_id))
        except NoResultFound:
            return 'Картинка не найдена'


@app.route('/posts/<int:pr_id>/upd/<int:img_id>/del')
def delete_image(img_id):
    with Session(autoflush=False, bind=engine) as table:
        try:
            image = table.query(Image).filter(Image.image_id == img_id).one()
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.image_name))
            table.delete(image)
            table.commit()
        except NoResultFound:
            return 'Картинка не найдена'


@app.route('/posts/<int:id>/upd/new_pictures', methods=['GET', 'POST'])
def add_new_pictures(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        if product:
            if request.files.getlist('image'):
                images = request.files.getlist('image')
                pictures = []
                try:
                    for image in images:
                        if image:
                            filename = secure_filename(image.filename)
                            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            picture = Image(image_name=filename, product=product)
                            db.session.add(picture)
                            db.session.commit()
                            pictures.append(picture)

                    product.images.extend(pictures)
                    db.session.commit()

                    return redirect(url_for('post_update', id=id))
                except:
                    return 'Изображения не найдены в запросе'

    return render_template("put_images.html", product=product)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
