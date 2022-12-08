#!/usr/bin/env python3
import sys
import subprocess
import traceback
import tkinter as tk
from tkinter import messagebox

try:
    subprocess.check_call(
        [sys.executable, '-m', 'pip', 'install', '-U', 'pip'])
    for package in ['pillow', 'openpyxl']:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', '-U', package])

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo('Uspjeh!', 'Instalacija je uspješno privedena kraju.')
    root.destroy()

except Exception as e:
    root = tk.Tk()
    root.withdraw()
    with open('error_log.txt', 'w') as f:
        f.write(f'{e}\n'+''.join(traceback.format_tb(e.__traceback__)))
    messagebox.showerror('Kritična greška!',
                         f'Instalacija nije dovršena do kraja.\n\nError: {e}')
    root.destroy()
    raise e

# Treba imati instaliran Python3 s opcijom ADD TO PATH!
