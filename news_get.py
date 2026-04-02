import requests
import os
from bs4 import BeautifulSoup

# --- 設定（GitHubのSecretsから自動で読み込まれます） ---
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_AFF_ID = os.getenv("RAKUTEN_AFFILIATE_ID")

def send_discord(message):
    if not WEBHOOK_URL:
        print("エラー: WEBHOOK_URLが設定されていません")
        return
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

def get_rakuten_info(keyword):
    """楽天APIで最安値とアフィリエイトURLを取得する"""
    if not RAKUTEN_APP_ID:
        return None, None
    
    # 検索ワードを少し綺麗にする（長すぎるとヒットしないため）
    clean_keyword = keyword.split(' / ')[0][:30] 

    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFF_ID,
        "keyword": clean_keyword,
        "sort": "+itemPrice", # 価格の安い順
        "hits": 1
    }
    
    try:
        res = requests.get(url, params=params).json()
        if "Items" in res and res["Items"]:
            item = res["Items"][0]["Item"]
            return item["itemPrice"], item["affiliateUrl"]
    except Exception as e:
        print(f"楽天APIエラー: {e}")
    return None, None

def main():
    print("--- LIPSから『最新トレンド』を分析中 ---")
    # LIPSの「新作」や「トレンド」が並ぶページを狙います
    url = "https://lipscosme.com/product_categories/1"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    
    found_count = 0
    # 商品カードを抽出
    items = soup.find_all("div", class_="style_productCard__N_7_L")
    
    for item in items:
        title_tag = item.find("div", class_="style_productName__m6m_e")
        if not title_tag: continue
        
        title = title_tag.get_text().strip()
        
        # 「限定」または「新作」が含まれる場合のみ処理（無駄を省くコスパ戦略）
        if "限定" in title or "新作" in title:
            found_count += 1
            print(f"ターゲット発見: {title}")
            
            # 楽天で最安値を検索
            price, aff_url = get_rakuten_info(title)
            
            if price:
                # 【稼げる通知】楽天に商品があった場合
                msg = f"✨ **【新作/限定コスメ速報】** ✨\n"
                msg += f"**{title}**\n\n"
                msg += f"💰 **楽天最安値: {price}円**\n"
                msg += f"🔗 [楽天で詳細・価格をチェック]({aff_url})\n"
                msg += "※PR 売り切れる前に確保推奨！"
            else:
                # 【通常通知】楽天にまだない場合
                msg = f"✨ **【新作コスメ発見】** ✨\n"
                msg += f"**{title}**\n\n"
                msg += "※楽天ではまだ取り扱いがないようです。店頭でチェック！"
            
            send_discord(msg)

    if found_count == 0:
        send_discord("🔍 本日は『バズりそうな新作』は見当たりませんでした。また明日22時にチェックします！")

if __name__ == "__main__":
    main()