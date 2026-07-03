"""tools/ の CLI ヘルパー関数のテスト（Kaggle API には接続しない）。"""

from tools.check_submission import is_finished
from tools.upload_checkpoints import to_kebab


def test_is_finished_detects_complete_and_error():
    assert is_finished("complete")
    assert is_finished("SubmissionStatus.COMPLETE")
    assert is_finished("error")
    assert not is_finished("pending")
    assert not is_finished("SubmissionStatus.PENDING")


def test_to_kebab_converts_underscores_and_case():
    assert to_kebab("exp001_baseline") == "exp001-baseline"
    assert to_kebab("Spaceship_Titanic exp001") == "spaceship-titanic-exp001"
    assert to_kebab("-already-kebab-") == "already-kebab"
