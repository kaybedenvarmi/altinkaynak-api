from http.server import BaseHTTPRequestHandler
import requests
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        gold_url = "https://static.altinkaynak.com/public/Gold"
        currency_url = "https://static.altinkaynak.com/public/Currency"
        
        try:
            # Altınkaynak'ın kendi JSON API'lerinden verileri hızlıca çekiyoruz
            gold_res = requests.get(gold_url, timeout=5).json()
            currency_res = requests.get(currency_url, timeout=5).json()
            
            # Altın ve Dövizi tek bir pakette birleştiriyoruz
            fiyatlar = {
                "altin": gold_res,
                "doviz": currency_res
            }
            
            # Başarılı cevap (200) ve güvenlik başlıklarını ayarlıyoruz
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 's-maxage=30, stale-while-revalidate')
            self.end_headers()
            
            # Türkçe karakterlerin (Çeyrek, Gümüş vs.) bozulmaması için ensure_ascii=False kullanıyoruz
            self.wfile.write(json.dumps(fiyatlar, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            # Hata durumunda 500 kodu dönüp hatanın sebebini yazdırıyoruz
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
