
import tkinter as tk
from tkinter import ttk, font
import datetime
import threading
import time
from plyer import notification
from backend.db import init_db, get_all_plans, save_plan

class TimeTableApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("周计划模板")
        self.geometry("1000x600")
        self.configure(bg='#f0f0f0')

        # --- Style Configuration ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        self.style.configure('Header.TLabel', background='#4a4a4a', foreground='white', font=('Helvetica', 11, 'bold'), padding=10)
        self.style.configure('Period.TLabel', background='#6c757d', foreground='white', font=('Helvetica', 10, 'bold'), padding=10)
        self.style.configure('Today.Header.TLabel', background='#d9534f', foreground='white')

        # --- Database ---
        init_db()

        # --- Main UI ---
        self.periods = [("morning", "上午"), ("afternoon", "下午"), ("evening", "晚上")]
        self.period_map = dict(self.periods)
        self.create_widgets()
        self.render_timetable()
        
        # --- Start Services ---
        self.update_clock()
        self.start_reminder_thread()

    def create_widgets(self):
        """Creates the main widgets for the application."""
        header_frame = ttk.Frame(self, padding="10 10 10 0")
        header_frame.pack(fill=tk.X)

        title_label = ttk.Label(header_frame, text="周计划模板", font=('Helvetica', 16, 'bold'))
        title_label.pack(side=tk.LEFT)

        self.clock_label = ttk.Label(header_frame, text="", font=('Helvetica', 12))
        self.clock_label.pack(side=tk.RIGHT)

        self.timetable_frame = ttk.Frame(self, padding="10")
        self.timetable_frame.pack(fill=tk.BOTH, expand=True)

        self.status_bar = ttk.Label(self, text="就绪", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def render_timetable(self):
        """Renders the timetable grid and populates it with data."""
        for widget in self.timetable_frame.winfo_children():
            widget.destroy()

        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        today_weekday = datetime.datetime.now().weekday() # Monday is 0

        # Create period labels
        for i, (period_key, period_name) in enumerate(self.periods):
            label = tk.Label(self.timetable_frame, text=period_name, background='#6c757d', foreground='white', font=('Helvetica', 10, 'bold'), padx=10, pady=10)
            label.grid(row=i + 1, column=0, sticky="nsew")

        # Create headers
        ttk.Label(self.timetable_frame).grid(row=0, column=0) # Empty corner
        for i, day in enumerate(days):
            style = 'Today.Header.TLabel' if i == today_weekday else 'Header.TLabel'
            ttk.Label(self.timetable_frame, text=day, style=style, anchor=tk.CENTER).grid(row=0, column=i + 1, sticky="nsew")

        # Create text cells
        self.cells = {}
        cell_colors = {'morning': '#fffbe6', 'afternoon': '#e6f7ff', 'evening': '#f3e8ff'}
        for row, (period, _) in enumerate(self.periods):
            for col, day_name in enumerate(days):
                day_of_week = col
                cell = tk.Text(self.timetable_frame, wrap=tk.WORD, height=5, width=15, relief=tk.FLAT, borderwidth=2, font=('Helvetica', 14), bg=cell_colors[period], padx=5, pady=5)
                cell.tag_configure("center", justify='center')
                cell.grid(row=row + 1, column=col + 1, sticky="nsew", padx=1, pady=1)
                cell.bind("<FocusOut>", lambda e, d=day_of_week, p=period, c=cell: self.auto_save(d, p, c))
                self.cells[(day_of_week, period)] = cell

        # Configure grid resizing
        self.timetable_frame.grid_columnconfigure(0, weight=0)  # Let the period column have a fixed width
        for i in range(1, len(days) + 1):  # Let the day columns expand
            self.timetable_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(self.periods) + 1):
            self.timetable_frame.grid_rowconfigure(i, weight=1)

        self.load_plans()

    def load_plans(self):
        """Loads all plans from the database and displays them in the grid."""
        plans = get_all_plans()
        for cell in self.cells.values():
            cell.delete(1.0, tk.END)
        for plan in plans:
            key = (plan['day_of_week'], plan['period'])
            if key in self.cells:
                self.cells[key].insert(tk.END, plan['content'], "center")

    def auto_save(self, day_of_week, period, cell):
        """Saves the content of a cell automatically when focus is lost."""
        content = cell.get(1.0, tk.END).strip()
        cell.tag_add("center", "1.0", "end")
        save_plan(day_of_week, period, content)
        self.status_bar.config(text=f"{self.period_map[period]}的计划已保存!")
        self.after(2000, lambda: self.status_bar.config(text="就绪"))

    def update_clock(self):
        """Updates the clock in the header every second."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.config(text=now)
        self.after(1000, self.update_clock)

    def start_reminder_thread(self):
        """Starts the background thread for sending reminders."""
        reminder_thread = threading.Thread(target=self.reminder_service, daemon=True)
        reminder_thread.start()

    def reminder_service(self):
        """The service that runs in the background to check for and send notifications."""
        reminder_times = {
            'morning': datetime.time(9, 0),
            'afternoon': datetime.time(14, 0),
            'evening': datetime.time(19, 0)
        }
        notified_today = set()

        while True:
            now = datetime.datetime.now()
            current_day_of_week = now.weekday()
            current_time = now.time()

            if current_time.hour == 0 and current_time.minute == 0:
                notified_today.clear()

            plans = get_all_plans()
            for plan in plans:
                if plan['day_of_week'] == current_day_of_week:
                    period = plan['period']
                    plan_time = reminder_times.get(period)
                    plan_content = plan['content']

                    if plan_time and current_time.hour == plan_time.hour and current_time.minute == plan_time.minute and (period not in notified_today):
                        if plan_content:
                            notification.notify(
                                title=f"{self.period_map.get(period, '')}计划提醒",
                                message=plan_content,
                                app_name='周计划模板',
                                timeout=10
                            )
                            notified_today.add(period)
            
            time.sleep(60)

if __name__ == "__main__":
    app = TimeTableApp()
    app.mainloop()
