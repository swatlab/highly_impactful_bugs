import understand
import csv
from igraph import *
    
#   Remove path prefix
def removePathPrefix(pathStr):
    return pathStr.split(root_folder)[-1]

#   Remove the extension of a file (to combine the .h and .cpp together)
def removeExtension(filename):
    return '.'.join(filename.split('.')[:-1])

#   Creat the adjacency matrix
def createAdjacencyMatrix(db):
    print('Creating adjacency matrix ...')
    all_classes = db.ents('File')
    #   build node_dict and combine .h and .cpp files into one node
    node_dict = dict()
    for a_class in all_classes:
        node = removeExtension(removePathPrefix(a_class.longname()))
        #   dependencies of a file
        dependency_dict = a_class.depends()
        dependency_set = set()
        for dep in dependency_dict:
            #print(removePathPrefix(dep.longname()))
            dep_name = removeExtension(removePathPrefix(dep.longname()))
            dependency_set.add(dep_name)
        #   construct node_dict
        if(node in node_dict):
            existing_set = node_dict[node]
            existing_set |= dependency_set
        else:
            node_dict[node] = dependency_set
    #   Node list is created as indices of rows and columns in the matrix
    node_list = list(node_dict.keys())
    # init matrix
    matrix_list = list()
    for i in range(0, len(node_dict)):
        a_row = [0]*len(node_dict)
        matrix_list.append(a_row)  
    # build matrix   
    i = 0
    for node in node_list:
        dependency_set = node_dict[node]
        j = 0
        for a_node in node_list:
            if(a_node in dependency_set):
                matrix_list[i][j] = 1
            j += 1
        i += 1
    return (node_list, matrix_list)

def codeMetrics(db):
    print('Computing and writing code metrics ...')
    writer = csv.writer(open('code_metrics_' + analytic_version + '.csv', 'w'))
    writer.writerow(['file', 'LOC', 'avg_cyclomatic', 'cnt_func', 'maxnesting', 'ratio_comment'])
    all_classes = db.ents('File')
    node_dict = dict()
    for a_class in all_classes:
        metric_dict = a_class.metric(['CountLine', 'AvgCyclomatic', 'CountDeclFunction', 'MaxNesting', 'RatioCommentToCode'])
        filename = removePathPrefix(a_class.longname())
        loc = metric_dict['CountLine']
        cyclomatic = metric_dict['AvgCyclomatic']
        cnt_func = metric_dict['CountDeclFunction']
        max_nesting = metric_dict['MaxNesting']
        ratio_comment = metric_dict['RatioCommentToCode']
        if(loc):
            #print([filename, loc, cyclomatic, cnt_func, max_nesting, ratio_comment])
            writer.writerow([filename, loc, cyclomatic, cnt_func, max_nesting, ratio_comment])
    return

#   Output results into a csv file
def outputResult():
    print('writing SNA results into csv ...')
    writer = csv.writer(open('sna_metrics_' + analytic_version + '.csv', 'w'))
    writer.writerow(['node', 'page_rank', 'betweenness', 'closeness', 'indegree', 'outdegree'])
    for i in range(0, len(node_list)):
        node_name = node_list[i]
        pagerank_value = round(pagerank_list[i] * 10**5, 3)
        betweenness_value = round(betweenness_list[i], 3)
        closeness_value = round(closeness_list[i] * 10**4, 3)
        indegree_value = indegree_list[i]
        outdegree_value = outdegree_list[i]
        writer.writerow([node_name, pagerank_value, betweenness_value, closeness_value, indegree_value, outdegree_value])
    return

if(__name__ == '__main__'):
    analytic_version = input('Please choose the analytic version:\n')
    product = input('Please choose the analytic product:\n')
    root_folder = product + analytic_version  
    # load the understand database
    print('Loading the database ...')
    db = understand.open(product + analytic_version + '.udb')
    #   create an adjacency matrix from the understand database
    (node_list, matrix_list) = createAdjacencyMatrix(db)
    #print(node_list)
    #   convert the adjacency matrix to a graph then compute the SNA metrics' values
    print('Computing graph metrics ...')
    g = Graph.Adjacency(matrix_list, mode=ADJ_DIRECTED)
    pagerank_list = g.pagerank()
    betweenness_list = g.betweenness()
    closeness_list = g.closeness()
    indegree_list = g.indegree()
    outdegree_list = g.outdegree()
        
    #   write the results into a csv file
    outputResult()
    
    codeMetrics(db)
    
    print('Done.')