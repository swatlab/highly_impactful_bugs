from __future__ import division
import csv
import MySQLdb
from numpy import median, percentile

# initialize the MySQL service
def initDatabase():
    #   Please set the database host, user and password here
    database = MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'your_passwd', db = dbname, port = 3306)
    cursor = database.cursor()
    return cursor

# build bug list
def buildBugList():
    inputDict = dict()
    entropyList, frequencyList = list(), list()
    for row in csvfile:
        inputDict[row[0]] = (float(row[1]), int(row[2]), float(row[4]))
        entropyList.append(float(row[1]))
        frequencyList.append(int(row[2]))
    '''#    bugList.append((row[0], float(row[1]), float(row[2])))
    splitList = [list(t) for t in zip(*bugList)]'''
    #entropy_cutoff = median(entropyList)
    #frequency_cutoff = median(frequencyList)
    entropy_cutoff = percentile(entropyList, sensitivity_level)
    frequency_cutoff = percentile(frequencyList, sensitivity_level)
    return (inputDict, entropy_cutoff, frequency_cutoff)

# determine whether a bug report has invalid status
def hasInvalid(bugID):
    cursor.execute('SELECT added FROM bugs_activity WHERE bug_id = ' + bugID)
    results = cursor.fetchall()
    invalid_status = False
    for r in results:
        if(r[0] == 'INVALID' or r[0] == 'WONTFIX' or r[0] == 'WORKSFORME' or r[0] == 'DUPLICATE'):
            invalid_status = True
            break
    if(invalid_status == True):
        return 'YES'
    else:
        return 'NO'

def isClosed(bugID):
    cursor.execute('SELECT bug_status FROM bugs WHERE bug_id = ' + bugID)
    results = cursor.fetchall()
    if(results[0][0] == 'VERIFIED' or results[0][0] == 'RESOLVED'):
        return 1
    else:
        return 0

# count patch number of a bug
def patchCount(bugID):
    cursor.execute('SELECT ispatch FROM attachments WHERE bug_id = ' + bugID)
    results = cursor.fetchall()
    patch_cnt = 0
    for r in results:
        if(r[0] == 1):
            patch_cnt += 1
    return patch_cnt

# count reopened times
def reopenedCount(bugID):
    cursor.execute('SELECT added FROM bugs_activity WHERE bug_id = ' + bugID)
    results = cursor.fetchall()
    reopened_cnt = 0
    for r in results:
        if(r[0] == 'REOPENED'):
            reopened_cnt += 1
    return reopened_cnt

def developerCount(bugID):
    cursor.execute('SELECT COUNT(DISTINCT who) FROM bugs_activity where bug_id = ' + bugID)
    results = cursor.fetchall()
    return results[0][0]

# extract metrics from bug database
def extractMetrics(cursor, inputDict):
    print 'Extracting metrics ...'
    bugDict = dict()
    for bugID in inputDict:
        metricDict = dict()
        # creat_time, bug_title, platform, severity, priority, last_modified_time, reporter, assignee 
        cursor.execute('SELECT  creation_ts, short_desc, rep_platform, bug_severity, priority, \
                                delta_ts, reporter, assigned_to, component_id \
                                FROM bugs WHERE bug_id = ' + bugID)
        results = cursor.fetchall()
        if(len(results)):
            tpl = results[0]
            metricDict['create_time'] = tpl[0]
            metricDict['title'] = tpl[1]
            metricDict['platform'] = tpl[2]
            metricDict['severity'] = tpl[3]
            metricDict['priority'] = tpl[4]
            metricDict['last_modified'] = tpl[5]
            metricDict['reporter'] = tpl[6]
            metricDict['assignee'] = tpl[7]
            metricDict['component'] = tpl[8]            
            # cc_count
            cursor.execute('SELECT COUNT(DISTINCT who) FROM cc WHERE bug_id = ' + bugID)
            results = cursor.fetchall()
            metricDict['cc_count'] = int(results[0][0])
            # comment
            cursor.execute('SELECT comments FROM bugs_fulltext where bug_id = ' + bugID)
            results = cursor.fetchall()
            metricDict['comment'] = results[0][0]
            # attachment
            metricDict['patch_count'] = patchCount(bugID)
            # invalid_status
            metricDict['invalid'] = hasInvalid(bugID)
            # reopened_count
            metricDict['reopened_count'] = reopenedCount(bugID)
            # developer_count
            metricDict['developer_count'] = developerCount(bugID)
            # is closed
            metricDict['is_closed'] = isClosed(bugID)
            # uptime
            metricDict['uptime'] = inputDict[bugID][2]
            # fixed time (if not fixed, fixed_time = -1)
            metricDict['fixing_time'] = computeFixingTime(bugID, cursor, metricDict['create_time'])
            componentOfBug(bugID, cursor)
            # bug triaging time
            metricDict['triaging_time'] = triagingDuration(bugID, cursor, tpl[0])
            # Add bugID/metrics to the bug dict
            bugDict[bugID] = metricDict
        else:
            print bugID
    return bugDict

# format and output the time by hour, weekday, monthday, month and yearday
def formatDate(tm): 
    hour = int(tm.strftime('%H'))
    week_day = tm.strftime('%a')
    month_day = int(tm.strftime('%d'))
    month = tm.strftime('%b')
    year_day = int(tm.strftime('%j'))
    return (hour, week_day, month_day, month, year_day)

# compute experience for reporters and assignees
def computeExperience(userDict, thisUser):
    if(thisUser in userDict):
        currentExp = userDict[thisUser] + 1
        userDict[thisUser] = currentExp
        return currentExp
    else:
        userDict[thisUser] = 1
        return 1

# compute the fixing time
def computeFixingTime(bugID, cursor, create_time):
    cursor.execute('SELECT added, bug_when FROM bugs_activity WHERE bug_id = ' + bugID)
    results = cursor.fetchall()
    for result in results:
        if(result[0] == 'RESOLVED'):
            fixed_time = result[1]
            return round((fixed_time - create_time).total_seconds(), 2)
    return -1

# return the component of a bug
def componentOfBug(bugID, cursor):
    cursor.execute('SELECT name FROM products WHERE id = (SELECT product_id FROM bugs WHERE bug_id = ' + bugID + ')')
    results = cursor.fetchall()
    #if(results[0][0] != 'Core'):
    #print 'product', results[0][0]
    cursor.execute('SELECT name FROM components WHERE id = (SELECT component_id FROM bugs WHERE bug_id = ' + bugID + ')')
    results = cursor.fetchall()
    #print 'component', results[0][0]
    component_set.add(results[0][0])
    return

# triaging duration
def triagingDuration(bugID, cursor, opened_time):
    cursor.execute('SELECT added, removed, bug_when FROM bugs_activity WHERE bug_id = ' + bugID + ' ORDER BY bug_when')
    results = cursor.fetchall()
    for row in results:
        if('assign' in row[0].lower()):
            return round((row[2] - opened_time).total_seconds(), 2)
        elif('assign' in row[1].lower()):
            return round((row[2] - opened_time).total_seconds(), 2)
    return '-1'

# decide one of the four regions for bugs 
def decideRegion(bugID, inputDict):
    thisEntropy = inputDict[bugID][0]
    thisFrequency = inputDict[bugID][1]
    if(thisEntropy > entropy_cutoff):
        if(thisFrequency > frequency_cutoff):
            return 'high'
    #return 'other'
        else:
            return 'moderate'
    else:
        if(thisFrequency > frequency_cutoff):
            return 'skewed'
        else:
            return 'isolated'

# analyse and output metrics into a csv file
def outputMetrics(bugDict, inputDict):
    print 'Outputing metrics ...'
    reporterDict, assigneeDict = dict(), dict()
    if(sensitivity_level == 50):
        csv_writer = csv.writer(open('metrics/' + product + '_metrics_' + criteria + '.csv', 'wb'))
    else:
        csv_writer = csv.writer(open('metrics/sensitivity_data/' + product + '_' + str(sensitivity_level) + '.csv', 'wb'))
    csv_writer.writerow(['bugID', 'hour', 'week_day', 'month_day', 'month', 'year_day', 'component', \
                        'title_size', 'platform', 'severity', 'priority', 'cc_count', 'comment_size', \
                        'invalid_status', 'is_closed', 'patch_count', 'fixing_time', 'reopened_count', 'triaging_time',\
                        'uptime', 'developer_count', 'reporter_exp', 'assignee_exp', 'region'])
    sortedList = sorted(bugDict.keys())
    for bugID in sortedList:
        metricDict = bugDict[bugID]
        create_time = metricDict['create_time']
        last_modified = metricDict['last_modified']
        title_size = len(metricDict['title'].split())
        platform = metricDict['platform']
        severity = metricDict['severity']
        priority = metricDict['priority']
        cc_count = metricDict['cc_count']
        component = metricDict['component']
        comment_size = len(metricDict['comment'].split())
        invalid_status = metricDict['invalid']
        is_closed = metricDict['is_closed']
        uptime = metricDict['uptime']
        patch_count = metricDict['patch_count']
        reopened_count = metricDict['reopened_count']
        triaging_time = metricDict['triaging_time']
        developer_count = metricDict['developer_count']
        reporter = metricDict['reporter']
        assignee = metricDict['assignee']
        (hour, week_day, month_day, month, year_day) = formatDate(create_time)
        fixing_time = metricDict['fixing_time']             
        reporter_exp = computeExperience(reporterDict, reporter)
        assignee_exp = computeExperience(assigneeDict, assignee)
        region = decideRegion(bugID, inputDict)
        #if(region == 'high' or region == 'isolated'):
        csv_writer.writerow([bugID, hour, week_day, month_day, month, year_day, component, \
                            title_size, platform, severity, priority, cc_count, comment_size, \
                            invalid_status, is_closed, patch_count, fixing_time, reopened_count, triaging_time,\
                            uptime, developer_count, reporter_exp, assignee_exp, region])
    return

if(__name__ == '__main__'):
    component_set = set()
    product = 'firefox'
    criteria = 'machine'
    sensitivity_level = 50

    csvfile = csv.reader(open('bugs/' + product + '_entropy_' + criteria + '.csv', 'rb'))
    next(csvfile, None)
    cursor = initDatabase()
    (inputDict, entropy_cutoff, frequency_cutoff) = buildBugList()
    bugDict = extractMetrics(cursor, inputDict)
    outputMetrics(bugDict, inputDict)
    
    comp_list = sorted(list(component_set))
    for c in comp_list:
        print c