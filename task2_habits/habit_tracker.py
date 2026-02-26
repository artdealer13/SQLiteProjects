
"""
Задание 2: Трекер привычек
Средний уровень - работа с датами, JOIN и агрегирующими функциями
"""

import sqlite3
from datetime import datetime, timedelta


class HabitTracker:
    """Приложение для отслеживания привычек"""
    
    def __init__(self, db_path="habits.db"):
        """Инициализация базы данных"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Подключение к БД"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Создание таблиц"""
        # Таблица привычек
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                category TEXT,
                frequency TEXT DEFAULT 'daily',
                target_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Таблица логов выполнения привычек
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                UNIQUE(habit_id, log_date)
            )
        """)
        
        # Таблица достижений (бейджи)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                badge_name TEXT NOT NULL,
                description TEXT,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            )
        """)
        
        self.conn.commit()
    
    # ============ CRUD ДЛЯ ПРИВЫЧЕК ============
    
    def create_habit(self, name, description="", category="", frequency="daily", target_time=""):
        """Создание новой привычки"""
        if not self._validate_habit(name):
            return False
        
        try:
            self.cursor.execute("""
                INSERT INTO habits (name, description, category, frequency, target_time)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, category, frequency, target_time))
            self.conn.commit()
            print(f"✓ Привычка '{name}' успешно создана!")
            return True
        except sqlite3.IntegrityError:
            print("✗ Ошибка: привычка с таким названием уже существует!")
            return False
    
    def read_habit(self, habit_id):
        """Получение информации о привычке"""
        self.cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,))
        habit = self.cursor.fetchone()
        
        if habit:
            self._print_habit(habit)
            return habit
        else:
            print(f"✗ Привычка с ID {habit_id} не найдена!")
            return None
    
    def update_habit(self, habit_id, **kwargs):
        """Обновление привычки"""
        valid_fields = {'name', 'description', 'category', 'frequency', 'target_time', 'is_active'}
        update_fields = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not update_fields:
            print("✗ Нет полей для обновления!")
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values()) + [habit_id]
        
        try:
            self.cursor.execute(f"UPDATE habits SET {set_clause} WHERE id = ?", values)
            self.conn.commit()
            print(f"✓ Привычка успешно обновлена!")
            return True
        except sqlite3.IntegrityError:
            print("✗ Ошибка: привычка с таким названием уже существует!")
            return False
    
    def delete_habit(self, habit_id):
        """Удаление привычки и всех её логов"""
        self.cursor.execute("SELECT name FROM habits WHERE id = ?", (habit_id,))
        habit = self.cursor.fetchone()
        
        if not habit:
            print(f"✗ Привычка с ID {habit_id} не найдена!")
            return False
        
        name = habit[0]
        self.cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self.conn.commit()
        print(f"✓ Привычка '{name}' успешно удалена!")
        return True
    
    # ============ ЛОГИРОВАНИЕ ============
    
    def log_habit_completion(self, habit_id, log_date=None, note=""):
        """Отметить выполнение привычки за день"""
        if log_date is None:
            log_date = datetime.now().date().isoformat()
        
        # Проверяем существование привычки
        self.cursor.execute("SELECT name FROM habits WHERE id = ?", (habit_id,))
        habit = self.cursor.fetchone()
        if not habit:
            print(f"✗ Привычка с ID {habit_id} не найдена!")
            return False
        
        try:
            self.cursor.execute("""
                INSERT INTO habit_logs (habit_id, log_date, completed, note)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(habit_id, log_date) DO UPDATE SET completed = 1, note = ?
            """, (habit_id, log_date, note, note))
            self.conn.commit()
            print(f"✓ '{habit[0]}' отмечена как выполненная на {log_date}")
            self._check_achievements(habit_id)
            return True
        except sqlite3.Error as e:
            print(f"✗ Ошибка: {e}")
            return False
    
    def unlog_habit_completion(self, habit_id, log_date=None):
        """Отменить отметку выполнения"""
        if log_date is None:
            log_date = datetime.now().date().isoformat()
        
        self.cursor.execute("""
            UPDATE habit_logs SET completed = 0 WHERE habit_id = ? AND log_date = ?
        """, (habit_id, log_date))
        self.conn.commit()
        print(f"✓ Отметка выполнения отменена")
        return True
    
    # ============ СТАТИСТИКА ============
    
    def get_weekly_stats(self, habit_id):
        """Статистика выполнения за неделю"""
        today = datetime.now().date()
        week_ago = today - timedelta(days=6)
        
        self.cursor.execute("""
            SELECT 
                habits.name,
                COUNT(habit_logs.id) as total_days,
                SUM(CASE WHEN habit_logs.completed = 1 THEN 1 ELSE 0 END) as completed_days,
                ROUND(SUM(CASE WHEN habit_logs.completed = 1 THEN 1 ELSE 0 END) * 100.0 / 
                      COUNT(habit_logs.id), 1) as success_rate
            FROM habits
            LEFT JOIN habit_logs ON habits.id = habit_logs.habit_id 
            WHERE habits.id = ? AND habit_logs.log_date BETWEEN ? AND ?
            GROUP BY habits.id
        """, (habit_id, week_ago.isoformat(), today.isoformat()))
        
        result = self.cursor.fetchone()
        if result:
            name, total, completed, rate = result
            print(f"\n📊 Статистика за неделю - '{name}':")
            print(f"  ✓ Выполнено дней: {completed} из {total}")
            print(f"  📈 Процент успеха: {rate}%")
            return result
        else:
            print(f"✗ Нет данных за неделю для привычки {habit_id}")
            return None
    
    def get_monthly_stats(self, habit_id):
        """Статистика за месяц"""
        today = datetime.now().date()
        month_ago = today - timedelta(days=29)
        
        self.cursor.execute("""
            SELECT 
                habits.name,
                COUNT(habit_logs.id) as total_days,
                SUM(CASE WHEN habit_logs.completed = 1 THEN 1 ELSE 0 END) as completed_days,
                ROUND(SUM(CASE WHEN habit_logs.completed = 1 THEN 1 ELSE 0 END) * 100.0 / 
                      COUNT(habit_logs.id), 1) as success_rate
            FROM habits
            LEFT JOIN habit_logs ON habits.id = habit_logs.habit_id 
            WHERE habits.id = ? AND habit_logs.log_date BETWEEN ? AND ?
            GROUP BY habits.id
        """, (habit_id, month_ago.isoformat(), today.isoformat()))
        
        result = self.cursor.fetchone()
        if result:
            name, total, completed, rate = result
            print(f"\n📊 Статистика за месяц - '{name}':")
            print(f"  ✓ Выполнено дней: {completed} из {total}")
            print(f"  📈 Процент успеха: {rate}%")
            return result
        else:
            print(f"✗ Нет данных за месяц для привычки {habit_id}")
            return None
    
    def get_all_habits_stats(self):
        """Статистика по всем привычкам"""
        self.cursor.execute("""
            SELECT 
                habits.id,
                habits.name,
                COUNT(habit_logs.id) as total_logs,
                SUM(CASE WHEN habit_logs.completed = 1 THEN 1 ELSE 0 END) as completed,
                ROUND(SUM(CASE WHEN habit_logs.completed = 1 THEN 1 ELSE 0 END) * 100.0 / 
                      NULLIF(COUNT(habit_logs.id), 0), 1) as success_rate
            FROM habits
            LEFT JOIN habit_logs ON habits.id = habit_logs.habit_id
            WHERE habits.is_active = 1
            GROUP BY habits.id
            ORDER BY success_rate DESC
        """)
        
        results = self.cursor.fetchall()
        if results:
            print("\n📊 СТАТИСТИКА ПО ВСЕМ ПРИВЫЧКАМ:")
            for habit_id, name, total, completed, rate in results:
                rate = rate if rate else 0
                print(f"  {name}: {completed}/{total} дней ({rate}%)")
            return results
        else:
            print("✗ Нет привычек!")
            return []
    
    def get_longest_streak(self, habit_id):
        """Самая длинная серия выполнения привычки"""
        self.cursor.execute("""
            WITH streaks AS (
                SELECT 
                    log_date,
                    completed,
                    ROW_NUMBER() OVER (ORDER BY log_date) - 
                    ROW_NUMBER() OVER (PARTITION BY completed ORDER BY log_date) as streak_group
                FROM habit_logs
                WHERE habit_id = ? AND completed = 1
            ),
            streak_lengths AS (
                SELECT 
                    streak_group,
                    COUNT(*) as streak_length,
                    MIN(log_date) as start_date,
                    MAX(log_date) as end_date
                FROM streaks
                GROUP BY streak_group
            )
            SELECT 
                streak_length,
                start_date,
                end_date
            FROM streak_lengths
            ORDER BY streak_length DESC
            LIMIT 1
        """, (habit_id,))
        
        result = self.cursor.fetchone()
        self.cursor.execute("SELECT name FROM habits WHERE id = ?", (habit_id,))
        habit = self.cursor.fetchone()
        
        if result and habit:
            length, start, end = result
            print(f"\n🔥 Самая длинная серия - '{habit[0]}':")
            print(f"  📈 Длина: {length} дней")
            print(f"  📅 С {start} по {end}")
            return result
        else:
            print(f"✗ Нет данных о сериях для привычки {habit_id}")
            return None
    
    def get_reminder_habits(self):
        """Привычки, не выполнявшиеся более 2 дней"""
        today = datetime.now().date()
        two_days_ago = today - timedelta(days=2)
        
        self.cursor.execute("""
            SELECT 
                habits.id,
                habits.name,
                MAX(habit_logs.log_date) as last_completion,
                julianday(?) - julianday(MAX(habit_logs.log_date)) as days_passed
            FROM habits
            LEFT JOIN habit_logs ON habits.id = habit_logs.habit_id 
                AND habit_logs.completed = 1
            WHERE habits.is_active = 1
            GROUP BY habits.id
            HAVING days_passed > 2 OR MAX(habit_logs.log_date) IS NULL
            ORDER BY days_passed DESC
        """, (today.isoformat(),))
        
        results = self.cursor.fetchall()
        if results:
            print("\n🚨 НАПОМИНАНИЕ - Привычки не выполнялись более 2 дней:")
            for habit_id, name, last_date, days in results:
                if last_date:
                    print(f"  ⚠️  '{name}' - {days:.0f} дней не выполнялась (последний раз: {last_date})")
                else:
                    print(f"  ⚠️  '{name}' - ни разу не выполнялась")
            return results
        else:
            print("✓ Все привычки выполняются регулярно! 🎉")
            return []
    
    # ============ ДОСТИЖЕНИЯ ============
    
    def _check_achievements(self, habit_id):
        """Проверка и добавление достижений (бейджи)"""
        # Получаем статистику
        self.cursor.execute("""
            SELECT 
                COUNT(CASE WHEN completed = 1 THEN 1 END) as completed_count
            FROM habit_logs
            WHERE habit_id = ? AND completed = 1
        """, (habit_id,))
        
        result = self.cursor.fetchone()
        if not result:
            return
        
        completed_count = result[0]
        
        # Проверяем достижения
        achievements = [
            (7, "🎯 Неделяч", "Выполнил привычку 7 дней подряд!"),
            (30, "🏆 Месячник", "Выполнил привычку 30 дней!"),
            (100, "💯 Столетие", "Выполнил привычку 100 раз!"),
        ]
        
        for threshold, badge_name, description in achievements:
            if completed_count == threshold:
                self.cursor.execute("""
                    SELECT id FROM achievements 
                    WHERE habit_id = ? AND badge_name = ?
                """, (habit_id, badge_name))
                
                if not self.cursor.fetchone():
                    self.cursor.execute("""
                        INSERT INTO achievements (habit_id, badge_name, description)
                        VALUES (?, ?, ?)
                    """, (habit_id, badge_name, description))
                    self.conn.commit()
                    print(f"  🎉 ДОСТИЖЕНИЕ: {badge_name} - {description}")
    
    def get_achievements(self, habit_id):
        """Получение достижений привычки"""
        self.cursor.execute("""
            SELECT badge_name, description, achieved_at
            FROM achievements
            WHERE habit_id = ?
            ORDER BY achieved_at DESC
        """, (habit_id,))
        
        achievements = self.cursor.fetchall()
        if achievements:
            print(f"\n🏆 ДОСТИЖЕНИЯ:")
            for badge, desc, date in achievements:
                print(f"  {badge} - {desc} ({date})")
            return achievements
        return []
    
    # ============ ЭКСПОРТ ============
    
    def export_stats_to_file(self, filename="habit_stats.txt"):
        """Экспорт статистики в текстовый файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("СТАТИСТИКА ПРИВЫЧЕК\n")
                f.write(f"Дата создания отчёта: {datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
                
                # Все привычки
                self.cursor.execute("""
                    SELECT name, description, category, created_at, is_active
                    FROM habits
                    ORDER BY name
                """)
                
                habits = self.cursor.fetchall()
                for name, desc, cat, created, active in habits:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Привычка: {name}\n")
                    f.write(f"Статус: {'Активна' if active else 'Неактивна'}\n")
                    if cat:
                        f.write(f"Категория: {cat}\n")
                    if desc:
                        f.write(f"Описание: {desc}\n")
                    f.write(f"Создана: {created}\n")
                
                print(f"✓ Статистика экспортирована в {filename}")
                return True
        except Exception as e:
            print(f"✗ Ошибка при экспорте: {e}")
            return False
    
    # ============ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ============
    
    def _print_habit(self, habit):
        """Форматированный вывод привычки"""
        habit_id, name, desc, cat, freq, target, created, active = habit
        
        print(f"\n  ID: {habit_id}")
        print(f"  📌 Название: {name}")
        print(f"  📂 Категория: {cat if cat else 'Без категории'}")
        print(f"  🔄 Частота: {freq}")
        if target:
            print(f"  ⏰ Время: {target}")
        if desc:
            print(f"  ℹ️  Описание: {desc}")
        print(f"  ✅ Статус: {'Активна' if active else 'Неактивна'}")
        print(f"  📅 Создана: {created}")
        print("  " + "-" * 60)
    
    def _validate_habit(self, name):
        """Валидация названия привычки"""
        if not name or not isinstance(name, str):
            print("✗ Название должно быть непустой строкой!")
            return False
        return True
    
    def list_all_habits(self):
        """Вывод всех привычек"""
        self.cursor.execute(
            "SELECT * FROM habits ORDER BY created_at DESC"
        )
        habits = self.cursor.fetchall()
        
        if habits:
            print(f"\n📋 ВСЕ ПРИВЫЧКИ ({len(habits)} всего):")
            for habit in habits:
                self._print_habit(habit)
            return habits
        else:
            print("✗ Привычки не найдены!")
            return []
    
    # ============ КОНСОЛЬНОЕ МЕНЮ ============
    
    def show_menu(self):
        """Интерактивное меню"""
        while True:
            print("\n" + "=" * 60)
            print("📊 ТРЕКЕР ПРИВЫЧЕК - ГЛАВНОЕ МЕНЮ")
            print("=" * 60)
            print("1. ➕ Добавить новую привычку")
            print("2. 🔍 Просмотреть привычку")
            print("3. 📝 Редактировать привычку")
            print("4. ❌ Удалить привычку")
            print("5. ✅ Отметить выполнение")
            print("6. 📊 Статистика за неделю")
            print("7. 📊 Статистика за месяц")
            print("8. 📈 Статистика по всем привычкам")
            print("9. 🔥 Самая длинная серия")
            print("10. 🚨 Напоминания")
            print("11. 🏆 Достижения")
            print("12. 📋 Все привычки")
            print("13. 💾 Экспорт статистики")
            print("14. 🚀 Добавить тестовые данные")
            print("0. ❌ Выход")
            print("=" * 60)
            
            choice = input("Выберите действие (0-14): ").strip()
            
            if choice == "0":
                print("✓ До свидания!")
                break
            elif choice == "1":
                self._menu_create_habit()
            elif choice == "2":
                self._menu_read_habit()
            elif choice == "3":
                self._menu_update_habit()
            elif choice == "4":
                self._menu_delete_habit()
            elif choice == "5":
                self._menu_log_completion()
            elif choice == "6":
                self._menu_weekly_stats()
            elif choice == "7":
                self._menu_monthly_stats()
            elif choice == "8":
                self.get_all_habits_stats()
            elif choice == "9":
                self._menu_longest_streak()
            elif choice == "10":
                self.get_reminder_habits()
            elif choice == "11":
                self._menu_achievements()
            elif choice == "12":
                self.list_all_habits()
            elif choice == "13":
                self.export_stats_to_file()
            elif choice == "14":
                self._add_test_data()
            else:
                print("✗ Неверный выбор!")
    
    def _menu_create_habit(self):
        """Меню создания привычки"""
        print("\n--- Создание привычки ---")
        try:
            name = input("Название привычки: ").strip()
            category = input("Категория (здоровье, учеба, спорт и т.д.): ").strip()
            description = input("Описание (опционально): ").strip()
            frequency = input("Частота (daily, weekly и т.д., по умолчанию daily): ").strip() or "daily"
            target_time = input("Время выполнения, например '09:00' (опционально): ").strip()
            
            self.create_habit(name, description, category, frequency, target_time)
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def _menu_read_habit(self):
        """Меню просмотра привычки"""
        try:
            habit_id = int(input("Введите ID привычки: ").strip())
            self.read_habit(habit_id)
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _menu_update_habit(self):
        """Меню редактирования привычки"""
        try:
            habit_id = int(input("Введите ID привычки для редактирования: ").strip())
            print("Оставьте пустым, чтобы не менять")
            
            updates = {}
            name = input("Новое название: ").strip()
            if name:
                updates['name'] = name
            
            cat = input("Новая категория: ").strip()
            if cat:
                updates['category'] = cat
            
            desc = input("Новое описание: ").strip()
            if desc:
                updates['description'] = desc
            
            if updates:
                self.update_habit(habit_id, **updates)
            else:
                print("✗ Нет изменений!")
        except ValueError:
            print("✗ Ошибка: некорректный ввод!")
    
    def _menu_delete_habit(self):
        """Меню удаления привычки"""
        try:
            habit_id = int(input("Введите ID привычки для удаления: ").strip())
            confirm = input("Вы уверены? (да/нет): ").strip().lower()
            if confirm in ['да', 'yes', 'y']:
                self.delete_habit(habit_id)
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _menu_log_completion(self):
        """Меню логирования выполнения"""
        try:
            habit_id = int(input("Введите ID привычки: ").strip())
            note = input("Заметка (опционально): ").strip()
            self.log_habit_completion(habit_id, note=note)
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _menu_weekly_stats(self):
        """Меню статистики за неделю"""
        try:
            habit_id = int(input("Введите ID привычки: ").strip())
            self.get_weekly_stats(habit_id)
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _menu_monthly_stats(self):
        """Меню статистики за месяц"""
        try:
            habit_id = int(input("Введите ID привычки: ").strip())
            self.get_monthly_stats(habit_id)
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _menu_longest_streak(self):
        """Меню самой длинной серии"""
        try:
            habit_id = int(input("Введите ID привычки: ").strip())
            self.get_longest_streak(habit_id)
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _menu_achievements(self):
        """Меню достижений"""
        try:
            habit_id = int(input("Введите ID привычки: ").strip())
            self.get_achievements(habit_id)
        except ValueError:
            print("✗ Ошибка: ID должно быть числом!")
    
    def _add_test_data(self):
        """Добавление тестовых данных"""
        habits_data = [
            ("Зарядка", "Спорт", "Утренняя зарядка на 20 минут", "daily", "07:00"),
            ("Медитация", "Здоровье", "10 минут медитации", "daily", "20:00"),
            ("Чтение", "Учеба", "Чтение 30 минут в день", "daily", "21:00"),
            ("Бег", "Спорт", "Пробежка 5 км", "3x/week", "06:30"),
            ("Проверка целей", "Планирование", "Проверка прогресса", "weekly", "Sunday 19:00"),
        ]
        
        count = 0
        for name, cat, desc, freq, time in habits_data:
            if self.create_habit(name, desc, cat, freq, time):
                count += 1
        
        # Добавляем логи для примера
        today = datetime.now().date()
        for i in range(1, 6):
            habit_id = i
            for day in range(0, 30):
                log_date = (today - timedelta(days=day)).isoformat()
                # ~70% выполнения
                import random
                if random.random() < 0.7:
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO habit_logs 
                        (habit_id, log_date, completed) 
                        VALUES (?, ?, 1)
                    """, (habit_id, log_date))
            
            self.conn.commit()
        
        print(f"✓ Добавлено {count} тестовых привычек с логами!")


def main():
    """Главная функция"""
    print("🚀 Запуск приложения 'Трекер привычек'...\n")
    
    tracker = HabitTracker()
    
    try:
        tracker.show_menu()
    except KeyboardInterrupt:
        print("\n\n✓ Программа прервана пользователем!")
    finally:
        tracker.close()


if __name__ == "__main__":
    main()
