from html.parser import HTMLParser
import queue
import sys
import threading

import requests


class HrefFinder(HTMLParser):
    '''parse html and find href value of all <a> tags'''
    hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for a in attrs:
                if a[0] == 'href':
                    self.hrefs.append(a[1])

    def get_hrefs(self):
        return self.hrefs

class App:
    '''
    Searches a site for all links checking to see if they work
    Thread starts a worker which takes a url from the Queue,
    then creates a request and constructs a list of links from the returned page.
    '''

    def __init__(self, **kwargs):
        self.max_workers = 5
        self.queue = queue.Queue()
        self.root_url = self.get_url_arg()
        self.queue.put(('', self.root_url,))

        # use to check if a url has been seen or not
        self.seen = set()

        # somewhere to store our results
        self.results = []

    def run(self):
        '''
        Main run method of the program
        creates threads and waits for them to complete
        '''
        print('\n#### Link Checker ####')
        print('checking: {}'.format(self.root_url))

        # create some threaded workers
        for _ in range(self.max_workers):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()

        # wait for tasks in queue to finish
        self.queue.join()

        print('DONE')
        for r in self.results:
            print(r)

    def get_url_arg(self):
        # Get command line argument or prompt user for url
        url = None
        if len(sys.argv) > 1:
            url = sys.argv[1]
        else:
            url = input("please enter a url:")
        return url

    def worker(self):
        while True:
            url = self.queue.get()
            try:
                res = requests.get(url[1])
                self.results.append((url[0], url[1], res.status_code, requests.status_codes._codes[res.status_code][0],))
                # check that the site we are hitting is the domain specified through sys.argv
                if self.root_url in url[1]:
                    all_links = self.get_a_tags(res)
                    for l in all_links:
                        # Make sure we have not already checked the url and add it to our
                        if l not in self.seen:
                            self.seen.add(l)
                            self.queue.put((url[1], l,))
                        else:
                            continue
            
            except Exception as e:
                # in case the http request fails due to bad url or protocol
                self.results.append((url[0], url[1], e))

            # our task is complete!
            self.queue.task_done()

    def get_a_tags(self, res):
        # feed response data to instance of HferFinder class
        parser = HrefFinder()
        parser.feed(res.text)
        return self.construct_urls(parser.get_hrefs())

    def construct_urls(self, hrefs):
        # Construct valid absolute urls from href links on the page
        links = []
        for h in hrefs:
            url = None

            if 'http' in h or 'https' in h:
                url = '' + h
            else:
                url = self.root_url + h

            if url and 'mailto:' not in url:
                links.append(url)
            else:
                pass

        return links


if __name__ == '__main__':
    app = App()
    app.run()
