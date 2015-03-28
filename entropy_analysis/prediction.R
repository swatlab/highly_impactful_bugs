library(data.table)

#	Initialise variables
project = 'fennecandroid'
model = 'cforest'
tree_number = 50
doVIF = 'NO'

#	Group all traning bug IDs
extractBugSet <- function(v_number) {
	row.list <- grep(v_number, data.set$version)
	bug.table <- data.set[row.list, ]
	bug.groups <- bug.table$bugs
	row.count <- nrow(bug.table)
	result <- vector()
	for(i in 1:row.count) {
		subversion_bugs <- strsplit(bug.groups[i], ' ')
		result <- c(result, unlist(subversion_bugs))
	}
	return(unique(result))
}

combineVersions <- function() {
	result <- vector()
	for (v in 10:13) {
		pattern <- sprintf('^%d\\.', v)
		bugset <- extractBugSet(pattern)
		result <- c(result, bugset)
	}
	return (unique(result))
}

#	Read data from the file
data.set <- data.table(fread(sprintf('bugs/%s_version.csv', project), header = TRUE, sep = ','))

#	Define modeling formula
if(project == 'firefox') {
	xcol <- c('week_day', 'month_day', 'month', 'uptime', 'cc_count', 'title_size', 'component', 'reporter_exp', 
			'betweenness', 'closeness', 'indegree', 'outdegree', 'LOC', 'avg_cyclomatic', 'maxnesting', 'ratio_comment', 
			'daily_crash', 'daily_user') # 'page_rank', 'cnt_func', 'year_day' are eliminated
}else if(project == 'fennecandroid') {
	xcol <- c('week_day', 'month_day', 'month', 'uptime', 'cc_count', 'title_size', 'component', 'reporter_exp', 
			'betweenness', 'closeness', 'indegree', 'outdegree', 'LOC', 'avg_cyclomatic', 'ratio_comment',  
			'daily_crash') #'page_rank', 'maxnesting', 'daily_user', 'year_day', 'cnt_func' are eliminated
}
formula <- as.formula(paste('region ~ ', paste(xcol, collapse= '+')))

#####	Training and testing versions	###
if(project == 'firefox') {
	version_pair <- c(3, 11, 3, 12, 3, 13, 3, 14, 3, 15, 3, 16, 3, 17, 3, 18, 3, 19, 3, 20, 5, 15, 5, 16)	# 35%
	#version_pair <- c(3, 19, 3, 20) # 40%
	#version_pair <- c(3, 9, 3, 10, 3, 11, 3, 12, 3, 13, 3, 14, 3, 15, 3, 16, 3, 17, 3, 18, 3, 19, 3, 20, 4, 20, 5, 11, 5, 12, 5, 13, 5, 14, 5, 15, 5, 16, 5, 17, 5, 18, 5, 19, 5, 20, 6, 12, 6, 13, 6, 14, 6, 15, 6, 16, 6, 17, 6, 20, 7, 15, 7, 16, 7, 17, 7, 20)	# 30%
	#version_pair <- c(3, 4, 3, 5, 3, 6, 3, 7, 3, 8, 3, 9, 3, 10, 3, 11, 3, 12, 3, 13, 3, 14, 3, 15, 3, 16, 3, 17, 3, 18, 3, 19, 3, 20, 4, 12, 4, 13, 4, 14, 4, 15, 4, 16, 4, 17, 4, 18, 4, 19, 4, 20, 5, 9, 5, 10, 5, 11, 5, 12, 5, 13, 5, 14, 5, 15, 5, 16, 5, 17, 5, 18, 5, 19, 5, 20, 6, 10, 6, 11, 6, 12, 6, 13, 6, 14, 6, 15, 6, 16, 6, 17, 6, 18, 6, 19, 6, 20, 7, 11, 7, 12, 7, 13, 7, 14, 7, 15, 7, 16, 7, 17, 7, 18, 7, 19, 7, 20, 8, 15, 8, 16, 8, 17, 8, 18, 8, 19, 8, 20, 9, 20)	# 25%
} else if(project == 'fennecandroid') {
	version_pair <- c(10, 14, 10, 15, 10, 16, 10, 17, 10, 18, 10, 19, 10, 20, 14, 19, 14, 20, 15, 19, 15, 20, 16, 20)	# 35%
	#version_pair <- c(10, 14, 10, 15, 10, 16, 10, 17, 10, 18, 10, 19, 10, 20, 14, 19, 14, 20, 15, 19, 15, 20) # 40%
	#version_pair <- c(10, 14, 10, 15, 10, 16, 10, 17, 10, 18, 10, 19, 10, 20, 14, 17, 14, 19, 14, 20, 15, 19, 15, 20, 16, 19, 16, 20, 17, 20, 18, 20, 19, 20)	# 30%
	#version_pair <- c(10, 14, 10, 15, 10, 16, 10, 17, 10, 18, 10, 19, 10, 20, 14, 16, 14, 17, 14, 18, 14, 19, 14, 20, 15, 19, 15, 20, 16, 19, 16, 20, 17, 19, 17, 20, 18, 19, 18, 20, 19, 20)	# 25%
}

#	Initialise the sum value of tp, tn, tp, and fn
tp.sum = tn.sum = fp.sum = fn.sum <- 0
#	Initialise the statistical matrix
matrix.stat <- matrix(nrow=length(version_pair)/2, ncol=4, dimnames=list(c(),c('version', 'traning', 'transferred', 'well_predicted')))
false.positives <- matrix(nrow=length(version_pair)/2, ncol=2, dimnames=list(c(),c('version', 'false_positive')))

for (i in 1:(length(version_pair)/2)) {	
	#	Version numbers for training and testing
	train.number <- version_pair[i*2-1]
	test.number <- version_pair[i*2]
	#	Extract bugs by version
	if(train.number == 10 & project == 'fennecandroid') {
		train.bugs <- combineVersions()
		#print(train.bugs)
	}
	else {
		train.pattern <- sprintf('^%d\\.', train.number)
		train.bugs <- extractBugSet(train.pattern)	
	}
	test.pattern <- sprintf('^%d\\.', test.number)
	#	transferred bugs to the new version
	intersect.bugs <- intersect(train.bugs, extractBugSet(test.pattern))
	#	new bugs in the new version
	test.bugs <- setdiff(extractBugSet(test.pattern), train.bugs)
	#	Read data from the file
	dataset <- as.data.frame(read.csv(sprintf('metrics/%s_metrics_machine.csv', project), header = TRUE))
	trainset <- dataset[dataset[, 'bugID'] %in% train.bugs, ]
	testset <- dataset[dataset[, 'bugID'] %in% test.bugs, ]	
	intersectset <- dataset[dataset[, 'bugID'] %in% intersect.bugs, ]
	#	Add code metrics to training and testing set
	metricset <- as.data.frame(read.csv(sprintf('SNA_analysis/%s/source_metrics_%d.csv', project, train.number), header = TRUE))
	trainset <- merge(trainset, metricset)
	metricset <- as.data.frame(read.csv(sprintf('SNA_analysis/%s/source_metrics_%d.csv', project, test.number), header = TRUE))
	testset <- merge(testset, metricset)
	#	Add before opening metrics to the data set
	metricset <- as.data.frame(read.csv(sprintf('metrics/%s_bfr_opening.csv', project), header = TRUE))
	trainset <- merge(trainset, metricset)
	metricset <- as.data.frame(read.csv(sprintf('metrics/%s_bfr_opening.csv', project), header = TRUE))
	testset <- merge(testset, metricset)		
	#	VIF analysis
	if(doVIF == 'YES') {
		library(car)
		formula <- as.formula(paste('region ~ ', paste(xcol, collapse= '+')))
		fit <- glm(formula, data = trainset, family = binomial())
		print(vif(fit))
	}
	#	Iteratively run validation
	if(model == 'C50') {
		library(C50)
		fit <- C5.0(formula, data = trainset, rules = TRUE)
	  	testset[, 'predict'] <- predict(fit, newdata = testset, type = 'class')
		print(C5imp(fit))
	} else if(model == 'randomForest') {
		library(randomForest)		
		fit <- randomForest(formula, data = trainset, ntree = tree_number, mtry = 5, importance = TRUE)
	  	testset[, 'predict'] <- predict(fit, newdata = testset)
		varImpPlot(fit, cex = 1, main = '')
	} else if(model == 'cforest') {
		library(party)
		data.controls <- cforest_unbiased(ntree = tree_number, mtry = 5)
		fit <- cforest(formula, data = trainset, controls = data.controls)
		testset[, 'predict'] <- predict(fit, newdata = testset)
		#print(sort(varimp(fit)))
	} else if(model == 'ctree') {
		library(party)
		data.controls <- ctree_control(maxsurrogate = 3)
		fit <- ctree(formula, data = trainset)
		testset[, 'predict'] <- predict(fit, newdata = testset)
		plot(fit)
	} else if(model == 'glm') {
		fit <- glm(formula, data = trainset, family = binomial())
		testset[, 'predict'] <- predict(fit, newdata = testset)
	}
	t <- table(observed = testset[, 'region'], predicted = testset[, 'predict'])
	#	Classify results into tp, tn, fp, and fn
	actualYES <- testset[testset['region'] == 'high', ]
	actualNO <- testset[testset['region'] != 'high', ]
	if(model == "glm"){
		threshold = 0.5
		tp <- nrow(actualYES[actualYES[,'predict'] > threshold,])
		tn <- nrow(actualNO[actualNO[, 'predict'] <= threshold,])
		fp <- nrow(actualNO[actualNO[, 'predict'] > threshold,])
		fn <- nrow(actualYES[actualYES[,'predict'] <= threshold,])
	} else {
		tp <- nrow(actualYES[actualYES[,'predict'] == 'high',])
		tn <- nrow(actualNO[actualNO[, 'predict'] != 'high',])
		fp <- nrow(actualNO[actualNO[, 'predict'] == 'high',])
		fn <- nrow(actualYES[actualYES[,'predict'] != 'high',])
	}
	tp.sum <- tp.sum + tp
	tn.sum <- tn.sum + tn
	fp.sum <- fp.sum + fp
	fn.sum <- fn.sum + fn
	print(sprintf('Validation no. %d finished', i))
	#	statictical data
	v.numbers <- sprintf('%d-%d', train.number, test.number)
	train_str <- paste(as.character(trainset$bugID), collapse = ' ')		#	train bugs to string
	intersect.high <- intersectset[intersectset['region'] == 'high', ]		#	transferred highly bugs to string
	intersect_str <- paste(as.character(intersect.high$bugID), collapse = ' ')	
	well_predicted <- actualYES[actualYES[,'predict'] == 'high',]			#	well predicted bugs to string
	well_predicted_str <- paste(as.character(well_predicted$bugID), collapse = ' ')
	matrix.stat[i, ] <- c(v.numbers, train_str, intersect_str, well_predicted_str)
	
	fp.bugs <- actualNO[actualNO[, 'predict'] == 'high',]$bugID
	fp.str <- paste(as.character(fp.bugs), collapse = ' ')
	false.positives[i, ] <- c(v.numbers, fp.str)
}

#	compute prediction results
acc <- ((tn.sum+tp.sum)/(tn.sum+fp.sum+fn.sum+tp.sum))
re_pre <- (tp.sum/(tp.sum+fp.sum))
re_rec <- (tp.sum/(tp.sum+fn.sum))
re_fm <- (2 * re_pre * re_rec / (re_pre + re_rec))
nr_pre <- (tn.sum/(tn.sum+fn.sum))
nr_rec <- (tn.sum/(tn.sum+fp.sum))
nr_fm <- (2 * nr_pre * nr_rec / (nr_pre + nr_rec))

print(sprintf('accuracy: %.1f%%', acc * 100))
print(sprintf('high pre: %.1f%%', re_pre * 100))
print(sprintf('high rec: %.1f%%', re_rec * 100))
print(sprintf('high f-measure: %.1f%%', re_fm * 100))


#	output prediction statistical results for the reduction analysis
#output.path <- sprintf('../crash_analysis/reduction_analysis/prediction_stat/%s_prediction_stat.csv', project)
#write.table(matrix.stat, output.path, row.names = FALSE, col.names=TRUE, sep = ',')

#	output prediction statistical results for the false postive analysis
#output.path <- sprintf('false_positives/%s_false_positives.csv', project)
#write.table(false.positives, output.path, row.names = FALSE, col.names=TRUE, sep = ',')
