#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Sun 09 Sep 2012 12:42:38 CEST 

"""Count blinks given partial scores.
"""

import os
import sys
import bob
import numpy
import argparse
from antispoofing.utils.db import *

def main():
  """Main method"""
  
  from .. import utils

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, help='Base directory containing the scores to be loaded and merged')
  parser.add_argument('outputdir', metavar='DIR', type=str, help='Base output directory for every file created by this procedure')
  
  parser.add_argument('-S', '--skip-frames', metavar='INT', type=int,
      default=10, dest='skip', help="Number of frames to skip once an eye-blink has been detected (defaults to %(default)s)")

  parser.add_argument('-T', '--threshold-ratio', metavar='FLOAT', type=float,
      default=3.0, dest='thres_ratio', help="How many standard deviations to use for counting positive blink picks to %(default)s)")

  parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
      default=False, help='Increases this script verbosity')

  Database.create_parser(parser, implements_any_of='video')

  args = parser.parse_args()

  if not os.path.exists(args.inputdir):
    parser.error("input directory `%s' does not exist" % args.inputdir)


  if not os.path.exists(args.outputdir):
    if args.verbose: print "Creating output directory %s..." % args.outputdir
    os.makedirs(args.outputdir)


  #Loading the database data
  database = args.cls(args)
  realObjects, attackObjects = database.get_all_data()
  process = realObjects + attackObjects


  counter = 0
  for obj in process:
    counter += 1
    arr = obj.load(args.inputdir, '.hdf5')
    nb = utils.count_blinks(arr, args.thres_ratio, args.skip)

    if args.verbose:
      print "Processed file %s [%d/%d]... %d blink(s)" % \
          (obj.videofile, counter, len(process), nb[-1])

    obj.save(nb, args.outputdir, '.hdf5')
