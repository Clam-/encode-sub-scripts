from subprocess import Popen, PIPE
from os.path import exists
from os import unlink
from sys import exit

from datetime import timedelta

#lol 
#ffmpeg -i somefile.avi -vcodec copy -f rawvideo -y /dev/null 2>&1 | tr "^M" '\n' | grep '^frame=' | perl -pe 's/^frame=\s*([0-9]+)\s.*$/\1/' | tail -n 1

class Presets:
	x264 = {	
		"quick" : "--preset veryfast --tune animation --crf 22",
		"full" : "--preset placebo --tune animation --crf 14",
		"full720p" : "--preset placebo --tune animation --crf 17 --vf resize:width=1280,height=720,method=spline36",
		"tiny" : "--preset fast --tune animation --crf 20 --vf resize:width=854,height=480,method=bilinear"
	}
	
	x264command = '"{bin}" {pipe}{splitstuff}{options} --output "{outfile}" "{infile}"'
	
	wavfiles = ("srcaudio/{prefix}audio-track1.wav", "srcaudio/{prefix}audio-track2.wav")
	
	audio = {
		"quick" : '~/neroAacEnc -q 0.55 -if "{infile}" -of "{outfile}"',
		"full" : 'flac --output-name="{outfile}" -8 "{infile}"',
		"full720p" : '~/neroAacEnc -q 0.55 -if "{infile}" -of "{outfile}"',
		"tiny" : '~/neroAacEnc -q 0.55 -if "{infile}" -of "{outfile}"'
	}
	audiofiles = {
		"quick" : 'quick/%saudio-track%s.m4a',
		"full" : 'full/%saudio-track%s.flac',
		"full720p" : 'full720p/%saudio720p-track%s.m4a',
		"tiny" : 'tiny/%saudio480p-track%s.m4a',
		"fullspecial" : 'full/%saudio-track%s.m4a'
	}
	
	ffmpegaudio = 'ffmpeg -i "{infile}" -vn -map 0:1 {stripstuff}{bitdepth}{track}'
	ffmpegaudio2 = 'ffmpeg -i "{infile}" -vn -map 0:1 {stripstuff}{bitdepth1}{track1} -map 0:2 {stripstuff}{bitdepth2}{track2}'
	
	sox = 'sox {srcinput} {outfile} trim {startstop}'
	
	mkvfiles = {
		"quick" : '%s%sQUICK-CRF22-aac-mux.mkv',
		"full" : '%s%sFULL-CRF14-flac-mux.mkv',
		"full720p" : '%s%s720p-CRF17-aac-mux.mkv',
		"tiny" :  '%s%s480p-CRF20-aac-mux.mkv'
	}
	
	x264filenames = {
		"quick" : "quick/%s%sCRF22.mkv",
		"full" : "full/%s%sCRF14.mkv",
		"full720p" : "full720p/%s%s720p-CRF17.mkv",
		"tiny" : "tiny/%s%s480p-CRF20.mkv"
	}
	ffmpegfilenames = {
		"quick" : "quick/%s-CRF22.mp4",
		"full" : "full/%s-CRF14.mp4",
		"full720p" : "full720p/%s-720p-CRF17.mp4",
		"tiny" : "tiny/%s-480p-CRF20.mp4"
	}

	ffmpegx264 = {
		"quick" : 'ffmpeg -i "{infile}" -an {stripstuff}-f yuv4mpegpipe pipe: | {x264}',
		"full" : 'ffmpeg -i "{infile}" -an {stripstuff}-f yuv4mpegpipe pipe: | {x264}',
		"full720p" : 'ffmpeg -i "{infile}" -an {stripstuff}-f yuv4mpegpipe pipe: | {x264}',
		"tiny" : 'ffmpeg -i "{infile}" -an {stripstuff}-f yuv4mpegpipe pipe: | {x264}'
	}
	
	# ffmpegx264 = {
		# "quick" : 'ffmpeg -i "{infile}" -an {stripstuff}-vcodec libx264 -preset veryfast -tune animation -crf 22 -threads 0 {outfile}',
		# "full" : 'ffmpeg -i "{infile}" -an {stripstuff}-vcodec libx264 -preset placebo -tune animation -crf 14 -threads 0 {outfile}',
		# "full720p" : 'ffmpeg -sws_flags spline36 -i "{infile}" -an {stripstuff}-vcodec libx264 -preset placebo -tune animation -crf 14 -threads 0 -vf scale=1280:720 {outfile}',
		# "tiny" : 'ffmpeg -sws_flags bilinear -i "{infile}" -an {stripstuff}-vcodec libx264 -preset fast -tune animation -crf 20 -threads 0 -vf scale=854:480 {outfile}'
	# }
	
	mkvmerge = 'mkvmerge -o "{mkvoutname}" \
"--language" "0:jpn" "--track-name" "0:Video track" "--default-track" "0:yes" "--forced-track" "0:no" "--display-dimensions" "0:{vidres}" "-d" "0" "-A" "-S" "-T" "--no-global-tags" "--no-chapters" "{inputvideo}" \
"--language" "{trackno}:jpn" "--track-name" "{trackno}:Audio track" "--default-track" "{trackno}:yes" "--forced-track" "{trackno}:no" "-a" "{trackno}" "-D" "-S" "-T" "--no-global-tags" "--no-chapters" "{audiotrack}"'
	
	mkvmerge2 = 'mkvmerge -o "{mkvoutname}" \
"--language" "0:jpn" "--track-name" "0:Video track" "--default-track" "0:yes" "--forced-track" "0:no" "--display-dimensions" "0:{vidres}" "-d" "0" "-A" "-S" "-T" "--no-global-tags" "--no-chapters" "{inputvideo}" \
"--language" "{trackno1}:jpn" "--track-name" "{trackno1}:Audio track" "--default-track" "{trackno1}:yes" "--forced-track" "{trackno1}:no" "-a" "{trackno1}" "-D" "-S" "-T" "--no-global-tags" "--no-chapters" "{audiotrack1}" \
"--language" "{trackno2}:jpn" "--track-name" "{trackno2}:Audio track - Commentary" "--default-track" "{trackno2}:no" "--forced-track" "{trackno2}:no" "-a" "{trackno2}" "-D" "-S" "-T" "--no-global-tags" "--no-chapters" "{audiotrack2}"'

	tracktable = { "quick": 0, "full": 0, "fullspecial": 0, "full720p": 0 , "tiny": 0 }
	displayres = { "quick": "1920x1080", "full": "1920x1080", "full720p": "1280x720", "tiny": "854x480"}


def getSec(s):
	s, e = s.split(".")
	l = s.split(':')
	return (int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])) + float("0."+e)
	
	
def getChopPoints(infile, s=""):
	ret = Popen('mediainfo --Inform="Video;%FrameRate%" {infile}'.format(infile=infile), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
	fps = ret[0]
	print "FRAME RATE : ", fps
	fcp = int(round(getSec(s)*float(fps)))
	print "FRAME CHOP POINT: ", fcp
	slen = fcp/float(fps)
	print "TIME LENGTH OF CHOP: ", slen, str(timedelta(seconds=slen))
	return (str(timedelta(seconds=slen)), fcp)
	
def buildx264(enc, bitdepth, options, part=""):
	fname = Presets.x264filenames[enc] % (bitdepth, ("%s-" % part) if part else part)
	if exists(fname):
		print "\t\t===== REMOVING %s =====" % fname
		unlink(fname)
	if bitdepth == "8bit": bin = options.bin
	else: bin = options.bin10bit
	
	splitstuff=""
	
	return Presets.x264command.format(pipe="", bin=bin, splitstuff=splitstuff, options=Presets.x264[enc], outfile=fname, infile=options.infile)
	
def buildffmpegx264(enc, bitdepth, options, part=""):
	fname = Presets.x264filenames[enc] % (bitdepth, ("%s-" % part) if part else part)
	if exists(fname):
		print "\t\t===== REMOVING %s =====" % fname
		unlink(fname)
	if bitdepth == "8bit": bin = options.bin
	else: bin = options.bin10bit
	#stripstuff
	stripstuff = ""
	if part:
		if part.end:
			stripstuff = "-ss %s -t %s " % (part.start, part.end)
		else:
			stripstuff = "-ss %s " % (part.start)
		
	x264cmd = Presets.x264command.format(pipe="--demuxer y4m ", bin=bin, splitstuff="", options=Presets.x264[enc], outfile=fname, infile="-")
	return Presets.ffmpegx264[enc].format(infile=options.infile, stripstuff=stripstuff, x264=x264cmd)
	
def buildextractWAV(infile, part=""):
	#determine bitdepth of audio stream using MediaInfo
	#run thus mediainfo --Inform="Audio;%BitDepth%-" infile
	ret = Popen('mediainfo --Inform="Audio;%BitDepth%-" {infile}'.format(infile=infile), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()
	print "MEDIAINFO SETTINGS : ", ret[0]
	bitdepths = []
	for bit in ret[0].split("-"):
		bit = bit.strip()
		if bit == "": continue
		if bit == "24":
			bitdepths.append("-acodec pcm_s24le ")
		else:
			bitdepths.append("")
	print "BITDEPTH SETTINGS: ", repr(bitdepths)
	
	stripstuff = ""
	if part:
		if part.end:
			stripstuff = "-ss %s -t %s " % (part.start, part.end)
		else:
			stripstuff = "-ss %s " % (part.start)
			
	track1 = Presets.wavfiles[0].format(prefix=part)
	if len(bitdepths) == 1:
		return Presets.ffmpegaudio.format(infile=infile, stripstuff=stripstuff, bitdepth=bitdepths[0], track=track1), 1
	if len(bitdepths) >1:
		track2 = Presets.wavfiles[1].format(prefix=part)
		return Presets.ffmpegaudio2.format(infile=infile, stripstuff=stripstuff, bitdepth1=bitdepths[0], bitdepth2=bitdepths[1], track1=track1, track2=track2), 2

def buildsoxsplit(tracks, s="", part=""):
	#assume raw file already made, check and abort if not there:
	for x in range(tracks):
		fname = Presets.wavfiles[x].format(prefix="")
		if not exists(fname):
			print "SOURCE AUDIO NOT FOUND."
			exit(1)
	
	startstop = "%s %s"
	if part == "epA": startstop = startstop % (0, s)
	elif part == "epB": startstop = startstop % (s, "")
	else: 
		print "WRONG PART"
		exit(1)
	
	cmds = []
	for x in range(tracks):
		src = Presets.wavfiles[x].format(prefix="")
		#'sox {srcinput} {outfile} trim {startstop}'
		cmds.append(Presets.sox.format(srcinput=src, outfile=Presets.wavfiles[x].format(prefix=part), startstop=startstop))
	return cmds
	
def dospecialAAC(part):
	track2=Presets.wavfiles[1].format(prefix=part)
	return Presets.audio["quick"].format(infile=track2, outfile=Presets.audiofiles["fullspecial"] % (part, "2"))
	
def buildencodeAudio(enc, tracks, part=""):
	#if 2 tracks, if flac do an AAC anyways
	# if exists(Presets.audiofiles[enc] % (part, "1")):
		# print "\t\t===== REMOVING %s =====" % (Presets.audiofiles[enc] % (part, "1"))
		# unlink(Presets.audiofiles[enc] % (part, "1"))
	# if exists(Presets.audiofiles[enc] % (part, "2")):
		# print "\t\t===== REMOVING %s =====" % (Presets.audiofiles[enc] % (part, "2"))
		# unlink(Presets.audiofiles[enc] % (part, "2"))
	track1=Presets.wavfiles[0].format(prefix=part)
	if tracks == 1:
		return (Presets.audio[enc].format(infile=track1, outfile=Presets.audiofiles[enc] % (part, "")), )
	if tracks > 1:
		track2=Presets.wavfiles[1].format(prefix=part)
		return (Presets.audio[enc].format(infile=track1, outfile=Presets.audiofiles[enc] % (part, "1")), 
			Presets.audio[enc].format(infile=track2, outfile=Presets.audiofiles[enc] % (part, "2")))

def buildmkvmerge(enc, bitdepth, tracks, part=""):
	fname = Presets.mkvfiles[enc] % (bitdepth, part)
	if exists(fname):
		print "\t\t===== REMOVING %s =====" % fname
		unlink(fname)
	invid = Presets.x264filenames[enc] % (bitdepth, ("%s-" % part) if part else part)
	if tracks == 1:
		return Presets.mkvmerge.format(mkvoutname=fname, inputvideo=invid, 
			audiotrack=Presets.audiofiles[enc] % (part, ""), trackno=Presets.tracktable[enc], vidres=Presets.displayres[enc])
	elif tracks > 1:
		trackno1 = Presets.tracktable[enc]
		if enc == "full":
			audiotrack2 = Presets.audiofiles["fullspecial"] % (part, "2")
			trackno2 = Presets.tracktable["fullspecial"]
		else:
			audiotrack2 = Presets.audiofiles[enc] % (part, "2")
			trackno2 = Presets.tracktable[enc]
		return Presets.mkvmerge2.format(mkvoutname=fname, inputvideo=invid, 
			audiotrack1=Presets.audiofiles[enc] % (part, "1"), audiotrack2=audiotrack2, trackno1=trackno1,
			trackno2=trackno2, vidres=Presets.displayres[enc])