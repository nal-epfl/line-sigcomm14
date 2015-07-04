#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Install dependencies:
# sudo pip install matplotlib

import colorsys
import copy
import getopt
import json
from nicePlot import nicePlot
from line import *
import math
import numpy
import os
import pprint
import re
import subprocess
import sys

## Params

inputFile = 'edge-seq-cong-prob.txt'
outputDir = 'edge-seq-cong-prob'
natural = True
removeRedundant = False

try:
  opts, args = getopt.getopt(sys.argv[1:], '', ['in=', 'out=', 'natural', 'removeRedundant'])
except getopt.GetoptError as err:
  # print help information and exit:
  print str(err) # will print something like "option -a not recognized"
  sys.exit(2)
for opt, arg in opts:
  if opt == '--in':
    inputFile = arg
  elif opt == '--out':
    outputDir = arg
  elif opt == '--natural':
    natural = True
  elif opt == '--removeRedundant':
    removeRedundant = True
  else:
    assert False, "Unhandled option: " + str(opt)

print 'Arguments:'
print 'Input file:', inputFile
print 'Output dir:', outputDir

## End of params

data = readSeqData(inputFile, removeRedundant, natural)

## End of data reading

## Plot

try:
  os.makedirs(outputDir)
except OSError as exception:
  pass

# Cleanup target dir
print 'Cleaning up target directory (%s)...' % outputDir
args = ['bash', '-c', '''cd '%s' && ls -1 | grep -E '.*.(pdf|png|json|eps)$' | while read -r f ; do rm -fv "$f" ; done || echo "Could not change dir to %s"''' % (outputDir, outputDir) ]
print(args)
subprocess.call(args)

# [left, bottom, width, height]
figureBorder = [0.10, 0.20, 0.80, 0.70]

probMax = 2.0
for e in range(len(data.linkSeqLinks)):
  print data.linkSeqLinks[e]
  for c in data.linkSeqClassValues[e].keys():
    for prob in data.linkSeqClassValues[e][c]:
      probMax = max(probMax, prob)
    for prob in data.linkSeqClassTruth[e][c]:
      probMax = max(probMax, prob)
probMax2 = int(probMax * 100) / 100.0
if probMax2 - probMax < 0.4:
  probMax2 = probMax2 + 0.5
probMax = probMax2

for graph in ["truth", "inferred"]:
  plot = {}
  #plot['title'] = '{0} link sequence: {1}'.format(linkSeqTypes[e].capitalize(), ' '.join([str(x) for x in linkSeqLinks[e]]))
  plot['xLabel'] = 'Link sequence'
  plot['yLabel'] = 'Probability of congestion\n({}) [\\%]'.format(graph)
  plot['fontScale'] = 1.0
  plot['grid'] = ''
  plot['xmin'] = 0.5
  plot['xmax'] = 0.5
  plot['ymin'] = -0.5
  plot['ymax'] = probMax
  plot['minorXTicks'] = 0
  plot['majorXTicks'] = 0
  plot['noLegend'] = 1
  #
  plot['data'] = []
  plot['xTicks'] = []
  plot['xTickLabels'] = []
  plot['xTickRotation'] = 30
  plot['xTicks'].append(0)
  plot['xTickLabels'].append('')
  plot['majorXTicks'] = plot['majorXTicks'] + 1
  majorIndex = 1
  for e in data.sortedSequences:
    #plot['xTickLabels'].append(', '.join([str(link) + ('' if link not in data.nonNeutralLinks else '*') for link in data.linkSeqLinks[e]]))
    plot['xTickLabels'].append(', '.join(['\\textcolor[rgb]{' + ('0,0,0' if link not in data.nonNeutralLinks else '0.7,0,0') + '}{' + str(link) + '}' for link in data.linkSeqLinks[e]]))
    plot['majorXTicks'] = plot['majorXTicks'] + 1
    plot['xmax'] = plot['xmax'] + 1
    box = {}
    box['type'] = 'boxplot'
    box['x'] = []
    box['positions'] = []
    box['w'] = 0.25
    color = [0.618, 0.75, 0.95] if data.linkSeqTypes[e] == 'neutral' else [0.0, 0.75, 0.95]
    box['boxColor'] = color
    box['medianColor'] = color
    box['whiskerColor'] = color
    box['capColor'] = color
    box['outlierColor'] = color
    box['outlierMarker'] = '+'
    box['lineWidth'] = 1.0
    minorOffset = - box['w'] / 2.0
    for c in naturalSorted(data.linkSeqClassValues[e].keys()):
      if graph == "inferred":
        box['x'].append(data.linkSeqClassValues[e][c])
      elif graph == "truth":
        box['x'].append(data.linkSeqClassTruth[e][c])
      elif graph == "delta":
        box['x'].append([data.linkSeqClassValues[e][c][i] - data.linkSeqClassTruth[e][c][i] for i in range(len(data.linkSeqClassValues[e][c]))])
      elif graph == "errorPath1":
        box['x'].append(data.linkSeqClassErrorPath1[e][c])
      elif graph == "errorPath2":
        box['x'].append(data.linkSeqClassErrorPath2[e][c])
      elif graph == "errorExternal":
        box['x'].append(data.linkSeqClassErrorExternal[e][c])
      elif graph == "errorInternal":
        box['x'].append(data.linkSeqClassErrorInternal[e][c])
      elif graph == "errorInternal1":
        box['x'].append(data.linkSeqClassErrorInternal1[e][c])
      elif graph == "errorInternal2":
        box['x'].append(data.linkSeqClassErrorInternal2[e][c])
      else:
        raise Exception("oops")
      box['positions'].append(majorIndex + minorOffset)
      minorOffset = minorOffset + box['w']
    plot['xTicks'].append(majorIndex)
    plot['data'].append({
      "type": "line",
      "y": [min(-10.0, plot['ymin']), max(110.0, plot['ymax'])],
      "x": [majorIndex - 0.5, majorIndex - 0.5],
      "pattern": ":",
      "label": "",
      "color": [0.0, 0.0, 0.7],
      "lineWidth": 1.0
      })
    plot['data'].append(box)
    majorIndex = majorIndex + 1
  plot['majorXTicks'] = plot['majorXTicks'] + 1
  for y in range(0 if not graph.startswith("error") and graph != "delta" else -100, 101, 25 if graph.startswith("error") else 1 if plot['ymax'] < 8 else 2 if plot['ymax'] < 16 else 5 if plot['ymax'] < 40 else 10):
    plot['data'].insert(0, {
      "type": "line",
      "x": [plot['xmin']-10, plot['xmax']+10],
      "y": [y, y],
      "pattern": ":",
      "label": "",
      "color": [0.0, 0.0, 0.7],
      "lineWidth": 1.0
      })
  plot['w'] = 2 + len(data.sortedSequences) / 2
  plot['h'] = 3
  if graph.startswith("error"):
    plot['ymin'] = -110
    plot['ymax'] = 110
  elif graph == "delta":
    plot['ymin'] = -probMax
    plot['ymax'] = probMax

  plot['fileName'] = outputDir + '/' + 'link-seq-cong-prob-all-' + graph + '.png'
  plot['fileName'] = plot['fileName'].replace('\\', ' ')
  plot['fileName'] = plot['fileName'].replace('%', ' ')
  #plot['dpi'] = 50
  with open(plot['fileName'] + '.json', 'wb') as f:
    json.dump(plot, f, sort_keys=True, indent=4, separators=(',', ': '))
  nicePlot(plot)
  print plot['fileName']

for graph in ["truth", "inferred"]:
  plot = {}
  #plot['title'] = '{0} link sequence: {1}'.format(data.linkSeqTypes[e].capitalize(), ' '.join([str(x) for x in data.linkSeqLinks[e]]))
  plot['xLabel'] = 'Probability of congestion\n({}) [\\%]'.format(graph)
  plot['yLabel'] = 'Frequency'
  plot['fontScale'] = 1.0
  plot['grid'] = ''
  plot['noLegend'] = 1
  #
  plot['data'] = []
  histogram = {
    "type": "histogram",
    "x": [[], []],
    "colors": [[0.618, 0.75, 0.95], [0.0, 0.75, 0.95]]
  }
  if graph == "inferred" or graph == "truth" or graph == "truthSinglePath":
    if probMax < 4:
      histogram["bins"] = [0.2 * x for x in range(int(math.ceil(probMax * 5)))]
    elif probMax < 10:
      histogram["bins"] = [0.5 * x for x in range(int(math.ceil(probMax * 2)))]
    elif probMax < 20:
      histogram["bins"] = [1.0 * x for x in range(int(math.ceil(probMax)))]
    elif probMax < 40:
      histogram["bins"] = [2.0 * x for x in range(int(math.ceil(probMax * 0.5)))]
    else:
      histogram["bins"] = [5.0 * x for x in range(int(math.ceil(probMax * 0.2)))]
  elif graph == "delta" or graph.startswith("error"):
    histogram["nBins"] = 20
  for e in data.sortedSequences:
    index = 0 if data.linkSeqTypes[e] == 'neutral' else 1
    for c in naturalSorted(data.linkSeqClassValues[e].keys()):
      if graph == "inferred":
        for prob in data.linkSeqClassValues[e][c]:
          histogram['x'][index].append(prob)
      elif graph == "truth":
        for prob in data.linkSeqClassTruth[e][c]:
          histogram['x'][index].append(prob)
      elif graph == "delta":
        for prob in [data.linkSeqClassValues[e][c][i] - data.linkSeqClassTruth[e][c][i] for i in range(len(data.linkSeqClassValues[e][c]))]:
          histogram['x'][index].append(prob)
      elif graph == "errorPath1":
        for prob in data.linkSeqClassErrorPath1[e][c]:
          histogram['x'][index].append(prob)
      elif graph == "errorPath2":
        for prob in data.linkSeqClassErrorPath2[e][c]:
          histogram['x'][index].append(prob)
      elif graph == "errorExternal":
        for prob in data.linkSeqClassErrorExternal[e][c]:
          histogram['x'][index].append(prob)
      elif graph == "errorInternal":
        for prob in data.linkSeqClassErrorInternal[e][c]:
          histogram['x'][index].append(prob)
      elif graph == "errorInternal1":
        for prob in data.linkSeqClassErrorInternal1[e][c]:
          histogram['x'][index].append(prob)
      elif graph == "errorInternal2":
        for prob in data.linkSeqClassErrorInternal2[e][c]:
          histogram['x'][index].append(prob)
      else:
        raise Exception("oops")
  plot['data'].append(histogram)
  plot['w'] = 14
  plot['h'] = 3

  plot['fileName'] = outputDir + '/' + 'link-seq-cong-prob-all-' + graph + '-histogram.png'
  plot['fileName'] = plot['fileName'].replace('\\', ' ')
  plot['fileName'] = plot['fileName'].replace('%', ' ')
  #plot['dpi'] = 50
  with open(plot['fileName'] + '.json', 'wb') as f:
    json.dump(plot, f, sort_keys=True, indent=4, separators=(',', ': '))
  nicePlot(plot)
  print plot['fileName']
