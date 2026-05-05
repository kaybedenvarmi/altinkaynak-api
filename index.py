from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Altınkaynak Canlı Kurlar Sayfası
        url = "https://www.altinkaynak.com/canli-kurlar/altin"
        
        # Siteye gerçek bir tarayıcı gibi görünmek için detaylı headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.altinkaynak.com/',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
        }

        try:
            # 1. Siteye istek atıyoruz
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            fiyatlar = []
            
            # 2. Sitedeki tüm tabloları tarayalım (Altın tablosu genellikle id="currGold" veya benzeridir)
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    
                    # En az 3 sütun (Tür, Alış, Satış) olan satırları işle
                    if len(cols) >= 3:
                        text_list = [c.get_text(strip=True) for c in cols]
                        
                        # Sadece Alış sütununda rakam olan satırları al (Başlıkları elemek için)
                        if any(char.isdigit() for char in text_list[1]):
                            fiyatlar.append({
                                "tur": text_list[0],
                                "alis": text_list[1],
                                "satis": text_list[2],
                                "degisim": text_list[3] if len(text_list) > 3 else "%0,00",
                                "saat": text_list[4] if len(text_list) > 4 else ""
                            })

            # 3. Eğer hiçbir veri bulunamadıysa (Scraping hatası kontrolü)
            if not fiyatlar:
                result = {
                    "hata": "Veri ayıklanamadı",
                    "debug": "HTML Uzunluğu: " + str(len(response.text)),
                    "ipucu": "Site yapısı değişmiş veya bot korumasına takılmış olabilir."
                }
            else:
                result = fiyatlar

            # 4. Yanıtı Gönder
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*') # Flutter erişimi için
            self.end_headers()
            
            # JSON formatında ve Türkçe karakterleri koruyarak bas
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # Hata durumunda 500 kodu ve hata mesajı dön
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_res = {"hata": str(e)}
            self.wfile.write(json.dumps(error_res).encode('utf-8'))
