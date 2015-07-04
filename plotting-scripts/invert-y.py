#!/usr/bin/env python2

import json
import sys

if len(sys.argv) != 2:
  print 'Reads a JSON plot file and outputs it with y inverted'
  print 'Usage: ' + str(sys.argv[0]) + ' filename'
  exit(0)

input = ''
filename = sys.argv[1]
with open (filename, "r") as myfile:
  input = myfile.read()
plot = json.loads(input)

for item in plot['data']:
  if 'y' in item:
    if isinstance(item['y'], list):
      for i in range(len(item['y'])):
        item['y'][i] = 100.0 - item['y'][i]

result = json.dumps(plot, sort_keys=True, indent=4, separators=(',', ': '))

outputFile = filename.replace('.json', '-inverted.json')
if outputFile != filename:
  with open (outputFile, "w") as out:
    out.write(result)
else:
  print result


