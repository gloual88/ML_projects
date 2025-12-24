import numpy as np
import pandas as pd
from typing_extensions import Self

class Node:
    """
    Node in a decision tree.

    Parameters
    ----------
    df : pd.DataFrame
      The dataframe (or subset) this node holds. Used for training.
      All columns except target_col are assumed to be features.
    target_col : str
      The column in the dataframe with labels. Must be 0s and 1s, with
      1s being the positive class.
    pk : float
      Proportion of node's df that contain the positive class.
    gini : float
      The node's Gini impurity.
    left : Node
      The left child of the node. None if no child.
    right : Node
      The right child of the node. None if no child.
    feature : str
      The column in the df whose splitting led to the largest reduction
      in weighted Gini impurity in the child nodes.
    threshold : float | int
      The value of the feature column to split the df.
    """
    def __init__(
        self,
        df: pd.DataFrame,
        target_col: str
    ) -> None:
        # For training
        self.df = self._check_df(df, target_col)
        self.target_col = target_col
        self.pk = self._set_pk()
        self.gini = self._set_gini()

        # For training/inference
        self.left = None
        self.right = None

        # For inference
        self.feature = None
        self.threshold = None

    def _check_df(
        self,
        df: pd.DataFrame,
        target_col: str
    ) -> pd.DataFrame:
        assert len(list(df)) > 1, \
            "df must have features"
        assert not set(df[target_col]).difference({0,1}), \
            "target column cannot have values besides {0,1}"
        return df

    def _set_pk(self) -> float:
        """
        Sets pk, the proportion of samples that are of the positive class.
        Assumes samples is a list of ints, where 1 is the positive class
        and 0 is the negative class.
        """
        return np.mean(self.df[self.target_col].values)

    def _set_gini(self) -> float:
        """
        Sets the Gini impurity.
        """
        return 1 - self.pk**2 - (1 - self.pk)**2

    def split_on_feature(
        self,
        feature: str
    ) -> tuple[float, int|float, Self, Self]:
        """
        Iterate through values of a feature and identify split that minimizes
        weighted Gini impurity in child nodes. Returns tuple of weighted Gini
        impurity, feature threshold, and left and right child nodes.
        """
        values = []

        for thresh in self.df[feature].unique():
            values.append(self._process_split(feature, thresh))

        values = [v for v in values if v[1] is not None]
        if values:
            return min(values, key=lambda x: x[0])
        return None, None, None, None

    def _process_split(
        self,
        feature: str,
        threshold: int|float
    ) -> tuple[float, int|float, Self|None, Self|None]:
        """
        Splits df on the feature threshold. Returns weighted Gini
        impurity, inputted threshold, and child nodes. If split
        results in empty subset, returns Gini impurity and None's.
        """
        df_lower = self.df[self.df[feature] <= threshold]
        df_upper = self.df[self.df[feature] > threshold]

        # If threshold doesn't split the data at all, end early
        if len(df_lower) == 0 or len(df_upper) == 0:
            return self.gini, None, None, None

        node_lower = Node(df_lower, self.target_col)
        node_upper = Node(df_upper, self.target_col)

        prop_lower = len(df_lower) / len(self.df)
        prop_upper = len(df_upper) / len(self.df)

        weighted_gini = node_lower.gini * prop_lower + node_upper.gini * prop_upper

        return weighted_gini, threshold, node_lower, node_upper
