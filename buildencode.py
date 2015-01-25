#buildencode v0.1

from sys import exit
from optparse import OptionParser
from os.path import exists
from os import unlink, mkdir
from subprocess import Popen, PIPE
from shutil import rmtree
from time import time, strftime, gmtime
from datetime import timedelta

from commandbuilder import getChopPoints, buildx264, buildextractWAV, buildsoxsplit, buildencodeAudio, \
	dospecialAAC, buildmkvmerge, buildffmpegx264
	
parser = OptionParser(usage="usage: %prog [options] inputfile")
parser.add_option("-f", "--full", action="store_true", dest="full", default=False,
	help="Do full CRF-14/FLAC encode.")
parser.add_option("--full720p", action="store_true", dest="full720p", default=False,
	help="Do full 720p CRF-17/FLAC? encode.")
parser.add_option("-q", "--quick", action="store_true", dest="quick", default=False,
	help="Do quick CRF-22/AAC encode.")
parser.add_option("-t", "--tiny", action="store_true", dest="tiny", default=False,
	help="Do quick tiny 480p AAC encode.")
parser.add_option("--8bit", action="store_true", dest="do8bit", default=False,
	help="Do 8bit encode. (Default is 10bit only)")
parser.add_option("--no10bit", action="store_true", dest="no10bit", default=False,
	help="Don't do 10bit encode.")
parser.add_option("--bin", dest="bin", default="x264",
	help="Binary filename of the 8bit x264 executable. [x264]")
parser.add_option("--10bitbin", dest="bin10bit", default="x264-10",
	help="Binary filename of the 10bit x264 executable. [x264-10]")
parser.add_option("-s", "--split", dest="split", 
	help="Specify split string. Multi split ; separated. e.g. 00:25:42.166 or 00:25:42.166;00:48:12.325")
parser.add_option("-d", "--dry", action="store_true", dest="debug", default=False,
	help="Debug/Dry run, only print intended commands.")
	
(options, args) = parser.parse_args()
print options
bitdepths = []
encodes = []

if not options.no10bit:
	bitdepths.append("10bit")
if options.do8bit:
	bitdepths.append("8bit")

def cleanfolders(folder, options):
	if exists(folder):
		print "Removing %s" % folder
		if not options.debug:	
			rmtree(folder)
	print "Creating %s" % folder
	if not options.debug:	
		mkdir(folder)

def giveTimeStamp():
	return strftime("[%Y/%m/%d %H:%M:%S] ", gmtime())
		
if options.quick: 
	encodes.append("quick") #lol quick before full
	cleanfolders("quick", options)
if options.tiny: 
	encodes.append("tiny") #lol tiny before others
	cleanfolders("tiny", options)
if options.full: 
	encodes.append("full")
	cleanfolders("full", options)
if options.full720p: 
	encodes.append("full720p") #lol 720p last
	cleanfolders("full720p", options)

if (not options.full) and (not options.quick) and (not options.tiny) and (not options.full720p):
	parser.print_help()
	print "lol watdo? meebe -a --all?"
	exit(1)
else:
	#clean src audio
	cleanfolders("srcaudio", options)
	
if len(args) != 1:
	print "Missing inputfile."
	exit(1)

start = time()

options.infile = args[0]

open("status.txt","w").write("%sSTARTING %s.\n" % (giveTimeStamp(), encodes))
open("status.txt","w").write("%sCleaned folders.\n" % giveTimeStamp())
def runcommand(command, options):
	print command
	if not options.debug:
		#run stuffs
		p = Popen(command, shell=True)
		p.wait()
		if p.returncode == None:
			print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
			print "WHY NOT FINISHED YET????"
			print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
			exit(1)
		elif p.returncode > 0:
			print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
			print "PROGRAM HAVE ERROR: ", p.returncode
			print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
			exit(1)
		elif p.returncode < 0:
			print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
			print "PROGRAM FORCED CLOSE?: ", p.returncode
			print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
			exit(1)

#okay, let's build some commandlines for chaining stuffs...

if not options.split:
	open("status.txt","a").write("%sStarting non-split.\n" % giveTimeStamp())
	#normal single stuffs
	if exists("audio-track1.wav"):
		print "\t\t===== REMOVING audio-track1.wav ====="
		unlink("audio-track1.wav")
	if exists("audio-track2.wav"):
		print "\t\t===== REMOVING audio-track2.wav ====="
		unlink("audio-track2.wav")
	open("status.txt","a").write("%sExtracting audio... " % giveTimeStamp())	
	print "\t===== EXTRACTING AUDIO ====="
	cmd, tracks = buildextractWAV(options.infile)
	runcommand(cmd, options)
	print "\t===== DONE EXTRACTING ====="
	open("status.txt","a").write("done.\n")
	open("status.txt","a").write("%sEncoding audio... " % giveTimeStamp())
	for enc in encodes:
		if enc == "full" and tracks > 1:
			print "\t===== ENCODING SPECIAL AAC TRACK AUDIO ====="
			runcommand(dospecialAAC("epB"), options)
		print "\t===== ENCODING %s AUDIO =====" % enc
		for x in buildencodeAudio(enc , tracks):
			runcommand(x, options)
		print "\t===== DONE %s AUDIO =====" % enc
	open("status.txt","a").write(" done.\n")
	for bitdepth in bitdepths:
		for enc in encodes:
			open("status.txt","a").write("%sEncoding %s %s... " % (giveTimeStamp(), bitdepth, enc))
			print "\t===== ENCODING %s,%s VIDEO =====" % (bitdepth, enc)
			runcommand(buildx264(enc, bitdepth, options), options)
			print "\t===== DONE %s,%s VIDEO =====" % (bitdepth, enc)
			open("status.txt","a").write("done.\n")
			open("status.txt","a").write("%sMuxing %s %s... " % (giveTimeStamp(), bitdepth, enc))
			print "\t===== MUXING %s,%s =====" % (bitdepth, enc)
			runcommand(buildmkvmerge(enc, bitdepth, tracks), options)
			print "\t===== DONE MUXING %s,%s =====" % (bitdepth, enc)
			open("status.txt","a").write("done.\n")
else:
	#splitting stuff
	#setup stuff
	def makeparts(splits):
		parts = []
		
		def getTimedelta(t):
			hours, minutes, rest = t.split(":")
			seconds, milli = [ int(x) for x in rest.split(".")]
			hours, minutes = int(hours), int(minutes)
			return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milli)

		def getDuration(t1, t2):
			t1d = getTimedelta(t1)
			t2d = getTimedelta(t2)
			return str(t2d-t1d)[:-3]

		
		class Part:
			def __init__(self, part, start=None, end=None):
				self.part = part
				self.start = start
				self.end = end
			def __str__(self):
				return self.part
			def __unicode__(self):
				return unicode(self.part)
				
		index = 65
		start = "00:00:00.000"
		for split in splits:
			parts.append(Part("part"+chr(index), start=start, end=getDuration(start, split)))
			index += 1
			start = split
		else:
			parts.append(Part("part"+chr(index), start=start))
		return parts
		
	splits = makeparts(options.split.split(";"))
	#soundpoint, framepoint = getChopPoints(options.infile, options.split)
	open("status.txt", "a").write("%sStarting split.\n" % giveTimeStamp())	
	tracks = 0
	for part in splits:
		if exists("%saudio-track1.wav" % part):
			print "\t\t===== REMOVING %saudio-track1.wav =====" % part
			unlink("%saudio-track1.wav" % part)
		if exists("%saudio-track2.wav" % part):
			print "\t\t===== REMOVING %saudio-track2.wav =====" % part
			unlink("%saudio-track2.wav" % part)

	print "\t===== EXTRACTING AUDIO ====="
	open("status.txt","a").write("%sExtracting audio... " % giveTimeStamp())
	for part in splits:
		#print "\t===== SPLITTING %s AUDIO =====" % part
		#for cmd in buildsoxsplit(tracks, soundpoint, part):
		cmd, tracks = buildextractWAV(options.infile, part)
		runcommand(cmd, options)
	print "\t===== DONE EXTRACTING ====="
	open("status.txt","a").write("done.\n")
	open("status.txt","a").write("%sEncoding audio... " % giveTimeStamp())
	for enc in encodes:
		for part in splits:
			if enc == "full" and tracks > 1:
				print "\t===== ENCODING SPECIAL AAC TRACK AUDIO ====="
				runcommand(dospecialAAC(part), options)
			print "\t===== ENCODING %s %s AUDIO =====" % (part, enc)
			for x in buildencodeAudio(enc, tracks, part):
				runcommand(x, options)
			print "\t===== DONE %s %s AUDIO =====" % (part, enc)
	open("status.txt","a").write(" done.\n")		
	for bitdepth in bitdepths:
		for enc in encodes:
			for part in splits:
				open("status.txt","a").write("%sEncoding %s %s %s... " % (giveTimeStamp(), bitdepth, enc, part))
				print "\t===== ENCODING %s,%s %s VIDEO =====" % (bitdepth, part, enc)
				runcommand(buildffmpegx264(enc, bitdepth, options, part), options)
				print "\t===== DONE %s,%s %s VIDEO =====" % (bitdepth, part, enc)
				open("status.txt","a").write("done.\n")
				open("status.txt","a").write("%sMuxing %s %s %s... " % (giveTimeStamp(), bitdepth, enc, part))
				print "\t===== MUXING %s,%s %s =====" % (bitdepth, part, enc)
				runcommand(buildmkvmerge(enc, bitdepth, tracks, part), options)
				print "\t===== DONE MUXING %s,%s %s =====" % (bitdepth, part, enc)
				open("status.txt","a").write("done.\n")
open("status.txt","a").write("%sCompleted everything. Took: %s\n" % (giveTimeStamp(), str(timedelta(seconds=time()-start))))