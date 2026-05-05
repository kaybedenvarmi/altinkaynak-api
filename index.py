from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Altınkaynak Canlı Kurlar Sayfası
        url = "https://www.altinkaynak.com/canli-kurlar/altin"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.altinkaynak.com/'
        }

        try:
            response = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            fiyatlar = []
            
            # Sitedeki tüm tabloları tarayalım
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    # En az 3 sütun ve ilk sütunda "Altın" kelimesi veya rakam içeren satırları seç
                    if len(cols) >= 3:
                        text_list = [c.get_text(strip=True) for c in cols]
                        
                        # Başlık satırlarını (Tür, Alış vb.) ve boş satırları eleyelim
                        if any(char.isdigit() for char in text_list[1]):
                            fiyatlar.append({
                                "tur": text_list[0],
                                "alis": text_list[1],
                                "satis": text_list[2],
                                "saat": text_list[4] if len(text_list) > 4 else ""
                            })

            # Eğer tablo boşsa alternatif bir yöntem: 'fiyat-item' classlarını tara
            if not fiyatlar:
                items = soup.find_all(class_='fiyat-item')
                for item in items:
                    try:
                        t = item.find(class_='label').text.strip()
                        v = item.find(class_='value').text.strip()
                        fiyatlar.append({"tur": t, "fiyat": v})
                    except: continue

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Veri hala boşsa debug bilgisini JSON'a ekle
            final_data = fiyatlar if fiyatlar else {"hata": "Veri ayiklanamadi", "debug": "HTML uzunlugu: " + str(len(response.text))}
            self.wfile.write(json.dumps(final_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"hata": str(e)}).encode('utf-8'))
