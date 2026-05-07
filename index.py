from http.server import BaseHTTPRequestHandler
import requests
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        gold_url = "https://static.altinkaynak.com/public/Gold"
        currency_url = "https://static.altinkaynak.com/public/Currency"
        
        # Supabase Bilgilerimiz
        SUPABASE_URL = "https://tfhdnjevpmjphaxclwwv.supabase.co"
        SUPABASE_KEY = "sb_publishable_cpoS5N_YNqiC_ZkREDxvAA_k4eVfLBf"
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        try:
            # 1. Altınkaynak JSON API'den canlı veriyi çek (Bot koruması yok, engellenmez!)
            gold_res = requests.get(gold_url, timeout=5).json()
            currency_res = requests.get(currency_url, timeout=5).json()
            
            all_live_data = gold_res + currency_res
            
            # 2. Supabase'den eski fiyatları çek (Karşılaştırma yapmak için)
            sb_res = requests.get(f"{SUPABASE_URL}/rest/v1/prices", headers=headers)
            old_prices = {item['id']: item for item in sb_res.json()} if sb_res.status_code == 200 else {}
            
            final_data = []
            updates = []
            
            # 3. YÜZDE DEĞİŞİM HESAPLAMA MOTORU
            for item in all_live_data:
                kod = item.get("Kod")
                if not kod: continue
                
                try:
                    buying = float(str(item.get("Alis", "0")).replace(".", "").replace(",", "."))
                    selling = float(str(item.get("Satis", "0")).replace(".", "").replace(",", "."))
                except:
                    continue
                
                name = item.get("Aciklama", kod)
                
                # Maden Tipi Belirleme
                asset_type = "currency"
                if kod in ["HH_T", "CH_T", "A", "GAT", "B_T", "A_T", "B", "18", "14", "C", "Y", "T", "G", "A5", "R", "H", "GA", "EC", "EY", "ET", "EG", "XAUUSD", "IAB_KAPANIS"]:
                    asset_type = "gold"
                elif kod == "AG_T":
                    asset_type = "silver"
                    
                percentage = 0.0
                old_data = old_prices.get(kod)
                
                if old_data:
                    old_selling = float(old_data.get("selling", 0))
                    old_percentage = float(old_data.get("percentage", 0))
                    
                    # Eğer fiyat değişmişse yeni % değişimi hesapla!
                    if old_selling > 0 and selling != old_selling:
                        percentage = ((selling - old_selling) / old_selling) * 100
                        percentage = round(percentage, 2)
                    else:
                        percentage = old_percentage # Fiyat aynıysa eski yüzdeyi koru
                
                row = {
                    "id": kod,
                    "name": name,
                    "buying": buying,
                    "selling": selling,
                    "percentage": percentage,
                    "asset_type": asset_type,
                    "updated_at": datetime.utcnow().isoformat()
                }
                final_data.append(row)
                updates.append(row)
            
            # 4. Supabase'i yeni fiyatlar ve yeni yüzdelerle güncelle
            if updates:
                upsert_headers = headers.copy()
                upsert_headers["Prefer"] = "resolution=merge-duplicates"
                requests.post(f"{SUPABASE_URL}/rest/v1/prices", headers=upsert_headers, json=updates)
            
            # 5. Mobil uygulamaya hazır veriyi gönder
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 's-maxage=30, stale-while-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(final_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
