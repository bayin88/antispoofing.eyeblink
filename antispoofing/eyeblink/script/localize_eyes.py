#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Mon 02 Aug 2010 11:31:31 CEST

"""
Localizes the center of the eyes for all videos
"""

import os, sys
import argparse

from antispoofing.utils.db import *

def get_biggest(dets):
  """Returns the biggest detection found"""
  retval = dets[0]
  for d in dets[1:]:
    if retval['bbox'][2] < d['bbox'][2]: retval = d
  return retval


def main():

  import bob
  import numpy
  from .. import utils
  from xbob.flandmark import Localizer

  op = Localizer() 


  basedir = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
  INPUTDIR = os.path.join(basedir, 'database')
  ANNOTATIONS = os.path.join(basedir, 'annotations')
  OUTPUTDIR = os.path.join(basedir, 'framediff')

  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('inputdir', metavar='DIR', type=str, default=INPUTDIR,
      nargs='?', help='Base directory containing the videos to be treated by this procedure (defaults to "%(default)s")')


  parser.add_argument('outputdir', metavar='DIR', type=str, default=OUTPUTDIR,
      nargs='?', help='Base output directory for every file created by this procedure defaults to "%(default)s")')

  parser.add_argument('-v', '--verbose', default=True, action='store_true', help="Increases the output verbosity level")

  # The next option just returns the total number of cases we will be running
  # It can be used to set jman --array option.
  parser.add_argument('--grid-count', dest='grid_count', action='store_true',
      default=False, help=argparse.SUPPRESS)

  Database.create_parser(parser, implements_any_of='video')

  args = parser.parse_args()

  outputdir = args.outputdir

  #Loading the database data
  database = args.cls(args)
  realObjects, attackObjects = database.get_all_data()
  process = realObjects + attackObjects

  if args.grid_count:
    print len(process)
    sys.exit(0)

  # if we are on a grid environment, just find what I have to process.
  if os.environ.has_key('SGE_TASK_ID'):
    key = int(os.environ['SGE_TASK_ID']) - 1
    if key >= len(process):
      raise RuntimeError, "Grid request for job %d on a setup with %d jobs" % \
          (key, len(process))
    process = [process[key]]

  for counter, obj in enumerate(process):

    filename = str(obj.videofile(args.inputdir))
    input = bob.io.VideoReader(filename)

    sys.stdout.write("Processing file %s (%d frames) [%d/%d]..." % (filename,
      input.number_of_frames, counter+1, len(process)))

    #Creating the output dir
    output_file = obj.videofile()[0:len(obj.videofile())-3]
    output_file = os.path.join(outputdir,output_file + 'flandmark')
    #output_file = os.path.join(outputdir,obj.videofile()).rstrip('.mov').rstrip('.avi') + '.flandmark'

    if(not os.path.exists(output_file)):
      bob.db.utils.makedirs_safe(os.path.dirname(output_file))

    output = open(output_file, 'wt')

    if args.verbose:
      print "Locating faces in %d frames" % len(input),
	  
    for k, frame in enumerate(input):

      dets = op(frame)
      if dets:
        biggest = get_biggest(dets)
        bbox = biggest['bbox']
        landmarks = biggest['landmark']
        output.write("%d %d %d %d %d " % ((k,) + bbox))
        lstr = " ".join("%d %d" % (round(p[0]), round(p[1])) for p in landmarks)
        output.write(lstr + "\n")
        if args.verbose:
          sys.stdout.write('.')
          sys.stdout.flush()
      else:
        output.write("%d 0 0 0 0\n" % k)
        if args.verbose:
          sys.stdout.write('x')
          sys.stdout.flush()


    if args.verbose is not None:
      sys.stdout.write('\n')
      sys.stdout.flush()

  return 0
