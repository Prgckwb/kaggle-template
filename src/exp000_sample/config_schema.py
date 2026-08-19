"""config.yaml のスキーマ定義（Hydra Structured Config）。

dataclass を ConfigStore に登録し、config.yaml の defaults で
`- base_schema` として読み込むことで、yaml や CLI オーバーライドの
タイポ・型違いを実行時に即エラーにする（例: `training.lrr=1e-3` は
起動時に ConfigKeyError になる）。

実験は互いに独立しているため、スキーマは各実験ディレクトリに置く。
config.yaml にキーを追加したら、このスキーマにも同じキーを追加すること。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hydra.core.config_store import ConfigStore


@dataclass
class DebugConfig:
    epochs: int = 1
    samples: int = 100
    limit_train_batches: int = 2
    limit_val_batches: int = 2
    n_folds: int = 1


@dataclass
class NoiseConfig:
    """判定の分解能（docs/competition-profile.yaml の metric.noise と揃える）。

    seed_spread が None の間は「棄却」「dead-end」を宣言してはいけない。
    """

    seed_spread: float | None = None
    fold0_resolution: float | None = None
    proxy_resolution: float | None = None


@dataclass
class MetricConfig:
    name: str = "score"
    mode: str = "max"  # "max" | "min"
    noise: NoiseConfig = field(default_factory=NoiseConfig)


@dataclass
class DataConfig:
    input_dir: str = "input"
    train_path: str = "input/train.csv"
    test_path: str = "input/test.csv"
    sample_submission_path: str = "input/sample_submission.csv"
    n_folds: int = 5
    # データの世代。wandb の tags に入れてクロスフィルタに使う（docs/wandb-spec.md）。
    # ⚠ 異なるバージョン間で CV スコアを比較しない（docs/experiment-methodology.md「判定の資格」）
    fold_version: str | None = None
    data_version: str | None = None
    label_version: str | None = None


@dataclass
class ModelConfig:
    name: str = "baseline"


@dataclass
class TrainingConfig:
    epochs: int = 10
    batch_size: int = 32
    lr: float = 1e-3


@dataclass
class WandbConfig:
    project: str = "kaggle-competition"
    entity: str | None = None
    mode: str = "online"  # online | offline | disabled


@dataclass
class LineageConfig:
    """この run の系譜。親との差分を宣言する（docs/experiment-methodology.md「効果の帰属」）。

    parent: 親 run の名前。ベース config を直接継承する場合は "config"
    varied: 親から変えたキーのドット表記（例: ["training.lr"]）。
            src/utils/lineage.py が実際の差分と照合し、宣言漏れを検出する。
            要素が 2 つ以上ある run の Δ を 1 変数の名前で呼んではいけない。
    """

    parent: str = "config"
    varied: list[str] = field(default_factory=list)


@dataclass
class ExpConfig:
    exp_name: str = "exp000_sample"
    run_name: str = "run000-base"
    seed: int = 42
    run_mode: str = "fold0"  # debug | fold0 | full
    lineage: LineageConfig = field(default_factory=LineageConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)
    metric: MetricConfig = field(default_factory=MetricConfig)
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    output_dir: str = "output"
    logs_dir: str = "logs"
    wandb: WandbConfig = field(default_factory=WandbConfig)


def register_config_schema() -> None:
    """ConfigStore にスキーマを登録する（train.py / inference.py の冒頭で呼ぶ）。"""
    cs = ConfigStore.instance()
    cs.store(name="base_schema", node=ExpConfig)
