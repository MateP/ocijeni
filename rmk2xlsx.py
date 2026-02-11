#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple drag-and-drop tool to convert an RMK file to XLSX using
helpers from `lib_ocijeni.py`.

Drop an RMK file onto the box or choose it with the file dialog,
then click Convert.
"""

import os
import traceback
import tkinter as tk
import openpyxl
import tkinterDnD
from tkinter import filedialog, messagebox

DULJINA_KODA = 3
import csv

def rmk_2_xlsx(rmk_path, dir_path):
    
    try:
        with open(rmk_path, 'r', encoding='utf-16') as file:
            csvreader = csv.reader(file, delimiter='\t')
            rmk = list(csvreader)
    except UnicodeError:
        with open(rmk_path, 'r', encoding='utf-8') as file:
            csvreader = csv.reader(file, delimiter='\t')
            rmk = list(csvreader)

    name = 'rmk_podaci.xlsx'
    xlsx_name = os.path.join(dir_path, name)
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    worksheet.append(['KOD', 'JMBAG', 'PREZIME', 'IME',
                     'ZADATAK', 'BODOVI', 'SLIKA_F', 'SLIKA_B'])

    for row in rmk[1::2]:
        slikaF = row[-2].split('\v')[0].split('\\')[-1]
        slikaB = row[-1].split('\v')[0].split('\\')[-1]
        kod = ''.join(row[:DULJINA_KODA])
        unos = {'kod': kod, 'zadatak': row[DULJINA_KODA],
                'bodovi': row[DULJINA_KODA+1], 'slikaF': slikaF, 'slikaB': slikaB}
        kod = unos['kod']
        zadatak = unos['zadatak']
        bodovi = unos['bodovi']
        slikaF = unos['slikaF']
        slikaB = unos['slikaB']
        jmbag = None
        prezime = None
        ime = None
        worksheet.append(
            [kod, jmbag, prezime, ime, zadatak, bodovi, slikaF, slikaB])
    workbook.save(xlsx_name)

def main():
    root = tkinterDnD.Tk()
    root.title('rmk → xlsx')
    root.geometry('700x250+200+200')

    path_var = tk.StringVar(value='Drop .rmk file here or choose with button')

    def drop(event):
        data = event.data
        if data.startswith('{') and data.endswith('}'):
            data = data[1:-1]
        path_var.set(data)

    def choose_file():
        fn = filedialog.askopenfilename(title='Open rmk file', filetypes=[('RMK files', '.rmk'), ('All', '*')])
        if fn:
            path_var.set(fn)

    def convert():
        rmk_fn = path_var.get()
        if not rmk_fn or not os.path.exists(rmk_fn):
            messagebox.showwarning('No file', 'Please choose or drop a valid .rmk file first')
            return
        try:
            dir_path = os.path.dirname(os.path.realpath(rmk_fn))
            rmk_2_xlsx(rmk_fn, dir_path)
            messagebox.showinfo('Done', f'Wrote rmk_podaci.xlsx in {dir_path}')
        except Exception as e:
            with open('error_log.txt', 'w') as f:
                f.write(f'{e}\n' + ''.join(traceback.format_tb(e.__traceback__)))
            messagebox.showerror('Error', f'Conversion failed: {e}\nSee error_log.txt')

    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True, padx=10, pady=10)

    label = tk.Label(frame, textvariable=path_var, relief='solid', width=80, height=6, wraplength=600, anchor='w', justify='left')
    label.grid(row=0, column=0, columnspan=2, sticky='nsew')
    label.register_drop_target('*')
    label.bind('<<Drop>>', drop)

    btn_choose = tk.Button(frame, text='Choose file...', command=choose_file)
    btn_choose.grid(row=1, column=0, sticky='w', pady=10)

    btn_convert = tk.Button(frame, text='Convert to XLSX', command=convert)
    btn_convert.grid(row=1, column=1, sticky='e', pady=10)

    root.mainloop()


if __name__ == '__main__':
    main()
