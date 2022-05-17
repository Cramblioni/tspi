
# tkinter interpreter
import tkinter as tk,tkinter.font as tkfont
from tspi import (parse,
                  _interpret,
                  StringIO,
                  IASSERT)

def _main():
  _root = tk.Tk()
  _root.title("tspi IDE")
  _root
  # getting tab size
  font = tkfont.Font()
  tabwidth = font.measure("    "*2)
  del font

  # now normal tk stuff
  progin = tk.Text(_root,width=50,height=50,highlightthickness=2,
                   tabs=tabwidth)
  progin.grid(row=0,column=0,rowspan=1000,sticky=tk.NSEW,padx=5,pady=5)
  textout = tk.Listbox(_root,width=50,height=20)
  textout.grid(row=0,column=1,sticky=tk.N,padx=5,pady=5,columnspan=10)
  testtext = tk.StringVar(_root,"Hello, World!")
  tk.Entry(_root,width=30,textvariable=testtext,
           font=("Courier New", 12, "bold"))\
          .grid(row=1,column=2,
                columnspan=8,sticky=tk.NE,
                padx=1)
  tk.Label(_root,text=": input",font=("Courier New", 12, "bold"))\
                         .grid(row=1,column=10,sticky=tk.E)
  textout.configure(font=("Courier New", 12, "bold"))
  progin.configure(font=("Courier New", 12, "bold"))
  
  def _onrun():
    nonlocal progin, testtext
    textout.delete(0,tk.END)
    try:
      textout.insert(tk.END,"prepping")
      textout.itemconfig(textout.size()-1,fg="blue")
      
      prog = parse(progin.get(0.0,tk.END))
      
      source_text = testtext.get()
      source = StringIO(source_text)
      
      textout.insert(tk.END,"starting")
      textout.itemconfig(textout.size()-1,fg="blue")
      try:
        while source.tell() < len(source_text):
          _root.update()
          _root.update_idletasks()
          tmp = _interpret(prog,source)
          textout.insert(tk.END,f"caught :: {tmp!r}")
      except IASSERT:
        textout.insert(tk.END,"Program terminated due to internal error")
        textout.itemconfig(textout.size()-1,fg="red")
      textout.insert(tk.END,"finished")
      textout.itemconfig(textout.size()-1,fg="blue")
        
    except SyntaxError as Err:
      textout.insert(tk.END,Err.args[0][:45])
      textout.itemconfig(textout.size()-1,fg="red")
      if Err.args[0][45:]:
        textout.insert(tk.END,Err.args[0][45:])
        textout.itemconfig(textout.size()-1,fg="red")
      
  tk.Button(text="Run",command=_onrun).grid(row=1,column=1,sticky=tk.NE)

if __name__ == "__main__":
  _main()
