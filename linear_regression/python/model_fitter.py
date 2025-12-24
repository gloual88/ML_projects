import logging
import numpy as np
from typing import Optional, Tuple


class ModelFitter:
    """
    | Fit a linear regression model to inputted X and y data. Contains methods for fitting
    | via the normal equation or by gradient descent
    """

    def normal_equation(self,
                        X: np.ndarray,
                        y: np.ndarray) -> np.ndarray:
        """
        | Solve for the vector of coefficients using the normal equation
        |  (X^T X)^-1 X^T y
        """
        self._check_matrix_vector_shapes(X, y, axis=0)

        X = self._add_intercept(X)
        return np.linalg.pinv(X.T.dot(X)).dot(X.T).dot(y)

    def _check_matrix_vector_shapes(self,
                                    X: np.ndarray,
                                    y: np.ndarray,
                                    axis: int) -> None:
        """
        | Checks whether number of rows or columns in X matches length of y
        | - Columns : normal equation
        | - Rows : predictions with theta vector
        """
        if X.shape[axis] != len(y):
            raise ValueError(f"Length of axis {axis} in X ({X.shape[axis]}) does not match length " +
                             f"of y ({len(y)})")

    def _add_intercept(self,
                       X: np.ndarray) -> np.ndarray:
        """
        | Checks whether first column of inputted data is the intercept. If not,
        | adds a column of intercepts to the beginning of the array
        |
        | ----------------------------------------------------------------------
        | Parameters
        | ----------
        |  X : np.ndarray
        |    Array of predictors
        |
        |
        | Returns
        | -------
        |  np.ndarray
        |    Original array if first column is all 1, else original array plus
        |    column with intercept
        """
        if all(X[:, 0] == 1):
            return X
        else:
            return np.c_[np.ones((X.shape[0], 1)), X]

    def predict(self,
                X: np.ndarray,
                theta: np.ndarray):
        """
        | Generate predictions based off of predictors (X) and linear regression
        | coefficients (theta)
        |
        | ----------------------------------------------------------------------
        | Parameters
        | ----------
        |  X : np.ndarray
        |    Matrix of predictors. Must include intercept
        |
        |  theta : np.ndarray
        |    Vector of coefficients
        """
        self._check_matrix_vector_shapes(X, theta, axis=1)
        return X.dot(theta)

    def gradient_descent(self,
                         X: np.ndarray,
                         y: np.ndarray,
                         alpha: Optional[float] = None,
                         max_iter: int = 10000,
                         min_diff_mse: float = 1e-5,
                         scale: bool = True) -> Tuple[np.ndarray, list]:
        """
        | Find linear regression coefficients via gradient descent. Descent occurs
        | for n_iter or until the improvement in MSE falls below stop_thresh.
        |
        | -------------------------------------------------------------------------
        | Parameters
        | ----------
        |  X : np.ndarray
        |    Predictors
        |
        |  y : np.ndarray
        |    Target
        |
        |  alpha : float
        |    The learning rate
        |
        |  max_iter : int
        |    The max number of iterations to run gradient descent, if stop_thresh isn't
        |    reached first
        |
        |  min_diff_mse : float
        |    The improvement in MSE between iterations below which gradient descent stops
        |
        |  scale : bool
        |    Whether to scale the predictors. If True, the value of each feature is subtracted
        |    by the feature mean, then divided by the feature standard deviation
        |
        |
        | Returns
        | -------
        |  np.ndarray
        |    The best fit for linear regression coefficients
        """
        X = self._add_intercept(X)

        # Initialize coefficients at zero
        theta = np.zeros((X.shape[1], 1))

        if alpha is None:
            alpha = self._set_alpha(len(y))

        if scale:
            X = self.scale(X)

        mse = []

        # Perform descent
        for i in range(max_iter):
            preds = self.predict(X, theta)
            theta = self._update_theta(theta, preds, y, X, alpha)
            mse.append(self.get_mse(preds, y))

            # Stop if change in MSE below threshold
            if i > 1 and (mse[i-1] - mse[i]) < min_diff_mse:
                break

            # If MSE is increasing, stop
            if mse[i] > mse[i-1]:
                logging.error("MSE is increasing; a smaller alpha should be used.")
                return theta, mse

        return theta, mse

    def _set_alpha(self,
                   m: int) -> float:
        """
        | Set alpha based on the number of samples.
        |
        | Examples:
        |   10 -> 1e-3
        |   100 -> 1e-5
        |   1000 -> 1e-7
        |
        | ----------------------------------------------------------
        | Parameters
        | ----------
        |  m : int
        |    Number of samples in data
        |
        |
        | Returns
        | -------
        |  float
        """
        return 10 ** -(round(np.log10(m)) * 2 + 1)

    def _update_theta(self,
                      theta: np.ndarray,
                      preds: np.ndarray,
                      y: np.ndarray,
                      X: np.ndarray,
                      alpha: float) -> np.ndarray:
        """
        | Update theta via gradient descent. Derivative of squared errors is
        | multiplied by the learning rate and added to vector of coefficients
        |
        | -------------------------------------------------------------------
        | Parameters
        | ----------
        |  theta : np.ndarray
        |    Vector of coefficients
        |
        |  preds : np.ndarray
        |    Vector of predictions (h(x), or y-hat)
        |
        |  y : np.ndarray
        |    Vector of target variable
        |
        |  X : np.ndarray
        |    Matrix of features
        |
        |  alpha : float
        |    Learning rate
        |
        |
        | Returns
        | -------
        |  np.ndarray
        |    Updated vector of coefficients
        """
        return theta - (1/len(y)) * alpha * (X.T.dot(preds - y))

    def get_mse(self,
                preds: np.ndarray,
                actuals: np.ndarray) -> float:
        """
        | Calculate the mean squared error
        |
        | ------------------------------------
        | Parameters
        | ----------
        |  preds : np.ndarray
        |    Predictions
        |
        |  actuals : np.ndarray
        |    Actual values
        |
        |
        | Returns
        | -------
        |  float
        |    Average squared error
        """
        return np.mean((preds - actuals) ** 2)

    # TODO: fix issue with Nans
    def scale(self,
              X: np.ndarray) -> np.ndarray:
        """
        | For each column of X, subtract the mean and divide by the standard deviation
        | of the column
        |
        | ----------------------------------------------------------------------------
        | Parameters
        | ----------
        |  X : np.ndarray
        |    Matrix of features
        |
        |
        | Returns
        | -------
        |  np.ndarray
        |    Original matrix with each column scaled by mean and standard deviation
        """
        feat_means = np.apply_along_axis(np.mean, 0, X)
        feat_stds = np.apply_along_axis(np.std, 0, X)

        return (X - feat_means) / feat_stds
