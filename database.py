import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    
    # 1. Склад сырья
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quantity REAL NOT NULL DEFAULT 0.0
        )
    ''')
    
    # 2. Склад заготовок (добавили поле для выхода по умолчанию)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pre_mixes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quantity REAL NOT NULL DEFAULT 0.0,
            default_output REAL NOT NULL DEFAULT 1.0
        )
    ''')
    
    # 3. ТАБЛИЦА РЕЦЕПТОВ (ТЕХКАРТ)
    # Связывает id заготовки с id ингредиента и указывает расход на 1 единицу выхода
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pre_mix_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            amount_needed REAL NOT NULL,
            FOREIGN KEY (pre_mix_id) REFERENCES pre_mixes(id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
        )
    ''')
    
    # 4. История
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action_type TEXT NOT NULL, 
            target_name TEXT NOT NULL,  
            amount REAL NOT NULL
        )
    ''')
    
    # Зальем стартовую базу, если она пустая
    try:
        cursor.execute("INSERT INTO ingredients (name, quantity) VALUES ('Мята (сырье)', 1000)")
        cursor.execute("INSERT INTO ingredients (name, quantity) VALUES ('Лайм (сырье)', 2000)")
        cursor.execute("INSERT INTO ingredients (name, quantity) VALUES ('Сахарный сироп (сырье)', 3000)")
        conn.commit()
    except sqlite3.IntegrityError:
        pass
        
    conn.close()

def add_new_ingredient_to_db(name):
    """Добавляет абсолютно новую позицию сырья на склад"""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO ingredients (name, quantity) VALUES (?, 0.0)", (name,))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False # если такое имя уже есть
    conn.close()
    return success

def create_pre_mix_with_recipe(mix_name, output, ingredients_dict):
    """Создает заготовку и записывает её техкарту (рецепт) в базу
    ingredients_dict формат: {'Имя Ингредиента': количество, ...}
    """
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    try:
        # 1. Создаем саму заготовку
        cursor.execute("INSERT INTO pre_mixes (name, quantity, default_output) VALUES (?, 0.0, ?)", (mix_name, output))
        mix_id = cursor.lastrowid
        
        # 2. Привязываем ингредиенты техкарты
        for ing_name, amount in ingredients_dict.items():
            cursor.execute("SELECT id FROM ingredients WHERE name = ?", (ing_name,))
            ing_id = cursor.fetchone()[0]
            # Считаем расход на 1 единицу выхода заготовки
            rate = amount / output
            cursor.execute("INSERT INTO recipes (pre_mix_id, ingredient_id, amount_needed) VALUES (?, ?, ?)", 
                           (mix_id, ing_id, rate))
        conn.commit()
        success = True
    except Exception as e:
        print(e)
        success = False
    conn.close()
    return success

def get_stock_data():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, quantity FROM ingredients ORDER BY name")
    ingredients = cursor.fetchall()
    cursor.execute("SELECT name, quantity FROM pre_mixes ORDER BY name")
    pre_mixes = cursor.fetchall()
    cursor.execute("SELECT timestamp, action_type, target_name, amount FROM history ORDER BY id DESC LIMIT 15")
    history = cursor.fetchall()
    conn.close()
    return ingredients, pre_mixes, history

def cook_pre_mix(mix_name, amount_to_make):
    """Универсальное списание по динамической техкарте из БД!"""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    
    # Получаем id заготовки
    cursor.execute("SELECT id FROM pre_mixes WHERE name = ?", (mix_name,))
    mix_id = cursor.fetchone()[0]
    
    # Достаем её рецепт: имя ингредиента и сколько нужно на 1л/1кг продукта
    cursor.execute('''
        SELECT ingredients.name, recipes.amount_needed 
        FROM recipes 
        JOIN ingredients ON recipes.ingredient_id = ingredients.id
        WHERE recipes.pre_mix_id = ?
    ''', (mix_id,))
    recipe_items = cursor.fetchall()
    
    # Списываем пропорционально объёму приготовления
    for ing_name, rate in recipe_items:
        spend = rate * amount_to_make
        cursor.execute("UPDATE ingredients SET quantity = quantity - ? WHERE name = ?", (spend, ing_name))
        
    cursor.execute("UPDATE pre_mixes SET quantity = quantity + ? WHERE name = ?", (amount_to_make, mix_name))
    
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cursor.execute("INSERT INTO history (timestamp, action_type, target_name, amount) VALUES (?, 'COOK', ?, ?)",
                   (now, mix_name, amount_to_make))
    conn.commit()
    conn.close()

def add_ingredients(ing_name, amount_to_add):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE ingredients SET quantity = quantity + ? WHERE name = ?", (amount_to_add, ing_name))
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cursor.execute("INSERT INTO history (timestamp, action_type, target_name, amount) VALUES (?, 'INCOME', ?, ?)",
                   (now, ing_name, amount_to_add))
    conn.commit()
    conn.close()

def undo_last_action():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, action_type, target_name, amount FROM history ORDER BY id DESC LIMIT 1")
    last_log = cursor.fetchone()
    
    if last_log:
        log_id, action_type, target_name, amount = last_log
        if action_type == 'COOK':
            cursor.execute("SELECT id FROM pre_mixes WHERE name = ?", (target_name,))
            mix_id = cursor.fetchone()[0]
            cursor.execute('''
                SELECT ingredients.name, recipes.amount_needed 
                FROM recipes JOIN ingredients ON recipes.ingredient_id = ingredients.id
                WHERE recipes.pre_mix_id = ?
            ''', (mix_id,))
            recipe_items = cursor.fetchall()
            
            for ing_name, rate in recipe_items:
                spend = rate * amount
                cursor.execute("UPDATE ingredients SET quantity = quantity + ? WHERE name = ?", (spend, ing_name))
            cursor.execute("UPDATE pre_mixes SET quantity = quantity - ? WHERE name = ?", (amount, target_name))
        elif action_type == 'INCOME':
            cursor.execute("UPDATE ingredients SET quantity = quantity - ? WHERE name = ?", (amount, target_name))
            
        cursor.execute("DELETE FROM history WHERE id = ?", (log_id,))
        conn.commit()
        return True
    return False