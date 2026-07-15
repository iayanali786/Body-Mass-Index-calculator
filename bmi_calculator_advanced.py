"""
BMI Calculator - Advanced Tier
--------------------------------
A desktop GUI application (tkinter) that calculates BMI, stores every
result per named user in an SQLite database, and can plot a user's
BMI trend over time with matplotlib.

Run with:  python bmi_calculator_advanced.py
"""

import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

DB_FILE = "bmi_records.db"


# --------------------------------------------------------------------------
# Database layer
# --------------------------------------------------------------------------
class BMIDatabase:
    """Handles all reads/writes to the SQLite database, with error handling
    so a locked or corrupted file doesn't crash the whole app."""

    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        weight REAL NOT NULL,
                        height REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        recorded_at TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not set up database:\n{e}")

    def add_record(self, username, weight, height, bmi, category):
        try:
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO records
                       (username, weight, height, bmi, category, recorded_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (username, weight, height, bmi, category,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not save record:\n{e}")
            return False

    def get_users(self):
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT username FROM records ORDER BY username"
                ).fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load users:\n{e}")
            return []

    def get_history(self, username):
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """SELECT recorded_at, bmi FROM records
                       WHERE username = ? ORDER BY recorded_at""",
                    (username,),
                ).fetchall()
            return rows
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load history:\n{e}")
            return []


# --------------------------------------------------------------------------
# BMI logic (same rules as the beginner tier)
# --------------------------------------------------------------------------
def calculate_bmi(weight_kg, height_m):
    return round(weight_kg / (height_m ** 2), 2)


def classify_bmi(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


CATEGORY_COLORS = {
    "Underweight": "#3B82F6",    # blue
    "Normal weight": "#22C55E",  # green
    "Overweight": "#F59E0B",     # amber
    "Obese": "#EF4444",          # red
}


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
class BMIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator - Advanced")
        self.geometry("480x560")
        self.resizable(False, False)
        self.configure(bg="#F3F4F6")

        self.db = BMIDatabase()

        self._build_input_section()
        self._build_result_section()
        self._build_history_section()

    # ---- UI construction -------------------------------------------------
    def _build_input_section(self):
        frame = tk.Frame(self, bg="#F3F4F6", padx=20, pady=20)
        frame.pack(fill="x")

        tk.Label(frame, text="BMI Calculator", font=("Segoe UI", 18, "bold"),
                  bg="#F3F4F6").grid(row=0, column=0, columnspan=2, pady=(0, 15))

        tk.Label(frame, text="Name:", bg="#F3F4F6", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.name_var, width=25).grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Weight (kg):", bg="#F3F4F6", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        self.weight_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.weight_var, width=25).grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Height (m):", bg="#F3F4F6", anchor="w").grid(row=3, column=0, sticky="w", pady=5)
        self.height_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.height_var, width=25).grid(row=3, column=1, pady=5)

        tk.Button(frame, text="Calculate", command=self.on_calculate,
                  bg="#2563EB", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=10, pady=5).grid(row=4, column=0, columnspan=2, pady=(15, 0))

    def _build_result_section(self):
        self.result_frame = tk.Frame(self, bg="#FFFFFF", padx=20, pady=15)
        self.result_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.result_label = tk.Label(self.result_frame, text="Enter your details above",
                                      font=("Segoe UI", 12), bg="#FFFFFF")
        self.result_label.pack()

    def _build_history_section(self):
        frame = tk.Frame(self, bg="#F3F4F6", padx=20, pady=5)
        frame.pack(fill="both", expand=True)

        tk.Button(frame, text="Show BMI Trend Graph", command=self.on_show_graph,
                  bg="#059669", fg="white", relief="flat", padx=10, pady=5).pack(pady=5)

        self.graph_container = tk.Frame(frame, bg="#F3F4F6")
        self.graph_container.pack(fill="both", expand=True)

    # ---- event handlers ----------------------------------------------------
    def on_calculate(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Please enter a name so your record can be saved.")
            return

        # Validate weight
        try:
            weight = float(self.weight_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Weight", "Weight must be a number, e.g. 65.5")
            return

        # Validate height
        try:
            height = float(self.height_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Height", "Height must be a number, e.g. 1.75")
            return

        if weight <= 0 or height <= 0:
            messagebox.showwarning("Invalid Values", "Weight and height must be positive numbers.")
            return

        bmi = calculate_bmi(weight, height)
        category = classify_bmi(bmi)
        color = CATEGORY_COLORS[category]

        self.result_label.config(
            text=f"{name}'s BMI: {bmi}  ({category})",
            fg=color,
            font=("Segoe UI", 14, "bold"),
        )

        self.db.add_record(name, weight, height, bmi, category)

    def on_show_graph(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Enter a name first, then calculate at least once.")
            return

        history = self.db.get_history(name)
        if len(history) < 1:
            messagebox.showinfo("No Data", f"No saved records for '{name}' yet.")
            return

        # Clear any previous chart before drawing a new one
        for widget in self.graph_container.winfo_children():
            widget.destroy()

        dates = [row[0] for row in history]
        bmis = [row[1] for row in history]

        figure = Figure(figsize=(4.3, 2.6), dpi=100)
        plot = figure.add_subplot(111)
        plot.plot(range(len(bmis)), bmis, marker="o", color="#2563EB")
        plot.set_title(f"{name}'s BMI Trend")
        plot.set_ylabel("BMI")
        plot.set_xticks(range(len(dates)))
        plot.set_xticklabels([d[5:10] for d in dates], rotation=45, fontsize=7)
        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=self.graph_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = BMIApp()
    app.mainloop()
