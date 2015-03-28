from __future__ import division
import csv, re
from collections import Counter
from numpy import mean

def showPercentage(decimal):
    return str(round(decimal*100, 1)) + '%'

def versionBugs(project):
    csvreader = csv.reader(open('../bugs/' + project + '_version.csv', 'rb'))
    next(csvreader, None)
    version_bug = dict()
    #   seperate bugs by version
    for row in csvreader:
        v_str = row[0]
        if(re.search(r'^[1-9][0-9]?\.', v_str)):
            v = v_str.split('.')[0]
            bug_list = row[1].split(' ')
            if(v in version_bug):
                bugs = version_bug[v]
                bugs += bug_list
            else:
                version_bug[v] = bug_list
    #   eliminate duplicate bugs in a version
    for v in version_bug:
        bugs = version_bug[v]
        version_bug[v] = set(bugs)
    return version_bug

def metricDict(project):
    fixing_dict = dict()
    closed_dict = dict()
    severity_dict = dict()
    csvreader = csv.reader(open('../metrics/' + project + '_metrics_machine.csv', 'rb'))
    next(csvreader, None)
    for row in csvreader:
        fixing_dict[row[0]] = row[16]
        closed_dict[row[0]] = row[14]
        severity_dict[row[0]] = row[9]
    return (fixing_dict, closed_dict, severity_dict)

def totalFixingTime(version_bug, fixing_dict, release):
    total_fixing = 0
    bugs = version_bug[release]
    for aBug in bugs:
        if(aBug in fixing_dict):
            total_fixing += float(fixing_dict[aBug])
    return total_fixing

def closedRate(closed_dict, bug_list):
    closed_cnt = 0
    for aBug in bug_list:
        if(closed_dict[aBug] != '0'):
            closed_cnt += 1
    return closed_cnt/len(bug_list)

def severityStat(severity_dict, bug_list):
    severity_list = list()
    for aBug in bug_list:
        severity_list.append(severity_dict[aBug])
    stat_dict = Counter(severity_list)
    severe_bugs = stat_dict.get('blocker', 0) + stat_dict.get('critical', 0)
    return severe_bugs/len(bug_list)

if(__name__ == '__main__'):
    project = 'firefox'

    version_bug = versionBugs(project)
    (fixing_dict, closed_dict, severity_dict) = metricDict(project)
    
    fp_dict = dict()
    csvreader = csv.reader(open(project + '_false_positives.csv', 'rb'))
    next(csvreader, None)
    for row in csvreader:
        fp_dict[row[0]] = row[1].split(' ')
        
    fp_fixing_rates = list()
    fp_closed_rates = list()
    fp_severe_rates = list()
    for validation in fp_dict:
        time_list = list()
        for bug in fp_dict[validation]:
            fixing_time = float(fixing_dict[bug])
            time_list.append(fixing_time)
        fp_closed_rate = closedRate(closed_dict, fp_dict[validation])
        fp_severe_rate = severityStat(severity_dict, fp_dict[validation])
        fp_fixing = sum(time_list)
        total_fixing = totalFixingTime(version_bug, fixing_dict, validation.split('-')[1])
        fp_fixing_rates.append(fp_fixing/total_fixing)
        fp_closed_rates.append(fp_closed_rate)
        fp_severe_rates.append(fp_severe_rate)
        print validation, fp_fixing, fp_fixing/total_fixing, fp_closed_rate, fp_severe_rate
    print 'False positive fixing time over all bugs fixing time:', showPercentage(mean(fp_fixing_rates))
    print 'False positive closed rate:', showPercentage(mean(fp_closed_rate))
    print 'Severe (blocker or critical) false positive rate:', showPercentage(mean(fp_severe_rate))



