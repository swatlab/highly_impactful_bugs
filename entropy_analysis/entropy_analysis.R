library(data.table)

product = 'firefox'		# please choose: firefox / fennecandroid
plot = 'NO'
sensitivity_level = 0.5

#	Read data from the file
data_set <- data.table(fread(sprintf('bugs/%s_entropy_machine.csv', product), header = TRUE, sep = ','))
total_bugs <- nrow(data_set)

#	Log of entropy
data_set[, 'log_entropy'] <- data_set[, log(entropy)]
data_set[, 'log_freq'] <- data_set[, log(frequency)]

#	Normalize frequency value
max_freq <- max(data_set$frequency)
data_set[, 'norm_freq'] <- data_set[, frequency/max_freq]

#	Nomalized log of frequency
max_freq <- max(data_set$log_freq)
data_set[, 'log_freq'] <- data_set[, log_freq/max_freq]

#	Normalize version_cnt value
max_ver_cnt <- max(data_set$version_cnt)
data_set[, 'norm_ver_cnt'] <- data_set[, version_cnt/max_ver_cnt]


#	Median of entropy and frequency (or 70%, 90% of percentile)
entropy.cutoff <- quantile(data_set$entropy, c(sensitivity_level)) 		
frequency.cutoff <- quantile(data_set$norm_freq, c(sensitivity_level)) 	


if(plot == 'YES') {
	#	Scatter plot for entropy vs. frequency
	plot(data_set$entropy, data_set$norm_freq,		# plot the variables 
		cex.lab=1.5, 
		xlab="Entropy",        						# x−axis label 
		ylab="Normalized Frequency")				# y−axis label

	#	Scatter plot for the log of entropy vs. frequency
	plot(data_set$log_entropy, data_set$log_freq,		
		xlab="Entropy (log)",        						
		ylab="Normalized Frequency (log)")				

	#	Scatter plot for entropy vs. version_cnt
	plot(data_set$entropy, data_set$norm_ver_cnt,	
		xlab="Entropy",        						
		ylab="Normalized Version Count")				

	#	Scatter plot for frequency vs. version_cnt
	plot(data_set$norm_freq, data_set$norm_ver_cnt,		
		xlab="Normalized Frequency",        						
		ylab="Normalized Version Count")				
}

high_entropy <- data_set[data_set[, entropy] > entropy.cutoff, ]
low_entropy <- data_set[data_set[, entropy] <= entropy.cutoff, ]

high_region <- high_entropy[high_entropy[, norm_freq] > frequency.cutoff, ]
moderated_region <- high_entropy[high_entropy[, norm_freq] <= frequency.cutoff, ]
skewed_region <- low_entropy[low_entropy[, norm_freq] > frequency.cutoff, ]
isolated_region <- low_entropy[low_entropy[, norm_freq] <= frequency.cutoff, ]


print(sprintf('Total Bugs: %d', total_bugs))

high_bugs = nrow(high_region)
print(sprintf('High Region: %d(%.1f%%)', high_bugs, high_bugs/total_bugs*100))

moderated_bugs <- nrow(moderated_region)
print(sprintf('Moderated Region: %d(%.1f%%)', moderated_bugs, moderated_bugs/total_bugs*100))

skewed_bugs <- nrow(skewed_region)
print(sprintf('Skewed Region: %d(%.1f%%)', skewed_bugs, skewed_bugs/total_bugs*100))

isolated_bugs <- nrow(isolated_region)
print(sprintf('Isolated Region: %d(%.1f%%)', isolated_bugs, isolated_bugs/total_bugs*100))

