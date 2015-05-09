# -*- coding: utf-8 -*-
"""
Created on Mon Sep 29 18:19:33 2014

@author: Teddy
"""
import csv

def loadDeck(fullpath):
    with open(fullpath, "rt") as f:
        reader = csv.reader(f, delimiter=',', skipinitialspace=True)
        
        lineData = list()
        
        cols = next(reader)
        #print(cols)
        
        for col in cols:
            # Create a list in lineData for each column of data.
            lineData.append(list())
            #print str(lineData)+'\n\n'
            #print lineData

        for line in reader:
            # Copy the data from the line into the correct columns.
            lineData[0].append(line[0].replace('\xe2\x80\x99',"'"))
            lineData[1].append(int(line[1]))
            #print str(lineData)+'\n\n'
        #print lineData
  
        data = dict()
        
        for i in range(len(lineData[0])):
            data[lineData[0][i]] = lineData[1][i]
        
        #for i in xrange(0, len(cols)):
            # Create each key in the dict with the data in its column.
        #    data[cols[i]] = lineData[i]
    
    return data, sum(data.values())

if __name__ == '__main__':
    fullpath     = "/home/teddy/Documents/Magic/Decks/Deck_Example.txt"
    deck_data, deck_size = loadDeck(fullpath)
    print deck_data
    print deck_size
