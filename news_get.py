import requests
import os
import re
from bs4 import BeautifulSoup

# --- 設定 ---
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_AFF_ID = os.getenv("RAKUTEN_AFFILIATE_ID")
HISTORY_FILE = "sent_products.txt"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_history(product_name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(product_name + "\n")

def get_rakuten_info(keyword):
    if not RAKUTEN_APP_ID: return None, None
    clean_keyword = keyword.split(' / ')[0][:30]
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFF_ID,
        "keyword": clean_keyword,
        "sort": "+itemPrice",
        "hits": 1
    }
    try:
        res = requests.get(url, params=params).json()
        if "Items" in res and res["Items"]:
            item = res["Items"][0]["Item"]
            return item["itemPrice"], item["affiliateUrl"]
    except:
        pass
    return None, None

def main():
    sent_list = load_history()
    print(f"--- 巡回開始（既知の商品数: {len(sent_list)}） ---")
    
    url = "https://lipscosme.com/product_categories/1"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.find_all("div", class_="style_productCard__N_7_L")
    
    found_new = False

    for item in items:
        name_tag = item.find("div", class_="style_productName__m6m_e")
        if not name_tag: continue
        name = name_tag.get_text().strip()

        # 【超重要】すでに送った商品ならスキップ（記憶チェック）
        if name in sent_list:
            continue

        price_tag = item.find("div", class_="style_price__0058I")
        clip_tag = item.find("span", class_="style_clipCount__IeR_P")
        
        list_price = int(re.sub(r'\D', '', price_tag.get_text())) if price_tag else 0
        clip_count = int(re.sub(r'\D', '', clip_tag.get_text())) if clip_tag else 0
        
        rakuten_price, aff_url = get_rakuten_info(name)
        
        # 判定ロジック：人気があるか、新作・限定か
        if (clip_count >= 100) or ("新作" in name or "限定" in name):
            # 楽天に商品がある場合のみ通知（稼ぐため）
            if rakuten_price:
                msg = f"🆕 **【新着/トレンド検知】**\n**{name}**\n"
                msg += f"📊 人気: {clip_count} clips\n"
                msg += f"💰 楽天最安: ￥{rakuten_price:,}\n"
                msg += f"🔗 [商品ページはこちら]({aff_url})\n※PR"
                
                requests.post(WEBHOOK_URL, json={"content": msg})
                save_history(name) # 記憶に保存
                found_new = True
                print(f"新着を通知しました: {name}")

    if not found_new:
        print("新しい更新はありませんでした。")

if __name__ == "__main__":
    main()