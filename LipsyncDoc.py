# Papagayo, a lip-sync tool for use with Lost Marble's Moho
# Copyright (C) 2005 Mike Clifton
# Contact information at http://www.lostmarble.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import codecs
import ConfigParser
import wx

from utilities import *
from PronunciationDialog import PronunciationDialog
import SoundPlayer
import traceback
import sys
import breakdowns
import copy
import math

strip_symbols = '.,!?;-/()"'
strip_symbols += u'\N{INVERTED QUESTION MARK}'


###############################################################

class LipsyncPhoneme(object):
	def __init__(self, parent):
		self.parent = parent
		self.text = ""
		self._frame = 0
		self.percentage = 0;
	
	@property
	def frame(self):
		return self._frame
	
	@frame.setter
	def frame(self, value):
		self.percentage = (value - self.parent.startFrame) / float(self.parent.endFrame - self.parent.startFrame)
		self._frame = value
		
	# May only be called if other phonemes are not affected by the previous change.
	def RepositionAndConstrain(self):
		self.Reposition()
		self.Constrain()
	
	def Reposition(self):
		parent = self.parent
		# Set value by percentage.
		self._frame = int(parent.startFrame + self.percentage * (parent.endFrame - parent.startFrame))

	def Constrain(self):
		parent = self.parent
		# Constrain by predecessor and successor bounds.
		index = parent.phonemes.index(self)
		if index < len(parent.phonemes)-1:
			self._frame = min(self._frame, parent.phonemes[index+1]._frame - 1)
		if index > 0:
			self._frame = max(self._frame, parent.phonemes[index-1]._frame + 1)
		# Constrain by parent bounds.
		self._frame = max(self._frame, parent.startFrame)
		self._frame = min(self._frame, parent.endFrame)

###############################################################

class LipsyncWord(object):
	def __init__(self, parent):
		self.parent = parent
		self.text = ""
		self._startFrame = 0
		self._endFrame = 0
		self.startPercentage = 0;
		self.endPercentage = 0;
		self.phonemes = []

	@property
	def startFrame(self):
		return self._startFrame
		
	@startFrame.setter
	def startFrame(self, value):
		self.startPercentage = (value - self.parent.startFrame) / float(self.parent.endFrame - self.parent.startFrame)
		self._startFrame = value
		
	@property
	def endFrame(self):
		return self._endFrame
		
	@endFrame.setter
	def endFrame(self, value):
		self.endPercentage = (value - self.parent.startFrame) / float(self.parent.endFrame - self.parent.startFrame)
		self._endFrame = value
	
	# May only be called if other words are not affected by the previous change.
	def RepositionAndConstrain(self):
		self.Reposition()
		self.Constrain()
	
	def Reposition(self):
		parent = self.parent;
		# Set values by percentage.
		self._startFrame = int(parent.startFrame + self.startPercentage * (parent.endFrame - parent.startFrame))
		self._endFrame = int(parent.startFrame + self.endPercentage * (parent.endFrame - parent.startFrame))
		# Reposition phonemes.
		for phoneme in self.phonemes:
			phoneme.Reposition()
		
	def Constrain(self):
		parent = self.parent
		# Constrain by predecessor and successor bounds.
		index = parent.words.index(self)
		if index < len(parent.words)-1:
			self._endFrame = min(self._endFrame, parent.words[index+1]._startFrame - 1)
		if index > 0:
			self._startFrame = max(self._startFrame, parent.words[index-1]._endFrame + 1)
		# Constrain by parent bounds.
		self._startFrame = max(self._startFrame, parent.startFrame)
		self._endFrame = min(self._endFrame, parent.endFrame)
		# Constrain phonemes.
		for phoneme in self.phonemes:
			phoneme.Constrain()
	
	def RunBreakdown(self, parentWindow, language, languagemanager, phonemeset):
		self.phonemes = []
		try:
			text = self.text.strip(strip_symbols)
			details = languagemanager.language_table[language]
			if details["type"] == "breakdown":
				exec("import %s as breakdown" % details["breakdown_class"])
				pronunciation_raw = breakdown.breakdownWord(text)
			elif details["type"] == "dictionary":
				if languagemanager.current_language != language:
					languagemanager.LoadLanguage(details)
					languagemanager.current_language = language
				if details["case"] == "upper":
					pronunciation_raw = languagemanager.raw_dictionary[text.upper()]
				elif details["case"] == "lower":
					pronunciation_raw = languagemanager.raw_dictionary[text.lower()]
				else:
					pronunciation_raw = languagemanager.raw_dictionary[text]
			else:
				pronunciation_raw = phonemeDictionary[text.upper()]

			pronunciation = []
			for i in range(len(pronunciation_raw)):
				try:
					pronunciation.append(phonemeset.conversion[pronunciation_raw[i]])
				except:
					print "Unknown phoneme:", pronunciation_raw[i], "in word:", text
			
			for p in pronunciation:
				if len(p) == 0:
					continue
				phoneme = LipsyncPhoneme(self)
				phoneme.text = p
				self.phonemes.append(phoneme)
		except:
			traceback.print_exc()
			# this word was not found in the phoneme dictionary
			dlg = PronunciationDialog(parentWindow, phonemeset.set)
			dlg.wordLabel.SetLabel(dlg.wordLabel.GetLabel() + ' ' + self.text)
			if dlg.ShowModal() == wx.ID_OK:
				for p in dlg.phonemeCtrl.GetValue().split():
					if len(p) == 0:
						continue
					phoneme = LipsyncPhoneme(self)
					phoneme.text = p
					self.phonemes.append(phoneme)
			dlg.Destroy()

###############################################################

class LipsyncPhrase:
	def __init__(self):
		self.text = ""
		self.startFrame = 0
		self.endFrame = 0
		self.words = []

	def RunBreakdown(self, parentWindow, language, languagemanager, phonemeset):
		self.words = []
		for w in self.text.split():
			if len(w) == 0:
				continue
			word = LipsyncWord(self)
			word.text = w
			self.words.append(word)
		for word in self.words:
			word.RunBreakdown(parentWindow, language, languagemanager, phonemeset)

###############################################################

class LipsyncVoice:
	def __init__(self, name = "Voice"):
		self.name = name
		self.text = ""
		self.phrases = []

	def RunBreakdown(self, frameDuration, parentWindow, language, languagemanager, phonemeset):
		# make sure there is a space after all punctuation marks
		repeatLoop = True
		while repeatLoop:
			repeatLoop = False
			for i in range(len(self.text) - 1):
				if (self.text[i] in ".,!?;-/()") and (not self.text[i + 1].isspace()):
					self.text = self.text[:i + 1] + ' ' + self.text[i + 1:]
					repeatLoop = True
					break
		# break text into phrases
		self.phrases = []
		for line in self.text.splitlines():
			if len(line) == 0:
				continue
			phrase = LipsyncPhrase()
			phrase.text = line
			self.phrases.append(phrase)
		# now break down the phrases
		for phrase in self.phrases:
			phrase.RunBreakdown(parentWindow, language, languagemanager, phonemeset)
		# for first-guess frame alignment, count how many phonemes we have
		phonemeCount = 0
		for phrase in self.phrases:
			for word in phrase.words:
				if len(word.phonemes) == 0: # deal with unknown words
					phonemeCount = phonemeCount + 4
				for phoneme in word.phonemes:
					phonemeCount = phonemeCount + 1
		# now divide up the total time by phonemes
		if frameDuration > 0 and phonemeCount > 0:
			framesPerPhoneme = int(float(frameDuration) / float(phonemeCount))
			if framesPerPhoneme < 1:
				framesPerPhoneme = 1
		else:
			framesPerPhoneme = 1
		# finally, assign frames based on phoneme durations
		curFrame = 0
		for phrase in self.phrases:
			for word in phrase.words:
				for phoneme in word.phonemes:
					phoneme.frame = curFrame
					curFrame = curFrame + framesPerPhoneme
				if len(word.phonemes) == 0: # deal with unknown words
					word.startFrame = curFrame
					word.endFrame = curFrame + 3
					curFrame = curFrame + 4
				else:
					word.startFrame = word.phonemes[0].frame
					word.endFrame = word.phonemes[-1].frame + framesPerPhoneme - 1
			phrase.startFrame = phrase.words[0].startFrame
			phrase.endFrame = phrase.words[-1].endFrame

	def RepositionPhrase(self, phrase, lastFrame):
		id = 0
		for i in range(len(self.phrases)):
			if phrase is self.phrases[i]:
				id = i
		if (id > 0) and (phrase.startFrame < self.phrases[id - 1].endFrame + 1):
			phrase.startFrame = self.phrases[id - 1].endFrame + 1
			if phrase.endFrame < phrase.startFrame + 1:
				phrase.endFrame = phrase.startFrame + 1
		if (id < len(self.phrases) - 1) and (phrase.endFrame > self.phrases[id + 1].startFrame - 1):
			phrase.endFrame = self.phrases[id + 1].startFrame - 1
			if phrase.startFrame > phrase.endFrame - 1:
				phrase.startFrame = phrase.endFrame - 1
		if phrase.startFrame < 0:
			phrase.startFrame = 0
		if phrase.endFrame > lastFrame:
			phrase.endFrame = lastFrame
		if phrase.startFrame > phrase.endFrame - 1:
			phrase.startFrame = phrase.endFrame - 1
		# First reposition all words.
		for word in phrase.words:
			word.Reposition()
		# Then constrain to sibling bounds.
		for word in phrase.words:
			word.Constrain()

	def Open(self, inFile):
		self.name = inFile.readline().strip()
		tempText = inFile.readline().strip()
		self.text = tempText.replace('|','\n')
		numPhrases = int(inFile.readline())
		for p in range(numPhrases):
			phrase = LipsyncPhrase()
			phrase.text = inFile.readline().strip()
			phrase.startFrame = int(inFile.readline())
			phrase.endFrame = int(inFile.readline())
			numWords = int(inFile.readline())
			for w in range(numWords):
				word = LipsyncWord(phrase)
				wordLine = inFile.readline().split()
				word.text = wordLine[0]
				word.startFrame = int(wordLine[1])
				word.endFrame = int(wordLine[2])
				numPhonemes = int(wordLine[3])
				for p in range(numPhonemes):
					phoneme = LipsyncPhoneme(word)
					phonemeLine = inFile.readline().split()
					phoneme.frame = int(phonemeLine[0])
					phoneme.text = phonemeLine[1]
					word.phonemes.append(phoneme)
				phrase.words.append(word)
			self.phrases.append(phrase)

	def Save(self, outFile):
		outFile.write("\t%s\n" % self.name)
		tempText = self.text.replace('\n','|')
		outFile.write("\t%s\n" % tempText)
		outFile.write("\t%d\n" % len(self.phrases))
		for phrase in self.phrases:
			outFile.write("\t\t%s\n" % phrase.text)
			outFile.write("\t\t%d\n" % phrase.startFrame)
			outFile.write("\t\t%d\n" % phrase.endFrame)
			outFile.write("\t\t%d\n" % len(phrase.words))
			for word in phrase.words:
				outFile.write("\t\t\t%s %d %d %d\n" % (word.text, word.startFrame, word.endFrame, len(word.phonemes)))
				for phoneme in word.phonemes:
					outFile.write("\t\t\t\t%d %s\n" % (phoneme.frame, phoneme.text))

	def GetPhonemeAtFrame(self, frame):
		for phrase in self.phrases:
			if (frame <= phrase.endFrame) and (frame >= phrase.startFrame):
				# we found the phrase that contains this frame
				word = None
				for w in phrase.words:
					if (frame <= w.endFrame) and (frame >= w.startFrame):
						word = w # the frame is inside this word
						break
				if word is not None:
					# we found the word that contains this frame
					for i in range(len(word.phonemes) - 1, -1, -1):
						if frame >= word.phonemes[i].frame:
							return word.phonemes[i].text
				break
		return "rest"

	def Export(self, path):
		if len(self.phrases) > 0:
			startFrame = self.phrases[0].startFrame
			endFrame = self.phrases[-1].endFrame
		else:
			startFrame = 0
			endFrame = 1
		outFile = open(path, 'w')
		outFile.write("MohoSwitch1\n")
		phoneme = ""
		for frame in range(startFrame, endFrame + 1):
			nextPhoneme = self.GetPhonemeAtFrame(frame)
			if nextPhoneme != phoneme:
				if phoneme == "rest":
					# export an extra "rest" phoneme at the end of a pause between words or phrases
					outFile.write("%d %s\n" % (frame, phoneme))
				phoneme = nextPhoneme
				outFile.write("%d %s\n" % (frame + 1, phoneme))
		outFile.close()

	def ExportAlelo(self, path, language, languagemanager):
		outFile = open(path, 'w')
		for phrase in self.phrases:
			for word in phrase.words:
				text = word.text.strip(strip_symbols)
				details = languagemanager.language_table[language]
				if languagemanager.current_language != language:
					languagemanager.LoadLanguage(details)
					languagemanager.current_language = language
				if details["case"] == "upper":
					pronunciation = languagemanager.raw_dictionary[text.upper()]
				elif details["case"] == "lower":
					pronunciation = languagemanager.raw_dictionary[text.lower()]
				else:
					pronunciation = languagemanager.raw_dictionary[text]
				first = True
				position = -1
#				print word.text
				for phoneme in word.phonemes:
#					print phoneme.text
					if first == True:
						first = False
					else:
						outFile.write("%d %d %s\n" % (lastPhoneme.frame, phoneme.frame-1, languagemanager.export_conversion[lastPhoneme_text]))
					if phoneme.text.lower() == "sil":
						position += 1
						outFile.write("%d %d sil\n" % (phoneme.frame, phoneme.frame))
						continue
					position += 1
					lastPhoneme_text = pronunciation[position]
					lastPhoneme = phoneme
				outFile.write("%d %d %s\n" % (lastPhoneme.frame, word.endFrame, languagemanager.export_conversion[lastPhoneme_text]))
		outFile.close()


###############################################################

class LipsyncDoc:
	def __init__(self, doc = None):
		# Copy / deepcopy fields from source doc if given:
		self.dirty = doc.dirty if doc else False
		self.name = doc.name if doc else "Untitled"
		self.path = doc.path if doc else None
		self.fps = doc.fps if doc else 24
		self.soundDuration = doc.soundDuration if doc else 72
		self.soundPath = doc.soundPath if doc else ""
		self.sound = doc.sound if doc else None
		self.voices = copy.deepcopy(doc.voices) if doc else []
		self.currentVoice = self.voices[doc.voices.index(doc.currentVoice)] if doc else None
	
	def __del__(self):
		# Properly close down the sound object
		if self.sound is not None:
			del self.sound

	def Open(self, path, frame):
		self.dirty = False
		self.path = os.path.normpath(path)
		self.name = os.path.basename(path)
		self.sound = None
		self.voices = []
		self.currentVoice = None
		inFile = codecs.open(self.path, 'r', 'utf-8', 'replace')
		inFile.readline() # discard the header
		self.soundPath = inFile.readline().strip()
		if not os.path.isabs(self.soundPath):
			self.soundPath = os.path.normpath(os.path.dirname(self.path) + '/' + self.soundPath)
		self.fps = int(inFile.readline())
		#print "self.path: %s" % self.path
		self.soundDuration = int(inFile.readline())
		#print "self.soundDuration: %d" % self.soundDuration
		numVoices = int(inFile.readline())
		for i in range(numVoices):
			voice = LipsyncVoice()
			voice.Open(inFile)
			self.voices.append(voice)
		inFile.close()
		self.OpenAudio(self.soundPath, frame)
		if len(self.voices) > 0:
			self.currentVoice = self.voices[0]

	def OpenAudio(self, path, frame):
		if self.sound is not None:
			del self.sound
			self.sound = None
		#self.soundPath = path.encode("utf-8")
		self.soundPath = path.encode('latin-1', 'replace')
		self.sound = SoundPlayer.SoundPlayer(self.soundPath, frame)
		if self.sound.IsValid():
			print "valid sound"
			self.soundDuration = int(self.sound.Duration() * self.fps)
			print "self.sound.Duration(): %d" % int(self.sound.Duration())
			print "frameRate: %d" % int(self.fps)
			print "soundDuration1: %d" % self.soundDuration
			if self.soundDuration < self.sound.Duration() * self.fps:
				self.soundDuration += 1
				print "soundDuration2: %d" % self.soundDuration
		else:
			self.sound = None

	def Save(self, path):
		self.path = os.path.normpath(path)
		self.name = os.path.basename(path)
		if os.path.dirname(self.path) == os.path.dirname(self.soundPath):
			savedSoundPath = os.path.basename(self.soundPath)
		else:
			savedSoundPath = self.soundPath
		outFile = codecs.open(self.path, 'w', 'utf-8', 'replace')
		outFile.write("lipsync version 1\n")
		outFile.write("%s\n" % savedSoundPath)
		outFile.write("%d\n" % self.fps)
		outFile.write("%d\n" % self.soundDuration)
		outFile.write("%d\n" % len(self.voices))
		for voice in self.voices:
			voice.Save(outFile)
		outFile.close()
		self.dirty = False

from phonemes import *

class PhonemeSet:
	__shared_state = {}

	def __init__(self):
		self.__dict__ = self.__shared_state
		self.set = []
		self.conversion = {}
		self.alternatives = phoneme_sets
		self.Load(self.alternatives[0])

	def Load(self, name=''):
		if name in self.alternatives:
			exec("import phonemes_%s as phonemeset" % name)
			self.set = phonemeset.phoneme_set
			self.conversion = phonemeset.phoneme_conversion
		else:
			print "Can't find phonemeset! (%s)" % name
			return
			

class LanguageManager:
	__shared_state = {}

	def __init__(self):
		self.__dict__ = self.__shared_state
		self.language_table = {}
		self.phoneme_dictionary = {}
		self.raw_dictionary = {}
		self.current_language = ""
		
		self.export_conversion = {}
		self.InitLanguages()
		
	def LoadDictionary(self,path):
		try:
			inFile = open(path, 'r')
		except:
			print "Unable to open phoneme dictionary!:", path
			return
		# process dictionary entries
		for line in inFile.readlines():
			if line[0] == '#':
				continue # skip comments in the dictionary
			# strip out leading/trailing whitespace
			line.strip()
			line = line.rstrip('\r\n')
			
			# split into components
			entry = line.split()
			if len(entry) == 0:
				continue
			# check if this is a duplicate word (alternate transcriptions end with a number in parentheses) - if so, throw it out
			if entry[0].endswith(')'):
				continue
			# add this entry to the in-memory dictionary
			for i in range(len(entry)):
				if i == 0:
					self.raw_dictionary[entry[0]] = []
				else:
					rawentry = entry[i]
					self.raw_dictionary[entry[0]].append(rawentry)
		inFile.close()
		inFile = None

	def LoadLanguage(self,language_config, force=False):
		if self.current_language == language_config["label"] and not force:
			return
		self.current_language = language_config["label"]
			
		for dictionary in language_config["dictionaries"]:
			self.LoadDictionary(os.path.join(get_main_dir(),language_config["location"],language_config["dictionaries"][dictionary]))
		
	def LanguageDetails(self, dirname, names):
		if "language.ini" in names:			
			config = ConfigParser.ConfigParser()
			config.read(os.path.join(dirname,"language.ini"))
			label = config.get("configuration","label")
			ltype = config.get("configuration","type")
			details = {}
			details["label"] = label
			details["type"] = ltype
			details["location"] = dirname		
			if ltype == "breakdown":
				details["breakdown_class"] = config.get("configuration","breakdown_class")
				self.language_table[label] = details
			elif ltype == "dictionary":
				try:
					details["case"] = config.get("configuration","case")
				except:
					details["case"] = "upper"
				details["dictionaries"] = {}

				if config.has_section('dictionaries'):
					for key, value in config.items('dictionaries'):
						details["dictionaries"][key] = value
				self.language_table[label] = details
			else:
				print "unknown type ignored language not added to table"

	def InitLanguages(self):
		if len(self.language_table) > 0:
			return
		for path, dirs, files in os.walk(os.path.join(get_main_dir(), "rsrc/languages")):			
			if "language.ini" in files:
				self.LanguageDetails(path, files)
	
