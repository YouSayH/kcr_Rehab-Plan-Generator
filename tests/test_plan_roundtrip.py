"""計画書の保存→取得のラウンドトリップ検証。

このテストは、リハビリ計画書の臨床項目が「保存して読み直しても失われない」ことを
型ごとに保証するためのものです。

背景: rehabilitation_plans を個別カラムから plan_data(JSON) へ移す作業が中断され、
モデル・CRUD・schema.sql が食い違ったまま作業ツリーに残っていたことがありました。
当時のテストは「行が1件できたか」「作成者IDが合っているか」しか見ていなかったため、
全臨床項目が保存されなくなっていても検知できませんでした。

したがってここでは件数ではなく、_chk / _val / _txt / _slct / 日付の各型について
「入れた値がそのまま戻ること」を検証します。保存経路の実装方式が将来変わっても
（個別カラムでもJSONでも）、この契約が守られていれば通ります。
"""

from datetime import date

import pytest

from app.crud import plan as plan_crud
from app.models import Patient

# フォームから送られてくる想定の値。実際のHTMLフォームと同じく全て文字列で渡す。
FORM_DATA = {
    # テキスト
    "header_disease_name_txt": "左変形性股関節症による人工股関節全置換術後",
    "main_comorbidities_txt": "骨粗鬆症、高血圧症",
    "main_risks_txt": "脱臼リスクに注意。過度な股関節屈曲を避ける。",
    # 日付
    "header_evaluation_date": "2026-07-23",
    "header_onset_date": "2026-06-10",
    # チェックボックス (HTMLは "on" を送る)
    "header_therapy_pt_chk": "on",
    "header_therapy_ot_chk": "on",
    "func_pain_chk": "on",
    # 数値 (FIM)
    "adl_eating_fim_start_val": "5",
    "adl_eating_fim_current_val": "7",
    "adl_transfer_bed_chair_wc_fim_start_val": "3",
    # 小数 (DECIMAL)
    "nutrition_height_val": "168.5",
    "nutrition_weight_val": "63.2",
    # 選択
    "nutrition_status_assessment_slct": "no_problem",
    # 目標
    "goals_1_month_txt": "屋内歩行が独歩で自立する",
    "goals_at_discharge_txt": "屋外歩行がT字杖で自立する",
}


@pytest.fixture
def patient(db_session):
    """計画書の保存先となる患者を1件用意する。"""
    p = Patient(name="ラウンドトリップ 太郎", date_of_birth=date(1957, 11, 5), gender="男")
    db_session.add(p)
    db_session.commit()
    return p


def test_save_and_get_plan_preserves_all_values(patient, db_session):
    """保存した臨床項目が、取得時に同じ値で戻ってくること。"""
    plan_id = plan_crud.save_new_plan(
        patient_id=patient.patient_id, staff_id=None, form_data=FORM_DATA
    )
    assert plan_id is not None, "save_new_plan が plan_id を返していません"

    result = plan_crud.get_plan_by_id(plan_id)
    assert result is not None, "保存した計画書を get_plan_by_id で取得できません"

    # --- テキスト ---
    for key in ("header_disease_name_txt", "main_comorbidities_txt", "main_risks_txt",
                "goals_1_month_txt", "goals_at_discharge_txt"):
        assert result[key] == FORM_DATA[key], f"{key} が保存されていません"

    # --- 日付: 文字列で渡しても date として戻ること ---
    assert result["header_evaluation_date"] == date(2026, 7, 23)
    assert result["header_onset_date"] == date(2026, 6, 10)

    # --- チェックボックス: "on" が True になること ---
    assert result["header_therapy_pt_chk"] is True
    assert result["header_therapy_ot_chk"] is True
    assert result["func_pain_chk"] is True

    # --- 数値 ---
    assert result["adl_eating_fim_start_val"] == 5
    assert result["adl_eating_fim_current_val"] == 7
    assert result["adl_transfer_bed_chair_wc_fim_start_val"] == 3

    # --- 小数 ---
    assert float(result["nutrition_height_val"]) == 168.5
    assert float(result["nutrition_weight_val"]) == 63.2

    # --- 選択 ---
    assert result["nutrition_status_assessment_slct"] == "no_problem"


def test_unchecked_checkboxes_are_false_not_missing(patient):
    """未チェックの項目が False として保存されること。

    ブラウザは未チェックの checkbox を送信しないため、キー自体がフォームに現れません。
    ここが None や欠落になると、Excel出力で「☐」も「☑」も付かない空欄になり、
    「評価した結果 該当なし」なのか「未評価」なのか区別できない計画書が出力されます。
    """
    plan_id = plan_crud.save_new_plan(
        patient_id=patient.patient_id, staff_id=None, form_data=FORM_DATA
    )
    result = plan_crud.get_plan_by_id(plan_id)

    # FORM_DATA に含めていないチェックボックス
    assert result["header_therapy_st_chk"] is False
    assert result["func_swallowing_disorder_chk"] is False


def test_patient_info_is_merged_into_plan(patient):
    """取得結果に患者情報がマージされていること。"""
    plan_id = plan_crud.save_new_plan(
        patient_id=patient.patient_id, staff_id=None, form_data=FORM_DATA
    )
    result = plan_crud.get_plan_by_id(plan_id)

    assert result["name"] == "ラウンドトリップ 太郎"
    assert result["patient_id"] == patient.patient_id
    assert result["age"] is not None, "@property の age がマージされていません"


def test_plan_identity_fields_survive(patient):
    """plan_id / created_at が取得結果に残っていること。

    患者情報と計画書をマージする際、患者側の値で上書きされて
    計画作成日が患者登録日にすり替わる事故が起きやすい箇所です。
    """
    plan_id = plan_crud.save_new_plan(
        patient_id=patient.patient_id, staff_id=None, form_data=FORM_DATA
    )
    result = plan_crud.get_plan_by_id(plan_id)

    assert result["plan_id"] == plan_id
    assert result["created_at"] is not None


def test_get_plan_by_id_returns_none_for_missing_plan(app):
    """存在しない plan_id では None を返すこと。

    app フィクスチャに依存させることでテスト用DBへの差し替えを適用する。
    依存させないと実DBへ接続しにいってしまう。
    """
    assert plan_crud.get_plan_by_id(999999) is None
