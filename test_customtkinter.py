import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ctkApp:
        
    def __init__(self):
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.geometry("1200x400+200x200")
        self.root.title("Dynamic Scatterplot")
        self.root.update()
        self.frame = ctk.CTkFrame(master=self.root,
                                  height= self.root.winfo_height()*0.95,
                                  width = self.root.winfo_width()*0.66,
                                  fg_color="darkblue")
        self.frame.place(relx=0.33, rely=0.025)
        self.input =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=300,
                                   height=50,
                                   fg_color="darkblue")
        self.input.insert(0,100)
        self.input.place(relx=0.025,rely=0.5)
        self.slider = ctk.CTkSlider(master=self.root,
                                    width=300,
                                    height=20,
                                    from_=1,
                                    to=1000,
                                    number_of_steps=999,
                                    command=self.update_surface)
        self.slider.place(relx= 0.025,rely=0.75) 
        self.button = ctk.CTkButton(master = self.root,
                               text="Update Graph",
                               width=300,
                               height=50,
                               command=self.update_window)
        self.button.place(relx=0.025,rely=0.25)
        self.root.mainloop()
    
    def update_window(self):
        fig, ax = plt.subplots()
        fig.set_size_inches(11,5.3)
        global x,y,s,c
        x,y,s,c = np.random.rand(4,int(self.input.get()))
        ax.scatter(x,y,s*self.slider.get(),c)
        ax.axis("off")
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
        canvas = FigureCanvasTkAgg(fig,master=self.root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.33, rely=0.025)
        self.root.update()
        
    def update_surface(self,other):
        fig, ax = plt.subplots()
        fig.set_size_inches(11,5.3)
        ax.scatter(x,y,s*self.slider.get(),c)
        ax.axis("off")
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
        canvas = FigureCanvasTkAgg(fig,master=self.root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.33, rely=0.025)
        self.root.update()

if __name__ == "__main__":        
    CTK_Window = ctkApp()