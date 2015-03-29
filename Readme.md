#An Empirical Study of Highly-Distributed Bugs in Mozilla Projects

#Requirements
- Python 2.7 or newer / Python 3.0 or newer
- R 3.1 or newer
- MySQL

#File description
- **crash_parser.py** is used to parse crash reports, map crash reports to bugs, and compute crashing frequency and entropy for bugs.
- **before_opening.py_** is used to compute the analysed bugs' average pre-opening daily crash occurrences and daily crashed users (the bugs' opened date is indicated in **bug_opening.csv**).
- **code_metric_analysis** contains code metric analysis script (and Understand databases).
	- **code_metrics.py**: to compute code complexity metrics and SNA metrics based on the Understand databases (the analytic UDBs should be put in this folder).
- **entropy_analysis** folder contains staticstical analytic scripts for bugs extracted from crash reports.
    - **bugs** folder:
		- bugs extracted from the subject crash reports, and the corresponding frequency, entropy, release number, and uptime of the bugs; 
		- releases extracted from subject crash reports, and the corresponding bugs of the releases.
	- **SNA_analysis** folder:
		- **source_metrics.py**: to compute each bug's code complexity metrics and SNA metrics via its buggy files (based on the results of **code_metrics.py**).
		- generated code complexity metrics and SNA metrics by subject systems and their releases.
	- **false_positives** folder contains the script and data to estimate the potential loss due to the false positives in the prediction.
    - **entropy_analysis.R**: compute the porportion of highly-distributed bugs and other bugs.
    - **extract_metrics.py**: extract bugs' metrics for prediction and hypothesis tests; the result will be outputed in the folder **metrics**.
    - **wilcoxon_test.R**: Wilcoxon rank sum test between highly-distributed bugs and other bugs.
    - **kruskal_wallis.R**: Kruskal-Wallis rank sum test among the four categories of bugs.
    - **prediction.R**: build predictive models for highly-distributed bugs with GLM, C5.0, ctree, randomForest, and cforest. 
- **reduction_analysis** folder contains the script to assess the benefit of the predictive model (*i.e.,* the reduction of crash occurrences and impacted users by the early prediction approach).

#How to use the script
- Run **crash_parser.py** to parse a group of crash reports.
    - There are two options to identify unique user, *i.e.,* by *installing profile* (Khomh et al.'s approach <a href="#refone" class="button">[1]</a>) or by *machine profile* (approach in this paper). The script will alert you to choose one of the options.
    - The range of subject crash reports could be changed in line 200.
- Please set your database's host, user and password in line 9 of **extract_metrics.py** (and do the same operation for **reduction_analysis.py** in line 11, **source_metrics.py** in line 8).
- Run **extract_metrics.py** to output metrics of bug for further analysis (hypothesis tests and prediction).
- In **prediction.R**, please set the prediction algorithm: GLM, C5.0, ctree, randomForest or cforest (in line 5), and set whether need a VIF analysis (in line 7).
- Before running **code_metrics.py**, you should generate an Understand database (UDB) by the Understand tool and put the UDB in the same folder of the script. The Understand tool is available: https://scitools.com.
- **code_metrics.py** is written in Python 3 (because Understand Python API only supports Python 3), other Python scripts are written in Python 2. Please make sure that you have installed all necessary modules required in these scripts.
   
#Data source
- Mozilla Bugzilla local database is available in:
    http://swat.polymtl.ca/anle/data/Mozilla_bugs/
- Socorro local crash reports are available in:
    https://crash-analysis.mozilla.com
- Firefox and Fennec source code (by release) is available in:
	http://download.cdn.mozilla.net/pub/mozilla.org/

#Reference
<p id="refone">[1] F. Khomh, B. Chan, Y. Zou, and A. E. Hassan. An entropy evaluation approach for triaging field 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;crashes: A case study of mozilla firefox. In *Reverse Engineering (WCRE), 2011 18th Working 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Conference on*, pages 261–270. IEEE, 2011.
</p>

#For any questions
Please send email to le.an@polymtl.ca
