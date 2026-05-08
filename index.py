from http.server import BaseHTTPRequestHandler
import requests
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        gold_url = "https://static.altinkaynak.com/public/Gold"
        currency_url = "https://static.altinkaynak.com/public/Currency"
        
        SUPABASE_URL = "https://tfhdnjevpmjphaxclwwv.supabase.co"
        SUPABASE_KEY = "sb_publishable_cpoS5N_YNqiC_ZkREDxvAA_k4eVfLBf"
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        try:
            # 1. Altınkaynak'tan CANLI verileri çek
            gold_res = requests.get(gold_url, timeout=5).json()
            currency_res = requests.get(currency_url, timeout=5).json()
            all_live_data = gold_res + currency_res
            
            # 2. Supabase'den DÜNKÜ / SABAHKİ açılış fiyatlarını çek
            sb_res = requests.get(f"{SUPABASE_URL}/rest/v1/prices", headers=headers)
            old_prices = {item['id']: item for item in sb_res.json()} if sb_res.status_code == 200 else {}
            
            final_data = []
            updates = []
            
            # UTC saatine göre şu anki "Tarih" (Gün değişti mi kontrolü için)
            current_date = datetime.utcnow().date().isoformat()
            
            for item in all_live_data:
                kod = item.get("Kod")
                if not kod: continue
                
                try:
                    buying = float(str(item.get("Alis", "0")).replace(".", "").replace(",", "."))
                    selling = float(str(item.get("Satis", "0")).replace(".", "").replace(",", "."))
                except:
                    continue
                
                name = item.get("Aciklama", kod)
                
                asset_type = "currency"
                if kod in ["HH_T", "CH_T", "A", "GAT", "B_T", "A_T", "B", "18", "14", "C", "Y", "T", "G", "A5", "R", "H", "GA", "EC", "EY", "ET", "EG", "XAUUSD", "IAB_KAPANIS"]:
                    asset_type = "gold"
                elif kod == "AG_T":
                    asset_type = "silver"
                    
                old_data = old_prices.get(kod)
                percentage = 0.0
                needs_db_update = False
                
                if not old_data:
                    # Hiç kayıt yoksa ilk defa kaydet
                    needs_db_update = True
                else:
                    last_update = old_data.get("updated_at", "")
                    
                    if not last_update.startswith(current_date):
                        # Gün değişmiş! Yeni sabahın açılış fiyatını kaydet (Günde 1 kez)
                        needs_db_update = True
                    else:
                        # Hala aynı gün içindeyiz. Supabase'deki fiyat SABAHKİ AÇILIŞ fiyatıdır.
                        daily_open_price = float(old_data.get("selling", 0))
                        
                        # Canlı fiyat ile sabahki açılış fiyatını karşılaştır ve GÜNLÜK YÜZDEYİ hesapla!
                        if daily_open_price > 0 and selling != daily_open_price:
                            percentage = ((selling - daily_open_price) / daily_open_price) * 100
                            percentage = round(percentage, 2)
                
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
                
                if needs_db_update:
                    # Sadece gün dönümünde (veya ilk kayıtta) veritabanına yeni açılış fiyatı yazılır
                    updates.append({
                        "id": kod,
                        "name": name,
                        "buying": buying,
                        "selling": selling,
                        "percentage": 0.0, 
                        "asset_type": asset_type,
                        "updated_at": datetime.utcnow().isoformat()
                    })
            
            # 3. Eğer gün değiştiyse Supabase'e yeni açılış fiyatlarını kaydet
            if updates:
                upsert_headers = headers.copy()
                upsert_headers["Prefer"] = "resolution=merge-duplicates"
                requests.post(f"{SUPABASE_URL}/rest/v1/prices", headers=upsert_headers, json=updates)
            
            # 4. Mobil uygulamaya gerçek ve hesaplanmış yüzdelerle gönder
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 's-maxage=30, stale-while-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(final_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
