#!/usr/bin/env python3
import sys, subprocess, traceback
import tkinter as tk
from tkinter import messagebox

try:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', 'pip'])
    for package in ['img2pdf', 'openpyxl']:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', package])

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo('Uspjeh!', 'Instalacija je uspješno privedena kraju.')

except Exception as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror('Kritična greška!', 'Instalacija nije dovršena do kraja.\n\n'+''.join(traceback.format_tb(e.__traceback__)))
    raise e

# Treba imati instaliran Python3 s opcijom ADD TO PATH!
