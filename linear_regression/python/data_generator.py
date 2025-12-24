import numpy as np
import pandas as pd
from typing import Union, Tuple

# Set global variables
Y_NOISE = 0.5


class DataGenerator:
    """
    | Methods for generating sample data
    """

    def __init__(self):
        self.y_noise = Y_NOISE

    def generate_data(self,
                      n_obs: int,
                      n_feat: int,
                      noise: Union[int, float, np.ndarray, list, pd.Series]) -> Tuple[np.ndarray, np.ndarray]:
        """
        | Generate data for predictors (X) and target (y). In X, each row represents an observation
        | and each column a feature. Features have positive trends with adjustable noise. y is a
        | vector with increasing values with a small amount of noise.
        |
        | -------------------------------------------------------------------------------
        | Parameters
        | ----------
        |  n_obs : int
        |    Number of observations
        |
        |  n_feat : int
        |    Number of features
        |
        |  noise : int, float, np.ndarray, list, pd.Series
        |    The noise to add to the linear relationship. Higher values correspond to
        |    more noise. If int or float, same amount of noise is applied to all features.
        |    If np.ndarray, list, or pd.Series, amount of noise may vary for each feature
        |
        |
        | Returns
        | -------
        |  np.ndarray, np.ndarray
        |    First array is an n_obs x n_feat matrix, and second is a vector of length n_obs
        """
        self._generate_samples_inputs_valid(n_obs, n_feat, noise)

        X = np.full([n_obs, n_feat], np.nan)

        if isinstance(noise, (int, float)):
            X = np.apply_along_axis(lambda f: self._create_positive_trend(n_obs, noise), 0, X)
        else:
            for i in range(n_feat):
                X[:, i] = self._create_positive_trend(n_obs, noise[i])

        y = np.array([self._create_positive_trend(n_obs, self.y_noise)]).T

        return X, y

    def _generate_samples_inputs_valid(self, n_obs, n_feat, noise) -> None:
        """
        | Confirm inputs to generate_samples are valid. Performs following checks:
        |   * n_obs and n_feat are int or np.int64
        |   * noise is either int, float, np.ndarray, list, or pd.Series
        |   * if noise is an array, it matches the number of features (n_feat)
        """
        for arg_tup in [('n_obs', n_obs), ('n_feat', n_feat)]:
            if not isinstance(arg_tup[1], (int, np.int64)):
                raise ValueError(f"{arg_tup[0]} is type {type(arg_tup[1])} but must be int")

        if not isinstance(noise, (int, float, np.ndarray, list, pd.Series)):
            raise ValueError(f"noise is type {type(noise)} but must be int, float, np.ndarray, " +
                             "list, or pd.Series")

        if isinstance(noise, (np.ndarray, list, pd.Series)) and len(noise) != n_feat:
            raise ValueError(f"Length of noise array ({len(noise)}) must match number of features " +
                             f"({n_feat})")

    def _create_positive_trend(self,
                               n_obs: int,
                               noise: Union[int, float]) -> np.ndarray:
        """
        | Generate data with a positive linear relationship, plus Gaussian noise
        |
        | -----------------------------------------------------------------------
        | Parameters
        | ----------
        |  n_obs : int
        |    Number of observations
        |
        |  noise : int, float
        |    Standard deviation on Gaussian noise
        |
        |
        | Returns
        | -------
        |  np.ndarray
        |    Values with
        """
        return range(n_obs) + np.random.normal(0, noise, n_obs)
