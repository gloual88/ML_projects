import numpy as np
import pandas as pd

from .node import Node

class DecisionTree:
    """
    Decision tree classifier.

    Parameters
    ----------
    feature_select : str
      The method for selecting features: ['all', 'sqrt']. Latter
      is used when training a tree in a random forest.
    """
    def __init__(
        self,
        df: pd.DataFrame,
        target_col: str,
        feature_select: float = 1.0,
        max_depth: int = 4
    ) -> None:
        self.root = Node(df, target_col)
        self.features = list(df)
        self.features.remove(target_col)
        self.feature_select = feature_select
        self.max_depth = max_depth

    def classify(self, feature_df: pd.DataFrame) -> list[int]:
        """
        Given a dataframe where each row is a feature vector, traverses
        the tree to generate a predicted label.
        """
        return [self._classify(self.root, f) for i, f in feature_df.iterrows()]

    def _classify(self, node: Node, features: pd.Series) -> int:
        """
        Given a vector of features, traverse the node's children until
        a leaf is reached, then return the most frequent class in the node.
        If there are an equal number of positive and negative labels,
        predicts the negative class.
        """
        # Child node
        if node.feature is None or node.threshold is None:
            return int(node.pk > 0.5)

        if features[node.feature] < node.threshold:
            return self._classify(node.left, features)
        return self._classify(node.right, features)

    def build_tree(
        self,
        verbose: bool = False
    ) -> None:
        """
        Builds tree using depth-first traversal. If verbose, prints
        the node depths as the tree is being built.
        """
        stack = [(self.root, 0)]

        while stack:
            current_node, depth = stack.pop()

            if depth <= self.max_depth:
                left, right = self._process_node(current_node)

                if left and right:
                    current_node.left = left
                    current_node.right = right
                    stack.append((right, depth+1))
                    stack.append((left, depth+1))

                if verbose:
                    print(depth)
                    print(current_node.feature)
                    print(current_node.threshold)
                    print()

        return self

    def _process_node(
        self,
        node: Node
    ) -> tuple[Node|None, Node|None]:
        """
        Iterates through features, identifies split that minimizes
        Gini impurity in child nodes, and identifies feature whose
        split minimizes Gini impurity the most. Then returns child
        nodes split on that feature.
        """
        # Randomly select features. No randomness if
        # self.feature_select = 1.0 (default).
        features = list(
            np.random.choice(
                self.features,
                int(self.feature_select*len(self.features)),
                replace=False
            )
        )

        # Get Gini impurity for best split for each column
        d = {}
        for col in features:
            feature_info = node.split_on_feature(col)
            if feature_info[0] is not None:
                d[col] = feature_info

        # Select best column to split on
        min_gini = np.inf
        best_feature = None
        for col, tup in d.items():
            if tup[0] < min_gini:
                min_gini = tup[0]
                best_feature = col

        # Only update if the best split reduces Gini impurity
        if min_gini < node.gini:
            # Update node
            node.feature = best_feature
            node.threshold = d[col][1]
            return d[col][2:]

        return None, None
