#!/usr/bin/env python

"""
1 args: <error>
2 args: <bucket> <local_dir_to_upload>
3 args: <bucket> <remote_dir_in_bucket> <local_dir_to_upload>
4 args:
"""

# Aja esim nain, Kuvat-hakemistossa
# python ~/git/python/src/filelist.py Valokuvia 2021

import os
import sys
import logging
import subprocess

b2cmd_base = 'b2'
b2cmd_command = 'upload-file'

#logFile = '/var/tmp/B2App.log.test'
logFile = '/var/tmp/B2App.log'

# this logging stuff was shamelessly copypasted from somewhere. Lost the link already :(
logger = logging.getLogger('B2App')
hdlr = logging.FileHandler(logFile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

def replaceIfNeeded(string, sChar, rChar):
    if sChar in string:
        print(string + " contains " + sChar)
        string = string.replace(sChar, rChar)
    return string

def createB2Command(bucket, filename):
    """
    Create a command that calls the b2 python script
    """
    targetName = filename
    targetName = replaceIfNeeded(targetName, "\xe4", "a")
    targetName = replaceIfNeeded(targetName, "\xf6", "o")
    targetName = replaceIfNeeded(targetName, "\xc4", "A")
    targetName = replaceIfNeeded(targetName, "\xd6", "O")

    b2cmd = b2cmd_base + ' ' + b2cmd_command + ' ' + bucket + ' "' + filename + '" "' + targetName + '"'
    return b2cmd

def printHelp():
    print
    print "Usage: " + sys.argv[0] + " <bucketti> <hakemisto>"
    print
    print "- If any file upload fails, this script exits"
    print "- TODO: some way to continue partial upload"
    print


def logLine(text):
    """
    Log a text into the log file
    """
    logger.info(text)

def uploadFile(f):
    """
    Upload the given file to the b2
    This method also calculates the file size and prints and returns it. I know, it's unorthodox to do many things
    but I'm now too tired to fix this
    """
    filename = f
    b2cmd = createB2Command(bucket, filename)
    print b2cmd
    logLine("Starting to handle " + filename)
    size = os.stat(filename).st_size/(1024.0*1024.0)
    print("File size: " + str(size) + "M")
    result = 0
    result = os.system(b2cmd)
#   print b2cmd
    if result != 0:
        msg = "Handling " + filename + " failed with exit code " + str(result) + ". Exiting.";
        logLine(msg)
        print msg
        sys.exit(result);
    logLine("Done handling file " + filename)
    return size

def parseLogFile(startdir):
    """
    This tries to parse log file and to find out what files are not yet uploaded into the
    b2. This is still under construction
    """
    # Starting to work in {dir}
    # Starting to handle {file}
    # Handling {file} failed with exit code
    # Done handling file {file}
    # Working in {dir} ended
    with open(logFile) as f:
        for line in f:
            donefiles = [line.split("Done handling file", 1)[1].strip() for line in f if "Done handling file" in line]
    return donefiles

def du(path):
    """
    Calculates the directory size: https://stackoverflow.com/a/1392549/5363167
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024.0 * 1024.0)

# Here is the __main__
print 'Argument list:', str(sys.argv)

# The first argument is the bucket where teh user wants to upload the file
bucket = sys.argv[1]

if bucket == "--parse":
    """ 
    Parse log files to find out what files are already uploaded
    Under construction..
    """
    parseLogFile(sys.argv[2])
    sys.exit(0)

if len(sys.argv) != 3:
    print 'Argument list length is ' + str(len(sys.argv)) + ' should be 3'
    printHelp()
    sys.exit(-1)

# The second argument is the directory the user wants to upload to B2
basedir = sys.argv[2]
if not os.path.isdir(basedir):
    print 'Parameter ' + basedir + ' is not a directory!'
    printHelp()
    sys.exit(-2)

logLine("Starting to work in " + os.getcwd())

sizeLeft = du(basedir)
print("Directory size: " + str(sizeLeft) + "M")

files = [os.path.join(basedir, f) for f in os.listdir(basedir) if os.path.isfile(os.path.join(basedir, f))]
print("Files: " + str(files))

# Flat dirs
# for f in sorted(files):
#     size = uploadFile(f)
#     sizeLeft = sizeLeft - size
#     print "Size left: " + str(sizeLeft) + "M"

# Go directories recursively
for dirpath, dirs, files in os.walk(basedir):
    dirs.sort()
    for f in sorted(files) :
        size = uploadFile(os.path.join(dirpath, f))
        sizeLeft = sizeLeft - size
        print "Size left: " + str(sizeLeft) + "M"

logger.info("Working in " + os.getcwd() + " ended")

