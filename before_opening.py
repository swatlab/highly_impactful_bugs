from __future__ import division
import os, re
import gzip, csv
import datetime
import math
from collections import Counter

#   Load bug opening date
def loadBugOpening(file):
    bug_dict_opening = dict()
    csvreader = csv.reader(open(file, 'rb'))
    next(csvreader, None)
    for row in csvreader:
        bug_dict_opening[row[0]] = row[1]
    return bug_dict_opening

#   Convert a date string to a datetime object
def strToDate(dateStr):
    return datetime.datetime.strptime(dateStr, '%Y%m%d%H%M')

#   Convert a datetime object to a date string    
def dateToStr(dateObj):
    return dateObj.strftime('%Y%m%d%H%M%S')

def dateDiff(s1, s2):
    d1 = datetime.datetime.strptime(s1, '%Y%m%d')
    d2 = datetime.datetime.strptime(s2, '%Y%m%d')
    return int((d2 - d1).total_seconds()/3600/24)
    
#   Parse a bug string
def parseBugs(bug_str):
    if(bug_str == ''):
        return []
    else:
        return [aBug.strip() for aBug in bug_str.split(',')]
    
def makeUserKey(os_name, os_version, cpu_info):
    return os_name + ',' + os_version + ',' + cpu_info

#   Count crash occurrences for the crash reports where the bug list is given
def countExplicitCrashes(user_key, bug_list):
    for thisBug in bug_list:
        if(thisBug in bug_dict_crash):
            bug_dict_crash[thisBug] += 1
            bug_dict_user[thisBug].add(user_key) 
        else:
            bug_dict_crash[thisBug] = 1
            bug_dict_user[thisBug] = set(user_key)
    return

#   Map crash types to a bug
def mapCrashesToBug(bug_list, signature):
    for thisBug in bug_list:
        if(thisBug in bug_dict_sig):
            signature_set = bug_dict_sig[thisBug]
            signature_set.add(signature)
        else:
            signature_set = set([signature])
            bug_dict_sig[thisBug] = signature_set
    return

#   Build a user list (by crashing order) on a crash
def mapOccurToCrash(signature, user_key, crash_date):
    if(signature in crash_occur):
        occur_stack = crash_occur[signature]
        occur_stack.append((user_key, crash_date))
    else:
        occur_stack = [(user_key, crash_date)]
        crash_occur[signature] = occur_stack
    return

#   Triage crash report by user and bug
def crashTriage(crash_report):
    signature = crash_report['signature']
    user_key = makeUserKey(crash_report['os_name'], crash_report['os_version'], crash_report['cpu_info'])
    crash_date = crash_report['crash_date']
    crash_date = dateToStr(crash_report['crash_date'])
    #   extract bug list
    bug_list = parseBugs(crash_report['bug_str'])
    if(len(bug_list) > 0):      # if bug_list in the crash report, map user directly to bug
        countExplicitCrashes(user_key, bug_list)
        mapCrashesToBug(bug_list, signature)
    else:                       # otherwise, do the two step mapping (user-crash_type, crash_type-bug)
        mapOccurToCrash(signature, user_key, crash_date)
    return

#   Parse files in the selected period
def parseFiles(folderList, beginDate, endDate):
    total_reports = 0
    for thisFolder in folderList:
        #   folders should with digital names and within the selected period
        if(re.search(r'^[0-9]+$', thisFolder) and thisFolder >= beginDate and thisFolder <= endDate):  
            print 'Processing ' + thisFolder + ' ...'
            folderPath = os.getcwd() + '/crash_report/' + thisFolder
            try:
                with gzip.open(folderPath + '/' + thisFolder +'-pub-crashdata.csv.gz', 'rb') as csvfile:
                    reader = csv.reader(csvfile, delimiter = '\t')
                    next(csvfile, None)      #   omit header
                    #   Extract metrics from a crash report
                    for line in reader:
                        #   put metrics in a dictionary
                        crash_report = {'signature': line[0],
                                        'crash_date': strToDate(line[3]),
                                        'product': line[6],
                                        'bug_str': line[14], 
                                        'os_name': line[10],
                                        'os_version': line[11],
                                        'cpu_info': line[12]}
                        if(crash_report['product'].lower() == product.lower()):   # analysis by product
                            #   Triage the crash report by user and bug
                            crashTriage(crash_report)
            except:
                print 'Error path or empty file'
    return

#   Build the total user list of a bug by concatenating the user lists of each related crash type
def userStackOfBug(aBug):
    occur_list = list()
    signature_set = bug_dict_sig[aBug]
    #print aBug, signature_set
    for thissignature in signature_set:         #   list of crash users for a bug
        if(thissignature in crash_occur):       #   some crash-types may not contain crashes without bug 
            occurs = crash_occur[thissignature]  #   by adding user lists of each crash type
            occur_list += occurs
    return occur_list


def beforeOpeningOccurrence(thisBug, occur_list):
    before_crash = 0
    before_user = set()
    if(thisBug in bug_dict_opening):
        opening_date = bug_dict_opening[thisBug]
        for occur in occur_list:
            occur_user = occur[0]
            occur_date = occur[1]
            if(occur_date < opening_date):
                before_crash += 1
                before_user.add(occur_user)
        total_crash = before_crash + bug_dict_crash[thisBug]
        total_user = before_user | bug_dict_user[thisBug]
        day_diff = dateDiff(beginDate, opening_date) + 1
        if(day_diff <= 0):
            return (0, 0)
        return (before_crash/day_diff, len(before_user)/day_diff)
    else:
        return (0, 0)

def beforeOpeningStatistics():
    for thisBug in bug_dict_sig:
        occur_list = userStackOfBug(thisBug)
        (before_crash, before_user) = beforeOpeningOccurrence(thisBug, occur_list)
        csvwriter.writerow([thisBug, before_crash, before_user])
        #print thisBug, before_crash, before_user
    return


if(__name__ == '__main__'):
    product = raw_input('Please choose the analysed product (Firefox/FennecAndroid):\n').lower()
    print ''
            
    #   Initialize variables
    bug_dict_opening = loadBugOpening('bug_opening.csv')
    crash_occur, bug_dict_crash, bug_dict_user, bug_dict_sig = dict(), dict(), dict(), dict()
    beginDate, endDate = '20120101', '20121231'
    
    csvwriter = csv.writer(open('output/' + product + '_bfr_opening.csv', 'wb'))
    csvwriter.writerow(['bugID', 'daily_crash', 'daily_user'])
    
    #   parse crash files   
    folderList = sorted(os.listdir(os.getcwd() + '/crash_report'))
    parseFiles(folderList, beginDate, endDate)
        
    #   compute entropy for each bug
    beforeOpeningStatistics()
