from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = "https://www.altinkaynak.com/canli-kurlar/altin"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            fiyatlar = []

            # Altınkaynak sitesindeki ana veri tablosunu ID üzerinden yakalıyoruz
            # Genellikle 'currGold' veya 'double-scroll' class'lı bir div içindedir
            rows = soup.select('table tr') # Daha geniş bir seçici

            for row in rows:
                cols = row.find_all('td')
                
                # Eğer td'ler boşsa th (başlık) kontrolü yapalım veya direkt veriyi süzelim
                if len(cols) >= 3:
                    tur = cols[0].get_text(strip=True)
                    # Sadece içinde rakam olan veya anlamlı satırları alalım
                    if any(char.isdigit() for char in cols[1].text):
                        fiyatlar.append({
                            "tur": tur,
                            "alis": cols[1].get_text(strip=True),
                            "satis": cols[2].get_text(strip=True),
                            "saat": cols[4].get_text(strip=True) if len(cols) > 4 else ""
                        })

            # Eğer hala boşsa, farklı bir seçici deneyelim (Sitedeki yeni kart yapısı için)
            if not fiyatlar:
                items = soup.select('.fiyat-item') # Bazı versiyonlarda kart yapısı var
                for item in items:
                    tur = item.select_one('.label').text.strip()
                    fiyat = item.select_one('.value').text.strip()
                    fiyatlar.append({"tur": tur, "fiyat": fiyat})

            if not fiyatlar:
                result = {"hata": "Veri bulunamadı, seçiciler güncellenmeli.", "debug": "Siteye ulasildi ancak tablo bos."}
            else:
                result = fiyatlar

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"hata": str(e)}).encode('utf-8'))
