from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Kaynak: Bigpara Altın Sayfası
        url = "https://bigpara.hurriyet.com.tr/altin/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            fiyatlar = []

            # Yöntem 1: Standart Tablo Taraması
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    t = cols[0].get_text(strip=True)
                    a = cols[1].get_text(strip=True)
                    s = cols[2].get_text(strip=True)
                    # Sadece içinde rakam olan satırları al
                    if any(char.isdigit() for char in a):
                        fiyatlar.append({"tur": t, "alis": a, "satis": s})

            # Yöntem 2: Eğer tablo boşsa alternatif liste yapısını tara
            if not fiyatlar:
                items = soup.select('.tableRow, .cell015')
                for item in items:
                    # Bu kısım Bigpara'nın mobil veya farklı görünüm yapıları için
                    text = item.get_text("|", strip=True).split("|")
                    if len(text) >= 3:
                        fiyatlar.append({"tur": text[0], "alis": text[1], "satis": text[2]})

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Eğer hala boşsa en azından boş liste yerine durum mesajı verelim
            output = fiyatlar if fiyatlar else [{"mesaj": "Veri su an cekilemedi, piyasa kapali olabilir."}]
            self.wfile.write(json.dumps(output, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"hata": str(e)}).encode('utf-8'))
