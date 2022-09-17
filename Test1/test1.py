
from tkinter import *
from tkinter import ttk

def calculate(*args):
    try:
        value = float(feet.get())
        meters.set(int(0.3048 * value * 10000.0 + 0.5)/10000.0)
    except ValueError:
        pass

root = Tk()
root.title("Menu Title")

cMenuFrame = ttk.Frame(root, padding="3 3 12 12")
cMenuFrame.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)


btn = list()
for n in range(1,21) :
    btn[n] = ttk.Button(cMenuFrame,text=n)
    btn[n].grid(column=1,row=n+1)

feet = StringVar()
feet_entry = ttk.Entry(cMenuFrame, width=7, textvariable=feet)
feet_entry.grid(column=2, row=25, sticky=(W, E))

meters = StringVar()
ttk.Label(cMenuFrame, textvariable=meters).grid(column=2, row=2, sticky=(W, E))

ttk.Button(cMenuFrame, text="Calculate", command=calculate).grid(column=3, row=27, sticky=W)

ttk.Label(cMenuFrame, text="feet").grid(column=3, row=1, sticky=W)
ttk.Label(cMenuFrame, text="is equivalent to").grid(column=1, row=28, sticky=E)
ttk.Label(cMenuFrame, text="meters").grid(column=3, row=28, sticky=W)

for child in cMenuFrame.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

feet_entry.focus()
root.bind("<Return>", calculate)

root.mainloop()