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
	if offset > 0:
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
# find the initial caret position - this changes between files for some reason - search for the "Cards" string
for i in range(3):
	if r('L', 100 + i*4) == 0x64726143:
		caret = 132 + i*4
		break
 
boundary, card_count = r('LL', caret)
deck_details_pointer = r('L', 92)
next_card = r('L', caret +16)
 
log('found ' + str(card_count) + ' cards')
 
while deck_details_pointer != 0:
	detail_label = ''.join(r('ssssssssssssssssssssssss', deck_details_pointer + 4)).strip('\0x0')
	detail_string = ''
	detail_data = r('L', deck_details_pointer + 40)
 
	if detail_label == 'CreationDate':
		# not a pointer, this is a timestamp
		creation_date = datetime.fromtimestamp(detail_data)
		detail_string = creation_date.strftime('%Y %B %d')
	elif detail_label == 'GUID':
		detail_string = str(detail_data)
	elif detail_label == 'Ordered':
		detail_string = str(detail_data)
	else:
		detail_string = string(detail_data)
	log('  ' + detail_label + ': ' + detail_string)
	deck_details_pointer = r('L', deck_details_pointer)
 
while (next_card != 0):
	address = next_card
	next_card, card_num, boundary, card_data, card_attributes = r('LLLLL', next_card)
	log('card ' + str(card_num) + ' @' + str(address) + ' data: ' + str(card_data) + ' attributes: ' + str(card_attributes))
 
	attributes = [
		['native_title', 4],
		['native_subtitle', 8],
		['foreign_title', 16],
		['foreign_subtitle', 32],
		['native_alt_answer', 64],
		['foreign_alt_answer', 128],
		['foreign_translit', 256],
		['native_tooltip', 512],
		['foreign_audio', 1024],
		['native_audio', 2048],
		['image', 4096]
	]
 
	data_pointer = card_data + 8
	for attr in attributes:
		if card_attributes & attr[1]:
			#log('card has ' + str(attr[0]) + ' @ ' + str(data_pointer))
			data_address = r('L', data_pointer)
			if attr[0] == 'foreign_audio':
				binfile(data_address, 'card'+str(card_num)+'_foreign.ogg')
			elif attr[0] == 'native_audio':
				binfile(data_address, 'card'+str(card_num)+'_native.ogg')
			elif attr[0] == 'image':
				binfile(data_address, 'card'+str(card_num)+'.jpg')
			else:
				value = string(data_address)
				if value != '':
					log(attr[0] + ': ' + string(data_address))
 
			data_pointer = data_pointer + 4