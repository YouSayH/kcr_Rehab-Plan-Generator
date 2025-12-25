# モデルを一括インポートして公開
# modelsフォルダー自体を一つのファイルみたく、次のようにimportできる。
# database.pyのimport部分 → from app.models import Base, LikedItemDetail, Patient, RegenerationHistory, RehabilitationPlan, Staff, SuggestionLike

from .base import Base  # noqa: F401
from .patient import Patient  # noqa: F401
from .plan import LikedItemDetail, RegenerationHistory, RehabilitationPlan, SuggestionLike  # noqa: F401
from .staff import Staff, staff_patients_association  # noqa: F401
