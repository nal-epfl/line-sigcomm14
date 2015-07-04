#!/usr/bin/env python2

import sys
from bs4 import BeautifulSoup

def toBase64(filename):
  try:
    fixedname = filename
    fixedname = fixedname.replace('\\', '/')
    with open (fixedname, 'rb') as myfile:
      return "data:;base64," + myfile.read().encode('base64').replace('\n', '')
  except:
    print >> sys.stderr, 'Could not open file:', filename
    return filename

def toText(filename):
  try:
    with open (filename, 'rb') as myfile:
      return myfile.read()
  except:
    print >> sys.stderr, 'Could not open file:', filename
    return ""

if len(sys.argv) != 2:
  print 'Reads an HTML file and outputs it with images inlined as base64 on standard output'
  print 'Usage: ' + str(sys.argv[0]) + ' filename'
  exit(0)

html = ''
filename = sys.argv[1]
with open (filename, "r") as myfile:
  html = myfile.read()

soup = BeautifulSoup(html)

for img in soup.find_all('img'):
  if img.get('src'):
    img['src'] = toBase64(img['src'])

for link in soup.find_all('link'):
  if link.get('rel') and link['rel'] == ['shortcut', 'icon'] and link.get('href'):
    link['href'] = toBase64(link['href'])
  elif link.get('rel') and link['rel'] == ['stylesheet'] and link.get('href'):
    text = toText(link['href'])
    if text:
      soup.head.append('\n<style type="text/css">' + toText(link['href']) + '</style>\n')
      link.extract()

for script in soup.find_all('script'):
  if script.get('src'):
    script.append(toText(script['src']))
    del script['src']

outputFile = filename.replace('.htm', '-inline.htm')

if outputFile != filename:
  with open (outputFile, "w") as out:
    out.write(soup.encode('utf-8', formatter=None))
else:
  print soup.encode('utf-8', formatter=None)
