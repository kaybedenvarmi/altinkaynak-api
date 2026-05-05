from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Hedef URL
        url = "https://www.altinkaynak.com/canli-kurlar/altin"
        
        # Siteyi gerçek bir kullanıcı olduğumuza ikna etmek için headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        }

        try:
            # Siteye istek atıyoruz
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status() # Hata varsa yakala
            
            soup = BeautifulSoup(response.content, 'html.parser')
            fiyatlar = []

            # Altınkaynak genellikle verileri <table> içinde sunar.
            # Sayfadaki tüm satırları (tr) buluyoruz.
            rows = soup.find_all('tr')

            for row in rows:
                cols = row.find_all('td')
                # Eğer satırda en az 3 sütun varsa (Tür, Alış, Satış)
                if len(cols) >= 3:
                    fiyatlar.append({
                        "tur": cols[0].get_text(strip=True),
                        "alis": cols[1].get_text(strip=True),
                        "satis": cols[2].get_text(strip=True),
                        # Varsa değişim oranını da alalım
                        "degisim": cols[3].get_text(strip=True) if len(cols) > 3 else "0.00"
                    })

            # Eğer veri çekilemediyse boş liste yerine bilgi verelim
            if not fiyatlar:
                result = {"hata": "Veri bulunamadı, site yapısı değişmiş olabilir."}
            else:
                result = fiyatlar

            # Başarılı Yanıt Gönderimi
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*') # Flutter için kritik
            self.end_headers()
            
            # JSON olarak ekrana basıyoruz
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # Hata oluşursa hatayı JSON olarak dönüyoruz
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_res = {"hata": str(e)}
            self.wfile.write(json.dumps(error_res).encode('utf-8'))
