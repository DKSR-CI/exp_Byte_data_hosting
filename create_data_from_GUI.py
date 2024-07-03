from data_functions import *
import tkinter as tk
import json
import os

#print('Bitte nenne mir eine Stadt oder Gemeinde.')

current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir = os.path.normpath(current_dir)
current_dir = current_dir.replace("\\", "/")

def download_data(current_dir, data_export):
    with open(current_dir + '/data/processed/chart_data.json', 'w') as fp:
        json.dump(data_export, fp)

def submit_data():
    city = entry.get()  # Get the data from the entry field
    #print(radio.get())
    try:
        export_1, LK_name = energy_data(city, radio.get())
        print('load 1')
        export_2 = kfz_data(city, LK_name, radio.get())
        print('load 2')
        export_3 = population_data(city, radio.get())
        print('load 3')
        export_4 = mobile_data(city, radio.get())
        print('load 4')

        data_export = {'Energie':export_1, 'KFZ':export_2, 'Bevoelkerung':export_3, 'Mobilfunk':export_4}

        download_data(current_dir, data_export)
        label2 = tk.Label(root, text="Die neuen Daten wurden erfolgreich erstellt.", fg="green", height=5)
        label2.pack_forget()
        label2.pack()
    except Exception as error:
        # handle the exception
        print("An exception occurred:", error)
        label2 = tk.Label(root, text="Falsche Eingabe", fg="red", height=5)
        label2.pack_forget()
        label2.pack()

# Create the main window
root = tk.Tk()
root.title("JSON-files")

root.geometry("500x300")

# Create a label
label = tk.Label(root, text="Neuer Gemeindename:")
label.pack()

# Create an entry field
entry = tk.Entry(root)
entry.pack()

# Radio selection
label_2 = tk.Label(root, text="\nHierarchieebene:")
radio = tk.StringVar(value="town")
radio1 = tk.Radiobutton(root, text="Gemeinde/Krfr.St.", value="town", variable=radio)
radio2 = tk.Radiobutton(root, text="Landkreis", value="Lkr", variable=radio)
label_3 = tk.Label(root, text="\n")

label_2.pack()
radio1.pack()
radio2.pack()
label_3.pack()

# Create a submit button
submit_button = tk.Button(root, text="Download", command=submit_data)
submit_button.pack()

# Run the main event loop
root.mainloop()
