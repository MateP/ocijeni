import os, csv, openpyxl, img2pdf, pickle, io
from tkinter.filedialog import askopenfile
from PIL import Image, ImageTk
import tkinter as tk

DULJINA_KODA = 3
BRISAN_ = '---'
KOD_NEPOZNAT_ = '***'

with io.BytesIO() as output:
    Image.new('RGB', (5, 5)).save(output, format="PNG")
    WHITE_PIXEL = output.getvalue()

def popup(root,status):
    popup=tk.Toplevel(root)
    popup.geometry('+0+0')
    popup.title('Uputa...')

    tk.Label(popup, text=status,width=80,height=10).grid(row=1,column=1, padx = 3, pady=3)
    tk.Button(popup, text='Nastavi', command=popup.destroy).grid(row=2,column=1, padx = 3, pady=3)
    root.wait_window(popup)

def Otvori_rmk_podaci(root,Frmk,only_podaci=False):
    if Frmk==None:
        if only_podaci:
            popup(root,'Odaberite datoteku podaci*.xlsx...')
            file_scan = askopenfile(mode='r', title = 'Učitajte datoteku \'podaci*.xlsx\'...', filetypes=[("Excel files", ".xlsx .xls")])
        else:
            popup(root,'Odaberite datoteku .rmk u mapi sa skenovima iz CIP-a, ili datoteku podaci*.xlsx...')
            file_scan = askopenfile(mode='r', title = 'Učitajte RMK ili \'podaci.xlsx\' datoteku...', filetypes=[("RMK/Excel files", ".rmk .xlsx .xls")])
    else:
        file_scan = open(Frmk,'r', newline='')

    dir_path = os.path.dirname(os.path.realpath(file_scan.name))
    return file_scan, dir_path

def Ucitaj_listu_izmjena(root, Fpromjene, jmbag2kod, BROJ_ZADATAKA):
    if Fpromjene==None:
        popup(root,'Učitajte datoteku \'izmjene.xlsx\'...\n\n'\
        'Datoteka mora imati jedan redak zaglavlja\n'\
        'sa stupcima JMBAG, Z1, Z2, Z3, ...')
        file_prom = askopenfile(mode='r', title = 'Učitajte datoteku \'izmjene.xlsx\'...', filetypes=[("Excel files", ".xlsx .xls")])
        ### OBLIKA
        ### JMBAG	Z1	Z2	Z3	Z4	Z5	Z6	Z7	Z8 ...
    else:
        file_prom = open(Fpromjene,'r', newline='', encoding='utf-8')

    prom_ime = file_prom.name
    file_prom.close()

    workbook = openpyxl.load_workbook(prom_ime, data_only=True)
    worksheet = workbook.worksheets[0]

    promjene = dict()


    worksheet_rows = worksheet.values
    head = [str(nm).upper() for nm in next(worksheet_rows)]
    i_jmbag = head.index('JMBAG')
    i_z = dict()
    for zad in range(1,BROJ_ZADATAKA+1):
        i_z[zad] = head.index(f'Z{zad}')

    for rowx in range(worksheet.max_row-1):
        row = next(worksheet_rows)
        jmbag = row[i_jmbag]
        if jmbag != None:
            jmbag = f'{int(jmbag):010}'
            kod = jmbag2kod[jmbag]

            for zad in range(1,BROJ_ZADATAKA+1):
                try:
                    bod=int(row[i_z[zad]])
                except:
                    bod=None

                if bod!=None:
                    if kod not in promjene:
                        promjene[kod]=dict()

                    promjene[kod][zad] = bod

    return promjene

class Student:
  def __init__(self, jmbag, ime, prezime, BROJ_ZADATAKA):
    self.jmbag = jmbag
    self.ime = ime
    self.prezime = prezime
    self.zadaci_index = dict((key, []) for key in range(BROJ_ZADATAKA+1))


def Ucitaj_kodove(root,Fkod,dir_path):
    if Fkod == None:
        dst = os.path.join(dir_path,'_kodovi.txt')
        if os.path.exists(dst):
            with open(dst,'r', newline='', encoding='utf-8') as f:
                file_kodovi_path = f.read()
                file_kodovi = open(file_kodovi_path,'r', newline='', encoding='utf-8')
        else:
            popup(root, 'Odaberite datoteku s kodovima za ovaj ispit...')
            file_kodovi = askopenfile(mode='r', title = 'Učitajte datoteku kodova...', filetypes=[("Excel files", ".xlsx .xls")])
            if file_kodovi != None:
                with open(dst,'w', newline='', encoding='utf-8') as f:
                    f.write(os.path.realpath(file_kodovi.name))
    else:
        file_kodovi = open(Fkod,'r', newline='', encoding='utf-8')

    name = file_kodovi.name
    file_kodovi.close()

    kod2jmbag = dict()
    jmbag2kod = dict()

    workbook = openpyxl.load_workbook(name, data_only=True)
    worksheet = workbook.worksheets[0]
    worksheet_rows = worksheet.values

    head = [str(nm).upper() for nm in next(worksheet_rows)]

    i_jmbag = head.index('JMBAG')
    i_kod = head.index('KOD')

    try:
        i_ime = head.index('IME')
        i_prezime = head.index('PREZIME')
    except:
        i_ime, i_prezime = None, None

    for rowx in range(worksheet.max_row-1):
        row = next(worksheet_rows)
        kod, jmbag = row[i_kod], row[i_jmbag]
        if kod != None and jmbag != None:
            if i_ime != None and i_prezime != None:
                ime, prezime  = row[i_ime], row[i_prezime]
            else:
                ime, prezime = '', ''
            kod2jmbag[f'{int(kod)}'.zfill(DULJINA_KODA)] = {'JMBAG': f'{int(jmbag):010}', 'IME': ime, 'PREZIME': prezime}
            jmbag2kod[f'{int(jmbag):010}'] = f'{int(kod)}'.zfill(DULJINA_KODA)
    return kod2jmbag, jmbag2kod

def Generiraj_datoteke_za_upload(root, lista, Studenti, dir_path, dir_skenovi, BROJ_ZADATAKA, kod2jmbag, promjene=None, novo_ime=None):
    '''
    Generira upload.rmk, odgovori.csv i pdfove sa ispitom svakog studenta
    '''

    dir_path_child = os.path.join(dir_path,'upload')
    if not os.path.exists(dir_path_child):
        os.makedirs(dir_path_child)

    rmk_file = open(os.path.join(dir_path_child,'cheat.rmk'),'w', newline='', encoding='utf-8')
    csv_file = open(os.path.join(dir_path_child,'odgovori.csv'),'w', newline='', encoding='utf-8')

    xlsx_name = os.path.join(dir_path,f'{"lista" if novo_ime==None else novo_ime}.xlsx')
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    rmk_file.write(f'X\tX\t{BROJ_ZADATAKA+2}')
    csvwriter = csv.writer(csv_file, delimiter=';')

    worksheet.append(['JMBAG','PREZIME','IME']+[f'Z{i}' for i in range(1,BROJ_ZADATAKA+1)]+['SUMA'])

    if promjene != None:
        for kod in promjene:
            if kod not in Studenti and kod in kod2jmbag:
                Studenti[kod] = Student(kod2jmbag[kod]['JMBAG'], kod2jmbag[kod]['IME'], kod2jmbag[kod]['PREZIME'], BROJ_ZADATAKA)

    N = len(Studenti)
    iter_stud=1
    for kod in Studenti:
        student = Studenti[kod]
        bodovi=dict()
        root.status['text'] = f'Generiram datoteke za upload...\n{iter_stud:8}/{N-2}'
        root.update()


        slike = []
        for zad in list(range(1,BROJ_ZADATAKA+1))+[0]:
            bodovi[zad] = 0
            for iter_ind in student.zadaci_index[zad]:

                if lista[iter_ind]['slikaF'] not in ['', None]:
                    slike.append(lista[iter_ind]['slikaF'])
                if lista[iter_ind]['slikaB'] not in ['', None]:
                    slike.append(lista[iter_ind]['slikaB'])

                try:
                    bod = int(lista[iter_ind]['bodovi'])
                except:
                    bod = 0
                if bod>0:
                    bodovi[zad] = bod

            if promjene != None:
                if kod in promjene:
                    if zad in promjene[kod]:
                        bodovi[zad] = promjene[kod][zad]


        if kod == KOD_NEPOZNAT_:
            pdf_filename = os.path.join(dir_path,'#NEPOZNATI.pdf')

        elif kod == BRISAN_:
            pdf_filename = os.path.join(dir_path,'#BRISANI.pdf')

        else:
            iter_stud+=1
            rmk_file.write(f'\n{student.jmbag}\tG{student.jmbag}'+BROJ_ZADATAKA*'\tA'+'\nX')

            zadaci = [bodovi[i] for i in range(1,BROJ_ZADATAKA+1)]

            csvwriter.writerow(['#',]+[f'Z{i}' for i in range(1,BROJ_ZADATAKA+1)])
            csvwriter.writerow([f'G{student.jmbag}']+ BROJ_ZADATAKA*['A'])
            csvwriter.writerow(['T']+ zadaci)
            csvwriter.writerow(['N']+ BROJ_ZADATAKA*[0])

            StartCell = f'{openpyxl.utils.get_column_letter(4)}{worksheet.max_row+1}'
            EndCell = f'{openpyxl.utils.get_column_letter(3+BROJ_ZADATAKA)}{worksheet.max_row+1}'
            # 3 gore nije DULJINA_KODA već JMBAG,Prezime, Ime
            worksheet.append([student.jmbag, student.prezime, student.ime]+ zadaci+[f'=SUM({StartCell}:{EndCell})'])

            pdf_filename = os.path.join(dir_path_child,f'{student.jmbag}.pdf')

        if len(slike) == 0:
            im_list = [WHITE_PIXEL]
        else:
            im_list = [os.path.join(dir_skenovi,sl) for sl in slike]

        with open(pdf_filename,"wb") as f:
            f.write(img2pdf.convert(im_list,engine=img2pdf.Engine.internal))


    rmk_file.close()
    csv_file.close()
    workbook.save(xlsx_name)

    pickle_file = os.path.join(dir_path,'_upisani.pickle')
    with open(pickle_file, 'wb') as f:
        pickle.dump(list(Studenti), f, pickle.HIGHEST_PROTOCOL)

def Nebodovani(root, lista, Studenti, dir_path, dir_skenovi, BROJ_ZADATAKA):

    dir_path_nebodovani = os.path.join(dir_path,'nebodovani')
    if not os.path.exists(dir_path_nebodovani):
        os.makedirs(dir_path_nebodovani)

    nebodo_sl = dict((key, []) for key in range(1,BROJ_ZADATAKA+1))

    for kod in Studenti:
        if kod not in [KOD_NEPOZNAT_, BRISAN_]:
            student = Studenti[kod]
            bodovi=dict()

            for zad in list(range(1,BROJ_ZADATAKA+1)):
                bodovan = False
                for iter_ind in student.zadaci_index[zad]:
                    try:
                        bod = int(lista[iter_ind]['bodovi'])
                        bodovan = True
                    except:
                        pass
                if not bodovan:
                    for iter_ind in student.zadaci_index[zad]:
                        if lista[iter_ind]['slikaF'] not in ['', None]:
                            nebodo_sl[zad].append(lista[iter_ind]['slikaF'])
                        if lista[iter_ind]['slikaB'] not in ['', None]:
                            nebodo_sl[zad].append(lista[iter_ind]['slikaB'])

    for zad in list(range(1,BROJ_ZADATAKA+1)):
        root.status['text'] = f'Generiram datoteke s nebodovanim ispitima...\n{zad}/{BROJ_ZADATAKA}'
        root.update()
        pdf_filename = os.path.join(dir_path_nebodovani,f'Z{zad}.pdf')

        if len(nebodo_sl[zad]) == 0:
            im_list = [WHITE_PIXEL]
        else:
            im_list = [os.path.join(dir_skenovi,sl) for sl in nebodo_sl[zad]]

        with open(pdf_filename,"wb") as f:
            f.write(img2pdf.convert(im_list,engine=img2pdf.Engine.internal))



def Ucitaj_podatke_u_studenti(lista, lista_brisani, kod2jmbag, Studenti, BROJ_ZADATAKA, dir_path):
    Studenti.clear()
    Studenti[BRISAN_] = Student(None, None, None, BROJ_ZADATAKA)
    Studenti[KOD_NEPOZNAT_] = Student(None, None, None, BROJ_ZADATAKA)

    pickle_file = os.path.join(dir_path,'_upisani.pickle')
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as f:
            upisani = pickle.load(f)
    else:
        upisani=[]

    for kod in upisani:
        if kod in kod2jmbag:
            Studenti[kod] = Student(kod2jmbag[kod]['JMBAG'], kod2jmbag[kod]['IME'], kod2jmbag[kod]['PREZIME'], BROJ_ZADATAKA)

    for i, unos in enumerate(lista):
        kod = unos['kod']
        zadatak = unos['zadatak']

        if lista_brisani[i]:
            kod = BRISAN_
        elif kod not in kod2jmbag:
            kod = KOD_NEPOZNAT_

        try:
            zad = int(zadatak)
        except:
            zad = 0

        if zad < 0 or zad > BROJ_ZADATAKA:
            zad = 0

        if kod not in Studenti:
            Studenti[kod] = Student(kod2jmbag[kod]['JMBAG'], kod2jmbag[kod]['IME'], kod2jmbag[kod]['PREZIME'], BROJ_ZADATAKA)
        Studenti[kod].zadaci_index[zad].append(i)

def Ucitaj_listu_rmk(rmk_file):

    try:
        with open(rmk_file.name,'r',encoding='utf-16') as file:
            csvreader = csv.reader(file, delimiter='\t')
            rmk = list(csvreader)
    except UnicodeError:
        with open(rmk_file.name,'r',encoding='utf-8') as file:
            csvreader = csv.reader(file, delimiter='\t')
            rmk = list(csvreader)

    lista = []

    for row in rmk[1::2]:
        slikaF = row[-2].split('\v')[0].split('\\')[-1]
        slikaB = row[-1].split('\v')[0].split('\\')[-1]
        kod = ''.join(row[:DULJINA_KODA])
        unos = {'kod': kod, 'zadatak': row[DULJINA_KODA], 'bodovi': row[DULJINA_KODA+1], 'slikaF': slikaF, 'slikaB': slikaB}
        lista.append(unos)
    return lista

def Ucitaj_listu_xlsx(xlsx_file):
    workbook = openpyxl.load_workbook(xlsx_file.name, data_only=True)
    worksheet = workbook.worksheets[0]
    worksheet_rows = worksheet.values

    next(worksheet_rows) # head = [str(nm).upper() for nm in next(worksheet_rows)]

    lista = []
    lista_brisani = []
    for rowx in range(worksheet.max_row-1):
        row = next(worksheet_rows)
        if type(row[0]) in [int, float]:
            kod = f'{int(row[0])}'.zfill(DULJINA_KODA)
        else:
            kod = str(row[0])

        if type(row[4]) in [int, float]:
            zad = int(row[4])
        else:
            zad = str(row[4])

        if type(row[5]) in [int, float]:
            bod = int(row[5])
        else:
            bod = str(row[5])

        unos = {'kod': kod, 'zadatak': zad, 'bodovi': bod, 'slikaF': row[6], 'slikaB': row[7]}
        lista.append(unos)
        lista_brisani.append(True if kod==BRISAN_ else False)
    return lista, lista_brisani

def Premjesti_skenove(lista,dir_path):
    dir_skenovi = os.path.join(dir_path,'skenovi')
    if not os.path.exists(dir_skenovi):
        os.makedirs(dir_skenovi)
        for unos in lista:
            try:
                os.replace(os.path.join(dir_path,unos['slikaF']),os.path.join(dir_skenovi,unos['slikaF']))
            except:
                pass
            try:
                os.replace(os.path.join(dir_path,unos['slikaB']),os.path.join(dir_skenovi,unos['slikaB']))
            except:
                pass
    return dir_skenovi

def Spremi_listu_xlsx(lista, kod2jmbag, dir_path, lista_brisani = None):
    '''lista_brisani = None znači da se isključivo iz koda
    odlučuje je li se nešto briše ili ignorira (ili ako ima valjan kod se uključuje)
    '''

    name = 'podaci.xlsx'
    # i=0
    # while os.path.exists(os.path.join(dir_path,name)):
    #     i+=1
    #     name = f'podaci{i}.xlsx'


    xlsx_name = os.path.join(dir_path,name)
    workbook = openpyxl.Workbook()
    worksheet = workbook.active



    worksheet.append(['KOD', 'JMBAG', 'PREZIME', 'IME', 'ZADATAK', 'BODOVI', 'SLIKA_F', 'SLIKA_B'])

    for i, unos in enumerate(lista):
        kod = unos['kod']
        zadatak = unos['zadatak']
        bodovi = unos['bodovi']
        slikaF = unos['slikaF']
        slikaB = unos['slikaB']

        if lista_brisani == None:
            if kod == BRISAN_:
                jmbag = None
                prezime = None
                ime = None
            elif kod in kod2jmbag:
                jmbag = kod2jmbag[kod]['JMBAG']
                prezime = kod2jmbag[kod]['PREZIME']
                ime = kod2jmbag[kod]['IME']
            else:
                kod = KOD_NEPOZNAT_
                jmbag = None
                prezime = None
                ime = None
        else:
            if lista_brisani[i] == True:
                kod = BRISAN_
                jmbag = None
                prezime = None
                ime = None
            elif kod in kod2jmbag:
                jmbag = kod2jmbag[kod]['JMBAG']
                prezime = kod2jmbag[kod]['PREZIME']
                ime = kod2jmbag[kod]['IME']
            else:
                kod = KOD_NEPOZNAT_
                jmbag = None
                prezime = None
                ime = None

        worksheet.append([kod, jmbag, prezime, ime, zadatak, bodovi, slikaF, slikaB])
    workbook.save(xlsx_name)

def Odredi_broj_zadataka(root, dir_path):
    BROJ_ZADATAKA=None
    brzad_file = os.path.join(dir_path,'_brzad.txt')
    if os.path.exists(brzad_file):
        with open(brzad_file,'r', newline='', encoding='utf-8') as f:
            BROJ_ZADATAKA = int(f.read())
    else:
        frame = tk.Toplevel(root)
        frame.title('Koji je broj zadataka na ovom ispitu?')
        tk.Label(frame,text=f'Unesi broj zadataka na ovom ispitu:').grid(row=1,column=1,sticky=tk.E)
        unosBrZad = tk.Entry(frame, width='8')
        unosBrZad.grid(row=1,column=2,sticky=tk.W,padx=10)
        def readBrZad():
            nonlocal BROJ_ZADATAKA
            try:
                BROJ_ZADATAKA = int(unosBrZad.get())
                with open(brzad_file,'w', newline='', encoding='utf-8') as f:
                    f.write(f'{BROJ_ZADATAKA}')
                frame.destroy()
            except:
                pass
        okButton = tk.Button(frame, text='Potvrdi', command=readBrZad)
        okButton.grid(row=2,columnspan=2,column=1)
        okButton.bind('<Return>', lambda _: readBrZad())
        okButton.bind('<KP_Enter>', lambda _: readBrZad())
        unosBrZad.bind('<Return>', lambda _: readBrZad())
        unosBrZad.bind('<KP_Enter>', lambda _: readBrZad())
        root.wait_window(frame)
    return BROJ_ZADATAKA

def Popravi_kod_zadatak(root, lista, kod2jmbag, jmbag2kod, BROJ_ZADATAKA, lista_brisani, dir_path, dir_skenovi):
    problematicni=set()

    lista_statusa = [[] for _ in range(len(lista))]

    for i,unos in enumerate(lista):
        kod = unos['kod']
        zadatak = unos['zadatak']
        bodovi = unos['bodovi']
        slikaF = unos['slikaF']
        slikaB = unos['slikaB']

        if kod not in kod2jmbag:
            lista_statusa[i].append('Kod nije prepoznat')
            problematicni.add(i)

        try:
            zad = int(zadatak)
            if zad<1 or zad>BROJ_ZADATAKA:
                lista_statusa[i].append('Broj zadatka izvan dozvoljenog ranga')
                problematicni.add(i)
        except ValueError:
            lista_statusa[i].append('Neispravan broj zadatka')
            problematicni.add(i)

    current = None
    Front = True

    def loadimage(image_name):
        image = Image.open(os.path.join(dir_skenovi,image_name))
        height = int(frame.winfo_screenheight()*0.85)
        width = int(21*height/29.7)
        image = image.resize((width, height), Image.ANTIALIAS)
        canvas = tk.Canvas(frame, width = width, height = height, bg = "#000000")
        photo = ImageTk.PhotoImage(image, master = canvas)
        slika['image'] = photo
        slika.photo = photo

    def spremi_trenutni():
        lista[current]['kod'] = Ekod.get()
        lista[current]['zadatak'] = Ezadatak.get()
        lista[current]['bodovi'] = Ebodovi.get()

    def clear():
        Ekod.delete(0, tk.END)
        Ejmbag.delete(0, tk.END)
        Ezadatak.delete(0, tk.END)
        Ebodovi.delete(0, tk.END)

    def toggle():
        nonlocal Front
        if Front:
            loadimage(lista[current]['slikaB'])
            Front = False
        else:
            loadimage(lista[current]['slikaF'])
            Front = True

    def erase():
        if lista_brisani[current] == False:
            lista_brisani[current] = True
            pazi['text'] = '------ ZA BRISANJE ------'
        else:
            lista_brisani[current] = False
            pazi['text'] = ';\n'.join(lista_statusa[current])

    def update_polja(var,*kwargs):
        if var=='kod':
            kod = tv_kod.get()
            if kod in kod2jmbag:
                Lime['text'] = kod2jmbag[kod]['IME'] + ' ' + kod2jmbag[kod]['PREZIME']
                jmbag = kod2jmbag[kod]['JMBAG']
            else:
                Lime['text'] = ''
                jmbag = ''
            tv_jmbag.trace_remove('write', tv_jmbag.trace_id)
            tv_jmbag.set(jmbag)
            tv_jmbag.trace_id = tv_jmbag.trace_add('write', update_polja)

        elif var=='jmbag':
            jmbag = tv_jmbag.get()
            if jmbag in jmbag2kod:
                kod = jmbag2kod[jmbag]
                Lime['text'] = kod2jmbag[kod]['IME'] + ' ' + kod2jmbag[kod]['PREZIME']
            else:
                Lime['text'] = ''
                kod = ''
            tv_kod.trace_remove('write', tv_kod.trace_id)
            tv_kod.set(kod)
            tv_kod.trace_id = tv_kod.trace_add('write', update_polja)


    def show(current):
        nonlocal Front

        status['text'] =f'{current+1}/{len(lista)}'

        unos = lista[current]
        kod = unos['kod']
        zadatak = unos['zadatak']
        bodovi = unos['bodovi']
        slikaF = unos['slikaF']
        slikaB = unos['slikaB']

        pazi['text'] ='------ ZA BRISANJE ------' if lista_brisani[current]==True else ';\n'.join(lista_statusa[current])

        loadimage(slikaF)
        Front = True

        clear()
        Ekod.insert(0,kod)
        Ezadatak.insert(0,zadatak)
        Ebodovi.insert(0,bodovi)

    def move(delta,first=False):
        if not first:
            spremi_trenutni()
        nonlocal current

        old_current = current
        M = len(lista)-1

        if delta == 0:
            current = 0
        elif delta == 1:
            current = min(M,current+1)
        elif delta == -1:
            current = max(0,current-1)
        elif delta == 2:
            current = min(M,current+1)
            while current < M and current not in problematicni:
                current+=1
        elif delta == -2:
            current = max(0,current-1)
            while current > 0 and current not in problematicni:
                current-=1

        if current != old_current:
            show(current)

    def quit():
        spremi_trenutni()
        frame.destroy()


    frame = tk.Toplevel(root)
    frame.title('Skenovi')
    frame.geometry('+0+0')

    slika = tk.Label(frame)
    slika.grid(row=0,column=0,rowspan=40)

    tv_kod = tk.StringVar(name='kod')
    tk.Label(frame,text='KOD:').grid(row=1,column=1,sticky=tk.E)
    Ekod = tk.Entry(frame, textvariable=tv_kod, width='12')
    Ekod.grid(row=1,column=2,sticky=tk.W,padx=5)
    tv_kod.trace_id = tv_kod.trace_add('write', update_polja)

    tk.Label(frame,text='IME:').grid(row=2,column=1,sticky=tk.E)
    Lime = tk.Label(frame,text='',font='sans 18 bold', anchor='w')
    Lime.grid(row=2,column=2,sticky=tk.W,padx=5)

    tv_jmbag = tk.StringVar(name='jmbag')
    tk.Label(frame,text='JMBAG:').grid(row=3,column=1,sticky=tk.E)
    Ejmbag = tk.Entry(frame, textvariable=tv_jmbag, width='12')
    Ejmbag.grid(row=3,column=2,sticky=tk.W,padx=5)
    tv_jmbag.trace_id = tv_jmbag.trace_add('write', update_polja)

    poz = 6
    tk.Label(frame,text='ZADATAK:').grid(row=poz,column=1,sticky=tk.E)
    Ezadatak = tk.Entry(frame, width='12')
    Ezadatak.grid(row=poz,column=2, sticky=tk.W, padx=5)

    tk.Label(frame,text='BODOVI:').grid(row=poz+1,column=1,sticky=tk.E)
    Ebodovi = tk.Entry(frame, width='12')
    Ebodovi.grid(row=poz+1,column=2, sticky=tk.W,padx=5)

    tk.Button(frame, text='>>>\nIdući\nproblematični', command=lambda: move(+2),width=10).grid(row=poz+6,column=2)
    tk.Button(frame, text='<<<\nPrethodni\nproblematični', command=lambda: move(-2),width=10).grid(row=poz+6,column=1)

    tk.Button(frame, text='>\nIdući', command=lambda: move(+1),width=10).grid(row=poz+10,column=2)
    tk.Button(frame, text='<\nPrethodni', command=lambda: move(-1),width=10).grid(row=poz+10,column=1)

    tk.Button(frame, text='Lice/Naličje', command=toggle).grid(row=poz+15,column=1,columnspan=2)

    status = tk.Label(frame,text='')
    status.grid(row=poz+13,column=1,columnspan=2)

    pazi = tk.Label(frame,text='',fg="red", width=30, height=5)
    pazi.grid(row=poz+19,column=1,columnspan=2)

    tk.Button(frame,text='Ovaj list je prazan\nBRIŠI',command=erase).grid(row=poz+25,column=1,columnspan=2)


    tk.Button(frame, text='Završi', command=quit).grid(row=38,column=1,columnspan=2)

    move(0,first=True)

    root.wait_window(frame)
    tv_kod.trace_remove('write', tv_kod.trace_id)
    tv_jmbag.trace_remove('write', tv_jmbag.trace_id)

def kolizija(root, lista_ijeva_u_koliziji, lista, kod2jmbag, jmbag2kod, BROJ_ZADATAKA, lista_brisani, dir_skenovi):

    current = None
    Front = True

    def loadimage(image_name):
        image = Image.open(os.path.join(dir_skenovi,image_name))
        height = int(frame.winfo_screenheight()*0.85)
        width = int(21*height/29.7)
        image = image.resize((width, height), Image.ANTIALIAS)
        canvas = tk.Canvas(frame, width = width, height = height, bg = "#000000")
        photo = ImageTk.PhotoImage(image, master = canvas)
        slika['image'] = photo
        slika.photo = photo

    def spremi_trenutni():
        lista[current]['kod'] = Ekod.get()
        lista[current]['zadatak'] = Ezadatak.get()
        lista[current]['bodovi'] = Ebodovi.get()

    def clear():
        Ekod.delete(0, tk.END)
        Ejmbag.delete(0, tk.END)
        Ezadatak.delete(0, tk.END)
        Ebodovi.delete(0, tk.END)

    def toggle():
        nonlocal Front
        if Front:
            loadimage(lista[current]['slikaB'])
            Front = False
        else:
            loadimage(lista[current]['slikaF'])
            Front = True

    def erase():
        if lista_brisani[current] == False:
            lista_brisani[current] = True
            pazi['text'] = '------ ZA BRISANJE ------'
        else:
            lista_brisani[current] = False
            pazi['text'] = 'Na više\nlistova su označeni bodovi\nveći od nula.'

    def update_polja(var,*kwargs):
        if var=='kod':
            kod = tv_kod.get()
            if kod in kod2jmbag:
                Lime['text'] = kod2jmbag[kod]['IME'] + ' ' + kod2jmbag[kod]['PREZIME']
                jmbag = kod2jmbag[kod]['JMBAG']
            else:
                Lime['text'] = ''
                jmbag = ''
            tv_jmbag.trace_remove('write', tv_jmbag.trace_id)
            tv_jmbag.set(jmbag)
            tv_jmbag.trace_id = tv_jmbag.trace_add('write', update_polja)

        elif var=='jmbag':
            jmbag = tv_jmbag.get()
            if jmbag in jmbag2kod:
                kod = jmbag2kod[jmbag]
                Lime['text'] = kod2jmbag[kod]['IME'] + ' ' + kod2jmbag[kod]['PREZIME']
            else:
                Lime['text'] = ''
                kod = ''
            tv_kod.trace_remove('write', tv_kod.trace_id)
            tv_kod.set(kod)
            tv_kod.trace_id = tv_kod.trace_add('write', update_polja)

    def show(current):
        nonlocal Front

        status['text'] =f'{lista_ijeva_u_koliziji.index(current)+1}/{len(lista_ijeva_u_koliziji)}'

        unos = lista[current]
        kod = unos['kod']
        zadatak = unos['zadatak']
        bodovi = unos['bodovi']
        slikaF = unos['slikaF']
        slikaB = unos['slikaB']

        pazi['text'] ='------ ZA BRISANJE ------' if lista_brisani[current]==True else 'Na više\nlistova su označeni bodovi\nveći od nula.'

        loadimage(slikaF)
        Front = True

        clear()
        Ekod.insert(0,kod)
        Ezadatak.insert(0,zadatak)
        Ebodovi.insert(0,bodovi)

    def move(delta,first=False):
        if not first:
            spremi_trenutni()
        nonlocal current

        old_current = current
        M = len(lista_ijeva_u_koliziji)-1

        if delta == 0:
            current = lista_ijeva_u_koliziji[0]
        elif delta == 1:
            tmp_i = lista_ijeva_u_koliziji.index(current)
            current = lista_ijeva_u_koliziji[min(M,tmp_i+1)]
        elif delta == -1:
            tmp_i = lista_ijeva_u_koliziji.index(current)
            current = lista_ijeva_u_koliziji[max(0,tmp_i-1)]

        if current != old_current:
            show(current)

    def quit():
        spremi_trenutni()
        frame.destroy()

    frame = tk.Toplevel(root)
    frame.title('Skenovi')
    frame.geometry('+0+0')

    slika = tk.Label(frame)
    slika.grid(row=0,column=0,rowspan=40)

    tv_kod = tk.StringVar(name='kod')
    tk.Label(frame,text='KOD:').grid(row=1,column=1,sticky=tk.E)
    Ekod = tk.Entry(frame, textvariable=tv_kod, width='12')
    Ekod.grid(row=1,column=2,sticky=tk.W,padx=5)
    tv_kod.trace_id = tv_kod.trace_add('write', update_polja)

    tk.Label(frame,text='IME:').grid(row=2,column=1,sticky=tk.E)
    Lime = tk.Label(frame,text='',font='sans 18 bold', anchor='w')
    Lime.grid(row=2,column=2,sticky=tk.W,padx=5)

    tv_jmbag = tk.StringVar(name='jmbag')
    tk.Label(frame,text='JMBAG:').grid(row=3,column=1,sticky=tk.E)
    Ejmbag = tk.Entry(frame, textvariable=tv_jmbag, width='12')
    Ejmbag.grid(row=3,column=2,sticky=tk.W,padx=5)
    tv_jmbag.trace_id = tv_jmbag.trace_add('write', update_polja)

    poz = 6
    tk.Label(frame,text='ZADATAK:').grid(row=poz,column=1,sticky=tk.E)
    Ezadatak = tk.Entry(frame, width='12')
    Ezadatak.grid(row=poz,column=2, sticky=tk.W, padx=5)

    tk.Label(frame,text='BODOVI:').grid(row=poz+1,column=1,sticky=tk.E)
    Ebodovi = tk.Entry(frame, width='12')
    Ebodovi.grid(row=poz+1,column=2, sticky=tk.W,padx=5)

    tk.Button(frame, text='>\nIdući', command=lambda: move(+1),width=10).grid(row=poz+10,column=2)
    tk.Button(frame, text='<\nPrethodni', command=lambda: move(-1),width=10).grid(row=poz+10,column=1)

    tk.Button(frame, text='Lice/Naličje', command=toggle).grid(row=poz+15,column=1,columnspan=2)

    status = tk.Label(frame,text='')
    status.grid(row=poz+13,column=1,columnspan=2)

    pazi = tk.Label(frame,text='',fg="red", width=30, height=5)
    pazi.grid(row=poz+19,column=1,columnspan=2)

    tk.Button(frame,text='Ovaj list je prazan\nBRIŠI',command=erase).grid(row=poz+25,column=1,columnspan=2)


    tk.Button(frame, text='Završi', command=quit).grid(row=38,column=1,columnspan=2)

    move(0,first=True)

    root.wait_window(frame)
    tv_kod.trace_remove('write', tv_kod.trace_id)
    tv_jmbag.trace_remove('write', tv_jmbag.trace_id)


def Obradi_nebodovane(root, nebodovani, lista, kod2jmbag, jmbag2kod, BROJ_ZADATAKA, lista_brisani, dir_skenovi):
    current = None
    cur_set = None
    cur_i = None
    Front = True

    def loadimage(image_name):
        image = Image.open(os.path.join(dir_skenovi,image_name))
        height = int(frame.winfo_screenheight()*0.85)
        width = int(21*height/29.7)
        image = image.resize((width, height), Image.ANTIALIAS)
        canvas = tk.Canvas(frame, width = width, height = height, bg = "#000000")
        photo = ImageTk.PhotoImage(image, master = canvas)
        slika['image'] = photo
        slika.photo = photo

    def spremi_trenutni():
        lista[current]['kod'] = Ekod.get()
        lista[current]['zadatak'] = Ezadatak.get()
        lista[current]['bodovi'] = Ebodovi.get()

    def clear():
        Ekod.delete(0, tk.END)
        Ejmbag.delete(0, tk.END)
        Ezadatak.delete(0, tk.END)
        Ebodovi.delete(0, tk.END)

    def toggle():
        nonlocal Front
        if Front:
            loadimage(lista[current]['slikaB'])
            Front = False
        else:
            loadimage(lista[current]['slikaF'])
            Front = True

    def erase():
        if lista_brisani[current] == False:
            lista_brisani[current] = True
            pazi['text'] = '------ ZA BRISANJE ------'
        else:
            lista_brisani[current] = False
            pazi['text'] = 'Nisu upisani bodovi.'

    def update_polja(var,*kwargs):
        if var=='kod':
            kod = tv_kod.get()
            if kod in kod2jmbag:
                Lime['text'] = kod2jmbag[kod]['IME'] + ' ' + kod2jmbag[kod]['PREZIME']
                jmbag = kod2jmbag[kod]['JMBAG']
            else:
                Lime['text'] = ''
                jmbag = ''
            tv_jmbag.trace_remove('write', tv_jmbag.trace_id)
            tv_jmbag.set(jmbag)
            tv_jmbag.trace_id = tv_jmbag.trace_add('write', update_polja)

        elif var=='jmbag':
            jmbag = tv_jmbag.get()
            if jmbag in jmbag2kod:
                kod = jmbag2kod[jmbag]
                Lime['text'] = kod2jmbag[kod]['IME'] + ' ' + kod2jmbag[kod]['PREZIME']
            else:
                Lime['text'] = ''
                kod = ''
            tv_kod.trace_remove('write', tv_kod.trace_id)
            tv_kod.set(kod)
            tv_kod.trace_id = tv_kod.trace_add('write', update_polja)


    def show(current):
        nonlocal Front

        status['text'] =f'{cur_i+1}/{len(nebodovani[cur_set])}'
        status2['text'] =f'{cur_set+1}/{len(nebodovani)}'

        unos = lista[current]
        kod = unos['kod']
        zadatak = unos['zadatak']
        bodovi = unos['bodovi']
        slikaF = unos['slikaF']
        slikaB = unos['slikaB']

        pazi['text'] ='------ ZA BRISANJE ------' if lista_brisani[current]==True else 'Nisu upisani bodovi.'

        loadimage(slikaF)
        Front = True

        clear()
        Ekod.insert(0,kod)
        Ezadatak.insert(0,zadatak)
        Ebodovi.insert(0,bodovi)

    def move(delta,first=False):
        if not first:
            spremi_trenutni()
        nonlocal current, cur_set, cur_i

        old_current = current
        M = len(nebodovani)-1

        if delta == 0:
            cur_set = 0
            cur_i = 0
        elif delta == 1:
            L = len(nebodovani[cur_set])-1
            cur_i = min(L,cur_i+1)
        elif delta == -1:
            L = len(nebodovani[cur_set])-1
            cur_i = max(0,cur_i-1)
        elif delta == 2:
            cur_set = min(M,cur_set+1)
            cur_i = 0
        elif delta == -2:
            cur_set = max(0,cur_set-1)
            cur_i = 0

        current = nebodovani[cur_set][cur_i]

        if current != old_current:
            show(current)

    def quit():
        spremi_trenutni()
        frame.destroy()


    frame = tk.Toplevel(root)
    frame.title('Skenovi')
    frame.geometry('+0+0')

    slika = tk.Label(frame)
    slika.grid(row=0,column=0,rowspan=40)

    tv_kod = tk.StringVar(name='kod')
    tk.Label(frame,text='KOD:').grid(row=1,column=1,sticky=tk.E)
    Ekod = tk.Entry(frame, textvariable=tv_kod, width='12')
    Ekod.grid(row=1,column=2,sticky=tk.W,padx=5)
    tv_kod.trace_id = tv_kod.trace_add('write', update_polja)

    tk.Label(frame,text='IME:').grid(row=2,column=1,sticky=tk.E)
    Lime = tk.Label(frame,text='',font='sans 18 bold', anchor='w')
    Lime.grid(row=2,column=2,sticky=tk.W,padx=5)

    tv_jmbag = tk.StringVar(name='jmbag')
    tk.Label(frame,text='JMBAG:').grid(row=3,column=1,sticky=tk.E)
    Ejmbag = tk.Entry(frame, textvariable=tv_jmbag, width='12')
    Ejmbag.grid(row=3,column=2,sticky=tk.W,padx=5)
    tv_jmbag.trace_id = tv_jmbag.trace_add('write', update_polja)

    poz = 6
    tk.Label(frame,text='ZADATAK:').grid(row=poz,column=1,sticky=tk.E)
    Ezadatak = tk.Entry(frame, width='12')
    Ezadatak.grid(row=poz,column=2, sticky=tk.W, padx=5)

    tk.Label(frame,text='BODOVI:').grid(row=poz+1,column=1,sticky=tk.E)
    Ebodovi = tk.Entry(frame, width='12')
    Ebodovi.grid(row=poz+1,column=2, sticky=tk.W,padx=5)

    tk.Button(frame, text='>>>\nIdući\nnebodovani', command=lambda: move(+2),width=10).grid(row=poz+10,column=2)
    tk.Button(frame, text='<<<\nPrethodni\nnebodovani', command=lambda: move(-2),width=10).grid(row=poz+10,column=1)

    tk.Button(frame, text='>\nIdući', command=lambda: move(+1),width=10).grid(row=poz+6,column=2)
    tk.Button(frame, text='<\nPrethodni', command=lambda: move(-1),width=10).grid(row=poz+6,column=1)

    tk.Button(frame, text='Lice/Naličje', command=toggle).grid(row=poz+15,column=1,columnspan=2)

    status = tk.Label(frame,text='')
    status.grid(row=poz+5,column=1,columnspan=2)

    status2 = tk.Label(frame,text='')
    status2.grid(row=poz+9,column=1,columnspan=2)

    pazi = tk.Label(frame,text='',fg="red", width=30, height=5)
    pazi.grid(row=poz+19,column=1,columnspan=2)

    tk.Button(frame,text='Ovaj list je prazan\nBRIŠI',command=erase).grid(row=poz+25,column=1,columnspan=2)


    tk.Button(frame, text='Završi', command=quit).grid(row=38,column=1,columnspan=2)

    move(0,first=True)

    root.wait_window(frame)
    tv_kod.trace_remove('write', tv_kod.trace_id)
    tv_jmbag.trace_remove('write', tv_jmbag.trace_id)


def update_Studenti(Studenti,kod_old,zad_old,lista,lista_brisani,BROJ_ZADATAKA,kod2jmbag):
    tmp = Studenti[kod_old].zadaci_index[zad_old]
    Studenti[kod_old].zadaci_index[zad_old] = []
    mijenjan_kod=False
    for i in tmp:
        unos = lista[i]
        kod = unos['kod']
        zadatak = unos['zadatak']

        if lista_brisani[i]:
            kod = BRISAN_
        elif kod not in kod2jmbag:
            kod = KOD_NEPOZNAT_

        if kod in kod2jmbag and kod!=kod_old:
            mijenjan_kod=True

        try:
            zad = int(zadatak)
        except:
            zad = 0

        if zad < 0 or zad > BROJ_ZADATAKA:
            zad = 0

        if kod not in Studenti:
            Studenti[kod] = Student(kod2jmbag[kod]['JMBAG'], kod2jmbag[kod]['IME'], kod2jmbag[kod]['PREZIME'], BROJ_ZADATAKA)
        Studenti[kod].zadaci_index[zad].append(i)

    if len(tmp) == len(Studenti[kod_old].zadaci_index[zad_old]):
        poz_bod = 0
        for i in tmp:
            try:
                bod = int(lista[i]['bodovi'])
                if(bod)>0:
                    poz_bod += 1
            except:
                pass

        if poz_bod>1:
            for i in tmp:
                lista[i]['bodovi']=None

    return mijenjan_kod

def provjeri_osobu(root, za_provjeriti, old_kod, Studenti, lista, kod2jmbag, jmbag2kod, BROJ_ZADATAKA, lista_brisani, dir_skenovi):

    current = None
    Front = True

    def loadimage(image_name):
        image = Image.open(os.path.join(dir_skenovi,image_name))
        height = int(frame.winfo_screenheight()*0.85)
        width = int(21*height/29.7)
        image = image.resize((width, height), Image.ANTIALIAS)
        canvas = tk.Canvas(frame, width = width, height = height, bg = "#000000")
        photo = ImageTk.PhotoImage(image, master = canvas)
        slika['image'] = photo
        slika.photo = photo

    def spremi_trenutni():
        lista[current]['kod'] = Ekod.get()
        lista[current]['zadatak'] = Ezadatak.get()
        lista[current]['bodovi'] = Ebodovi.get()

    def clear():
        Ekod.delete(0, tk.END)
        Ejmbag.delete(0, tk.END)
        Ezadatak.delete(0, tk.END)
        Ebodovi.delete(0, tk.END)

    def toggle():
        nonlocal Front
        if Front:
            loadimage(lista[current]['slikaB'])
            Front = False
        else:
            loadimage(lista[current]['slikaF'])
            Front = True

    def erase():
        if lista_brisani[current] == False:
            lista_brisani[current] = True
            pazi['text'] = '------ ZA BRISANJE ------'
        else:
            lista_brisani[current] = False
            pazi['text'] = ''

    def update_polja(var,*kwargs):
        if var=='kod':
            kod = tv_kod.get()
            if kod in kod2jmbag:
                Lime['text'] = kod2jmbag[kod]['IME'] + ' ' + kod2jmbag[kod]['PREZIME']
                jmbag = kod2jmbag[kod]['JMBAG']
            else:
                Lime['text'] = ''
                jmbag = ''
            tv_jmbag.trace_remove('write', tv_jmbag.trace_id)
            tv_jmbag.set(jmbag)
            tv_jmbag.trace_id = tv_jmbag.trace_add('write', update_polja)

        elif var=='jmbag':
            jmbag = tv_jmbag.get()
            if jmbag in jmbag2kod:
                kod = jmbag2kod[jmbag]
                Lime['text'] = kod2jmbag[kod]['IME'] + ' ' + kod2jmbag[kod]['PREZIME']
            else:
                Lime['text'] = ''
                kod = ''
            tv_kod.trace_remove('write', tv_kod.trace_id)
            tv_kod.set(kod)
            tv_kod.trace_id = tv_kod.trace_add('write', update_polja)

    def show(current):
        nonlocal Front

        status['text'] =f'{za_provjeriti.index(current)+1}/{len(za_provjeriti)}'

        unos = lista[current]
        kod = unos['kod']
        zadatak = unos['zadatak']
        bodovi = unos['bodovi']
        slikaF = unos['slikaF']
        slikaB = unos['slikaB']

        pazi['text'] ='------ ZA BRISANJE ------' if lista_brisani[current]==True else ''

        loadimage(slikaF)
        Front = True

        clear()
        Ekod.insert(0,kod)
        Ezadatak.insert(0,zadatak)
        Ebodovi.insert(0,bodovi)

    def move(delta,first=False):
        if not first:
            spremi_trenutni()
        nonlocal current

        old_current = current
        M = len(za_provjeriti)-1

        if delta == 0:
            current = za_provjeriti[0]
        elif delta == 1:
            tmp_i = za_provjeriti.index(current)
            current = za_provjeriti[min(M,tmp_i+1)]
        elif delta == -1:
            tmp_i = za_provjeriti.index(current)
            current = za_provjeriti[max(0,tmp_i-1)]

        if current != old_current:
            show(current)

    def quit():
        spremi_trenutni()
        frame.destroy()

    frame = tk.Toplevel(root)
    frame.title('Skenovi')
    frame.geometry('+0+0')

    slika = tk.Label(frame)
    slika.grid(row=0,column=0,rowspan=40)

    tv_kod = tk.StringVar(name='kod')
    tk.Label(frame,text='KOD:').grid(row=1,column=1,sticky=tk.E)
    Ekod = tk.Entry(frame, textvariable=tv_kod, width='12')
    Ekod.grid(row=1,column=2,sticky=tk.W,padx=5)
    tv_kod.trace_id = tv_kod.trace_add('write', update_polja)

    tk.Label(frame,text='IME:').grid(row=2,column=1,sticky=tk.E)
    Lime = tk.Label(frame,text='',font='sans 18 bold', anchor='w')
    Lime.grid(row=2,column=2,sticky=tk.W,padx=5)

    tv_jmbag = tk.StringVar(name='jmbag')
    tk.Label(frame,text='JMBAG:').grid(row=3,column=1,sticky=tk.E)
    Ejmbag = tk.Entry(frame, textvariable=tv_jmbag, width='12')
    Ejmbag.grid(row=3,column=2,sticky=tk.W,padx=5)
    tv_jmbag.trace_id = tv_jmbag.trace_add('write', update_polja)

    poz = 6
    tk.Label(frame,text='ZADATAK:').grid(row=poz,column=1,sticky=tk.E)
    Ezadatak = tk.Entry(frame, width='12')
    Ezadatak.grid(row=poz,column=2, sticky=tk.W, padx=5)

    tk.Label(frame,text='BODOVI:').grid(row=poz+1,column=1,sticky=tk.E)
    Ebodovi = tk.Entry(frame, width='12')
    Ebodovi.grid(row=poz+1,column=2, sticky=tk.W,padx=5)

    tk.Button(frame, text='>\nIdući', command=lambda: move(+1),width=10).grid(row=poz+10,column=2)
    tk.Button(frame, text='<\nPrethodni', command=lambda: move(-1),width=10).grid(row=poz+10,column=1)

    tk.Button(frame, text='Lice/Naličje', command=toggle).grid(row=poz+15,column=1,columnspan=2)

    status = tk.Label(frame,text='')
    status.grid(row=poz+13,column=1,columnspan=2)

    pazi = tk.Label(frame,text='',fg="red", width=30, height=5)
    pazi.grid(row=poz+19,column=1,columnspan=2)

    tk.Button(frame,text='Ovaj list je prazan\nBRIŠI',command=erase).grid(row=poz+25,column=1,columnspan=2)


    tk.Button(frame, text='Završi', command=quit).grid(row=38,column=1,columnspan=2)

    move(0,first=True)

    root.wait_window(frame)
    tv_kod.trace_remove('write', tv_kod.trace_id)
    tv_jmbag.trace_remove('write', tv_jmbag.trace_id)

    for zz in range(BROJ_ZADATAKA+1):
        Studenti[old_kod].zadaci_index[zz].clear()

    for i in za_provjeriti:
        unos = lista[i]
        kod = unos['kod']
        zadatak = unos['zadatak']

        if lista_brisani[i]:
            kod = BRISAN_
        elif kod not in kod2jmbag:
            kod = KOD_NEPOZNAT_

        try:
            zad = int(zadatak)
        except:
            zad = 0

        if zad < 0 or zad > BROJ_ZADATAKA:
            zad = 0

        if kod not in Studenti:
            Studenti[kod] = Student(kod2jmbag[kod]['JMBAG'], kod2jmbag[kod]['IME'], kod2jmbag[kod]['PREZIME'], BROJ_ZADATAKA)
        Studenti[kod].zadaci_index[zad].append(i)
