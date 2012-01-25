import codecs
from datetime import datetime
import struct
import sys
 
f = open('verbos.b4u', 'rb')
contents = f.read()
f.close()
 
# helper function to simplify reading syntax
def r(fmt, offset):
	read = struct.unpack_from('<' + fmt, contents, offset)
	if len(read) == 1:
		return read[0]
	return read
 
# the Windows console fails on non-ascii characters, so we also log to a file
logfile = codecs.open('log.txt', encoding='utf-8', mode='a')
def log(s):
	s = unicode(s)
	print s.encode('ascii', 'ignore') # only send ascii to the console
	logfile.write('\n' + s) # but write the full content to file
log('---- ' + str(datetime.now()) + ' -----------------')
 
 
# read the .b4u deck
caret = 144
boundary, card_count = r('LL', caret)
next_card = r('L', caret +16)
 
log('found ' + str(card_count) + ' cards')
 
while (next_card != 0):
	address = next_card
	next_card, card_num, boundary, a, b = r('LLLLL', next_card)
	log('card ' + str(card_num) + ' @' + str(address) + ' a: ' + str(a) + ' b: ' + str(b))