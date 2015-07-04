#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import colorsys
import copy
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


## Natural sorting (e.g.: asdf7, asdf8, asdf9, asdf10, ...)
# ref: http://stackoverflow.com/questions/4836710
def naturalSorted(l):
  convert = lambda text: int(text) if text.isdigit() else text.lower()
  alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', str(key)) ]
  return sorted(l, key = alphanum_key)

def isRedundant(seq, sequences):
  if not seq:
    return True
  for other in sequences:
    if other <= seq:
      newSeq = seq - other
      if isRedundant(newSeq, sequences):
        return True
  return False

def computeGap(e):
  global data
  values = []
  for c in naturalSorted(data.linkSeqClassValues[e].keys()):
    values.append(sum(data.linkSeqClassValues[e][c]) / float(len(data.linkSeqClassValues[e][c])))
  return max(values) - min(values)

class Data:
  def __init__(self):
    self.experimentName = ""
    self.intervalSize = ""
    self.linkSeqLinks = []
    self.linkSeqTypes = []
    # list[linkSeq] of dict[class] -> list of float
    self.linkSeqClassValues = []
    self.linkSeqClassTruth = []
    self.linkSeqClassTruthSinglePath = []
    self.linkSeqClassErrorPath1 = []
    self.linkSeqClassErrorPath2 = []
    self.linkSeqClassErrorExternal = []
    self.linkSeqClassErrorInternal = []
    self.linkSeqClassErrorInternal1 = []
    self.linkSeqClassErrorInternal2 = []
    self.nonNeutralLinks = set([])
    self.sortedSequences = []

data = None
def readSeqData(inputFileName, removeRedundant, naturalSorting):
  global data
  data = Data()
  with open (inputFileName) as f:
    for line in f.read().split('\n'):
      if not line:
        continue
      tokens = line.split('\t')
      if tokens[0] == 'Experiment':
        # Experiment	long-policing-1	interval	0.1
        data.experimentName = tokens[1]
        data.intervalSize = tokens[3]
      elif tokens[0] == 'Non-neutral links':
        # Non-neutral links	1 2 3 4
        for e in tokens[1:]:
          data.nonNeutralLinks.add(int(e))
      elif tokens[0] == 'Link sequence':
        # Link sequence neutrality	neutral	links	2	4
        data.linkSeqTypes.append(tokens[2])
        data.linkSeqLinks.append([int(token) for token in tokens[4:]])
        print line
        print data.linkSeqLinks[-1]
        data.linkSeqClassValues.append({})
        data.linkSeqClassTruth.append({})
        data.linkSeqClassTruthSinglePath.append({})
        data.linkSeqClassErrorPath1.append({})
        data.linkSeqClassErrorPath2.append({})
        data.linkSeqClassErrorExternal.append({})
        data.linkSeqClassErrorInternal.append({})
        data.linkSeqClassErrorInternal1.append({})
        data.linkSeqClassErrorInternal2.append({})
      elif tokens[0] == 'Class':
        # Class 1	1.1256	1.22113
        # Class 2	2.06498	1.97177
        # Class 1+2	0.913869	0.808522 0.901636
        data.linkSeqClassValues[-1][tokens[1]] = [float(token) for token in tokens[2:]]
      elif tokens[0] == 'True class':
        # True class 1	1.1256	1.22113
        # True class 2	2.06498	1.97177
        # True class 1+2	0.913869	0.808522 0.901636
        data.linkSeqClassTruth[-1][tokens[1]] = [float(token) for token in tokens[2:]]
      elif tokens[0] == 'TrueSinglePath class':
        # TrueSinglePath class	b1c1	4.80104	5.88235	4.71861	4.63203	6.03037	5.81345	5.09138	5.83116
        # TrueSinglePath class	b1c2	5.53532	6.26366	5.5088	5.27927	5.17381	5.98222	4.97592	4.97592
        data.linkSeqClassTruthSinglePath[-1][tokens[1]] = [float(token) for token in tokens[2:]]
      elif tokens[0] == 'ErrorPath1 class':
        # ErrorPath1 class	b1c1	4.80104	5.88235	4.71861	4.63203	6.03037	5.81345	5.09138	5.83116
        # ErrorPath1 class	b1c2	5.53532	6.26366	5.5088	5.27927	5.17381	5.98222	4.97592	4.97592
        data.linkSeqClassErrorPath1[-1][tokens[1]] = [float(token) for token in tokens[2:]]
      elif tokens[0] == 'ErrorPath2 class':
        # ErrorPath2 class	b1c1	4.80104	5.88235	4.71861	4.63203	6.03037	5.81345	5.09138	5.83116
        # ErrorPath2 class	b1c2	5.53532	6.26366	5.5088	5.27927	5.17381	5.98222	4.97592	4.97592
        data.linkSeqClassErrorPath2[-1][tokens[1]] = [float(token) for token in tokens[2:]]
      elif tokens[0] == 'ErrorExternal class':
        # ErrorExternal class	b1c1	4.80104	5.88235	4.71861	4.63203	6.03037	5.81345	5.09138	5.83116
        # ErrorExternal class	b1c2	5.53532	6.26366	5.5088	5.27927	5.17381	5.98222	4.97592	4.97592
        data.linkSeqClassErrorExternal[-1][tokens[1]] = [float(token) for token in tokens[2:]]
      elif tokens[0] == 'ErrorInternal class':
        # ErrorInternal class	b1c1	4.80104	5.88235	4.71861	4.63203	6.03037	5.81345	5.09138	5.83116
        # ErrorInternal class	b1c2	5.53532	6.26366	5.5088	5.27927	5.17381	5.98222	4.97592	4.97592
        data.linkSeqClassErrorInternal[-1][tokens[1]] = [float(token) for token in tokens[2:]]
      elif tokens[0] == 'ErrorInternal1 class':
        # ErrorInternal1 class	b1c1	4.80104	5.88235	4.71861	4.63203	6.03037	5.81345	5.09138	5.83116
        # ErrorInternal1 class	b1c2	5.53532	6.26366	5.5088	5.27927	5.17381	5.98222	4.97592	4.97592
        data.linkSeqClassErrorInternal1[-1][tokens[1]] = [float(token) for token in tokens[2:]]
      elif tokens[0] == 'ErrorInternal2 class':
        # ErrorInternal2 class	b1c1	4.80104	5.88235	4.71861	4.63203	6.03037	5.81345	5.09138	5.83116
        # ErrorInternal2 class	b1c2	5.53532	6.26366	5.5088	5.27927	5.17381	5.98222	4.97592	4.97592
        data.linkSeqClassErrorInternal2[-1][tokens[1]] = [float(token) for token in tokens[2:]]

  # Remove redundant sequences
  redundancy = []
  for i in range(len(data.linkSeqLinks)):
    if removeRedundant:
      seq = copy.deepcopy(data.linkSeqLinks[i])
      newSequences = copy.deepcopy(data.linkSeqLinks)
      newSequences.pop(i)
      seq = set(seq)
      for j in range(len(newSequences)):
        newSequences[j] = set(newSequences[j])
      redundancy.append(isRedundant(seq, newSequences))
    else:
      redundancy.append(False)

  data.linkSeqLinks = [data.linkSeqLinks[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqTypes = [data.linkSeqTypes[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassValues = [data.linkSeqClassValues[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassTruth = [data.linkSeqClassTruth[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassTruthSinglePath = [data.linkSeqClassTruthSinglePath[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassErrorPath1 = [data.linkSeqClassErrorPath1[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassErrorPath2 = [data.linkSeqClassErrorPath2[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassErrorExternal = [data.linkSeqClassErrorExternal[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassErrorInternal = [data.linkSeqClassErrorInternal[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassErrorInternal1 = [data.linkSeqClassErrorInternal1[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]
  data.linkSeqClassErrorInternal2 = [data.linkSeqClassErrorInternal2[i] for i in range(len(data.linkSeqLinks)) if not redundancy[i]]

  if not naturalSorting:
    data.sortedSequences = range(len(data.linkSeqLinks))
    data.sortedSequences.sort(key=computeGap)
  else:
    data.sortedSequences = range(len(data.linkSeqLinks))
    convert = lambda text: int((text + '').replace('*', '')) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', str(len(data.linkSeqLinks[key])) + ' ' + ' '.join([ str(x) for x in naturalSorted(data.linkSeqLinks[key])]) ) ]
    data.sortedSequences.sort(key=alphanum_key)
    for e in data.sortedSequences:
      data.linkSeqLinks[e] = naturalSorted(data.linkSeqLinks[e])
  return data
