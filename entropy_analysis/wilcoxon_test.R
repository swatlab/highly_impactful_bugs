product = 'fennecandroid'

closed_rate <- function(region, reg.name)
{
	closed <- length(region[region[] == 1])
	all <- length(region)
	print(sprintf('%s bugs closed rate: %f', reg.name, closed/all))
}

wilcoxon_test <- function(data, index)
{	
	size <- length(data[, 1])
	high <- numeric()
	other <- numeric()
	skewed <- numeric()
	#	split high impact bugs and other bugs
	for(i in 1:size){
		if(data[i, 'region'] == 'high') {
			high <- append(high, data[i, index])
		}
		else {
			other <- append(other, data[i, index])
			if(data[i, 'region'] == 'skewed') {
				skewed <- append(skewed, data[i, index])
			}
		}
	}
	if(index == 'is_closed') {
		closed_rate(high, 'Highly dis.')
		closed_rate(other, 'Other')
	}
	else {
		#	only consider fixed bug for the fixing time metric
		if(index == 'fixing_time') {
			high <- high[high >=0 ]
			other <- other[other >= 0]
			skewed <- skewed[skewed >= 0]
		}
		#	output data
		print(paste('Highly dis. bugs:', mean(high)))
		print(paste('Other bugs:', mean(other)))
		wilcox.test(high, other, correct=FALSE)
		#print(paste('Skewed bugs:', mean(skewed))) 
		#wilcox.test(high, skewed, correct=FALSE)
	}
}

data <- read.csv(sprintf('metrics/%s_metrics_machine.csv', product), header = TRUE)
#data <- read.csv(sprintf('metrics/sensitivity_data/%s_70.csv', product), header = TRUE)
#data <- read.csv(sprintf('metrics/sensitivity_data/%s_90.csv', product), header = TRUE)

print('fixing time')
wilcoxon_test(data, 'fixing_time')

print('triaging time')
triaging.data <- data[data$triaging_time > 0,]
wilcoxon_test(triaging.data, 'triaging_time')

print('patch count')
wilcoxon_test(data, 'patch_count')

print('comment size')
wilcoxon_test(data, 'comment_size')

print('reopened frequency')
wilcoxon_test(data, 'reopened_count')

print('reporter experience')
wilcoxon_test(data, 'reporter_exp')

print('assignee experience')
wilcoxon_test(data, 'assignee_exp')

print('developer count')
wilcoxon_test(data, 'developer_count')

print('cc count')
wilcoxon_test(data, 'cc_count')

print('is closed')
wilcoxon_test(data, 'is_closed')

