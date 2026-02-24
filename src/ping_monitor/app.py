import tkinter as tk

from ping_monitor.ui.main_window import MainWindow


def run() -> None:
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
