product = 'fennecandroid'

closed_rate <- function(region, reg.name)
{
	closed <- length(region[region[] == 1])
	all <- length(region)
	print(sprintf('%s bugs closed rate: %f', reg.name, closed/all))
}

kruskal_test <- function(data, index, title, yaxis)
{
	size <- length(data[, 1])
	high <- numeric()
	moderate <- numeric()
	skewed <- numeric()
	isolated <- numeric()

	for(i in 1:size){
		if(data[i, 'region'] == 'high') {
			high <- append(high, data[i, index])
		}
		else if(data[i, 'region'] == 'skewed') {
			skewed <- append(skewed, data[i, index])
		}
		else if(data[i, 'region'] == 'moderate') {
			moderate <- append(moderate, data[i, index])
		}
		else if(data[i, 'region'] == 'isolated') {
			isolated <- append(isolated, data[i, index])
		}
	}

	if(index == 'is_closed') {
		closed_rate(high, 'Highly dis.')
		closed_rate(skewed, 'Skewed')
		closed_rate(moderate, 'Moderately dis.')
		closed_rate(isolated, 'Isolated')
	}
	else {
		if(index == 'fixing_time') {
			high <- high[high >=0 ]
			skewed <- skewed[skewed >= 0]
			moderate <- moderate[moderate >= 0]
			isolated <- isolated[isolated >= 0]
		}

		print(paste('Highly dis. bugs:', mean(high)))
		print(paste('Skewed bugs:', mean(skewed)))
		print(paste('Moderately dis. bugs:', mean(moderate)))
		print(paste('Isolated bugs:', mean(isolated)))
	
		par(cex.axis=1.5, cex.lab=1.5, cex.main=1.5)
		boxplot(list(high, skewed, moderate, isolated), 
				names = c('highly', 'skewed', 'moderately', 'isolated'), 
				main = title, ylab = yaxis, 
				col=rep(c('grey', 'white', 'white', 'white')), 
				outline=FALSE)
	
		four.regions <- list(high, moderate, skewed, isolated)
		kruskal.test(four.regions)
	}
}

data <- read.csv(sprintf('metrics/%s_metrics_machine.csv', product), header = TRUE)
#data <- read.csv(sprintf('metrics/sensitivity_data/%s_70.csv', product), header = TRUE)
#data <- read.csv(sprintf('metrics/sensitivity_data/%s_90.csv', product), header = TRUE)

print('fixing time')
kruskal_test(data, 'fixing_time', 'Fixing time (seconds)', 'Time in second')

print('triaging time')
triaging.data <- data[data$triaging_time > 0,]
kruskal_test(triaging.data, 'triaging_time', 'triaging days', 'triaging days')

print('patch count')
kruskal_test(data, 'patch_count', 'Patch number', 'patches')

print('comment size')
kruskal_test(data, 'comment_size', 'Comment size (words)', 'Words in comment')

print('reopened frequency')
kruskal_test(data, 'reopened_count', 'reopened count', 'reopened occur')

print('reporter experience')
kruskal_test(data, 'reporter_exp', 'Reporter experience', 'Prior reported bugs')

print('assignee experience')
kruskal_test(data, 'assignee_exp', 'Assignee experience', 'Prior assigned bugs')

print('developer count')
kruskal_test(data, 'developer_count', 'Fixer number', 'Fixers')

print('cc count')
kruskal_test(data, 'cc_count', 'CC number', 'CC number')

print('is closed')
kruskal_test(data, 'is_closed', 'is closed', 'closed rate')
