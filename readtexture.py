#!/usr/bin/python
import sys, os, errno, struct, optparse

class Texture(object):
  def __init__(self, fname):
    self.fname = fname
    self.ddsname = None

    self.f = open(fname, "rb")

    hdrdata = self.f.read(32)
    hdr = struct.unpack("<LLLLLLL4s", hdrdata)
    self.offset = hdr[0]
    self.width = hdr[2]
    self.height = hdr[3]

    slen = self.offset - 32
    data = self.f.read(slen)
    self.meta = hdrdata + data

    idx = data.index("\0")
    if idx != -1:
      self.ddsname = data[:idx]
      self.extra = data[idx+1:]

  def list_files(self, options):
    print "Header: %u bytes" % len(self.meta)
    print " Dimensions: %ux%u" % (self.width, self.height)
    print " Extra data: %u bytes" % len(self.extra)
    print "File: %s" % self.ddsname

  def extract_file(self, options):
    name = self.ddsname
    if not options.quiet and not options.pipe:
      print "Extracting %s..." % name
    self.f.seek(self.offset)
    data = self.f.read()
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

  def extract_meta(self, options):
    name = self.fname + ".meta"
    if not options.quiet and not options.pipe:
      print "Extracting %s..." % name
    if options.pipe:
      sys.stdout.write(self.meta)
      sys.stdout.flush()
    else:
      df = open(name, "wb")
      df.write(self.meta)
      df.close()

def main():
  usage = "usage: %prog [options] file.texture"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option("-l", "--list",
                    action="store_true", dest="list_files",
                    help="list contents of file")
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

  f = Texture(args[0])
  if options.list_files:
    f.list_files(options)
  elif options.meta:
    f.extract_meta(options)
  else:
    f.extract_file(options)

if __name__ == "__main__":
  main()
