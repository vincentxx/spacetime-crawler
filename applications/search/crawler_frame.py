import logging
from datamodel.search.Vuqt1Hoangt5Malaya_datamodel import Vuqt1Hoangt5MalayaLink, OneVuqt1Hoangt5MalayaUnProcessedLink
from spacetime.client.IApplication import IApplication
from spacetime.client.declarations import Producer, GetterSetter, Getter
from lxml import html,etree
import re, os
import time
from uuid import uuid4

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

@Producer(Vuqt1Hoangt5MalayaLink)
@GetterSetter(OneVuqt1Hoangt5MalayaUnProcessedLink)
class CrawlerFrame(IApplication):
    app_id = "Vuqt1Hoangt5Malaya"

    def __init__(self, frame):
        self.app_id = "Vuqt1Hoangt5Malaya"
        self.frame = frame


    def initialize(self):
        self.count = 0
        links = self.frame.get_new(OneVuqt1Hoangt5MalayaUnProcessedLink)
        if len(links) > 0:
            print "Resuming from the previous state."
            self.download_links(links)
        else:
            l = Vuqt1Hoangt5MalayaLink("http://www.ics.uci.edu/")
            print l.full_url
            self.frame.add(l)

    def update(self):
        unprocessed_links = self.frame.get_new(OneVuqt1Hoangt5MalayaUnProcessedLink)
        if unprocessed_links:
            self.download_links(unprocessed_links)

    def download_links(self, unprocessed_links):
        global subDomains_visited, visited_links, total_links_processed
        for link in unprocessed_links:
            print "Got a link to download:", link.full_url
            downloaded = link.download()
            visited_links.add(link.full_url)  # added code
            links = extract_next_links(downloaded)
            validlink = 0 #added variable
            for l in links:
                if is_valid(l):
                    #added code
                    validlink += 1
                    suburl = urlparse(l)
                    domains = suburl.hostname
                    if domains not in subDomains_visited:
                        subDomains_visited[domains] = 1
                    else:
                        subDomains_visited[domains] += 1
                    #end added code
                    self.frame.add(Vuqt1Hoangt5MalayaLink(l))
            #added code
            max_links_page[link.full_url] = validlink
            if(len(visited_links) > total_links_processed):
                self.analytic()
                print("--------------------!!! Crawler stopped !!!--------------------")
                raise KeyboardInterrupt
            #added code end

    def shutdown(self):
        print(
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
    # Skip if the page has error response such as 404, return empty
    if (rawDataObj.http_code > 399):
        bad_links.add(rawDataObj.url)
        return outputLinks

    # Checks if url has redirected, if yes then use the final link as root link
    if (rawDataObj.is_redirected):
        url = rawDataObj.final_url
        outputLinks.append(rawDataObj.final_url.encode('utf-8'))
    else:
        url = rawDataObj.url

    # If frontier returned a link which is not able to convert to utf-8
    try:
        soup = bs(rawDataObj.content, 'html.parser')  # ? feature
        rootLink = str(url)
    except:
        bad_links.add(rawDataObj.url)
        return outputLinks

    # Extract links from the content
    for link in soup.find_all('a'):
        try:
            pattern = str(link.get('href'))  # Throws exception if converting to UTF-8 is out of range: link.get() return unicode obj
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
    #print url

    if parsed.scheme not in set(["http", "https"]):
        bad_links.add(url)
        return False

    # look for calendar in path (trap)
    elif re.search(r'^.*calendar.*$', parsed.path):
        bad_links.add(url)
        return False

    # another trap
    elif (re.compile("calendar", re.IGNORECASE)).match(str(url)):
        print "BAD URL " + url
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

