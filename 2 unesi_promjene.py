#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import traceback
from lib_ocijeni import *

Fpodaci = None
Fpromjene = None
Fkod = None

if __name__ == '__main__':
    try:
        root = tk.Tk()
        root.title('Ocijeni')
        root.withdraw()
        # root.geometry('+0+0')

        root.option_add("*font", "sans 14")
        try:
            try:
                root.tk.call('tk_getOpenFile', '-foobarbaz')
            except tk.TclError:
                pass
            root.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')
        except:
            pass

        root.status = tk.Label(root, text='', width=80, height=5)
        root.status.grid(row=1, column=1, padx=10, pady=10)
        root.update()

        file_podaci, dir_path = Otvori_rmk_podaci(
            root, Fpodaci, only_podaci=True)

        kod2jmbag, jmbag2kod = Ucitaj_kodove(root, Fkod, dir_path)

        root.status['text'] = 'Učitavam podatke...'
        root.update()
        root.deiconify()

        if file_podaci.name.split('.')[-1] == 'rmk':
            lista = Ucitaj_listu_rmk(file_podaci)
            lista_brisani = [False, ]*len(lista)
        else:
            lista, lista_brisani = Ucitaj_listu_xlsx(file_podaci)
        file_podaci.close()

        root.status['text'] = 'Premještam skenove u zaseban folder...'
        root.update()
        dir_skenovi = Premjesti_skenove(lista, dir_path)
        root.withdraw()

        BROJ_ZADATAKA = Odredi_broj_zadataka(root, dir_path)

        root.status['text'] = 'Učitavam podatke...'
        root.update()
        root.deiconify()

        Studenti = dict()
        Ucitaj_podatke_u_studenti(
            lista, lista_brisani, kod2jmbag, Studenti, BROJ_ZADATAKA, dir_path)

        root.withdraw()

        promjene = Ucitaj_listu_izmjena(
            root, Fpromjene, jmbag2kod, BROJ_ZADATAKA)

        root.status['text'] = 'Generiram datoteke za upload...'
        root.update()
        root.deiconify()
        Generiraj_datoteke_za_upload(root, lista, Studenti, dir_path, dir_skenovi,
                                     BROJ_ZADATAKA, kod2jmbag, promjene, novo_ime='nova_lista_s_izmjenama')

        root.destroy()

        ######## END PROGRAM ########
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            'Uspjeh!', 'Obrada je uspješno privedena kraju. Datoteke za upload Vas čekaju u folderu sa skenovima.')
        root.destroy()

    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        with open('error_log.txt', 'w') as f:
            f.write(f'{e}\n'+''.join(traceback.format_tb(e.__traceback__)))
        messagebox.showerror(
            'Kritična greška!', f'Obrada nije dovršena do kraja. Nemojte nastaviti s uploadom na FERweb prije nego detektirate problem. Podaci mogu biti krivi ili nepotpuni.\n\nError: {e}')
        root.destroy()
        raise e
