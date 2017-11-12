from __future__ import division
import os, re
import gzip, csv
import datetime
import math
from collections import Counter
from numpy import median

#   Convert a date string to a datetime object
def strToDate(dateStr):
    return datetime.datetime.strptime(dateStr, '%Y%m%d%H%M')

#   Convert a datetime object to a date string    
def dateToStr(dateObj):
    return dateObj.strftime('%Y%m%d%H%M%S')

#   Compute the install time (crash_time - install_age)
def computeInstallTime(crashTime, installAge):
    return crashTime - datetime.timedelta(seconds = int(installAge))
    
#   Parse a bug string
def parseBugs(bug_str):
    if(bug_str == ''):
        return []
    else:
        return [aBug.strip() for aBug in bug_str.split(',')]
    
def makeUserKey(os_name, os_version, cpu_info, crash_date, install_age):
    install_time = computeInstallTime(crash_date, install_age)
    '''precise install time to hour, convert it to string
    timeStr = install_time.replace(hour = 0, minute = 0, second = 0).strftime('%Y%m%d%H')'''
    timeStr = install_time.strftime('%Y%m%d%H%M%S')     
    if(user_key_mode == 'time'):
        return timeStr
    elif(user_key_mode == 'machine'):
        return os_name + ',' + os_version + ',' + cpu_info

#   Build a user list (by crashing order) on a crash
def mapUsersToCrash(signature, user_key):
    if(signature in crash_users):
        user_list = crash_users[signature]
        user_list.append(user_key)
    else:
        user_list = [user_key]
        crash_users[signature] = user_list
    return

def mapUsersToBug(user_key, bug_list):
    for thisBug in bug_list:
        if(thisBug in bug_dict_usr):
            user_list = bug_dict_usr[thisBug]
            user_list.append(user_key)
        else:
            user_list = [user_key]
            bug_dict_usr[thisBug] = user_list
    return

#   Map bugs to a version
def mapBugsToVersion(bug_list, version):
    if(version in version_bugs):
        bug_set = version_bugs[version]
        version_bugs[version] = bug_set | set(bug_list)
    else:
        bug_set = set(bug_list)
        version_bugs[version] = bug_set
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

#   Build a up_seconds list on a bug
def mapUptimeToBug(bug_list, up_seconds):
    for thisBug in bug_list:
        if thisBug in bug_uptime:
            uptime_list = bug_uptime[thisBug]
            uptime_list.append(up_seconds)
        else:
            uptime_list = [up_seconds]
            bug_uptime[thisBug] = uptime_list
    return

def mapBugsToSignaturee(bug_list, signature):
    for thisBug in bug_list:
        bug_to_signature[thisBug] = signature
    signature_to_bugs[signature] = bug_list

#   Triage crash report by user and bug
def crashTriage(crash_report):
    signature = crash_report['signature']
    user_key = makeUserKey(crash_report['os_name'], 
                        crash_report['os_version'],
                        crash_report['cpu_info'], 
                        crash_report['crash_date'], 
                        crash_report['install_age'])    
    process_date = dateToStr(crash_report['process_date'])
    crash_date = dateToStr(crash_report['crash_date'])
    up_seconds = int(crash_report['up_seconds'])
    version = crash_report['version']  
    #   extract bug list
    bug_list = parseBugs(crash_report['bug_str'])
    
    if(len(bug_list) > 0):      # if bug_list in the crash report, map user directly to bug
        mapUsersToBug(user_key, bug_list)
        mapCrashesToBug(bug_list, signature)
        mapBugsToVersion(bug_list, version)
        mapUptimeToBug(bug_list, up_seconds)
        mapBugsToSignaturee(bug_list, signature)
    else:                       # otherwise, do the two step mapping (user-crash_type, crash_type-bug)
        mapUsersToCrash(signature, user_key)
    
    #   build total user set
    total_user.add(user_key)

    return

#   Parse files in the selected period
def parseFiles(folderList, beginDate, endDate):
    total_reports = 0
    for thisFolder in folderList:
        #   folders should with digital names and within the selected period
        if(re.search(r'^[0-9]+$', thisFolder) and thisFolder >= beginDate and thisFolder <= endDate):  
            print 'Processing ' + thisFolder + ' ...'
            folderPath = os.getcwd() + '/crash_report/' + thisFolder
            with gzip.open(folderPath + '/' + thisFolder +'-pub-crashdata.csv.gz', 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter = '\t')
                next(csvfile, None)      #   omit header
                #   Extract metrics from a crash report
                for line in reader:
                    #   put metrics in a dictionary
                    crash_report = {'signature': line[0],
                                    'crash_date': strToDate(line[3]),
                                    'process_date': strToDate(line[4]),
                                    'product': line[6],
                                    'version': line[7],
                                    'bug_str': line[14],
                                    'up_seconds': line[16],
                                    'install_age': line[-4], 
                                    'os_name': line[10],
                                    'os_version': line[11],
                                    'cpu_info': line[12]}
                    if(crash_report['product'].lower() == product.lower()):   # analysis by product
                        #   Triage the crash report by user and bug
                        crashTriage(crash_report)
                        #   Count total reports
                        total_reports += 1
    return total_reports

#   Build the total user list of a bug by concatenating the user lists of each related crash type
def userStackOfBug(aBug):
    user_stack = list()
    signature_set = bug_dict_sig[aBug]
    #print aBug, signature_set
    for thissignature in signature_set:         #   list of crash users for a bug
        if(thissignature in crash_users):       #   some crash-types may not contain crashes without bug 
            users = crash_users[thissignature]  #   by adding user lists of each crash type
            user_stack += users
    return user_stack

#   Count the total version numbers in a bug
def versionsOfBug(thisBug):
    version_cnt = 0
    for aVersion in version_bugs:
        bug_set = version_bugs[aVersion]
        if(thisBug in bug_set):
            version_cnt += 1
    return version_cnt

#   Compute median up_seconds of a bug
def uptimeOfBug(thisBug):
    uptime_list = bug_uptime[thisBug]
    return median(uptime_list)

#   Remove the meaningless bug ID (i.e., '')
def cleanVoidBug():
    #   clean void key in bug_dict_sig
    if('' in bug_dict_sig):
        del bug_dict_sig['']
    #   clean void bugID for eash version
    for aVersion in version_bugs:
        bug_set = version_bugs[aVersion]
        version_bugs[aVersion] = bug_set - set([''])
    return

#   Compute bugs' entropy
def computeEntropy(total_user_cnt):
    for thisBug in bug_dict_sig:
        user_stack = userStackOfBug(thisBug)    # indirectly mapped users
        user_stack += bug_dict_usr[thisBug]     # directly mapped users
        
        version_cnt = versionsOfBug(thisBug)    # version count of the bug
        uptime = uptimeOfBug(thisBug)           # median uptime of the bug                 
        occur_dict = Counter(user_stack)
        entropy = 0
        frequency = len(user_stack)             # total crash occurrence for the bug
        for user in occur_dict:
            user_occur = occur_dict[user]       # one user's crash occurrence for the bug
            p_user = user_occur / frequency     # probability of the user triggering the bug  
            entropy += -(p_user * math.log(p_user, total_user_cnt))
        entropy_dict[thisBug] = (entropy, frequency, version_cnt, uptime)
    return

def computeSignEntropy(total_user_cnt):
    for sign in signature_to_bugs:        
        thisBug = signature_to_bugs[sign][0]
        user_stack = userStackOfBug(thisBug)    # indirectly mapped users
        user_stack += bug_dict_usr[thisBug]     # directly mapped users
        occur_dict = Counter(user_stack)
        entropy = 0
        frequency = len(user_stack)             # total crash occurrence for the bug
        for user in occur_dict:
            user_occur = occur_dict[user]       # one user's crash occurrence for the bug
            p_user = user_occur / frequency     # probability of the user triggering the bug  
            entropy += -(p_user * math.log(p_user, total_user_cnt))
        entropy_sign_dict[sign] = (entropy, frequency, len(signature_to_bugs[sign]))
    return

#   Output bugs' entropy, frequency and bugs in a csv file
def outputEntropy():
    print 'writing entropy to csv ...'
    for bugID in entropy_dict:
        (entropy, frequency, version_cnt, uptime) = entropy_dict[bugID]
        entropy_writer.writerow([bugID, entropy, frequency, version_cnt, uptime])
    return

def outputSignEntropy():
    print 'writing sign entropy to csv ...'
    for sign in signature_to_bugs:
        (entropy, frequency, no_of_bugs) = entropy_sign_dict[sign]
        signature_entropy_writer.writerow([sign, entropy, frequency, no_of_bugs])
    return

def outputVersionBugs():
    print 'writing version_bugs to csv ...'
    for aVersion in version_bugs:
        bug_set = version_bugs[aVersion]
        if(len(bug_set) > 0):
            bugs_str = ' '.join(bug_set)
            version_writer.writerow([aVersion, bugs_str])
    return

if(__name__ == '__main__'):
    user_key_mode = raw_input('Please choose the mode for entropy computing (time/machine):\n')
    print ''
    product = raw_input('Please choose the analysed product (Firefox/FennecAndroid):\n').lower()
    print ''
            
    #   Initialize variables
    crash_users, bug_dict_sig, entropy_dict, entropy_sign_dict, user_version, version_bugs = dict(), dict(), dict(), dict(), dict(), dict()
    bug_to_signature, signature_to_bugs = dict(), dict()
    bug_dict_usr, bug_uptime = dict(), dict()
    total_user = set()
    beginDate, endDate = '20120101', '20121231'
    
    #   create csv writer for each bug (about entropy, frequency and bugs)
    entropy_writer = csv.writer(open('output/' + product + '_entropy_' + user_key_mode + '.csv', 'wb'), delimiter = ',')
    #entropy_writer.writerow(['crash_type', 'entropy', 'frequency', 'bugs'])
    entropy_writer.writerow(['bug', 'entropy', 'frequency', 'version_cnt', 'up_time'])
    
    signature_entropy_writer = csv.writer(open('output/firefox_signature_entropy.csv', 'wb'), delimiter = ',')
    signature_entropy_writer.writerow(['signature', 'entropy', 'frequency', 'bug_count'])
    

    #   creat csv writer to map version~bugs
    #if(user_key_mode == 'time'):
    version_writer = csv.writer(open('output/' + product + '_version.csv', 'wb'), delimiter = ',')
    version_writer.writerow(['version', 'bugs'])
    
    #   parse crash files   
    folderList = sorted(os.listdir(os.getcwd() + '/crash_report'))
    total_reports = parseFiles(folderList, beginDate, endDate)
        
    #   compute entropy for each bug
    #cleanVoidBug()
    computeEntropy(len(total_user))
    
    computeSignEntropy(len(total_user))

    #   output entropy to a csv file
    outputEntropy()
    
    outputSignEntropy()
    #   output version~bugs to a csv file
    #if(user_key_mode == 'time'):
    outputVersionBugs()
    
    print 'total users:', len(total_user)
    print 'total reports:', total_reports