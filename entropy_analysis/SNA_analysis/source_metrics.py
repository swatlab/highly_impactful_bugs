import csv
import MySQLdb
import re

# initialise the MySQL service
def initDatabase():
    #   Please set the database host, user and password here
    database = MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'your_passwd', db = dbname, port = 3306)
    cursor = database.cursor()
    return cursor

def extractTopFrame(topFrame):
    if(topFrame[-1] == ''):
        return topFrame[-2]
    else:
        return topFrame[-1]

def extractPath(location_str):
    if(re.search(r'([0-9]|[a-z0-9]+\.[a-z]+)\s*\t(\w|:)+\s*\t(\w|:)+', location_str)):
        path = re.search(r'\/[^\s]+\.(cpp|c|h)', location_str)
        if(path):
            folder = path.group(0)
            #return re.sub(r'^[\/\.]+', '', folder) + '  \t' + 'path'
            return ('path', re.sub(r'^[\/\.]+', '', folder))
        else:
            return 'not matched' 
    return 'not matched'

def extractFile(location_str):
    if(re.search(r'([0-9]|[a-z0-9]+\.[a-z]+)\s*\t(\w|:)+\s*\t(\w|:)+', location_str)):
        file = re.search(r'[^\s]+\.(cpp|c|h)[\s\:]+', location_str)
        if(file):
            sections = location_str.split(' ')
            for sec in sections:
                if('.cpp' in sec or '.h' in sec or '.c' in sec):
                    filename = re.search(r'\w+\.(cpp|c|h|cc)\b', sec)
                    if(filename):
                        #return filename.group(0) + '  \t' + 'file'
                        return ('file', filename.group(0))
        else:
            return 'not matched'
    return 'not matched'

def extractMethod(location_str):
    method = re.search(r'(\w+\:{2})+\w+', location_str)
    if(method):
        #return method.group(0) + '  \t' + 'method'
        return ('method', method.group(0))
    else:
        return 'not matched'

def extractOther(location_str):
    if(re.search(r'\.(cpp|c|h|cc)\b', location_str)):
        sections = location_str.split(' ')
        for sec in sections:
            if('.cpp' in sec or '.h' in sec or '.c' in sec):
                other = re.search(r'\w+\.(cpp|c|h|cc)\b', sec)
                if(other):
                    #return other.group(0) + '  \t' + 'other'
                    return ('other', other.group(0))
    else:
        return 'not matched'

def bugLocation(comments):
    text_list = comments.split('\n')
    for oneline in text_list:
        path = extractPath(oneline)
        if(path != 'not matched'):
            return path
    for oneline in text_list:
        file = extractFile(oneline)
        if(file != 'not matched'):
            return file
    for oneline in text_list:
        method = extractMethod(oneline)
        if(method != 'not matched'):
            return method
    for oneline in text_list:
        other = extractOther(oneline)
        if(other != 'not matched'):
            return other 
    #print comments
    return 'unknown'

def mapBugToCrash(bug_set):
    print 'Localise buggy files or methods ...'
    location_dict = dict()
    for bugID in bug_set:
        cursor.execute('SELECT comments FROM bugs_fulltext where bug_id = ' + bugID)
        results = cursor.fetchall()
        if(results):
            if(re.search(r'([0-9]|[a-z0-9]+\.[a-z]+)\s*\t(\w|:)+\s*\t(\w|:)+', results[0][0])):
                location_dict[bugID] = bugLocation(results[0][0])
            else:
                cursor.execute('SELECT short_desc FROM bugs_fulltext where bug_id = ' + bugID)
                results = cursor.fetchall()
                if(results):
                    #print bugID, results[0][0].decode('utf-8','ignore')
                    location_dict[bugID] = extractMethod(results[0][0])
        #else:
        #    print bugID
    return location_dict

def loadMetrics(metricFile):
    if('sna' in metricFile):
        print 'Load SNA metrics ...'
    elif('code' in metricFile):
        print 'Load code metrics ...'
    metricDict = dict()
    metricreader = csv.reader(open(metricFile, 'rb'))
    title = next(metricreader, None)
    for row in metricreader:
        #print row[0]
        if(len(row[0])):
            path = row[0].lower()
            metricDict[path] = row[1:]
    return (metricDict, title)

def fileMapping(location, metricDict, ncol):
    location_name = location[1].split('.')[0].lower()
    for node in metricDict:
        if((location_name in node) or (node in location_name)):
            #print node, metricDict[node]
            return metricDict[node]
    file_name = location_name.split('/')[-1].lower()
    for node in metricDict:
        if((file_name in node) or (node in file_name)):
            #print node, metricDict[node]
            return metricDict[node]    
    return [-1] * ncol

def methodMapping(location, metricDict, ncol):
    file_name = location[1].split('::')[-2].lower()
    for node in metricDict:
        if(file_name in node):
            #print node, metricDict[node]
            return metricDict[node]
    return [-1] * ncol

def mappingAndOutputMetrics():
    print 'Mapping bugs and outputing metrics ...'
    writer = csv.writer(open(product + '/source_metrics_' + analytic_version + '.csv', 'w'))
    writer.writerow(['bugID'] + title_sna[1:] + title_file[1:])
    
    ncol_sna = len(title_sna) -1
    ncol_file = len(title_file) -1
    bugMetrics = dict()
    for bugID in location_dict:
        location = location_dict[bugID]
        if(not isinstance(location, basestring)):
            if(location[0] == 'method'):
                #print bugID, location
                #metrics = methodMapping(location)
                #bugMetrics[bugID] = methodMapping(location, snaDict, ncol_sna) + methodMapping(location, fileDict, ncol_file)
                metric_list = methodMapping(location, snaDict, ncol_sna) + methodMapping(location, fileDict, ncol_file)
            else:
                #print bugID, location
                #metrics = fileMapping(location)
                #bugMetrics[bugID] = fileMapping(location, snaDict, ncol_sna) + fileMapping(location, fileDict, ncol_file)
                metric_list = fileMapping(location, snaDict, ncol_sna) + fileMapping(location, fileDict, ncol_file)
        else:
            #bugMetrics[bugID] = ['n/a'] * (ncol_sna + ncol_file)
            metric_list = [-1] * (ncol_sna + ncol_file)
        writer.writerow([bugID] + metric_list)
    return bugMetrics

if(__name__ == '__main__'):
    analytic_version = '10'
    product = 'fennecandroid'
    bugfile = csv.reader(open('../bugs/' + product + '_version.csv', 'rb'))
    next(bugfile, None)
    #   load the version-bug mapping file
    bug_dict = dict()
    for row in bugfile:
        bug_dict[row[0]] = row[1].split(' ')
    #   extract bugs by version
    bug_set = set()
    for v in bug_dict:
        #   because Fennec for Android did not release versions 11, 12, and 13
        #   the next version of v10 is v14
        if(product == 'fennecandroid' and analytic_version == '10'):
            if(v.startswith('10.') or v.startswith('11.') or v.startswith('12.') or v.startswith('13')):
                bug_set |= set(bug_dict[v])
        elif(v.startswith(analytic_version + '.')):
            bug_set |= set(bug_dict[v])
    #   initialise bug database service
    cursor = initDatabase()
    #   locate buggy files or methods
    location_dict = mapBugToCrash(bug_set)
    #   read file metrics to a dictionary
    (snaDict, title_sna) = loadMetrics(product + '/sna_metrics_' + analytic_version + '.csv')
    (fileDict, title_file) = loadMetrics(product +'/code_metrics_' + analytic_version + '.csv')
    
    #   mapping bugs to metrics and output to a csv file
    bugMetrics = mappingAndOutputMetrics()
    
    #for bugID in bugMetrics:
    #    print bugID, bugMetrics[bugID]
    print 'Done.'
    
