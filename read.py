import struct
import sys
 
f = open('verbos.b4u', 'rb')
contents = f.read()
f.close()
print struct.unpack_from('<L', contents, 148)