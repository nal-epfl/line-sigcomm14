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

## Params

dataFile = 'data-plot1.txt'
latencyFile = 'latency.txt'
throughputInFile = 'throughput-in.txt'
throughputOutFile = 'throughput-out.txt'
inputDir = ''
outputDir = ''
plotNumber = '1'
extraTitleLabel = ''

try:
  opts, args = getopt.getopt(sys.argv[1:], '', ['plot=', 'in=', 'out=', 'label='])
except getopt.GetoptError as err:
  # print help information and exit:
  print str(err) # will print something like "option -a not recognized"
  sys.exit(2)
output = None
verbose = False
for opt, arg in opts:
  if opt == '--plot':
    plotNumber = arg
  elif opt == '--in':
    inputDir = arg
  elif opt == '--out':
    outputDir = arg
  elif opt == '--label':
    extraTitleLabel = arg
  else:
    assert False, "Unhandled option: " + str(opt)

if plotNumber == 'all':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for plot in [ '1', '1b', '2', '3', '4', '5', '5b', '7', '7b', '7b+', '8', '8b', '8b+' ]:
    args = ['python', script, '--plot', plot]
    print(args)
    subprocess.call(args)
  exit(0)
elif plotNumber == 'real-vs-shaping':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'

  args = ['python', script, '--plot', '1', '--in', 'plot1-real-data', '--out', 'plot1-real', '--label', '(real)']
  print(args)
  subprocess.call(args)

  args = ['python', script, '--plot', '1', '--in', 'plot1-emulator-data', '--out', 'plot1-emulator', '--label', '(emulator)']
  print(args)
  subprocess.call(args)

  args = ['python', script, '--plot', '7', '--in', 'plot7-real-data', '--out', 'plot7-real', '--label', '(real)']
  print(args)
  subprocess.call(args)

  args = ['python', script, '--plot', '7', '--in', 'plot7-emulator-data', '--out', 'plot7-emulator', '--label', '(emulator)']
  print(args)
  subprocess.call(args)

  args = ['python', script, '--plot', '2', '--in', 'plot2-real-data', '--out', 'plot2-real', '--label', '(real)']
  print(args)
  subprocess.call(args)

  args = ['python', script, '--plot', '2', '--in', 'plot2-emulator-data', '--out', 'plot2-emulator', '--label', '(emulator)']
  print(args)
  subprocess.call(args)

  args = ['python', script, '--plot', '2', '--in', 'plot2-shaping-real-data', '--out', 'plot2-shaping-real', '--label', '(real)']
  print(args)
  subprocess.call(args)

  args = ['python', script, '--plot', '2', '--in', 'plot2-shaping-emulator-data', '--out', 'plot2-shaping-emulator', '--label', '(emulator)']
  print(args)
  subprocess.call(args)

  exit(0)
elif plotNumber == 'vary-rtt-and-buffers':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  #for tag in ['', 'sigcomm-deadline', 'sigcomm-deadline-repro']:
  #for tag in ['sigcomm-deadline-repro']:
  for tag in ['']:
    for qos in ['policing', 'shaping']:
      niceqos = qos.capitalize()
      for rtt in ['50', '80', '120', '200']:
        for buffers in ['large', 'small', 'medium']:
          for scaling in ['notscaled', 'scaleddown']:
            nicescaling = 'not scaled' if scaling == 'notscaled' else 'scaled down' if scaling == 'scaleddown' else scaling
            dataDir = 'plot2-{0}-data-rtt-{1}-buffers-{2}-{3}{4}'.format(qos, rtt, buffers, scaling, ('-' + tag) if tag else '')
            plotDir = 'plot2-{0}-rtt-{1}-buffers-{2}-{3}{4}'.format(qos, rtt, buffers, scaling, ('-' + tag) if tag else '')
            label = '{0}, RTT {1}ms, {2} buffers, {3}'.format(niceqos, rtt, buffers, nicescaling)
            if os.path.isdir(dataDir):
              args = ['python', script,
                      '--plot', '2',
                      '--in', dataDir,
                      '--out', plotDir,
                      '--label', label]
              print(args)
              if subprocess.call(args) != 0:
                exit(1)
  exit(0)
elif plotNumber == 'diff-rtt':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for tag in ['']:
    for qos in ['policing', 'shaping', 'neutral']:
      niceqos = qos.capitalize()
      for rtt in ['48-120', '120-48']:
        for buffers in ['large', 'small', 'medium']:
          for scaling in ['notscaled', 'scaleddown']:
            for tcp in ['cubic']:
              nicescaling = 'not scaled' if scaling == 'notscaled' else 'scaled down' if scaling == 'scaleddown' else scaling
              nicertt = rtt.replace('-', '(1)/') + '(2) ms'
              dataDir = 'plot2-{0}-data-rtt-{1}-buffers-{2}-{3}-{4}{5}'.format(qos, rtt, buffers, scaling, tcp, ('-' + tag) if tag else '')
              plotDir = 'plot2-{0}-rtt-{1}-buffers-{2}-{3}-{4}{5}'.format(qos, rtt, buffers, scaling, tcp, ('-' + tag) if tag else '')
              label = '{0}, RTT {1}, {2} buffers, {3}, TCP {4}'.format(niceqos, nicertt, buffers, nicescaling, tcp)
              if os.path.isdir(dataDir):
                args = ['python', script,
                        '--plot', '2',
                        '--in', dataDir,
                        '--out', plotDir,
                        '--label', label]
                print(args)
                if subprocess.call(args) != 0:
                  exit(1)
  exit(0)
elif plotNumber == 'diff-rtt-tcp':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for tag in ['']:
    for qos in ['policing', 'shaping', 'neutral']:
      niceqos = qos.capitalize()
      for rtt in ['48-120', '120-48']:
        for buffers in ['large', 'small', 'medium']:
          for scaling in ['notscaled', 'scaleddown']:
            for tcp in ['cubic', 'cubic-reno', 'reno-cubic']:
              nicescaling = 'not scaled' if scaling == 'notscaled' else 'scaled down' if scaling == 'scaleddown' else scaling
              dataDir = 'plot2-{0}-data-rtt-{1}-buffers-{2}-{3}-{4}{5}'.format(qos, rtt, buffers, scaling, tcp, ('-' + tag) if tag else '')
              plotDir = 'plot2-{0}-rtt-{1}-buffers-{2}-{3}-{4}{5}'.format(qos, rtt, buffers, scaling, tcp, ('-' + tag) if tag else '')
              label = '{0}, RTT {1}ms, {2} buffers, {3}, TCP {4}'.format(niceqos, rtt, buffers, nicescaling, tcp)
              if os.path.isdir(dataDir):
                args = ['python', script,
                        '--plot', '2',
                        '--in', dataDir,
                        '--out', plotDir,
                        '--label', label]
                print(args)
                if subprocess.call(args) != 0:
                  exit(1)
  exit(0)
elif plotNumber == 'diff-tcp':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for tag in ['cubic-reno', 'reno-cubic']:
    for qos in ['policing', 'shaping', 'neutral']:
      niceqos = qos.capitalize()
      for rtt in ['50', '80', '120', '200']:
        for buffers in ['large', 'small', 'medium']:
          for scaling in ['notscaled', 'scaleddown']:
            nicescaling = 'not scaled' if scaling == 'notscaled' else 'scaled down' if scaling == 'scaleddown' else scaling
            dataDir = 'plot2-{0}-data-rtt-{1}-buffers-{2}-{3}{4}'.format(qos, rtt, buffers, scaling, ('-' + tag) if tag else '')
            plotDir = 'plot2-{0}-rtt-{1}-buffers-{2}-{3}{4}'.format(qos, rtt, buffers, scaling, ('-' + tag) if tag else '')
            label = '{0}, RTT {1}ms, {2} buffers, {3}, {4}'.format(niceqos, rtt, buffers, nicescaling, tag)
            if os.path.isdir(dataDir):
              args = ['python', script,
                      '--plot', '2',
                      '--in', dataDir,
                      '--out', plotDir,
                      '--label', label]
              print(args)
              if subprocess.call(args) != 0:
                exit(1)
  exit(0)
elif plotNumber == 'vary-qos':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for d in os.listdir('.'):
    if not os.path.isdir(d):
      continue
    if 'image' in d:
      continue
    plotNo = '1-7'
    dataDir = d
    plotDir = 'image-{0}'.format(d)
    label = d
    print 'Looking for {0}'.format(dataDir)
    if os.path.isdir(dataDir):
      args = ['python', script,
              '--plot', plotNo,
              '--in', dataDir,
              '--out', plotDir,
              '--label', label]
      print(args)
      if subprocess.call(args) != 0:
        exit(1)
  exit(0)
elif plotNumber == 'vary-transfer-size':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for d in os.listdir('.'):
    if not os.path.isdir(d):
      continue
    if 'image' in d:
      continue
    plotNo = '2'
    dataDir = d
    plotDir = 'image-{0}'.format(d)
    label = d
    print 'Looking for {0}'.format(dataDir)
    if os.path.isdir(dataDir):
      args = ['python', script,
              '--plot', plotNo,
              '--in', dataDir,
              '--out', plotDir,
              '--label', label]
      print(args)
      if subprocess.call(args) != 0:
        exit(1)
  exit(0)
elif plotNumber == 'vary-rtt':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for d in os.listdir('.'):
    if not os.path.isdir(d):
      continue
    if 'image' in d:
      continue
    plotNo = '9'
    dataDir = d
    plotDir = 'image-{0}'.format(d)
    label = d
    print 'Looking for {0}'.format(dataDir)
    if os.path.isdir(dataDir):
      args = ['python', script,
              '--plot', plotNo,
              '--in', dataDir,
              '--out', plotDir,
              '--label', label]
      print(args)
      if subprocess.call(args) != 0:
        exit(1)
  exit(0)
elif plotNumber == 'vary-tcp':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for d in os.listdir('.'):
    if not os.path.isdir(d):
      continue
    if 'image' in d:
      continue
    plotNo = '10'
    dataDir = d
    plotDir = 'image-{0}'.format(d)
    label = d
    print 'Looking for {0}'.format(dataDir)
    if os.path.isdir(dataDir):
      args = ['python', script,
              '--plot', plotNo,
              '--in', dataDir,
              '--out', plotDir,
              '--label', label]
      print(args)
      if subprocess.call(args) != 0:
        exit(1)
  exit(0)
elif plotNumber == 'vary-congestion':
  script = os.path.realpath(__file__)
  print 'Running script for all scenarios...'
  for d in os.listdir('.'):
    if not os.path.isdir(d):
      continue
    if 'image' in d:
      continue
    plotNo = '11'
    dataDir = d
    plotDir = 'image-{0}'.format(d)
    label = d
    print 'Looking for {0}'.format(dataDir)
    if os.path.isdir(dataDir):
      args = ['python', script,
              '--plot', plotNo,
              '--in', dataDir,
              '--out', plotDir,
              '--label', label]
      print(args)
      if subprocess.call(args) != 0:
        exit(1)
  exit(0)

if plotNumber == '5':
  if not inputDir:
    inputDir = 'plot%s-data' % '1'
  dataFile = 'data-plot%s.txt' % '1'
elif plotNumber == '5b':
  if not inputDir:
    inputDir = 'plot%s-data' % '1b'
  dataFile = 'data-plot%s.txt' % '1b'
elif plotNumber == '7b+':
  if not inputDir:
    inputDir = 'plot%s-data' % '7b'
  dataFile = 'data-plot%s.txt' % '7b'
elif plotNumber == '8':
  if not inputDir:
    inputDir = 'plot%s-data' % '7'
  dataFile = 'data-plot%s.txt' % '7'
elif plotNumber == '8b' or plotNumber == '8b+':
  if not inputDir:
    inputDir = 'plot%s-data' % '7b'
  dataFile = 'data-plot%s.txt' % '7b'
else:
  if not inputDir:
    inputDir = 'plot%s-data' % plotNumber
  dataFile = 'data-plot%s.txt' % plotNumber
if not outputDir:
  outputDir = 'plot%s' % plotNumber

print 'Arguments:'
print 'Input dir:', inputDir
print 'Data file:', dataFile
print 'Output dir:', outputDir
print 'Plot:', plotNumber

## End of params

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

class Experiment(object):
  def __init__(self):
    self.tag = ""
    self.policing = ""
    self.shaping = ""
    self.tcp = ""
    self.rtt = ""
    self.congestion = ""
    self.throughputIn = ""
    self.pCongClass1PerPath = []
    self.pCongClass2PerPath = []
    self.pCongLinkComputed = []
    self.procDelayAverage = 0
    self.procDelayPeak = 0
    self.queuingDelay = 0 # queuing delay for 1 frame
    self.pathClass = []
    self.congThreshold = 0.05 # congestion threshold in percent, modified below
  def __repr__(self):
    pp = pprint.PrettyPrinter(indent=2)
    return "Experiment" + pp.pformat(self.__dict__)
  def __str__(self):
    pp = pprint.PrettyPrinter(indent=2)
    return "Experiment" + pp.pformat(self.__dict__)

# Regenerate data file
print 'Regenerating data file from experiment data...'
args = ['bash', '-c', '''rm -f {0} ; for d in {1}/* ; do echo $d; cat "$d/path-congestion-probs.txt" 1>>{0} 2>/dev/null ; done'''.format(dataFile, inputDir)]
print(args)
subprocess.call(args)

args = ['bash', '-c', '''rm -f {0} ; for d in {1}/* ; do echo $d; cat "$d/emulator.out" | grep -A1 'Event delay' | grep -i max | grep -v Sync 1>>{0} 2>/dev/null ; done'''.format(latencyFile, inputDir)]
print(args)
subprocess.call(args)

args = ['bash', '-c', '''rm -f {0} ; for d in {1}/* ; do echo $d; cat "$d/emulator.out" | grep 'Bits received per second' 1>>{0} 2>/dev/null ; done'''.format(throughputInFile, inputDir)]
print(args)
subprocess.call(args)

args = ['bash', '-c', '''rm -f {0} ; for d in {1}/* ; do echo $d; cat "$d/emulator.out" | grep 'Bits sent per second' 1>>{0} 2>/dev/null ; done'''.format(throughputOutFile, inputDir)]
print(args)
subprocess.call(args)

## Read data
print 'Reading data...'
latencyPeaks = []
latencyAverages = []
throughputInValues = []
throughputOutValues = []

def timeUnitToUs(unit):
  if unit == "ns":
    return 0.0001
  elif unit == "us":
      return 1
  elif unit == "ms":
    return 1000
  elif unit == "s":
      return 1000 * 1000
  elif unit == "m":
      return 60 * 1000 * 1000
  elif unit == "h":
      return 60 * 60 * 1000 * 1000
  elif unit == "d":
      return 24 * 60 * 60 * 1000 * 1000
  else:
    print unit
    assert(False)

def timestampStr2us(str):
  # "1 d 2 h 3 m 4 s 5 ms 6 us 7 ns"
  tokens = str.split()
  result = 0
  for i in range(0, len(tokens), 2):
    result += float(tokens[i]) * timeUnitToUs(tokens[i+1])
  return result

def timestampStr2usOld(str):
  # '   0   0s   0m  98u 542n'
  tokens = [float(re.sub('[a-z]', '', word)) for word in str.split()]
  return tokens[0] * 1.0e9 + tokens[1] * 1.0e6 + tokens[2] * 1.0e3 + tokens[3] * 1.0e0 + tokens[4] * 1.0e-3

with open (latencyFile, "r") as myfile:
  for line in myfile.read().split('\n'):
    if not line:
      continue
    line = line[0:-1]
    try:
      # 'Min 0 ns, Max 10 us 292 ns, Average 549 ns:'
      avgDelayStr = line.split(',')[2].replace(' Average', '')
      maxDelayStr = line.split(',')[1].replace(' Max', '')
      latencyAverages.append(timestampStr2us(avgDelayStr))
      latencyPeaks.append(timestampStr2us(maxDelayStr))
    except:
      # 'Event delay: avg  0   0s   0m   0u 361n ', ' max  0   0s   0m  98u 542n'
      avgDelayStr = line.split(':')[1].split(',')[0].replace('avg', '')
      maxDelayStr = line.split(':')[1].split(',')[1].replace('max', '')
      latencyAverages.append(timestampStr2usOld(avgDelayStr))
      latencyPeaks.append(timestampStr2usOld(maxDelayStr))

with open (throughputInFile, "r") as myfile:
  for line in myfile.read().split('\n'):
    if not line:
      continue
    # 'Bits received per second: 67.6772 Mbps'
    throughput = float(line.split(':')[1].split(' ')[1])
    throughputInValues.append(throughput)

with open (throughputOutFile, "r") as myfile:
  for line in myfile.read().split('\n'):
    if not line:
      continue
    # 'Bits sent per second: 67.6772 Mbps'
    throughput = float(line.split(':')[1].split(' ')[1])
    throughputOutValues.append(throughput)

experiments = []
with open (dataFile, "r") as myfile:
  data = myfile.read()
  for line in data.split('\n'):
    tokens = line.split('\t')
    for i in range(len(tokens)):
      tokens[i] = tokens[i].strip()
    if tokens[0] == 'Experiment':
      if experiments:
        print experiments[-1]
      print 'Found experiment:', tokens[1]
      experiments.append(Experiment())
      experiments[-1].tag = tokens[1]
      experiments[-1].procDelayAverage = latencyAverages.pop(0)
      experiments[-1].procDelayPeak = latencyPeaks.pop(0)
      experiments[-1].throughputIn = throughputInValues.pop(0)
      experiments[-1].throughputOut = throughputOutValues.pop(0)
      try:
        experiments[-1].policing = re.compile('policing-[0-9]+(\\.[0-9]+)?-[0-9]+(\\.[0-9]+)?').search(experiments[-1].tag).group(0).replace('policing-', '').replace('-', '/').replace('1.0/1.0', 'No policing')
      except:
        pass
      try:
        experiments[-1].shaping = re.compile('shaping-[0-9]+(\\.[0-9]+)?-[0-9]+(\\.[0-9]+)?').search(experiments[-1].tag).group(0).replace('shaping-', '').replace('-', '/')
      except:
        pass
      try:
        experiments[-1].transferSize = re.compile('transfer-size-[0-9]+(\\.[0-9]+)?-[0-9]+(\\.[0-9]+)?').search(experiments[-1].tag).group(0).replace('transfer-size-', '').replace('-', '/').replace('9999', 'Long')
        sizes = experiments[-1].transferSize.split('/')
        if len(sizes) == 2 and sizes[0] == sizes[1]:
          experiments[-1].transferSize = sizes[0]
      except:
        pass
      try:
        experiments[-1].linkSpeed = re.compile('link-[0-9]+(\\.[0-9]+)?Mbps').search(experiments[-1].tag).group(0).replace('link-', '')
      except:
        pass
      try:
        experiments[-1].numFlows = str(4*int(re.compile('nflows-[0-9]+').search(experiments[-1].tag).group(0).replace('nflows-', '')))
      except:
        pass
      try:
        experiments[-1].tcp = re.compile('tcp-(cubic-reno|reno-cubic|cubic|reno)').search(experiments[-1].tag).group(0).replace('tcp-', '').replace('-', '/')
      except:
        pass
      try:
        experiments[-1].rtt = re.compile('rtt-[0-9]+-[0-9]+').search(experiments[-1].tag).group(0).replace('rtt-', '').replace('-', '/')
        rtts = experiments[-1].rtt.split('/')
        if len(rtts) == 2 and rtts[0] == rtts[1]:
          experiments[-1].rtt = rtts[0]
      except:
        pass
      try:
        experiments[-1].congestion = re.compile('congestion-[a-zA-Z0-9]+-[a-zA-Z0-9]+').search(experiments[-1].tag).group(0).replace('congestion-', '').replace('-', '/').replace('light', 'lo').replace('medium', 'me').replace('high', 'hi').replace('none', 'no')
      except:
        pass
      if experiments[-1].policing and experiments[-1].policing != 'No policing':
        experiments[-1].congThreshold = 0.001
      elif experiments[-1].shaping:
        if experiments[-1].tcp == 'reno' and experiments[-1].transferSize == 'Long':
          experiments[-1].congThreshold = 0.001
        else:
          experiments[-1].congThreshold = 0.001
      else:
        experiments[-1].congThreshold = 0.001
    elif tokens[0] == 'Class':
      experiments[-1].pathClass = [int(c) for c in tokens[1:]]
    elif experiments and tokens[0] == str(experiments[-1].congThreshold):
      print 'Hit 347'
      for p in range(len(tokens) - 1):
        print 'Hit 349'
        if experiments[-1].pathClass[p] == 0:
          experiments[-1].pCongClass1PerPath.append(float(tokens[1 + p]))
        elif experiments[-1].pathClass[p] == 1:
          experiments[-1].pCongClass2PerPath.append(float(tokens[1 + p]))
        else:
          print 'NO CLASS!!!', experiments[-1].pathClass[p]
    print 'tokens = ', tokens
    if len(tokens) < 2:
      if experiments:
        print experiments[-1]
      break
    if not experiments:
      continue
    # delay in us
    # 100 Mb/s = 100 b/us
    # d(us) = 1500 * 8(b) / speed(b/us)
    experiments[-1].queuingDelay = (1500 * 8) / float(experiments[-1].linkSpeed.replace('Mbps', ''))

for e in experiments:
  if not e.policing and not e.shaping:
    e.policing = e.shaping = 'neutral'

args = ['bash', '-c', '''rm -f {0} 2>/dev/null'''.format(dataFile)]
print(args)
subprocess.call(args)

args = ['bash', '-c', '''rm -f {0} {1} {2} 2>/dev/null'''.format(latencyFile, throughputInFile, throughputOutFile)]
print(args)
subprocess.call(args)

## End of data reading

## Group experiments
print 'Grouping eperiments by parameters...'
experimentGroup1 = {}
experimentGroupTitle = {}
experimentGroupLegendTitle = {}

if plotNumber == '1-7':
  key1 = 'policing'
  if len(set([getattr(e, key1) for e in experiments])) > 1:
    plotNumber = '1'
  key1 = 'shaping'
  if len(set([getattr(e, key1) for e in experiments])) > 1:
    plotNumber = '7'
  if plotNumber == '1-7':
    raise SystemExit('Error')

key1 = ''
if plotNumber == '1' or plotNumber == '1b' or plotNumber == '5' or plotNumber == '5b':
  key1 = 'policing'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'Policing'
elif plotNumber == '2':
  key1 = 'transferSize'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'Transfer size'
elif plotNumber == '3':
  key1 = 'linkSpeed'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'Bottleneck bandwidth'
elif plotNumber == '4':
  key1 = 'numFlows'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'Total number of flows'
elif plotNumber == '7' or plotNumber == '7b' or plotNumber == '8' or plotNumber == '8b':
  key1 = 'shaping'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'Shaping'
elif plotNumber == '7b+' or plotNumber == '8b+':
  key1 = 'shaping'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'Shaping (cong. thresh. 0.25\\%)'
elif plotNumber == '9':
  key1 = 'rtt'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'RTT'
elif plotNumber == '10':
  key1 = 'tcp'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'TCP'
elif plotNumber == '11':
  key1 = 'congestion'
  experimentGroupTitle[key1] = '@label@'
  experimentGroupLegendTitle[key1] = 'Congestion'
else:
  print 'Bad plot number %s' % plotNumber
  exit()

# 'key1': @key1 -> [ @experiment ]
allValues = sorted(list(set([getattr(e, key1) for e in experiments])))
experimentGroup1[key1] = {}
for v in allValues:
  experimentGroup1[key1][str(v)] = [e for e in experiments if getattr(e, key1) == v]

# Remove empty lists
for key1 in experimentGroup1.keys():
  for key2 in experimentGroup1[key1].keys():
    if not experimentGroup1[key1][key2]:
      del experimentGroup1[key1][key2]
  if not experimentGroup1[key1]:
    del experimentGroup1[key1]

print 'experimentGroup1 = ', experimentGroup1

## End of experiment grouping


## Plot

try:
  os.makedirs(outputDir)
except OSError as exception:
  pass

fig = 0
# [left, bottom, width, height]
figureBorder = [0.10, 0.20, 0.80, 0.70]

# Cleanup target dir
print 'Cleaning up target directory (%s)...' % outputDir
args = ['bash', '-c', '''cd '%s' && ls -1 | grep -E '^[0-9]+\\..*.(pdf|png)$' | while read -r f ; do rm -fv "$f" ; done || echo "Could not change dir to %s"''' % (outputDir, outputDir) ]
print(args)
subprocess.call(args)

print 'Generating plot %s...' % plotNumber
for key1 in naturalSorted(experimentGroup1.keys()):
  if plotNumber == '1' or plotNumber == '1b' or plotNumber == '2' or plotNumber == '3' or plotNumber == '4' \
  or plotNumber == '7' or plotNumber == '7b' or plotNumber == '7b+' or plotNumber == '9' or plotNumber == '10' \
  or plotNumber == '11':
    # Probability of congestion per class curve plots
    curvex = []
    curvexLabels = ['']
    curves1y = []
    curves2y = []
    paramKeys = naturalSorted(experimentGroup1[key1].keys())
    if plotNumber == '1' or plotNumber == '1b':
      paramKeys = reversed(paramKeys)
    elif plotNumber == '11':
      paramKeys = sortCongestion(paramKeys)
    print 'experimentGroup1[key1][key2][0] = ', experimentGroup1[key1][key2][0]
    numPathsClass1 = len(experimentGroup1[key1][key2][0].pCongClass1PerPath)
    for key2 in paramKeys:
      curvex.append(1 + len(curvex))
      curvexLabels.append(key2)
    curvexLabels.append('')
    print 'curvex =', curvex
    print 'curvexLabels = ', curvexLabels
    print 'numPathsClass1 = ', numPathsClass1
    congThresholds = set()
    for iPath in range(numPathsClass1):
      curvey = []
      for key2 in paramKeys:
        for e in experimentGroup1[key1][key2]:
          curvey.append(sorted(e.pCongClass1PerPath)[iPath])
          congThresholds.add(e.congThreshold)
      print 'curvey (1) =', curvey
      curves1y.append(curvey)
    if len(congThresholds) == 1:
      congThresholdLabel = str(congThresholds.pop())
    else:
      congThresholdLabel = str(congThresholds)
    extraTitleLabel += " {0}\\%".format(congThresholdLabel)
    numPathsClass2 = len(experimentGroup1[key1][key2][0].pCongClass2PerPath)
    for iPath in range(numPathsClass2):
      curvey = []
      for key2 in paramKeys:
        for e in experimentGroup1[key1][key2]:
          curvey.append(sorted(e.pCongClass2PerPath)[iPath])
      print 'curvey (2) =', curvey
      curves2y.append(curvey)
    # Draw curve plot
    fig += 1
    plot = {}
    metric = 'prob-cong-path'
    plot['title'] = experimentGroupTitle[key1].replace('@metric@', 'Probability of congestion per path')
    if extraTitleLabel:
      plot['title'] = experimentGroupTitle[key1].replace('@label@', extraTitleLabel)
    plot['xLabel'] = experimentGroupLegendTitle[key1]
    plot['yLabel'] = 'Probability of congestion (\\%)'
    plot['fontScale'] = 1.0
    plot['grid'] = ''
    plot['xmin'] = 0
    plot['xmax'] = max(curvex) + 1
    plot['ymin'] = 0
    plot['ymax'] = 100.0
    plot['minorXTicks'] = 0
    plot['majorXTicks'] = len(curvexLabels)
    #
    print 'curves1y = ', curves1y
    print 'curves2y = ', curves2y
    plot['data'] = []
    for iPath in range(len(curves1y)):
      curve = {}
      curve['type'] = 'bar'
      curve['x'] = curvex
      curve['y'] = curves1y[iPath]
      curve['hatch'] = '/' if iPath == 0 else '\\'
      curve['label'] = 'Path class 1'
      curve['color'] = [0.667, 0, 0.4]
      plot['data'].append(curve)
    for iPath in range(len(curves2y)):
      curve = {}
      curve['type'] = 'bar'
      curve['x'] = curvex
      curve['y'] = curves2y[iPath]
      curve['hatch'] = '/' if iPath == 0 else '\\'
      curve['label'] = 'Path class 2'
      curve['color'] = [0., 0., 0.8]
      plot['data'].append(curve)
    plot['xTickLabels'] = curvexLabels
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '.pdf'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '.png'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    plot['w'] = 8
    plot['h'] = 6
    plot['dpi'] = 100
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '-300.png'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    plot['w'] = 8
    plot['h'] = 6
    plot['dpi'] = 50
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    print plot['fileName']

    ## Emulator latency (processing delay) plot
    curve1y = []
    for key2 in paramKeys:
      for e in experimentGroup1[key1][key2]:
        curve1y.append(e.procDelayPeak)
    print curve1y

    curve2y = []
    for key2 in paramKeys:
      for e in experimentGroup1[key1][key2]:
        curve2y.append(e.procDelayAverage)
    print curve2y

    curve3y = []
    for key2 in paramKeys:
      for e in experimentGroup1[key1][key2]:
        curve3y.append(e.queuingDelay)
    print curve3y

    # Draw curve plot
    fig += 1
    plot = {}
    metric = 'latency'
    plot['title'] = experimentGroupTitle[key1].replace('@metric@', 'Emulator latency')
    if extraTitleLabel:
      plot['title'] = experimentGroupTitle[key1].replace('@label@', extraTitleLabel)
    plot['xLabel'] = experimentGroupLegendTitle[key1]
    plot['yLabel'] = 'Processing delay (us)'
    plot['fontScale'] = 1.0
    plot['grid'] = ''
    plot['xmin'] = 0
    plot['xmax'] = max(curvex) + 1
    plot['ymin'] = 0
    #plot['ymax'] = 100.0
    plot['minorXTicks'] = 0
    plot['majorXTicks'] = len(curvexLabels)
    #
    plot['data'] = []
    #
    curve = {}
    curve['type'] = 'bar'
    curve['x'] = curvex
    curve['y'] = curve1y
    curve['hatch'] = ''
    curve['label'] = 'Peak'
    curve['color'] = [0., 0, 0.8]
    plot['data'].append(curve)
    #
    curve = {}
    curve['type'] = 'bar'
    curve['x'] = curvex
    curve['y'] = curve2y
    curve['hatch'] = ''
    curve['label'] = 'Average'
    curve['color'] = [0., 0., 0.4]
    plot['data'].append(curve)
    #
    curve = {}
    curve['type'] = 'line'
    curve['x'] = [plot['xmin'], plot['xmax']]
    curve['y'] = [curve3y[0], curve3y[0]]
    curve['label'] = 'Queuing delay of 1 frame'
    curve['pattern'] = '--'
    curve['color'] = [0., 0., 0.]
    plot['data'].append(curve)
    #
    plot['xTickLabels'] = curvexLabels
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '-latency' + '.pdf'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '-latency' + '.png'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    plot['w'] = 8
    plot['h'] = 6
    plot['dpi'] = 100
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '-latency' + '-300.png'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    plot['w'] = 8
    plot['h'] = 6
    plot['dpi'] = 50
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    print plot['fileName']

    ## Emulator throughput plot
    curve1y = []
    for key2 in paramKeys:
      for e in experimentGroup1[key1][key2]:
        curve1y.append(e.throughputIn)
    print curve1y

    curve2y = []
    for key2 in paramKeys:
      for e in experimentGroup1[key1][key2]:
        curve2y.append(e.throughputOut)
    print curve2y

    # Draw curve plot
    fig += 1
    plot = {}
    metric = 'throughput'
    plot['title'] = experimentGroupTitle[key1].replace('@metric@', 'Throughput')
    if extraTitleLabel:
      plot['title'] = experimentGroupTitle[key1].replace('@label@', extraTitleLabel)
    plot['xLabel'] = experimentGroupLegendTitle[key1]
    plot['yLabel'] = 'Throughput (Mbps)'
    plot['fontScale'] = 1.0
    plot['grid'] = ''
    plot['xmin'] = 0
    plot['xmax'] = max(curvex) + 1
    plot['ymin'] = 0
    #plot['ymax'] = 100.0
    plot['minorXTicks'] = 0
    plot['majorXTicks'] = len(curvexLabels)
    #
    plot['data'] = []
    #
    curve = {}
    curve['type'] = 'bar'
    curve['x'] = curvex
    curve['y'] = curve1y
    curve['hatch'] = ''
    curve['label'] = 'In'
    curve['color'] = [0., 0, 0.8]
    plot['data'].append(curve)
    #
    curve = {}
    curve['type'] = 'bar'
    curve['x'] = curvex
    curve['y'] = curve2y
    curve['hatch'] = ''
    curve['label'] = 'Out'
    curve['color'] = [0., 0., 0.4]
    plot['data'].append(curve)
    # Hardcode 100 Mbps line
    curve = {}
    curve['type'] = 'line'
    curve['x'] = [plot['xmin'], plot['xmax']]
    curve['y'] = [100.0, 100.0]
    curve['label'] = ''
    curve['pattern'] = '--'
    curve['color'] = [0., 0., 0.]
    plot['data'].append(curve)
    #
    plot['xTickLabels'] = curvexLabels
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '-throughput' + '.pdf'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '-throughput' + '.png'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    plot['w'] = 8
    plot['h'] = 6
    plot['dpi'] = 100
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '-throughput' + '-300.png'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    plot['w'] = 8
    plot['h'] = 6
    plot['dpi'] = 50
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    print plot['fileName']
  elif plotNumber == '5' or plotNumber == '5b' or plotNumber == '8' or plotNumber == '8b' or plotNumber == '8b+':
    # Non-neutrality
    curvex = []
    curvexLabels = ['']
    curvey = []
    paramKeys = naturalSorted(experimentGroup1[key1].keys())
    if plotNumber == '5' or plotNumber == '5b':
      paramKeys = reversed(paramKeys)
    for key2 in paramKeys:
      curvex.append(1 + len(curvex))
      curvexLabels.append(key2)
    curvexLabels.append('')
    print 'curvex =', curvex
    print 'curvexLabels = ', curvexLabels
    for key2 in paramKeys:
      for e in experimentGroup1[key1][key2]:
        curvey.append(max(e.pCongLinkComputed) - min(e.pCongLinkComputed))
    print 'curvey =', curvey
    # Draw curve plot
    fig += 1
    plot = {}
    metric = 'non-neutrality'
    plot['title'] = experimentGroupTitle[key1].replace('@metric@', 'Computed non-neutrality')
    if extraTitleLabel:
      plot['title'] = experimentGroupTitle[key1].replace('@label@', extraTitleLabel)
    plot['xLabel'] = experimentGroupLegendTitle[key1]
    plot['yLabel'] = 'Computed non-neutrality (0-100)'
    plot['fontScale'] = 1.0
    plot['grid'] = ''
    plot['xmin'] = 0
    plot['xmax'] = max(curvex) + 1
    plot['ymin'] = 0
    plot['ymax'] = 100.0
    plot['minorXTicks'] = 0
    plot['majorXTicks'] = len(curvexLabels)
    plot['noLegend'] = 1
    #
    plot['data'] = []
    curve = {}
    curve['type'] = 'line'
    curve['x'] = curvex
    curve['y'] = curvey
    curve['pattern'] = '-+'
    #curve['label'] = 'Computed non-neutrality'
    curve['color'] = [0.667, 1.0, 0.8]
    plot['data'].append(curve)
    plot['xTickLabels'] = curvexLabels
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '.pdf'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '.png'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    plot['w'] = 8
    plot['h'] = 6
    plot['dpi'] = 100
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    plot['fileName'] = outputDir + '/' + str(plotNumber) + '. stats ' + metric + ' - ' + key1 + '-300.png'
    plot['fileName'] = plot['fileName'].replace('\\', ' ')
    plot['fileName'] = plot['fileName'].replace('%', ' ')
    plot['w'] = 8
    plot['h'] = 6
    plot['dpi'] = 50
    with open(plot['fileName'] + '.json', 'wb') as f:
      json.dump(plot, f)
    nicePlot(plot)
    print plot['fileName']
  else:
    print 'Unknown plotNumber:', plotNumber
exit()
