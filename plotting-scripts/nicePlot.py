#!/usr/bin/env python2

# Author: Ovidiu Mara <ovidiu.mara@epfl.ch>
# License: GPLv2
#
# See main() for an example input

import colorsys
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rc
from matplotlib.ticker import AutoLocator, AutoMinorLocator, MaxNLocator, MultipleLocator, LinearLocator
from matplotlib.font_manager import FontProperties
import numpy as np
import os
import pprint
import re
import subprocess
import sys

# ref: http://stackoverflow.com/questions/4836710
def naturalSorted(l):
  convert = lambda text: int(text) if text.isdigit() else text.lower()
  alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
  return sorted(l, key = alphanum_key)

def resample(l, maxPoints):
  if len(l) < maxPoints:
    return l
  l = sorted(l)
  step = int(round(float(len(l)) / maxPoints + 0.5))
  lSampled = []
  for i in range(0, len(l), step):
    lSampled.append(l[i])
  return lSampled

def nicePlotInternal(plot):
  rc('font', **{'family':'sans-serif','sans-serif':['Helvetica', 'Liberation Sans']})
  rc('text.latex', preamble=[r'\usepackage{siunitx}',   # i need upright \micro symbols, but you need...
     r'%\sisetup{detect-all}',   # ...this to force siunitx to actually use your fonts
       r'\usepackage{helvet}',    # set the normal font here
       r'\usepackage{sfmath}\usepackage{sansmath}',  # load up the sansmath so that math -> helvet
       r'\sansmath'])
  #rc('font', **{'family' : 'serif', 'serif' : ['Latin Modern Roman']})
  rc('text', usetex=True)
  rc('mathtext', default='regular', fontset='stixsans')
  plt.rcParams['xtick.major.pad'] = 6
  plt.rcParams['xtick.minor.pad'] = 6
  fontSizeTitle = 16
  fontSizeAxisLabel = 16
  fontSizeAxisTicks = 14
  fontSizeLegendTitle = 14
  fontSizeLegendItem = 12
  # multiply legendHandleLength by fontSizeLegendItem to get pixels
  legendHandleLength = 2

  fig = 0
  if 'w' in plot and 'h' in plot and 'dpi' in plot:
    plt.figure(fig, figsize=(plot['w'], plot['h']), dpi=plot['dpi'])
  elif 'dpi' in plot:
    plt.figure(fig, dpi=plot['dpi'])
  elif 'w' in plot and 'h' in plot:
    plt.figure(fig, figsize=(plot['w'], plot['h']))
  else:
    plt.figure(fig)
  fig += 1
  plt.hold = True

  legendLabels = []
  for item in plot['data']:
    if 'labels' in item:
      for label in item['labels']:
        legendLabels.append(label)
    else:
      if 'label' in item:
        legendLabels.append(item['label'])

  legendWidth = 0.0
  if 'noLegend' not in plot:
    for label in legendLabels:
      fontP = FontProperties()
      fontP.set_size(fontSizeLegendItem * plot['fontScale'])
      t = plt.text(0, 0, label, fontproperties=fontP, transform=None)
      bb = t.get_window_extent(renderer=plt.gcf().canvas.get_renderer())
      #w = (1.7 + legendHandleLength) * fontSizeLegendItem * plot['fontScale'] + bb.width
      #w = bb.width + legendHandleLength
      w = bb.width
      if w > legendWidth:
        legendWidth = w
      plt.clf()

  legendEntries = []
  legendLabels = []

  if 'title' in plot and plot['title']:
    box = [0.15, 0.10, 0.80, 0.80]
  else:
    box = [0.07, 0.18, 0.80, 0.80]

  # box[2] = 1.0 - legendWidth / (plt.gcf().get_figwidth() * plt.gcf().dpi) - box[0]
  box[2] = 1.20 - 0 / (plt.gcf().get_figwidth() * plt.gcf().dpi) - box[0]
  plt.gcf().add_axes(box)
  noHistogramTicks = False
  histogramTicks = set()
  barCount = 0
  for item in plot['data']:
    if item['type'] == 'bar':
      barCount = barCount + 1
  barOffsetX = 0.0
  barWidth = 0.8/max(1.0, barCount)
  for item in plot['data']:
    if item['type'] == 'line':
      noHistogramTicks = True
      p, = plt.plot(item['x'], item['y'], item['pattern'], label=item['label'] if 'label' in item else None, color=colorsys.hsv_to_rgb(item['color'][0], item['color'][1], item['color'][2]), linewidth=1.5)
      if 'label' in item and len(item['label']) > 0:
        legendEntries.append(p)
        legendLabels.append(item['label'])
    elif item['type'] == 'bar':
      noHistogramTicks = True
      barLeft = []
      for x in item['x']:
        barLeft.append(x + barOffsetX - barWidth*barCount/2.0)
      barOffsetX = barOffsetX + barWidth
      p = plt.bar(barLeft, item['y'], width=barWidth, color=colorsys.hsv_to_rgb(item['color'][0], item['color'][1], item['color'][2]), hatch=item['hatch'])
      if 'label' in item and len(item['label']) > 0:
        legendEntries.append(p)
        legendLabels.append(item['label'])
    elif item['type'] == 'boxplot':
      maxPoints = 1000
      data = item['x']
      if data:
        if isinstance(data[0], list):
          for i in range(len(data)):
            data[i] = resample(data[i], maxPoints)
        else:
          data = resample(data, maxPoints)
      boxWidth = item['w'] if 'w' in item else 0.5
      if 'positions' in item:
        p = plt.boxplot(data, positions=item['positions'], widths=boxWidth)
      else:
        p = plt.boxplot(data, widths=boxWidth)
      plt.setp(p['boxes'], color='black')
      plt.setp(p['whiskers'], color='black')
      plt.setp(p['medians'], color='gray')
      plt.setp(p['fliers'], color='black', marker='+')
    elif item['type'] == 'stem':
      if 'lineFormat' in item:
        lineFormat = item['lineFormat']
      else:
        lineFormat = 'b-'
      if 'markerFormat' in item:
        markerFormat = item['markerFormat']
      else:
        markerFormat = 'bo'
      p = plt.stem(item['x'], item['y'], lineFormat, markerFormat, basefmt='')
    elif item['type'] == 'histogram':
      isMultiHistogram = any(isinstance(el, list) for el in item['x'])
      bins = []
      binCenters = []
      points = set()
      if isMultiHistogram:
        for boxes in item['x']:
          for point in boxes:
            points.add(point)
      else:
        for point in item['x']:
          points.add(point)
      points = sorted(points)
      if 'bins' in item:
        bins = item['bins']
        binCenters = 0.5 * np.diff(bins) + bins[:-1]
      else:
        binCenters = []
        binWidth = 0.5
        if 'binWidth' in item:
          binWidth = item['binWidth']
        if 'binCenters' in item:
          binCenters = item['binCenters']
        else:
          nbins = 7
          if 'nBins' in item:
            nbins = item['nBins']
          if len(points) < nbins and 'nBins' not in item and 'binWidth' not in item:
            binCenters = points
          else:
            binCenters = []
            if nbins <= 1:
              binCenters = [(max(points) - min(points)) / 2.0]
            else:
              binWidth = (max(points) - min(points)) / (nbins - 1.0)
              if 'binWidth' in item:
                binWidth = item['binWidth']
                nbins = int(math.ceil((max(points) - min(points)) / binWidth))
              for i in range(nbins):
                binCenters.append(min(points) + binWidth * i)
        if len(binCenters) == 0:
          binCenters = [0.0]
        bins = []
        if len(binCenters) == 1:
          bins = [binCenters[0] - binWidth/2.0, binCenters[0] + binWidth/2.0]
        else:
          for i in range(len(binCenters) - 1):
            p1 = binCenters[i]
            p2 = binCenters[i+1]
            if i == 0:
              bins.append(p1 - (p2 - p1)/2.0)
            bins.append((p1 + p2)/2.0)
            if i == len(binCenters) - 2:
              bins.append(p2 + (p2 - p1)/2.0)
        if bins[0] > min(points):
          bins[0] = min(points)
        if bins[-1] < max(points):
          bins[-1] = max(points)
      for center in binCenters:
        histogramTicks.add(center)
      colors=[]
      if isMultiHistogram:
        if item['colors'] == 'auto':
          hue = 0.0
          for i in range(len(item['x'])):
            colors.append(colorsys.hsv_to_rgb(hue, 0.75, 0.95))
            # Add 1/goldenRatio
            # Ref: http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
            hue += 0.618033988749895
            if hue > 1.0:
              hue -= 1.0
        else:
          for i in range(len(item['x'])):
            colors.append(colorsys.hsv_to_rgb(item['colors'][i][0], item['colors'][i][1], item['colors'][i][2]))
      if not isMultiHistogram:
        plt.hist(item['x'], bins=bins, label=item['label'] if 'label' in item else None, align='mid', histtype='bar', color=colorsys.hsv_to_rgb(item['color'][0], item['color'][1], item['color'][2]))
      else:
        plt.hist(item['x'], bins=bins, label=item['labels'] if 'labels' in item else None, align='mid', histtype='bar', color=colors)
      if not isMultiHistogram:
        if 'label' in item and len(item['label']) > 0:
          p = plt.Rectangle((0, 0), 1, 1, facecolor=colorsys.hsv_to_rgb(item['color'][0], item['color'][1], item['color'][2]))
          legendEntries.append(p)
          legendLabels.append(item['label'])
      else:
        for i in range(len(item['x'])):
          if 'labels' in item and len(item['labels'][i]) > 0:
            p = plt.Rectangle((0, 0), 1, 1, facecolor=colors[i])
            legendEntries.append(p)
            legendLabels.append(item['labels'][i])
    else:
      print 'Unknown plot type:', item['type']

  box = plt.gca().get_position()
  plt.gca().set_position([box.x0, box.y0, box.width * 0.8, box.height])
  box = plt.gca().get_position()

  #plt.title(plot['title'], fontsize=fontSizeTitle * plot['fontScale'])
  if 'title' in plot:
    #plt.text(0.5, 1.04, plot['title'], horizontalalignment='center', fontsize=fontSizeTitle * plot['fontScale'], transform=plt.gca().transAxes)
    plt.figtext(0.5, 0.94, plot['title'], horizontalalignment='center', fontsize=fontSizeTitle * plot['fontScale'])
  histogramTicks = list(set(histogramTicks))
  if len(histogramTicks) > 0 and len(histogramTicks) < 20 and not noHistogramTicks:
    histogramTicks = sorted(histogramTicks)
    plt.xticks(histogramTicks, size=fontSizeAxisTicks * plot['fontScale'])
  else:
    plt.xticks(size=fontSizeAxisTicks * plot['fontScale'])
  plt.yticks(size=fontSizeAxisTicks * plot['fontScale'])

  #plt.xlabel(plot['xLabel'], fontsize=fontSizeAxisLabel * plot['fontScale'])
  #plt.ylabel(plot['yLabel'], fontsize=fontSizeAxisLabel * plot['fontScale'])
  plt.figtext(0.5, 0.05, plot['xLabel'], ha='center', va='center', fontsize=fontSizeAxisLabel * plot['fontScale'])
  plt.figtext(0.02, 0.5, plot['yLabel'], ha='center', va='center', rotation='vertical', fontsize=fontSizeAxisLabel * plot['fontScale'])

  if 'xFormatStr' in plot:
    plt.gca().xaxis.set_major_formatter(plt.FormatStrFormatter(plot['xFormatStr']))
  else:
    if hasattr(plt.gca().xaxis.get_major_formatter(), 'set_useOffset'):
      plt.gca().xaxis.get_major_formatter().set_useOffset(True)
  if 'yFormatStr' in plot:
    plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter(plot['yFormatStr']))
  else:
    if hasattr(plt.gca().yaxis.get_major_formatter(), 'set_useOffset'):
      plt.gca().yaxis.get_major_formatter().set_useOffset(True)

  majorXTicks = -1
  if 'majorXTicks' in plot:
    majorXTicks = int(plot['majorXTicks'])
  if majorXTicks >= 0:
    plt.gca().xaxis.set_major_locator(LinearLocator(numticks=majorXTicks))
  else:
    plt.gca().xaxis.set_major_locator(AutoLocator())

  minorXTicks = 1
  if 'minorXTicks' in plot:
    minorXTicks = int(plot['minorXTicks'])
  if minorXTicks > 0:
    plt.gca().xaxis.set_minor_locator(AutoMinorLocator(n=minorXTicks))

  majorYTicks = -1
  if 'majorYTicks' in plot:
    majorYTicks = int(plot['majorYTicks'])
  if majorYTicks >= 0:
    plt.gca().yaxis.set_major_locator(LinearLocator(numticks=majorYTicks))
  else:
    plt.gca().yaxis.set_major_locator(AutoLocator())

  minorYTicks = 1
  if 'minorYTicks' in plot:
    minorYTicks = int(plot['minorYTicks'])
  if minorYTicks > 0:
    plt.gca().yaxis.set_minor_locator(AutoMinorLocator(n=minorYTicks))

  if 'xTicks' in plot:
    if 'xTickLabels' in plot:
      plt.xticks(plot['xTicks'], plot['xTickLabels'])
    else:
      plt.xticks(plot['xTicks'])
  else:
    if 'xTickLabels' in plot:
      plt.gca().set_xticklabels(plot['xTickLabels'])
  if 'yTicks' in plot:
    if 'yTickLabels' in plot:
      plt.yticks(plot['yTicks'], plot['yTickLabels'])
    else:
      plt.yticks(plot['yTicks'])
  else:
    if 'yTickLabels' in plot:
      plt.gca().set_yticklabels(plot['yTickLabels'])
  plt.grid(which=plot['grid'])
  lim = [None, None]
  if 'xmin' in plot:
    lim[0] = plot['xmin']
  if 'xmax' in plot:
    lim[1] = plot['xmax']
  plt.xlim(lim)
  lim = [None, None]
  if 'ymin' in plot:
    lim[0] = plot['ymin']
  if 'ymax' in plot:
    lim[1] = plot['ymax']
  plt.ylim(lim)
  fontP = FontProperties()
  fontP.set_size(fontSizeLegendItem * plot['fontScale'])
  legendTitle = 'Legend'
  if 'legendTitle' in plot:
    legendTitle = plot['legendTitle']
  if 'noLegend' not in plot:
    #plt.legend(legendEntries, legendLabels, loc='upper left', bbox_to_anchor=(1, 1.016), prop=fontP, title=legendTitle, handlelength=2, frameon=False)
    #plt.legend(legendEntries, legendLabels, loc='upper left', bbox_to_anchor=(0, 1.016), prop=fontP, title=legendTitle, handlelength=2, frameon=True)
    plt.legend(legendEntries, legendLabels, loc='lower left', bbox_to_anchor=(0, 0), prop=fontP, title=legendTitle, handlelength=2, frameon=True)
    plt.setp(plt.gca().get_legend().get_title(), fontsize=fontSizeLegendTitle * plot['fontScale'])
    plt.setp(plt.gca().get_legend().get_texts(), fontsize=fontSizeLegendItem * plot['fontScale'])
    plt.gca().get_legend().get_frame().set_alpha(0.5)
  if 'w' in plot and 'h' in plot:
    plt.gcf().set_size_inches(plot['w'], plot['h'])
  if 'dpi' in plot:
    plt.savefig(plot['fileName'], dpi=plot['dpi'])
  else:
    plt.savefig(plot['fileName'])

def nicePlot(plot):
  with open(plot['fileName'] + '.json', 'wb') as f:
    json.dump(plot, f, sort_keys=True, indent=4, separators=(',', ': '))
  script = os.path.join(os.path.dirname(__file__), 'nicePlot.py')
  args = ['python', script, plot['fileName'] + '.json']
  print(args)
  subprocess.call(args)

def main():
  plotJsonPath = ''
  if len(sys.argv) > 1:
    plotJsonPath = sys.argv[1]
    with open (plotJsonPath, "r") as myfile:
      jsonString = myfile.read()
  else:
    # Items prefixed with _ are ignored. They are shown so that you can see the other
    # available options.
    jsonString = r'''{
                    "title": "Plot title",
                    "xLabel": "The X axis",
                    "yLabel": "The Y axis",
                    "fileName": "figure1.pdf",
                    "_wh_comment": "If present, w and h are given in inches. Use them only for aspect ratio changes, for scaling specify a different dpi."
                    "_w": 8,
                    "_h": 6,
                    "_dpi": 100,
                    "fontScale": 1.5,
                    "_grid_comment": "Possible values: empty string, major, minor, both.",
                    "grid": "",
                    "_xmin": 0.0,
                    "_xmax": 1.0,
                    "ymin": 0.0,
                    "_ymax": 1.0,
                    "_xFormatStr": "%2.1f",
                    "_yFormatStr": "%2.1f",
                    "_xTicks": [],
                    "_yTicks": [],
                    "_xTickLabels": [],
                    "_yTickLabels": [],
                    "_minorXTicks" : 1,
                    "_minorYTicks" : 1,
                    "_majorXTicks_comment": "Possible values: -1 (auto), 0 (none), >0 (number of ticks).",
                    "_majorXTicks" : -1,
                    "_majorYTicks" : -1,
                    "_noLegend_comment" : "If present, the legend is not drawn.",
                    "_noLegend": 0,
                    "_legendTitle": "Legend",
                    "data": [
                      {
                        "type": "line",
                        "x": [2, 3, 5, 8, 11],
                        "y": [4, 5, 9, 3, 2],
                        "pattern": "o-",
                        "label": "Curve 1",
                        "_color_comment": "HSV triple with real values from 0 to 1.",
                        "color": [0.0, 1.0, 0.8]
                      },
                      {
                        "type": "histogram",
                        "_x_comment": "You can use either a list of values (histogram), or a list of lists (multi-histogram, i.e. parallel bars). For a multi-histogram, you must use labels and colors instead of label and color.",
                        "_x": [2, 3, 3, 4, 5, 7, 8],
                        "x": [[2, 3, 3, 5, 7], [2, 5, 5, 5, 6, 7, 8], [1, 2, 2, 2, 5, 7, 7, 7], [2, 3, 4, 5]],
                        "_binCenters": [2, 3, 4, 5, 7, 8],
                        "_bins": [0, 4, 8],
                        "_nBins": 3,
                        "_binWidth": 2.0,
                        "_label": "Histogram 1",
                        "labels": ["Apples", "Oranges", "Berries", "Bananas"],
                        "_color": [0.3, 1.0, 0.8],
                        "_colors_comment": "Use 'auto' to have them generated automatically.",
                        "_colors": [[0.0, 1.0, 0.8], [0.14, 1.0, 1.0]],
                        "colors": "auto"
                      },
                      {
                        "type": "boxplot",
                        "_x_comment": "You can use either a list of values (boxplot), or a list of lists (multi-boxplot). For a multi-boxplot, the first boxplot is generated at x=1, the second at x=2 etc.",
                        "_x": [2, 3, 3, 4, 5, 7, 8],
                        "x": [[2, 3, 3, 5, 7], [2, 5, 5, 5, 6, 7, 8], [1, 2, 2, 2, 5, 7, 7, 7], [2, 3, 4, 5]]
                      },
                      {
                        "type": "stem",
                        "x": [3, 4, 5, 6, 7, 8, 9],
                        "y": [1, 1.5, 2.2, 2.9, 3.7, 3.8, 3.9],
                        "lineFormat": "b-",
                        "markerFormat": "bo"
                      },
                      {
                        "type": "line",
                        "x": [3, 4, 5, 7, 8],
                        "y": [2, 1, 5, 9, 1],
                        "pattern": "x--",
                        "label": "Curve 2",
                        "color": [0.6, 1.0, 1.0]
                      }
                    ]}'''
  plot = json.loads(jsonString)
  nicePlotInternal(plot)

if __name__ == "__main__":
  main()
