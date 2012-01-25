import codecs
from datetime import datetime
import struct
import sys
 
f = open('verbos.b4u', 'rb')
contents = f.read()
f.close()
 
def r(fmt, offset):
	read = struct.unpack_from('<' + fmt, contents, offset)
	if len(read) == 1:
		return read[0]
	return read
 
def s(offset):
	s = u''
	length = r('H', offset)
	for i in range(length):
		raw = r('H', offset + i*2 +2)
		char = raw ^ 0x7E
		s = s + unichr(char)
	return s
 
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
	english_title = s(english_title)
	english_subtitle = s(english_subtitle)
	foreign_title = s(foreign_title)
	foreign_subtitle = s(foreign_subtitle)
	log('  ' + foreign_title + ' : ' + foreign_subtitle + ' => ' + english_title + ' : ' + english_subtitle)