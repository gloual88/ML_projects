######################################################################################################
# Multivariate linear regression via gradient descent
# Author: Matt Sosna
#
# - Purpose:
#     o Demonstrate iterative approach to calculating linear regression coefficients
#     o Quantify superiority of analytical solution for higher-dimension regressions
# - Requirements: 'scatterplot3d' package
#
######################################################################################################
# Prerequisite: install 'scatterplot3d' package if necessary
try(library('scatterplot3d'),
    outFile = install.packages('scatterplot3d'))

#####################################################################################################
# Functions

# 1. Generate structured data
# - Makes it much easier to test ideas on data with different dimensions
# - Creates X and y data with a positive relationship. Strength of relationship can
#   be modified with 'noise' parameter

gen_data <- function(n_obs, n_features, noise = 3){

   # Generate data
   X <- matrix(1:n_obs + rnorm(n_obs*n_features, sd = noise), ncol = n_features)
   y <- 1:n_obs + rnorm(n_obs, sd = noise)

   # Label X
   colnames(X) <- paste0("feature_", 1:n_features)

   return(list("X" = X, "y" = y))
}


#------------------------------------------------------------------------------
# 2. Perform analytical linear regression
# - Perform matrix multiplication to get linear regression coefficients
# - Generate predictions and compare to actual values to get mean squared error
# - Requires X to be more than 1 dimension

analytical_reg <- function(X, y){

   # Prepare X
   X <- as.matrix(X)

   # If X is 1-dimensional, stop
   if(ncol(X) == 1){
      stop("Error: ncol(X) must be greater than 1. Use 'lm' instead.\n")
   }

   # Create column of 1's
   X <- cbind(1, X)

   # Perform matrix multiplications to get coefficients
   lm_coeffs <- solve(t(X) %*% X) %*% t(X) %*% y

   rownames(lm_coeffs) <- c("intercept", paste0("beta_", 1:(nrow(lm_coeffs)-1)))

   # Generate predictions to get MSE
   lm_preds <- lm_coeffs[1] + rowSums(sweep(X[, -1], MARGIN = 2, lm_coeffs[2:length(lm_coeffs)], "*"))
   lm_MSE <- mean((lm_preds - y)^2)

   # Return list
   our_list <- list("betas" = t(lm_coeffs), "MSE" = lm_MSE)
   return(our_list)
}


#------------------------------------------------------------------------------
# 3. Generate predictions from any-dimensional inputs
# - Function takes in coefficients and input data and outputs model predictions

gen_preds <- function(input_coeffs, input_data){

   # Make it a matrix
   input_data <- as.matrix(input_data)

   # Check dimensionality of input data
   if(ncol(input_data) == 1){

          # Can't use sweep if 1-dimensional X data
          return(input_coeffs[1] + input_coeffs[2] * input_data)

   } else {
          # Use sweep if higher-dimension data
          return(input_coeffs[1] + rowSums(sweep(input_data, MARGIN = 2, input_coeffs[-1], "*")))}
}

#---------------------------------------------------------------------------------
# 4. Perform multivariate linear regression via gradient descent
gd_lm <- function(X, y, alpha = 1e-4, n_iter = 1000, stop_thresh = 1e-5, n_runs = 5,
                  figure = F, full = F){

   # Note: user has to specify what the features (X) and what the output (y) are
   # - X and y can be in matrix or data.frame format

   # Convert X to matrix
   X <- as.matrix(X)

   run_vals <- matrix(NA, ncol = ncol(X) + 3, nrow = n_runs)
   colnames(run_vals) <- c("MSE", "num_iter", paste0("beta_", seq(0, ncol(X))))

   # Create matrix to hold all MSE and coefficient paths
   if(full == T){

      MSE_matrix <- matrix(NA, nrow = n_iter, ncol = n_runs)
      colnames(MSE_matrix) <- paste0("run", 1:n_runs)
      rownames(MSE_matrix) <- paste0("iter", 1:n_iter)

      coef_array <- array(NA, dim = c(n_iter, n_runs, ncol(X) + 1))
      dimnames(coef_array) <- list(paste0("iter", 1:n_iter),
                                   paste0("run", 1:n_runs),
                                   paste0("beta_", seq(0, ncol(X))))

   }

   # Go through the runs
   for(run in 1:n_runs){

      # Create empty matrix of betas matching number of features
      coeffs <- matrix(NA, ncol = ncol(X) + 1, nrow = n_iter)
      colnames(coeffs) <- paste0('beta_', 0:(ncol(X)))

      # Initialize the betas at random values close to zero
      coeffs[1, ] <- rnorm(ncol(coeffs), mean = 0, sd = 3)

      #-------------------------------------------------------------------------------------------
      # Create empty variables to store mean squared error and number of iterations at convergence

      MSE_run <- c()
      final_iter <- c()

      ##################################################################################
      # Iterate
      for(iter in 2:n_iter){

         # Generate predictions
         predictions <- coeffs[iter-1, 1] +                          # Intercept
            rowSums(sweep(X, MARGIN = 2, coeffs[iter-1, -1], "*"))   # Slopes for all features

         #-----------------------------------------------------------------------------
         # Update betas based on residuals

         # 1. Intercept
         coeffs[iter, 1] <- coeffs[iter-1, 1] - alpha * mean(predictions - y)

         # 2. Slopes
         coeffs[iter, -1] <- coeffs[iter-1, -1] - alpha * apply((predictions - y) * X, 2, mean)

         #-------------------------------------------------------------------------------
         # Record MSE
         MSE_run[iter] <- mean((predictions - y)^2)

         # Stop iterating if MSE not improving substantially
         final_iter <- iter

         if(iter > 3 & ((MSE_run[iter - 1] - MSE_run[iter]) < stop_thresh)){break}

      }

      # Save run's final coefficients
      run_coeffs <- coeffs[final_iter, ]

      # Record this run's values
      run_vals[run, ] <- c(MSE_run[final_iter], final_iter, run_coeffs)

      # Save full MSE and coefficient paths if full = T
      if(full == T){

         MSE_matrix[1:final_iter, run] <- MSE_run[1:final_iter]
         coef_array[1:final_iter, run, ] <- coeffs[1:final_iter, ]
      }

   }

   ####################################################################################
   # Use the coefficients corresponding to the lowest MSE

   final_MSE <- min(run_vals[,1], na.rm = T)
   final_coeffs <- run_vals[which(run_vals[,1] == final_MSE), -(1:2)]

   #-----------------------------------------------------------
   # Generate plot if figure = T
   if(figure == T){

      # Too many dimensions
      if(ncol(X) > 2){cat("\nFigures only possible when N features < 3\n\n")}

      # 3-dimensional plot
      if(ncol(X) == 2){

         # Load 'scatterplot3d' package or tell user to install
         try(library(scatterplot3d),
             outFile = cat("\nPlease install 'scatterplot3d' library first\n"))

         # Generate X sequences
         x_seq <- seq(0, max(X), length = 1000)

         # Plot data and add line
         plt <- scatterplot3d(X[,1], X[,2], y, xlab = "Feature_1", ylab = "Feature_2",
                              zlab = "Output", font.lab = 2, font.axis = 2)

         plt$points3d(x_seq, x_seq, gen_preds(final_coeffs, cbind(x_seq, x_seq)),
                      col = "red", type = 'l')

      }

      # 2-dimensional plot
      if(ncol(X) == 1){

         # Generate X sequences
         x_seq <- seq(0, max(X), length = 1000)

         plot(X, y, font.lab = 2, font.axis = 2, main = "Linear regression", pch = 19,
              col = "gray40", cex = 1.3, las = 1, cex.lab = 1.2, cex.axis = 1.2)
         points(X, y, cex = 1.3)
         lines(x_seq, gen_preds(final_coeffs, x_seq), col = "deepskyblue4", lwd = 3,
               lty = 2)
         abline(lm(y ~ X), col = "orange", lty = 2, lwd = 3)
         par(font = 2)
         legend("top", bty = 'n', c("Gradient descent", "Analytical"), pch = 19,
                col = c("deepskyblue4", "orange"), pt.cex = 1.2)

      }
   }

   #-----------------------------------------------------------
   # Create list for output

   # If X is 1-dimensional, just use lm
   if(ncol(X) == 1){

      # Run analytical regression
      reg <- lm(y ~ X)

      # Generate data frames of coefficients and MSE
      beta_df <- data.frame("grad_desc" = final_coeffs,
                            "analytical" = coef(reg))

      MSE_df <- data.frame("grad_desc" = final_MSE,
                           "analytical" = mean(residuals(reg)^2))

   } else {

      # Run analytical regression
      lm_reg <- analytical_reg(X, y)

      # Generate data frames of coefficients and MSE
      beta_df <- data.frame("grad_desc" = final_coeffs,
                            "analytical" = t(lm_reg$betas))

      MSE_df <- data.frame("grad_desc" = final_MSE,
                           "analytical" = lm_reg$MSE)

   }

   # Add run number to MSE
   run_vals <- cbind("run_number" = 1:n_runs, run_vals)

   # Rearrange run_vals data
   ordered_runs <- run_vals[order(run_vals[,2]), ]

   #------------------------------------------------------------
   # Create output list

   if(full == F){

      our_list <- list(ordered_runs, beta_df, MSE_df)
      names(our_list) <- c("run_outcomes", "betas", "final_MSE")

      return(our_list)

   } else {

      our_list <- list(MSE_matrix, coef_array, ordered_runs, beta_df, MSE_df)
      names(our_list) <- c("MSE_paths", "coeff_paths", "run_outcomes", "betas", "final_MSE")

      return(our_list)

   }

}
