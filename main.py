
import os, json, shutil, calendar as pycalendar
from datetime import datetime, timedelta
from pathlib import Path

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.image import Image
from kivy.clock import Clock

KV = r"""
#:import dp kivy.metrics.dp

<RootScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color: rgba: app.col("inhalt")
            Rectangle: pos: self.pos; size: self.size

        BoxLayout:
            id: topbar
            size_hint_y: None
            height: dp(60)
            padding: dp(12), dp(6)
            canvas.before:
                Color: rgba: app.col("navigation")
                Rectangle: pos: self.pos; size: self.size
            Label:
                text: "Mein Organizer"
                bold: True
                font_size: "20sp"
                color: app.col("text")
                halign: "left"
                valign: "middle"
                text_size: self.size
            Label:
                text: app.clock_text
                font_size: "12sp"
                color: app.col("text_sekundaer")
                size_hint_x: .55
                halign: "right"
                valign: "middle"
                text_size: self.size

        BoxLayout:
            orientation: "horizontal"
            ScrollView:
                id: navscroll
                do_scroll_x: False
                size_hint_x: .30
                BoxLayout:
                    id: nav
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(6), dp(8)
                    spacing: dp(4)
                    canvas.before:
                        Color: rgba: app.col("navigation")
                        Rectangle: pos: self.pos; size: self.size

            BoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(12)
"""

class RootScreen(Screen):
    pass

class MeinOrganizerAndroid(App):
    title="Mein Organizer"
    clock_text=StringProperty("")
    current_page=StringProperty("Start")
    theme= {}
    default_theme={
        "navigation":"#202020","inhalt":"#2b2b2b","button":"#202020",
        "aktiv":"#3d5afe","hover":"#303030","karte":"#353535",
        "karte_innen":"#404040","eingabe":"#353535","dialog":"#2f2f2f",
        "button_hover":"#454545","text":"#ffffff",
        "text_sekundaer":"#aaaaaa","text_dezent":"#777777",
    }

    def build(self):
        self.data_dir=Path(self.user_data_dir)
        self.data_dir.mkdir(parents=True,exist_ok=True)
        self.attach_dir=self.data_dir/"notiz_anhaenge"
        self.attach_dir.mkdir(exist_ok=True)
        self.files={
            "tasks":self.data_dir/"aufgaben.json",
            "events":self.data_dir/"termine.json",
            "folders":self.data_dir/"aufgaben_ordner.json",
            "importance":self.data_dir/"aufgaben_ordner_wichtigkeit.json",
            "notes":self.data_dir/"notizen.json",
            "categories":self.data_dir/"kategorien.json",
            "theme":self.data_dir/"theme.json",
        }
        self.tasks=self.load("tasks",[])
        self.events=self.load("events",[])
        self.folders=self.load("folders",[])
        self.importance=self.load("importance",{})
        self.notes=self.load("notes",[])
        self.categories=self.load("categories",[])
        self.load_theme()
        Builder.load_string(KV)
        sm=ScreenManager()
        sm.add_widget(RootScreen(name="root"))
        return sm

    def on_start(self):
        Clock.schedule_interval(self.tick,1)
        self.show_page("Start")

    def tick(self,*_):
        self.clock_text=datetime.now().strftime("%H:%M:%S")+" Uhr"
        if self.current_page=="Start":
            # Refresh dashboard counters without forcing disruptive redraw too often.
            pass

    def load(self,key,default):
        try:
            if self.files[key].exists():
                with open(self.files[key],"r",encoding="utf-8") as f:
                    d=json.load(f)
                    return d
        except Exception: pass
        return default.copy() if isinstance(default,(list,dict)) else default

    def save(self,key,value):
        with open(self.files[key],"w",encoding="utf-8") as f:
            json.dump(value,f,ensure_ascii=False,indent=2)

    def load_theme(self):
        self.theme=dict(self.default_theme)
        mode="Darkmode"
        try:
            d=self.load("theme",{})
            for k in self.default_theme:
                if isinstance(d.get("farben",{}).get(k),str):
                    self.theme[k]=d["farben"][k]
            mode=d.get("modus","Darkmode")
        except Exception: pass
        self.theme_mode=mode

    def save_theme(self):
        self.save("theme",{"modus":self.theme_mode,"farben":self.theme})

    def col(self,key):
        h=self.theme.get(key,self.default_theme.get(key,"#ffffff")).lstrip("#")
        try:
            if len(h)==6:
                return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))+(1,)
        except Exception: pass
        return (1,1,1,1)

    def clear(self):
        c=self.root.get_screen("root").ids.content
        c.clear_widgets()
        return c

    def label(self,text,size=14,bold=False,height=None,color=None):
        w=Label(text=text,font_size=f"{size}sp",bold=bold,
                color=color or self.col("text"),halign="left",valign="middle")
        if height is not None: w.size_hint_y=None; w.height=dp(height)
        w.bind(size=lambda x,v:setattr(x,"text_size",(x.width,None)))
        return w

    def btn(self,text,fn=None,height=48,active=False):
        b=Button(text=text,size_hint_y=None,height=dp(height),
                 background_normal="",background_color=self.col("aktiv" if active else "button"),
                 color=self.col("text"),font_size="14sp")
        if fn: b.bind(on_release=lambda *_: fn())
        return b

    def input(self,hint="",text="",height=48,multi=False):
        w=TextInput(text=text,hint_text=hint,multiline=multi,size_hint_y=None,
                    height=dp(height),background_color=self.col("eingabe"),
                    foreground_color=self.col("text"),hint_text_color=self.col("text_sekundaer"),
                    padding=[dp(10),dp(10)])
        return w

    def card(self,title,value,sub,fn=None):
        b=Button(text=f"{title}\n{value}\n{sub}",size_hint_y=None,height=dp(110),
                 background_normal="",background_color=self.col("karte"),
                 color=self.col("text"),font_size="14sp",halign="left",valign="middle")
        b.bind(size=lambda x,v:setattr(x,"text_size",(x.width-dp(20),None)))
        if fn:b.bind(on_release=lambda *_:fn())
        return b

    def show_page(self,name):
        self.current_page=name
        self.rebuild_nav()
        pages={"Start":self.page_start,"Aufgaben":self.page_tasks,"Kalender":self.page_calendar,
               "Notizen":self.page_notes,"Suche":self.page_search,"Einstellungen":self.page_settings,
               "Theme":self.page_theme}
        pages.get(name,self.page_start)()

    def rebuild_nav(self):
        nav=self.root.get_screen("root").ids.nav
        nav.clear_widgets()
        items=[("⌕  Suche","Suche"),("🏠  Start","Start"),("✓  Aufgaben","Aufgaben"),
               ("📅  Kalender","Kalender"),("📝  Notizen","Notizen"),
               ("⚙  Einstellungen","Einstellungen"),("🎨  Theme","Theme")]
        for txt,name in items:
            nav.add_widget(self.btn(txt,lambda n=name:self.show_page(n),52,name==self.current_page))
        nav.add_widget(Label(size_hint_y=None,height=dp(10)))
        nav.add_widget(self.label("Mein Organizer",11,False,28,self.col("text_dezent")))

    # ---------- Start ----------
    def page_start(self):
        c=self.clear()
        now=datetime.now()
        c.add_widget(self.label("Guten Tag! 👋",28,True,45))
        german={"Monday":"Montag","Tuesday":"Dienstag","Wednesday":"Mittwoch","Thursday":"Donnerstag","Friday":"Freitag","Saturday":"Samstag","Sunday":"Sonntag"}
        months={"January":"Januar","February":"Februar","March":"März","April":"April","May":"Mai","June":"Juni","July":"Juli","August":"August","September":"September","October":"Oktober","November":"November","December":"Dezember"}
        date=now.strftime("%A, %d. %B %Y")
        for a,b in {**german,**months}.items(): date=date.replace(a,b)
        c.add_widget(self.label(date,14,False,30,self.col("text_sekundaer")))
        open_tasks=sum(not t.get("erledigt",False) for t in self.tasks)
        done=sum(t.get("erledigt",False) for t in self.tasks)
        today=now.strftime("%d.%m.%Y")
        today_events=sum(e.get("datum")==today for e in self.events)
        grid=GridLayout(cols=1 if Window.width<700 else 3,spacing=dp(8),size_hint_y=None,height=dp(330 if Window.width<700 else 115))
        grid.add_widget(self.card("📋 OFFENE AUFGABEN",str(open_tasks),"Aufgaben zu erledigen",lambda:self.show_page("Aufgaben")))
        grid.add_widget(self.card("✓ ERLEDIGT",str(done),"Aufgaben abgeschlossen",lambda:self.show_page("Aufgaben")))
        grid.add_widget(self.card("📅 HEUTE",str(today_events),"Kalendertermine",lambda:self.show_page("Kalender")))
        c.add_widget(grid)
        row=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(170))
        future=[]
        for i,e in enumerate(self.events):
            try:
                dt=datetime.strptime(f"{e.get('datum','')} {e.get('uhrzeit','00:00')}","%d.%m.%Y %H:%M")
                if dt>=now: future.append((dt,i,e))
            except: pass
        future.sort()
        if future:
            dt,i,e=future[0]
            tag="HEUTE" if dt.date()==now.date() else ("MORGEN" if dt.date()==(now+timedelta(days=1)).date() else dt.strftime("%d.%m.%Y"))
            text=f"{tag}\n{e.get('titel','')}  ·  {e.get('uhrzeit','')}"
            if e.get("ort"): text+=f"\n📍 {e['ort']}"
        else: text="Keine kommenden Termine 🎉"
        row.add_widget(self.label("📅  NÄCHSTER TERMIN",15,True,34))
        row.add_widget(self.label(text,15,False,80,self.col("text_sekundaer")))
        c.add_widget(row)
        c.add_widget(self.label("📋  NÄCHSTE AUFGABEN",15,True,34))
        upcoming=[]
        for i,t in enumerate(self.tasks):
            if t.get("erledigt"): continue
            due=self.task_dt(t)
            upcoming.append((due or datetime.max,i,t))
        upcoming.sort(key=lambda x:x[0])
        for due,i,t in upcoming[:5]:
            status="🔴 Überfällig" if due and due<now else (due.strftime("%d.%m.%Y %H:%M") if due else "Keine Fälligkeit")
            c.add_widget(self.btn(f"{t.get('text',t.get('titel',''))}\n{status}",lambda idx=i:self.edit_task(idx),64))

    # ---------- Tasks ----------
    def task_dt(self,t):
        try:return datetime.strptime(t.get("faelligkeit","").strip(),"%d.%m.%Y %H:%M") if t.get("faelligkeit") else None
        except:return None

    def page_tasks(self):
        c=self.clear()
        c.add_widget(self.label("✓ Aufgaben",26,True,46))
        top=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(6))
        inp=self.input("Neue Aufgabe …")
        top.add_widget(inp)
        due=self.input("TT.MM.JJJJ HH:MM",height=48)
        top.add_widget(due)
        top.add_widget(self.btn("＋",lambda:self.add_task(inp.text,due.text),48))
        c.add_widget(top)
        c.add_widget(self.btn("📁 Aufgabenordner verwalten",self.folder_popup,46))
        filt=Spinner(text="Alle",values=["Alle"]+self.folders,size_hint_y=None,height=dp(44),
                     background_normal="",background_color=self.col("karte"),color=self.col("text"))
        c.add_widget(filt)
        scroll=ScrollView(do_scroll_x=False)
        box=BoxLayout(orientation="vertical",size_hint_y=None,spacing=dp(6))
        box.bind(minimum_height=box.setter("height"))
        selected=filt
        def refresh(*_):
            box.clear_widgets()
            for i,t in enumerate(self.tasks):
                if selected.text!="Alle" and t.get("ordner","")==selected.text: continue
                due_dt=self.task_dt(t); over=due_dt and datetime.now()>due_dt and not t.get("erledigt")
                title=("✓ " if t.get("erledigt") else "")+t.get("text",t.get("titel",""))
                if due_dt: title+=f"\n{'🔴 Überfällig' if over else '📅'} {due_dt.strftime('%d.%m.%Y %H:%M')}"
                title+=f"\n📁 {t.get('ordner','Keine') or 'Keine'}"
                b=self.btn(title,lambda idx=i:self.edit_task(idx),70)
                box.add_widget(b)
        selected.bind(text=refresh); scroll.add_widget(box); c.add_widget(scroll); refresh()

    def add_task(self,text,due=""):
        text=text.strip()
        if not text:return
        t={"text":text,"erledigt":False,"faelligkeit":due.strip(),"ordner":""}
        self.tasks.append(t); self.save("tasks",self.tasks); self.show_page("Aufgaben")

    def edit_task(self,i):
        t=self.tasks[i]
        p=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
        txt=self.input("Aufgabe",t.get("text",""),50); p.add_widget(txt)
        due=self.input("Fälligkeit TT.MM.JJJJ HH:MM",t.get("faelligkeit",""),50); p.add_widget(due)
        sp=Spinner(text=t.get("ordner") or "Kein Ordner",values=["Kein Ordner"]+self.folders,size_hint_y=None,height=dp(46));p.add_widget(sp)
        buttons=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(6))
        popup=Popup(title="Aufgabe bearbeiten",content=p,size_hint=(.94,.55))
        def saveit():
            t["text"]=txt.text.strip();t["faelligkeit"]=due.text.strip();t["ordner"]="" if sp.text=="Kein Ordner" else sp.text
            self.save("tasks",self.tasks);popup.dismiss();self.show_page("Aufgaben")
        buttons.add_widget(self.btn("Speichern",saveit));buttons.add_widget(self.btn("✓ Erledigt",lambda:(t.update(erledigt=not t.get("erledigt",False)),self.save("tasks",self.tasks),popup.dismiss(),self.show_page("Aufgaben"))));buttons.add_widget(self.btn("🗑 Löschen",lambda:(self.tasks.pop(i),self.save("tasks",self.tasks),popup.dismiss(),self.show_page("Aufgaben"))))
        p.add_widget(buttons);popup.open()

    def folder_popup(self):
        p=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
        inp=self.input("Neuer Aufgabenordner …");p.add_widget(inp)
        box=BoxLayout(orientation="vertical",size_hint_y=None);box.bind(minimum_height=box.setter("height"))
        for f in self.folders:
            row=BoxLayout(size_hint_y=None,height=dp(44))
            row.add_widget(self.label("📁 "+f,13,False,44))
            row.add_widget(self.btn("🗑",lambda ff=f:self.delete_folder(ff),44))
            box.add_widget(row)
        s=ScrollView(do_scroll_x=False);s.add_widget(box);p.add_widget(s);p.add_widget(self.btn("＋ Hinzufügen",lambda:(self.folders.append(inp.text.strip()),self.save("folders",self.folders),self.folder_popup_close()))); 
        self.folder_popup_ref=Popup(title="Aufgabenordner",content=p,size_hint=(.92,.75));self.folder_popup_ref.open()
    def folder_popup_close(self):
        self.folder_popup_ref.dismiss();self.folder_popup()
    def delete_folder(self,f):
        if f in self.folders:self.folders.remove(f)
        for t in self.tasks:
            if t.get("ordner")==f:t["ordner"]=""
        self.save("folders",self.folders);self.save("tasks",self.tasks);self.folder_popup_close()

    # ---------- Calendar ----------
    def page_calendar(self):
        c=self.clear(); now=datetime.now()
        c.add_widget(self.label("📅 Kalender",26,True,46))
        # Month navigation
        if not hasattr(self,"cal_month"): self.cal_month=now.month;self.cal_year=now.year
        head=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(6))
        head.add_widget(self.btn("‹",lambda:self.shift_month(-1)))
        head.add_widget(self.label(f"{pycalendar.month_name[self.cal_month]} {self.cal_year}",17,True,48))
        head.add_widget(self.btn("›",lambda:self.shift_month(1)))
        head.add_widget(self.btn("＋ Termin",lambda:self.event_popup(),48))
        c.add_widget(head)
        weeks=pycalendar.monthcalendar(self.cal_year,self.cal_month)
        grid=GridLayout(cols=7,spacing=dp(3),size_hint_y=None,height=dp(len(weeks)*52+30))
        for wd in ["Mo","Di","Mi","Do","Fr","Sa","So"]:grid.add_widget(self.label(wd,11,True,28,self.col("text_sekundaer")))
        for week in weeks:
            for day in week:
                if not day: grid.add_widget(Label(size_hint_y=None,height=dp(50)));continue
                date=f"{day:02d}.{self.cal_month:02d}.{self.cal_year:04d}"
                count=sum(e.get("datum")==date for e in self.events)
                grid.add_widget(self.btn(f"{day}\n{count} Termin(e)" if count else str(day),lambda d=date:self.day_popup(d),50))
        c.add_widget(grid)
        c.add_widget(self.label("Termine dieses Monats",14,True,35))
        for i,e in sorted(enumerate(self.events),key=lambda x:(x[1].get("datum",""),x[1].get("uhrzeit",""))):
            try:
                dt=datetime.strptime(e.get("datum",""),"%d.%m.%Y")
                if dt.month==self.cal_month and dt.year==self.cal_year:
                    c.add_widget(self.btn(f"{e.get('datum')} {e.get('uhrzeit','')} · {e.get('titel','')}",lambda idx=i:self.event_edit(idx),58))
            except: pass

    def shift_month(self,d):
        self.cal_month+=d
        if self.cal_month<1:self.cal_month=12;self.cal_year-=1
        if self.cal_month>12:self.cal_month=1;self.cal_year+=1
        self.show_page("Kalender")
    def day_popup(self,date):
        p=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(6))
        p.add_widget(self.label(date,17,True,40))
        for i,e in enumerate(self.events):
            if e.get("datum")==date:p.add_widget(self.btn(f"{e.get('uhrzeit','')} · {e.get('titel','')}",lambda idx=i:self.event_edit(idx),48))
        p.add_widget(self.btn("＋ Neuer Termin",lambda:self.event_popup(date)))
        pop=Popup(title="Tag",content=p,size_hint=(.9,.7));pop.open()

    def event_popup(self,date=None):
        p=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(7))
        title=self.input("Titel");datum=self.input("TT.MM.JJJJ",date or datetime.now().strftime("%d.%m.%Y"));time=self.input("HH:MM","12:00");ort=self.input("Ort (optional)")
        for x in [title,datum,time,ort]:p.add_widget(x)
        color=self.input("Farbe HEX (optional)",self.theme["aktiv"]);p.add_widget(color)
        p.add_widget(self.btn("Speichern",lambda:self.save_event(title,datum,time,ort,color,None,popup=None),50))
        pop=Popup(title="Neuer Termin",content=p,size_hint=(.9,.78));p.children[0].bind(on_release=lambda *_:None)
        # Replace save button callback cleanly
        p.remove_widget(p.children[0])
        p.add_widget(self.btn("Speichern",lambda:self.save_event(title,datum,time,ort,color,pop),50))
        pop.open()
    def save_event(self,title,datum,time,ort,color,pop,popup=None):
        if not title.text.strip():return
        try:datetime.strptime(f"{datum.text.strip()} {time.text.strip()}","%d.%m.%Y %H:%M")
        except:return
        self.events.append({"titel":title.text.strip(),"datum":datum.text.strip(),"uhrzeit":time.text.strip(),"ort":ort.text.strip(),"farbe":color.text.strip() or self.theme["aktiv"]})
        self.save("events",self.events)
        if pop:pop.dismiss()
        self.show_page("Kalender")
    def event_edit(self,i):
        e=self.events[i];p=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(7))
        fields=[self.input("Titel",e.get("titel","")),self.input("Datum",e.get("datum","")),self.input("Uhrzeit",e.get("uhrzeit","")),self.input("Ort",e.get("ort","")),self.input("Farbe",e.get("farbe",self.theme["aktiv"]))]
        for x in fields:p.add_widget(x)
        pop=Popup(title="Termin bearbeiten",content=p,size_hint=(.92,.78))
        actions=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        actions.add_widget(self.btn("Speichern",lambda:self.update_event(i,fields,pop)))
        actions.add_widget(self.btn("🗑 Löschen",lambda:(self.events.pop(i),self.save("events",self.events),pop.dismiss(),self.show_page("Kalender"))))
        p.add_widget(actions);pop.open()
    def update_event(self,i,f,pop):
        e=self.events[i];e.update(titel=f[0].text.strip(),datum=f[1].text.strip(),uhrzeit=f[2].text.strip(),ort=f[3].text.strip(),farbe=f[4].text.strip() or self.theme["aktiv"])
        self.save("events",self.events);pop.dismiss();self.show_page("Kalender")

    # ---------- Notes ----------
    def page_notes(self):
        c=self.clear();c.add_widget(self.label("📝 Notizen",26,True,46))
        bar=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(6))
        bar.add_widget(self.btn("＋ Neue Notiz",lambda:self.note_popup(),48))
        bar.add_widget(self.btn("🏷 Kategorien",self.categories_popup,48))
        c.add_widget(bar)
        search=self.input("Notizen durchsuchen …");c.add_widget(search)
        scroll=ScrollView(do_scroll_x=False);box=BoxLayout(orientation="vertical",size_hint_y=None,spacing=dp(7));box.bind(minimum_height=box.setter("height"))
        def refresh(*_):
            box.clear_widgets();q=search.text.lower()
            items=[(i,n) for i,n in enumerate(self.notes) if q in (n.get("titel","")+" "+n.get("inhalt","")).lower()]
            items.sort(key=lambda x:(not x[1].get("angepinnt",False),x[1].get("titel","").lower()))
            for i,n in items:
                preview=n.get("inhalt","").replace("\n"," ")[:90]
                at=len(n.get("anhaenge",[]))
                box.add_widget(self.btn(("📌 " if n.get("angepinnt") else "")+n.get("titel","(Ohne Titel)")+"\n"+preview+(f"\n📎 {at} Anhang/Anhänge" if at else ""),lambda idx=i:self.note_popup(idx),82))
        search.bind(text=refresh);scroll.add_widget(box);c.add_widget(scroll);refresh()

    def note_popup(self,index=None):
        n=self.notes[index] if index is not None else {"titel":"","inhalt":"","kategorie":"","farbe":self.theme["karte"],"angepinnt":False,"anhaenge":[]}
        p=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(7))
        title=self.input("Titel",n.get("titel",""));p.add_widget(title)
        cat=Spinner(text=n.get("kategorie") or "Keine Kategorie",values=["Keine Kategorie"]+self.categories,size_hint_y=None,height=dp(44));p.add_widget(cat)
        pin=CheckBox(active=bool(n.get("angepinnt")));row=BoxLayout(size_hint_y=None,height=dp(40));row.add_widget(self.label("📌 Anpinnen",12,False,40));row.add_widget(pin);p.add_widget(row)
        body=self.input("Notiztext …",n.get("inhalt",""),180,True);p.add_widget(body)
        att_label=self.label("Anhänge: "+str(len(n.get("anhaenge",[]))),12,False,32);p.add_widget(att_label)
        actions=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(5))
        actions.add_widget(self.btn("📎 Datei/Bild",lambda:self.pick_attachment(n,att_label)))
        actions.add_widget(self.btn("Speichern",lambda:self.save_note(index,title,cat,pin,body,n,popup),48))
        if index is not None:actions.add_widget(self.btn("🗑",lambda:self.delete_note(index,popup),48))
        p.add_widget(actions)
        popup=Popup(title="Notiz bearbeiten" if index is not None else "Neue Notiz",content=p,size_hint=(.94,.88))
        # callback closures above need popup; rebuild binding for save after popup exists
        actions.children[-2].unbind(on_release=None) if False else None
        popup.open()
        # Add an additional reliable save button at bottom
        p.add_widget(self.btn("✓ Notiz speichern",lambda:self.save_note(index,title,cat,pin,body,n,popup),50))

    def save_note(self,index,title,cat,pin,body,n,popup):
        n.update(titel=title.text.strip() or "Ohne Titel",inhalt=body.text,kategorie="" if cat.text=="Keine Kategorie" else cat.text,angepinnt=pin.active)
        if index is None:self.notes.append(n)
        else:self.notes[index]=n
        self.save("notes",self.notes);popup.dismiss();self.show_page("Notizen")
    def delete_note(self,i,popup):
        self.notes.pop(i);self.save("notes",self.notes);popup.dismiss();self.show_page("Notizen")

    def categories_popup(self):
        p=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(7));inp=self.input("Neue Kategorie …");p.add_widget(inp)
        box=BoxLayout(orientation="vertical",size_hint_y=None);box.bind(minimum_height=box.setter("height"))
        for cat in self.categories:
            row=BoxLayout(size_hint_y=None,height=dp(44));row.add_widget(self.label("🏷️ "+cat,12,False,44));row.add_widget(self.btn("🗑",lambda cc=cat:self.delete_category(cc),44));box.add_widget(row)
        s=ScrollView(do_scroll_x=False);s.add_widget(box);p.add_widget(s)
        self.cat_popup=Popup(title="Notiz-Kategorien",content=p,size_hint=(.92,.72));p.add_widget(self.btn("＋ Kategorie hinzufügen",lambda:self.add_category(inp.text.strip()),48));self.cat_popup.open()
    def add_category(self,x):
        if x and x not in self.categories:self.categories.append(x);self.save("categories",self.categories)
        self.cat_popup.dismiss();self.categories_popup()
    def delete_category(self,x):
        if x in self.categories:self.categories.remove(x)
        for n in self.notes:
            if n.get("kategorie")==x:n["kategorie"]=""
        self.save("categories",self.categories);self.save("notes",self.notes);self.cat_popup.dismiss();self.categories_popup()

    def pick_attachment(self,n,label):
        # Android Storage Access Framework; desktop fallback opens a normal file chooser if available.
        try:
            from jnius import autoclass, cast
            from android import activity
            Intent=autoclass("android.content.Intent")
            intent=Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE);intent.setType("*/*")
            current=(n,label)
            self._pending_attachment=current
            def cb(requestCode,resultCode,data):
                if resultCode!= -1 or data is None:return
                uri=data.getData()
                resolver=activity.getApplication().getContentResolver()
                name="anhang_"+datetime.now().strftime("%Y%m%d_%H%M%S")
                dest=self.attach_dir/name
                stream=resolver.openInputStream(uri)
                out=open(dest,"wb")
                buf=bytearray(8192)
                while True:
                    ln=stream.read(buf)
                    if ln==-1:break
                    out.write(buf[:ln])
                out.close();stream.close()
                n.setdefault("anhaenge",[]).append(str(dest))
                label.text="Anhänge: "+str(len(n["anhaenge"]))
            activity.bind(on_activity_result=cb)
            activity.startActivityForResult(intent,9001)
        except Exception:
            # If SAF is unavailable, leave the feature usable on desktop via FileChooser.
            try:
                from kivy.uix.filechooser import FileChooserListView
                fc=FileChooserListView(filters=["*.*"],multiselect=False)
                pop=Popup(title="Datei auswählen",content=fc,size_hint=(.95,.85))
                fc.bind(selection=lambda *_:None)
                def chosen(*_):
                    if fc.selection:
                        src=fc.selection[0];dest=self.attach_dir/os.path.basename(src);shutil.copy2(src,dest)
                        n.setdefault("anhaenge",[]).append(str(dest));label.text="Anhänge: "+str(len(n["anhaenge"]));pop.dismiss()
                pop.bind(on_open=lambda *_: fc.bind(on_submit=lambda *_:chosen()))
                pop.open()
            except Exception: pass

    # ---------- Search ----------
    def page_search(self):
        c=self.clear();c.add_widget(self.label("⌕ Suche",26,True,46))
        inp=self.input("Aufgaben, Termine und Notizen durchsuchen …");c.add_widget(inp)
        scroll=ScrollView(do_scroll_x=False);box=BoxLayout(orientation="vertical",size_hint_y=None,spacing=dp(6));box.bind(minimum_height=box.setter("height"));scroll.add_widget(box);c.add_widget(scroll)
        def refresh(*_):
            box.clear_widgets();q=inp.text.lower().strip()
            if not q:return
            for i,t in enumerate(self.tasks):
                if q in str(t).lower():box.add_widget(self.btn("✓ Aufgabe: "+t.get("text",""),lambda:self.show_page("Aufgaben"),55))
            for i,e in enumerate(self.events):
                if q in str(e).lower():box.add_widget(self.btn("📅 Termin: "+e.get("titel",""),lambda:self.show_page("Kalender"),55))
            for i,n in enumerate(self.notes):
                if q in str(n).lower():box.add_widget(self.btn("📝 Notiz: "+n.get("titel",""),lambda idx=i:self.note_popup(idx),55))
        inp.bind(text=refresh)

    # ---------- Settings ----------
    def page_settings(self):
        c=self.clear();c.add_widget(self.label("⚙ Einstellungen",26,True,46))
        c.add_widget(self.label("Allgemeine Einstellungen",15,True,36))
        c.add_widget(self.label("Das Erscheinungsbild wird separat unter „🎨 Theme“ angepasst.",12,False,50,self.col("text_sekundaer")))
        c.add_widget(self.btn("🎨 Zum Theme",lambda:self.show_page("Theme"),50))
        c.add_widget(self.btn("🌙 Standard-Darkmode",self.reset_theme,50))

    # ---------- Theme ----------
    def page_theme(self):
        c=self.clear();c.add_widget(self.label("🎨 Theme",26,True,46))
        c.add_widget(self.label("Passe die Farben der App an. Änderungen werden sofort übernommen.",12,False,42,self.col("text_sekundaer")))
        names={"navigation":"Menüleiste – Hintergrund","button":"Menüleiste – Buttons","aktiv":"Highlight / aktive Auswahl","hover":"Hover-Farbe","inhalt":"Hauptbereich – Hintergrund","karte":"Karten / Bereiche","karte_innen":"Karten – innere Bereiche","eingabe":"Eingabefelder","dialog":"Dialoge / Zusatzbereiche","button_hover":"Buttons – Hover","text":"Haupttext","text_sekundaer":"Sekundärtext","text_dezent":"Dezenter Text"}
        for k,n in names.items():
            row=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(6))
            row.add_widget(self.label(n,11,False,52))
            row.add_widget(self.btn(self.theme[k],lambda key=k:self.color_popup(key),50))
            c.add_widget(row)
        c.add_widget(self.btn("🌙 Zum Standard-Darkmode zurücksetzen",self.reset_theme,52))

    def color_popup(self,key):
        p=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(6))
        cp=ColorPicker(color=self.col(key));p.add_widget(cp)
        pop=Popup(title="Farbe auswählen",content=p,size_hint=(.94,.82))
        def done(*_):
            r,g,b,a=cp.color;self.theme[key]="#%02x%02x%02x"%(int(r*255),int(g*255),int(b*255));self.theme_mode="Eigenes Theme";self.save_theme();pop.dismiss();self.show_page("Theme")
        p.add_widget(self.btn("Übernehmen",done,50));pop.open()

    def reset_theme(self):
        self.theme=dict(self.default_theme);self.theme_mode="Darkmode";self.save_theme();self.show_page(self.current_page)

if __name__=="__main__":
    MeinOrganizerAndroid().run()
