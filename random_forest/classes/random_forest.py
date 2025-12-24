import pandas as pd

from .decision_tree import DecisionTree

class RandomForest:
    """
    Forest of decision trees.

    Parameters
    ----------
    df : pd.DataFrame
      The data to model
    target_col : str
      The column in df containing labels
    n_trees : int
      The number of trees to use for the forest
    max_depth : int
      The deepest we allow the forest trees to grow
    """
    def __init__(
        self,
        df: pd.DataFrame,
        target_col: str,
        n_trees: int = 100,
        feature_select: float = 0.5,
        max_depth: int = 4
    ) -> None:
        self.df = df
        self.target_col = target_col
        self.n_trees = n_trees
        self.feature_select = feature_select
        self.max_depth = max_depth
        self.forest = []

    def train(self) -> None:
        """
        Fit the forest to self.df
        """
        print("Bootstrapping data...")
        bootstrap_dfs = [self._bootstrap() for _ in range(self.n_trees)]
        self.forest = [
            DecisionTree(bdf, self.target_col, self.feature_select, self.max_depth)
            for bdf in bootstrap_dfs
        ]
        print("Building trees...")
        self.forest = [tree.build_tree() for tree in self.forest]
        print(f"Trained forest with {self.n_trees} trees.")
        return None

    def classify(self, feature_df: pd.DataFrame) -> int:
        """
        Classify inputted feature vectors. Each tree in the forest generates
        a predicted label and the most common label for each feature vector
        is returned.
        """
        if not self.forest:
            raise ValueError("RandomForest instance must first be trained.")
        preds = pd.DataFrame([tree.classify(feature_df) for tree in self.forest])

        # Return most common predicted label
        return list(preds.mode().iloc[0])

    def _bootstrap(self) -> pd.DataFrame:
        """
        Sample rows from self.df with replacement
        """
        return self.df.sample(len(self.df), replace=True)
