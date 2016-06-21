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
  


preamble = """"""

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

def percentileString(graphtype, graphnum, cases): # expects a list of cases
    """return a string representing the gnuplot command to
       create a graph for the given type (cdf, pdf, histogram)
       given a column to graph and the various different cases"""

    percentiles = ["50th", "90th", "99th", "99.9th", "99.99th", "99.999th", "99.9999th", "99.99999th", "100th"]

    p50s = []
    p90s = []
    p99s = []
    p99_9s = []
    p99_99s = []
    p99_999s = []
    p99_9999s = []
    p99_99999s = []
    p100s = []

    ps = [p50s, p90s, p99s, p99_9s, p99_99s, p99_999s, p99_9999s, p99_99999s, p100s]

    for c in cases:
        p50s.append(c.datafiles[graphtype].columns[graphnum].p50th)
        p90s.append(c.datafiles[graphtype].columns[graphnum].p90th)
        p99s.append(c.datafiles[graphtype].columns[graphnum].p99th)
        p99_9s.append(c.datafiles[graphtype].columns[graphnum].p99_9th)
        p99_99s.append(c.datafiles[graphtype].columns[graphnum].p99_99th)
        p99_999s.append(c.datafiles[graphtype].columns[graphnum].p99_999th)
        p99_9999s.append(c.datafiles[graphtype].columns[graphnum].p99_9999th)
        p99_99999s.append(c.datafiles[graphtype].columns[graphnum].p99_99999th)
        p100s.append(c.datafiles[graphtype].columns[graphnum].p100th)

    output = "Machine %s Latency (usec) Percentiles\n" % (NAMES[graphnum])
    output += "Percentile\t%s\n" % ('\t'.join([c.casename for c in cases]))
    casename_lengths = [len(c.casename) for c in cases]
    for i, p in enumerate(percentiles):
        output += '\n{:^10s}'.format(p)
        for j, c in enumerate(cases):
            if ps[i][j] <= 0:
                continue
            dynlength = '\t{:' + str(casename_lengths[j]) + '.4f}'
            output += dynlength.format(ps[i][j])
    output += "\n\n"
    
    return output



def main():

    cases = []
    parser = OptionParser()
    parser.add_option("-o", "--output", dest="outfile", help="output filename")
    (options, args) = parser.parse_args()

    for arg in args:
        cases.append(caseData(arg))

    # load everything
    for c in cases:
        c.load()

    output = preamble

    for i in range(3,12):
        output += percentileString("cdf", i, cases)

    if options.outfile:
        fh = open(options.outfile, "w")
    else:
        fh = stdout

    print >> fh, output


if __name__ == "__main__":
        main()
