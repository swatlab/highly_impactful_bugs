from __future__ import division
import os, re, gzip, csv
import datetime
import MySQLdb
from numpy import median, mean
from datetime import timedelta

# initialize the MySQL service
def initDatabase():
    #   Please set the database host, user and password here
    database = MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'your_passwd', db = dbname, port = 3306)
    cursor = database.cursor()
    return cursor
    
# build bug set for fixed High Impact Bugs
def buildBugSet(stat_file):
    bug_dict = dict()
    csvreader = csv.reader(open(stat_file, 'rb'))
    next(csvreader, None)
    for row in csvreader:
        transferred_bugs = set(row[2].split(' '))
        well_predicted_bugs = set(row[3].split(' '))
        bug_dict[row[0]] = (transferred_bugs, well_predicted_bugs)
        validation_user[row[0]] = dict()
    return bug_dict

# compute the median of fixing time High Impact Bugs in train set
def fixingTimeMdian(cursor, stat_file):
    print 'Computing median fixing time ...'
    median_fixing = dict()
    csvreader = csv.reader(open(stat_file, 'rb'))
    next(csvreader, None)
    for row in csvreader:
        trainBugs = set(row[1].split(' '))
        fixing_time_list = list()
        for bugID in trainBugs:
            cursor.execute('SELECT creation_ts, delta_ts, bug_status, priority FROM bugs WHERE bug_id = ' + bugID)
            results = cursor.fetchall()
            result_tpl = results[0]
            priority = result_tpl[3]
            if(priority == 'P1'):
                if(result_tpl[2] == 'RESOLVED'):
                    time_span = result_tpl[1] - result_tpl[0]
                    fixing_time_list.append(time_span.total_seconds())
        median_fixing[row[0]] = median(fixing_time_list)
    return median_fixing

# simulate fixed time for well predicted High Impact Bugs in test set
def simulateBugFixedDate(median_fixing, bug_dict):
    print 'Simulate bug fixing date ...'
    validation_bugs = dict()
    for validation in bug_dict:
        estimated_fixing = median_fixing[validation]
        transferred_bugs = bug_dict[validation][0]
        well_predicted_bugs = bug_dict[validation][1]
        reducible_bugs = transferred_bugs | well_predicted_bugs
        #print validation, len(reducible_bugs)
        reducible_dict = dict()
        for bugID in reducible_bugs:
            cursor.execute('SELECT creation_ts FROM bugs WHERE bug_id = ' + bugID)
            results = cursor.fetchall()
            if(len(results)):
                open_date = results[0][0]
                closed_date = open_date + timedelta(seconds = estimated_fixing)
                #   Each value in the dictionary is a list where the four elements represent: 
                #   opening date, closed date, total crashes, reduced crashes
                reducible_dict[bugID] = [open_date, closed_date, 0, 0]
        validation_bugs[validation] = reducible_dict
    return validation_bugs

#   Convert a date string to a datetime object
def strToDate(dateStr):
    return datetime.datetime.strptime(dateStr, '%Y%m%d%H%M')

#   Initialise reduced user dictioinary
def initUserDict():
    for validation in validation_bugs:
        impacted_user[validation] = set()
    return

#   Parse files in the selected period
def parseFiles(folderList, beginDate, endDate):
    print 'Count reduced crashes and users'
    total_reports = 0
    total_void = 0
    for thisFolder in folderList:
        #   folders should with digital names and within the selected period
        if(re.search(r'^[0-9]+$', thisFolder) and thisFolder >= beginDate and thisFolder <= endDate):  
            print 'Processing ' + thisFolder + ' ...'
            folderPath = parent_path + '/crash_report/' + thisFolder
            with gzip.open(folderPath + '/' + thisFolder +'-pub-crashdata.csv.gz', 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter = '\t')
                next(reader, None)  #   omit header
                #   Extract metrics from a crash report
                for line in reader: 
                    #   put metrics in a dictionary
                    crash_report = {'signiture': line[0],
                                    'crash_date': strToDate(line[3]),
                                    #'version': line[7],
                                    'bug_str': line[14],
                                    'os_name': line[10],
                                    'os_version': line[11],
                                    'cpu_info': line[12]}
                    #   Triage the crash report by user and bug
                    total_void += crashTriage(crash_report)
    return total_void

#   Analyse a crash report
def crashTriage(crash_report):
    void = 0    # count crash without bug list
    bug_list = list()
    crash_date = crash_report['crash_date']
    bug_str = crash_report['bug_str']    
    # handle crashes
    if(len(bug_str)):
        bug_list = bug_str.split(',')
    else:
        void = void + 1
    # handle users
    os_name = crash_report['os_name']
    os_version = crash_report['os_version']
    cpu_info = crash_report['cpu_info']
    user_key = os_name + ',' + os_version + ',' + cpu_info    
    # count total and reduced
    for validation in validation_bugs:
        bug_user_dict = validation_user[validation]     #   for the statistics of users
        reducible_dict = validation_bugs[validation]    #   for the statistics of crashes
        for bugID in bug_list:
            if(bugID in reducible_dict):
                #   total user count
                if(bugID in bug_user_dict):
                    user_stat_tpl = bug_user_dict[bugID]
                    user_stat_tpl[0].add(user_key)
                else:
                    user_stat_tpl = (set([user_key]), set())    # [total_users, impacted_users]
                    bug_user_dict[bugID] = user_stat_tpl
                #   reduced crash count
                stat_list = reducible_dict[bugID]
                closed_date = stat_list[1]
                stat_list[2] += 1               # total crashes of the bug
                if(crash_date > closed_date):   # reduced crashes/users of the bug
                    stat_list[3] += 1
                else:
                #   reduced user count
                    user_stat_tpl[1].add(user_key)
    return void

#   Compute reduced crash rate
def reducedCrash(total_void, validation_bugs):
    reduced_sum, total_sum = 0, 0
    reduced_stat_crash = dict()
    for validation in validation_bugs:
        total_crash, reduced_crash = 0, 0
        reducible_dict = validation_bugs[validation]
        for bugID in reducible_dict:
            stat_list = reducible_dict[bugID]
            total_crash += stat_list[2]
            reduced_crash += stat_list[3]
        reduced_rate = round(reduced_crash / (total_crash+total_void), 3)
        reduced_stat_crash[validation] = reduced_rate
        reduced_sum += reduced_crash
        total_sum += (total_crash + total_void)
    return (reduced_stat_crash, reduced_sum/total_sum)

#   Compute reduced user rate
def reducedUser(total_user, impacted_user):
    reduced_stat_user = dict()
    for validation in validation_user:
        bug_user_dict = validation_user[validation]
        reduced_list = list()
        for bugID in bug_user_dict:
            user_stat_tpl = bug_user_dict[bugID]
            total_user = user_stat_tpl[0]
            if(len(total_user)):
                impacted_user = user_stat_tpl[1]
                reduced_user = total_user - impacted_user
                reduced_rate = len(reduced_user) / len(total_user)
                reduced_list.append(reduced_rate)
        #print reduced_list
        reduced_stat_user[validation] = round(mean(reduced_list), 3)
    return reduced_stat_user

if(__name__ == '__main__'):
    product = raw_input('Please choose the analysed product (Firefox/FennecAndroid):\n').lower()
    #print ''
    cursor = initDatabase()
    total_user = set()
    impacted_user = dict()
    validation_user = dict()
    
    #   median fixed time of Highly-Distributed Bugs in traning sets
    median_fixing = fixingTimeMdian(cursor, 'prediction_stat/' + product + '_prediction_stat.csv')
    #   simulate bugs' fixing date
    bug_dict = buildBugSet('prediction_stat/' + product + '_prediction_stat.csv')
    validation_bugs = simulateBugFixedDate(median_fixing, bug_dict)
    #   initialise reduced user dictionary
    initUserDict()
    
    #   compute reduction
    beginDate, endDate = '20120101', '20121231'
    path = os.getcwd()
    parent_path = os.sep.join(path.split(os.sep)[:-1])
    folderList = sorted(os.listdir(parent_path + '/crash_report'))
    total_void = parseFiles(folderList, beginDate, endDate)
    
    #   output results
    (reduced_stat_crash, reduced_crash_mean) = reducedCrash(total_void, validation_bugs)
    reduced_stat_user = reducedUser(total_user, impacted_user)
    
    print 'Median reduced crash rate:', median(reduced_stat_crash.values())
    print 'Median reduced user rate:', median(reduced_stat_user.values())
    print 'Mean reduced crash rate:', reduced_crash_mean
    print 'Mean reduced user rate:', mean(reduced_stat_user.values())
    print reduced_stat_crash
    print reduced_stat_user
    
    