#!/usr/bin/env python2

# Install dependencies:
# sudo apt-get install python-matplotlib dvipng

import colorsys
import getopt
import json
from nicePlot import nicePlot
import math
import numpy
import os
import pprint
import re
import subprocess
import sys

def isNumber(s):
  try:
    float(s)
    return True
  except ValueError:
    return False

def toBase64JS(filename):
  return '"' + open(filename, 'rb').read().encode('base64').replace('\n', '" + \n"') + '"'

## Natural sorting (e.g.: asdf7, asdf8, asdf9, asdf10, ...)
# ref: http://stackoverflow.com/questions/4836710
def naturalSorted(l):
  convert = lambda text: int(text) if text.isdigit() else text.lower()
  alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
  return sorted(l, key = alphanum_key)

def reversed(l):
  l2 = l
  l2.reverse()
  return l2

def sortCongestion(l):
  convert = lambda text: int(1) if text == 'no1' else int(2) if text == 'no2' else int(3) if text == 'no3' else int(4) if text == 'lo' else int(5) if text == 'me' else int(6) if text == 'hi' else text
  keyfunc = lambda key: [ convert(c) for c in re.split('/', key) ]
  return sorted(l, key = keyfunc)

def mean(l):
  return sum(l)/len(l) if len(l) > 0 else 0

def timestampStr2us(str):
  # '   0   0s   0m  98u 542n'
  tokens = [float(re.sub('[a-z]', '', word)) for word in str.split()]
  return tokens[0] * 1.0e9 + tokens[1] * 1.0e6 + tokens[2] * 1.0e3 + tokens[3] * 1.0e0 + tokens[4] * 1.0e-3


## Params

inputFile = 'edge-class-path-cong-prob.txt'
outputDir = 'edge-class-path-cong-prob'

try:
  opts, args = getopt.getopt(sys.argv[1:], '', ['in=', 'out='])
except getopt.GetoptError as err:
  # print help information and exit:
  print str(err) # will print something like "option -a not recognized"
  sys.exit(2)
for opt, arg in opts:
  if opt == '--in':
    inputFile = arg
  elif opt == '--out':
    outputDir = arg
  else:
    assert False, "Unhandled option: " + str(opt)

print 'Arguments:'
print 'Input file:', inputFile

## End of params

experimentName = ''
intervalSize = ''
# dict[link] of type
linkTypes = {}
# dict[link] of dict[class] -> list of float
linkClassValues = {}

linkName = ''
with open (inputFile, "r") as myfile:
  for line in myfile.read().split('\n'):
    if not line:
      continue
    tokens = line.split('\t')
    if tokens[0] == 'Experiment':
      # Experiment	long-policing-1	interval	0.1
      experimentName = tokens[1]
      intervalSize = tokens[3]
    elif tokens[0] == 'Link':
      # Link	1	n
      linkName = tokens[1]
      linkTypes[linkName] = tokens[2]
      linkClassValues[linkName] = {}
    elif tokens[0] == 'Class':
      # Class	1	0.0109439	0.011855	0.0120234	0.0112965
      # Class	2
      linkClassValues[linkName][tokens[1]] = [100.0 - float(token) for token in tokens[2:]]

## End of data reading

## Plot

try:
  os.makedirs(outputDir)
except OSError as exception:
  pass

# Cleanup target dir
print 'Cleaning up target directory (%s)...' % outputDir
args = ['bash', '-c', '''cd '%s' && ls -1 | grep -E '.*.(pdf|png|json)$' | while read -r f ; do rm -fv "$f" ; done || echo "Could not change dir to %s"''' % (outputDir, outputDir) ]
print(args)
subprocess.call(args)

# [left, bottom, width, height]
figureBorder = [0.10, 0.20, 0.80, 0.70]

probMin = 100.0
for e in linkClassValues:
  for c in linkClassValues[e].keys():
    for prob in linkClassValues[e][c]:
      probMin = min(probMin, prob)

plot = {}
plot['xLabel'] = 'Link (left box: paths from class 1; right box: paths from class 2)'
plot['yLabel'] = 'Prob. of non-congestion [\\%]'
plot['fontScale'] = 2.5
plot['grid'] = ''
plot['xmin'] = 0
plot['xmax'] = 1
plot['ymin'] = probMin
plot['ymax'] = 100.1
plot['minorXTicks'] = 0
plot['majorXTicks'] = 0
plot['noLegend'] = 1
#
plot['data'] = []
box = {}
box['type'] = 'boxplot'
box['x'] = []
box['positions'] = []
box['w'] = 0.25
plot['xTickLabels'] = []
plot['xTickLabels'].append('')
plot['majorXTicks'] = plot['majorXTicks'] + 1
majorIndex = 1
for e in [1, 2, 3, 4, 5, 9, 12, 13, 14, 19, 20]:
  e = str(e)
  plot['xTickLabels'].append(e)
  plot['majorXTicks'] = plot['majorXTicks'] + 1
  plot['xmax'] = plot['xmax'] + 1
  minorOffset = - box['w'] / 2.0
  for c in naturalSorted(linkClassValues[e].keys()):
    box['x'].append(linkClassValues[e][c])
    box['positions'].append(majorIndex + minorOffset)
    minorOffset = minorOffset + box['w']
  plot['data'].append({
    "type": "line",
    "y": [plot['ymin'], plot['ymax']],
    "x": [majorIndex, majorIndex],
    "pattern": ":",
    "label": "",
    "color": [0.0, 0.0, 0.7]
    })
  majorIndex = majorIndex + 1
plot['majorXTicks'] = plot['majorXTicks'] + 1
plot['data'].append(box)
plot['data'].append({
  "type": "line",
  "x": [plot['xmin'], plot['xmax']],
  "y": [100.0, 100.0],
  "pattern": ":",
  "label": "",
  "color": [0.0, 0.0, 0.7]
  })
plot['fileName'] = outputDir + '/' + 'class-path-cong-probs-links.eps'
plot['fileName'] = plot['fileName'].replace('\\', ' ')
plot['fileName'] = plot['fileName'].replace('%', ' ')
plot['w'] = 30
plot['h'] = 8
with open(plot['fileName'] + '.json', 'wb') as f:
  json.dump(plot, f, sort_keys=True, indent=4, separators=(',', ': '))
  pass
nicePlot(plot)
print plot['fileName']

exit()
