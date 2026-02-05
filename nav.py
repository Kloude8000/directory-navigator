from tkinter import *
from ttkbootstrap import*
import os
import shutil
from collections import Counter
master = Window(themename='cyborg')
master.title('NAVVI')
master.geometry('400x450')

# under the hood
def dir_trav(event):
    global shownFiles
    global display_no
    global shown_F_and_C
    # get content of search entry widget
    search_con = search_entry.get()
    # delete content of search entry widget
    search_entry.delete(0, END)
    # import os module to work with files
    # check if directory exists
    check_exist = os.path.exists(search_con)
    if check_exist is True:
        var_show = os.listdir(search_con)
        # create label to display files
        shownFiles = Label(tab_dir, text = '\n'.join(var_show), font = 'century 10')
        shownFiles.grid(row = 4, column = 0)
        # show number of files
        file_num = len(os.listdir(search_con))
        display_no = Label(tab_dir, text= file_num, font = 'century 10', style = 'danger')
        display_no.grid(row = 1, column = 2, padx = 5)
        # list to store extensions
        ext_list = []
        # show file type and count
        for filename in os.listdir(search_con):
            root, ext = os.path.splitext(filename)
            ext_list.append(ext)
        # imported Counter from collections module
        list_ext = Counter(ext_list)
        show_count = ''
        for ext, count in list_ext.items():
            show_count = show_count + f'{ext} : {count}\n'
        # display ext and count on interface
        shown_F_and_C = Label(tab_dir, text= show_count, font = 'century 10', style = 'danger')
        shown_F_and_C.place(x = 240, y = 100)
    # if directory does not exist
    else:
        shownFiles = Label(tab_dir, text = 'Directory not found', style = 'danger', 
        font = 'century 12')
        shownFiles.grid(row = 4, column = 0)
    # counting number of lines
    line_getting = shownFiles.cget('text')
    line_converting = str(line_getting).count('\n')
    line_incrementer = line_converting + 1
    if line_incrementer >= 16:
        nb_dir.config(height=(line_incrementer+9)*15)

# function to clear first tab
def clearContent():
    if shownFiles.cget('text') != '':
        shownFiles.config(text = '')
    shownFiles.grid(row = 4, column = 0)
    if display_no.cget('text') != '':
        display_no.config(text='')
    if shown_F_and_C.cget('text') != '':
        shown_F_and_C.config(text='')
    nb_dir.config(height=350)
    master.geometry('400x450')

# under the hood tab 2
def path_exist():
    if not os.path.exists(dest_dir_entry.get()):
        os.mkdir(dest_dir_entry.get())
    if os.path.exists(src_dir_entry.get()):
    # iterating through contents of source directory
        for filename in os.listdir(src_dir_entry.get()):
          file_path = os.path.join(src_dir_entry.get(), filename)
          if file_path.endswith(ext_type.get()):
            shutil.copy(file_path, dest_dir_entry.get()) 

def Deletion():
    de_li = deletion_entry.get()
    if os.path.isdir(de_li):
        shutil.rmtree(de_li)
        deletion_entry.delete(0, END)
    elif os.path.isfile(de_li):
        os.remove(de_li)
        deletion_entry.delete(0, END)

# create function to show absolute path of file
def Display():
        #par_dir = os.pardir='C:\\'
        for root, dirs, files in os.walk('C:\\'):
            if show_entry.get() in files:
                sas = os.path.join(root, show_entry.get())
                L = Label(tab_move, text=sas, style='light', font='century 10')
                L.place(x=0, y=290)
                #show_entry.delete(0,END)
        #
        wide_count = len(L.cget('text'))
        if wide_count >= 55:
            nb_dir.config(width=wide_count*8)
        #if len(L.cget('text')) > 50:
            #nb_dir.config(width=500)
            #master.geometry('500x450')
        #if abs_show == '':
            #L.config(text='No filename entered') 
        

# create another function to clear content
def clearContent2():
    global L
    if L.cget('text') != '':
        L.config(text = '')
    nb_dir.config(width=400)
    master.geometry('400x450')
    

# create notebook tabs
nb_dir = Notebook(master, width = 400, height = 350)
nb_dir.grid(row = 0, column = 0)

# create first tab
tab_dir = Frame(nb_dir, relief=FLAT)

# create search directory label
search_label = Label(tab_dir, text='Search for directory', style= 'danger', font='century 10')
search_label.grid(row = 0, column = 0, padx = 5, pady = 5)

# create number of files label
no_of_files = Label(tab_dir, text = 'Number of files:', style = 'light', font = 'century 10')
no_of_files.grid(row= 1, column = 1, padx = 15)

# create shown files label
show_files = Label(tab_dir, text = 'Files in the directory', style = 'light', font = 'century 10')
show_files.grid(row = 2, column = 0, pady = 10, padx = 5)

# create file type label 
file_type = Label(tab_dir, text = 'File type & count', style = 'light', font = 'century 10')
file_type.grid(row= 2, column = 1)

# function to clear entry
def clear(event):
    search_entry.delete(0, END)

# create search entry 
search_entry = Entry(tab_dir, width = 30, style = 'success')
search_entry.grid(row = 1, column = 0, padx = 5)
search_entry.insert(0, 'Enter directory path')
search_entry.bind('<FocusIn>', clear)
search_entry.bind('<Return>', dir_trav)

# create second tab
tab_move = Frame(nb_dir, relief = FLAT)

# create entry for extension type
ext_type = Entry(tab_move, width = 10, style = 'success')
ext_type.place(x = 310, y = 10)

# create label for extension type
ext_type_label = Label(tab_move, text = 'Extension type', style = 'light', font = 'century 10')
ext_type_label.place(x = 210, y = 10)

# create function to clear entry for source
def clear1(event):
    if src_dir_entry.get() == 'Enter source directory':
        src_dir_entry.delete(0, END)
# create function to restore entry for destination
def restore1(event):
    if src_dir_entry.get() == '':
        src_dir_entry.insert(0, 'Enter source directory')

# create function to clear entry for source 
def clear2(event):
    if dest_dir_entry.get() == 'Enter destination directory':
        dest_dir_entry.delete(0, END)
# create function to restore entry for destination
def restore2(event):
    if dest_dir_entry.get() == '':
        dest_dir_entry.insert(0, 'Enter destination directory') 

# create entry for source directory
src_dir_entry = Entry(tab_move, width = 25, style = 'success')
src_dir_entry.place(x = 10, y = 70)
src_dir_entry.insert(0, 'Enter source directory')
src_dir_entry.bind('<FocusIn>', clear1)
src_dir_entry.bind('<FocusOut>', restore1)

# create entry for destination directory
dest_dir_entry = Entry(tab_move, width = 25, style = 'success')
dest_dir_entry.place(x = 220, y = 70)
dest_dir_entry.insert(0, 'Enter destination directory')
dest_dir_entry.bind('<FocusIn>', clear2)
dest_dir_entry.bind('<FocusOut>', restore2)

# create button to handle file movement 
button_move = Button(tab_move, text = 'move', style = 'warning outline', cursor='hand2', command= path_exist)
button_move.place(x = 10, y = 130)

# create partition 
divider = Label(tab_move, text = '_'*100, style = 'light')
divider.place(x = 0, y = 170)

# create label for deletion
deletion_label = Label(tab_move, text = 'Delete file or directory', style = 'light',
                       font = 'century 10')
deletion_label.place(x = 5, y = 180)

# create function to clear deletion entry
def clear3(event):
    if deletion_entry.get() == 'Enter file or directory path':
        deletion_entry.delete(0, END)

# create entry for deletion
deletion_entry = Entry(tab_move, width = 30, style = 'success')
deletion_entry.place(x = 5, y = 210)
deletion_entry.insert(0, 'Enter file or directory path')
deletion_entry.bind('<FocusIn>', clear3)

# create label for extension type not to delete
no_del_ext_type = Label(tab_move, text = 'Show path to file', style = 'light',
                        font = 'century 10')
no_del_ext_type.place(x = 270, y = 180)

# create label 
ent_lab = Label(tab_move, text = 'enter filename', style = 'light', font='century 10')
ent_lab.place(x = 275, y = 210)
# create entry for extension type not to delete
show_entry = Entry(tab_move, width = 15, style = 'success')
show_entry.place(x = 265, y = 230)

# create clear button
clear_button = Button(tab_dir, text = 'clear', style = 'warning outline', cursor = 'hand2',
                      command = clearContent)
clear_button.place(x = 340, y = 310)

# create deletion button
deletion_button = Button(tab_move, text = 'delete', style = 'warning outline', cursor='hand2',
                         command = Deletion)
deletion_button.place(x = 10, y = 267)

# create another clear button
clear_button2 = Button(tab_move, text = 'clear', style='warning outline', cursor = 'hand2',
                       command = clearContent2)
clear_button2.place(x = 156, y = 267)

# create button
but_dis = Button(tab_move, text = 'show', style='warning outline', cursor = 'hand2', command = Display)
but_dis.place(x = 315, y = 265)

# add tab to notebook
nb_dir.add(tab_dir, text = 'DIRECTORIES')
nb_dir.add(tab_move, text = 'MOVE')

master.mainloop()
