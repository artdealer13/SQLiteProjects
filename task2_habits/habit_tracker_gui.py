#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI for "Трекер привычек" using Tkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from habit_tracker import HabitTracker


class HabitTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Трекер привычек")
        self.root.geometry("1000x700")

        self.app = HabitTracker()
        self._setup_style()
        self._build_ui()
        self.refresh_habits()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_style(self):
        style = ttk.Style(self.root)
        style.configure("Treeview", rowheight=40, font=("DejaVu Sans", 10))
        style.configure("Treeview.Heading", font=("DejaVu Sans", 10, "bold"))

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_habits = ttk.Frame(self.notebook)
        self.tab_logs = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_habits, text="Привычки")
        self.notebook.add(self.tab_logs, text="Логи")
        self.notebook.add(self.tab_reports, text="Отчеты")

        self._build_habits_tab()
        self._build_logs_tab()
        self._build_reports_tab()

    def _build_habits_tab(self):
        form = ttk.LabelFrame(self.tab_habits, text="Привычка")
        form.pack(fill=tk.X, padx=10, pady=10)

        self.habit_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.cat_var = tk.StringVar()
        self.freq_var = tk.StringVar(value="daily")
        self.time_var = tk.StringVar()

        fields = [
            ("ID", self.habit_id_var),
            ("Название", self.name_var),
            ("Описание", self.desc_var),
            ("Категория", self.cat_var),
            ("Частота", self.freq_var),
            ("Время", self.time_var),
        ]

        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
            ttk.Entry(form, textvariable=var, width=60).grid(row=i, column=1, sticky=tk.W, padx=6, pady=4)

        btns = ttk.Frame(form)
        btns.grid(row=0, column=2, rowspan=6, padx=10, pady=4, sticky=tk.N)

        ttk.Button(btns, text="Добавить", command=self.add_habit).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Обновить", command=self.update_habit).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Удалить", command=self.delete_habit).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Очистить", command=self.clear_form).pack(fill=tk.X, pady=2)

        table_frame = ttk.LabelFrame(self.tab_habits, text="Список привычек")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "name", "category", "frequency", "active")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for col, label in zip(columns, ["ID", "Название", "Категория", "Частота", "Активна"]):
            self.tree.heading(col, text=label)
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("active", width=70, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        actions = ttk.Frame(self.tab_habits)
        actions.pack(pady=4)
        ttk.Button(actions, text="Обновить список", command=self.refresh_habits).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Загрузить тестовые данные", command=self.load_test_data).pack(side=tk.LEFT, padx=6)

    def _build_logs_tab(self):
        logs = ttk.LabelFrame(self.tab_logs, text="Логирование")
        logs.pack(fill=tk.X, padx=10, pady=10)

        self.log_habit_id_var = tk.StringVar()
        self.log_date_var = tk.StringVar()
        self.log_note_var = tk.StringVar()

        ttk.Label(logs, text="ID привычки").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(logs, textvariable=self.log_habit_id_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(logs, text="Дата (YYYY-MM-DD)").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(logs, textvariable=self.log_date_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(logs, text="Заметка").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(logs, textvariable=self.log_note_var, width=50).grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Button(logs, text="Отметить выполнение", command=self.log_completion).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(logs, text="Отменить", command=self.unlog_completion).grid(row=1, column=2, padx=6, pady=4)

    def _build_reports_tab(self):
        reports = ttk.LabelFrame(self.tab_reports, text="Отчеты")
        reports.pack(fill=tk.X, padx=10, pady=10)

        self.report_id_var = tk.StringVar()
        ttk.Label(reports, text="ID привычки").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(reports, textvariable=self.report_id_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Button(reports, text="Статистика за неделю", command=self.weekly_stats).grid(row=1, column=0, padx=6, pady=4)
        ttk.Button(reports, text="Статистика за месяц", command=self.monthly_stats).grid(row=1, column=1, padx=6, pady=4)
        ttk.Button(reports, text="Статистика по всем", command=self.all_stats).grid(row=1, column=2, padx=6, pady=4)

        ttk.Button(reports, text="Самая длинная серия", command=self.longest_streak).grid(row=2, column=0, padx=6, pady=4)
        ttk.Button(reports, text="Напоминания", command=self.reminders).grid(row=2, column=1, padx=6, pady=4)
        ttk.Button(reports, text="Достижения", command=self.achievements).grid(row=2, column=2, padx=6, pady=4)

        ttk.Button(reports, text="Экспорт в файл", command=self.export_stats).grid(row=3, column=0, padx=6, pady=6)

        self.output = tk.Text(self.tab_reports, height=18, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def refresh_habits(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        habits = self.app.list_all_habits()
        for h in habits:
            active = "Да" if h[7] else "Нет"
            self.tree.insert("", tk.END, values=(h[0], h[1], h[3], h[4], active))

    def load_test_data(self):
        self.app._add_test_data()
        self.refresh_habits()
        messagebox.showinfo("Готово", "Тестовые данные загружены.")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        habit_id = int(values[0])
        habit = self.app.read_habit(habit_id)
        if habit:
            self.habit_id_var.set(habit[0])
            self.name_var.set(habit[1])
            self.desc_var.set(habit[2] or "")
            self.cat_var.set(habit[3] or "")
            self.freq_var.set(habit[4] or "")
            self.time_var.set(habit[5] or "")

    def clear_form(self):
        for var in [self.habit_id_var, self.name_var, self.desc_var, self.cat_var, self.freq_var, self.time_var]:
            var.set("")

    def add_habit(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Название обязательно.")
            return
        if self.app.create_habit(
            name,
            self.desc_var.get().strip(),
            self.cat_var.get().strip(),
            self.freq_var.get().strip() or "daily",
            self.time_var.get().strip(),
        ):
            self.refresh_habits()

    def update_habit(self):
        try:
            habit_id = int(self.habit_id_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректный ID.")
            return
        updates = {}
        if self.name_var.get().strip():
            updates["name"] = self.name_var.get().strip()
        if self.desc_var.get().strip():
            updates["description"] = self.desc_var.get().strip()
        if self.cat_var.get().strip():
            updates["category"] = self.cat_var.get().strip()
        if self.freq_var.get().strip():
            updates["frequency"] = self.freq_var.get().strip()
        if self.time_var.get().strip():
            updates["target_time"] = self.time_var.get().strip()
        if updates and self.app.update_habit(habit_id, **updates):
            self.refresh_habits()

    def delete_habit(self):
        try:
            habit_id = int(self.habit_id_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректный ID.")
            return
        if messagebox.askyesno("Подтверждение", "Удалить привычку?"):
            if self.app.delete_habit(habit_id):
                self.refresh_habits()
                self.clear_form()

    def log_completion(self):
        try:
            habit_id = int(self.log_habit_id_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректный ID.")
            return
        date_str = self.log_date_var.get().strip() or None
        note = self.log_note_var.get().strip()
        self.app.log_habit_completion(habit_id, log_date=date_str, note=note)

    def unlog_completion(self):
        try:
            habit_id = int(self.log_habit_id_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректный ID.")
            return
        date_str = self.log_date_var.get().strip() or None
        self.app.unlog_habit_completion(habit_id, log_date=date_str)

    def _write_output(self, title, lines):
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, title + "\n")
        self.output.insert(tk.END, "-" * 60 + "\n")
        for line in lines:
            self.output.insert(tk.END, line + "\n")

    def weekly_stats(self):
        habit_id = self._get_report_id()
        if habit_id is None:
            return
        result = self.app.get_weekly_stats(habit_id)
        if result:
            name, total, completed, rate = result
            self._write_output("Статистика за неделю", [f"{name}: {completed}/{total} дней ({rate}%)"])

    def monthly_stats(self):
        habit_id = self._get_report_id()
        if habit_id is None:
            return
        result = self.app.get_monthly_stats(habit_id)
        if result:
            name, total, completed, rate = result
            self._write_output("Статистика за месяц", [f"{name}: {completed}/{total} дней ({rate}%)"])

    def all_stats(self):
        results = self.app.get_all_habits_stats()
        lines = [f"{name}: {completed}/{total} дней ({rate or 0}%)" for _, name, total, completed, rate in results]
        self._write_output("Статистика по всем привычкам", lines)

    def longest_streak(self):
        habit_id = self._get_report_id()
        if habit_id is None:
            return
        result = self.app.get_longest_streak(habit_id)
        if result:
            length, start, end = result
            self._write_output("Самая длинная серия", [f"{length} дней: {start} - {end}"])

    def reminders(self):
        results = self.app.get_reminder_habits()
        lines = []
        for _, name, last_date, days in results:
            if last_date:
                lines.append(f"{name}: {days:.0f} дней без выполнения (последний раз {last_date})")
            else:
                lines.append(f"{name}: ни разу не выполнялась")
        self._write_output("Напоминания", lines or ["Нет просроченных привычек"])

    def achievements(self):
        habit_id = self._get_report_id()
        if habit_id is None:
            return
        results = self.app.get_achievements(habit_id)
        lines = [f"{badge} - {desc} ({date})" for badge, desc, date in results]
        self._write_output("Достижения", lines or ["Пока нет достижений"])

    def export_stats(self):
        filename = filedialog.asksaveasfilename(
            title="Сохранить отчет",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
        )
        if filename:
            if self.app.export_stats_to_file(filename):
                messagebox.showinfo("Готово", f"Отчет сохранен: {filename}")

    def _get_report_id(self):
        try:
            return int(self.report_id_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректный ID привычки.")
            return None

    def on_close(self):
        self.app.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    HabitTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
