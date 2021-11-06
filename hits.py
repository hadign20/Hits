# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 11:23:24 2019

@author: Hadi
"""
#from googlesearch import search 
try:
    import urllib.request as urllib2
except ImportError:
#except Exception:
    import urllib2 
from googlesearch import search   
from bs4 import BeautifulSoup
import urllib.parse
import io, re, math
import requests
from requests.exceptions import *
#from .excepts import *
#from .helpers import process_image_url
from webpreview import web_preview
import networkx as nx
import matplotlib.pyplot as plt



'''
##################################################
set parameters
##################################################
'''

searchQuery = "Big Data Analytics"
header = {'user-agent': 'Mozilla/5.0'}

rootSetFile = 'G:/My Drive/Sem2/DataMining/Projects/advanced/RootSet.txt'
baseSet1File = 'G:/My Drive/Sem2/DataMining/Projects/advanced/baseSet1.txt'
baseSet2File = 'G:/My Drive/Sem2/DataMining/Projects/advanced/baseSet2.txt'
allPages = 'G:/My Drive/Sem2/DataMining/Projects/advanced/allPgaes.txt'
adjfile = 'G:/My Drive/Sem2/DataMining/Projects/advanced/adjfile.txt'

online_search = 1 # 1 to search online, 0 to use file from memory
use_google_package = 1 # 1 to use google search library, 0 to use requests
saveToFile = 1
printNeighbourhood = 0 # 0 to avoid printing all pages in neighbourhood graph
printGraph = 1
seed = 30 # number of seed pages
error_rate = 0.0001

'''
##################################################
general variables and functions 
##################################################
'''

addedPages = [0]*seed # for the upper-bound k
nodes = []
adj = []

class URLopener(urllib2.FancyURLopener):
    version = "Mozilla/5.0"
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        if errcode == 403:
            raise ValueError("403")
        return super(URLopener, self).http_error_default(
            url, fp, errcode, errmsg, headers
        )

class node:
    def __init__(self, pageid, url, auth, hub):
        self.pageid = pageid
        self.url = url
        self.auth = auth
        self.hub = hub
             
def searchGoogle(query=None, times=0):
    search_results = search(query,tld="com", num=times, stop=times, pause=2);
    return search_results

def searchYahoo(query=None, times=0):
    query = re.sub(r"\s+", '+', query)
    yahoo = "https://search.yahoo.com/search?q=" + query + "&n=" + str(times)
    result=[]
    #opener = URLopener()
    try:
        #page = opener.open(urllib.parse.unquote(yahoo))
        page = urllib2.urlopen(yahoo)
        soup = BeautifulSoup(page, "lxml")
        #soup = BeautifulSoup(page.read(), features='lxml')
        #links = soup.find_all('a', href=True);
        #for link in links:
        for link in soup.find_all(attrs={"class": "ac-algo"}):
        #for link in soup.select("algo"):
            #if link.get('class') and "ac-algo" in link['class']:
            result.append(link.get('href'))
    except (HTTPError, ValueError):
    #except Exception:
        pass
    return(result)
    
def save_file(filename, savedlist):
    with io.open(filename, "w", encoding="utf-8") as f:    
            for item in savedlist:
                f.write("%s\n" % item)

def validLink(url): 
    wrong = ['facebook', 'twitter', 'linkedin', 'youtube', 'deeplearning4j', 'slideshare', 'doubleclick', 'ads', '.png', '.jpg', '.svg', '.png']
    validLink = bool(re.match(r'^(?:https?:\/\/)(?:[\w-]+)(?:\.[\w-]+)*\.[\w]+(?:\/[^\n]+)?$', url))
    invalidLink = bool(re.match(r'^.*\.(jpg|JPG|gif|GIF|doc|DOC|pdf|PDF)$',url))
    
    if (
            validLink == True and
            invalidLink == False and
            all(url.find(t)==-1 for t in wrong)
        ):
        return True
    else:
        return False
        
def getDomain(url):
    domain = url.split("//")[-1].split("/")[0]
    return domain


def getLinks(url):
    #page = opener.open(urllib.parse.unquote(i))
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page.read(), features='lxml')
    links = soup.findAll("a", href=True)
    #check for ads
    adLinks = soup.findAll("h3", {"class": "sA5rQ"})
    return links


def checkforAd (url):
    #check for ads
    query1 = query.replace(" ","+")
    url = "https://www.google.com/search?q="+query1
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page.read(), features='lxml')
    mydivs = soup.findAll("div", {"class": "sA5rQ"})
    
'''
##################################################
build root set
##################################################
'''

def build_root_set(query):
    RootSet = []
    count = 0
    
    if use_google_package:     
        
        search_results = searchGoogle(query, seed+10) #Getting 40 results if any duplicates
        for page in search_results:
            if not page in RootSet and count < seed and validLink(page):
                RootSet.append(page)
                node1 = node(count,page,1,1)
                nodes.append(node1) # add seed page to nodes
                adj.append([])
                count = count + 1    
    else:
        query = re.sub(r"\s+", '+', query)
        url = "https://www.google.com/search?q="+query+"&num=35" #Getting 35 results if any duplicates
        raw_page = requests.get(url, headers=header).text
        results = re.findall(r'(?<=<h3 class="r"><a href="/url\?q=).*?(?=&amp)', str(raw_page))
        RootSet = list(set(results))[0:30] #Provides 30 unique of the 35 we requested above
        for page in RootSet:
            if count < seed:
                node1 = node(count,page,1,1)
                nodes.append(node1) # add seed page to nodes
                adj.append([])
                count = count + 1
    
    if saveToFile: save_file(rootSetFile, RootSet)            
    return RootSet 

'''
##################################################
build first base set
##################################################
'''
        
def addLinkedPages(rootSet):
    seedIndex = 0
    baseSet1 = []
    opener = URLopener()
    
    for i in rootSet:
        try:
            page = opener.open(urllib.parse.unquote(i))
            soup = BeautifulSoup(page.read(), features='lxml')
            links = soup.findAll("a", href=True)
        except Exception:
            continue
        for link in links:     
            if validLink(link["href"]) and getDomain(link["href"]) != getDomain(i): 
                if link["href"] in rootSet or link["href"] in baseSet1: # page already exists in graph
                    for x in nodes:
                        if x.url == link["href"]: linkedNode = x
                    for y in nodes:
                        if y.url == i: linkingNode = y
                    if not linkedNode.pageid in adj[linkingNode.pageid]:
                        adj[linkingNode.pageid].append(linkedNode.pageid)
                else: # it is a new page
                    baseSet1.append(link["href"])
                    nodeid = len(rootSet) + len(baseSet1) - 1
                    node1 = node(nodeid,link["href"],1,1)
                    nodes.append(node1) # add page to graph
                    adj.append([])
                    for x in nodes:
                        if x.url == link["href"]: linkedNode = x
                    for y in nodes:
                        if y.url == i: linkingNode = y
                    if not linkedNode.pageid in adj[linkingNode.pageid]:
                        adj[linkingNode.pageid].append(linkedNode.pageid)
                    addedPages[seedIndex] = addedPages[seedIndex] + 1
            if addedPages[seedIndex] >= k: break
                
        seedIndex = seedIndex + 1
        if seedIndex > seed:
            break
    
    if saveToFile: save_file(baseSet1File, baseSet1)
    return baseSet1

'''
##################################################
Build second base set
##################################################
'''

def addLinkingPages(rootSet, baseSet1):
    seedIndex = 0
    baseSet2 = []
    
    for i in rootSet:
        
        query = "link:" + i
        limit = k - addedPages[seedIndex]
        urls = searchYahoo(query , limit)
        
        for j in urls:    
            if validLink(j) and getDomain(j) != getDomain(i):
                if j in rootSet or j in baseSet1 or j in baseSet2: # page already exists in graph
                    for x in nodes:
                        if x.url == j: linkingNode = x
                    for y in nodes:
                        if y.url == i: linkedNode = y
                    if not linkedNode.pageid in adj[linkingNode.pageid]:
                        adj[linkingNode.pageid].append(linkedNode.pageid)
                    
                else: # it is a new page
                    baseSet2.append(j)
                    nodeid = len(rootSet) + len(baseSet1) + len(baseSet2) - 1
                    node1 = node(nodeid,j,1,1)
                    nodes.append(node1) # add page to graph
                    adj.append([]) # add link to adjacency matrix
                    for x in nodes:
                        if x.url == i: linkingNode = x
                    for y in nodes:
                        if y.url == j: linkedNode = y
                    if not linkedNode.pageid in adj[linkingNode.pageid]:
                        adj[linkingNode.pageid].append(linkedNode.pageid)
                    addedPages[seedIndex] = addedPages[seedIndex] + 1 
            
            if addedPages[seedIndex] >= k: break
        
        seedIndex = seedIndex + 1
        if seedIndex > seed:
            break
    
    if saveToFile:
        save_file(baseSet2File, baseSet2)
        with open(adjfile, 'w') as file: # save adjacency list
            file.writelines('\t'.join(str(j) for j in i) + '\n' for i in adj)
            
    return baseSet2


'''
##################################################
Build Neighbourhood Graph
##################################################
'''

def buildWholeSet():
    
    rootSet = [] #list of seed pages
    
    if online_search==1:
        rootSet = build_root_set(searchQuery)
        baseSet1 = addLinkedPages(rootSet)
        baseSet2 = addLinkingPages(rootSet, baseSet1)
        wholeSet = rootSet + baseSet1 + baseSet2 
    
        if saveToFile:
            with io.open(allPages, "w", encoding="utf-8") as f: #save neighbourhood graph to file allPages
                for item in wholeSet:
                    f.write("%s\n" % item)
    else: # load from files
        rootFile = open(rootSetFile, "r")
        rootSet = rootFile.read().split('\n')
        
        base1File = open(baseSet1File, "r")
        baseSet1 = base1File.read().split('\n')
        
        base2File = open(baseSet2File, "r")
        baseSet2 = base2File.read().split('\n')
        
        allPagesFile = open(allPages, "r")
        wholeSet = allPagesFile.read().split('\n')
        
        infile = open(adjfile,'r')
        for line in infile:
            adj.append(line.strip().split('\t'))
        infile.close()
    
    return (wholeSet, adj)

'''
##################################################
Print search results
##################################################
'''

def print_desccriptions1(nodes,Nbound,k):
    count = 0
    if(len(nodes)== 0):
        print("No pages found. Enter an upperbound (k) higher than", k)
    while count < Nbound:
        try:
            title, description, image = web_preview(nodes[count].url)
            print(title,'\n', description ,'\n ((authority= {0:1.6f}'.format(nodes[count].auth) , " |||   hub= {0:1.6f}".format(nodes[count].hub),'))')
            print('-------------------------------------------------------------------------------------')
        #except (ConnectionError, HTTPError, Timeout, TooManyRedirects, InvalidURL, KeyError):
        except Exception:
            pass
        count = count + 1
'''    
def print_desccriptions(nodes,Nbound,k):
    
    descriptions = []
    
    count = 0
    if(len(nodes)== 0):
        print("No pages found. Enter an upperbound (k) higher than", k)
    else:
        print("There are less resulting searched pages than", Nbound)
        while count <= Nbound:
            print('********************************************', nodes[count].url)

            req = urllib.request.Request(nodes[count].url, headers=header)
            try:
                html = urllib2.urlopen(req)
            except:
                continue
            
            soup = BeautifulSoup(html, "lxml")
    
            title = soup.title.text
            metas = soup.find_all("meta")
            desc = [ meta.attrs['content'] for meta in metas if 'name' in meta.attrs and meta.attrs['name'] == 'description' ]
    
            if len(title) < 1:
                title = re.findall(r'^(?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^:\/\n]+)', nodes[count].url)
                title = title[0]
            if len(desc) < 1:
                desc = soup.p.text
            else:
                desc = desc[0]
    
            if len(desc) > 140:
                desc = desc[0:140]+'...'
    
            descriptions.append([title, nodes[count].url, desc, nodes[count].auth, nodes[count].hub])
            count = count + 1
     
        for dis in descriptions:
            print(dis[0],'\n', dis[1], '\n', dis[2],'\n', "((authority= {0:1.6f}".format(dis[3]) , " |||    hub= {0:1.6f}".format(dis[4],'))'))
            print('-------------------------------------------------------------------------------------')
'''         
            



def printPages(nodes,N,k):
    
    if printNeighbourhood==1:
        print('\n=============================================')
        print("    pages in the neighbourhood graph")
        print("==============================================")
        print_desccriptions1(nodes,len(nodes),k)
    
    nodes.sort(key=lambda x: x.auth, reverse=True)
    print('\n=============================================')
    print("    pages sorted by authority")
    print("==============================================")
    print_desccriptions1(nodes,N,k)
    
    nodes.sort(key=lambda x: x.hub, reverse=True)
    print('\n=============================================')
    print("    pages sorted by hub")
    print("==============================================")
    print_desccriptions1(nodes,N,k)
    
def mapping(x):
    return x + 100


def showGraph(nodes, adj):
    
    nodeList= []
    edgeList = []
    options = {
        'node_color': 'lavender',
        'node_size': 800,
        'width': 1,
        'arrowstyle': '-|>',
        'arrowsize': 20,
    }
    
    G = nx.DiGraph(directed=True)
    
    for node in nodes:
        nodeList.append(node.pageid)
    
    for i in range(len(adj)):
        for j in adj[i]:
            edgeList.append((i,j))
    
    G.add_nodes_from(nodeList)
    G.add_edges_from(edgeList) 
    
    nx.draw_networkx(G, arrows=True, with_labels = True, **options)
    if saveToFile: plt.savefig("graph.png") # save as png
    plt.show()
   
        

'''
##################################################
hits functions 
##################################################
'''

def converge(nodes, errorrate, auth, auth_prev, hub, hub_prev):
    counter = 0;
    for i in range(len(nodes)):
        if ((abs(auth[i] - auth_prev[i]) < errorrate) and (abs(hub[i] - hub_prev[i]) < errorrate)):
            counter = counter + 1;
    if counter == len(nodes): #converge if all differences are less than errorrate
        return 1
    else:
        return 0

def hits(nodes, adj, errorrate):
    converged = 0
    auth = []
    auth_prev = []
    hub = []
    hub_prev = []

    for p in nodes:
        p.auth = 1
        p.hub = 1
        auth.append(p.auth)
        hub.append(p.hub)
        auth_prev.append(p.auth)
        hub_prev.append(p.hub)
    
    while True:
        
        auth_prev = auth[:]
        hub_prev = hub[:]
        
        #update authority values first
        norm = 0
        for p in nodes: 
            #look in the adj list for incoming links to p
            incoming = []
            for i in range(len(adj)):
                if p.pageid in adj[i]:
                    incoming.append(i)
            
            for q in nodes:    # for q in p.incoming
                if q.pageid in incoming:
                    p.auth = p.auth + q.hub
            norm = norm + math.pow(p.auth,2) #calculate the sum of the squared auth values to normalise
        norm = math.sqrt(norm)
        
        for p in nodes:
            p.auth = p.auth / norm if norm else 1 #update the auth scores with normalization
            
        # update hub values
        norm = 0
        for p in nodes: 
            for q in nodes: # for q in p.outgoing
                if q.pageid in adj[p.pageid]:
                    p.hub = p.hub + q.auth
            norm = norm + math.pow(p.hub,2) #calculate the sum of the squared hub values to normalise
        norm = math.sqrt(norm)
        for p in nodes:
            p.hub = p.hub / norm if norm else 1 #update the hub scores with normalization
            #hub_prev[count] = p.hub
        
        for i in range(len(nodes)):
            auth[i] = nodes[i].auth
            hub[i] = nodes[i].hub
        
        converged = converge(nodes, errorrate, auth, auth_prev, hub, hub_prev)
        if (converged): break
    

'''
##################################################
main function
##################################################
'''

if __name__ == "__main__":
    
    k = int(input("define Upper bound for added pages (k): " or 5 )) # uper bound of added pages for each seed page 
    N = int(input("define Upper bound for printed pages (N): " or 5 )) # uper bound of added pages for each seed page 
    wholeSet, adj = buildWholeSet()
    hits(nodes, adj, error_rate)
    printPages(nodes,N,k)
    if printGraph:
        showGraph(nodes, adj)
    
    
        
        