from functools import partial
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

from classes import DecisionTree, Node, RandomForest

# Set seed for reproducibility
np.random.seed(0)

# Data generation helpers. Only parameter to pass in is the mean.
npn = partial(np.random.normal, scale=1, size=1)
npc = partial(np.random.choice, a=[0,1], size=1)

# Use this function for a detailed look at decision tree formation
def gen_df(n: int) -> pd.DataFrame:
    labels = np.random.choice([0,1], n)
    return pd.DataFrame({
        'strong_continuous': [npn(3)[0] if x else npn(0)[0] for x in labels],
        'weak_continuous': [npn(1)[0] if x else npn(0)[0] for x in labels],
        'strong_categorical': [
            npc(p=[0.8, 0.2])[0] if x else npc(p=[0.5,0.5])[0]
            for x in labels
        ],
        'label': labels
    })

# Use this function for a random forest using many features
def gen_df_hd(n_rows: int, n_cols: int) -> pd.DataFrame:
    """
    Note: actual df has 2*n_cols, since we produce both
    a continuous and categorical feature for each col.
    """

    labels = np.random.choice([0,1], n_rows)
    d = {'label': labels}

    for i in range(n_cols):
        mean = np.random.uniform(0, 1, 1)[0]
        d[f"continuous_{i}"] = [
            npn(mean)[0] if x else npn(0)[0] for x in labels
        ]
        ratio = np.random.uniform(0.4, 0.6, 1)[0]
        d[f"categorical_{i}"] = [
            npc(p=[ratio, 1-ratio])[0] if x else npc(p=[0.5,0.5])[0]
            for x in labels
        ]

    return pd.DataFrame(d)

# Generate data
print("Generating train and test data")
train_df = gen_df_hd(400, 50)
test_df = gen_df_hd(100, 50)

# 1. Decision Tree
print("1. Fitting a decision tree")
decision_tree = DecisionTree(train_df, target_col='label')
decision_tree.build_tree()
tree_preds = decision_tree.classify(test_df)
tree_accuracy = round(accuracy_score(test_df['label'], tree_preds), 3)

# 2. Random Forest
print("2. Fitting a random forest")
forest = RandomForest(train_df, target_col='label', n_trees=50)
forest.train()
forest_preds = forest.classify(test_df)
forest_accuracy = round(accuracy_score(test_df['label'], forest_preds), 3)

# 3. Average tree in forest
print("3. Calculating average tree accuracy")
tree_accs = []
for i in range(forest.n_trees):
    forest_tree_preds = forest.forest[i].classify(test_df)
    tree_accs.append(accuracy_score(test_df['label'], forest_tree_preds))
forest_tree_accuracy = np.mean(tree_accs).round(3)

# 4. Scikit-learn
print("4. Fitting scikit-learn forest")
X_train = train_df.copy()
X_train = X_train.drop('label', axis=1)

X_test = test_df.copy()
X_test = X_test.drop('label', axis=1)

y_train = train_df['label']
y_test = test_df['label']

rf = RandomForestClassifier(n_estimators=50)
rf.fit(X_train, y_train)

sklearn_preds = rf.predict(X_test)
sklearn_acc = round(accuracy_score(y_test, sklearn_preds), 3)

# Display results
print("Accuracy")
print(f" * Single decision tree:   {tree_accuracy}")
print(f" * Avg random forest tree: {forest_tree_accuracy}")
print(f" * Full random forest:     {forest_accuracy}")
print(f" * Scikit-learn forest:    {sklearn_acc}")
