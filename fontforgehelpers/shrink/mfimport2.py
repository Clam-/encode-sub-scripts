from codecs import open as codopen
from shutil import copyfile
from os import getcwdu, listdir
from os.path import exists, join, splitext, split, isdir
from time import sleep
from unicodedata import name

from fnmatch import fnmatch

import fontforge

class Globals:
	alphabetdict = {}
	fonts = []
	index = 0
	doneref = False
	tempstuffs = None
	FONTS = "/home/mayuri/substuff/fonts"
	LOOKUPFILE = "fontdb.txt"
	
def genalphabets(fname, fontdb):
	ESCAPE = None
	mode = 0
	#0 start
	#1 styles
	#2 events

	styles = {} # mapping of style to font
	for line in codopen(fname, "rb", "utf-8"):
		line = line.strip()
		if line == "": continue
		
		#pre
		if mode == 0:
			if line == "[V4+ Styles]":
				mode = 1
				continue
		#styles
		if mode == 1:
			if line == "[Events]":
				mode = 2
				continue
			
			istyle, rest = line.split(":",1)
			if istyle == "Format": continue
			elif istyle == "Comment": continue
			
			rest = rest.strip()
			style, font, rest = rest.split(",",2)
			if style not in styles:
				styles[style] = font
			if fontdb[font] not in Globals.alphabetdict:
				if font not in fontdb: 
					print line
					print "---MISSING FONT in DB: %s" % font
					raise NoU
				Globals.alphabetdict[fontdb[font]] = set([])
			
		#Events
		if mode == 2:
			idia, rest = line.split(":",1)
			if idia == "Format": continue
			
			rest = rest.strip()
			fields = rest.split(",",9)
			style = fields[3]
			text = fields[9]
			
			font = styles[style]
			
			escape = False
			comment = False
			index = 0
			while index < len(text):
				if text[index] == ESCAPE:
					index += 1
					escape = True
					continue
				
				if (not escape) and (text[index] == "{"): 
					#find index where closing }
					end = index+1
					index += 1
					while True:
						if text[end] == "}": break
						end += 1
					st = text[index:end]
					if r"\fn" in st:
						commands = st.split("\\")
						for com in commands:
							if com == "fn": font = styles[style]
							elif com[:2] == "fn":
								font = com[2:]
								if font not in fontdb: 
									print line
									print "-MISSING FONT in DB: %s" % font
									raise NoU
								if fontdb[font] not in Globals.alphabetdict:
									Globals.alphabetdict[fontdb[font]] = set([])
					index = end+1
					continue
				charnum = ord(text[index])
				if charnum == 32:
					Globals.alphabetdict[fontdb[font]].add("space")
				Globals.alphabetdict[fontdb[font]].add(charnum)
				index += 1
	return

def removeGlyphs(font, characters, refs, keep):
	for gname in font:
		if gname in keep: continue
		#check if gname in refs
		if gname in refs: continue
		if gname in font:
			if font[gname].unicode >= 0:
				#unicode codepoint, check if it character set
				if font[gname].unicode not in characters:
					#remove the glyph
					try:
						font.removeGlyph(font[gname])
					except:
						print "Already removed(1)"
			else:
				#remove the glyph
				try:
					font.removeGlyph(font[gname])
				except:
					print "Already removed(2)"
		else:
			print "Already removed? %s" % gname

def findreferences(font, characters):
	refs = set([])
	size = len(refs)
	keep = set([])
	for gname in font:
		if gname in characters:
			keep.add(gname)
			#make sure to keep all variants (And their references?)
			sleep(0)
			for info in font[gname].getPosSub("*"):
				if info[1] == "Substitution":
					print "SUBS FOR:", gname
					if len(info) != 3:
						print "WARNING MORE THAN THINGS:", info
					if info[2] not in keep:
						print "adding:", info[2]
						keep.add(info[2])
						if font[info[2]].references:
							print "SUB REFERENCES"
							for ref in font[info[2]].references:
								refs.add(ref[0]) #added glyphname
				elif info[1] == "AltSubs":
					print "ALTSUBS FOR:", gname
					for index in range(2,len(info)):
						if info[index] not in keep:
							print "adding:", info[index]
							keep.add(info[index])
							if font[info[index]].references:
								print "ALTSUB REFERENCES"
								for ref in font[info[index]].references:
									refs.add(ref[0]) #added glyphname
						
				elif info[1] == "Pair": pass
				elif info[1] == "Position": pass
				else:
					print "WARNING, UNKNOWN THING:", info
			sleep(0)
			if font[gname].references:
				print "GLYPH REFERENCES"
				for ref in font[gname].references:
					refs.add(ref[0]) #added glyphname
			sleep(0)
			
		if gname in font:
			if font[gname].unicode >= 0:
				# if font[gname].unicode == 12288:
					# print "FOUND SPECIAL", gname
				# elif font[gname].unicode == 12288:
					# print "FOUND SPECIAL", gname
				#check for wanted char then get references
				if font[gname].unicode in characters:
					keep.add(gname)
					#make sure to keep all variants (And their references?)
					sleep(0)
					for info in font[gname].getPosSub("*"):
						if info[1] == "Substitution":
							print "SUBS FOR:", gname
							if len(info) != 3:
								print "WARNING MORE THAN THINGS:", info
							if info[2] not in keep:
								print "adding:", info[2]
								keep.add(info[2])
								if font[info[2]].references:
									print "SUB REFERENCES"
									for ref in font[info[2]].references:
										refs.add(ref[0]) #added glyphname
						elif info[1] == "AltSubs":
							print "ALTSUBS FOR:", gname
							for index in range(2,len(info)):
								if info[index] not in keep:
									print "adding:", info[index]
									keep.add(info[index])
									if font[info[index]].references:
										print "ALTSUB REFERENCES"
										for ref in font[info[index]].references:
											refs.add(ref[0]) #added glyphname
								
						elif info[1] == "Pair": pass
						elif info[1] == "Position": pass
						else:
							print "WARNING, UNKNOWN THING:", info
					sleep(0)
					if font[gname].references:
						print "GLYPH REFERENCES"
						for ref in font[gname].references:
							refs.add(ref[0]) #added glyphname
					sleep(0)
	while size != len(refs):
		size = len(refs)
		for gname in refs:
			if font[gname].references:
				print "GLYPH -REF- REFERENCES"
				sleep(0.5)
				for ref in font[gname].references:
					refs.add(ref[0]) #added glyphname
	return refs, keep

def setup(dirname):
	if not exists(dirname) or not isdir(dirname): 
		fontforge.postError("ERROR:", "This is not a folder, or whatever it is, it doesn't exist.\nTry Again.")
		return
	
	if len(listdir(dirname)) == 0:
		fontforge.postError("ERROR:", "There are no files in this folder... You want only subtitle script and commentary script if there is one.")
		return
	
	fontdb = {}
	alternatives = {}
	for line in codopen(join(Globals.FONTS, Globals.LOOKUPFILE),"rb","utf-8"):
		line = line.strip()
		if not line: continue
		
		friendly, fname = line.split("|",1)
		fnames = fname.split("|")
		fontdb[friendly] = fnames[0]
		if len(fnames) > 1:
			if friendly in alternatives:
				alternatives[friendly].extend(fnames[1:])
			else:
				alternatives[friendly] = fnames[1:]
	
	for subfile in listdir(dirname):
		if fnmatch(subfile, "*.ass"):
			print "Processing: %s" % subfile
			genalphabets(join(dirname, subfile), fontdb)
	
	for friendly in alternatives:
		for fname in alternatives[friendly]:
			Globals.alphabetdict[fname] = Globals.alphabetdict[fontdb[friendly]]
	
	Globals.fonts = sorted(Globals.alphabetdict.keys())
	
	Globals.index = 0
	Globals.refs = set([])
	Globals.keep = set([])
	
	Globals.suffix = split(dirname)[1]
	Globals.fontpath = dirname
	print "SETTED UP"
				
def loadnext():
	bail = False
	while Globals.index < len(Globals.fonts):
		print "AT INDEX: %s of %s" % (Globals.index, len(Globals.fonts)-1)
		print Globals.fonts
		Globals.tempstuffs = None
		fontname = Globals.fonts[Globals.index]
		if fontname == "MSMINCHO.TTF": 
			print "WARNING BAD FONT: %s" % fontname
			print "EXITING. GET BETTER SCRIPT"
			raise NoU
		
		print "	================"
		#print "	==========", characters
		
		p = join(Globals.FONTS, fontname)
		print "OPENING FONT: %s" % p
		Globals.font = fontforge.open(p)
		font = Globals.font
		
		if font.iscid:
			print "LOL CID INCOMING AAAA"
			#font.cidFlatten()
		Globals.doneref = False
		print "LOADED."
		sleep(3)
		findrefs()
		sleep(3)
		if not shrink():
			print "Error found, not continuing after save..."
			bail = True
		sleep(3)
		savenow()
		sleep(2)
		if bail:
			break

def loadman():
	print "AT INDEX:", Globals.index
	Globals.tempstuffs = None
	fontname = Globals.fonts[Globals.index]
	if fontname == "MSMINCHO.TTF": 
		print "WARNING BAD FONT: %s" % fontname
		print "EXITING. GET BETTER SCRIPT"
		raise NoU
	
	print "	================"
	#print "	==========", characters
	
	p = join(Globals.FONTS, fontname)
	print "OPENING FONT: %s" % p
	Globals.font = fontforge.open(p)
	font = Globals.font
	
	if font.iscid:
		print "LOL CID INCOMING AAAA"
		#font.cidFlatten()
	Globals.doneref = False
	print "LOADED."

def findrefman():
	print "FINDING REFS"
	alphabetdict = Globals.alphabetdict
	characters = alphabetdict[Globals.fonts[Globals.index]]
	#lol cid
	font = Globals.font

	refs, keep = findreferences(font, characters)
	Globals.refs.update(refs)
	Globals.keep.update(keep)
	Globals.doneref = True
	print "FOUND REFERENCES", Globals.refs
	
def findrefs():
	print "FINDING REFS"
	alphabetdict = Globals.alphabetdict
	characters = alphabetdict[Globals.fonts[Globals.index]]
	#lol cid
	font = Globals.font
	if font.iscid:
		print "lol cid"
		for x in range(font.cidsubfontcnt):
			font.cidsubfont = x
			print x, ":", font
			sleep(1.5)
			refs, keep = findreferences(font, characters)
			Globals.refs.update(refs)
			Globals.keep.update(keep)
			sleep(1.5)
		
	else:
		refs, keep = findreferences(font, characters)
		Globals.refs.update(refs)
		Globals.keep.update(keep)
	Globals.doneref = True
	print "FOUND REFERENCES", Globals.refs
	
def shrink():
	print "MINIMIZING FONT..."
	if not Globals.doneref:
		print "WARNING: NOT SEARCHED FOR REFS YET. Bailing..."
		return
	alphabetdict = Globals.alphabetdict
	characters = alphabetdict[Globals.fonts[Globals.index]]
	
	refs, keep = Globals.refs, Globals.keep
	print "REFERENCES:", refs
	print "KEEP:", keep
	font = Globals.font
	print "Still MINIMIZING FONT..."
	if font.iscid:
		print "lol cid"
		for x in range(font.cidsubfontcnt):
			font.cidsubfont = x
			print x, ":", font
			sleep(1)
			removeGlyphs(font, characters, refs, keep)
			sleep(1)
	else:
		removeGlyphs(font, characters, refs, keep)
	print "SHRUNK."
	new = set(list(characters))
	#lol this will be lame for cid's
	if font.iscid:
		print "lol cid"
		for x in range(font.cidsubfontcnt):
			font.cidsubfont = x
			print x, ":", font
			sleep(1)
			for gname in font:
				if gname in font:
					if gname in font:
						try: new.remove(gname)
						except: pass
			
					if font[gname].unicode >= 0:
						try: new.remove(font[gname].unicode)
						except: pass
			sleep(1)
	else:
		for gname in font:
			if gname in font:
				try: new.remove(gname)
				except: pass
			
			if font[gname].unicode >= 0:
				try: new.remove(font[gname].unicode)
				except: pass
	if new:
		print "DID THE FONT EVER HAVE THIS? :", new
		return False
	return True
		
def shrinkman():
	print "MINIMIZING FONT"
	if not Globals.doneref:
		print "WARNING: NOT SEARCHED FOR REFS YET. Bailing..."
		return
	alphabetdict = Globals.alphabetdict
	characters = alphabetdict[Globals.fonts[Globals.index]]
	refs, keep = Globals.refs, Globals.keep
	font = Globals.font
	
	removeGlyphs(font, characters, refs, keep)
	print "Done this."
	
def checkthings():
	alphabetdict = Globals.alphabetdict
	characters = alphabetdict[Globals.fonts[Globals.index]]
	refs, keep = Globals.refs, Globals.keep
	font = Globals.font
	if Globals.tempstuffs == None:
		Globals.tempstuffs = set(list(characters))
	#lol this will be lame for cid's
	for gname in font:
		if gname in font:
			try: Globals.tempstuffs.remove(gname)
			except: pass
			if font[gname].unicode >= 0:
				try: Globals.tempstuffs.remove(font[gname].unicode)
				except: pass
	if Globals.tempstuffs:
		print "DID THE FONT EVER HAVE THIS? :", Globals.tempstuffs
	print "dont chek"
		
def savenow():
	fontname = Globals.fonts[Globals.index]
	Globals.index += 1
	if Globals.index >= len(Globals.fonts):
		fontforge.postError("Done.", "Done, stop now")
	else:
		pass
		#fontforge.postError("Done.", "Ready to save and proceed")
	
	fbase, fext = splitext(fontname)
	
	newfname = join(Globals.fontpath, "%s-%s%s" % (fbase, Globals.suffix, fext) )
	#print "SAVE AS THIS FNAME:", newfname
	font = Globals.font
	print "SAVING NEW FONT... (%s)" % newfname
	font.generate(newfname)
	print "DONE."
	font.close()
	print "	================"
	
def savealphabets():
	f = codopen(join(Globals.fontpath, "alphabets.txt"), "wb", "utf-8")
	for key in Globals.alphabetdict:
		f.write("FOR %s:\n" % key)
		for character in Globals.alphabetdict[key]:
			if type(character) is int:
				unichar = unichr(character)
				f.write("\t%s - %s\n" % (unichar, name(unichar)))
