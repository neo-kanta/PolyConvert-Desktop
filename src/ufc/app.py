import tkinter as tk
from tkinter import ttk

from ufc.ui.main_window import MainWindow, AppConfig

def main():
    cfg = AppConfig.load()
    root = tk.Tk()
    
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    app = MainWindow(root, cfg)
    root.mainloop()

if __name__ == "__main__":
    main()
