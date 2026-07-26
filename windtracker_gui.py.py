
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import requests
from datetime import datetime
import threading

class RuzgarApp:
    def __init__(self):
        self.pencere = tk.Tk()
        self.pencere.title("Rüzgar Veri Takip")
        self.pencere.geometry("700x500")
        
        self.baglanti = sqlite3.connect('ruzgar.db')
        self.cursor = self.baglanti.cursor()
        self.tabloOlustur()
        
        self.arayuzOlustur()
        self.enIyiGoster()
    
    def tabloOlustur(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ruzgar_veri (
                            id INTEGER PRIMARY KEY,
                            sehir TEXT,
                            hiz REAL,
                            yon TEXT,
                            tarih TEXT,
                            kayit TEXT)''')
        self.baglanti.commit()
    
    def arayuzOlustur(self):
        ustFrame = tk.Frame(self.pencere)
        ustFrame.pack(pady=10)
        
        tk.Label(ustFrame, text="Şehir:").pack(side=tk.LEFT)
        self.sehirGiris = tk.Entry(ustFrame, width=15)
        self.sehirGiris.pack(side=tk.LEFT, padx=5)
        self.sehirGiris.insert(0, "Ankara")
        
        self.buton = tk.Button(ustFrame, text="Veri Al", command=self.veriAl)
        self.buton.pack(side=tk.LEFT, padx=10)
        
        tk.Label(self.pencere, text="Güncel Durum:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=10)
        self.guncelText = tk.Text(self.pencere, height=5, width=80)
        self.guncelText.pack(padx=10, pady=5)
        
        tk.Label(self.pencere, text="En Yüksek Rüzgar:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=10)
        self.eniyiText = tk.Text(self.pencere, height=3, width=80)
        self.eniyiText.pack(padx=10, pady=5)
        
        tk.Label(self.pencere, text="Geçmiş Kayıtlar:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=10)
        
        listeFrame = tk.Frame(self.pencere)
        listeFrame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.liste = ttk.Treeview(listeFrame, columns=('sehir', 'hiz', 'yon', 'tarih'), show='headings', height=8)
        self.liste.heading('sehir', text='Şehir')
        self.liste.heading('hiz', text='Hız')
        self.liste.heading('yon', text='Yön')  
        self.liste.heading('tarih', text='Kayıt Zamanı')
        
        scrollbar = ttk.Scrollbar(listeFrame, orient="vertical", command=self.liste.yview)
        self.liste.configure(yscrollcommand=scrollbar.set)
        self.liste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        altFrame = tk.Frame(self.pencere)
        altFrame.pack(pady=10)
        tk.Button(altFrame, text="Listeyi Yenile", command=self.listeYenile).pack(side=tk.LEFT, padx=5)
        
        self.listeYenile()
    
    def veriAl(self):
        t = threading.Thread(target=self.apiCagir)
        t.daemon = True
        t.start()
    
    def apiCagir(self):
        sehir = self.sehirGiris.get()
        if not sehir:
            self.pencere.after(0, lambda: messagebox.showwarning("Uyarı", "Şehir giriniz"))
            return
            
        try:
            api_key = "YOUR_API_KEY_HERE"
            url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={sehir}"
            
            response = requests.get(url, timeout=8)
            if response.status_code != 200:
                self.pencere.after(0, lambda: messagebox.showerror("Hata", "API'den veri alınamadı"))
                return
                
            veri = response.json()
            
            sehir_adi = veri['location']['name'] + " , " + veri['location']['country']
            ruzgar_hiz = veri['current']['wind_kph']
            ruzgar_yon = veri['current']['wind_dir']
            api_zaman = veri['current']['last_updated']
            
            kayit_zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.pencere.after(0, lambda: self.veriKaydet(sehir_adi, ruzgar_hiz, ruzgar_yon, api_zaman, kayit_zaman))
            
        except Exception as hata:
            self.pencere.after(0, lambda: messagebox.showerror("Hata", f"Sorun: {str(hata)}"))
    
    def veriKaydet(self, sehir, hiz, yon, api_zaman, kayit_zaman):
        bilgi = f"{sehir} - Rüzgar Bilgisi\n"
        bilgi += f"Hız: {hiz} km/s\n"
        bilgi += f"Yön: {yon}\n" 
        bilgi += f"API Zamanı: {api_zaman}\n"
        bilgi += f"Kayıt: {kayit_zaman}"
        
        self.guncelText.delete(1.0, tk.END)
        self.guncelText.insert(1.0, bilgi)
        
        try:
            self.cursor.execute("INSERT INTO ruzgar_veri (sehir, hiz, yon, tarih, kayit) VALUES (?, ?, ?, ?, ?)",
                              (sehir, hiz, yon, api_zaman, kayit_zaman))
            self.baglanti.commit()
            
            self.enIyiGoster()
            self.listeYenile()
            messagebox.showinfo("Tamam", "Veri kaydedildi!")
            
        except Exception as e:
            messagebox.showerror("DB Hatası", f"Kayıt sorunu: {e}")
    
    def enIyiGoster(self):
        self.cursor.execute("SELECT sehir, hiz, yon, kayit FROM ruzgar_veri ORDER BY hiz DESC LIMIT 1")
        sonuc = self.cursor.fetchone()
        
        if sonuc:
            bilgi = f"En Yüksek: {sonuc[1]} km/s - {sonuc[0]}\nYön: {sonuc[2]} | Tarih: {sonuc[3]}"
        else:
            bilgi = "Henüz kayıt yok"
            
        self.eniyiText.delete(1.0, tk.END)
        self.eniyiText.insert(1.0, bilgi)
    
    def listeYenile(self):
        for item in self.liste.get_children():
            self.liste.delete(item)
        
        self.cursor.execute("SELECT sehir, hiz, yon, kayit FROM ruzgar_veri ORDER BY kayit DESC LIMIT 20")
        kayitlar = self.cursor.fetchall()
        
        for kayit in kayitlar:
            sehir, hiz, yon, tarih = kayit
            self.liste.insert('', tk.END, values=(sehir, hiz, yon, tarih))
    
    def calistir(self):
        self.pencere.mainloop()
        self.baglanti.close()

if __name__ == "__main__":
    app = RuzgarApp()
    app.calistir()