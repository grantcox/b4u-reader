import codecs
from datetime import datetime
import os
import struct
import sys

#logfile = codecs.open('log.txt', encoding='utf-8', mode='a')
#def log(s):
#	s = unicode(s)
#	print s.encode('ascii', 'ignore')
#	logfile.write('\n' + s)
#log('---- ' + str(datetime.now()) + ' -----------------')

class Parser(object):
	struct_short = struct.Struct('<H')

	def __init__(self, filename):
		self.filedata = None
		if filename != '':
			try:
				f = open(filename, 'rb')
				self.filedata = f.read()
				f.close()
			
			except IOError as e:
				pass
		
	def read(self, fmt, offset):
		if self.filedata is None:
			return None
		read = struct.unpack_from('<' + fmt, self.filedata, offset)
		if len(read) == 1:
			return read[0]
		return read
	
	def string(self, offset):
		if self.filedata is None:
			return None
		s = u''
		if offset > 0:
			length = self.read('H', offset)
			for i in range(length):
				raw = self.read('H', offset + i*2 +2)
				char = raw ^ 0x7E
				s = s + unichr(char)
		return s

	def plain_fixed_string(self, offset):
		if self.filedata is None:
			return None
		plain_bytes = struct.unpack_from('<ssssssssssssssssssssssss', self.filedata, offset)
		plain_string = ''.join(plain_bytes).strip('\0x0')
		return plain_string

	def blob(self, offset, filename=''):
		length = self.read('L', offset)
		data = self.filedata[offset+8 : offset+length+8]
		
		return Blob(data, filename)

class Blob(object):
	def __init__(self, data, filename=''):
		self.data = data
		self.filename = filename

	def write(self, filename=None):
		if filename is None:
			filename = self.filename
		if filename is not None and filename != '':
			f = open(filename, 'wb')
			f.write(self.data)
			f.close()
		
class Card(object):
	number = None
	native_title = ''
	native_subtitle = ''
	foreign_title = ''
	foreign_subtitle = ''
	native_alt_answer = ''
	foreign_alt_answer = ''
	foreign_translit = ''
	native_tooltip = ''
	foreign_audio = None
	native_audio = None
	image = None

	def __init__(self, parser, data_pointer=0, card_attributes=0):
		self.data = {}
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
		
		self.number = parser.read('L', data_pointer +4)
		data_pointer = data_pointer + 8
		for attr in attributes:
			if card_attributes & attr[1]:
				data_address = parser.read('L', data_pointer)
				data = None
				
				if attr[0] == 'foreign_audio':
					data = parser.blob(data_address)
				elif attr[0] == 'native_audio':
					data = parser.blob(data_address)
				elif attr[0] == 'image':
					data = parser.blob(data_address)
				else:
					data = parser.string(data_address)
				
				setattr(self, attr[0], data)
				
				data_pointer = data_pointer + 4

		self.valid = True

	def html(self, tofolder):
		def wrap(content, prefix, suffix):
			if content == None or content == '':
				return ''
			return unicode(prefix) + unicode(content) + unicode(suffix)

		src = ''
		cardnum = str(self.number)
		write = {
			'number' : cardnum,
			'native_title' : self.native_title,
			'native_subtitle' : wrap(self.native_subtitle, '<p>', '</p>\n'),
			'foreign_title' : self.foreign_title,
			'foreign_subtitle' : wrap(self.foreign_subtitle, '<p>', '</p>\n'),
			'foreign_translit' : '',
			'native_alt_answer' : wrap(self.native_alt_answer, '<p>Also: ', '</p>\n'),
			'foreign_alt_answer' : wrap(self.foreign_alt_answer, '<p>Also: ', '</p>\n'),
			'native_tooltip' : wrap(self.native_tooltip, '<p class="tooltip">', '</p>\n'),
			'foreign_audio' : '',
			'native_audio' : '',
			'image' : ''
		}
		
		if isinstance(self.foreign_audio, Blob):
			fn = 'card' + cardnum + '_foreign.ogg'
			self.foreign_audio.write(os.path.join(tofolder, fn))
			write['foreign_audio'] = '<a class="audio" href="' + fn + '">(o)</a>'
			
		if isinstance(self.native_audio, Blob):
			fn = 'card' + cardnum + '_native.ogg'
			self.native_audio.write(os.path.join(tofolder, fn))
			write['native_audio'] = '<a class="audio" href="' + fn + '">(o)</a>'
			
		if isinstance(self.image, Blob):
			fn = 'card' + cardnum + '_image.jpg'
			self.image.write(os.path.join(tofolder, fn))
			write['image'] = '<img class="image" src="' + fn + '"/>'
		
		src	= '\
	<div class="card">\n\
		<p class="num">#%(number)s</p>\n\
		%(image)s\
		<h1>%(foreign_title)s%(foreign_audio)s</h1>\n\
		%(foreign_subtitle)s\
		%(foreign_alt_answer)s\
		%(native_tooltip)s\
		\
		<h2>%(native_title)s%(native_audio)s</h2>\n\
		%(native_subtitle)s\n\
		%(native_alt_answer)s\n\
	</div>\n\
				\n' %write
		
		return src
		
class Deck(object):
	title = ''
	description = ''
	native_language = ''
	foreign_language = ''
	copyright = ''
	copyright_url = ''
	creation_date = ''
	app_creator_name = ''
	
	def __init__(self, filename):
		self.valid = False
		self.cards = []
		self.parser = Parser(filename)
		self.parse()

	def parse(self):
		self.valid = False
		self.data = {}
		self.cards = []
		
		caret = None
		# find the initial caret position - this changes between files for some reason - search for the "Cards" string
		for i in range(3):
			addr = 104 + i*4
			if ''.join(self.parser.read('sssss', addr)) == 'Cards':
				caret = addr + 32
				break
		
		if caret is None:
			return
		
		deck_details_pointer = self.parser.read('L', 92)
		card_count = self.parser.read('L', caret +4)
		next_card = self.parser.read('L', caret +16)
		
		# read in all of the deck properties - name, creator, description, copyright etc
		fields = {
			'Name': 'title',
			'Side1Lang': 'native_language',
			'Side2Lang': 'foreign_language',
			'Description': 'description',
			'Copyright': 'copyright',
			'CopyrightURL': 'copyright_url',
			'CreationDate': 'creation_date',
			'AppCreatorName': 'app_creator_name'
		}
		
		while deck_details_pointer != 0:
			detail_label = self.parser.plain_fixed_string(deck_details_pointer + 4)
			if detail_label in fields:
				detail_string = ''
				detail_data = self.parser.read('L', deck_details_pointer + 40)
			 
				if detail_label == 'CreationDate':
					# not a pointer, this is a timestamp
					creation_date = datetime.fromtimestamp(detail_data)
					detail_string = creation_date.strftime('%Y %B %d')
				elif detail_label == 'GUID':
					detail_string = str(detail_data)
				elif detail_label == 'Ordered':
					detail_string = str(detail_data)
				else:
					detail_string = self.parser.string(detail_data)
				
				# set this property on the Deck object
				setattr(self, fields[detail_label], detail_string)
				
			# move to the next attribute
			deck_details_pointer = self.parser.read('L', deck_details_pointer)
		
		self.valid = True
		
		# read in all of the cards
		while (next_card != 0):
			next_card, card_num, boundary, card_data_pointer, card_attributes = self.parser.read('LLLLL', next_card)
			card = Card(self.parser, card_data_pointer, card_attributes)
			if card.valid:
				self.cards.append(card)
		
		return self.valid

	def html(self, tofolder):
		if not os.path.isdir(tofolder):
			os.makedirs(tofolder)
		html = '\
<!DOCTYPE html><html lang="en">\
<head><meta charset="utf-8" />\n\
	<title>Deck</title>\n\
	<style type="text/css">\n\
	.card{border:2px solid #999; margin: 30px; padding: 20px; text-align: center;}\
	</style>\n\
</head><body>\n\
	<h1>'+unicode(self.title)+'</h1>\
	<h2>'+unicode(self.native_language)+':'+unicode(self.foreign_language)+'</h2>\
	<p>Description: '+unicode(self.description)+'</p>\
	<p>Copyright: '+unicode(self.copyright)+' '+unicode(self.copyright_url)+'</p>\
	<p>Created with: '+unicode(self.app_creator_name)+' on '+unicode(self.creation_date)+'</p>\
		\n'

		for card in self.cards:
			html = html + card.html(tofolder)
			
		html = html + '</body></html>'
		
		fn = os.path.join(tofolder, 'cards.html')
		f = codecs.open(fn, encoding='utf-8', mode='w')
		f.write(html)
		f.close()

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print 'Usage: readb4u.py [filename]'
		sys.exit()

	SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
	OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')
	
	d = Deck(sys.argv[1])
	d.html(OUTPUT_DIR)

 
