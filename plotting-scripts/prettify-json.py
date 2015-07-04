#!/usr/bin/env python2

import json
import sys

if len(sys.argv) != 2:
  print 'Reads a JSON file and outputs it prettified'
  print 'Usage: ' + str(sys.argv[0]) + ' filename'
  exit(0)

input = ''
filename = sys.argv[1]
with open (filename, "r") as myfile:
  input = myfile.read()
result = json.dumps(json.loads(input), sort_keys=True, indent=4, separators=(',', ': '))

outputFile = filename.replace('.json', '-pretty.json')
if outputFile != filename:
  with open (outputFile, "w") as out:
    out.write(result)
else:
  print result


