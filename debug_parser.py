# debug_parser.py
import sys
import logging
import pprint
import json

# アプリケーションのパスを通す
sys.path.append('.')

# ログ設定
logging.basicConfig(level=logging.INFO)

from app.services.llm.patient_info_parser import PatientInfoParser

SAMPLE_TEXT = """
# 患者プロフィール：田中 太郎 様 (72歳・男性)

## 概要
* 脳梗塞を発症し、右半身に麻痺が残っている。
* リハビリテーションにより、身の回りの動作の再獲得と、安全な自宅への退院を目指している。
* 退院後は、同居している妻（68歳）が主な介護者となる予定。

---

# 詳細情報

## 病状と経過
* 診断名: 脳梗塞（左中大脳動脈領域）による右片麻痺
* 発症日: 2025年7月15日
* リハビリ開始日: 2025年7月18日
* 持病（合併症）: 高血圧症、2型糖尿病、脂質異常症

## 主な問題点（心身機能）
* 麻痺・筋力: 右手足に重度の麻痺と筋力低下がある。
* 痛み: 右肩に痛みがあり、特に腕を上げようとすると痛みが強くなる。
* 関節の動き: 痛みの影響で、右肩が上がりにくくなっている（屈曲100度まで）。
* 嚥下（飲み込み）: 飲み込みに軽度の問題があり、食事は刻み食、水分にはとろみが必要。
* 言語: 軽度の失語症があり、言葉が少し出にくいことがある。
* 高次脳機能: 注意力が散漫になりやすい傾向がある。

## 日常生活動作（ADL）の状況
* 食事: 軽度の介助があれば、自分で食べることができる。
* 身の回りの動作: 着替えや洗面、トイレ動作は一部手伝いが必要。
* 乗り移り: ベッドと車椅子の間の乗り移りは、軽度の介助で可能。
* 移動: 現在は主に車椅子で移動しており、介助が必要。

## 社会状況と退院後の計画
* 退院先: 自宅
* 介護保険: 現在、要介護認定を申請中。
* 計画中のサービス:
    * 通所リハビリ（デイケア）
    * 訪問介護（ホームヘルプ）
* 住宅改修: 自宅の廊下・トイレへの手すり設置や、段差の解消を検討中。
* 福祉用具: 介護ベッドやポータブルトイレの導入を検討中。

## 本人の趣味
* 庭いじり、盆栽
"""

def main():
    print("=== Debugging PatientInfoParser (Full Flow) ===")
    
    # use_hybrid_mode=True で実行
    parser = PatientInfoParser(use_hybrid_mode=True)
    
    print("\n[Client Check]")
    print(f"Client Type: {parser.client_type}")
    if parser.client_type == 'ollama':
        print(f"Extraction Model: {getattr(parser.llm_client, 'extraction_model_name', 'Not Found')}")

    print("\n=== Running Parse Text ===")
    try:
        # 実行
        result = parser.parse_text(SAMPLE_TEXT)
        
        print("\n=== Extraction Result (Selected FIM Items) ===")
        # FIM関連項目のみ抜粋して表示
        fim_keys = [k for k in result.keys() if 'fim' in k]
        fim_result = {k: result[k] for k in fim_keys}
        pprint.pprint(fim_result)

        print("\n=== Full Result Summary (Keys) ===")
        print(list(result.keys()))
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()