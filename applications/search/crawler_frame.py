import logging
from datamodel.search.Malaya_datamodel import MalayaLink, OneMalayaUnProcessedLink
from spacetime.client.IApplication import IApplication
from spacetime.client.declarations import Producer, GetterSetter, Getter
from lxml import html,etree
import re, os
from time import time
from uuid import uuid4

from bs4 import SoupStrainer 
from urlparse import urlparse, parse_qs, urljoin
from uuid import uuid4

from bs4 import BeautifulSoup as bs
import re, operator

#-------------------------------- Simple Database
visited_links = set()
subDomains_visited = dict()
max_links_page = {}
bad_links = set()
total_links_processed = 5000
#---------------------------------

logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"

@Producer(MalayaLink)
@GetterSetter(OneMalayaUnProcessedLink)
class CrawlerFrame(IApplication):
    app_id = "Malaya"

    def __init__(self, frame):
        self.app_id = "Malaya"
        self.frame = frame


    def initialize(self):
        self.count = 0
        links = self.frame.get_new(OneMalayaUnProcessedLink)
        if len(links) > 0:
            print "Resuming from the previous state."
            self.download_links(links)
        else:
            l = MalayaLink("http://www.ics.uci.edu/")
            print l.full_url
            self.frame.add(l)

    def update(self):
        unprocessed_links = self.frame.get_new(OneMalayaUnProcessedLink)
        if unprocessed_links:
            self.download_links(unprocessed_links)

    def download_links(self, unprocessed_links):

        for link in unprocessed_links:
            print "Got a link to download:", link.full_url
            downloaded = link.download()
            links = extract_next_links(downloaded)
            for l in links:
                if is_valid(l):
                    self.frame.add(MalayaLink(l))

    def shutdown(self):
        print (
            "Time time spent this session: ",
            time() - self.starttime, " seconds.")
    
    def analytic(self):
            # All coded are added
            # Create Analytic text file
            output_file = open("Analytics.txt", "w")
            output_file.write("Team 55 - Analytic:\n")
            output_file.write("***************************************************************\n")

            list_of_max_links = sorted(max_links_page.items(), key=operator.itemgetter(1), reverse=True)
            output_file.write("\nPage have the most outlinks: " + list_of_max_links[0][0] + "\n")
            output_file.write("Total: " + str(list_of_max_links[0][1]) + "\n")
            output_file.write("\n***************************************************************\n")
            for key, value in sorted(subDomains_visited.items()):
                output_file.write("Subdomain: " + key + "\n")
                output_file.write("Subdomain URLS: " + str(value) + "\n\n")
            output_file.close()

            # Create a text file with all BAD links
            output_file1 = open("bad_link.txt", "w")
            output_file1.write("LIST OF THE BAD LINKS: \n")
            output_file1.write("***************************************************************\n")
            for item in bad_links:
                output_file1.write(item + "\n")
            output_file1.close()

    def shutdown(self):
        print (
            "Time time spent this session: ",
            time() - self.starttime, " seconds.")
    
def extract_next_links(rawDataObj):
    global subDomains_visited  # dict
    global max_links_page  # dict
    global bad_links  # set
    global visited_links  # set

    outputLinks = []
    '''
    rawDataObj is an object of type UrlResponse declared at L20-30
    datamodel/search/server_datamodel.py
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.
    
    Suggested library: lxml
    '''
    if (rawDataObj.is_redirected):  # Checks if url has redirected
        url = rawDataObj.final_url
        try:
            outputLinks.append(rawDataObj.final_url.encode('utf-8'))
        except:
             bad_links.add(rawDataObj.final_url)

    else:
        url = rawDataObj.url
    if (rawDataObj.http_code > 399): 
        return outputLinks

    soup = bs(rawDataObj.content, parse_only=SoupStrainer('a'))  # ? feature
    rootLink = str(rawDataObj.url)
    for link in soup.find_all('a'):
        try:
            pattern = str(link.get('href'))
            #print "origin pattern: " + pattern
            if (re.compile('^http')).match(pattern):
                outputLinks.append(pattern)
            elif (re.compile('^//')).match(pattern):
                outputLinks.append(urljoin(rootLink, pattern, True))
            elif (re.compile("^/")).match(pattern):
                outputLinks.append(urljoin(rootLink, pattern, True))    
        except:
             bad_links.add(link.get('href'))
             continue
    return outputLinks
    '''
    if (rawDataObj.http_code > 399):  # Contains error code
        return outputLinks
    soup = bs(rawDataObj.content.decode('utf-8'), 'lxml')
    for tagObj in soup.find_all('a'):
        if (tagObj.attrs.has_key('href')):
            # print(tagObj['href'].encode('utf-8'))
            outputLinks.append(urljoin(url.decode('utf-8'), tagObj['href']).encode('utf-8'))
    return outputLinks
    '''

def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be
    downloaded or not.
    Robot rules and duplication rules are checked separately.
    This is a great place to filter out crawler traps.
    '''
    global subDomains_visited  # dict
    global max_links_page  # Tuple
    global bad_links  # sets
    global visited_links  # sets

    if url in visited_links:
        return False
    elif len(url) > 100:
        bad_links.add(url)
        return False

    # parse url string to url object
    parsed = urlparse(url)

    if parsed.scheme not in set(["http", "https"]):
        bad_links.add(url)
        return False

    # look for calendar in path (trap)
    elif re.search(r'^.*calendar.*$', parsed.path):
        bad_links.add(url)
        return False

    # another trap
    elif re.search(r'^.*ganglia.*$', parsed.path):
        bad_links.add(url)
        return False

    # regx for Repeating Directories:
    elif re.search(r'^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$', parsed.path):
        bad_links.add(url)
        return False

    try:
        if ".ics.uci.edu" in parsed.hostname and not re.match(
                ".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4" \
                + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
                + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
                + "|thmx|mso|arff|rtf|jar|csv" \
                + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf)$", parsed.path.lower()):
            visited_links.add(url)
            return True
        else:
            bad_links.add(url)
            return False

    except TypeError:
        print("TypeError for ", parsed)
        return False

    finally:
        bad_links.add(url)

