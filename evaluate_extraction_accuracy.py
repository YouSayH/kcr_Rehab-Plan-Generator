import sys
import logging
import json
from typing import Dict, Any, List

# プロジェクトのルートパスをシステムのパスに追加
sys.path.append('.')

# ログ設定: エラーのみ表示してすっきりさせる
logging.basicConfig(level=logging.ERROR) 

try:
    from app.services.llm.patient_info_parser import PatientInfoParser
except ImportError:
    print("エラー: app.services.llm.patient_info_parser が見つかりません。")
    print("このスクリプトはプロジェクトのルートディレクトリで実行してください。")
    sys.exit(1)

# ==========================================
# 1. テストデータと正解（Ground Truth）の定義
# ==========================================
# 検証したい項目だけを 'expected' に記述してください。
# ここに記述がないキーは検証から除外されます（部分一致評価）。

TEST_CASES = [
    # ---------------------------------------------------------
    # Case 1: 脳血管疾患（標準的・合併症多）
    # ---------------------------------------------------------
    {
        "id": "case_01_tanaka",
        "description": "田中 太郎様 (72) - 脳梗塞・右片麻痺・嚥下・リスク多",
        "text": """
# 患者プロフィール：田中 太郎 様 (72歳・男性)
## 詳細情報
* 診断名: 脳梗塞（左中大脳動脈領域）による右片麻痺
* 発症日: 2025年7月15日
* 持病（合併症）: 高血圧症、2型糖尿病、脂質異常症
* 麻痺・筋力: 右手足に重度の麻痺と筋力低下がある。
* 痛み: 右肩に痛みがあり、特に腕を上げようとすると痛みが強くなる。
* 嚥下: 飲み込みに軽度の問題があり、食事は刻み食、水分にはとろみが必要。
* 言語: 軽度の失語症があり、言葉が少し出にくいことがある。
* 高次脳機能: 注意力が散漫になりやすい傾向がある。
* ADL 食事: 軽度の介助があれば、自分で食べることができる。
* ADL 移動: 現在は主に車椅子で移動しており、介助が必要。
* 社会背景: 介護保険 要介護認定を申請中。
        """,
        "expected": {
            # --- 基本属性 ---
            "name": "田中 太郎",
            "age": 72,
            "gender": "男",
            "header_disease_name_txt": "脳梗塞", # 部分一致でOK
            
            # --- 機能障害 (True/False) ---
            "func_motor_paralysis_chk": True,      # 麻痺
            "func_pain_chk": True,                 # 痛み
            "func_swallowing_disorder_chk": True,  # 嚥下障害
            "func_speech_aphasia_chk": True,       # 失語症
            "func_higher_brain_attention_chk": True, # 注意障害
            
            # --- リスク因子 ---
            "func_risk_hypertension_chk": True,    # 高血圧
            "func_risk_diabetes_chk": True,        # 糖尿病
            "func_risk_dyslipidemia_chk": True,    # 脂質異常
            
            # --- テキスト内容検証 (部分一致) ---
            "func_pain_txt": "右肩",
            "func_swallowing_disorder_txt": "とろみ",

            # --- 社会背景 ---
            "social_care_level_status_slct": "applying", # 申請中
        }
    },

    # ---------------------------------------------------------
    # Case 2: 脳血管疾患（回復期・若年・高次脳・復職）
    # ---------------------------------------------------------
    {
        "id": "case_02_suzuki",
        "description": "鈴木 一郎様 (55) - 脳梗塞・左片麻痺・USN・復職希望",
        "text": """
# 患者プロフィール：鈴木 一郎 様 (55歳・男性)
## 概要
* 1か月前に脳梗塞を発症し、左半身に麻痺が残っている。
* 趣味はカメラ。リハビリの目標は、職場復帰と趣味の再開。
## 詳細情報
* 診断名: 脳梗塞（右中大脳動脈領域）による左片麻痺
* 筋緊張: 左手首や指の筋肉が硬くなりやすい（痙縮）。
* 感覚障害: 左半身の感覚が鈍い。
* 高次脳機能障害: 軽度の半側空間無視があり、左側への注意が向きにくい。
* ADL 移動: 室内はT字杖と短下肢装具を使用して、見守りの下で歩行可能。
* ADL 更衣: ボタンのかけ外しなど、細かい手の動作に介助が必要。
        """,
        "expected": {
            "name": "鈴木 一郎",
            "age": 55,
            
            # --- 機能障害 ---
            "func_motor_paralysis_chk": True,
            "func_motor_muscle_tone_abnormality_chk": True, # 痙縮・筋緊張異常
            "func_sensory_dysfunction_chk": True,           # 感覚障害
            "func_higher_brain_dysfunction_chk": True,      # 高次脳機能障害
            
            # --- テキスト内容検証 ---
            "func_higher_brain_agnosia_chk": True, # 半側空間無視(失認の一種)として判定されるか、もしくはdysfunction全体で拾うか
            
            # --- 目標 (Goal P) ---
            "goal_p_return_to_work_chk": True,     # 復職
            "goal_p_hobby_chk": True,              # 趣味
            "goal_p_hobby_txt": "カメラ",          # 趣味の内容
            
            # --- FIM/ADLレベル推論 ---
            # "見守り" -> 5点 (監視・準備)
            "adl_locomotion_walk_walkingAids_wc_fim_current_val": 5,
        }
    },

    # ---------------------------------------------------------
    # Case 3: 整形外科（膝OA・高齢女性・否定チェック）
    # ---------------------------------------------------------
    {
        "id": "case_03_sato",
        "description": "佐藤 和子様 (68) - 変形性膝関節症・肥満・手術回避",
        "text": """
# 患者プロフィール：佐藤 和子 様 (68歳・女性)
## 概要
* 長年、立ち仕事や歩行時の右膝の痛みに悩んでいる。
* 可能な限り手術はせず、痛みをコントロールしながら生活したい。
## 詳細情報
* 診断名: 変形性膝関節症（右膝、内側型）
* 背景: 肥満傾向あり
* 主な問題点:
    * 疼痛: 歩き始めや階段昇降で膝の内側に痛みが生じる。
    * 関節可動域制限: 膝が完全に伸びきらず（伸展-10°）、正座ができない。
    * 筋力低下: 大腿四頭筋の筋力が低下している。
* ADL: 15分以上歩くと痛みが増す。階段は手すりがないと不安。
        """,
        "expected": {
            "name": "佐藤 和子",
            "gender": "女",
            "header_disease_name_txt": "変形性膝関節症",
            
            # --- 機能障害 ---
            "func_pain_chk": True,                 # 疼痛
            "func_rom_limitation_chk": True,       # 可動域制限
            "func_muscle_weakness_chk": True,      # 筋力低下
            "func_risk_obesity_chk": True,         # 肥満
            
            # --- 【重要】否定（Negative）チェック ---
            # 脳血管疾患ではないので、麻痺や嚥下障害はFalseであるべき
            "func_motor_paralysis_chk": False,     
            "func_swallowing_disorder_chk": False, 
            "func_speech_aphasia_chk": False,
        }
    },

    # ---------------------------------------------------------
    # Case 4: 整形外科（五十肩・ADL制限具体性）
    # ---------------------------------------------------------
    {
        "id": "case_04_takahashi",
        "description": "高橋 美咲様 (52) - 肩関節周囲炎・夜間痛・結髪結帯不可",
        "text": """
# 患者プロフィール：高橋 美咲 様 (52歳・女性)
## 概要
* 3か月前から右肩に強い痛みが出現し、腕が上がらなくなった。
* 特に夜間に痛みが強く、寝返りで目が覚めてしまうことがある。
* 仕事は事務職。
## 詳細情報
* 診断名: 肩関節周囲炎（いわゆる五十肩）
* 主な問題点:
    * 疼痛: 腕を動かせる範囲の最終域で強い痛み。
    * 夜間痛: 痛い方の肩を下にして眠れない。
    * 関節可動域制限: 結髪・結帯動作が困難。
* ADL 更衣: 背中のファスナーを上げる動作が困難。
* ADL 整容: ドライヤーで髪を乾かす動作ができない。
        """,
        "expected": {
            "name": "高橋 美咲",
            "age": 52,
            
            # --- 機能障害 ---
            "func_pain_chk": True,           # 疼痛
            "func_pain_txt": "夜間",         # 「夜間」という単語が含まれているか
            "func_rom_limitation_chk": True, # 可動域制限
            
            # --- ADL詳細 ---
            # 整容動作が困難 -> FIMが満点(7)ではないことを期待
            # ※完全な点数予測は難しいが、テキストが含まれているか確認
            # "adl_equipment_and_assistance_details_txt": "ドライヤー", # こういうチェックもあり
            
            # --- 否定チェック ---
            "func_motor_paralysis_chk": False, # 麻痺なし
        }
    },

    # ---------------------------------------------------------
    # Case 5: スポーツ整形（FAI・若年・リスクなし）
    # ---------------------------------------------------------
    {
        "id": "case_05_nakamura",
        "description": "中村 健太様 (28) - 股関節インピンジメント・スポーツ復帰",
        "text": """
## 患者プロフィール：中村 健太 様 (28歳・男性)
## 概要
* 社会人サッカーチームに所属。
* 今後もサッカーを続けるため、根本的な原因を解決したい。
## 詳細情報
* 診断名: 大腿骨寛骨臼インピンジメント（FAI）
* 主な問題点:
    * 疼痛: 股関節を深く曲げると痛みが生じる。
    * 筋機能低下: 殿筋群の筋力低下が見られる。
* ADL: ダッシュやキック時に痛みが強く、全力プレー困難。
        """,
        "expected": {
            "name": "中村 健太",
            "age": 28,
            "header_disease_name_txt": "インピンジメント", # 部分一致
            
            # --- 機能障害 ---
            "func_pain_chk": True,             # 疼痛
            "func_muscle_weakness_chk": True,  # 筋力低下
            
            # --- 目標 ---
            "goal_p_hobby_chk": True,          # 趣味
            "goal_p_hobby_txt": "サッカー",    # 具体的種目
            
            # --- リスク否定チェック ---
            # 若年スポーツマンなので、高齢者特有のリスクはFalseであるべき
            "func_risk_hypertension_chk": False,
            "func_consciousness_disorder_chk": False,
            "func_risk_diabetes_chk": False,
        }
    }
]

# ==========================================
# 2. 評価ロジック
# ==========================================

def compare_values(key, expected, actual):
    """
    値の比較を行う。
    - 数値: 型変換して比較
    - 文字列: 部分一致（expected in actual）を許容
    - ブール値: 厳密比較
    - None: 厳密比較
    """
    if expected is None:
        return actual is None

    # NoneでないのにActualがNoneなら不一致
    if actual is None:
        return False

    # 数値の比較
    if isinstance(expected, (int, float)):
        try:
            return float(expected) == float(actual)
        except:
            return False

    # ブール値
    if isinstance(expected, bool):
        return bool(actual) is expected

    # 文字列
    if isinstance(expected, str):
        # 期待値が実際の値に含まれていればOK（柔軟な評価）
        return str(expected) in str(actual)

    return expected == actual

def evaluate_parser(use_hybrid=True):
    print(f"\n{'='*70}")
    print(f"   PatientInfoParser 精度評価 (Hybrid Mode: {use_hybrid})")
    print(f"{'='*70}\n")

    parser = PatientInfoParser(use_hybrid_mode=use_hybrid)
    
    total_checks = 0
    total_pass = 0
    results_summary = []

    for case in TEST_CASES:
        print(f"Running Case [{case['id']}] {case['description']} ...")
        
        try:
            # 解析実行
            actual_result = parser.parse_text(case["text"])
            
            case_checks = 0
            case_pass = 0
            mismatches = []

            # 期待値と比較
            for key, expected_val in case["expected"].items():
                actual_val = actual_result.get(key)
                
                is_match = compare_values(key, expected_val, actual_val)
                
                case_checks += 1
                if is_match:
                    case_pass += 1
                else:
                    mismatches.append({
                        "key": key,
                        "expected": expected_val,
                        "actual": actual_val
                    })

            # 結果保存
            score = (case_pass / case_checks * 100) if case_checks > 0 else 0
            print(f"  -> Score: {case_pass}/{case_checks} ({score:.1f}%)")
            
            results_summary.append({
                "id": case["id"],
                "score": score,
                "mismatches": mismatches
            })
            
            total_checks += case_checks
            total_pass += case_pass

        except Exception as e:
            print(f"  -> Error: {e}")
            import traceback
            traceback.print_exc()
            results_summary.append({
                "id": case["id"],
                "error": str(e)
            })
        print("-" * 50)

    # ==========================================
    # 3. レポート出力
    # ==========================================
    print(f"\n{'='*30} 最終評価レポート {'='*30}")
    if total_checks > 0:
        print(f"Total Accuracy: {total_pass}/{total_checks} ({(total_pass/total_checks*100):.1f}%)")
    else:
        print("No checks run.")
    
    for res in results_summary:
        if "error" in res:
            print(f"\n[FAIL] {res['id']}: Runtime Error - {res['error']}")
            continue

        if res["mismatches"]:
            print(f"\n[WARN] {res['id']} (Score: {res['score']:.1f}%) - Mismatches:")
            for m in res["mismatches"]:
                print(f"  - Key: {m['key']}")
                print(f"    Expected: {m['expected']}")
                print(f"    Actual  : {m['actual']}")
        else:
            print(f"\n[PASS] {res['id']} - All Clear")

if __name__ == "__main__":
    # 引数でモード切り替えなどができるようにしても良い
    evaluate_parser(use_hybrid=True)