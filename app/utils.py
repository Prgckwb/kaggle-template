"""Dashboard utilities — re-export facade.

All implementations live in app/services/. This module provides backward
compatibility so that existing imports from ``app.utils`` continue to work.
"""

from app.services.data import (  # noqa: F401
    data_file_icon,
    get_csv_preview_and_stats,
    get_csv_statistics,
    get_file_info,
    list_directory_images,
    list_input_files,
    read_csv_preview,
)
from app.services.documents import (  # noqa: F401
    get_competition_overview,
    get_validation_strategy,
    list_discussion_docs,
    list_docs,
    list_knowledge_docs,
    read_markdown_file,
)
from app.services.experiments import (  # noqa: F401
    get_all_experiment_scores,
    get_experiment_detail,
    get_oof_analysis,
    list_checkpoints,
    list_experiment_files,
    list_experiments,
    list_notebooks,
    parse_experiments_table,
    parse_mermaid_tree,
    read_config_yaml,
)
from app.services.helpers import (  # noqa: F401
    PROJECT_ROOT,
    file_icon,
    human_filesize,
    is_htmx,
    safe_relative_path,
    timeago,
)
