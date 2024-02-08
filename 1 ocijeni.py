#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import traceback
from lib_ocijeni import *

Fkod = None
Frmk = None

if __name__ == '__main__':
    try:
        root = myTk()
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

        file_podaci, dir_path = Otvori_rmk_podaci(root, Frmk)

        kod2jmbag, jmbag2kod = Ucitaj_kodove(root, Fkod, dir_path)

        root.status['text'] = 'Učitavam podatke...'
        root.update()
        root.deiconify()

        if file_podaci.name.split('.')[-1] == 'rmk':
            lista = Ucitaj_listu_rmk(file_podaci)
            lista_brisani = [False, ]*len(lista)
        elif file_podaci.name.split('.')[-1] == 'csv':
            lista = Ucitaj_listu_csv(file_podaci)
            lista_brisani = [False, ]*len(lista)
        else:
            lista, lista_brisani = Ucitaj_listu_xlsx(file_podaci)
        file_podaci.close()

        root.status['text'] = 'Premještam skenove u zaseban folder...'
        root.update()
        dir_skenovi = Premjesti_skenove(lista, dir_path)
        root.withdraw()

        BROJ_ZADATAKA = Odredi_broj_zadataka(root, dir_path)

        popup(root, 'Sada rješavamo probleme s neprepoznatim kodom ili brojem zadatka...')
        Popravi_kod_zadatak(root, lista, kod2jmbag, jmbag2kod,
                            BROJ_ZADATAKA, lista_brisani, dir_path, dir_skenovi)

        root.status['text'] = 'Spremam podatke...'
        root.update()
        root.deiconify()

        Spremi_listu_xlsx(lista, kod2jmbag, dir_path, lista_brisani)

        Studenti = dict()
        Ucitaj_podatke_u_studenti(
            lista, lista_brisani, kod2jmbag, Studenti, BROJ_ZADATAKA, dir_path)

        root.withdraw()

        # obradi nebodovane zadatke
        nebodovani = []
        for kod in Studenti:
            if kod not in [BRISAN_, KOD_NEPOZNAT_]:
                student = Studenti[kod]
                for zad in range(1, BROJ_ZADATAKA+1):
                    if len(student.zadaci_index[zad]) > 0:
                        ima_bodove = False
                        for i in student.zadaci_index[zad]:
                            try:
                                bod = int(lista[i]['bodovi'])
                                ima_bodove = True
                            except:
                                pass
                        if not ima_bodove:
                            nebodovani.append(student.zadaci_index[zad])
        if len(nebodovani) > 0:
            popup(root, 'Sada će biti izlistani svi zadaci koji imaju sken ali nemaju očitane bodove.\n'
                  'Ukoliko je mnogo takvih slučajeva, vjerojatno je neki od ispravljača zaboravio ispraviti dio ispita.\n'
                  'Obavijestiti koordinatora!\n\n'
                  'Ukoliko su bodovi zaokruženi na više listova,\n'
                  'te slučajeve možemo preskočiti, oni će se rješavati na uvidima.')
            Obradi_nebodovane(root, nebodovani, lista, kod2jmbag,
                              jmbag2kod, BROJ_ZADATAKA, lista_brisani, dir_skenovi)

        root.status['text'] = 'Spremam podatke...'
        root.update()
        root.deiconify()

        Spremi_listu_xlsx(lista, kod2jmbag, dir_path, lista_brisani)

        Studenti.clear()
        Ucitaj_podatke_u_studenti(
            lista, lista_brisani, kod2jmbag, Studenti, BROJ_ZADATAKA, dir_path)

        root.withdraw()

        # obradi kolizije
        first_kolizija = True
        postoji_kolizija = True
        while postoji_kolizija:
            postoji_kolizija = False

            Studenti_tmp = list(Studenti)
            for kod in Studenti_tmp:
                if kod not in [BRISAN_, KOD_NEPOZNAT_]:
                    student = Studenti[kod]
                    for zad in range(1, BROJ_ZADATAKA+1):
                        bodovi = set()
                        for i in student.zadaci_index[zad]:
                            try:
                                bod = int(lista[i]['bodovi'])
                            except:
                                bod = None
                            if bod is not None:
                                bodovi.add(i)
                        if len(bodovi) > 1:
                            postoji_kolizija = True

                            if first_kolizija:
                                popup(root, 'Sada rješavamo krivo prepoznate kodove ili zadatke...\n'
                                      'Treba pregledati podudara li se ime studenta na listu\n'
                                      's prepoznatim imenom kao i broj zadatka.\n'
                                      'Ukoliko su zbilja svi listovi od istog studenta i za isti zadatak,\n'
                                      'preskačemo i ostavljamo za uvide.')
                                first_kolizija = False

                            kolizija(
                                root, student.zadaci_index[zad], lista, kod2jmbag, jmbag2kod, BROJ_ZADATAKA, lista_brisani, dir_skenovi)
                            mijenjan_kod = update_Studenti(
                                Studenti, kod, zad, lista, lista_brisani, BROJ_ZADATAKA, kod2jmbag)
                            if mijenjan_kod:
                                popup(root, 'Za provjeru ćemo sada pročešljati\n'
                                      f'sve skenove povezane s kodom {kod}.\n'
                                      'Treba pregledati pripadaju li svi oni osobi:\n'
                                      f'{student.ime} {student.prezime}\n'
                                      'U suprotnom, treba upisati ispravan kod ili jmbag.')
                                za_provjeriti = [
                                    izz for zz in Studenti[kod].zadaci_index for izz in Studenti[kod].zadaci_index[zz]]
                                provjeri_osobu(root, za_provjeriti, kod, Studenti, lista, kod2jmbag,
                                               jmbag2kod, BROJ_ZADATAKA, lista_brisani, dir_skenovi)

        root.status['text'] = 'Spremam podatke...'
        root.update()
        root.deiconify()
        Spremi_listu_xlsx(lista, kod2jmbag, dir_path, lista_brisani)

        root.status['text'] = 'Generiram datoteke za upload...'
        root.update()

        Generiraj_datoteke_za_upload(
            root, lista, Studenti, dir_path, dir_skenovi, BROJ_ZADATAKA, kod2jmbag)

        root.status['text'] = 'Generiram datoteke s nebodovanim ispitima...'
        root.update()

        Nebodovani(root, lista, Studenti, dir_path, dir_skenovi, BROJ_ZADATAKA)

        root.destroy()

        ######## END PROGRAM ########
        root = myTk()
        root.withdraw()
        messagebox.showinfo(
            'Uspjeh!', 'Obrada je uspješno privedena kraju. Datoteke za upload Vas čekaju u folderu sa skenovima.')
        root.destroy()

    except Exception as e:
        root = myTk()
        root.withdraw()
        with open('error_log.txt', 'w') as f:
            f.write(f'{e}\n'+''.join(traceback.format_tb(e.__traceback__)))
        messagebox.showerror(
            'Kritična greška!', f'Obrada nije dovršena do kraja. Nemojte nastaviti s uploadom na FERweb prije nego detektirate problem. Podaci mogu biti krivi ili nepotpuni.\n\nError: {e}')
        root.destroy()
        raise e
