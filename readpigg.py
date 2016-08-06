#!/usr/bin/python
import sys, os, errno, struct, datetime, zlib, optparse

def is_match(name, args):
  if len(args) == 0:
    return True
  # FIXME: handle wildcards?
  return name in args

class DirEntry(object):
  def __init__(self, dirent):
    self.name = None
    self.slot = None
    self.strnum = dirent[1]
    self.fsize = dirent[2]
    self.tstamp = datetime.datetime.fromtimestamp(dirent[3])
    self.offset = dirent[4]
    self.slotnum = dirent[6]
    self.md5 = dirent[7]
    self.csize = dirent[8]

class PiggFile(object):
  def __init__(self, fname):
    self.fname = fname
    self.files = []
    self.strings = []
    self.slots = []

    self.f = open(fname, "rb")

    hdr = self.read_struct("<LHHHHL", 16)
    if hdr[0] != 0x123:
      print "Not a PIGG file!"
      return
    ents = hdr[5]

    # read directory entries
    for n in range(0, ents):
      ent = self.read_struct("<LLLLLLL16sL", 48)
      self.files.append(DirEntry(ent))

    # read string table
    strhdr = self.read_struct("<LLL", 12)
    if strhdr[0] != 0x6789:
      print "Invalid string table!"
      return

    pos = self.f.tell()

    for n in range(0, strhdr[1]):
      s = self.read_string()
      self.strings.append(s)

    # read slot table
    pos += strhdr[2]
    self.f.seek(pos)
    slothdr = self.read_struct("<LLL", 12)
    if slothdr[0] != 0x9abc:
      print "Invalid slot table!"
      return
    for n in range(0, slothdr[1]):
      s = self.read_vardata()
      ds = self.decompress_slot(s)
      self.slots.append(s)

    # fixup file list
    for ent in self.files:
      if ent.strnum < len(self.strings):
        ent.name = self.strings[ent.strnum]
      if ent.slotnum < len(self.slots):
        ent.slot = self.slots[ent.slotnum]

  def list_files(self, args, options):
    print " Length     Size    Meta      Date   Time               MD5                  Name"
    print "--------  -------  -----  ---------- ----- --------------------------------  ----"
    for ent in self.files:
      if not is_match(ent.name, args):
        continue
      name = ent.name
      fsize = ent.fsize
      csize = ent.csize
      if csize == 0:
        csize = fsize
      if ent.slot is not None:
        msize = len(ent.slot)
      else:
        msize = 0
      dt = ent.tstamp.strftime("%Y-%m-%d %H:%M")
      md5 = "".join(["%02x" % ord(x) for x in ent.md5])
      print "%8u %8u %6u  %s %s  %s" % (fsize, csize, msize, dt, md5, name)

  def extract_files(self, args, options):
    for ent in self.files:
      if not is_match(ent.name, args):
        continue
      name = ent.name
      if not options.quiet and not options.pipe:
        print "Extracting %s..." % name
      self.f.seek(ent.offset)
      if ent.csize == 0:
        data = self.f.read(ent.fsize)
      else:
        cdata = self.f.read(ent.csize)
        data = zlib.decompress(cdata)
      if options.pipe:
        sys.stdout.write(data)
        sys.stdout.flush()
      else:
        try:
          os.makedirs(os.path.dirname(name))
        except OSError, e:
          if e.errno != errno.EEXIST:
            raise
        df = open(name, "wb")
        df.write(data)
        df.close()

  def extract_meta(self, args, options):
    for ent in self.files:
      if ent.slot is None:
        continue
      if not is_match(ent.name, args):
        continue
      name = ent.name + ".meta"
      if not options.quiet and not options.pipe:
        print "Extracting %s..." % name
      data = ent.slot
      if options.pipe:
        sys.stdout.write(data)
        sys.stdout.flush()
      else:
        try:
          os.makedirs(os.path.dirname(name))
        except OSError, e:
          if e.errno != errno.EEXIST:
            raise
        df = open(name, "wb")
        df.write(data)
        df.close()

  def decompress_slot(self, data):
    fsize = struct.unpack("<L", data[:4])[0]
    if fsize == len(data):
      return data[4:]
    (fsize, csize) = struct.unpack("<LL", data[:8])
    if fsize + 4 != len(data):
      print "Slot size mismatch:", fsize, csize, len(data)
    if csize == 0:
      return data[8:]
    else:
      return zlib.decompress(data[8:])

  def read_struct(self, format, size):
    if size is None:
      size = struct.calcsize(format)
    data = self.f.read(size)
    return struct.unpack(format, data)

  def read_vardata(self):
    slen = self.read_struct("<L", 4)[0]
    data = self.f.read(slen)
    return data

  def read_string(self):
    # strip final null byte
    return self.read_vardata()[:-1]

def main():
  usage = "usage: %prog [options] file.pigg [filenames]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option("-l", "--list",
                    action="store_true", dest="list_files",
                    help="list contents of PIGG")
  parser.add_option("-m", "--meta",
                    action="store_true", dest="meta",
                    help="extract metadata")
  parser.add_option("-p", "--pipe",
                    action="store_true", dest="pipe",
                    help="extract to standard output")
  parser.add_option("-q", "--quiet",
                    action="store_true", dest="quiet",
                    help="quiet mode")

  (options, args) = parser.parse_args()

  if len(args) < 1:
    parser.error("need a filename")

  f = PiggFile(args[0])
  if options.list_files:
    f.list_files(args[1:], options)
  elif options.meta:
    f.extract_meta(args[1:], options)
  else:
    f.extract_files(args[1:], options)

if __name__ == "__main__":
  main()
