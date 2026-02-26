#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Задание 3: Бюджетный планировщик с аналитикой
Продвинутый уровень - транзакции, иерархия категорий, оптимизация
"""

import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal


class BudgetPlanner:
    """Система учета личных финансов с аналитикой"""
    
    def __init__(self, db_path="budget.db"):
        """Инициализация БД"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        self.create_indexes()
    
    def connect(self):
        """Подключение к БД с включением иностранных ключей"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Создание всех таблиц"""
        # Таблица иерархии категорий
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                parent_id INTEGER,
                category_type TEXT CHECK(category_type IN ('income', 'expense')),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)
        
        # Таблица транзакций
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                description TEXT,
                is_recurring INTEGER DEFAULT 0,
                recurring_period TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Таблица бюджетов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                planned_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category_id, month),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Таблица финансовых целей
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                target_date TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица регулярных транзакций
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                frequency TEXT NOT NULL,
                last_executed TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        self.conn.commit()
    
    def create_indexes(self):
        """Создание индексов для оптимизации запросов"""
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)",
             "Индекс на дату транзакций"),
            ("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)",
             "Индекс на категорию"),
            ("CREATE INDEX IF NOT EXISTS idx_budgets_month ON budgets(month)",
             "Индекс на месяц бюджета"),
            ("CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(category_type)",
             "Индекс на тип категории"),
        ]
        
        for index_sql, description in indexes:
            try:
                self.cursor.execute(index_sql)
            except sqlite3.OperationalError:
                pass
        
        self.conn.commit()
    
    # ============ КАТЕГОРИИ (ИЕРАРХИЯ) ============
    
    def create_category(self, name, category_type, parent_id=None, description=""):
        """Создание категории (с поддержкой иерархии)"""
        if category_type not in ['income', 'expense']:
            print("✗ Тип категории должен быть 'income' или 'expense'")
            return False
        
        try:
            self.cursor.execute("""
                INSERT INTO categories (name, parent_id, category_type, description)
                VALUES (?, ?, ?, ?)
            """, (name, parent_id, category_type, description))
            self.conn.commit()
            print(f"✓ Категория '{name}' создана!")
            return True
        except sqlite3.IntegrityError:
            print(f"✗ Категория '{name}' уже существует!")
            return False
    
    def get_category_hierarchy(self):
        """Получение иерархии категорий"""
        self.cursor.execute("""
            WITH RECURSIVE category_tree AS (
                SELECT id, name, parent_id, category_type, 0 as level
                FROM categories
                WHERE parent_id IS NULL
                
                UNION ALL
                
                SELECT c.id, c.name, c.parent_id, c.category_type, ct.level + 1
                FROM categories c
                JOIN category_tree ct ON c.parent_id = ct.id
            )
            SELECT id, name, parent_id, category_type, level
            FROM category_tree
            ORDER BY level, parent_id, name
        """)
        
        categories = self.cursor.fetchall()
        if categories:
            print("\n📂 ИЕРАРХИЯ КАТЕГОРИЙ:")
            for cat_id, name, parent_id, cat_type, level in categories:
                indent = "  " * level
                emoji = "💰" if cat_type == 'income' else "💸"
                print(f"{indent}{emoji} {name} (ID: {cat_id})")
            return categories
        else:
            print("✗ Категории не найдены!")
            return []
    
    def list_categories(self, category_type=None):
        """Вывод категорий"""
        if category_type:
            self.cursor.execute(
                "SELECT * FROM categories WHERE category_type = ? ORDER BY name",
                (category_type,)
            )
        else:
            self.cursor.execute("SELECT * FROM categories ORDER BY name")
        
        categories = self.cursor.fetchall()
        return categories
    
    # ============ ТРАНЗАКЦИИ ============
    
    def create_transaction(self, category_id, amount, description="", transaction_date=None):
        """Создание транзакции"""
        if transaction_date is None:
            transaction_date = datetime.now().date().isoformat()
        
        if amount <= 0:
            print("✗ Сумма должна быть > 0!")
            return False
        
        # Проверка существования категории
        self.cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        category = self.cursor.fetchone()
        if not category:
            print(f"✗ Категория с ID {category_id} не найдена!")
            return False
        
        try:
            self.cursor.execute("""
                INSERT INTO transactions (category_id, amount, transaction_date, description)
                VALUES (?, ?, ?, ?)
            """, (category_id, amount, transaction_date, description))
            self.conn.commit()
            print(f"✓ Транзакция на {amount} создана!")
            return True
        except sqlite3.Error as e:
            print(f"✗ Ошибка: {e}")
            return False
    
    def update_transaction(self, transaction_id, **kwargs):
        """Обновление транзакции в транзакции БД"""
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            valid_fields = {'amount', 'description', 'transaction_date'}
            update_fields = {k: v for k, v in kwargs.items() if k in valid_fields}
            
            if not update_fields:
                print("✗ Нет полей для обновления!")
                return False
            
            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [transaction_id]
            
            self.cursor.execute(f"UPDATE transactions SET {set_clause} WHERE id = ?", values)
            self.conn.commit()
            print(f"✓ Транзакция обновлена!")
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"✗ Ошибка: {e}")
            return False
    
    def delete_transaction(self, transaction_id):
        """Удаление транзакции"""
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            self.cursor.execute("SELECT amount FROM transactions WHERE id = ?", (transaction_id,))
            result = self.cursor.fetchone()
            
            if not result:
                print(f"✗ Транзакция {transaction_id} не найдена!")
                return False
            
            self.cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            self.conn.commit()
            print(f"✓ Транзакция удалена!")
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"✗ Ошибка: {e}")
            return False
    
    # ============ БЮДЖЕТЫ ============
    
    def set_budget(self, category_id, month, planned_amount):
        """Установка планового бюджета на месяц"""
        if planned_amount <= 0:
            print("✗ Бюджет должен быть > 0!")
            return False
        
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            self.cursor.execute("""
                INSERT INTO budgets (category_id, month, planned_amount)
                VALUES (?, ?, ?)
                ON CONFLICT(category_id, month) DO UPDATE SET planned_amount = ?
            """, (category_id, month, planned_amount, planned_amount))
            
            self.conn.commit()
            print(f"✓ Бюджет {planned_amount} установлен на {month}!")
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"✗ Ошибка: {e}")
            return False
    
    def get_budget_analysis(self, month):
        """Анализ соотношения бюджета и расходов"""
        self.cursor.execute("""
            SELECT 
                c.id,
                c.name,
                COALESCE(b.planned_amount, 0) as budget,
                COALESCE(SUM(t.amount), 0) as spent,
                COALESCE(b.planned_amount, 0) - COALESCE(SUM(t.amount), 0) as remaining,
                CASE 
                    WHEN b.planned_amount = 0 THEN 0
                    ELSE ROUND(COALESCE(SUM(t.amount), 0) * 100.0 / b.planned_amount, 1)
                END as utilization_percent
            FROM categories c
            LEFT JOIN budgets b ON c.id = b.category_id AND b.month = ?
            LEFT JOIN transactions t ON c.id = t.category_id AND strftime('%Y-%m', t.transaction_date) = ?
            WHERE c.category_type = 'expense'
            GROUP BY c.id, c.name, b.planned_amount
            ORDER BY spent DESC
        """, (month, month))
        
        results = self.cursor.fetchall()
        if results:
            print(f"\n💰 АНАЛИЗ БЮДЖЕТА НА {month}:")
            print(f"{'Категория':<20} {'Бюджет':>10} {'Потрачено':>10} {'Остаток':>10} {'%':>6}")
            print("-" * 60)
            
            total_budget = 0
            total_spent = 0
            
            for cat_id, name, budget, spent, remaining, utilization in results:
                utilization = utilization if utilization is not None else 0
                status = "✓" if spent <= budget else "⚠️" if spent <= budget * 1.1 else "❌"
                print(f"{status} {name:<18} {budget:>10.0f} {spent:>10.0f} {remaining:>10.0f} {utilization:>5.1f}%")
                total_budget += budget
                total_spent += spent
            
            print("-" * 60)
            print(f"ИТОГО:            {total_budget:>10.0f} {total_spent:>10.0f}")
            
            return results
        else:
            print("✗ Нет бюджетов!")
            return []
    
    # ============ АНАЛИТИКА И ОТЧЕТЫ ============
    
    def get_period_report(self, start_date, end_date):
        """Детальный отчёт за период"""
        self.cursor.execute("""
            SELECT 
                c.name,
                c.category_type,
                SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.transaction_date BETWEEN ? AND ?
            GROUP BY c.id, c.name, c.category_type
            ORDER BY c.category_type DESC, total DESC
        """, (start_date, end_date))
        
        results = self.cursor.fetchall()
        
        if results:
            print(f"\n📊 ОТЧЁТ С {start_date} ПО {end_date}:")
            print("=" * 60)
            
            income_total = 0
            expense_total = 0
            
            print("\n💰 ДОХОДЫ:")
            for name, cat_type, total in results:
                if cat_type == 'income':
                    print(f"  {name}: {total:.2f}")
                    income_total += total
            
            print(f"\nИтого доходов: {income_total:.2f}")
            
            print("\n💸 РАСХОДЫ:")
            for name, cat_type, total in results:
                if cat_type == 'expense':
                    print(f"  {name}: {total:.2f}")
                    expense_total += total
            
            print(f"\nИтого расходов: {expense_total:.2f}")
            print(f"\n💵 Баланс: {income_total - expense_total:.2f}")
            
            return results
        else:
            print("✗ Нет транзакций за этот период!")
            return []
    
    def get_monthly_dynamics(self, year):
        """Динамика доходов/расходов по месяцам"""
        self.cursor.execute("""
            SELECT 
                strftime('%m', t.transaction_date) as month,
                c.category_type,
                SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE strftime('%Y', t.transaction_date) = ?
            GROUP BY strftime('%m', t.transaction_date), c.category_type
            ORDER BY month
        """, (year,))
        
        results = self.cursor.fetchall()
        if results:
            print(f"\n📈 ДИНАМИКА ПО МЕСЯЦАМ ({year}):")
            
            months = {}
            for month, cat_type, total in results:
                if month not in months:
                    months[month] = {'income': 0, 'expense': 0}
                months[month][cat_type] = total
            
            print(f"{'Месяц':<10} {'Доходы':>12} {'Расходы':>12} {'Баланс':>12}")
            print("-" * 50)
            
            for month in sorted(months.keys()):
                income = months[month].get('income', 0)
                expense = months[month].get('expense', 0)
                balance = income - expense
                print(f"{month:<10} {income:>12.0f} {expense:>12.0f} {balance:>12.0f}")
            
            return results
        else:
            print("✗ Нет данных за этот год!")
            return []
    
    def compare_with_previous_period(self, month):
        """Сравнение с предыдущим месяцем"""
        # Парсируем месяц YYYY-MM
        year, month_num = month.split('-')
        
        # Предыдущий месяц
        prev_month_int = int(month_num) - 1
        if prev_month_int == 0:
            prev_year = str(int(year) - 1)
            prev_month_int = 12
        else:
            prev_year = year
        
        prev_month = f"{prev_year}-{prev_month_int:02d}"
        
        self.cursor.execute("""
            SELECT 
                c.name,
                c.category_type,
                strftime('%Y-%m', t.transaction_date) as period,
                SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE strftime('%Y-%m', t.transaction_date) IN (?, ?)
            GROUP BY c.name, c.category_type, period
            ORDER BY c.category_type DESC, c.name
        """, (month, prev_month))
        
        results = self.cursor.fetchall()
        if results:
            print(f"\n📊 СРАВНЕНИЕ {month} с {prev_month}:")
            print(f"{'Категория':<20} {f'{prev_month}':>12} {f'{month}':>12} {'Δ':>10} {'%Δ':>10}")
            print("-" * 65)
            
            for name, cat_type, period, total in results:
                # Значение out по периодам
                print(f"{name:<20} {total:>12.0f}")
            
            return results
        else:
            print("✗ Нет данных для сравнения!")
            return []
    
    def forecast_accumulation(self, goal_id, days=30):
        """Прогнозирование накоплений к сроку цели"""
        self.cursor.execute(
            "SELECT target_amount, current_amount, target_date FROM financial_goals WHERE id = ?",
            (goal_id,)
        )
        goal = self.cursor.fetchone()
        
        if not goal:
            print(f"✗ Цель {goal_id} не найдена!")
            return None
        
        target, current, target_date = goal
        
        # Средний доход за последний месяц
        self.cursor.execute("""
            SELECT SUM(t.amount) * 1.0
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE c.category_type = 'income'
            AND t.transaction_date >= date('now', '-30 days')
        """)
        
        result = self.cursor.fetchone()
        avg_monthly_income = result[0] if result[0] else 0
        
        # Средние расходы за последний месяц
        self.cursor.execute("""
            SELECT SUM(t.amount) * 1.0
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE c.category_type = 'expense'
            AND t.transaction_date >= date('now', '-30 days')
        """)
        
        result = self.cursor.fetchone()
        avg_monthly_expense = result[0] if result[0] else 0
        
        avg_monthly_savings = avg_monthly_income - avg_monthly_expense
        
        # Дней до целевой даты
        target_datetime = datetime.fromisoformat(target_date)
        days_to_target = (target_datetime.date() - datetime.now().date()).days
        
        if days_to_target <= 0:
            print("✗ Целевая дата уже прошла!")
            return None
        
        # Прогноз
        months_to_target = days_to_target / 30
        forecasted_amount = current + (avg_monthly_savings * months_to_target)
        
        print(f"\n🎯 ПРОГНОЗ ЦЕЛИ: {goal[2]}")
        print(f"  Текущая сумма: {current:.2f}")
        print(f"  Целевая сумма: {target:.2f}")
        print(f"  Средние сбережения в месяц: {avg_monthly_savings:.2f}")
        print(f"  Дней до цели: {days_to_target}")
        print(f"  Прогнозируемая сумма: {forecasted_amount:.2f}")
        
        if forecasted_amount >= target:
            print(f"  ✓ УСПЕШНО! Цель будет достаточно. Избыток: {forecasted_amount - target:.2f}")
        else:
            print(f"  ⚠️  НЕДОСТАТОЧНО. Не хватит: {target - forecasted_amount:.2f}")
        
        return forecasted_amount
    
    # ============ РЕГУЛЯРНЫЕ ТРАНЗАКЦИИ ============
    
    def create_recurring_transaction(self, category_id, amount, description, frequency):
        """Создание регулярной транзакции"""
        try:
            self.cursor.execute("""
                INSERT INTO recurring_transactions 
                (category_id, amount, description, frequency)
                VALUES (?, ?, ?, ?)
            """, (category_id, amount, description, frequency))
            self.conn.commit()
            print(f"✓ Регулярная транзакция создана!")
            return True
        except sqlite3.Error as e:
            print(f"✗ Ошибка: {e}")
            return False
    
    def process_recurring_transactions(self):
        """Обработка регулярных транзакций (автоматическое создание)"""
        today = datetime.now().date().isoformat()
        
        self.cursor.execute("""
            SELECT id, category_id, amount, description, frequency, last_executed
            FROM recurring_transactions
            WHERE is_active = 1
        """)
        
        recurring = self.cursor.fetchall()
        count = 0
        
        for rec_id, cat_id, amount, desc, frequency, last_exec in recurring:
            should_execute = False
            
            if frequency == 'daily':
                should_execute = True
            elif frequency == 'weekly':
                should_execute = (not last_exec or 
                    (datetime.fromisoformat(today) - datetime.fromisoformat(last_exec)).days >= 7)
            elif frequency == 'monthly':
                should_execute = (not last_exec or
                    (datetime.fromisoformat(today).month != 
                     datetime.fromisoformat(last_exec).month))
            
            if should_execute:
                self.create_transaction(cat_id, amount, f"{desc} (Регулярная)", today)
                self.cursor.execute(
                    "UPDATE recurring_transactions SET last_executed = ? WHERE id = ?",
                    (today, rec_id)
                )
                count += 1
        
        self.conn.commit()
        if count > 0:
            print(f"✓ Обработано {count} регулярных транзакций!")
        return count
    
    # ============ ФИНАНСОВЫЕ ЦЕЛИ ============
    
    def create_financial_goal(self, name, target_amount, target_date, priority="normal", description=""):
        """Создание финансовой цели"""
        try:
            self.cursor.execute("""
                INSERT INTO financial_goals 
                (name, target_amount, target_date, priority, description)
                VALUES (?, ?, ?, ?, ?)
            """, (name, target_amount, target_date, priority, description))
            self.conn.commit()
            print(f"✓ Цель '{name}' создана!")
            return True
        except sqlite3.Error as e:
            print(f"✗ Ошибка: {e}")
            return False
    
    def update_goal_progress(self, goal_id, new_amount):
        """Обновление прогресса цели"""
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            self.cursor.execute(
                "UPDATE financial_goals SET current_amount = ? WHERE id = ?",
                (new_amount, goal_id)
            )
            
            self.conn.commit()
            print(f"✓ Прогресс цели обновлён!")
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"✗ Ошибка: {e}")
            return False
    
    def get_goals_progress(self):
        """Получение прогресса всех целей с визуализацией"""
        self.cursor.execute("""
            SELECT id, name, target_amount, current_amount, target_date, priority
            FROM financial_goals
            ORDER BY priority DESC, target_date ASC
        """)
        
        goals = self.cursor.fetchall()
        if goals:
            print("\n🎯 ФИНАНСОВЫЕ ЦЕЛИ:")
            print("-" * 80)
            
            for goal_id, name, target, current, target_date, priority in goals:
                percent = (current / target * 100) if target > 0 else 0
                filled = int(percent / 5)
                empty = 20 - filled
                bar = "█" * filled + "░" * empty
                
                print(f"\n{name} ({priority})")
                print(f"[{bar}] {percent:.0f}% ({current:.0f}/{target:.0f})")
                print(f"Срок: {target_date}")
            
            return goals
        else:
            print("✗ Нет целей!")
            return []
    
    # ============ КОНСОЛЬНОЕ МЕНЮ ============
    
    def show_menu(self):
        """Главное меню"""
        while True:
            print("\n" + "=" * 60)
            print("💼 БЮДЖЕТНЫЙ ПЛАНИРОВЩИК - ГЛАВНОЕ МЕНЮ")
            print("=" * 60)
            print("1. 📂 Управление категориями")
            print("2. 💰 Управление транзакциями")
            print("3. 📊 Управление бюджетами")
            print("4. 🎯 Финансовые цели")
            print("5. 📈 Аналитика и отчеты")
            print("6. 🔄 Регулярные транзакции")
            print("7. 🚀 Добавить тестовые данные")
            print("0. ❌ Выход")
            print("=" * 60)
            
            choice = input("Выберите: ").strip()
            
            if choice == "0":
                print("✓ До свидания!")
                break
            elif choice == "1":
                self._menu_categories()
            elif choice == "2":
                self._menu_transactions()
            elif choice == "3":
                self._menu_budgets()
            elif choice == "4":
                self._menu_goals()
            elif choice == "5":
                self._menu_analytics()
            elif choice == "6":
                self._menu_recurring()
            elif choice == "7":
                self._add_test_data()
            else:
                print("✗ Неверный выбор!")
    
    def _menu_categories(self):
        """Меню категорий"""
        print("\n--- Категории ---")
        print("1. Добавить категорию")
        print("2. Иерархия категорий")
        print("3. Показать категории")
        print("0. Назад")
        
        choice = input("Выберите: ").strip()
        if choice == "1":
            name = input("Название: ").strip()
            cat_type = input("Тип (income/expense): ").strip()
            parent = input("ID родителя (опционально): ").strip()
            self.create_category(name, cat_type, int(parent) if parent else None)
        elif choice == "2":
            self.get_category_hierarchy()
        elif choice == "3":
            self.get_category_hierarchy()
    
    def _menu_transactions(self):
        """Меню транзакций"""
        print("\n--- Транзакции ---")
        print("1. Добавить транзакцию")
        print("2. Редактировать")
        print("3. Удалить")
        print("0. Назад")
        
        choice = input("Выберите: ").strip()
        if choice == "1":
            cat_id = int(input("ID категории: ").strip())
            amount = float(input("Сумма: ").strip())
            desc = input("Описание: ").strip()
            self.create_transaction(cat_id, amount, desc)
        elif choice == "2":
            trans_id = int(input("ID транзакции: ").strip())
            amount = float(input("Новая сумма: ").strip())
            self.update_transaction(trans_id, amount=amount)
        elif choice == "3":
            trans_id = int(input("ID транзакции: ").strip())
            self.delete_transaction(trans_id)
    
    def _menu_budgets(self):
        """Меню бюджетов"""
        print("\n--- Бюджеты ---")
        print("1. Установить бюджет")
        print("2. Анализ бюджета")
        print("0. Назад")
        
        choice = input("Выберите: ").strip()
        if choice == "1":
            cat_id = int(input("ID категории: ").strip())
            month = input("Месяц (YYYY-MM): ").strip()
            amount = float(input("Сумма: ").strip())
            self.set_budget(cat_id, month, amount)
        elif choice == "2":
            month = input("Месяц (YYYY-MM): ").strip()
            self.get_budget_analysis(month)
    
    def _menu_goals(self):
        """Меню целей"""
        print("\n--- Финансовые цели ---")
        print("1. Создать цель")
        print("2. Показать прогресс")
        print("3. Прогноз")
        print("0. Назад")
        
        choice = input("Выберите: ").strip()
        if choice == "1":
            name = input("Название: ").strip()
            target = float(input("Целевая сумма: ").strip())
            date = input("Дата (YYYY-MM-DD): ").strip()
            self.create_financial_goal(name, target, date)
        elif choice == "2":
            self.get_goals_progress()
        elif choice == "3":
            goal_id = int(input("ID цели: ").strip())
            self.forecast_accumulation(goal_id)
    
    def _menu_analytics(self):
        """Меню аналитики"""
        print("\n--- Аналитика ---")
        print("1. Отчёт за период")
        print("2. Динамика по месяцам")
        print("3. Сравнение с предыдущим периодом")
        print("0. Назад")
        
        choice = input("Выберите: ").strip()
        if choice == "1":
            start = input("С (YYYY-MM-DD): ").strip()
            end = input("По (YYYY-MM-DD): ").strip()
            self.get_period_report(start, end)
        elif choice == "2":
            year = input("Год (YYYY): ").strip()
            self.get_monthly_dynamics(year)
        elif choice == "3":
            month = input("Месяц (YYYY-MM): ").strip()
            self.compare_with_previous_period(month)
    
    def _menu_recurring(self):
        """Меню регулярных транзакций"""
        print("\n--- Регулярные транзакции ---")
        print("1. Создать регулярную")
        print("2. Обработать")
        print("0. Назад")
        
        choice = input("Выберите: ").strip()
        if choice == "1":
            cat_id = int(input("ID категории: ").strip())
            amount = float(input("Сумма: ").strip())
            desc = input("Описание: ").strip()
            freq = input("Частота (daily/weekly/monthly): ").strip()
            self.create_recurring_transaction(cat_id, amount, desc, freq)
        elif choice == "2":
            self.process_recurring_transactions()
    
    def _add_test_data(self):
        """Добавление тестовых данных"""
        print("Добавляю тестовые данные...")
        
        # Категории
        self.create_category("Зарплата", "income")
        self.create_category("Фриланс", "income")
        self.create_category("Еда", "expense")
        self.create_category("Транспорт", "expense")
        self.create_category("Развлечения", "expense")
        self.create_category("Квартира", "expense")
        
        # Транзакции
        today = datetime.now().date()
        for i in range(30):
            date = (today - timedelta(days=i)).isoformat()
            
            if i % 7 == 0:
                self.create_transaction(1, 50000, "Зарплата", date)
            
            if i % 3 == 0:
                self.create_transaction(3, 2000, "Продукты", date)
            
            if i % 5 == 0:
                self.create_transaction(4, 500, "Метро", date)
        
        self.create_transaction(6, 25000, "Коммунальные услуги", 
                               (today - timedelta(days=1)).isoformat())
        
        # Цели
        self.create_financial_goal("Отпуск", 100000, 
                                  (today + timedelta(days=200)).isoformat(), 
                                  "high", "Отпуск в Таиланде")
        self.create_financial_goal("Ноутбук", 150000, 
                                  (today + timedelta(days=120)).isoformat(),
                                  "normal", "Новый рабочий ноутбук")
        
        # Бюджеты
        month = today.strftime("%Y-%m")
        self.set_budget(3, month, 15000)
        self.set_budget(4, month, 5000)
        self.set_budget(5, month, 10000)
        
        print("✓ Тестовые данные добавлены!")


def main():
    """Главная функция"""
    print("🚀 Запуск 'Бюджетный планировщик'...\n")
    
    planner = BudgetPlanner()
    
    try:
        planner.show_menu()
    except KeyboardInterrupt:
        print("\n\n✓ Программа прервана!")
    finally:
        planner.close()


if __name__ == "__main__":
    main()
