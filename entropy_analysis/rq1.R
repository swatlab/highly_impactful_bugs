product = 'firefox'

wilcoxon_test <- function(data, index)
{	
	size <- length(data[, 1])
	high_entropy <- numeric()
	low_entropy <- numeric()
	#	split high impact bugs and other bugs
	for(i in 1:size){
		if(data[i, 'region'] == 'high' || data[i,  'region'] == 'moderate') {
			high_entropy <- append(high_entropy, data[i, index])
		}
		else {
			low_entropy <- append(low_entropy, data[i, index])
		}
	}
	if(index == 'fixing_time') {
		high_entropy <- high_entropy[high_entropy >=0]
		low_entropy <- low_entropy[low_entropy >= 0]
	}
	#	output data
	print(paste('High Entropy:', mean(high_entropy)))
	print(paste('Low Entropy:', mean(low_entropy)))
	wilcox.test(high_entropy, low_entropy, correct=FALSE)
}

wilcoxon_test_for_signed <- function(data)
{	
	size <- length(data[, 1])
	multi_entropy <- numeric()
	single_entropy <- numeric()

	#	split high impact bugs and other bugs
	for(i in 1:size){
		if(data[i, 'bug_count'] > 1) {
			multi_entropy <- append(multi_entropy, data[i, 'entropy'])
		}
		else {
			single_entropy <- append(single_entropy, data[i, 'entropy'])
		}
	}
	#	output data
	print(paste('multibugs Entropy:', mean(multi_entropy)))
	print(paste('singlebugs Entropy:', mean(single_entropy)))
	wilcox.test(multi_entropy, single_entropy, correct=FALSE)
}

data <- read.csv(sprintf('metrics/%s_metrics_machine.csv', product), header = TRUE)

datasign <- read.csv(sprintf('metrics/firefox_signature_entropy.csv', product), header = TRUE)

print('the entropy for multibugs and single bug crashes are same')
wilcoxon_test_for_signed(datasign)

print('the fixing period for high-entropy bugs is same as low-entropy bugs')
wilcoxon_test(data, 'fixing_time')

print('the number of comments are same for high-entropy and low-entropy bugs')
wilcoxon_test(data, 'comment_size')

# [1] "the entropy for multibugs and single bug crashes are same"
# [1] "multibugs Entropy: 0.340879172111919"
# [1] "singlebugs Entropy: 0.264677044478464"

# 	Wilcoxon rank sum test

# data:  multi_entropy and single_entropy
# W = 703260, p-value < 2.2e-16
# alternative hypothesis: true location shift is not equal to 0

# [1] "the fixing period for high-entropy bugs is same as low-entropy bugs"
# [1] "High Entropy: 12722551.0052961"
# [1] "Low Entropy: 15369408.1490163"

# 	Wilcoxon rank sum test

# data:  high_entropy and low_entropy
# W = 2378200, p-value = 0.01673
# alternative hypothesis: true location shift is not equal to 0

# [1] "the number of comments are same for high-entropy and low-entropy bugs"
# [1] "High Entropy: 572.969493593655"
# [1] "Low Entropy: 468.4754396604"

# 	Wilcoxon rank sum test

# data:  high_entropy and low_entropy
# W = 6169800, p-value < 2.2e-16
# alternative hypothesis: true location shift is not equal to 0