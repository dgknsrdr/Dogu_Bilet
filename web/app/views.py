from datetime import timedelta, datetime
from flask import Flask, render_template, request, redirect, url_for, make_response, session, jsonify
import sqlite3
from itsdangerous import Signer, BadSignature
import os
from dotenv import load_dotenv
import random
import pandas as pd
import requests   # OpenRouteService API için
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import google.generativeai as genai

load_dotenv()
app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ORS_API_KEY = os.getenv("ORS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")



gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Kullanılan model
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        print("Gemini model oluşturulamadı:", e)
        gemini_model = None

# 81 il koordinatları (lon, lat)
SEHIR_KOORD = {
    "Adana":        (35.3213, 37.0000),
    "Adıyaman":     (38.2786, 37.7648),
    "Afyonkarahisar": (30.5567, 38.7507),
    "Ağrı":         (43.0503, 39.7191),
    "Amasya":       (35.8353, 40.6499),
    "Ankara":       (32.8541, 39.9208),
    "Antalya":      (30.7056, 36.8841),
    "Artvin":       (41.8183, 41.1828),
    "Aydın":        (27.8416, 37.8560),
    "Balıkesir":    (27.8826, 39.6484),
    "Bilecik":      (30.0665, 40.0567),
    "Bingöl":       (40.7696, 39.0626),
    "Bitlis":       (42.1232, 38.3938),
    "Bolu":         (31.5788, 40.5760),
    "Burdur":       (30.0665, 37.4613),
    "Bursa":        (29.0634, 40.2669),
    "Çanakkale":    (26.4142, 40.1553),
    "Çankırı":      (33.6134, 40.6013),
    "Çorum":        (34.9556, 40.5506),
    "Denizli":      (29.0864, 37.7765),
    "Diyarbakır":   (40.2306, 37.9144),
    "Edirne":       (26.5623, 41.6818),
    "Elazığ":       (39.2264, 38.6810),
    "Erzincan":     (39.5000, 39.7500),
    "Erzurum":      (41.2700, 39.9000),
    "Eskişehir":    (30.5206, 39.7767),
    "Gaziantep":    (37.3833, 37.0662),
    "Giresun":      (38.3895, 40.9128),
    "Gümüşhane":    (39.5086, 40.4386),
    "Hakkari":      (43.7333, 37.5833),
    "Hatay":        (36.3498, 36.4018),
    "Isparta":      (30.5566, 37.7648),
    "Mersin":       (34.6333, 36.8000),
    "İstanbul":     (28.9770, 41.0053),
    "İzmir":        (27.1287, 38.4189),
    "Kars":         (43.1000, 40.6167),
    "Kastamonu":    (33.7827, 41.3887),
    "Kayseri":      (35.4787, 38.7312),
    "Kırklareli":   (27.2167, 41.7333),
    "Kırşehir":     (34.1709, 39.1425),
    "Kocaeli":      (29.8815, 40.8533),
    "Konya":        (32.4833, 37.8667),
    "Kütahya":      (29.9833, 39.4167),
    "Malatya":      (38.3095, 38.3552),
    "Manisa":       (27.4289, 38.6191),
    "Kahramanmaraş": (36.9371, 37.5858),
    "Mardin":       (40.7245, 37.3212),
    "Muğla":        (28.3636, 37.2153),
    "Muş":          (41.7539, 38.9462),
    "Nevşehir":     (34.6857, 38.6939),
    "Niğde":        (34.6833, 37.9667),
    "Ordu":         (37.8764, 40.9839),
    "Rize":         (40.5234, 41.0201),
    "Sakarya":      (30.4358, 40.6940),
    "Samsun":       (36.3313, 41.2928),
    "Siirt":        (41.9500, 37.9333),
    "Sinop":        (35.1531, 42.0231),
    "Sivas":        (37.0179, 39.7477),
    "Tekirdağ":     (27.5167, 40.9833),
    "Tokat":        (36.5500, 40.3167),
    "Trabzon":      (39.7178, 41.0015),
    "Tunceli":      (39.4388, 39.3074),
    "Şanlıurfa":    (38.7969, 37.1674),
    "Uşak":         (29.4058, 38.6823),
    "Van":          (43.3832, 38.5012),
    "Yozgat":       (34.8086, 39.8181),
    "Zonguldak":    (31.7987, 41.4564),
    "Aksaray":      (34.0254, 38.3687),
    "Bayburt":      (40.2270, 40.2552),
    "Karaman":      (33.2150, 37.1810),
    "Kırıkkale":    (33.5167, 39.8468),
    "Batman":       (41.1322, 37.8812),
    "Şırnak":       (42.4610, 37.5164),
    "Bartın":       (32.3375, 41.5811),
    "Ardahan":      (42.7022, 41.1105),
    "Iğdır":        (44.0440, 39.9237),
    "Yalova":       (29.2769, 40.6500),
    "Karabük":      (32.6278, 41.2061),
    "Kilis":        (37.1150, 36.7161),
    "Osmaniye":     (36.2478, 37.0742),
    "Düzce":        (31.1639, 40.8438),
}

# --- Metinden şehir ve tarih ayıklama yardımcıları ---

TURKCE_AYLAR = {
    "ocak": 1,
    "şubat": 2, "subat": 2,
    "mart": 3,
    "nisan": 4,
    "mayıs": 5, "mayis": 5,
    "haziran": 6,
    "temmuz": 7,
    "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9,
    "ekim": 10,
    "kasım": 11, "kasim": 11,
    "aralık": 12, "aralik": 12,}



def admin_istatistik_grafik():

    conn = sqlite3.connect("dogubilet.db")
    cursor = conn.cursor()

    #  Aktif / İade edilen bilet
    cursor.execute("""
        SELECT Iade_Edildi, COUNT(*)
        FROM Biletler
        GROUP BY Iade_Edildi
    """)
    bilet_durum = cursor.fetchall()

    aktif = 0
    iade = 0
    for durum, adet in bilet_durum:
        if durum == 0:
            aktif = adet
        else:
            iade = adet

    #  Sefer başına satılan bilet
    cursor.execute("""
        SELECT Sefer_ID, COUNT(*)
        FROM Biletler
        GROUP BY Sefer_ID
    """)
    sefer_bilet = cursor.fetchall()

    seferler = [str(s[0]) for s in sefer_bilet]
    sefer_adet = [s[1] for s in sefer_bilet]

    # Bugün satılan bilet
    cursor.execute("""
        SELECT COUNT(*)
        FROM Biletler
        WHERE date(Satin_Alma_Tarihi) = date('now')
    """)
    bugun_bilet = cursor.fetchone()[0]

    #  Genel sayılar
    cursor.execute("SELECT COUNT(*) FROM Kullanici")
    toplam_kullanici = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Sefer")
    toplam_sefer = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Biletler")
    toplam_bilet = cursor.fetchone()[0]

    conn.close()

    #  GRAFİKLER
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    # Grafik 1: Aktif / İade
    if aktif + iade > 0:
        axs[0, 0].pie(
            [aktif, iade],
            labels=["Aktif", "İade"],
            autopct="%1.1f%%",
            startangle=90
        )
    else:
        axs[0, 0].text(
            0.5, 0.5,
            "Henüz bilet yok",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=12
        )

    axs[0, 0].set_title("Bilet Durumu")

    # Grafik 2: Sefer başına bilet
    axs[0, 1].bar(seferler, sefer_adet)
    axs[0, 1].set_title("Sefer Başına Satılan Bilet")
    axs[0, 1].set_xlabel("Sefer ID")
    axs[0, 1].set_ylabel("Bilet Sayısı")

    # Grafik 3: Bugün satılan bilet
    axs[1, 0].bar(["Bugün"], [bugun_bilet])
    axs[1, 0].set_title("Bugün Satılan Bilet")

    # Grafik 4: Genel istatistik
    axs[1, 1].bar(
        ["Kullanıcı", "Sefer", "Bilet"],
        [toplam_kullanici, toplam_sefer, toplam_bilet]
    )
    axs[1, 1].set_title("Genel Sistem Durumu")

    plt.tight_layout()

    #  base64
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    grafik_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    plt.close()

    return grafik_base64



def ayikla_tarih(metin: str):
    """
    Kullanıcı mesajından YYYY-MM-DD formatında tarih döndürür.
    Örnekler:
      - '8 aralıkta' -> '2025-12-08'
      - 'yarın'      -> bugün+1
      - 'bugün'      -> bugün
    Bulamazsa None döndürür.
    """
    text = metin.lower()
    bugun = datetime.now().date()

    # bugün / yarın
    if "bugün" in text or "bugun" in text:
        return bugun.strftime("%Y-%m-%d")
    if "yarın" in text or "yarin" in text:
        return (bugun + timedelta(days=1)).strftime("%Y-%m-%d")

    # '8 aralık', '08 aralik' vb.
    m = re.search(r"(\d{1,2})\s*(ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)", text)
    if m:
        gun = int(m.group(1))
        ay_adi = m.group(2)
        ay = TURKCE_AYLAR.get(ay_adi, None)
        if ay is None:
            return None
        yil = bugun.year
        try:
            t = datetime(yil, ay, gun).date()
            return t.strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def ayikla_sefer_sorgusu(metin: str):
    """
    Mesajdan (kalkış, varış, tarih_str) ayıklar.
    Örnek: 'ankaradan istanbula 8 aralıkta bilet var mı'
      -> ('Ankara', 'İstanbul', '2025-12-08')
    Bulamazsa None döner.
    """
    text = metin.lower()

    # 1) Şehirleri sırayla bul
    sehir_eslesmeleri = []
    for sehir in SEHIR_KOORD.keys():
        s_lower = sehir.lower()
        idx = text.find(s_lower)
        if idx != -1:
            sehir_eslesmeleri.append((idx, sehir))

    if len(sehir_eslesmeleri) < 2:
        return None  # En az iki şehir yok

    sehir_eslesmeleri.sort(key=lambda x: x[0])
    kalkis = sehir_eslesmeleri[0][1]
    varis = sehir_eslesmeleri[1][1]

    # 2) Tarihi bul
    tarih_str = ayikla_tarih(text)
    if not tarih_str:
        return None

    return kalkis, varis, tarih_str

# ------------Database bağlantısı--------------
def create_database():
    conn = sqlite3.connect('dogubilet.db')
    cursor = conn.cursor()
    return conn, cursor
# ----------------------------------------------


def sefer_tarihlerini_guncelle(cursor):
    bugun = datetime.now().date()
    yeni_tarih = bugun + timedelta(days=3)

    cursor.execute("SELECT Sefer_ID , Tarih FROM Sefer ORDER BY Sefer_ID")
    seferler = cursor.fetchall()

    for sefer_id, tarih_str in seferler:
        tarih = datetime.strptime(tarih_str, "%Y-%m-%d").date()
        if tarih < bugun:
            cursor.execute(
                "UPDATE Sefer SET Tarih = ? WHERE Sefer_ID = ?",
                (yeni_tarih.strftime("%Y-%m-%d"), sefer_id)
            )


# ------------ ORS API ile süre + fiyat hesaplama ------------
def hesapla_sure_ve_fiyat(kalkis, varis):
    if kalkis not in SEHIR_KOORD or varis not in SEHIR_KOORD:
        return 6.0, 400

    start = SEHIR_KOORD[kalkis]  # (lon, lat)
    end = SEHIR_KOORD[varis]

    if not ORS_API_KEY:
        return 6.0, 400

    try:
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json"
        }
        body = {
            "coordinates": [
                list(start),
                list(end)
            ]
        }
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "routes" not in data or not data["routes"]:
            return 6.0, 400

        route = data["routes"][0]
        summary = route.get("summary", {})

        duration_sec = summary.get("duration")
        distance_m = summary.get("distance")

        if duration_sec is None or distance_m is None:
            return 6.0, 400

        sure_saat = round(duration_sec / 3600, 1)
        mesafe_km = distance_m / 1000.0

        fiyat = mesafe_km * 0.9 + 80
        fiyat = max(200, min(900, int(fiyat)))

        return sure_saat, fiyat

    except Exception:
        return 6.0, 400

# ------------------------------------------------------------


# -----------------Sahte sefer verisi oluştur----------------
def sefer_olustur(cursor):
    iller = [
        "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir",
        "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
        "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane",
        "Hakkari", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli",
        "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş",
        "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat",
        "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman",
        "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce"
    ]
    firmalar = ["Metro", "Pamukkale", "Kamil Koç", "Buzlu"]
    sefer_id = 1001
    bugun = datetime.now()
    tarih_listesi = [(bugun + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]

    cursor.execute("SELECT * FROM Sefer WHERE Sefer_ID=?", (sefer_id,))
    a = cursor.fetchall()
    if a == []:
        for i in iller:
            for j in range(30):
                varis = random.choice([v for v in iller if v != i])
                firma = random.choice(firmalar)
                tarih = random.choice(tarih_listesi)
                saat = f"{random.randint(0, 23):02d}:{random.choice(['00', '15', '30', '45'])}"

                cursor.execute(
                    "INSERT INTO Sefer(Sefer_ID, Kalkis, Varis, Firma, Tarih, Saat, Sure, Fiyat) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (sefer_id, i, varis, firma, tarih, saat, 0.0, 0)
                )
                sefer_id += 1
# ---------------------------------------------------------------------


# -----------------Veritabanı tablolarını oluşturma--------------------
def create_table(cursor):
    cursor.execute("""CREATE TABLE IF NOT EXISTS Kullanici(
                ID INTEGER PRIMARY KEY,
                Ad TEXT NOT NULL,
                Soyad TEXT NOT NULL,
                Dogum_gunu TEXT NOT NULL,
                E_Posta TEXT NOT NULL,
                Sifre TEXT NOT NULL,
                Rol TEXT NOT NULL DEFAULT 'user'
                      )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Sefer(
                Sefer_ID INTEGER PRIMARY KEY NOT NULL,
                Kalkis TEXT NOT NULL,
                Varis TEXT NOT NULL,
                Firma TEXT NOT NULL,
                Tarih TEXT NOT NULL,
                Saat TEXT NOT NULL,
                Sure REAL,
                Fiyat INTEGER NOT NULL
                    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Koltuklar(
                ID INTEGER PRIMARY KEY NOT NULL,
                Sefer_ID INTEGER NOT NULL,
                Koltuk_no INTEGER NOT NULL,
                Koltuk_Durum TEXT NOT NULL CHECK (Koltuk_Durum IN('Boş','Dolu')),
                FOREIGN KEY (Sefer_ID) REFERENCES Sefer(Sefer_ID)
                )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Biletler(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Kullanici_ID INTEGER NOT NULL,
                Sefer_ID INTEGER NOT NULL,
                Koltuk_No INTEGER NOT NULL,
                Satin_Alma_Tarihi TEXT NOT NULL,
                Iade_Edildi INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (Kullanici_ID) REFERENCES Kullanici(ID),
                FOREIGN KEY (Sefer_ID) REFERENCES Sefer(Sefer_ID)
                )""")

    cursor.execute("SELECT COUNT(*) FROM Sefer")
    sefer_sayisi = cursor.fetchone()[0]
    if sefer_sayisi == 0:
        sefer_olustur(cursor)
        koltuk_olustur(cursor)
    else:
        sefer_tarihlerini_guncelle(cursor)
        koltuk_olustur(cursor)

    cursor.execute("PRAGMA table_info(Kullanici)")
    k_cols = [row[1] for row in cursor.fetchall()]
    if "Rol" not in k_cols:
        cursor.execute("ALTER TABLE Kullanici ADD COLUMN Rol TEXT NOT NULL DEFAULT 'user'")

    cursor.execute("PRAGMA table_info(Biletler)")
    b_cols = [row[1] for row in cursor.fetchall()]
    if "Iade_Edildi" not in b_cols:
        cursor.execute("ALTER TABLE Biletler ADD COLUMN Iade_Edildi INTEGER NOT NULL DEFAULT 0")
# ---------------------------------------------------------------------


def koltuk_olustur(cursor):
    cursor.execute("SELECT Sefer_ID FROM Sefer")
    seferler = cursor.fetchall()

    for (sefer_id,) in seferler:
        cursor.execute(
            "SELECT COUNT(*) FROM Koltuklar WHERE Sefer_ID = ?",
            (sefer_id,)
        )
        adet = cursor.fetchone()[0]

        if adet == 0:
            for num in range(1, 41):
                cursor.execute(
                    "INSERT INTO Koltuklar (Sefer_ID, Koltuk_no, Koltuk_Durum) VALUES (?,?,?)",
                    (sefer_id, num, "Boş")
                )

def admin_yap(cursor):
    cursor.execute("UPDATE Kullanici SET Rol='admin' WHERE E_Posta='dgknsrdr@gmail.com'")


# ----------------- SESSION AYARI -----------------
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(days=30)
gizli_sifre = Signer(SECRET_KEY)
# -------------------------------------------------


# ------------------ Giriş Sayfası -----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if session.get("user_id"):
        return redirect(url_for("kullanici_panel"))

    if request.method == "POST":
        mail = request.form["mail"]
        sifre = request.form["user_sifre"]

        conn, cursor = create_database()
        cursor.execute(
            "SELECT ID, Ad, Soyad, Dogum_gunu, E_Posta FROM Kullanici WHERE E_Posta=? AND Sifre=?",
            (mail, sifre)
        )
        kullanici_varmi = cursor.fetchone()

        if kullanici_varmi:
            user_id, ad, soyad, dogum_gunu, mail_db = kullanici_varmi

            session.permanent = True
            session["user_id"] = user_id
            session["ad"] = ad.capitalize()
            session["soyad"] = soyad.capitalize()
            session["mail"] = mail_db

            sifreli_ad = gizli_sifre.sign(ad).decode()
            sifreli_soyad = gizli_sifre.sign(soyad).decode()
            sifreli_mail = gizli_sifre.sign(mail_db).decode()

            response = make_response(redirect(url_for('kullanici_panel')))

            cookie_sure = 60 * 60 * 24 * 30  # 1 ay

            response.set_cookie("user_name", sifreli_ad, max_age=cookie_sure,
                                secure=False, httponly=True, samesite='Lax')
            response.set_cookie("user_surname", sifreli_soyad, max_age=cookie_sure,
                                secure=False, httponly=True, samesite='Lax')
            response.set_cookie("user_mail", sifreli_mail, max_age=cookie_sure,
                                secure=False, httponly=True, samesite='Lax')

            conn.close()
            return response

        else:
            conn.close()
            return render_template("home.html", mesaj="E-posta veya şifre hatalı")

    return render_template("home.html")
# --------------------------------------------------


# ---------------- Kullanıcı Paneli -----------------
@app.route("/kullanici_panel")
def kullanici_panel():
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]

    conn, cursor = create_database()
    cursor.execute(
        "SELECT E_Posta FROM Kullanici WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()

    if not user:
        session.clear()
        return redirect(url_for("home"))

    cursor.execute("""
        SELECT Ad, Soyad, Dogum_gunu, E_Posta, Rol
        FROM Kullanici
        WHERE ID = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return redirect(url_for("home"))

    ad, soyad, dogum_gunu, mail, rol = row

    return render_template(
        "kullanici_panel.html",
        user_ad=ad.capitalize(),
        user_soyad=soyad.capitalize(),
        user_mail=mail,
        user_dogum=dogum_gunu,
        user_role=rol
    )
# --------------------------------------------------


# ---------------- Bilet listesi (aktif / geçmiş) -----------------
@app.route("/biletlerim")
def biletlerim():
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]
    tip = request.args.get("tip", "aktif")  # aktif / gecmis

    conn, cursor = create_database()
    cursor.execute("""
        SELECT 
            B.ID AS Bilet_ID,
            S.Kalkis,
            S.Varis,
            S.Tarih,
            S.Saat,
            S.Firma,
            S.Fiyat,
            S.Sure,
            B.Koltuk_No,
            B.Iade_Edildi
        FROM Biletler AS B
        JOIN Sefer AS S ON B.Sefer_ID = S.Sefer_ID
        WHERE B.Kullanici_ID = ?
        ORDER BY S.Tarih DESC, S.Saat DESC
    """, (user_id,))
    satirlar = cursor.fetchall()
    conn.close()

    simdi = datetime.now()
    aktif_biletler = []
    gecmis_biletler = []

    for (bilet_id, kalkis, varis, tarih, saat, firma, fiyat,
         sure, koltuk_no, iade_edildi) in satirlar:

        sefer_dt = datetime.strptime(f"{tarih} {saat}", "%Y-%m-%d %H:%M")
        sure_saat = float(sure) if sure is not None else 0.0
        bitis_dt = sefer_dt + timedelta(hours=sure_saat)

        bilet_info = {
            "bilet_id": bilet_id,
            "kalkis": kalkis,
            "varis": varis,
            "tarih": tarih,
            "saat": saat,
            "firma": firma,
            "fiyat": fiyat,
            "sure": sure_saat,
            "koltuk_no": koltuk_no,
            "iade_edildi": bool(iade_edildi),
            "durum": ""
        }

        if iade_edildi:
            bilet_info["durum"] = "İade edildi"
            gecmis_biletler.append(bilet_info)
        else:
            if bitis_dt >= simdi:
                bilet_info["durum"] = "Aktif"
                aktif_biletler.append(bilet_info)
            else:
                bilet_info["durum"] = "Seyahat tamamlandı"
                gecmis_biletler.append(bilet_info)

    if tip == "gecmis":
        gonderilecek = gecmis_biletler
    else:
        tip = "aktif"
        gonderilecek = aktif_biletler

    return render_template(
        "biletlerim.html",
        tip=tip,
        biletler=gonderilecek
    )
# -----------------------------------------------------------------


# ------------------ Bilet Ekranı ------------------
@app.route("/bilet_ekrani", methods=["GET", "POST"])
def bilet_ekrani():
    if "user_id" in session:
        ad = session.get("ad")
        soyad = session.get("soyad")
    else:
        ad_cookie = request.cookies.get("user_name")
        soyad_cookie = request.cookies.get("user_surname")
        mail_cookie = request.cookies.get("user_mail")

        if not ad_cookie or not soyad_cookie or not mail_cookie:
            return redirect(url_for("home"))

        try:
            ad = gizli_sifre.unsign(ad_cookie).decode()
            soyad = gizli_sifre.unsign(soyad_cookie).decode()
            mail = gizli_sifre.unsign(mail_cookie).decode()
        except BadSignature:
            return redirect(url_for("home"))

        conn, cursor = create_database()
        cursor.execute("SELECT ID FROM Kullanici WHERE E_Posta=?", (mail,))
        sonuc = cursor.fetchone()
        conn.close()
        if not sonuc:
            return redirect(url_for("home"))

        user_id = sonuc[0]
        session.permanent = True
        session["user_id"] = user_id
        session["ad"] = ad
        session["soyad"] = soyad
        session["mail"] = mail

    if request.method == "POST":
        tarih = request.form["tarih_secim"]
        kalkis = request.form["kalkis"]
        varis = request.form["varis"]

        conn, cursor = create_database()
        df = pd.read_sql_query(
            "SELECT * FROM Sefer WHERE Kalkis=? AND Varis=? AND Tarih=?",
            conn,
            params=(kalkis, varis, tarih)
        )

        for index, row in df.iterrows():
            sefer_id = int(row["Sefer_ID"])
            if pd.isna(row["Sure"]) or row["Sure"] == 0:
                sure, fiyat = hesapla_sure_ve_fiyat(row["Kalkis"], row["Varis"])
                df.at[index, "Sure"] = sure
                df.at[index, "Fiyat"] = fiyat

                cursor.execute(
                    "UPDATE Sefer SET Sure = ?, Fiyat = ? WHERE Sefer_ID = ?",
                    (sure, fiyat, sefer_id)
                )

        conn.commit()
        conn.close()

        session["df"] = df.to_json()
        return redirect(url_for("seferler"))

    return render_template("bilet_ekrani.html", name=f"{ad} {soyad}")
# --------------------------------------------------


# ---------------- Seferler ekranı -------------------
@app.route("/seferler")
def seferler():
    df_json = session.get('df')
    if not df_json:
        return redirect(url_for("bilet_ekrani"))

    df = pd.read_json(df_json)
    veri = df.to_dict(orient="records")
    return render_template("seferler.html", seferler=veri)
# ----------------------------------------------------


# ----------------- Kayıt olma sayfası ----------------
@app.route("/kayit", methods=["GET", "POST"])
def kayit():
    mesaj = None
    if request.method == "POST":
        ad = request.form["user_name"]
        soyad = request.form["user_surname"]
        dogum_gunu = request.form["user_birthday"]
        mail = request.form["user_mail"]
        sifre = request.form["user_password"]

        conn, cursor = create_database()

        cursor.execute("SELECT * FROM Kullanici WHERE E_Posta = ?", (mail,))
        mail_sorgulama = cursor.fetchall()

        if mail_sorgulama == []:
            cursor.execute(
                "INSERT INTO Kullanici (Ad,Soyad,Dogum_gunu,E_Posta,Sifre) VALUES (?,?,?,?,?)",
                (ad, soyad, dogum_gunu, mail, sifre)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("home"))
        else:
            mesaj = "Bu e-posta zaten kayıtlı."
            conn.close()

    return render_template("kayit.html", mesaj=mesaj)
# ----------------------------------------------------


# --------------- Profil sayfası (bilgi güncelle) -------------
@app.route("/profil", methods=["GET", "POST"])
def profil():
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]
    mesaj = None
    mesaj_tipi = None

    conn, cursor = create_database()

    if request.method == "POST":
        yeni_ad = request.form.get("ad", "").strip()
        yeni_soyad = request.form.get("soyad", "").strip()
        yeni_dogum = request.form.get("dogum_gunu", "").strip()
        yeni_mail = request.form.get("mail", "").strip()

        if not (yeni_ad and yeni_soyad and yeni_dogum and yeni_mail):
            mesaj = "Lütfen tüm alanları doldurun."
            mesaj_tipi = "hata"
        else:
            cursor.execute(
                "SELECT ID FROM Kullanici WHERE E_Posta = ? AND ID != ?",
                (yeni_mail, user_id)
            )
            var_mi = cursor.fetchone()
            if var_mi:
                mesaj = "Bu e-posta başka bir kullanıcı tarafından kullanılıyor."
                mesaj_tipi = "hata"
            else:
                cursor.execute("""
                    UPDATE Kullanici
                    SET Ad = ?, Soyad = ?, Dogum_gunu = ?, E_Posta = ?
                    WHERE ID = ?
                """, (yeni_ad, yeni_soyad, yeni_dogum, yeni_mail, user_id))
                conn.commit()

                session["ad"] = yeni_ad.capitalize()
                session["soyad"] = yeni_soyad.capitalize()
                session["mail"] = yeni_mail

                mesaj = "Bilgileriniz başarıyla güncellendi."
                mesaj_tipi = "basari"

    cursor.execute("""
        SELECT Ad, Soyad, Dogum_gunu, E_Posta
        FROM Kullanici
        WHERE ID = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return redirect(url_for("home"))

    ad, soyad, dogum_gunu, mail = row

    return render_template(
        "profil.html",
        ad=ad,
        soyad=soyad,
        dogum_gunu=dogum_gunu,
        mail=mail,
        mesaj=mesaj,
        mesaj_tipi=mesaj_tipi
    )
# -------------------------------------------------------------


# -------------------Koltuk seçme sayfası --------------
@app.route("/koltuk_sec/<int:sefer_id>", methods=["GET", "POST"])
def koltuk_sec(sefer_id):
    if "user_id" not in session:
        return redirect(url_for("home"))

    conn, cursor = create_database()

    cursor.execute("""
        SELECT Sefer_ID, Kalkis, Varis, Firma, Tarih, Saat, Sure, Fiyat
        FROM Sefer
        WHERE Sefer_ID = ?
    """, (sefer_id,))
    satir = cursor.fetchone()

    if not satir:
        conn.close()
        return redirect(url_for("bilet_ekrani"))

    sefer_id_db, kalkis, varis, firma, tarih, saat, sure, fiyat = satir

    cursor.execute("""
        SELECT Koltuk_no 
        FROM Koltuklar 
        WHERE Sefer_ID = ? AND Koltuk_Durum = 'Dolu'
    """, (sefer_id_db,))
    dolu_koltuklar = [row[0] for row in cursor.fetchall()]

    if request.method == "POST":
        koltuk_no = request.form.get("koltuk_no")

        if not koltuk_no:
            conn.close()
            return render_template(
                "koltuk_sec.html",
                sefer_id=sefer_id_db,
                kalkis=kalkis,
                varis=varis,
                firma=firma,
                tarih=tarih,
                saat=saat,
                sure=sure,
                fiyat=fiyat,
                dolu_koltuklar=dolu_koltuklar,
                mesaj="Lütfen bir koltuk seçiniz."
            )

        koltuk_no = int(koltuk_no)

        cursor.execute("""
            SELECT Koltuk_Durum 
            FROM Koltuklar 
            WHERE Sefer_ID = ? AND Koltuk_no = ?
        """, (sefer_id_db, koltuk_no))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return "Böyle bir koltuk yok.", 400

        durum = row[0]

        if durum == "Boş":
            session["secili_sefer_id"] = sefer_id_db
            session["secili_koltuk_no"] = koltuk_no

            conn.close()
            return redirect(url_for("bilet_bilgi"))
        else:
            conn.close()
            return render_template(
                "koltuk_sec.html",
                sefer_id=sefer_id_db,
                kalkis=kalkis,
                varis=varis,
                firma=firma,
                tarih=tarih,
                saat=saat,
                sure=sure,
                fiyat=fiyat,
                dolu_koltuklar=dolu_koltuklar,
                mesaj="Bu koltuk zaten dolu, lütfen başka koltuk seçiniz."
            )

    conn.close()

    return render_template(
        "koltuk_sec.html",
        sefer_id=sefer_id_db,
        kalkis=kalkis,
        varis=varis,
        firma=firma,
        tarih=tarih,
        saat=saat,
        sure=sure,
        fiyat=fiyat,
        dolu_koltuklar=dolu_koltuklar
    )
#-------------------------------------------------------


# ---------------- Bilet bilgi / onay sayfası -----------
@app.route("/bilet_bilgi", methods=["GET", "POST"])
def bilet_bilgi():
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]
    sefer_id = session.get("secili_sefer_id")
    koltuk_no = session.get("secili_koltuk_no")

    if not sefer_id or not koltuk_no:
        return redirect(url_for("bilet_ekrani"))

    conn, cursor = create_database()
    cursor.execute("SELECT Kalkis , Varis , Firma , Tarih , Saat , Sure , Fiyat  FROM Sefer WHERE Sefer_ID = ?", (sefer_id,))
    bilgiler = cursor.fetchone()

    if not bilgiler:
        conn.close()
        return redirect(url_for("bilet_ekrani"))

    kalkis, varis, firma, tarih, saat, sure, fiyat = bilgiler

    if request.method == "POST":
        cursor.execute("""
            UPDATE Koltuklar 
            SET Koltuk_Durum = ? 
            WHERE Sefer_ID = ? AND Koltuk_no = ?
        """, ("Dolu", sefer_id, koltuk_no))

        satin_alma = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("""
            INSERT INTO Biletler (Kullanici_ID, Sefer_ID, Koltuk_No, Satin_Alma_Tarihi)
            VALUES (?,?,?,?)
        """, (user_id, sefer_id, koltuk_no, satin_alma))

        conn.commit()
        conn.close()

        session.pop("secili_sefer_id", None)
        session.pop("secili_koltuk_no", None)

        return redirect(url_for("biletlerim", tip="aktif"))

    conn.close()

    return render_template(
        "bilet_bilgi.html",
        kalkis=kalkis,
        varis=varis,
        firma=firma,
        tarih=tarih,
        saat=saat,
        sure=sure,
        fiyat=fiyat,
        koltuk_no=koltuk_no,
    )
# -------------------------------------------------------


# --------------- Bilet iade ----------------------------
@app.route("/bilet_iade/<int:bilet_id>", methods=["POST"])
def bilet_iade(bilet_id):
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]

    conn, cursor = create_database()

    cursor.execute("""
        SELECT Sefer_ID, Koltuk_No, Iade_Edildi
        FROM Biletler
        WHERE ID = ? AND Kullanici_ID = ?
    """, (bilet_id, user_id))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return redirect(url_for("biletlerim", tip="aktif"))

    sefer_id, koltuk_no, iade_edildi = row

    if iade_edildi:
        conn.close()
        return redirect(url_for("biletlerim", tip="aktif"))

    cursor.execute("""
        SELECT Tarih, Saat, Sure
        FROM Sefer
        WHERE Sefer_ID = ?
    """, (sefer_id,))
    sefer_row = cursor.fetchone()

    if sefer_row:
        tarih, saat, sure = sefer_row
        sefer_dt = datetime.strptime(f"{tarih} {saat}", "%Y-%m-%d %H:%M")
        simdi = datetime.now()

        if simdi >= sefer_dt:
            conn.close()
            return redirect(url_for("biletlerim", tip="aktif"))

    cursor.execute("""
        UPDATE Koltuklar
        SET Koltuk_Durum = 'Boş'
        WHERE Sefer_ID = ? AND Koltuk_no = ?
    """, (sefer_id, koltuk_no))

    cursor.execute("""
        UPDATE Biletler
        SET Iade_Edildi = 1
        WHERE ID = ? AND Kullanici_ID = ?
    """, (bilet_id, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for("biletlerim", tip="aktif"))
# -------------------------------------------------------


# ---------------- Şifre değiştirme -----------------
@app.route("/sifre_degistir", methods=["GET", "POST"])
def sifre_degistir():
    if "user_id" not in session:
        return redirect(url_for("home"))

    user_id = session["user_id"]
    mesaj = None
    mesaj_tipi = None

    if request.method == "POST":
        eski_sifre = request.form.get("eski_sifre", "")
        yeni_sifre = request.form.get("yeni_sifre", "")
        yeni_sifre_tekrar = request.form.get("yeni_sifre_tekrar", "")

        sifre_gucu = re.findall(r'[^\w\s]', yeni_sifre)
        if not eski_sifre or not yeni_sifre or not yeni_sifre_tekrar:
            mesaj = "Lütfen tüm alanları doldurun."
            mesaj_tipi = "hata"
        elif yeni_sifre != yeni_sifre_tekrar:
            mesaj = "Yeni şifreler birbiriyle uyuşmuyor."
            mesaj_tipi = "hata"
        elif len(yeni_sifre) < 8:
            mesaj = "Yeni şifre en az 8 karakter olmalıdır."
            mesaj_tipi = "hata"
        elif len(sifre_gucu) == 0:
            mesaj = "Şifrede en az bir noktalama işareti olmalı."
            mesaj_tipi = "hata"
        else:
            conn, cursor = create_database()
            cursor.execute("SELECT Sifre FROM Kullanici WHERE ID = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                mesaj = "Kullanıcı bulunamadı."
                mesaj_tipi = "hata"
            else:
                mevcut_sifre = row[0]
                if mevcut_sifre != eski_sifre:
                    conn.close()
                    mesaj = "Mevcut şifrenizi hatalı girdiniz."
                    mesaj_tipi = "hata"
                else:
                    cursor.execute(
                        "UPDATE Kullanici SET Sifre = ? WHERE ID = ?",
                        (yeni_sifre, user_id)
                    )
                    conn.commit()
                    conn.close()
                    mesaj = "Şifreniz başarıyla güncellendi."
                    mesaj_tipi = "basari"

    return render_template(
        "sifre_degistir.html",
        mesaj=mesaj,
        mesaj_tipi=mesaj_tipi
    )
# ----------------------------------------------------


# ---------------- Admin panel -----------------
@app.route("/admin_panel")
def admin_panel():
    if "user_id" not in session:
        return redirect(url_for("home"))
    bugun = datetime.now().date()
    user_id = session["user_id"]
    conn, cursor = create_database()

    cursor.execute("SELECT Rol FROM Kullanici WHERE ID = ?", (user_id,))
    row = cursor.fetchone()
    if not row or row[0] != "admin":
        conn.close()
        return redirect(url_for("kullanici_panel"))

    cursor.execute("SELECT COUNT(*) FROM Kullanici")
    toplam_kullanici = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Sefer")
    toplam_sefer = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Biletler")
    toplam_bilet = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Biletler WHERE Iade_Edildi = 1")
    iade_edilen_bilet_sayisi = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Sefer WHERE Tarih =?",(bugun.strftime("%Y-%m-%d"),))
    bugun_sefer_sayisi=cursor.fetchone()[0]
    conn.close()

    grafik = admin_istatistik_grafik()

    return render_template(
        "admin_panel.html",
        toplam_kullanici=toplam_kullanici,
        toplam_sefer=toplam_sefer,
        toplam_bilet=toplam_bilet,
        iade_edilen_bilet_sayisi=iade_edilen_bilet_sayisi,
        grafik=grafik,
        bugun_sefer_sayisi=bugun_sefer_sayisi
    )

# ----------------------------------------------------


# 🌟 YENİ: Chatbot sayfası (sadece arayüz)
@app.route("/chatbot")
def chatbot():
    if "user_id" not in session:
        return redirect(url_for("home"))
    return render_template("chatbot.html")


# 🌟 YENİ: Chatbot API (Gemini + veritabanı ile konuşan endpoint)
@app.route("/chatbot_api", methods=["POST"])
def chatbot_api():
    if "user_id" not in session:
        return jsonify({"error": "Oturum bulunamadı. Lütfen tekrar giriş yapın."}), 401

    data = request.get_json() or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Mesaj boş olamaz."}), 400

    # 1️⃣ ÖNCE: Mesaj sefer sorgusu gibi mi? (şehir + tarih var mı?)
    sefer_sorgu = ayikla_sefer_sorgusu(user_message)
    if sefer_sorgu is not None:
        kalkis, varis, tarih_str = sefer_sorgu

        # Veritabanından gerçek seferleri çek
        conn, cursor = create_database()
        df = pd.read_sql_query(
            "SELECT * FROM Sefer WHERE Kalkis=? AND Varis=? AND Tarih=?",
            conn,
            params=(kalkis, varis, tarih_str)
        )

        # Süre / fiyat eksikse dolduralım
        for index, row in df.iterrows():
            sefer_id = int(row["Sefer_ID"])
            if pd.isna(row["Sure"]) or row["Sure"] == 0:
                sure, fiyat = hesapla_sure_ve_fiyat(row["Kalkis"], row["Varis"])
                df.at[index, "Sure"] = sure
                df.at[index, "Fiyat"] = fiyat

                cursor.execute(
                    "UPDATE Sefer SET Sure = ?, Fiyat = ? WHERE Sefer_ID = ?",
                    (sure, fiyat, sefer_id)
                )

        conn.commit()
        conn.close()

        if df.empty:
            cevap = f"{tarih_str} tarihinde {kalkis} → {varis} için kayıtlı bir sefer bulunamadı."
            return jsonify({"answer": cevap})

        # Sefer varsa, seferler.html'de kullanılmak üzere session'a koy
        session["df"] = df.to_json()

        cevap = f"{tarih_str} tarihinde {kalkis} → {varis} için {len(df)} adet sefer bulundu. Seferler sayfasına yönlendiriyorum."

        return jsonify({
            "answer": cevap,
            "redirect": url_for("seferler")
        })

    # 2️⃣ Sefer sorgusu değilse → Gemini'ye bırak
    if gemini_model is None:
        return jsonify({
            "answer": "Şu an yapay zeka servisi yapılandırılmamış görünüyor, ama menüden bilet arama işlemlerinizi yapabilirsiniz."
        })

    try:
        prompt = f"""
Sen Doğu Bilet isimli otobüs bileti web sitesinin yapay zeka asistanısın.
Görevin:
- Kullanıcının bilet arama, bilet alma, iade, sefer süresi, fiyat bilgisi vb. konularda soru sormasına yardımcı olmak.
- Eğer kullanıcı cümlesinde hem kalkış, hem varış şehri hem de tarih belirtirse,
  backend zaten veritabanından uygun seferleri bulup kullanıcıyı /seferler sayfasına yönlendirecektir.
- Sen genel olarak açıklama, yönlendirme, kurallar vb. konularda yardımcı ol.
- Bilet sistemi dışındaki konularda ısrar edilirse
  'Ben yalnızca bilet sistemiyle ilgili sorulara yardımcı olabiliyorum.' de.
- Cevapları kısa ve anlaşılır Türkçe ile ver.

Kullanıcının sorusu:
\"\"\"{user_message}\"\"\""""
        resp = gemini_model.generate_content(prompt)
        answer = (resp.text or "").strip()
        if not answer:
            answer = "Şu an yanıt üretirken bir sorun oluştu, lütfen tekrar dener misiniz."

        return jsonify({"answer": answer})

    except Exception as e:
        print("Gemini hatası:", repr(e))
        return jsonify({"error": "Yapay zeka servisinde bir hata oluştu. Detay: " + str(e)}), 500

# -------------- Kullanıcı Çıkışı -------------
@app.route("/cikis")
def cikis():
    session.clear()

    response = make_response(redirect(url_for("home")))
    response.delete_cookie("user_name")
    response.delete_cookie("user_surname")
    response.delete_cookie("user_mail")
    return response
# ---------------------------------------------


if __name__ == "__main__":
    conn, cursor = create_database()
    create_table(cursor)
    admin_yap(cursor)
    conn.commit()
    conn.close()

    app.run(debug=True)
