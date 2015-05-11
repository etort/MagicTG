"""
pic_grab.py
    Downloads all the images on the supplied URL, and saves them to the
    specified output file ("/test/" by default)
"""

from bs4 import BeautifulSoup as bs
import urlparse
from urllib2 import urlopen
from urllib import urlretrieve
import os
import sys

def download_pic(ID, out_folder='cache/', url_base='http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid='):
    """Downloads all the images at 'url' to /test/"""
    ID    = str(ID)
    url   = url_base+ID
    soup  = bs(urlopen(url))
    count = 1

    image_extensions = [".png", ".jpg", ".jpeg"]
    #print "LOOK HERE: " + str(soup.findAll('img')[0])
    for image in soup.findAll("img")[2:3]:
        imgurl = image["src"]
        if not imgurl.startswith("http://"):
            imgurl = urlparse.urljoin(url, imgurl)
        #print "Image URL: " + imgurl

        result = urlopen(imgurl)
        filename = image["src"].split("/")[-1]

        rename = True
        for ext in image_extensions:
            if image["src"].endswith(ext):
                rename = False

        if rename:
            file_extension = result.info().gettype().split("/")[-1]
            filename = ID + "." + file_extension
            count = count + 1

        #print "Image filename: " + filename

        data = result.read()
        output = open(os.path.join(out_folder, filename), "w")
        output.write(data)
        output.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        id = sys.argv[1]


