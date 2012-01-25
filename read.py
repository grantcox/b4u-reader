import codecs
from datetime import datetime
import os
import struct
import sys
 
if len(sys.argv) < 2:
	print 'Usage: readb4u.py [filename]'
	sys.exit()
 
f = open(sys.argv[1], 'rb')
contents = f.read()
f.close()
 
def r(fmt, offset):
	read = struct.unpack_from('<' + fmt, contents, offset)
	if len(read) == 1:
		return read[0]
	return read
 
def string(offset):
	s = u''
	length = r('H', offset)
	for i in range(length):
		raw = r('H', offset + i*2 +2)
		char = raw ^ 0x7E
		s = s + unichr(char)
	return s
 
def binfile(offset, filename):
	length = r('L', offset)
	filedata = contents[offset+8 : offset+length+8]
 
	f = open(os.path.join(filename), 'wb')
	f.write(filedata)
	f.close()
 
logfile = codecs.open('log.txt', encoding='utf-8', mode='a')
def log(s):
	s = unicode(s)
	print s.encode('ascii', 'ignore')
	logfile.write('\n' + s)
log('---- ' + str(datetime.now()) + ' -----------------')
 
 
# read the file
caret = 144
boundary, card_count = r('LL', caret)
next_card = r('L', caret +16)
 
log('found ' + str(card_count) + ' cards')
 
while (next_card != 0):
	address = next_card
	next_card, card_num, boundary, card_data, b = r('LLLLL', next_card)
	log('card ' + str(card_num) + ' @' + str(address) + ' data: ' + str(card_data) + ' b: ' + str(b))
 
	card_head, number, english_title, english_subtitle, foreign_title, foreign_subtitle = r('LLLLLL', card_data)
	unknown, unknown, unknown, unknown, audio, image = r('LLLLLL', card_data + 24)
 
	english_title = string(english_title)
	english_subtitle = string(english_subtitle)
	foreign_title = string(foreign_title)
	foreign_subtitle = string(foreign_subtitle)
	binfile(audio, 'card'+str(card_num)+'.ogg')
	binfile(image, 'card'+str(card_num)+'.jpg')
	log('  ' + foreign_title + ' : ' + foreign_subtitle + ' => ' + english_title + ' : ' + english_subtitle)