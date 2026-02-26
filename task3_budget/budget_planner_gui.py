#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI for "Бюджетный планировщик" using Tkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from budget_planner import BudgetPlanner


class BudgetPlannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Бюджетный планировщик")
        self.root.geometry("1100x720")

        self.app = BudgetPlanner()
        self._setup_style()
        self._build_ui()
        self.refresh_categories()
        self.refresh_transactions()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_style(self):
        style = ttk.Style(self.root)
        style.configure("Treeview", rowheight=36, font=("DejaVu Sans", 10))
        style.configure("Treeview.Heading", font=("DejaVu Sans", 10, "bold"))

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_categories = ttk.Frame(self.notebook)
        self.tab_transactions = ttk.Frame(self.notebook)
        self.tab_budgets = ttk.Frame(self.notebook)
        self.tab_goals = ttk.Frame(self.notebook)
        self.tab_analytics = ttk.Frame(self.notebook)
        self.tab_recurring = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_categories, text="Категории")
        self.notebook.add(self.tab_transactions, text="Транзакции")
        self.notebook.add(self.tab_budgets, text="Бюджеты")
        self.notebook.add(self.tab_goals, text="Цели")
        self.notebook.add(self.tab_analytics, text="Аналитика")
        self.notebook.add(self.tab_recurring, text="Регулярные")

        self._build_categories_tab()
        self._build_transactions_tab()
        self._build_budgets_tab()
        self._build_goals_tab()
        self._build_analytics_tab()
        self._build_recurring_tab()

    def _build_categories_tab(self):
        form = ttk.LabelFrame(self.tab_categories, text="Категория")
        form.pack(fill=tk.X, padx=10, pady=10)

        self.cat_name_var = tk.StringVar()
        self.cat_type_var = tk.StringVar(value="expense")
        self.cat_parent_var = tk.StringVar()
        self.cat_desc_var = tk.StringVar()

        ttk.Label(form, text="Название").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.cat_name_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Тип (income/expense)").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.cat_type_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Родитель ID (опц.)").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.cat_parent_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Описание").grid(row=3, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.cat_desc_var, width=50).grid(row=3, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Button(form, text="Добавить", command=self.add_category).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(form, text="Обновить список", command=self.refresh_categories).grid(row=1, column=2, padx=6, pady=4)
        ttk.Button(form, text="Загрузить тестовые", command=self.load_test_data).grid(row=2, column=2, padx=6, pady=4)

        table_frame = ttk.LabelFrame(self.tab_categories, text="Иерархия категорий")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "name", "type", "parent")
        self.cat_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for col, label in zip(columns, ["ID", "Название", "Тип", "Родитель"]):
            self.cat_tree.heading(col, text=label)
        self.cat_tree.column("id", width=60, anchor=tk.CENTER, stretch=False)
        self.cat_tree.column("name", width=260, anchor=tk.W)
        self.cat_tree.column("type", width=120, anchor=tk.W, stretch=False)
        self.cat_tree.column("parent", width=90, anchor=tk.CENTER, stretch=False)
        self.cat_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    def _build_transactions_tab(self):
        form = ttk.LabelFrame(self.tab_transactions, text="Транзакция")
        form.pack(fill=tk.X, padx=10, pady=10)

        self.tr_id_var = tk.StringVar()
        self.tr_cat_var = tk.StringVar()
        self.tr_amount_var = tk.StringVar()
        self.tr_date_var = tk.StringVar(value=datetime.now().date().isoformat())
        self.tr_desc_var = tk.StringVar()

        ttk.Label(form, text="ID транзакции").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.tr_id_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="ID категории").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.tr_cat_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Сумма").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.tr_amount_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Дата").grid(row=3, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.tr_date_var, width=20).grid(row=3, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Описание").grid(row=4, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.tr_desc_var, width=50).grid(row=4, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Button(form, text="Добавить", command=self.add_transaction).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(form, text="Обновить", command=self.update_transaction).grid(row=1, column=2, padx=6, pady=4)
        ttk.Button(form, text="Удалить", command=self.delete_transaction).grid(row=2, column=2, padx=6, pady=4)

        table_frame = ttk.LabelFrame(self.tab_transactions, text="Последние транзакции")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "date", "category", "amount", "desc")
        self.tr_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for col, label in zip(columns, ["ID", "Дата", "Категория", "Сумма", "Описание"]):
            self.tr_tree.heading(col, text=label)
        self.tr_tree.column("id", width=60, anchor=tk.CENTER, stretch=False)
        self.tr_tree.column("date", width=110, anchor=tk.CENTER, stretch=False)
        self.tr_tree.column("category", width=180, anchor=tk.W)
        self.tr_tree.column("amount", width=110, anchor=tk.E, stretch=False)
        self.tr_tree.column("desc", width=320, anchor=tk.W)
        self.tr_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        ttk.Button(self.tab_transactions, text="Обновить список", command=self.refresh_transactions).pack(pady=4)

    def _build_budgets_tab(self):
        form = ttk.LabelFrame(self.tab_budgets, text="Бюджет")
        form.pack(fill=tk.X, padx=10, pady=10)

        self.budget_cat_var = tk.StringVar()
        self.budget_month_var = tk.StringVar(value=datetime.now().strftime("%Y-%m"))
        self.budget_amount_var = tk.StringVar()

        ttk.Label(form, text="ID категории").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.budget_cat_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Месяц (YYYY-MM)").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.budget_month_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Сумма").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.budget_amount_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Button(form, text="Установить", command=self.set_budget).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(form, text="Анализ бюджета", command=self.budget_analysis).grid(row=1, column=2, padx=6, pady=4)

        self.budget_output = tk.Text(self.tab_budgets, height=14, wrap=tk.WORD)
        self.budget_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_goals_tab(self):
        form = ttk.LabelFrame(self.tab_goals, text="Финансовая цель")
        form.pack(fill=tk.X, padx=10, pady=10)

        self.goal_id_var = tk.StringVar()
        self.goal_name_var = tk.StringVar()
        self.goal_target_var = tk.StringVar()
        self.goal_current_var = tk.StringVar()
        self.goal_date_var = tk.StringVar()
        self.goal_priority_var = tk.StringVar(value="normal")

        ttk.Label(form, text="ID цели").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.goal_id_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Название").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.goal_name_var, width=40).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Целевая сумма").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.goal_target_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Текущая сумма").grid(row=3, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.goal_current_var, width=20).grid(row=3, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Дата цели (YYYY-MM-DD)").grid(row=4, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.goal_date_var, width=20).grid(row=4, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Приоритет").grid(row=5, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.goal_priority_var, width=20).grid(row=5, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Button(form, text="Создать", command=self.create_goal).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(form, text="Обновить прогресс", command=self.update_goal).grid(row=1, column=2, padx=6, pady=4)
        ttk.Button(form, text="Показать прогресс", command=self.show_goals).grid(row=2, column=2, padx=6, pady=4)
        ttk.Button(form, text="Прогноз", command=self.goal_forecast).grid(row=3, column=2, padx=6, pady=4)

        self.goal_output = tk.Text(self.tab_goals, height=14, wrap=tk.WORD)
        self.goal_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_analytics_tab(self):
        form = ttk.LabelFrame(self.tab_analytics, text="Аналитика")
        form.pack(fill=tk.X, padx=10, pady=10)

        self.report_start_var = tk.StringVar()
        self.report_end_var = tk.StringVar()
        self.report_year_var = tk.StringVar(value=str(datetime.now().year))
        self.report_month_var = tk.StringVar(value=datetime.now().strftime("%Y-%m"))

        ttk.Label(form, text="С (YYYY-MM-DD)").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.report_start_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="По (YYYY-MM-DD)").grid(row=0, column=2, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.report_end_var, width=15).grid(row=0, column=3, sticky=tk.W, padx=6, pady=4)

        ttk.Button(form, text="Отчет за период", command=self.report_period).grid(row=0, column=4, padx=6, pady=4)

        ttk.Label(form, text="Год (YYYY)").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.report_year_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)
        ttk.Button(form, text="Динамика по месяцам", command=self.report_dynamics).grid(row=1, column=2, padx=6, pady=4)

        ttk.Label(form, text="Месяц (YYYY-MM)").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.report_month_var, width=15).grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)
        ttk.Button(form, text="Сравнение с прошлым", command=self.report_compare).grid(row=2, column=2, padx=6, pady=4)

        self.analytics_output = tk.Text(self.tab_analytics, height=16, wrap=tk.WORD)
        self.analytics_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_recurring_tab(self):
        form = ttk.LabelFrame(self.tab_recurring, text="Регулярные транзакции")
        form.pack(fill=tk.X, padx=10, pady=10)

        self.rec_cat_var = tk.StringVar()
        self.rec_amount_var = tk.StringVar()
        self.rec_desc_var = tk.StringVar()
        self.rec_freq_var = tk.StringVar(value="monthly")

        ttk.Label(form, text="ID категории").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.rec_cat_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Сумма").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.rec_amount_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Описание").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.rec_desc_var, width=40).grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(form, text="Частота (daily/weekly/monthly)").grid(row=3, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(form, textvariable=self.rec_freq_var, width=20).grid(row=3, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Button(form, text="Создать", command=self.create_recurring).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(form, text="Обработать", command=self.process_recurring).grid(row=1, column=2, padx=6, pady=4)

    def add_category(self):
        name = self.cat_name_var.get().strip()
        cat_type = self.cat_type_var.get().strip()
        parent = self.cat_parent_var.get().strip()
        desc = self.cat_desc_var.get().strip()
        parent_id = int(parent) if parent else None
        if self.app.create_category(name, cat_type, parent_id, desc):
            self.refresh_categories()

    def refresh_categories(self):
        for row in self.cat_tree.get_children():
            self.cat_tree.delete(row)
        categories = self.app.list_categories()
        for cat in categories:
            self.cat_tree.insert("", tk.END, values=(cat[0], cat[1], cat[3], cat[2]))

    def load_test_data(self):
        self.app._add_test_data()
        self.refresh_categories()
        self.refresh_transactions()
        messagebox.showinfo("Готово", "Тестовые данные загружены.")

    def add_transaction(self):
        try:
            cat_id = int(self.tr_cat_var.get().strip())
            amount = float(self.tr_amount_var.get().strip())
            date = self.tr_date_var.get().strip()
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте ID категории и сумму.")
            return
        desc = self.tr_desc_var.get().strip()
        if self.app.create_transaction(cat_id, amount, desc, date):
            self.refresh_transactions()

    def update_transaction(self):
        try:
            tr_id = int(self.tr_id_var.get().strip())
            amount = float(self.tr_amount_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте ID и сумму.")
            return
        if self.app.update_transaction(tr_id, amount=amount):
            self.refresh_transactions()

    def delete_transaction(self):
        try:
            tr_id = int(self.tr_id_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректный ID.")
            return
        if messagebox.askyesno("Подтверждение", "Удалить транзакцию?"):
            if self.app.delete_transaction(tr_id):
                self.refresh_transactions()

    def refresh_transactions(self):
        for row in self.tr_tree.get_children():
            self.tr_tree.delete(row)
        self.app.cursor.execute("""
            SELECT t.id, t.transaction_date, c.name, t.amount, t.description
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            ORDER BY t.transaction_date DESC, t.id DESC
            LIMIT 50
        """)
        rows = self.app.cursor.fetchall()
        for r in rows:
            self.tr_tree.insert("", tk.END, values=r)

    def set_budget(self):
        try:
            cat_id = int(self.budget_cat_var.get().strip())
            month = self.budget_month_var.get().strip()
            amount = float(self.budget_amount_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте поля бюджета.")
            return
        self.app.set_budget(cat_id, month, amount)

    def budget_analysis(self):
        month = self.budget_month_var.get().strip()
        results = self.app.get_budget_analysis(month)
        lines = []
        for _, name, budget, spent, remaining, utilization in results:
            utilization = utilization if utilization is not None else 0
            lines.append(f"{name}: бюджет {budget:.0f}, потрачено {spent:.0f}, остаток {remaining:.0f}, {utilization:.1f}%")
        self._write_text(self.budget_output, f"Анализ бюджета {month}", lines)

    def create_goal(self):
        try:
            name = self.goal_name_var.get().strip()
            target = float(self.goal_target_var.get().strip())
            date = self.goal_date_var.get().strip()
            priority = self.goal_priority_var.get().strip() or "normal"
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте значения цели.")
            return
        self.app.create_financial_goal(name, target, date, priority)

    def update_goal(self):
        try:
            goal_id = int(self.goal_id_var.get().strip())
            current = float(self.goal_current_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте ID и сумму.")
            return
        self.app.update_goal_progress(goal_id, current)

    def show_goals(self):
        goals = self.app.get_goals_progress()
        lines = []
        for _, name, target, current, target_date, priority in goals:
            percent = (current / target * 100) if target else 0
            lines.append(f"{name} ({priority}) {percent:.0f}%: {current:.0f}/{target:.0f}, срок {target_date}")
        self._write_text(self.goal_output, "Прогресс целей", lines)

    def goal_forecast(self):
        try:
            goal_id = int(self.goal_id_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректный ID цели.")
            return
        forecast = self.app.forecast_accumulation(goal_id)
        if forecast is not None:
            self._write_text(self.goal_output, "Прогноз", [f"Прогнозируемая сумма: {forecast:.2f}"])

    def report_period(self):
        start = self.report_start_var.get().strip()
        end = self.report_end_var.get().strip()
        if not start or not end:
            messagebox.showerror("Ошибка", "Введите период.")
            return
        results = self.app.get_period_report(start, end)
        lines = [f"{name}: {total:.2f} ({cat_type})" for name, cat_type, total in results]
        self._write_text(self.analytics_output, f"Отчет {start} - {end}", lines)

    def report_dynamics(self):
        year = self.report_year_var.get().strip()
        results = self.app.get_monthly_dynamics(year)
        lines = [f"{month}: {cat_type} {total:.2f}" for month, cat_type, total in results]
        self._write_text(self.analytics_output, f"Динамика {year}", lines)

    def report_compare(self):
        month = self.report_month_var.get().strip()
        results = self.app.compare_with_previous_period(month)
        lines = [f"{name} {period}: {total:.2f} ({cat_type})" for name, cat_type, period, total in results]
        self._write_text(self.analytics_output, f"Сравнение {month}", lines)

    def create_recurring(self):
        try:
            cat_id = int(self.rec_cat_var.get().strip())
            amount = float(self.rec_amount_var.get().strip())
            desc = self.rec_desc_var.get().strip()
            freq = self.rec_freq_var.get().strip()
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте поля регулярной транзакции.")
            return
        self.app.create_recurring_transaction(cat_id, amount, desc, freq)

    def process_recurring(self):
        count = self.app.process_recurring_transactions()
        messagebox.showinfo("Готово", f"Обработано транзакций: {count}")
        self.refresh_transactions()

    def _write_text(self, widget, title, lines):
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, title + "\n")
        widget.insert(tk.END, "-" * 60 + "\n")
        for line in lines:
            widget.insert(tk.END, line + "\n")

    def on_close(self):
        self.app.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    BudgetPlannerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
