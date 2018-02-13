#!/usr/bin/env python3

import configparser
import re
import requests
from operator import itemgetter
import matplotlib.pyplot as plt
from matplotlib import interactive

config = configparser.ConfigParser()
config.read('config.ini')

ticker1 = config['DEFAULT']['Ticker1']
ticker2 = config['DEFAULT']['Ticker2']
small = int(config['DEFAULT']['SmallIntervalSize'])
large = int(config['DEFAULT']['LargeIntervalSize'])
days = int(config['DEFAULT']['RecentDays'])

print('Making request for', ticker1, '...')

a = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY'
+ '&outputsize=full&apikey=6CITKGABXG4P8ZUH&symbol=' + ticker1).text

print('Making request for', ticker2, '...')

b = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY'
+ '&outputsize=full&apikey=6CITKGABXG4P8ZUH&symbol=' + ticker2).text

print("Parsing values...")
pricesa = []
pricesb = []
volumesa = []
volumesb = []
linesa = a.splitlines()
linesa.reverse()
linesb = b.splitlines()
linesb.reverse()
filt = re.compile('2[0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
filt1 = re.compile('4\. close')
filt2 = re.compile('5\. volume')
for line in linesa:
    # find all domains in each line
    ls = filt.findall(line)
    if len(ls) != 0:
        #print(ls[0] + ',', prices[-1])
        pass
    ls = filt1.findall(line)
    if len(ls) != 0:
        deci = line[25:31].find('.')
        pricesa.append((float)(line[25:deci+29]))
    ls = filt2.findall(line)
    if len(ls) != 0:
        deci = line.find('v')
        volumesa.append(int(line[deci+10:-1]))

for line in linesb:
    # find all domains in each line
    ls = filt.findall(line)
    if len(ls) != 0:
        #print(ls[0] + ',', prices[-1])
        pass
    ls = filt1.findall(line)
    if len(ls) != 0:
        deci = line[25:31].find('.')
        pricesb.append((float)(line[25:deci+29]))
    ls = filt2.findall(line)
    if len(ls) != 0:
        deci = line.find('v')
        volumesb.append(int(line[deci+10:-1]))

print(len(pricesa), 'data points processed for', ticker1, 'and', len(pricesb), 'data points processed for', ticker2)

filea = open('out.csv', 'w')
for i in range(min(len(pricesa), len(pricesb))):
    filea.write(str(pricesa[i])+', '+str(pricesb[i])+', '+str(volumesa[i])+', '+str(volumesb[i])+'\n')

print('All prices and volumes written to csv file')

chunksizestr = input('Small ('+str(small)+') or large ('+str(large)+') chunks: ')
chunksize = 0
if chunksizestr.lower() == 'small':
    chunksize = small
elif chunksizestr.lower() == 'large':
    chunksize = large
else:
    exit()

origpricesa = pricesa
origpricesb = pricesb
pricesa = pricesa[:-1*chunksize]
pricesb = pricesb[:-1*chunksize]

print('Matching', chunksizestr, 'correlation chunks, set size', chunksize, 'total size', days)
selectedtriples = []
varaverage = 0.0
for i in range(len(pricesa)-days, len(pricesa)-chunksize):
    print('Set', i, 'matching')
    settriples = []
    for j in range(len(pricesb)-days, len(pricesb)-chunksize):
        percents = []
        for k in range(1, chunksize):
            percents.append((float)(pricesa[i+k]-pricesa[i+k-1])/pricesa[i+k])
            percents[-1] -= (float)(pricesb[j+k]-pricesb[j+k-1])/pricesb[j+k]
            percents[-1] = abs(percents[-1])
        settriples.append([i, j, sum(percents)])
    settriples.sort(key=itemgetter(2))

    print('Set', i, 'lowest, highest, average of '+str(len(settriples))+'matching absolute-variance sums:')
    sumtriples = 0.0
    for j in range(len(settriples)):
        sumtriples += settriples[j][2]
    varaverage += sumtriples/len(settriples)
    print(str(settriples[0])+',', str(settriples[-1])+',', str(sumtriples/len(settriples)))
    selectedtriples.append(settriples[0])

selectedtriples.sort(key=itemgetter(2))
print('Lowest absolute-variance sum:', selectedtriples[0], 'Average absolute-variance sum:', varaverage/len(settriples))

input()

xa = range(len(pricesa)-days, len(pricesa))
plt.plot(xa, pricesa[len(pricesa)-days:])
interactive(True)
plt.show()

plt.figure()
plt.plot(xa, pricesb[len(pricesb)-days:])
plt.show()

plt.figure()
xb = range(selectedtriples[0][0], selectedtriples[0][0]+chunksize)
plt.plot(xb, pricesa[selectedtriples[0][0]:selectedtriples[0][0]+chunksize])
plt.show()

plt.figure()
xc = range(selectedtriples[0][1], selectedtriples[0][1]+chunksize)
plt.plot(xc, pricesb[selectedtriples[0][1]:selectedtriples[0][1]+chunksize])
plt.show()

input('Show next '+str(chunksize)+' days')

origi = selectedtriples[0][0]
origj = selectedtriples[0][1]
percents = []
for k in range(1, chunksize):
    percents.append((float)(origpricesa[origi+chunksize+k]-origpricesa[origi+chunksize+k-1])/origpricesa[origi+chunksize+k])
    percents[-1] -= (float)(origpricesb[origj+chunksize+k]-origpricesb[origj+chunksize+k-1])/origpricesb[origj+chunksize+k]
    percents[-1] = abs(percents[-1])
print('Absolute-variance sum:', sum(percents))

plt.figure()
xb = range(selectedtriples[0][0]+chunksize, selectedtriples[0][0]+chunksize+chunksize)
plt.plot(xb, origpricesa[selectedtriples[0][0]+chunksize:selectedtriples[0][0]+chunksize+chunksize])
plt.show()

plt.figure()
xc = range(selectedtriples[0][1]+chunksize, selectedtriples[0][1]+chunksize+chunksize)
plt.plot(xc, origpricesb[selectedtriples[0][1]+chunksize:selectedtriples[0][1]+chunksize+chunksize])
interactive(False)
plt.show()
