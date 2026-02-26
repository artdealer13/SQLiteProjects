
"""
Задание 1: Книга рецептов
Базовый уровень - работа с CRUD операциями в SQLite
"""

import sqlite3
from datetime import datetime


class RecipeBook:
    """Приложение для управления рецептами"""
    
    def __init__(self, db_path="recipes.db"):
        """Инициализация базы данных"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_table()
    
    def connect(self):
        """Подключение к БД"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()
    
    def create_table(self):
        """Создание таблицы рецептов"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                cooking_time INTEGER NOT NULL,
                rating REAL DEFAULT 5.0,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    # ============ CRUD ОПЕРАЦИИ ============
    
    def create_recipe(self, name, category, ingredients, cooking_time, rating=5.0, description=""):
        """
        Создание нового рецепта
        Args:
            name: название рецепта
            category: категория (салаты, супы, основные блюда и т.д.)
            ingredients: ингредиенты (строка)
            cooking_time: время приготовления в минутах
            rating: рейтинг (1-5)
            description: описание
        """
        if not self._validate_input(name, category, cooking_time, rating):
            return False
        
        try:
            self.cursor.execute("""
                INSERT INTO recipes (name, category, ingredients, cooking_time, rating, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, category, ingredients, cooking_time, rating, description))
            self.conn.commit()
            print(f"✓ Рецепт '{name}' успешно добавлен!")
            return True
        except sqlite3.IntegrityError:
            print("✗ Ошибка: рецепт с таким названием уже существует!")
            return False
    
    def read_recipe(self, recipe_id):
        """Получение рецепта по ID"""
        self.cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        recipe = self.cursor.fetchone()
        if recipe:
            self._print_recipe(recipe)
            return recipe
        else:
            print(f"✗ Рецепт с ID {recipe_id} не найден!")
            return None
    
    def update_recipe(self, recipe_id, **kwargs):
        """
        Обновление рецепта
        Args:
            recipe_id: ID рецепта
            **kwargs: поля для обновления (name, category, ingredients, cooking_time, rating, description)
        """
        valid_fields = {'name', 'category', 'ingredients', 'cooking_time', 'rating', 'description'}
        update_fields = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not update_fields:
            print("✗ Нет полей для обновления!")
            return False
        
        # Валидация
        if 'cooking_time' in update_fields and update_fields['cooking_time'] <= 0:
            print("✗ Время приготовления должно быть > 0!")
            return False
        
        if 'rating' in update_fields and not (1 <= update_fields['rating'] <= 5):
            print("✗ Рейтинг должен быть от 1 до 5!")
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values()) + [recipe_id]
        
        try:
            self.cursor.execute(f"UPDATE recipes SET {set_clause} WHERE id = ?", values)
            self.conn.commit()
            print(f"✓ Рецепт успешно обновлён!")
            return True
        except sqlite3.IntegrityError:
            print("✗ Ошибка: рецепт с таким названием уже существует!")
            return False
    
    def delete_recipe(self, recipe_id):
        """Удаление рецепта"""
        self.cursor.execute("SELECT name FROM recipes WHERE id = ?", (recipe_id,))
        recipe = self.cursor.fetchone()
        
        if not recipe:
            print(f"✗ Рецепт с ID {recipe_id} не найден!")
            return False
        
        name = recipe[0]
        self.cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        self.conn.commit()
        print(f"✓ Рецепт '{name}' успешно удалён!")
        return True
    
    # ============ ПОИСК ============
    
    def search_by_category(self, category):
        """Поиск рецептов по категории"""
        self.cursor.execute(
            "SELECT * FROM recipes WHERE LOWER(category) = LOWER(?) ORDER BY rating DESC",
            (category,)
        )
        recipes = self.cursor.fetchall()
        
        if recipes:
            print(f"\n📂 Рецепты в категории '{category}' ({len(recipes)} найдено):")
            for recipe in recipes:
                self._print_recipe(recipe)
            return recipes
        else:
            print(f"✗ Рецепты в категории '{category}' не найдены!")
            return []
    
    def search_by_name(self, name_part):
        """Поиск рецептов по названию (частичное совпадение)"""
        self.cursor.execute(
            "SELECT * FROM recipes WHERE LOWER(name) LIKE LOWER(?) ORDER BY rating DESC",
            (f"%{name_part}%",)
        )
        recipes = self.cursor.fetchall()
        
        if recipes:
            print(f"\n🔍 Рецепты, содержащие '{name_part}' ({len(recipes)} найдено):")
            for recipe in recipes:
                self._print_recipe(recipe)
            return recipes
        else:
            print(f"✗ Рецепты с названием '{name_part}' не найдены!")
            return []
    
    def search_by_max_time(self, max_time):
        """Поиск рецептов по максимальному времени приготовления"""
        self.cursor.execute(
            "SELECT * FROM recipes WHERE cooking_time <= ? ORDER BY cooking_time ASC",
            (max_time,)
        )
        recipes = self.cursor.fetchall()
        
        if recipes:
            print(f"\n⏱️  Рецепты за {max_time} минут или меньше ({len(recipes)} найдено):")
            for recipe in recipes:
                self._print_recipe(recipe)
            return recipes
        else:
            print(f"✗ Рецепты за {max_time} минут не найдены!")
            return []
    
    # ============ ОТЧЕТЫ ============
    
    def get_top_5_recipes(self):
        """Получение топ-5 рецептов по рейтингу"""
        self.cursor.execute(
            "SELECT * FROM recipes ORDER BY rating DESC LIMIT 5"
        )
        recipes = self.cursor.fetchall()
        
        if recipes:
            print("\n⭐ ТОП-5 РЕЦЕПТОВ:")
            for idx, recipe in enumerate(recipes, 1):
                print(f"{idx}. {recipe[1]} - Рейтинг: {recipe[5]}/5 ({recipe[4]} мин)")
            return recipes
        else:
            print("✗ Рецепты не найдены!")
            return []
    
    def get_category_statistics(self):
        """Подсчёт статистики по категориям"""
        self.cursor.execute("""
            SELECT category, COUNT(*) as count, AVG(rating) as avg_rating
            FROM recipes
            GROUP BY category
            ORDER BY count DESC
        """)
        stats = self.cursor.fetchall()
        
        if stats:
            print("\n📊 СТАТИСТИКА ПО КАТЕГОРИЯМ:")
            for category, count, avg_rating in stats:
                print(f"  {category}: {count} рецептов (средний рейтинг: {avg_rating:.1f}/5)")
            return stats
        else:
            print("✗ Данные не найдены!")
            return []
    
    def list_all_recipes(self):
        """Вывод всех рецептов"""
        self.cursor.execute("SELECT * FROM recipes ORDER BY rating DESC")
        recipes = self.cursor.fetchall()
        
        if recipes:
            print(f"\n📖 ВСЕ РЕЦЕПТЫ ({len(recipes)} всего):")
            for recipe in recipes:
                self._print_recipe(recipe)
            return recipes
        else:
            print("✗ Рецепты не найдены!")
            return []
    
    # ============ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ============
    
    def _print_recipe(self, recipe):
        """Форматированный вывод рецепта"""
        recipe_id, name, category, ingredients, cooking_time, rating, description, created_at = recipe
        
        print(f"\n  ID: {recipe_id}")
        print(f"  📝 Название: {name}")
        print(f"  📂 Категория: {category}")
        print(f"  ⏱️  Время: {cooking_time} минут")
        print(f"  ⭐ Рейтинг: {rating}/5")
        print(f"  📄 Ингредиенты: {ingredients}")
        if description:
            print(f"  ℹ️  Описание: {description}")
        print(f"  📅 Добавлено: {created_at}")
        print("  " + "-" * 60)
    
    def _validate_input(self, name, category, cooking_time, rating):
        """Валидация входных данных"""
        if not name or not isinstance(name, str):
            print("✗ Название должно быть непустой строкой!")
            return False
        
        if not category or not isinstance(category, str):
            print("✗ Категория должна быть непустой строкой!")
            return False
        
        if not isinstance(cooking_time, int) or cooking_time <= 0:
            print("✗ Время приготовления должно быть положительным числом!")
            return False
        
        if not isinstance(rating, (int, float)) or not (1 <= rating <= 5):
            print("✗ Рейтинг должен быть числом от 1 до 5!")
            return False
        
        return True
    
    # ============ КОНСОЛЬНОЕ МЕНЮ ============
    
    def show_menu(self):
        """Отображение главного меню"""
        while True:
            print("\n" + "=" * 60)
            print("📖 КНИГА РЕЦЕПТОВ - ГЛАВНОЕ МЕНЮ")
            print("=" * 60)
            print("1. ➕ Добавить новый рецепт")
            print("2. 🔍 Просмотреть рецепт по ID")
            print("3. 📝 Редактировать рецепт")
            print("4. ❌ Удалить рецепт")
            print("5. 📂 Поиск по категории")
            print("6. 🔎 Поиск по названию")
            print("7. ⏱️  Поиск по максимальному времени")
            print("8. ⭐ Топ-5 рецептов")
            print("9. 📊 Статистика по категориям")
            print("10. 📖 Все рецепты")
            print("11. 🚀 Добавить тестовые данные")
            print("0. ❌ Выход")
            print("=" * 60)
            
            choice = input("Выберите действие (0-11): ").strip()
            
            if choice == "0":
                print("✓ До свидания!")
                break
            elif choice == "1":
                self._menu_add_recipe()
            elif choice == "2":
                self._menu_read_recipe()
            elif choice == "3":
                self._menu_update_recipe()
            elif choice == "4":
                self._menu_delete_recipe()
            elif choice == "5":
                self._menu_search_by_category()
            elif choice == "6":
                self._menu_search_by_name()
            elif choice == "7":
                self._menu_search_by_time()
            elif choice == "8":
                self.get_top_5_recipes()
            elif choice == "9":
                self.get_category_statistics()
            elif choice == "10":
                self.list_all_recipes()
            elif choice == "11":
                self._add_test_data()
            else:
                print("✗ Неверный выбор! Попробуйте снова.")
    
    def _menu_add_recipe(self):
        """Меню добавления рецепта"""
        print("\n--- Добавление нового рецепта ---")
        try:
            name = input("Название рецепта: ").strip()
            category = input("Категория (салаты, супы, основные блюда и т.д.): ").strip()
            ingredients = input("Ингредиенты (через запятую): ").strip()
            cooking_time = int(input("Время приготовления (минут): ").strip())
            
            rating_input = input("Рейтинг (1-5, по умолчанию 5): ").strip()
            rating = float(rating_input) if rating_input else 5.0
            
            description = input("Описание (опционально): ").strip()
            
            self.create_recipe(name, category, ingredients, cooking_time, rating, description)
        except ValueError:
            print("✗ Ошибка: некорректный ввод данных!")
    
    def _menu_read_recipe(self):
        """Меню просмотра рецепта"""
        try:
            recipe_id = int(input("Введите ID рецепта: ").strip())
            self.read_recipe(recipe_id)
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _menu_update_recipe(self):
        """Меню редактирования рецепта"""
        try:
            recipe_id = int(input("Введите ID рецепта для редактирования: ").strip())
            print("Оставьте поле пустым, чтобы не менять значение")
            
            updates = {}
            name = input("Новое название: ").strip()
            if name:
                updates['name'] = name
            
            category = input("Новая категория: ").strip()
            if category:
                updates['category'] = category
            
            ingredients = input("Новые ингредиенты: ").strip()
            if ingredients:
                updates['ingredients'] = ingredients
            
            cooking_time = input("Новое время приготовления: ").strip()
            if cooking_time:
                updates['cooking_time'] = int(cooking_time)
            
            rating = input("Новый рейтинг: ").strip()
            if rating:
                updates['rating'] = float(rating)
            
            description = input("Новое описание: ").strip()
            if description:
                updates['description'] = description
            
            if updates:
                self.update_recipe(recipe_id, **updates)
            else:
                print("✗ Не было внесено никаких изменений!")
        except ValueError:
            print("✗ Ошибка: некорректный ввод данных!")
    
    def _menu_delete_recipe(self):
        """Меню удаления рецепта"""
        try:
            recipe_id = int(input("Введите ID рецепта для удаления: ").strip())
            confirm = input("Вы уверены? (да/нет): ").strip().lower()
            if confirm in ['да', 'yes', 'y']:
                self.delete_recipe(recipe_id)
            else:
                print("✓ Удаление отменено!")
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _menu_search_by_category(self):
        """Меню поиска по категории"""
        category = input("Введите категорию: ").strip()
        self.search_by_category(category)
    
    def _menu_search_by_name(self):
        """Меню поиска по названию"""
        name = input("Введите часть названия: ").strip()
        self.search_by_name(name)
    
    def _menu_search_by_time(self):
        """Меню поиска по времени"""
        try:
            max_time = int(input("Введите максимальное время приготовления (минут): ").strip())
            self.search_by_max_time(max_time)
        except ValueError:
            print("✗ Ошибка: время должно быть числом!")
    
    def _add_test_data(self):
        """Добавление тестовых данных"""
        test_recipes = [
            ("Цезарь с курицей", "Салаты", "курица, салат романо, пармезан, сухарики", 15, 4.8, "Классический салат"),
            ("Борщ", "Супы", "свёкла, говядина, капуста, картофель", 60, 4.7, "Украинский борщ"),
            ("Паста Болоньезе", "Основные блюда", "паста, говяжий фарш, помидоры, лук", 30, 4.5, "Спагетти с мясным соусом"),
            ("Греческий салат", "Салаты", "томаты, огурцы, сыр фета, маслины", 10, 4.6, "Свежий и полезный"),
            ("Суп из курицы", "Супы", "курица, морковь, сельдерей, лапша", 45, 4.4, "Домашний суп"),
            ("Рис с овощами", "Гарниры", "рис, морковь, горошек, кукуруза", 20, 4.3, "Чумли рис"),
            ("Томатный суп", "Супы", "помидоры, сливки, лук, чеснок", 25, 4.2, "Кремовый суп"),
            ("Шоколадное печенье", "Десерты", "мука, шоколад, масло, яйцо", 30, 4.9, "Мягкое печенье"),
        ]
        
        count = 0
        for recipe in test_recipes:
            if self.create_recipe(*recipe):
                count += 1
        
        print(f"\n✓ Добавлено {count} тестовых рецептов!")


def main():
    """Главная функция"""
    print("🚀 Запуск приложения 'Книга рецептов'...\n")
    
    recipe_book = RecipeBook()
    
    try:
        recipe_book.show_menu()
    except KeyboardInterrupt:
        print("\n\n✓ Программа прервана пользователем!")
    finally:
        recipe_book.close()


if __name__ == "__main__":
    main()
