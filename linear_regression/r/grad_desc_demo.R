######################################################################################################
# Multivariate linear regression via gradient descent: demo
# Author: Matt Sosna
#
######################################################################################################
# Load functions
setwd("")   # Set path to function here
source('grad_desc_lm.R')

#-----------------------------------------------------------------------------------------------------
# 1. Relationship between hours studied and exam score

   # Generate data
   dat <- gen_data(n_obs = 50, noise = 3, n_features = 1)

   # Create color spectrum
   library(RColorBrewer)
   colors <- colorRampPalette(c("red", "orange", "green", "forestgreen"))(n = round(max(dat$y))+1)

   # Plot relationship
   plot(dat$X/10 + 0.2, dat$y + 50, pch = 19, col = colors[round(dat$y)], xlab = "Hours studied",
        ylab = "Exam score", font.lab = 2, font.axis = 2, las = 1, cex = 2, cex.main = 1.5,
        main = "Hours studied versus exam score", cex.lab = 1.3, cex.axis = 1.2)
   points(dat$X/10 + 0.2, dat$y+50, cex = 2)

#---------------------------------------------------------------------------------------------------
# 2. Various regressions with different MSE

   # Three regressions that differ in their MSE
   attempts <- as.matrix(data.frame('beta_0' = c(100, 75, 49.630775),
                                    'beta_1' = c(-5, 0, 9.653769)))

   # Plot it
   par(mfrow = c(1,3), oma = c(2, 2, 3, 0))
   for(i in 1:nrow(attempts)){

      # Calculate MSE
      model_mse <- mean((gen_preds(attempts[i, ], dat$X/10 + 0.2) - (dat$y + 50))^2)

      # Original plot
      plot(dat$X/10 + 0.2, dat$y + 50, pch = 19, col = colors[round(dat$y)], xlab = NA,
           ylab = NA, font.lab = 2, font.axis = 2, las = 1, cex = 2, cex.main = 2,
           main = "MSE:\n", cex.lab = 1.3, cex.axis = 1.2)
      points(dat$X/10 + 0.2, dat$y+50, cex = 2)
      title(paste0("\n", round(model_mse, 3)), col.main = "gray30", cex.main = 1.8)

      # Regression
      lines(seq(0, 6, length = 1000), gen_preds(attempts[i, ], seq(0, 6, length = 1000)),
            lwd = 3, lty = 3, col = "gray20")

      # Labels for overall plot
      mtext(outer = T, side = 1, font = 2, cex = 1.4, "Hours studied")
      mtext(outer = T, side = 2, font = 2, cex = 1.4, "Exam score")
      mtext(outer = T, side = 3, font = 2, cex = 1.7, "Hours studied versus exam score", padj = -0.4)

   }

#---------------------------------------------------------------------------------------------------
# 3a. Decrease in MSE with number of iterations

   # Generate 1-dimensional data
   dat <- gen_data(n_obs = 50, n_features = 1)

   # Generate model
   fit_1dim <- gd_lm(dat$X, dat$y, stop_thresh = 1e-3, full = T)

#---------------------------------------------------------------------------
# 3b. Number of iterations to convergence at the 1e-3 level vs. dimensions

   # Set parameters
   n_dimensions <- 1:6
   num_runs <- 1000
   num_iter <- 10000    # High value so model runs not artificially constrained

   # Create empty matrix
   iter_to_converge <- matrix(NA, ncol = length(n_dimensions), nrow = num_runs_iter)

   # Iterate through dimensions
   for(i in 1:length(n_dimensions)){

      # Generate n-dimensional data
      dat <- gen_data(n_obs = 50, n_features = n_dimensions[i])

      # Generate model
      fit <- gd_lm(dat$X, dat$y, stop_thresh = 1e-3, full = T, n_iter = num_iter_iter,
                   n_runs = num_runs_iter)

      # Save the number of iterations it took to get to 1e-3 stopping point
      iter_to_converge[, i] <- fit$run_outcomes[,3]

      print(i)
   }

#-----------------------------------------------------------------------------------------
# Set colors for plots
# - MSE plot: distinct colors
# - Iterations plot: color by mean number of iterations for that dimension

   library(scales)
   library(RColorBrewer)

   # MSE plot
   mse_colors <- c("black", "orange", "firebrick2", "forestgreen", "deepskyblue4")

   # Boxplots
   mean_iter <- apply(iter_to_converge, 2, mean)

   colors <- colorRampPalette(c("deepskyblue4", "orange", "firebrick2"))(n = max(mean_iter))
   boxplot_cols <- colors[mean_iter]

#-------------------------------------------------------------------------------------------
# Plots

   par(mfrow = c(1,2), font.axis = 2, font.lab = 2, cex.main = 1.5, cex.lab = 1.5, cex.axis = 1.1)

   # MSE plot
   plot(NA, log = 'y', xlab = "Iteration", ylab = "Mean Squared Error",
        xlim = c(0, max(fit$run_outcomes[,3])),
        ylim = c(min(fit$final_MSE), max(fit$MSE_paths, na.rm=T)),
        main = "Model error over time\n")
   title("\nN dimensions = 1", col.main = "gray40")
   par(font = 4)
   legend("topright", bty = 'n', col = mse_colors, pch = 19, legend = paste0("Run", 1:5))

   for(i in 1:ncol(fit$MSE_paths)){
      points(fit$MSE_paths[,i], col = alpha(mse_colors[i], 0.8), cex = 1.3, pch = 19)
   }

   # Number of iterations
   boxplot(itc, main = "Number of iterations until convergence\n",
           outline = F, font.lab = 2, xlab = "N dimensions in input data",
           ylab = "N iterations", border = boxplot_cols, lwd = 2)
   title("\nThreshold = 1e-3", col.main = "gray40")

################################################################################################
# 4. Number of runs versus number of iterations heat map

   # Set ranges
   range_n_dim_X <- 1:6
   range_n_runs <- 1:5
   range_n_iter <- c(50, 100, 250, 500, 1000, 5000)


   # Create empty arrayss
   MSE_diff_raw <- MSE_diff_prop <-  array(NA, dim = c(length(range_n_dim_X),
                                                       length(range_n_runs),
                                                       length(range_n_iter)))

   # Name arrays
   dimnames(MSE_diff_raw) <- dimnames(MSE_diff_prop) <- list(range_n_dim_X,
                                                             range_n_runs,
                                                             range_n_iter)

   #-------------------------------------------------------------------
   # The data at smaller dimensions can be particularly noisy, so let's run the analysis
   # many times and then take the mean.

   num_repeats <- 1000

   # Iterate through dimensionality of data
   for(i in 1:length(range_n_dim_X)){

      # Generate the data
      dat <- gen_data(n_obs = 50, n_features = range_n_dim_X[i])

      # Iterate through number of runs
      for(j in 1:length(range_n_runs)){

         # Iterate through number of iterations
         for(k in 1:length(range_n_iter)){

            # To deal with noise, run each parameter combination 5 times, then take the average
            rep_MSEs_raw <- rep_MSEs_prop <- c()

            for(replicate in 1:num_repeats){

               # Print progress
               cat("Processing - N dimensions:", range_n_dim_X[i],
                   "| N runs:", range_n_runs[j],
                   "| N iterations:", range_n_iter[k],
                   "| replicate:", replicate,
                   "\n")

               # Run the model
               mod <- custom_lm(dat$X, dat$y, n_runs = range_n_runs[j], n_iter = range_n_iter[k])

               # Save this replicate's difference in MSE
               # - [,1] and [1, 2] at end is necessary b/c data frame
               rep_MSEs_raw[replicate] <- (mod$MSE[1] - mod$MSE[2])[,1]
               rep_MSEs_prop[replicate] <- rep_MSEs_raw[replicate] / mod$MSE[1,2]
            }

            # Save the mean replicate MSE for this parameter combination
            MSE_diff_raw[i, j, k] <- mean(rep_MSEs_raw)
            MSE_diff_prop[i, j, k] <- mean(rep_MSEs_prop)

         }
      }
   }

   #--------------------------------------------------------------------------------------
   # Let's visualize some stuff

   library(lattice)
   library(RColorBrewer)
   library(grid)
   library(gridExtra)

   # Set up color gradient

   # Raw breaks
   raw_breaks <- seq(min(MSE_diff_raw), max(MSE_diff_raw)+1, by = 0.01)
   raw_cols <- colorRampPalette(c("white", "orange", "firebrick2", "brown"))(length(raw_breaks)-1)

   # Proportion breaks
   prop_breaks <- seq(0,35, by = 0.01)
   prop_cols <- colorRampPalette(c("white", "orange", "firebrick2", "brown"),
                                 bias = 3.5)(length(prop_breaks)-1)

   # Save plots as variables
   raw_list <- prop_list <- list()

   for(i in 1:length(range_n_dim_X)){

      prop_list[[i]] <- levelplot(MSE_diff_prop[i, , ], at = prop_breaks, col.regions = prop_cols,
                                  xlab = " ", ylab = " ", main = paste0("N dimensions = ", i),
                                  scales = list(font=2))
   }

   #-------------------------------------------------------------------------------
   grid.arrange(prop_list[[1]], prop_list[[2]], prop_list[[3]], prop_list[[4]],
                prop_list[[5]], prop_list[[6]], ncol = 3,
                top = textGrob("MSE difference (proportion)",
                               gp = gpar(fontsize = 28, font = 2)),

                bottom = textGrob("Number of runs",
                                  gp = gpar(fontsize = 20, font = 2), y = 1),
                left = textGrob("Number of iterations",
                                gp = gpar(fontsize = 20, font = 2), rot = 90, x = 1))
