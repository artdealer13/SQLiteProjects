#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI for "Книга рецептов" using Tkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from recipe_book import RecipeBook


class RecipeBookGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Книга рецептов")
        self.root.geometry("980x640")

        self.app = RecipeBook()
        self._build_ui()
        self.refresh_list()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_crud = ttk.Frame(self.notebook)
        self.tab_search = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_crud, text="CRUD")
        self.notebook.add(self.tab_search, text="Поиск и отчеты")

        self._build_crud_tab()
        self._build_search_tab()

    def _build_crud_tab(self):
        form = ttk.LabelFrame(self.tab_crud, text="Рецепт")
        form.pack(fill=tk.X, padx=10, pady=10)

        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.ingredients_var = tk.StringVar()
        self.time_var = tk.StringVar()
        self.rating_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.id_var = tk.StringVar()

        fields = [
            ("ID", self.id_var),
            ("Название", self.name_var),
            ("Категория", self.category_var),
            ("Ингредиенты", self.ingredients_var),
            ("Время (мин)", self.time_var),
            ("Рейтинг (1-5)", self.rating_var),
            ("Описание", self.desc_var),
        ]

        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
            ttk.Entry(form, textvariable=var, width=60).grid(row=i, column=1, sticky=tk.W, padx=6, pady=4)

        btns = ttk.Frame(form)
        btns.grid(row=0, column=2, rowspan=7, padx=10, pady=4, sticky=tk.N)

        ttk.Button(btns, text="Добавить", command=self.add_recipe).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Обновить", command=self.update_recipe).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Удалить", command=self.delete_recipe).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Очистить", command=self.clear_form).pack(fill=tk.X, pady=2)

        table_frame = ttk.LabelFrame(self.tab_crud, text="Список рецептов")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "name", "category", "time", "rating")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for col, label in zip(columns, ["ID", "Название", "Категория", "Время", "Рейтинг"]):
            self.tree.heading(col, text=label)
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("time", width=80, anchor=tk.CENTER)
        self.tree.column("rating", width=80, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        ttk.Button(self.tab_crud, text="Обновить список", command=self.refresh_list).pack(pady=4)

    def _build_search_tab(self):
        search = ttk.LabelFrame(self.tab_search, text="Поиск")
        search.pack(fill=tk.X, padx=10, pady=10)

        self.search_cat_var = tk.StringVar()
        self.search_name_var = tk.StringVar()
        self.search_time_var = tk.StringVar()

        ttk.Label(search, text="Категория").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(search, textvariable=self.search_cat_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)
        ttk.Button(search, text="Найти", command=self.search_by_category).grid(row=0, column=2, padx=6, pady=4)

        ttk.Label(search, text="Название содержит").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(search, textvariable=self.search_name_var, width=30).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)
        ttk.Button(search, text="Найти", command=self.search_by_name).grid(row=1, column=2, padx=6, pady=4)

        ttk.Label(search, text="Макс. время (мин)").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(search, textvariable=self.search_time_var, width=30).grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)
        ttk.Button(search, text="Найти", command=self.search_by_time).grid(row=2, column=2, padx=6, pady=4)

        reports = ttk.LabelFrame(self.tab_search, text="Отчеты")
        reports.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(reports, text="Топ-5 рецептов", command=self.show_top5).grid(row=0, column=0, padx=6, pady=6)
        ttk.Button(reports, text="Статистика по категориям", command=self.show_stats).grid(row=0, column=1, padx=6, pady=6)

        self.output = tk.Text(self.tab_search, height=16, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        recipes = self.app.list_all_recipes()
        for r in recipes:
            self.tree.insert("", tk.END, values=(r[0], r[1], r[2], r[4], r[5]))

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        recipe_id = int(values[0])
        recipe = self.app.read_recipe(recipe_id)
        if recipe:
            self.id_var.set(recipe[0])
            self.name_var.set(recipe[1])
            self.category_var.set(recipe[2])
            self.ingredients_var.set(recipe[3])
            self.time_var.set(recipe[4])
            self.rating_var.set(recipe[5])
            self.desc_var.set(recipe[6] or "")

    def clear_form(self):
        for var in [self.id_var, self.name_var, self.category_var, self.ingredients_var, self.time_var, self.rating_var, self.desc_var]:
            var.set("")

    def add_recipe(self):
        try:
            name = self.name_var.get().strip()
            category = self.category_var.get().strip()
            ingredients = self.ingredients_var.get().strip()
            cooking_time = int(self.time_var.get().strip())
            rating = float(self.rating_var.get().strip() or 5)
            description = self.desc_var.get().strip()
            if self.app.create_recipe(name, category, ingredients, cooking_time, rating, description):
                self.refresh_list()
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте числовые поля (время, рейтинг).")

    def update_recipe(self):
        try:
            recipe_id = int(self.id_var.get().strip())
            updates = {}
            if self.name_var.get().strip():
                updates["name"] = self.name_var.get().strip()
            if self.category_var.get().strip():
                updates["category"] = self.category_var.get().strip()
            if self.ingredients_var.get().strip():
                updates["ingredients"] = self.ingredients_var.get().strip()
            if self.time_var.get().strip():
                updates["cooking_time"] = int(self.time_var.get().strip())
            if self.rating_var.get().strip():
                updates["rating"] = float(self.rating_var.get().strip())
            if self.desc_var.get().strip():
                updates["description"] = self.desc_var.get().strip()
            if updates and self.app.update_recipe(recipe_id, **updates):
                self.refresh_list()
        except ValueError:
            messagebox.showerror("Ошибка", "ID и числовые поля должны быть корректными.")

    def delete_recipe(self):
        try:
            recipe_id = int(self.id_var.get().strip())
            if messagebox.askyesno("Подтверждение", "Удалить рецепт?"):
                if self.app.delete_recipe(recipe_id):
                    self.refresh_list()
                    self.clear_form()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректный ID.")

    def _write_output(self, title, lines):
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, title + "\n")
        self.output.insert(tk.END, "-" * 60 + "\n")
        for line in lines:
            self.output.insert(tk.END, line + "\n")

    def search_by_category(self):
        cat = self.search_cat_var.get().strip()
        results = self.app.search_by_category(cat)
        lines = [f"{r[1]} | {r[2]} | {r[4]} мин | {r[5]}/5" for r in results]
        self._write_output(f"Категория: {cat}", lines)

    def search_by_name(self):
        name_part = self.search_name_var.get().strip()
        results = self.app.search_by_name(name_part)
        lines = [f"{r[1]} | {r[2]} | {r[4]} мин | {r[5]}/5" for r in results]
        self._write_output(f"Название содержит: {name_part}", lines)

    def search_by_time(self):
        try:
            max_time = int(self.search_time_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число минут.")
            return
        results = self.app.search_by_max_time(max_time)
        lines = [f"{r[1]} | {r[2]} | {r[4]} мин | {r[5]}/5" for r in results]
        self._write_output(f"До {max_time} минут", lines)

    def show_top5(self):
        results = self.app.get_top_5_recipes()
        lines = [f"{i+1}. {r[1]} | {r[5]}/5 | {r[4]} мин" for i, r in enumerate(results)]
        self._write_output("ТОП-5 рецептов", lines)

    def show_stats(self):
        results = self.app.get_category_statistics()
        lines = [f"{cat}: {count} рецептов, средний рейтинг {avg:.1f}/5" for cat, count, avg in results]
        self._write_output("Статистика по категориям", lines)

    def on_close(self):
        self.app.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    RecipeBookGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
