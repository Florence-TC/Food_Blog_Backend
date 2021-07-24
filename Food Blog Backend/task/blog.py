import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('db_name')
parser.add_argument('--ingredients')
parser.add_argument('--meals')

args = parser.parse_args()

conn = sqlite3.connect(args.db_name)
cur = conn.cursor()

cur.execute('PRAGMA foreign_keys = ON;')

cur.execute('''CREATE TABLE IF NOT EXISTS meals (
                    meal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meal_name TEXT NOT NULL UNIQUE);
            ''')
cur.execute('''CREATE TABLE IF NOT EXISTS ingredients (
                    ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ingredient_name TEXT NOT NULL UNIQUE);
            ''')
cur.execute('''CREATE TABLE IF NOT EXISTS measures (
                    measure_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    measure_name TEXT UNIQUE);
            ''')
cur.execute('''CREATE TABLE IF NOT EXISTS recipes (
                    recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_name TEXT NOT NULL,
                    recipe_description TEXT);
            ''')
cur.execute('''CREATE TABLE IF NOT EXISTS serve (
                    serve_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meal_id INTEGER NOT NULL,
                    recipe_id INTEGER NOT NULL,
                    FOREIGN KEY(meal_id) REFERENCES meals(meal_id),
                    FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id));
            ''')
cur.execute('''CREATE TABLE IF NOT EXISTS quantity (
                    quantity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quantity INTEGER NOT NULL,
                    recipe_id INTEGER NOT NULL,
                    measure_id INTEGER NOT NULL,
                    ingredient_id INTEGER NOT NULL,
                    FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
                    FOREIGN KEY(measure_id) REFERENCES measures(measure_id),
                    FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id));
            ''')
conn.commit()

data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
        "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
        "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}


def populate_table():
    for table in data:
        for item in data[table]:
            cur.execute(f"INSERT INTO {table} ('{table[:-1]}_name') VALUES ('{item}');")
    conn.commit()


def add_recipe():
    while True:
        print("Pass the empty recipe name to exit.")
        recipe_name = input("Recipe name:")
        if recipe_name != "":
            recipe_description = input("Recipe description:")
            last_recipe_id = cur.execute(f'''INSERT INTO recipes ('recipe_name', 'recipe_description')
                            VALUES ('{recipe_name}', '{recipe_description}');''').lastrowid
            conn.commit()
            available_meals = cur.execute(f'SELECT * FROM meals;').fetchall()
            for meal in available_meals:
                print(f'{meal[0]}) {meal[1]}', sep=" ", end=" ")
            print()
            meal_list = input('Enter proposed meals separated by a space: ').split()
            for meal in meal_list:
                cur.execute(f'''INSERT INTO serve ('meal_id', 'recipe_id')
                            VALUES ('{meal[0]}', '{last_recipe_id}')
                            ''')
                conn.commit()
            add_ingredients(last_recipe_id)
        else:
            conn.close()
            break


def add_ingredients(last_recipe):
    while True:
        ingredient_name = input('Input quantity of ingredient <press enter to stop>: ')
        if ingredient_name == '':
            break
        else:
            if len(ingredient_name.split()) == 3:
                (quantity, measure, ingredient) = ingredient_name.split()
                measure_tuple = cur.execute(f'''SELECT * FROM measures
                                WHERE measure_name LIKE '{measure}%';
                            ''').fetchall()
                ingredient_tuple = cur.execute(f'''SELECT * FROM ingredients
                                WHERE ingredient_name LIKE '%{ingredient}%';
                            ''').fetchall()
                if len(measure_tuple) > 1 or len(ingredient_tuple) > 1:
                    print('The measure is not conclusive!')
                else:
                    cur.execute(f'''INSERT INTO quantity ('quantity', 'recipe_id', 'measure_id', 'ingredient_id')
                                    VALUES (
                                    '{quantity}',
                                    '{last_recipe}',
                                    '{measure_tuple[0][0]}',
                                    '{ingredient_tuple[0][0]}');
                                ''')
                    conn.commit()

            elif len(ingredient_name.split()) == 2:
                (quantity, ingredient) = ingredient_name.split()
                ingredient_tuple = cur.execute(f'''SELECT * FROM ingredients
                                WHERE ingredient_name LIKE '%{ingredient}%';
                            ''').fetchall()
                if len(ingredient_tuple) > 1:
                    print('The measure is not conclusive!')
                else:
                    cur.execute(f'''INSERT INTO quantity ('quantity', 'recipe_id', 'measure_id', 'ingredient_id')
                                    VALUES (
                                    '{quantity}',
                                    '{last_recipe}',
                                    '8',
                                    '{ingredient_tuple[0][0]}');
                                ''')
                    conn.commit()


def look_for_recipe(ingredients, meals):
    if len(ingredients) > 1:
        ingredients_ids = cur.execute(f'''SELECT ingredient_id FROM ingredients
                                         WHERE ingredient_name IN {tuple(ingredients)};
                                     ''').fetchall()
        ingredients_ids = [ingredient_id[0] for ingredient_id in ingredients_ids]
    else:
        ingredients_ids = cur.execute(f'''SELECT ingredient_id FROM ingredients
                                                 WHERE ingredient_name = '{ingredients[0]}';
                                             ''').fetchall()
        ingredients_ids = [ingredient_id[0] for ingredient_id in ingredients_ids]

    if len(meals) > 1:
        meals_ids = cur.execute(f'''SELECT meal_id FROM meals
                                    WHERE meal_name IN {tuple(meals)};
                                ''').fetchall()
        meals_ids = [meal_id[0] for meal_id in meals_ids]
    else:
        meals_ids = cur.execute(f'''SELECT meal_id FROM meals
                                            WHERE meal_name = '{meals[0]}';
                                        ''').fetchall()
        meals_ids = [meal_id[0] for meal_id in meals_ids]

    recipe_ids = []
    for ingredient in ingredients_ids:
        recipe_ids.append(set(cur.execute(f'''SELECT recipe_id FROM quantity
                                              WHERE ingredient_id = {ingredient} 
                                          ''').fetchall()))
    recipe_ingredients = [r_id[0] for r_id in list(set.intersection(*recipe_ids))]

    recipe_meal = []
    for meal in meals_ids:
        recipe_meal.append(set(cur.execute(f'''SELECT recipe_id FROM serve
                                           WHERE meal_id = {meal} 
                                        ''').fetchall()))
    recipe_meals = [r_id[0] for r_id in list(set.union(*recipe_meal))]

    possible_recipe_ids = tuple(set(recipe_ingredients).intersection(recipe_meals))

    if possible_recipe_ids:
        possible_recipe_names = cur.execute(f'''SELECT recipe_name FROM recipes
                                                WHERE recipe_id IN {possible_recipe_ids}
                                            ''').fetchall()
        possible_recipe_names = [r_name[0] for r_name in possible_recipe_names]
        print(f'Recipes selected for you:', end=' ')
        print(*possible_recipe_names, sep=', ')
    else:
        print('There are no such recipes in the database.')

    conn.close()


if not args.ingredients:
    populate_table()
    add_recipe()
else:
    req_ingredients = args.ingredients.split(',')
    req_meals = args.meals.split(',')
    ingredients_check = True
    for ingredient in req_ingredients:
        if ingredient in data['ingredients']:
            continue
        else:
            print('There are no such recipes in the database.')
            conn.close()
            ingredients_check = False
    if ingredients_check:
        look_for_recipe(req_ingredients, req_meals)
