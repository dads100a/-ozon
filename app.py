from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime



import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Замените на свой секретный ключ

DATABASE = 'database.db'



 
def check_and_add_column():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Получаем список колонок в таблице
    c.execute("PRAGMA table_info(orders)")
    columns = c.fetchall()
    column_names = [col[1] for col in columns]
    if 'notification_message' not in column_names:
        try:
            c.execute('ALTER TABLE orders ADD COLUMN notification_message TEXT')
        except sqlite3.OperationalError as e:
            print(f"Ошибка при добавлении колонки: {e}")
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Создаем таблицу users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            name TEXT,
            password TEXT,
            card_number TEXT,
            balance REAL DEFAULT 0
        )
    ''')

    # Создаем таблицу products
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL,
            image_url TEXT,
            stock INTEGER DEFAULT 10,
            delivery_time TEXT,
            seller_id TEXT
        )
    ''')

    # Таблица reviews
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            name TEXT,
            text TEXT,
            datetime TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Таблица questions
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            name TEXT,
            question TEXT,
            datetime TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Таблица answers
    c.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            name TEXT,
            answer TEXT,
            datetime TEXT,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')

    # Таблица orders
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id TEXT,
            buyer_id TEXT,
            productName TEXT,
            characteristics TEXT,
            price REAL,
            status TEXT,
            quantity INTEGER DEFAULT 1,
            notification_message TEXT
        )
    ''')

    # Попытка добавить seller_id в products, если еще нет
    try:
        c.execute('ALTER TABLE products ADD COLUMN seller_id TEXT')
    except sqlite3.OperationalError:
        pass

    # Попытка добавить notification_message в orders, если еще нет
    try:
        c.execute('ALTER TABLE orders ADD COLUMN notification_message TEXT')
    except sqlite3.OperationalError:
        pass

    # Создание тестовых товаров, если таблица пустая
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        products = [
            ('Товар 1', 'Описание 1', 1000, 'static/images/product1_img1.jpg', 10, '3-5 дней', 'admin'),
            ('Товар 2', 'Описание 2', 2000, 'static/images/product2_img1.jpg', 5, '5-7 дней', 'admin')
        ]
        c.executemany(
            'INSERT INTO products (name, description, price, image_url, stock, delivery_time, seller_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            products
        )

    conn.commit()
    conn.close()





@app.route('/api/complete_order/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    if 'user_id' not in session:
        return jsonify({'status':'error', 'message':'Не авторизован'}), 401
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Проверка, что заказ существует и принадлежит продавцу
    c.execute('SELECT seller_id, status, buyer_id FROM orders WHERE id=?', (order_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'status':'error', 'message':'Заказ не найден'}), 404
    seller_id, status, buyer_id = row
    if seller_id != session['user_id']:
        conn.close()
        return jsonify({'status':'error', 'message':'Нет прав'}), 403
    if status != 'Обработка':
        conn.close()
        return jsonify({'status':'error', 'message':'Заказ уже завершен'}), 400

    # Обновляем статус заказа
    c.execute('UPDATE orders SET status="Доставлен" WHERE id=?', (order_id,))
    # Создаем сообщение для покупателя
    message = "Ваш заказ доставлен. Спасибо за покупку!"
    c.execute('UPDATE orders SET notification_message=? WHERE id=?', (message, order_id))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})


@app.route('/api/get_my_deliveries')
def get_my_deliveries():
    if 'user_id' not in session:
        return jsonify({'orders': []})
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE buyer_id=? AND status="Доставлен"', (user_id,))
    rows = c.fetchall()
    conn.close()
    orders = []
    for row in rows:
        orders.append({
            'id': row[0],
            'seller_id': row[1],
            'buyer_id': row[2],
            'product': row[3],
            'characteristics': row[4],
            'price': row[5],
            'status': row[6],
            'quantity': row[7],
            'notification_message': row[8],
        })
    return jsonify({'orders': orders})


@app.route('/api/get_sales_orders')
def get_sales_orders():
    if 'user_id' not in session:
        return jsonify({'orders': []})
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE seller_id=?', (user_id,))
    rows = c.fetchall()
    conn.close()
    orders = []
    for row in rows:
        orders.append({
            'id': row[0],
            'seller_id': row[1],
            'buyer_id': row[2],
            'productName': row[3],
            'characteristics': row[4],
            'price': row[5],
            'status': row[6],
            'quantity': row[7],
            'notification_message': row[8],
        })
    return jsonify({'orders': orders})


@app.route('/manage_orders')
def manage_orders():
    return render_template('order_management.html')

@app.route('/api/update_product/<int:product_id>', methods=['POST'])
def api_update_product(product_id):
    if 'user_id' not in session:
        return jsonify({'status':'error', 'message':'Не авторизован'}), 401

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    delivery_time = data.get('delivery_time')
    stock = data.get('stock')

    # Проверка обязательных полей
    if not all([name, description, delivery_time]) or price is None or stock is None:
        return jsonify({'status':'error', 'message':'Некорректные данные'}), 400

    try:
        price = float(price)
        stock = int(stock)
    except:
        return jsonify({'status':'error', 'message':'Некорректный формат данных'}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Проверка, что товар принадлежит текущему пользователю
    c.execute('SELECT * FROM products WHERE id=? AND seller_id=?', (product_id, session['user_id']))
    if not c.fetchone():
        conn.close()
        return jsonify({'status':'error', 'message':'Нет прав на редактирование этого товара'}), 403

    c.execute('UPDATE products SET name=?, description=?, price=?, delivery_time=?, stock=? WHERE id=?',
              (name, description, price, delivery_time, stock, product_id))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})

@app.route('/api/delete_product/<int:product_id>', methods=['POST'])
def api_delete_product(product_id):
    if 'user_id' not in session:
        return jsonify({'status':'error', 'message':'Не авторизован'}), 401

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Проверка, что товар принадлежит текущему пользователю
    c.execute('SELECT * FROM products WHERE id=? AND seller_id=?', (product_id, session['user_id']))
    if not c.fetchone():
        conn.close()
        return jsonify({'status':'error', 'message':'Нет прав на удаление этого товара'}), 403

    c.execute('DELETE FROM products WHERE id=?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})


@app.route('/api/get_product/<int:product_id>')
def get_product(product_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Не авторизован'}), 401
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM products WHERE id=?', (product_id,))
    product = c.fetchone()
    conn.close()
    if not product:
        return jsonify({'status':'error', 'message':'Товар не найден'}), 404
    return jsonify({
        'name': product[1],
        'description': product[2],
        'price': product[3],
        'image_url': product[4],  # если нужно
        'stock': product[5],
        'delivery_time': product[6]
    })


@app.route('/api/topup', methods=['POST'])
def topup():
    data = request.get_json()
    card_number = data.get('card_number')
    amount = data.get('amount')

    if not card_number or not amount:
        return jsonify({'status': 'error', 'message': 'Некорректные данные'}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('SELECT id, balance FROM users WHERE card_number = ?', (card_number,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Пользователь не найден'}), 404

    new_balance = user[1] + amount
    c.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user[0]))

    # Можно добавить логирование транзакции в таблицу, если есть

    conn.commit()
    conn.close()

    return jsonify({'status': 'ok', 'new_balance': new_balance})

@app.before_request
def auto_login():
    if 'user_id' not in session:
        user_id_cookie = request.cookies.get('user_id')
        if user_id_cookie:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE user_id = ?', (user_id_cookie,))
            user = c.fetchone()
            conn.close()
            if user:
                session['user_id'] = user[1]
                session['name'] = user[2]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['login']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE (user_id = ? OR name = ?) AND password = ?', (login_input, login_input, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[1]
            session['name'] = user[2]
            resp = redirect(url_for('main'))
            resp.set_cookie('user_id', user[1], max_age=60*60*24*30)
            return resp
        else:
            flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/api/accept_order/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    if 'user_id' not in session:
        return jsonify({'status':'error','message':'Не авторизован'})
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT seller_id, status FROM orders WHERE id=?', (order_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'status':'error','message':'Заказ не найден'})
    if row[0] != session['user_id']:
        conn.close()
        return jsonify({'status':'error','message':'Нет прав'})
    if row[1] != 'Обработка':
        conn.close()
        return jsonify({'status':'error','message':'Заказ уже обработан или доставлен'})
    c.execute('UPDATE orders SET status="Доставлен" WHERE id=?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok'})

@app.route('/api/get_order/<int:order_id>')
def get_order(order_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE id=?', (order_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'status': 'error', 'message': 'Заказ не найден'})
    return jsonify({
        'status': 'ok',
        'order': {
            'id': row[0],
            'seller_id': row[1],
            'buyer_id': row[2],
            'product': row[3],
            'characteristics': row[4],
            'price': row[5],
            'status': row[6],
            'quantity': row[7],
            'message': 'Заказ подтвержден'
        }
    })

@app.route('/api/get_incoming_orders')
def get_incoming_orders():
    if 'user_id' not in session:
        return jsonify({'orders': []})
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE buyer_id=?', (user_id,))
    rows = c.fetchall()
    conn.close()
    orders = []
    for row in rows:
        orders.append({
            'id': row[0],
            'seller_id': row[1],
            'buyer_id': row[2],
            'productName': row[3],
            'characteristics': row[4],
            'price': row[5],
            'status': row[6],
            'quantity': row[7],
            'datetime': row[3]
        })
    return jsonify({'orders': orders})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('name', None)
    return redirect(url_for('index'))

@app.route('/balance', methods=['GET', 'POST'])
def balance():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],))
    user = c.fetchone()
    if request.method == 'POST':
        action = request.form['action']
        amount_str = request.form['amount']
        if action == 'deposit':
            try:
                amount = float(amount_str)
            except:
                flash('Некорректная сумма')
                return redirect(url_for('balance'))
            new_balance = user[5] + amount
            c.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user[1]))
            conn.commit()
            flash('Баланс пополнен')
        elif action == 'withdraw':
            bank_id = request.form['bank_id'].strip()
            try:
                amount = float(amount_str)
            except:
                flash('Некорректная сумма')
                return redirect(url_for('balance'))
            if amount <= 0:
                flash('Сумма должна быть больше 0')
                return redirect(url_for('balance'))
            if user[5] < amount:
                flash('Недостаточно средств')
                return redirect(url_for('balance'))
            if not bank_id:
                flash('Введите ID банка')
                return redirect(url_for('balance'))
            # Здесь логика отправки на внешний банк
            # Например, вызов API или создание записи в базе
            new_balance = user[5] - amount
            c.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user[1]))
            conn.commit()
            flash(f'Средства {amount} руб. успешно отправлены на банк {bank_id}')
        # Обновляем текущий баланс
        c.execute('SELECT balance FROM users WHERE user_id = ?', (user[1],))
        user = list(c.fetchone()) + list(user)[2:]
    conn.close()
    return render_template('balance.html', user=user)

@app.route('/edit_product/<int:product_id>')
def edit_product(product_id):
    return render_template('edit_product.html', product_id=product_id)
@app.route('/api/order/<int:product_id>', methods=['POST'])
def api_order_create(product_id):
    if 'user_id' not in session:
        return jsonify({'status':'error', 'message':'Не авторизован'}), 401

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],))
    user = c.fetchone()  # покупатель
    c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = c.fetchone()

    if not product:
        conn.close()
        return jsonify({'status':'error', 'message':'Товар не найден'}), 404

    price = product[3]
    stock = product[5]
    seller_id = product[7]

    if stock <= 0:
        conn.close()
        return jsonify({'status':'error', 'message':'Товара нет в наличии'}), 400

    data = request.get_json()
    quantity = data.get('quantity', 1)
    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError
    except:
        conn.close()
        return jsonify({'status':'error', 'message':'Некорректное количество'}), 400

    if stock < quantity:
        conn.close()
        return jsonify({'status':'error', 'message':'Недостаточно товара'}), 400

    total_price = price * quantity

    # Проверка баланса покупателя
    if user[5] < total_price:
        conn.close()
        return jsonify({'status':'error', 'message':'Недостаточно средств'}), 400

    # Получение продавца
    c.execute('SELECT id, balance FROM users WHERE user_id = ?', (seller_id,))
    seller = c.fetchone()
    if not seller:
        conn.close()
        return jsonify({'status':'error', 'message':'Продавец не найден'}), 404

    new_balance_buyer = user[5] - total_price
    new_balance_seller = seller[1] + total_price
    new_stock = stock - quantity

    # Обновление баланса покупателя и продавца, запасов товара, создание заказа
    try:
        c.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance_buyer, user[0]))
        c.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance_seller, seller[0]))
        c.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product[0]))
        c.execute('INSERT INTO orders (seller_id, buyer_id, productName, characteristics, price, status, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (seller_id, user[1], product[1], '1', total_price, 'Обработка', quantity))
        conn.commit()
    finally:
        # Перечитываем баланс покупателя для подтверждения
        c.execute('SELECT balance FROM users WHERE id=?', (user[0],))
        updated_balance = c.fetchone()[0]
        conn.close()

    return jsonify({'status':'ok', 'message': 'Заказ оформлен и средства списаны', 'new_balance': updated_balance})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/my_products')
def my_products():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('my_products.html')

@app.route('/seller_orders')
def seller_orders():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Добавьте это для получения строк как словари
    c = conn.cursor()
    c.execute('SELECT id, buyer_id, productName, characteristics, price, status, quantity, notification_message FROM orders WHERE seller_id=?', (user_id,))
    orders = c.fetchall()
    conn.close()
    return render_template('seller_orders.html', orders=orders)

@app.route('/received_orders')
def received_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('received_orders.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        card_number = request.form['card_number']
        user_id = request.form['user_id']
        name = request.form['name']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if c.fetchone():
            flash('Этот айди уже существует')
            conn.close()
            return redirect(url_for('register'))
        c.execute('INSERT INTO users (user_id, name, password, card_number, balance) VALUES (?, ?, ?, ?, ?)', (user_id, name, password, card_number, 0))
        conn.commit()
        conn.close()
        flash('Регистрация прошла успешно! Войдите в систему.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],))
    user = c.fetchone()
    c.execute('SELECT * FROM products')
    products = c.fetchall()
    conn.close()
    return render_template('main.html', user=user, products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = c.fetchone()
    if not product:
        conn.close()
        return "Товар не найден", 404
    description = product[2]
    stock = product[5]
    delivery_time = product[6]
    seller_name = "Продавец Иван"
    images = [
        url_for('static', filename='images/product1_img1.jpg'),
        url_for('static', filename='images/product1_img2.jpg')
    ]
    c.execute('SELECT name, text, datetime FROM reviews WHERE product_id = ?', (product_id,))
    reviews_rows = c.fetchall()
    reviews = [{'name': r[0], 'text': r[1], 'datetime': r[2]} for r in reviews_rows]
    c.execute('SELECT * FROM questions WHERE product_id = ?', (product_id,))
    questions_rows = c.fetchall()
    questions = []
    for q in questions_rows:
        c.execute('SELECT * FROM answers WHERE question_id = ?', (q[0],))
        answers_rows = c.fetchall()
        answers = [{'name': a[2], 'answer': a[3], 'datetime': a[4]} for a in answers_rows]
        questions.append({'id': q[0], 'name': q[2], 'question': q[3], 'answers': answers})
    conn.close()
    return render_template('product_detail.html', product=product, images=images, description=description, stock=stock, delivery_time=delivery_time, seller_name=seller_name, reviews=reviews, questions=questions)

@app.route('/api/reviews/<int:product_id>')
def get_reviews(product_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT name, text, datetime FROM reviews WHERE product_id = ?', (product_id,))
    reviews_rows = c.fetchall()
    conn.close()
    reviews = [{'name': r[0], 'text': r[1], 'datetime': r[2]} for r in reviews_rows]
    return jsonify(reviews)

@app.route('/api/add_review/<int:product_id>', methods=['POST'])
def api_add_review(product_id):
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Не авторизован'}, 401
    data = request.get_json()
    name = data.get('name', 'Гость')
    text = data.get('text', '')
    stars = data.get('stars', 0)
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO reviews (product_id, name, text, datetime) VALUES (?, ?, ?, ?)', (product_id, name, text, now))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/ask_question/<int:product_id>', methods=['POST'])
def ask_question(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    question_text = request.form['question_text']
    name = session.get('name', 'Гость')
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO questions (product_id, name, question) VALUES (?, ?, ?)', (product_id, name, question_text))
    conn.commit()
    conn.close()
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/new_product')
def new_product():
    return render_template('create_product.html')

@app.route('/create_product', methods=['GET', 'POST'])
def create_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        delivery_time = request.form['delivery_time']
        stock = int(request.form['stock'])

        upload_folder = os.path.join('static', 'images')
        os.makedirs(upload_folder, exist_ok=True)

        # Основное изображение
        main_image = request.files['main_image']
        filename_main = f"product_{name}_{main_image.filename}"
        main_image_path = os.path.join(upload_folder, filename_main)
        main_image.save(main_image_path)
        main_image_url = url_for('static', filename='images/' + filename_main)

        # Дополнительные изображения
        additional_images = request.files.getlist('additional_images')
        images_paths = [main_image_url]
        for i, img in enumerate(additional_images[:4]):
            filename = f"product_{name}_extra_{i}_{img.filename}"
            img_path = os.path.join(upload_folder, filename)
            img.save(img_path)
            images_paths.append(url_for('static', filename='images/' + filename))

        # Вставка в базу с привязкой к продавцу
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        seller_id = session['user_id']
        c.execute(
            'INSERT INTO products (name, description, price, image_url, stock, delivery_time, seller_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, description, price, images_paths[0], stock, delivery_time, seller_id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('main'))
    return render_template('create_product.html')

@app.route('/api/admin/add_funds', methods=['POST'])
def admin_add_funds():
    if 'user_id' not in session:
        return jsonify({'status':'error', 'message':'Не авторизован'}), 401
    data = request.get_json()
    account_id = data.get('account_id')
    amount = data.get('amount')
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except:
        return jsonify({'status':'error','message':'Некорректная сумма'}), 400
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, balance FROM users WHERE user_id=?', (account_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'status':'error','message':'Пользователь не найден'}), 404
    new_balance = user[1] + amount
    c.execute('UPDATE users SET balance=? WHERE id=?', (new_balance, user[0]))
    conn.commit()
    conn.close()
    return jsonify({'status':'ok', 'new_balance': new_balance})

# ================== ВАЖНОЕ ДОПОЛНЕНИЕ ===================
# 1. Исправление функции заказа (списывать деньги и уменьшать товар)
@app.route('/api/order/<int:product_id>', methods=['POST'])
def api_create_order(product_id):
    if 'user_id' not in session:
        return jsonify({'status':'error', 'message':'Не авторизован'}), 401

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],))
    user = c.fetchone()
    c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = c.fetchone()

    if not product:
        conn.close()
        return jsonify({'status':'error', 'message':'Товар не найден'}), 404

    price = product[3]
    stock = product[5]
    seller_id = product[7]

    if stock <= 0:
        conn.close()
        return jsonify({'status':'error', 'message':'Товара нет в наличии'}), 400

    data = request.get_json()
    quantity = data.get('quantity', 1)
    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError
    except:
        conn.close()
        return jsonify({'status':'error', 'message':'Некорректное количество'}), 400

    if stock < quantity:
        conn.close()
        return jsonify({'status':'error', 'message':'Недостаточно товара'}), 400

    total_price = price * quantity

    if user[5] < total_price:
        conn.close()
        return jsonify({'status':'error', 'message':'Недостаточно средств'}), 400

    # Получаем продавца
    c.execute('SELECT id, balance FROM users WHERE user_id = ?', (seller_id,))
    seller = c.fetchone()
    if not seller:
        conn.close()
        return jsonify({'status':'error', 'message':'Продавец не найден'}), 404

    new_balance_buyer = user[5] - total_price
    new_balance_seller = seller[1] + total_price
    new_stock = stock - quantity

    # Создаем сообщение для продавца
    message_for_seller = f"У вас заказано {quantity} шт. {product[1]} на сумму {total_price} руб."

    try:
        c.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance_buyer, user[0]))
        c.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance_seller, seller[0]))
        c.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product[0]))
        c.execute('INSERT INTO orders (seller_id, buyer_id, productName, characteristics, price, status, quantity, notification_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (seller_id, user[1], product[1], '1', total_price, 'Обработка', quantity, message_for_seller))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'status':'ok', 'message': 'Заказ оформлен и средства списаны'})


# 2. Создайте маршрут для редактирования товара (чтобы редактировать и сохранять изменения)
@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_product_full(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    delivery_time = request.form['delivery_time']
    stock = int(request.form['stock'])
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Проверка, что товар принадлежит текущему пользователю
    c.execute('SELECT * FROM products WHERE id=? AND seller_id=?', (product_id, session['user_id']))
    if not c.fetchone():
        conn.close()
        return "Вы не можете редактировать этот товар", 403
    c.execute('UPDATE products SET name=?, description=?, price=?, delivery_time=?, stock=? WHERE id=?',
              (name, description, price, delivery_time, stock, product_id))
    conn.commit()
    conn.close()
    return redirect(url_for('my_products'))

# ================== КОНЕЦ ВАЖНЫХ ДОПОЛНЕНИЙ ===================

@app.route('/my-deliveries')
def my_deliveries():
    return render_template('my_deliveries.html')


@app.route('/api/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Не авторизован'}), 401
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Получаем заказ и проверяем, что он принадлежит текущему пользователю (как покупателю)
    c.execute('SELECT buyer_id FROM orders WHERE id=?', (order_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Заказ не найден'}), 404

    if row[0] != session['user_id']:
        # Тут можно разрешить удаление только если пользователь - покупатель
        # Или оставить так, чтобы удалять только свои заказы
        conn.close()
        return jsonify({'status': 'error', 'message': 'Нет прав'}), 403

    # Удаляем заказ
    c.execute('DELETE FROM orders WHERE id=?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    users = load_users()
    user = next((u for u in users if u['email'] == session['user_email']), None)
    if not user:
        flash('Пользователь не найден')
        return redirect(url_for('index'))
    if request.method == 'POST':
        amount_str = request.form['amount']
        bank_account_id = request.form['bank_account_id'].strip()

        try:
            amount = float(amount_str)
        except:
            flash('Некорректная сумма')
            return redirect(url_for('withdraw'))

        if amount <= 0:
            flash('Сумма должна быть больше 0')
            return redirect(url_for('withdraw'))

        if 'balance' not in user:
            user['balance'] = 0

        if user['balance'] < amount:
            flash('Недостаточно средств')
            return redirect(url_for('withdraw'))

        # Обновляем баланс
        user['balance'] -= amount
        # Логируем транзакцию
        user['transactions'].append({
            'amount': -amount,
            'type': 'debit',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'description': f'Вывод на счет {bank_account_id}'
        })

        save_users(users)
        flash(f'Средства успешно выведены: {amount} на счет {bank_account_id}')
        return redirect(url_for('transactions'))
    return render_template('withdraw.html')

#----------------------------------------------------
@app.route('/api/update_balance', methods=['POST'])
def update_balance():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Не авторизован'}), 401

    data = request.get_json()
    amount = data.get('amount')
    if not amount:
        return jsonify({'status': 'error', 'message': 'Некорректная сумма'}), 400
    try:
        amount = float(amount)
    except:
        return jsonify({'status': 'error', 'message': 'Некорректный формат суммы'}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Получаем текущий баланс пользователя
    c.execute('SELECT * FROM users WHERE user_id=?', (session['user_id'],))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Пользователь не найден'}), 404

    current_balance = user[5]
    if current_balance < amount:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Недостаточно средств'}), 400

    # Обновляем баланс
    new_balance = current_balance - amount
    c.execute('UPDATE users SET balance=? WHERE user_id=?', (new_balance, session['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok', 'new_balance': new_balance})


if __name__ == '__main__':
    init_db()
    check_and_add_column()
    app.run(host='0.0.0.0', port=5000, debug=True)