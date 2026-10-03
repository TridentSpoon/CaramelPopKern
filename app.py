#!/usr/bin/env python3
import json, os, queue, shutil, subprocess, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from backend import Backend, host_env
from updater import VERSION, replace_appimage

BG='#171512'; PANEL='#242019'; TEXT='#fff5e8'; MUTED='#d2c7b8'; GOLD='#efb366'; HOVER='#40362b'; DISABLED='#c5b9a8'
class App:
 def __init__(self, root):
  self.root=root; self.backend=Backend(); self.events=queue.Queue(); self.busy=False; self.rows=[]
  root.title('CaramelPopKern '+VERSION+' • Sugar coating the kernel'); root.geometry('1100x760'); root.minsize(850,600); root.configure(bg=BG)
  style=ttk.Style(); style.theme_use('clam')
  style.configure('.',background=PANEL,foreground=TEXT,font=('Sans',11))
  # Clam supplies its own light hover/disabled colours unless every state is mapped.
  style.configure('TFrame',background=PANEL)
  style.configure('TLabel',background=PANEL,foreground=TEXT)
  style.map('TLabel',foreground=[('disabled',DISABLED)])
  style.configure('TNotebook',background=BG)
  style.configure('TNotebook.Tab',background=PANEL,foreground=TEXT,padding=(18,12))
  style.map('TNotebook.Tab',background=[('selected',GOLD),('active',HOVER)],
            foreground=[('selected',BG),('disabled',DISABLED),('active',TEXT)])
  style.configure('TButton',background=HOVER,foreground=TEXT,padding=(12,8))
  style.map('TButton',background=[('disabled',PANEL),('pressed',GOLD),('active',HOVER)],
            foreground=[('disabled',DISABLED),('pressed',BG),('active',TEXT)])
  style.configure('TCheckbutton',background=PANEL,foreground=TEXT)
  style.map('TCheckbutton',background=[('active',PANEL)],
            foreground=[('disabled',DISABLED),('active',TEXT)],
            indicatorbackground=[('disabled',HOVER),('selected',GOLD),('!selected',MUTED)],
            indicatorforeground=[('selected',BG),('!selected',BG)])
  style.configure('Treeview',background=PANEL,foreground=TEXT,fieldbackground=PANEL,rowheight=30)
  style.map('Treeview',background=[('selected',GOLD)],foreground=[('selected',BG)])
  style.configure('Treeview.Heading',background=HOVER,foreground=TEXT)
  style.map('Treeview.Heading',background=[('active',HOVER)],foreground=[('active',TEXT)])
  header=tk.Frame(root,bg=BG); header.pack(fill='x',padx=26,pady=(22,0))
  tk.Label(header,text='CaramelPopKern',font=('Sans',26,'bold'),fg=GOLD,bg=BG).pack(side='left')
  self.menu=tk.Menu(root,tearoff=False,bg=PANEL,fg=TEXT,activebackground=GOLD,activeforeground=BG)
  self.menu.add_command(label='About & Upgrade…',command=self.about)
  self.menu.add_separator(); self.menu.add_command(label='Quit',command=root.destroy)
  hamburger=tk.Button(header,text='☰',font=('Sans',22),bg=BG,fg=TEXT,
                      activebackground=HOVER,activeforeground=TEXT,relief='flat',bd=0,
                      padx=12,pady=2,takefocus=True)
  hamburger.configure(command=lambda:self.menu.tk_popup(hamburger.winfo_rootx(),hamburger.winfo_rooty()+hamburger.winfo_height()))
  hamburger.pack(side='right')
  tk.Label(root,text='Sugar coating the kernel  •  Select your ingredients. Keep a way back.',fg=MUTED,bg=BG).pack(anchor='w',padx=28,pady=(4,18))
  # Flat navigation keeps the same geometry in every selection state.
  style.layout('Flat.TNotebook.Tab',[])
  navigation=tk.Frame(root,bg=BG); navigation.pack(fill='x',padx=24,pady=(0,0))
  self.tabs=ttk.Notebook(root,style='Flat.TNotebook'); self.tabs.pack(fill='both',expand=True,padx=24)
  self.pages={}; self.tab_buttons={}
  for name in ['Overview','Kernels','Gaming','Graphics & NVIDIA','Recovery']:
   frame=ttk.Frame(self.tabs,padding=20); self.tabs.add(frame,text=name); self.pages[name]=frame
   button=tk.Button(navigation,text=name,font=('Sans',11),bg=PANEL,fg=TEXT,
                    activebackground=PANEL,activeforeground=TEXT,relief='flat',bd=0,
                    padx=18,pady=12,highlightthickness=0,takefocus=True,
                    command=lambda page=frame:self.tabs.select(page))
   button.pack(side='left'); self.tab_buttons[name]=button
  def colour_tabs(event=None):
   selected=self.tabs.select()
   for name,button in self.tab_buttons.items():
    active=str(self.pages[name])==selected
    button.configure(bg=GOLD if active else PANEL,fg=BG if active else TEXT,
                     activebackground=GOLD if active else PANEL,activeforeground=BG if active else TEXT)
  self.tabs.bind('<<NotebookTabChanged>>',colour_tabs); colour_tabs()
  root.bind('<Control-Tab>',lambda event:self.tabs.select((self.tabs.index('current')+1)%len(self.pages)))
  self.status=tk.StringVar(value='Inspecting this machine…'); tk.Label(root,textvariable=self.status,fg=MUTED,bg=BG,anchor='w').pack(fill='x',padx=26,pady=12)
  self.overview= self.textbox(self.pages['Overview'])
  ttk.Button(self.pages['Overview'],text='Refresh system',command=self.refresh).pack(anchor='e',pady=10)
  self.kernel_tree=ttk.Treeview(self.pages['Kernels'],columns=('state',),show='tree headings'); self.kernel_tree.heading('#0',text='Kernel / package'); self.kernel_tree.heading('state',text='Status'); self.kernel_tree.pack(fill='both',expand=True)
  ttk.Label(self.pages['Kernels'],text='Install and default-boot switching are not yet enabled. Existing kernels are never removed.',wraplength=850).pack(anchor='w',pady=12)
  ttk.Button(self.pages['Kernels'],text='View selected kernel',command=self.kernel_detail).pack(anchor='e')
  self.gaming_list=ttk.Frame(self.pages['Gaming']); self.gaming_list.pack(fill='both',expand=True)
  ttk.Button(self.pages['Gaming'],text='Review selected installs',command=self.review).pack(anchor='e',pady=10)
  self.graphics=self.textbox(self.pages['Graphics & NVIDIA'])
  ttk.Label(self.pages['Graphics & NVIDIA'],text='Driver discovery is available. Driver switching, DLSS/FSR upgrades and OptiScaler activation are not enabled in this build.',wraplength=850).pack(anchor='w',pady=12)
  self.recovery=self.textbox(self.pages['Recovery'])
  ttk.Button(self.pages['Recovery'],text='Refresh history',command=self.show_history).pack(anchor='e',pady=10)
  root.after(100,self.poll); self.refresh()
 def about(self):
  win=tk.Toplevel(self.root); win.title('About CaramelPopKern'); win.geometry('620x440'); win.configure(bg=PANEL)
  ttk.Label(win,text='CaramelPopKern',font=('Sans',22,'bold'),foreground=GOLD).pack(pady=(24,6))
  ttk.Label(win,text='Version '+VERSION+' • Sugar coating the kernel').pack(pady=6)
  ttk.Label(win,text='A selective Linux kernel and gaming manager.\n\nEarly development release: kernel/driver switching and automatic\nrollback are unfinished. OptiScaler activation is unavailable.\n\nUpdates use AppImage files. No online release source is configured.',wraplength=560,justify='center').pack(padx=20,pady=16)
  ttk.Button(win,text='Check for updates',command=lambda:messagebox.showinfo('Online updates unavailable','No release repository has been configured yet. Download a CaramelPopKern AppImage from the project publisher, then use Install downloaded update.',parent=win)).pack(pady=5)
  button=ttk.Button(win,text='Install downloaded update…',command=lambda:self.upgrade(win)); button.pack(pady=5)
  if not os.environ.get('APPIMAGE'):
   button.configure(state='disabled')
   ttk.Label(win,text='Run the AppImage release to enable in-app replacement.').pack(pady=5)
  ttk.Button(win,text='Close',command=win.destroy).pack(pady=10)
 def upgrade(self,parent):
  if self.busy:
   messagebox.showinfo('Operation in progress','Wait for the current operation before updating.',parent=parent); return
  candidate=filedialog.askopenfilename(parent=parent,title='Choose downloaded CaramelPopKern AppImage',filetypes=[('AppImage releases','*.AppImage')])
  if not candidate: return
  if not messagebox.askyesno('Review update','Only install a CaramelPopKern release from a publisher you trust. This app cannot verify its publisher, signature or version.\n\nSelected file:\n'+candidate+'\n\nReplace the current AppImage and preserve a backup? The selected file will not be executed now.',parent=parent): return
  try:
   backup=replace_appimage(os.environ['APPIMAGE'],candidate)
  except (OSError,ValueError) as e:
   messagebox.showerror('Update failed',str(e),parent=parent); return
  messagebox.showinfo('Update installed','Close the app and reopen the AppImage to use the update.\n\nPrevious version saved at:\n'+str(backup)+'\n\nYour settings and history were retained.',parent=parent)
 def textbox(self,parent):
  box=tk.Text(parent,bg=PANEL,fg=TEXT,insertbackground=GOLD,selectbackground=GOLD,selectforeground=BG,relief='flat',wrap='word',font=('Sans',11),padx=16,pady=16); box.pack(fill='both',expand=True); box.configure(state='disabled'); return box
 def write(self,box,text): box.configure(state='normal'); box.delete('1.0','end'); box.insert('end',text); box.configure(state='disabled')
 def work(self,fn,callback):
  if self.busy: return
  self.busy=True
  def worker():
   try: self.events.put((callback,fn(),None))
   except Exception as e: self.events.put((callback,None,str(e)))
  threading.Thread(target=worker,daemon=True).start()
 def poll(self):
  try:
   while True:
    cb,result,error=self.events.get_nowait(); self.busy=False
    if error: self.status.set(error); messagebox.showerror('CaramelPopKern',error)
    else: cb(result)
  except queue.Empty: pass
  self.root.after(100,self.poll)
 def refresh(self):
  self.status.set('Reading system and configured package repositories…')
  self.work(lambda:(self.backend.summary(),self.backend.kernels(),self.backend.packages(),self.backend.drivers()),self.loaded)
 def loaded(self,data):
  summary,kernels,self.rows,drivers=data
  self.write(self.overview,'YOUR CURRENT INGREDIENTS\n\n'+'\n\n'.join(k+'\n'+v for k,v in summary.items())+'\n\nThis first build performs read-only discovery. Gaming installs require a reviewed plan and administrator authentication.')
  self.kernels=kernels
  for i in self.kernel_tree.get_children(): self.kernel_tree.delete(i)
  for i,row in enumerate(kernels): self.kernel_tree.insert('', 'end',iid=str(i),text=row['name'],values=(row['state'],))
  for w in self.gaming_list.winfo_children(): w.destroy()
  self.selections={}
  for row in self.rows:
   var=tk.BooleanVar(value=False); self.selections[row['key']]=var
   state='Installed' if row['installed'] else 'Available' if row['available'] else 'Unavailable in configured repositories'
   line=ttk.Frame(self.gaming_list); line.pack(fill='x',pady=5)
   check=ttk.Checkbutton(line,text=row['title'],variable=var,width=20); check.pack(side='left')
   if row['installed'] or not row['available']: check.configure(state='disabled')
   ttk.Label(line,text=row['description']+'  •  '+state,wraplength=650).pack(side='left',padx=12)
  self.write(self.graphics,drivers+'\n\nPER-GAME GRAPHICS — PLANNED\n\nDLSS / FSR / XeSS: require GPU, runtime and game compatibility checks.\nDLSS 5 Linux support: unverified.\nOptiScaler: OFF by default. No global activation. Known anti-cheat games must be blocked.\n\nNative upscaling, frame generation, VRR and HDR remain game/display-dependent; installing a driver cannot add them universally.')
  self.show_history(); self.status.set('Ready • No system settings have been changed by discovery')
 def kernel_detail(self):
  sel=self.kernel_tree.selection()
  if not sel: return
  row=self.kernels[int(sel[0])]
  messagebox.showinfo('Kernel details',row['name']+'\n'+row['state']+'\n\nBoot switching is not implemented yet. Retain your working kernel; select it from your boot menu for recovery. NVIDIA module and bootloader validation must precede enabling installation.')
 def review(self):
  packages=[r['package'] for r in self.rows if self.selections[r['key']].get() and r['available'] and not r['installed']]
  if not packages: messagebox.showinfo('Choose ingredients','Select one or more available applications.'); return
  self.status.set('Validating selected packages…'); self.work(lambda:self.backend.plan(packages),self.preview)
 def preview(self,plan):
  win=tk.Toplevel(self.root); win.title('Review installation'); win.geometry('760x430'); win.configure(bg=PANEL)
  box=self.textbox(win); self.write(box,'INSTALL SELECTED APPLICATIONS\n\n'+'\n'.join(plan['packages'])+'\n\nCommand:\n'+' '.join(plan['command'])+'\n\nThe package manager will show dependencies and ask for confirmation in a terminal. Cancel if it proposes removing or replacing existing packages. This does not activate gaming profiles or change the kernel.\n\nHistory records requested packages, not a complete dependency snapshot. Automatic uninstall/rollback is not yet supported.')
  ttk.Button(win,text='Continue in administrator terminal',command=lambda:self.execute(plan,win)).pack(pady=12)
 def execute(self,plan,win):
  terminals=[('xterm',['-e']),('konsole',['-e']),('gnome-terminal',['--wait','--'])]
  terminal=next(((shutil.which(n),args) for n,args in terminals if shutil.which(n)),None)
  pkexec=shutil.which('pkexec')
  if not terminal or not pkexec: messagebox.showerror('Terminal required','Install xterm, Konsole or GNOME Terminal and polkit to use reviewed installation.'); return
  win.destroy(); self.status.set('Package-manager transaction in progress…')
  def transaction():
   # Revalidate immediately before elevation; exact argv is passed without a shell.
   fresh=self.backend.plan(plan['packages']); fresh['status']='started'; path=self.backend.save(fresh)
   code=subprocess.call([terminal[0]]+terminal[1]+[pkexec]+fresh['command'],env=host_env())
   fresh['terminal_exit_code']=code; fresh['installed_after']=[p for p in fresh['packages'] if self.backend.installed(p)]
   fresh['status']='requested packages installed' if len(fresh['installed_after'])==len(fresh['packages']) else 'incomplete or cancelled'
   path.write_text(json.dumps(fresh,indent=2)); return fresh
  self.work(transaction,lambda result:(self.show_history(),self.status.set(result['status']),messagebox.showinfo('Transaction finished',result['status']+'\nRefresh the system view to update installed status.')))
 def show_history(self):
  entries=self.backend.history()
  text='RECOVERY & CHANGE HISTORY\n\nKeep a known-working kernel available in the boot menu. A desktop recovery button cannot rescue a machine that cannot boot.\n\nKernel rollback, driver rollback and automatic settings restore are not implemented in this first build. No kernel or driver changes are made.\n\n'
  text+='\n\n'.join(e.get('status','unknown')+'\nRequested: '+', '.join(e.get('packages',[])) for e in entries) or 'No recorded transactions.'
  self.write(self.recovery,text)

if __name__=='__main__':
 import sys
 if '--self-test' in sys.argv:
  root=tk.Tk(); root.withdraw(); app=App(root)
  import time
  deadline=time.monotonic()+60
  while app.busy and time.monotonic()<deadline:
   root.update(); time.sleep(.05)
  root.update()
  assert not app.busy, 'Discovery timed out'
  assert len(app.rows)==8, 'Discovery failed'
  print('AppImage GUI and live discovery check passed:',app.backend.family)
  root.destroy()
 else:
  root=tk.Tk(); App(root); root.mainloop()
