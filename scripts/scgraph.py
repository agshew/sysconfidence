#!/usr/bin/env python
#  This file is part of SystemBurn.
#
#  Copyright (C) 2012, UT-Battelle, LLC.
#
#  This product includes software produced by UT-Battelle, LLC under Contract No. 
#  DE-AC05-00OR22725 with the Department of Energy. 
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the New BSD 3-clause software license (LICENSE). 
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
#  LICENSE for more details.
#
#  For more information please contact the SystemBurn developers at: 
#  systemburn-info@googlegroups.com


from optparse import OptionParser
from math import ceil, floor, log10
from sys import stderr,stdout
import re
import gzip

# format of output files from sysconfidence:
# bin binbot bintop timer onNode1 oneNodePair onNode1Min onNodePairMin offNode1 offNodePair offNode1Min offNodePairMin
# 0   1      2      3     4       5           6          7             8        9           10          11

# if adding more constants, be sure to add an associated name below
BIN = 0
BINBOT = 1
BINTOP = 2
TIMER = 3
ONNODE_ONE = 4
ONNODE_PAIR = 5
ONNODE_ONEMIN = 6
ONNODE_PAIRMIN = 7
OFFNODE_ONE = 8
OFFNODE_PAIR = 9
OFFNODE_ONEMIN = 10
OFFNODE_PAIRMIN = 11
NUM_STATS = 12
DATAFILES = {"histogram": "global.HIST.0", "pdf":"global.PDF.0", "cdf":"global.CDF.0"}
# if adding more names, be sure to add an associated constant above
NAMES = ["", 
    "", 
    "", 
    "Timer", 
    "onNodeOneSided", 
    "onNodePairwise", 
    "onNodeOneSidedMinimum", 
    "onNodePairwiseMinimum",
    "offNodeOneSided",
    "offNodePairwise",
    "offNodeOneSideMinimum",
    "offNodePairwiseMinimum" ]
  


preamble = """#!/usr/bin/gnuplot
set macros
Node   = "using 3:6"
Nodemin= "using 3:7"
PW     = "using 3:10"
PWmin  = "using 3:12"
OS     = "using 3:9"
OSmin  = "using 3:11"
Timer  = "using 3:4"
set style line 1 lt rgb "green" lw 3 pt 0
set style line 2 lt rgb "red" lw 3 pt 0
set style line 3 lt rgb "blue" lw 3 pt 0
set style line 4 lt rgb "#FF00FF" lw 3 pt 0
set style line 5 lt rgb "cyan" lw 3 pt 0
set style line 6 lt rgb "greenyellow" lw 3 pt 0
set style line 7 lt rgb "#A9A9A9" lw 3 pt 0
set style line 8 lt rgb "#48D1CC" lw 3 pt 0
set style line 9 lt rgb "orangered" lw 3 pt 0
set style line 1 lt rgb "#BA55D3" lw 3 pt 0

set terminal png medium size 1600,1200
set xlabel "Latency (microseconds)"
"""

def min_max_with_index(condata,colnumber):
    """return a set of minimums, maximums, as well as percentile locations (from CDF) for the given data set and column"""
    min_y = 1.0e99
    min_x = 1.0e99
    max_y = -1.0
    max_x = -1.0
    p50th = -1.0
    p90th = -1.0
    p95th = -1.0
    p99th = -1.0
    p99_9th = -1.0
    p99_99th = -1.0
    p99_999th = -1.0
    p99_9999th = -1.0
    p99_99999th = -1.0
    p100th = -1.0
    oldval = 0
    val=0

    for row in condata:
        oldval = val
        val = float(row[colnumber])
        if 0.0 < val < min_y:
            min_y = val
        if val > max_y:
            max_y = val

        if val != 0.0 and val != oldval:
            if row[BINBOT] < min_x:
                min_x = row[BINBOT]
            if row[BINTOP] > max_x:
                max_x = row[BINTOP]

        if val < 0.5:
            continue

        if p50th < 0 and val > 0.5:
            p50th = row[BINTOP]
            continue

        if p90th < 0 and val > 0.9:
            p90th = row[BINTOP]
            continue

        if p95th < 0 and val >= 0.95:
            p95th = row[BINTOP]
            continue

        if p99th < 0 and val >= 0.99:
            p99th = row[BINTOP]
            continue

        if p99_9th < 0 and val >= 0.999:
            p99_9th = row[BINTOP]
            continue

        if p99_99th < 0 and val >= 0.9999:
            p99_99th = row[BINTOP]
            continue

        if p99_999th < 0 and val >= 0.99999:
            p99_999th = row[BINTOP]
            continue

        if p99_9999th < 0 and val >= 0.999999:
            p99_9999th = row[BINTOP]
            continue

        if p99_99999th < 0 and val >= 0.9999999:
            p99_99999th = row[BINTOP]
            continue

        if p100th < 0 and val == 1.0:
            p100th = row[BINTOP]
            continue

        if val > 1.0:
            continue

# make sure we've got reasonable bounds
    if min_y == 1.0e99:
        min_y = 1.0e-6
        min_x = 0

    if max_x < 0.0:
        max_x = 0

    return (min_x, max_x, min_y, max_y, p50th, p90th, p95th, p99th, p99_9th, p99_99th, p99_999th, p99_9999th, p99_99999th, p100th)

class dataColumn(object):
    """represent the minimums and maximums for a column"""
    def __init__(self):
# x are our latencies, y our counts or probabilities
        self.xmin = 1.0e5
        self.xmax = -1.0
        self.ymin = 1.0e5
        self.ymax = -1.0
# for CDF
        self.p50th = -1.0
        self.p90th = -1.0
        self.p95th = -1.0
        self.p99th = -1.0
        self.p99_9th = -1.0
        self.p99_99th = -1.0
        self.p99_999th = -1.0
        self.p99_9999th = -1.0
        self.p99_99999th = -1.0
        self.p100th = -1.0 # latency where CDF is 1

class dataFile(object):
    """encapsulates a data set and associated options"""
    def __init__(self, filename):
        self.columns = [] # create placeholders for our columns
        for i in range(NUM_STATS):
            self.columns.append(dataColumn())

        self.filename = filename

        try:
            self.fh = gzip.open(filename, "r")
        except Exception, e:
            print e

    def parse(self):
        """Read in the file, and put it into some happy data structures"""
        lines = self.fh.readlines()
        self.rows = []
        for line in lines:
            if re.match("^#", line):
                continue
            line = line.rstrip()
            line = line.lstrip()
            fields = re.split("[ \t]*", line)
            fields = [ float(f) for f in fields ]
            #print fields
            self.rows.append(fields)
            #print float(fields[2])
        #print first column
        for i in range(3,NUM_STATS):
            stats = min_max_with_index(self.rows, i)
            self.columns[i].xmin = stats[0]
            self.columns[i].xmax = stats[1]
            self.columns[i].ymin = stats[2]
            self.columns[i].ymax = stats[3]

            if re.search("CDF", self.filename):
                self.columns[i].p50th = stats[4]
                self.columns[i].p90th = stats[5]
                self.columns[i].p95th = stats[6]
                self.columns[i].p99th = stats[7]
                self.columns[i].p99_9th = stats[8]
                self.columns[i].p99_99th = stats[9]
                self.columns[i].p99_999th = stats[10]
                self.columns[i].p99_9999th = stats[11]
                self.columns[i].p99_99999th = stats[12]
                self.columns[i].p100th = stats[13]

class caseData(object):
    """a particular data case"""
    def __init__(self, casename):
        self.casename = casename
        self.datafiles = {}

    def load(self):
        for f in DATAFILES.keys():
            self.datafiles[f] = dataFile(self.casename+"/"+DATAFILES[f]);
            self.datafiles[f].parse()

def graphString(graphtype, graphnum, cases): # expects a list of cases
    """return a string representing the gnuplot command to
       create a graph for the given type (cdf, pdf, histogram)
       given a column to graph and the various different cases"""

    outfile = '"%s-%s.png"' % (graphtype, NAMES[graphnum])

    zoom = ""
    if graphtype == "cdf-0.9":
        graphtype = "cdf"
        zoom = "0.9"
    elif graphtype == "cdf-0.99":
        graphtype = "cdf"
        zoom = "0.99"

    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    p50s = []
    p90s = []
    p99s = []
    p99_9s = []
    p99_99s = []
    p99_999s = []
    p99_9999s = []
    p99_99999s = []
    p100s = []

    for c in cases:
        xmins.append(c.datafiles[graphtype].columns[graphnum].xmin)
        xmaxs.append(c.datafiles[graphtype].columns[graphnum].xmax)
        ymins.append(c.datafiles[graphtype].columns[graphnum].ymin)
        ymaxs.append(c.datafiles[graphtype].columns[graphnum].ymax)
        p50s.append(c.datafiles[graphtype].columns[graphnum].p50th)
        p90s.append(c.datafiles[graphtype].columns[graphnum].p90th)
        p99s.append(c.datafiles[graphtype].columns[graphnum].p99th)
        p99_9s.append(c.datafiles[graphtype].columns[graphnum].p99_9th)
        p99_99s.append(c.datafiles[graphtype].columns[graphnum].p99_99th)
        p99_999s.append(c.datafiles[graphtype].columns[graphnum].p99_999th)
        p99_9999s.append(c.datafiles[graphtype].columns[graphnum].p99_9999th)
        p99_99999s.append(c.datafiles[graphtype].columns[graphnum].p99_99999th)
        p100s.append(c.datafiles[graphtype].columns[graphnum].p100th)

    percentiles = ["50th", "90th", "99th", "99.9th", "99.99th", "99.999th", "99.9999th", "99.99999th", "100th"]
    probabilities = ["0.5", "0.9", "0.99", "0.999", "0.9999", "0.99999", "0.999999", "0.9999999", "1.0"]
    ps = [p50s, p90s, p99s, p99_9s, p99_99s, p99_999s, p99_9999s, p99_99999s, p100s]

    xmin = min(xmins)
    xmax = max(xmaxs)
    ymin = min(ymins)
    ymax = max(ymaxs)
    p90s = [i for i in p90s if i > 0]
    p90th = 1.0e-6
    if p90s:
         p90th = min(p90s)
    p99s = [i for i in p99s if i > 0]
    p99th = 1.0e-6
    if p99s:
         p99th = min(p99s)
    p99_999th = max(p99_999s)
    p100th = max(p100s)

    #stderr.write("%s: xmin: %e xmax: %e ymin: %e ymax: %e\n" % (outfile, xmin, xmax, ymin, ymax))

    if ymax == 0.0:
        if ymin == 0.0:
            ymax = 1.1
        else:
            ymax = 1.0



    if xmin == 0.0 and xmax == 0.0:
        xmax = 1.0


    if graphtype == "cdf":
        if not zoom:
            output = "unset logscale\nset logscale x\nunset label\n"
        else:
            output = "unset logscale\nunset label\n"
# get some slightly better mins/maxes
        if xmin < 1.0e-6:
            #print "Min x for %s was %e, resetting\n" % ( outfile, xmin )
            xmin = 1.0e-6
        else:
            xmin = pow(10,floor(log10(xmin)))

	if p100th > 0:
            xmax = pow(10,ceil(log10(p100th)))

        if zoom == "0.9":
            xmin = p90th - p90th % 10
            xmax = p99_999th
            ymin = 0.9
            ymax = 0.99999
        elif zoom == "0.99":
            xmin = p99th - p99th % 10
            xmax = p99_999th
            ymin = 0.99
            ymax = 0.99999

        output += "# Machine %s Latency (usec) Percentiles\n" % (NAMES[graphnum])
        output += "# Percentile\t%s\n#" % ('\t'.join([c.casename for c in cases]))
        casename_lengths = [len(c.casename) for c in cases]
        for i, p in enumerate(percentiles):
            output += '\n# {:^10s}'.format(p)
            for j, c in enumerate(cases):
                if ps[i][j] <= 0:
                    continue
                dynlength = '\t{:' + str(casename_lengths[j]) + '.4f}'
                output += dynlength.format(ps[i][j])
        output += "\n\n"

        for i, p in enumerate(probabilities):
            for j, c in enumerate(cases):
                if ps[i][j] <= 0:
                    continue
                output += '# set label sprintf("%%g", %e) at %e,%s front point offset -0.01,0.1\n' % (ps[i][j], ps[i][j], p)
    elif graphtype == "pdf":
        output = "unset logscale\nset logscale xy\n"
        if xmin < 1.0e-6:
            #print "Min x for %s was %e, resetting\n" % ( outfile, xmin )
            xmin = 1.0e-6
        else:
            xmin = pow(10,floor(log10(xmin)))

        if xmax > 0:
            xmax = pow(10,ceil(log10(xmax)))

        if ymin < 1.0e-12:
            #print "Min y for %s was %e, resetting\n" % ( outfile, ymin )
            ymin = 1.0
        else:
            ymin = pow(10,floor(log10(ymin)))
        #print "type: %s num: %s ymax: %e\n" % (graphtype, graphnum, ymax)

        if xmax > 0:
            ymax = pow(10,ceil(log10(ymax)))
    else:
        output = "unset logscale\n"

   
    #stderr.write("  FINAL: %s: xmin: %e xmax: %e ymin: %e ymax: %e\n\n" % (outfile, xmin, xmax, ymin, ymax))

    output += 'set output %s\nset xr [%e:%e]\nset yr [%e:%e]\n' % ( outfile, xmin, xmax, ymin, ymax) 
    if not zoom:
        output += 'set title "Confidence %s Latency Observations"' % (NAMES[graphnum])
    else:
        output += 'set title "Confidence %s Latency Observations CDF %s-0.99999"' % (NAMES[graphnum], zoom)
    output += '\nplot \\\n'
    ls = 1
    extrachars = ""
    for c in cases:
        output += '%s   "%s" using %d:%d title "%s" with linespoints ls %d' % ( extrachars, c.datafiles[graphtype].filename, BINTOP+1,graphnum+1,c.casename, ls)
        ls += 1
        extrachars = ", \\\n"
    
    output += "\n"
    return output



def main():

    cases = []
    parser = OptionParser()
    parser.add_option("-o", "--output", dest="outfile", help="output filename")
    parser.add_option("-z", "--zoom", dest="zoom", help="zoom in on percentile of CDF")
    (options, args) = parser.parse_args()

    for arg in args:
        cases.append(caseData(arg))

    # load everything
    for c in cases:
        c.load()

    output = preamble

    for i in range(3,12):
        output += graphString("pdf", i, cases)

        if not options.zoom:
            output += graphString("cdf", i, cases)
        else:
            output += graphString("cdf-0.9", i, cases)

        output += graphString("histogram", i, cases)
    if options.outfile:
        fh = open(options.outfile, "w")
    else:
        fh = stdout

    print >> fh, output


if __name__ == "__main__":
        main()
