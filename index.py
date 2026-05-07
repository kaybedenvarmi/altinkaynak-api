from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Altınkaynak HTML sayfası
        url = "https://www.altinkaynak.com/canli-kurlar/altin"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            fiyatlar = []
            
            # Tüm tablo satırlarını (tr) bul
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                
                # Eğer satırda en az 3 sütun varsa (Tür, Alış, Satış)
                if len(cols) >= 3:
                    # Yüzdelik değişim 4. sütunda (cols[3]) var mı diye güvenli kontrol yapıyoruz
                    yuzde = "%0.00"
                    if len(cols) >= 4:
                        yuzde = cols[3].get_text(strip=True)
                        
                    fiyatlar.append({
                        "tur": cols[0].get_text(strip=True),
                        "alis": cols[1].get_text(strip=True),
                        "satis": cols[2].get_text(strip=True),
                        "yuzde": yuzde # Canlı değişim oranını ekledik!
                    })
                    
            # Başarılı cevap (200) ve güvenlik başlıkları
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            
            # Vercel Caching (Çok Önemli! Sunucunun yorulmaması için veriyi 30 sn hafızada tutar)
            self.send_header('Cache-Control', 's-maxage=30, stale-while-revalidate')
            
            self.end_headers()
            
            # Türkçe karakterlerin bozulmaması için ensure_ascii=False
            self.wfile.write(json.dumps(fiyatlar, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            # Hata durumunda
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
