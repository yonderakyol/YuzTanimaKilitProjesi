from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer
from arayuzler.ui_door_check import Ui_DoorCheck
import cv2
import face_recognition
import numpy as np
import glob
import os
from model.Veritabani_Kisi import VeriTabaniKisi

class DoorCheck(QWidget):
    def __init__(self):
        super(DoorCheck,self).__init__()
        self.ui = Ui_DoorCheck()
        self.ui.setupUi(self)
        self.timer = QTimer()
        self.klasorBilgileri() #klasörlerdeki bilgileri alıyoruz.
        self.timer.timeout.connect(self.kameraGoster)
        self.Uzaklik = 0.6  # tanima orani
        self.ui.btnTekrarDene.clicked.connect(self.clickKameraAc)
        self.vtk = VeriTabaniKisi()
        pass

    def klasorBilgileri(self):
        sozluk = {}
        Resimler = "resimler/kisiler"
        print(glob.glob((os.path.join(Resimler, '*.jpg'))))
        for dosyaad in glob.glob((os.path.join(Resimler, '*.jpg'))):
            image_rgb = face_recognition.load_image_file(dosyaad)
            kimlik = os.path.splitext(os.path.basename(dosyaad))
            konumlar = face_recognition.face_locations(image_rgb)
            kodlamalar = face_recognition.face_encodings(image_rgb, konumlar)
            sozluk[kimlik] = kodlamalar[0]

        self.yuzler = list(sozluk.values())
        self.adlar = list(sozluk.keys())

    def kameraGoster(self):
        ret, kare = self.kamera.read()
        kare = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
        height, width, channel = kare.shape
        step = channel * width
        self.sonGoruntu = kare  # resmin ekrandaki son  temiz hali
        kontrolluResim = self.kontrolluResimGoster(kare)
        qImg = QImage(kontrolluResim.data, width, height, step, QImage.Format_RGB888)
        self.ui.lbKamera.setPixmap(QPixmap.fromImage(qImg))

    def clickKameraAc(self):
        if not self.timer.isActive():
            self.kamera = cv2.VideoCapture(0)
            self.ui.btnTekrarDene.setText("Durdur")
            self.timer.start(20)
        else:
            self.kameraDurdur()

    def kameraDurdur(self):
        self.ui.btnTekrarDene.setText("Tekrar Dene")
        self.timer.stop()
        self.kamera.release()

    def kontrolluResimGoster(self, kare):
        # kare = cv2.flip(kare, 1)  # 1 yatay 0 ise dikey
        kucuk_kare = cv2.resize(kare, (0, 0), fx=0.25, fy=0.25)
        rgb_kucuk_kare = kucuk_kare[:, :, ::-1]  # BGR -> RGB dönüsümü
        konumlar = face_recognition.face_locations(rgb_kucuk_kare)
        kodlamalar = face_recognition.face_encodings(rgb_kucuk_kare, konumlar)
        for konum, kodlama in zip(konumlar, kodlamalar):
            mesafeler = face_recognition.face_distance(self.yuzler, kodlama)
            if np.any(mesafeler <= self.Uzaklik):
                en_uygun = np.argmin(mesafeler)
                ad = self.adlar[en_uygun]
                #öğrenci tanındı.
                okulNo = int(ad[0])
                self.kisiGetir(okulNo=okulNo)
            else:
                #ogrenci tanınmadı
                ad = None
                self.ui.lbDurum.setText("Durum: Kişi Tanınmadı")
            tepe, sag, alt, sol = konum

            # eger goruntuyu kuculttuysek yeniden büyütmek gerekir
            tepe *= 4
            sag *= 4
            alt *= 4
            sol *= 4

            if ad is None:
                ad = "Bilinmiyor"
                renk = (0, 0, 255)
            else:
                renk = (0, 255, 0)

            # cerceve
            cv2.rectangle(kare, (sol, tepe), (sag, alt), renk, 2)

            # yazi arkaplani
            cv2.rectangle(kare, (sol, alt), (sag, alt + 30), renk, cv2.FILLED)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(kare, ad[0], (sol + 25, alt + 25), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        return kare

    def kisiGetir(self, okulNo):
        # self.kameraDurdur()
        self.vtk.Bagla()
        kisi = self.vtk.GetirOkulNo(okulNo)
        self.ui.lbDurum.setText(kisi.adSoyad + " Giriş Başarılı")
        self.vtk.Kes()