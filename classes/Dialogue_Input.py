import Tkinter


class CustomDialog(Tkinter.Tk):
    
    def __init__(self, prompt):
        super(CustomDialog, self).__init__()
        self.var = Tkinter.StringVar()

        self.label = Tkinter.Label(self, text=prompt)
        self.entry = Tkinter.Entry(self, textvariable=self.var)
        self.ok_button = Tkinter.Button(self, text="OK", command=self.on_ok)

        self.label.pack(side="top", fill="x")
        self.entry.pack(side="top", fill="x")
        self.ok_button.pack(side="right")

        self.entry.bind("<Return>", self.on_ok)

    def on_ok(self, event=None):
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.entry.focus_force()
        self.wait_window()
        return self.var.get()
