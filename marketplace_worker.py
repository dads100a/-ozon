import os
import json
import time
import sqlite3

DATABASE = 'database.db'  # Путь к базе маркетплейса

while True:
    try:
        if os.path.exists('transfer_request.json'):
            with open('transfer_request.json', 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            account_id = request_data.get('account_id')
            amount = request_data.get('amount')

            # Обработка
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('SELECT id, balance FROM users WHERE user_id = ?', (account_id,))
            user = c.fetchone()
            if user:
                new_balance = user[1] + amount
                c.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user[0]))
                conn.commit()
                response = {'status': 'ok', 'new_balance': new_balance}
            else:
                response = {'status': 'error', 'message': 'Пользователь не найден'}
            conn.close()

            # Запись ответа
            with open('transfer_response.json', 'w', encoding='utf-8') as f:
                json.dump(response, f)

            # Удаление файла запроса
            os.remove('transfer_request.json')
    except Exception as e:
        print(f"Ошибка обработки файла: {e}")

    time.sleep(1)