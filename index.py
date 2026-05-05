from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Engelleme olasılığı düşük ve stabil kaynak: Bigpara
        url = "https://bigpara.hurriyet.com.tr/altin/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            fiyatlar = []

            # Bigpara'daki altın fiyatları tablosunu hedef alıyoruz
            # Genellikle 'contentBox' veya 'table' class'ları içindedir
            rows = soup.select('.box.fiyatlar table tr')

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    # Tür, Alış, Satış ve Saat bilgisini çekiyoruz
                    tur = cols[0].get_text(strip=True)
                    alis = cols[1].get_text(strip=True)
                    satis = cols[2].get_text(strip=True)
                    saat = cols[3].get_text(strip=True) if len(cols) > 3 else ""

                    # Başlık satırlarını ve boş değerleri eliyoruz
                    if any(char.isdigit() for char in alis):
                        fiyatlar.append({
                            "tur": tur,
                            "alis": alis,
                            "satis": satis,
                            "saat": saat
                        })

            # Eğer yukarıdaki seçici çalışmazsa (Bigpara bazen yapı değiştirebilir), alternatif:
            if not fiyatlar:
                rows = soup.find_all('li', class_='cell015')
                # Bu kısım Bigpara'nın liste yapısı için yedektir

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(fiyatlar, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"hata": str(e)}).encode('utf-8'))
