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

inputFile = 'edge-seq-cong-prob.txt'
outputDir = 'edge-seq-cong-prob'

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
linkSeqLinks = []
linkSeqTypes = []
# list[linkSeq] of dict[class] -> list of float
linkSeqClassValues = []

with open (inputFile, "r") as myfile:
  for line in myfile.read().split('\n'):
    if not line:
      continue
    tokens = line.split('\t')
    if tokens[0] == 'Experiment':
      # Experiment	long-policing-1	interval	0.1
      experimentName = tokens[1]
      intervalSize = tokens[3]
    elif tokens[0] == 'Link sequence':
      # Link sequence	neutrality	neutral	links	2	4
      linkSeqTypes.append(tokens[2])
      linkSeqLinks.append([int(token) for token in tokens[4:]])
      linkSeqClassValues.append({})
    elif tokens[0] == 'Class':
      # Class 1	1.1256	1.22113
      # Class 2	2.06498	1.97177
      # Class 1+2	0.913869	0.808522 0.901636
      linkSeqClassValues[-1][tokens[1]] = [min(100.0, 100.0 - float(token)) for token in tokens[2:]]

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
for e in range(len(linkSeqLinks)):
  for c in linkSeqClassValues[e].keys():
    for prob in linkSeqClassValues[e][c]:
      probMin = min(probMin, prob)
probMin = int(0.999 * probMin * 500) / 500.0 - 0.1

plot = {}
#plot['title'] = '{0} link sequence: {1}'.format(linkSeqTypes[e].capitalize(), ' '.join([str(x) for x in linkSeqLinks[e]]))
plot['xLabel'] = 'Link sequence'
plot['yLabel'] = 'Estimated prob.\nof non-congestion [\\%]'
plot['fontScale'] = 2.5
plot['grid'] = ''
plot['xmin'] = 0.5
plot['xmax'] = 0.5
plot['ymin'] = probMin
plot['ymax'] = 100.1
plot['minorXTicks'] = 0
plot['majorXTicks'] = 0
plot['noLegend'] = 1
#
plot['data'] = []
plot['xTicks'] = []
plot['xTickLabels'] = []
plot['xTickRotation'] = 90
plot['xTicks'].append(0)
plot['xTickLabels'].append('')
plot['majorXTicks'] = plot['majorXTicks'] + 1
majorIndex = 1
for e in range(len(linkSeqLinks)):
  plot['xTickLabels'].append(str(e + 1) + ('' if linkSeqTypes[e] == 'neutral' else '*') + ' (' + ', '.join([str(link) for link in linkSeqLinks[e]]) + ')')
  plot['majorXTicks'] = plot['majorXTicks'] + 1
  plot['xmax'] = plot['xmax'] + 1
  box = {}
  box['type'] = 'boxplot'
  box['x'] = []
  box['positions'] = []
  box['w'] = 0.25
  color = [0.667, 1.0, 0.7] if linkSeqTypes[e] == 'neutral' else [0.0, 1.0, 0.7]
  box['boxColor'] = color
  box['medianColor'] = color
  box['whiskerColor'] = color
  box['capColor'] = color
  box['outlierColor'] = color
  box['outlierMarker'] = '+'
  minorOffset = - box['w'] / 2.0
  for c in naturalSorted(linkSeqClassValues[e].keys()):
    box['x'].append(linkSeqClassValues[e][c])
    box['positions'].append(majorIndex + minorOffset)
    minorOffset = minorOffset + box['w']
  plot['xTicks'].append(majorIndex)
  plot['data'].append({
    "type": "line",
    "y": [plot['ymin'], plot['ymax']],
    "x": [majorIndex - 0.5, majorIndex - 0.5],
    "pattern": ":",
    "label": "",
    "color": [0.0, 0.0, 0.7]
    })
  plot['data'].append(box)
  majorIndex = majorIndex + 1
plot['majorXTicks'] = plot['majorXTicks'] + 1
plot['data'].append({
  "type": "line",
  "x": [plot['xmin'], plot['xmax']],
  "y": [100.0, 100.0],
  "pattern": ":",
  "label": "",
  "color": [0.0, 0.0, 0.7]
  })
plot['w'] = 30
plot['h'] = 10

plot['fileName'] = outputDir + '/' + 'link-seq-cong-prob-all.eps'
plot['fileName'] = plot['fileName'].replace('\\', ' ')
plot['fileName'] = plot['fileName'].replace('%', ' ')
with open(plot['fileName'] + '.json', 'wb') as f:
  json.dump(plot, f, sort_keys=True, indent=4, separators=(',', ': '))
nicePlot(plot)
print plot['fileName']

plot['fileName'] = outputDir + '/' + 'link-seq-cong-prob-all.png'
plot['fileName'] = plot['fileName'].replace('\\', ' ')
plot['fileName'] = plot['fileName'].replace('%', ' ')
plot['dpi'] = 50
with open(plot['fileName'] + '.json', 'wb') as f:
  json.dump(plot, f, sort_keys=True, indent=4, separators=(',', ': '))
nicePlot(plot)
print plot['fileName']

exit()
