"""Data loading and preprocessing."""

from pathlib import Path


def load_data(train_path: str, test_path: str):
    """Load train and test data.

    Args:
        train_path: Path to training data
        test_path: Path to test data

    Returns:
        Tuple of (train_df, test_df)
    """
    # TODO: Implement data loading
    # Example:
    # import pandas as pd
    # train_df = pd.read_csv(train_path)
    # test_df = pd.read_csv(test_path)
    # return train_df, test_df
    raise NotImplementedError


def preprocess(df):
    """Preprocess dataframe.

    Args:
        df: Input dataframe

    Returns:
        Preprocessed dataframe
    """
    # TODO: Implement preprocessing
    raise NotImplementedError


def create_folds(df, n_folds: int = 5, seed: int = 42):
    """Create cross-validation folds.

    Args:
        df: Input dataframe
        n_folds: Number of folds
        seed: Random seed

    Returns:
        Dataframe with fold column
    """
    # TODO: Implement fold creation
    # Example:
    # from sklearn.model_selection import KFold
    # kf = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
    # df["fold"] = -1
    # for fold, (_, val_idx) in enumerate(kf.split(df)):
    #     df.loc[val_idx, "fold"] = fold
    # return df
    raise NotImplementedError
