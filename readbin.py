#!/usr/bin/python
import sys, os, errno, struct, datetime, zlib, optparse

indent = "  "
danger_limit = 32768

def is_match(name, args):
  if args is None or len(args) == 0:
    return True
  # FIXME: handle wildcards?
  return name in args

class Decoder(object):
  def list_names(self, f, sz, args=None):
    pass
  def decode(self, f, sz, pfx, args=None, options=None):
    pass

class String(Decoder):
  def __init__(self, name="unknown"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    s = f.read_string()
    print pfx + "%s \"%s\"" % (self.name, s)

class Name(String):
  def __init__(self):
    String.__init__(self, "Name")
  def list_names(self, f, sz, args=None):
    name = f.read_string()
    if is_match(name, args):
      print "%6u  %s" % (sz, name)
  def decode(self, f, sz, pfx, args=None, options=None):
    name = f.read_string()
    if is_match(name, args):
      print pfx + "%s \"%s\"" % (self.name, name)
      return name

class Bool(Decoder):
  def __init__(self, name="unknown_bool"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    num = f.read_struct("<l", 4)[0]
    if num == 0: return
    if num == 1:
      print pfx + self.name
    else:
      print pfx + "%s(%d)" % (self.name, num)

class Flag(Decoder):
  def __init__(self, name="unknown"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    num = f.read_struct("<L", 4)[0]
    print pfx + "%s 0x%x" % (self.name, num)

class Integer(Decoder):
  def __init__(self, name="unknown"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    num = f.read_struct("<l", 4)[0]
    print pfx + "%s %d" % (self.name, num)

class Float(Decoder):
  def __init__(self, name="unknown"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    num = f.read_struct("<f", 4)[0]
    print pfx + "%s %f" % (self.name, num)

class StringList(Decoder):
  def __init__(self, name="unknown_list"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    count = f.read_struct("<L", 4)[0]
    if count == 0: return
    if count > danger_limit:
      print "dangerously large list:", count
      count = danger_limit
    data = []
    for n in range(0, count):
      data.append(f.read_string())
    s = ", ".join(["\"%s\"" % x for x in data])
    print pfx + "%s %s" % (self.name, s)

class IntegerList(Decoder):
  def __init__(self, name="unknown_list"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    count = f.read_struct("<L", 4)[0]
    if count == 0: return
    if count > danger_limit:
      print "dangerously large list:", count
      count = danger_limit
    data = []
    for n in range(0, count):
      data.append(f.read_struct("<l", 4)[0])
    s = ", ".join(["%d" % x for x in data])
    print pfx + "%s %s" % (self.name, s)

class FloatList(Decoder):
  def __init__(self, name="unknown_list"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    count = f.read_struct("<L", 4)[0]
    if count == 0: return
    if count > danger_limit:
      print "dangerously large list:", count
      count = danger_limit
    data = []
    for n in range(0, count):
      data.append(f.read_struct("<f", 4)[0])
    s = ", ".join(["%f" % x for x in data])
    print pfx + "%s %s" % (self.name, s)

class OptColor(IntegerList):
  def __init__(self, name="Color"):
    IntegerList.__init__(self, name)

class IntegerPair(Decoder):
  def __init__(self, name="unknown_pair"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    d = f.read_struct("<ll", 8)
    print pfx + "%s %d %d" % (self.name, d[0], d[1])

class OptIntegerPair(Decoder):
  def __init__(self, name="unknown_pair"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    s = f.read_struct("<L", 4)[0]
    if s == 0: return
    if s != 8:
      return "Invalid pair field"
    d = f.read_struct("<ll", 8)
    print pfx + "%s %d %d" % (self.name, d[0], d[1])

class IntegerTriplet(Decoder):
  def __init__(self, name="unknown_triplet"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    d = f.read_struct("<lll", 12)
    print pfx + "%s %d %d %d" % (self.name, d[0], d[1], d[2])

class FloatPair(Decoder):
  def __init__(self, name="unknown_pair"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    d = f.read_struct("<ff", 8)
    print pfx + "%s %f, %f" % (self.name, d[0], d[1])

class FloatTriplet(Decoder):
  def __init__(self, name="unknown_triplet"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    d = f.read_struct("<fff", 12)
    print pfx + "%s %f, %f, %f" % (self.name, d[0], d[1], d[2])

class OptFloatPair(Decoder):
  def __init__(self, name="unknown_pair"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    s = f.read_struct("<L", 4)[0]
    if s == 0: return
    if s != 8:
      return "Invalid pair field"
    d = f.read_struct("<ff", 8)
    print pfx + "%s %f %f" % (self.name, d[0], d[1])

class OptFloatTriplet(Decoder):
  def __init__(self, name="unknown_triplet"):
    self.name = name
  def decode(self, f, sz, pfx, args=None, options=None):
    s = f.read_struct("<L", 4)[0]
    if s == 0: return
    if s != 12:
      return "Invalid triplet field"
    d = f.read_struct("<fff", 12)
    print pfx + "%s %f %f %f" % (self.name, d[0], d[1], d[2])

class Enum(Decoder):
  def __init__(self, name, elements):
    self.name = name
    self.elements = elements
  def decode(self, f, sz, pfx, args=None, options=None):
    num = f.read_struct("<L", 4)[0]
    if num < len(self.elements):
      s = self.elements[num]
    else:
      s = None
    if s is not None:
      print pfx + "%s %s" % (self.name, s)
    else:
      print pfx + "%s Unknown(%u)" % (self.name, num)

class Struct(Decoder):
  def __init__(self, name, elements):
    self.name = name
    self.elements = elements
  def decode(self, f, sz, pfx, args=None, options=None):
    end = f.tell() + sz
    npfx = pfx + indent
    print pfx + self.name
    for e in self.elements:
      pos = f.tell()
      e.decode(f, end - pos, npfx)
    pos = f.tell()
    if pos < end:
      DefaultDecoder().decode(f, end - pos, npfx)
    elif pos > end:
      print "Decode overrun, %u bytes" % (pos - end)
    print pfx + "End" + self.name
    f.seek(end)

class OptStruct(Decoder):
  def __init__(self, name, elements):
    self.name = name
    self.elements = elements
  def decode(self, f, sz, pfx, args=None, options=None):
    size = f.read_struct("<L", 4)[0]
    if size == 0: return
    end = f.tell() + size
    npfx = pfx + indent
    print pfx + self.name
    for e in self.elements:
      pos = f.tell()
      e.decode(f, end - pos, npfx, args)
    pos = f.tell()
    if pos < end:
      DefaultDecoder().decode(f, end - pos, npfx)
    elif pos > end:
      print "Decode overrun, %u bytes" % (pos - end)
    print pfx + "End" + self.name
    f.seek(end)

class Array(Decoder):
  def __init__(self, elements):
    self.elements = elements
  def decode(self, f, sz, pfx, args=None, options=None):
    pos = f.tell()
    end = pos + sz
    count = f.read_struct("<L", 4)[0]
    if count > danger_limit:
      print "dangerously large number:", count
      count = danger_limit
    for n in range(0, count):
      pos = f.tell()
      self.elements.decode(f, end - pos, pfx)

class List(Decoder):
  def __init__(self, name, elements):
    self.name = name
    self.elements = elements
  def list_names(self, f, sz, args=None):
    count = f.read_struct("<L", 4)[0]
    if count > danger_limit:
      print "dangerously large number:", count
      count = danger_limit
    for n in range(0, count):
      size = f.read_struct("<L", 4)[0]
      end = f.tell() + size
      if len(self.elements) > 0 and \
         type(self.elements[0]) is Name:
        name = f.read_string()
        if not is_match(name, args):
          f.seek(end)
          continue
        print "%6u  %s" % (sz, name)
      f.seek(end)
  def decode(self, f, sz, pfx, args=None, options=None):
    npfx = pfx + "  "
    count = f.read_struct("<L", 4)[0]
    if count > danger_limit:
      print "dangerously large number:", count
      count = danger_limit
    for n in range(0, count):
      size = f.read_struct("<L", 4)[0]
      pos = f.tell()
      end = pos + size

      if args is not None and \
         len(self.elements) > 0 and \
         type(self.elements[0]) is Name:
        name = f.read_string()
        if not is_match(name, args):
          f.seek(end)
          continue
        print pfx + self.name
        print npfx + "%s \"%s\"" % (self.elements[0].name, name)
        for e in self.elements[1:]:
          pos = f.tell()
          e.decode(f, end - pos, npfx)
      else:
        print pfx + self.name
        for e in self.elements:
          pos = f.tell()
          e.decode(f, end - pos, npfx)
      pos = f.tell()
      if pos < end:
        DefaultDecoder().decode(f, end - pos, npfx)
      elif pos > end:
        print "Decode overrun, %u bytes" % (pos - end)
      print pfx + "End" + self.name
      f.seek(end)

class DefaultDecoder(Decoder):
  def __init__(self):
    pass
  def decode(self, f, sz, pfx, args=None, options=None):
    if sz <= 0: return
    tsz = sz
    if tsz > 128: tsz = 128
    print pfx + "<unknown>",
    start = f.tell()
    pos = 0
    end = start + sz
    while pos < tsz:
      data = f.read(4)

      # try to autodetect strings
      if ord(data[0]) > 1 and ord(data[1]) == 0 and \
         ord(data[2]) >= 32 and ord(data[2]) <= 126 and \
         ord(data[3]) >= 32 and ord(data[3]) <= 126 and \
         ord(data[0]) + pos <= sz:
        f.seek(-4, 1)
        s = f.read_string()
        print "\"%s\"" % s,
      # special case for single-character string
      elif ord(data[0]) == 1 and ord(data[1]) == 0 and \
         ord(data[2]) >= 32 and ord(data[2]) <= 126 and \
         ord(data[3]) == 0 and \
         ord(data[0]) + pos <= sz:
        f.seek(-4, 1)
        s = f.read_string()
        print "\"%s\"" % s,
      # try to autodetect floats
      elif ord(data[3]) >= 0x35 and ord(data[3]) < 0xff:
        s = struct.unpack("<f", data)[0]
        print s,
      # otherwise, assume integer
      else:
        s = struct.unpack("<L", data)[0]
        if s == 0:
          print "0",
        else:
          print "0x%x" % s,
      pos = f.tell() - start
    print
    if pos < sz:
      print pfx + "<bytes: %u 0x%x>" % (sz, sz)
    f.seek(end)

font = OptStruct("Font", [
         Name(),
         Integer("Size"),
         Bool("Italic"),
         Bool("Bold"),
         Integer("Outline"),
         OptIntegerPair("DropShadow")
       ])

blend_modes = ["Overlay", "Multiply", None, "Subtract"]

layer_elements = [Name(),
                  Enum("Type", [None, None, "Text", "Image"]),
                  Enum("Stretch", ["None", "Full", "Tile"]),
                  String("Text"),
                  String("Image"),
                  OptColor("Color"),
                  OptColor("Color0"), OptColor("Color1"),
                  OptColor("Color2"), OptColor("Color3"),
                  FloatPair("Pos"),
                  FloatPair("Size"),
                  Float("Rot"),
                  Bool("Hidden"),
                  font,
                  List("Filter", [
                   Enum("Type", [None, None, "DropShadow"]),
                   Integer("Magnitude"),
                   Float("Percent"),
                   Float("Spread"),
                   OptColor("Color"),
                   OptIntegerPair("Offset"),
                   Enum("Blend", blend_modes),
                  ]),
                  List("SubLayer", None), # filled in below
                  Enum("SubBlend", blend_modes),
                  Float("SubBlendWeight")
                 ]
# fill in SubLayer here, since it's recursive
layer_elements[16].elements = layer_elements

decoders = {
  0x0c027625: List("DefName", [ # defnames.bin
               Name(),
              ]),
  0x090e82f6: List("ReplacePowerName", [ # replacepowernames.bin
               Name(),
               String(),
              ]),
  0x10184422: List("RoomCategory", [ # roomcategories.bin
               Name(),
               String(),
               String(),
               String(),
              ]),
  0x102d6c1e: Struct("BaseUpkeep", [ # baseupkeep.bin
               String(),
               Integer(),
               Integer(), Integer(), Integer(), Integer(),
               Integer(),
               List("Unknown", [
                Integer(), Integer(), Integer(),
               ]),
              ]),
  0x120e98ea: List("PCDefMapUnique", [ # PC_Def_MapUnique.bin
               String(),
               List("Unknown", [
                String(),
                String(),
               ]),
              ]),
  0x144dc947: List("Plot", [ # plots.bin
               Name(),
               String(),
               String(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               List("Unknown", [
                String(),
                Integer(),
               ]),
               Integer(),
              ]),
  0x15ea15cf: List("Badge", [ # badges.bin, supergroup_badges.bin
               String(),
               Name(),
               Integer(), Integer(), Integer(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               String(),
               Integer(), # unused
               Integer(),
               Integer(), # unused
               Integer(), # unused
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(), # unused
               Integer(),
              ]),
  0x1c11d177: List("PCDefContact", [ # PC_Def_Contacts.bin
               String(),
               List("Unknown", [
                String(),
               ]),
              ]),
  0x1e2c2c56: List("Behavior", [ # behaviors.bin
               Flag(), Flag(), Flag(), Flag(), Flag(),
               Name(),
               Float(),
               FloatTriplet(),
               FloatTriplet(),
               FloatTriplet(),
               Integer(), # unused
               Float(),
               Integer(),
               FloatTriplet(),
               FloatPair(),
               Integer(), # unused
               Float(),
               FloatPair(),
               FloatPair(),
               Integer(), # unused
               FloatTriplet(),
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), # unused
               Integer(),
               Integer(),
               FloatTriplet(),
               FloatTriplet(),
               FloatPair(),
               FloatTriplet(),
               Integer(), Integer(), Integer(), # unused
               FloatTriplet(),
               FloatTriplet(),
               Integer(), Integer(), Integer(), # unused
               FloatTriplet(),
               Integer(),
               Float(),
               FloatPair(),
               FloatPair(),
               FloatPair(),
               FloatTriplet(),
               Integer(),
               Float(),
               Integer(),
               Integer(),
               Integer(),
               Float(),
               Integer(),
               Float(),
               Float(),
               Float(),
               Integer(),
               Integer(),
               Float(),
               Float(),
               Float(),
               List("Unknown", [
                Float(), Float(),
                String(),
                Integer(), # unused
               ]),
               Integer(), Integer(), # unused
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               Integer(),
               FloatPair(),
               Integer(), Integer(), Integer(), # unused
               Float(),
               Integer(), # unused
               Float(),
               Integer(), Integer(), # unused
               Integer(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
              ]),
  0x1f5ae0b6: List("AttribName", [ # attrib_names.bin
               Name(),
               String(),
              ]),
  0x23b72742: List("EntType", [ # ent_types.bin
               Flag(),
               Name(),
               Float(),
               String(),
               String(),
               List("Unknown", [
                String(),
                String(),
               ]),
               Float(),
               String(),
               Float(),
               Float(),
               Float(),
               Float(),
               Integer(),
               Float(),
               Float(),
               Float(),
               Integer(),
               Integer(),
               Integer(),
               String(),
               Integer(),
               FloatTriplet(),
               IntegerPair(), # unused
               Float(),
               Integer(),
               Integer(),
               Integer(),
               FloatList(),
               List("Unknown2", [
                Integer(),
                Float(),
               ]),
               Integer(),
               String(),
               Integer(),
               StringList(),
               String(),
               List("Unknown3", [
                Float(),
                Float(),
                StringList(),
                StringList(),
                StringList(),
                Integer(), # unused
               ]),
               Float(),
               String(),
               String(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               StringList(),
               FloatTriplet(),
               FloatPair(),
               Integer(), # unused
               FloatPair(),
               Integer(), # unused
               Float(),
               IntegerTriplet(), # unused
               FloatPair(),
               IntegerTriplet(), # unused
               FloatTriplet(),
               Float(), Float(), Float(),
               Float(), Float(), Float(),
               Float(), Float(), Float(),
               Float(), Float(), Float(),
               Integer(),
               Float(),
               Float(),
               Integer(),
               Integer(),
               Integer(),
              ]),
  0x28525566: List("Product", [ # productcatalog.bin
               Name(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               String(),
               Integer(),
               Integer(),
              ]),
  0x2d11c077: Struct("Experience", [ # experience.bin
               OptStruct("Unknown", [
                IntegerList(),
                IntegerList(),
               ]),
              ]),
  0x2fe0d52d: List("PowerSet", [ # powersets.bin
               String(),
               Name(),
               String(),
               Integer(), # unused
               Integer(),
               String(),
               String(),
               String(),
               String(),
               StringList(),
               StringList(),
               String(),
               String(),
               String(),
               StringList(),
               String(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               StringList(),
               StringList(),
               Integer(), # unused
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               Integer(),
              ]),
  0x310ce383: List("PCDefObject", [ # PC_Def_Objects.bin
               Name(),
               String(),
               List("Unknown", [
                Name(),
                String(),
               ]),
              ]),
  0x315acdb1: List("AttribDescription", [ # attrib_descriptions.bin
               Name(),
               List("Unknown", [
                Name(),
                String(),
                String(),
               ]),
              ]),
  0x326ad4e9: List("Detail", [ # details.bin
               Name(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(), # unused
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               StringList(),
               Integer(),
               Integer(), # unused
               Integer(),
               Integer(), # unused
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(), # unused
               Integer(),
               Float(),
               Integer(), # unused
               Integer(),
               Integer(), # unused
               String(),
               Integer(),
               StringList(),
               Integer(),
               Integer(),
               StringList(),
               Integer(), # unused
               String(),
               String(),
               String(),
              ]),
  0x33e59071: List("VillainDef", [ # VillainDef.bin
               Name(),
               String(),
               Integer(),
               String(),
               String(),
               String(),
               String(),
               Integer(),
               List("Unknown1", [
                String(),
                String(),
                String(),
                Integer(), # unused
                Integer(), # unused
                Integer(),
               ]),
               List("Unknown2", [
                Integer(),
                StringList(),
                StringList(),
                Integer(), # unused
               ]),
               Integer(),
               String(),
               String(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               IntegerPair(),
               StringList(),
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Float(),
               StringList(),
               String(),
               String(),
               Float(),
               List("Unknown3", [
                StringList(),
                StringList(),
                StringList(),
                StringList(),
                StringList(),
                StringList(),
                Integer(), # unused
                Integer(), # unused
                StringList(),
                StringList(),
                StringList(),
               ]),
               Integer(),
               Integer(),
               String(),
               Integer(), # unused
               Integer(), # unused
              ]),
  0x3c2f0dae: List("TailorCost", [ # tailorcost.bin
               Integer(), Integer(), Integer(),
               Integer(), # unused
               Integer(), Integer(), Integer(),
               Integer(), Integer(), Integer(),
               Integer(), # unused
              ]),
  0x3e7f1a90: Struct("GeoBin", [ # geobin/*.bin
               Integer(),
               String(),
               Integer(),
               List("Unknown", [
                Name(),
                List("Unknown2", [
                 Name(),
                 FloatTriplet(),
                 FloatTriplet(),
                 Flag(),
                ]),
                List("Unknown3", [
                 Name(),
                 String(),
                ]),
               ]),
               List("Unknown4", [
                Name(),
                FloatTriplet(),
               ]),
              ]),
  0x4011736e: List("MenuAnimation", [ # menuAnimations.bin
               Name(),
               StringList(),
               StringList(),
               String(),
              ]),
  0x44061748: Struct("VisionPhase", [ # visionPhases*.bin
               StringList(),
              ]),
  0x46937197: Struct("SupergroupEmblems", [ # supergroupEmblems.bin
               String(),
               String(),
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               List("Unknown", [
                String(),
                Integer(), # unused
                String(),
                String(),
                String(),
                Integer(), Integer(), Integer(), # unused
                Integer(), Integer(), Integer(), # unused
                Integer(), # unused
                Integer(),
                Integer(), Integer(), Integer(), # unused
                Integer(), # unused
               ]),
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), Integer(), # unused
               Integer(), # unused
              ]),
  0x479da30a: List("TexWord", [ # texWords.bin
               Name(),
               OptIntegerPair("Size"),
               List("Layer", layer_elements),
              ]),
  0x4837cab2: List("Map", [ # map.bin
               Name(),
               String(),
               FloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               Integer(),
              ]),
  0x4908d1c3: List("PCDefEntity", [ # PC_Def_Entitites.bin
               Name(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               String(),
              ]),
  0x492a3929: List("ClothWindInfo", [ # clothWindInfo.bin
               Name(),
               FloatPair(),
               FloatPair(),
               FloatPair(),
               FloatPair(),
               IntegerPair(),
              ]),
  0x499f34b4: List("DimReturn", [ # dimreturns.bin
               Integer(),
               IntegerList(),
               List("Unknown", [
                Integer(),
                IntegerList(),
                List("Unknown2", [
                 Float(),
                 Float(),
                 Integer(), # unused
                ]),
               ]),
              ]),
  0x4a499aee: List("RoomTemplate", [ # roomtemplates.bin
               Name(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               String(),
               List("Unknown", [
                String(),
                Integer(),
               ]),
              ]),
  0x4ac5b355: List("Particle", [ # particles.bin
               Name(),
               Integer(),
               Integer(),
               Float(),
               Integer(),
               FloatList(),
               IntegerList(),
               FloatList(),
               Integer(),
               Float(),
               Float(),
               Float(),
               Integer(),
               FloatList(),
               Float(),
               Float(),
               Float(),
               Float(),
               IntegerTriplet(),
               Float(),
               Float(),
               Integer(),
               Integer(), # unused
               FloatList(),
               FloatList(),
               FloatTriplet(),
               FloatTriplet(),
               Float(),
               FloatTriplet(),
               FloatTriplet(),
               IntegerList(),
               Integer(),
               Integer(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               FloatTriplet(),
               FloatTriplet(),
               FloatTriplet(),
               Float(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               Integer(),
               Integer(), # unused
               FloatTriplet(),
               String(),
               Integer(),
               FloatList(),
               Float(),
               Integer(),
               String(),
               String(),
               FloatTriplet(),
               FloatTriplet(),
               FloatTriplet(),
               FloatTriplet(),
               FloatTriplet(),
               Float(),
               Integer(),
               Integer(), # unused
               FloatList(),
               Float(),
               Integer(),
               Integer(),
               Float(),
               Integer(),
               Integer(),
               Integer(), # unused
               Integer(), # unused
               Integer(),
              ]),
  0x4b22fb3b: List("DefaultBodyCfg", [ # defaultBodyCfg.bin
               Name(),
               String(),
               String(),
               Integer(),
               Integer(),
               Float(),
               Float(),
               Float(),
               Float(),
               Float(),
               Float(),
               Float(),
              ]),
  0x4c0d578c: Struct("ExemplarHandicap", [ # exemplarhandicaps.bin
               FloatList(),
               FloatList(),
               FloatList(),
               FloatList(),
              ]),
  0x4cb7d9cb: List("FXInfo", [ # fxinfo.bin
               Name(),
               Float(),
               Integer(),
               Integer(),
               List("Unknown", [
                String(),
               ]),
               List("Unknown2", [
                String(),
                Float(),
                Float(),
                Float(),
                Integer(), # unused
                Float(),
                Integer(),
                Integer(),
                Integer(),
                Array(StringList("Unknown3")),
                List("Unknown4", [
                 String(),
                 Integer(),
                 Integer(),
                 Integer(),
                 String(),
                 String(),
                 List("Unknown5", [
                  Integer(),
                  Integer(),
                  Integer(),
                  Flag(), Flag(),
                  String(),
                  Float(),
                  FloatTriplet(),
                  FloatTriplet(),
                  FloatTriplet(),
                  Integer(), # unused
                  Float(),
                  Integer(),
                  FloatTriplet(),
                  FloatPair(),
                  Integer(), # unused
                  FloatTriplet(),
                  FloatTriplet(),
                  FloatTriplet(),
                  Integer(),
                  FloatTriplet(),
                  Float(),
                  FloatTriplet(),
                  Float(),
                  Float(),
                  Float(),
                  Float(),
                  Float(),
                  Integer(),
                  Integer(),
                  Integer(),
                  FloatTriplet(),
                  FloatTriplet(),
                  Float(),
                  Float(),
                  Float(),
                  Float(),
                  Float(),
                  Float(),
                  Float(),
                  Float(),
                  FloatTriplet(),
                  FloatTriplet(),
                  Integer(), Integer(), # unused
                  Float(),
                  FloatTriplet(),
                  Integer(),
                  Float(),
                  FloatTriplet(),
                  FloatTriplet(),
                  FloatTriplet(),
                  Integer(), # unused
                  Float(),
                  Integer(),
                  Integer(), # unused
                  Integer(),
                  Float(),
                  Integer(),
                  Integer(), # unused
                  Float(),
                  Float(),
                  Integer(),
                  Integer(),
                  Integer(), # unused
                  Float(),
                  Float(),
                  Integer(), # unused
                  Float(),
                  Float(),
                  IntegerTriplet(),
                  IntegerTriplet(),
                  Integer(), # unused
                  Integer(),
                  Integer(),
                  IntegerTriplet(), # unused
                  IntegerTriplet(), # unused
                  Integer(),
                  IntegerTriplet(), # unused
                  Float(),
                  IntegerTriplet(), # unused
                  Integer(), # unused
                  Float(),
                  IntegerTriplet(), # unused
                  Integer(), # unused
                  Integer(),
                  IntegerTriplet(),
                  IntegerTriplet(),
                  Integer(), # unused
                  Integer(),
                  Integer(),
                  IntegerTriplet(), # unused
                  IntegerTriplet(), # unused
                  Integer(),
                  IntegerTriplet(), # unused
                  Integer(), # unused
                  Integer(),
                 ]),
                 String(),
                 String(),
                 Integer(),
                 Integer(),
                 Integer(), Integer(), # unused
                 Float(),
                 Integer(), Integer(),
                 Integer(), Integer(),
                 Integer(), Integer(), # unused
                 Array(StringList("Unknown6")),
                 Array(StringList("Unknown7")),
                 Integer(),
                 String(),
                 Array(StringList("Unknown8")),
                 String(),
                 String(),
                 String(),
                 String(),
                 String(),
                 String(),
                 String(),
                 List("Unknown9", [
                  String(),
                  String(),
                 ]),
                 List("Unknown10", [
                  String(),
                  FloatTriplet(),
                 ]),
                 Integer(),
                 Float(),
                 Float(),
                 Integer(),
                 Integer(),
                 Array(StringList("Unknown11")),
                 Array(StringList("Unknown12")),
                 String(),
                 Integer(),
                ]),
                Integer(),
                Float(),
               ]),
               Integer(),
               Integer(),
               Float(),
               Float(),
               FloatTriplet(),
               FloatTriplet(),
              ]),
  0x4e72020c: List("LoyaltyReward", [ # LoyaltyReward.bin
               Name(),
               String(),
               String(),
               String(),
               Integer(),
               List("Unknown", [
                String(),
                String(),
                String(),
                StringList(),
                Integer(),
                Integer(),
                Integer(),
               ]),
              ]),
  0x522ad306: List("DetailCat", [ # detailcats.bin
               Name(),
               String(),
               IntegerPair(),
               IntegerPair(),
               Integer(),
              ]),
  0x58032133: List("PCDefDestructObject", [ # PC_Def_DestructObject.bin
               Name(),
              ]),
  0x591c0566: List("PopHelp", [ # PopHelp.bin
               Name(),
               Integer(),
               String(),
               String(),
               String(),
               Integer(), # unused
               Integer(), # unused
              ]),
  0x59248ecb: List("PowerCat", [ # powercats.bin
               String(),
               Name(),
               String(),
               Integer(), # unused
               Integer(), # unused
               StringList(),
               Integer(), # unused
              ]),
  0x5a060975: List("Dept", [ # depts.bin
               Name(),
              ]),
  0x5d068463: Struct("BoostEffect", [ # boost_effect_*.bin
               FloatList(),
              ]),
  0x5b3be1a2: List("MapSpec", [ # mapspecs.bin
               Integer(),
               Integer(),
               StringList(),
               List("Unknown", [
                Integer(),
                List("Unknown2", [
                 Name(),
                ])
               ]),
              ]),
  0x5b3f53ab: List("Proficiency", [ # Proficiencies.bin
               Name(),
               String(),
               String(),
               String(),
               Integer(), # unused
               Integer(),
               Integer(),
              ]),
  0x5b9c4ac0: List("Salvage", [ # Salvage.bin
               Name(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(),
               StringList(),
               Integer(),
               StringList(),
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Integer(),
               Integer(),
               Integer(),
               String(),
              ]),
  0x5ba1b0e3: List("Trick", [ # tricks.bin
               Name(),
               String(),
               Float(),
               String(),
               Float(),
               String(),
               FloatPair(),
               OptFloatPair(),
               OptFloatPair(),
               String(),
               String(),
               Integer(),
               Flag(),
               Integer(),
               String(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               FloatPair(),
               Integer(),
               Integer(),
               String(),
               OptFloatPair(),
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Integer(),
               Integer(), Integer(), Integer(),
               Integer(), Integer(), Integer(),
               Integer(), Integer(), Integer(),
               Integer(), Integer(), Integer(),
               Integer(), Integer(),
               FloatPair(),
               Float(),
               FloatTriplet(),
               Integer(),
               Float(),
               Integer(),
               Integer(),
               IntegerTriplet(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               OptFloatTriplet(),
               OptFloatTriplet(),
               FloatTriplet(),
               Integer(),
               OptFloatPair(),
               OptFloatPair(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(),
               OptFloatTriplet(),
               OptFloatTriplet(),
               IntegerTriplet(), # unused
              ]),
  0x5c03f63a: List("PCDefMapSet", [ # PC_Def_MapSets.bin
               Name(),
               String(),
              ]),
  0x5d7d6c82: List("PCDefUI", [ # PC_Def_UI.bin
               Name(),
               String(),
               Integer(), Integer(), # unused
               List("Unknown1", [
                String(),
                Integer(), # unused
                Integer(),
                List("Unknown2", [
                 String(),
                 String(),
                 Integer(), Integer(), # unused
                 StringList(),
                 Integer(), # unused
                 List("Unknown3", [
                  String(),
                  Integer(), # unused
                  Integer(),
                  Integer(), Integer(), # unused
                  StringList(),
                  Integer(), # unused
                  String(),
                  Integer(), Integer(), # unused
                  String(),
                  Integer(), # unused
                  Integer(),
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(),
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), # unused
                 ]),
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), # unused
                 Integer(),
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                ]),
                Integer(), # unused
                StringList(),
                String(),
                String(),
                Integer(), Integer(), # unused
                String(),
                Integer(), Integer(), # unused
                Integer(), Integer(),
                Integer(), Integer(), Integer(), # unused
                Integer(), # unused
                Integer(), Integer(),
                Integer(), Integer(), Integer(), # unused
                Integer(), Integer(), Integer(), # unused
                Integer(), Integer(), # unused
               ]),
               List("Unknown4", [
                String(),
                Integer(), # unused
                List("Unknown5", [
                 String(),
                 Integer(), # unused
                 Integer(),
                 List("Unknown6", [
                  String(),
                  String(),
                  Integer(), # unused
                  Integer(),
                  Integer(), Integer(), # unused
                  List("Unknown7", [
                   String(),
                   Integer(), # unused
                   Integer(),
                   Integer(), Integer(), # unused
                   StringList(),
                   Integer(), # unused
                   String(),
                   Integer(), Integer(), # unused
                   String(),
                   Integer(), # unused
                   Integer(),
                   Integer(), Integer(), Integer(), # unused
                   Integer(), Integer(), Integer(),
                   Integer(), Integer(), Integer(), # unused
                   Integer(), Integer(), Integer(), # unused
                   Integer(), Integer(), Integer(), # unused
                   Integer(), # unused
                  ]),
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), # unused
                  Integer(),
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                  Integer(), Integer(), Integer(), # unused
                 ]),
                 Integer(), # unused
                 StringList(),
                 String(),
                 String(),
                 Integer(), Integer(), # unused
                 String(),
                 Integer(),
                 Integer(), # unused
                 Integer(), Integer(), Integer(),
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(),
                 Integer(), # unused
                 Integer(),
                 Integer(), Integer(), Integer(), # unused
                 Integer(), Integer(), Integer(), # unused
                ]),
                Integer(), # unused
                String(),
                Integer(), # unused
                Integer(),
                Integer(), Integer(), Integer(), # unused
               ]),
               String(),
               String(),
               String(),
               String(),
               Integer(), Integer(), Integer(), # unused
               Integer(), Integer(), # unused
               Integer(), Integer(),
              ]),
  0x6246004e: List("Cape", [ # capes.bin
               Name(),
               Float(),
               String(),
               String(),
               String(),
               String(),
               String(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               IntegerTriplet(),
               String(),
               String(),
               String(),
               String(),
               FloatTriplet(),
               IntegerPair(), # unused
               FloatTriplet(),
               Integer(),
               String(),
               String(),
              ]),
  0x6b0e7f06: List("SeqStateBit", [ # seqstatebits.bin
               Name(),
               Integer(),
              ]),
  0x6d043156: List("PCDefAnimation", [ # PC_Def_Animation.bin
               Name(),
               String(),
              ]),
  0x6d177c17: List("Origin", [ # origins.bin
               Name(),
               String(),
               String(),
               String(),
               String(),
              ]),
  0x6f0830ea: List("InvItem", [ # Inv*.bin, ProficiencyIds.bin
               Integer(),
               Name(),
              ]),
  0x7513c2d9: List("ArenaMap", [ # arenamaps.bin
               Name(),
               String(),
              ]),
  0x7520ffe0: List("MiniMap", [ # minimap.bin
               Name(),
               List("Unknown", [
                Integer(), # unused
                FloatPair(),
                List("Unknown2", [
                 String(),
                 Integer(), # unused
                 FloatPair(),
                 List("Unknown3", [
                  FloatPair(),
                  IntegerTriplet(), # unused
                  Float(),
                  IntegerPair(), # unused
                 ]),
                ]),
               ]),
               List("Unknown4", [
                Integer(), # unused
                FloatPair(),
                List("Unknown5", [
                 String(),
                 Integer(),
                 FloatPair(),
                 List("Unknown6", [
                  FloatPair(),
                  IntegerPair(), # unused
                  IntegerPair(), # unused
                  IntegerPair(),
                 ]),
                ]),
               ]),
               List("Unknown7", [
                Integer(), # unused
                FloatPair(),
                List("Unknown8", [
                 String(),
                 Integer(),
                 IntegerPair(), # unused
                 List("Unknown9", [
                  FloatTriplet(),
                  IntegerTriplet(), # unused
                  IntegerPair(),
                 ]),
                ]),
               ]),
              ]),
  0x7ff68aaf: List("Class", [ # classes.bin
               Name(),
               String("Text"),
               String("DescText"),
               StringList("Origin"),
               StringList("Alignment"),
               String("Cond"),
               String("CondText"),
               String("Cond2"),
               String(),
               Integer(),
               IntegerList(),
               String("RankText"),
               String("Icon"),
               String("Primary"),
               String("Secondary"),
               String(),
              ]),
  0x81031e47: List("BehaviorAlias", [ # behavioralias.bin
               Name(),
               String(),
               String(),
              ]),
  0x8506dc69: Struct("CombineChance", [ # combine_*chances.bin
               FloatList(),
              ]),
  0x8753ff10: List("Item", [ # items.bin
               Name(),
               Integer(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(), # unused
               Integer(), # unused
               Integer(),
               Integer(),
               Integer(), # unused
               IntegerList(),
              ]),
  0x881ecd94: Struct("CustomCritterRewardMod", [ # CustomCritterRewardMods.bin
               FloatList(),
               FloatList(),
               IntegerList(),
               Float(),
              ]),
  0x8a0b086a: List("SoundInfo", [ # soundinfo.bin
               Name(),
               Integer(),
               StringList(),
              ]),
  0x8e49f551: List("BoostSet", [ # boostsets.bin
               Name(),
               String(),
               String(),
               StringList(),
               StringList(),
               List("Unknown1", [
                StringList(),
               ]),
               List("Unknown2", [
                Integer(), # unused
                Integer(),
                Integer(),
                StringList(),
                StringList(),
                Integer(), # unused
               ]),
               Integer(),
               Integer(),
               String(),
              ]),
  0x8f12ada6: List("ChestGeoLink", [ # chestGeoLink.bin
               Name(),
               StringList(),
               String(),
              ]),
  0x9606818a: List("GeoBound", [ # geobin/*.bounds
               Name(),
               FloatTriplet(),
               FloatTriplet(),
               FloatTriplet(),
               FloatTriplet(),
              ]),
  0x9dfb79df: List("Sequencer", [ # sequencers.bin
               Name(),
               List("Unknown1", [
                Name(),
                String(),
                String(),
               ]),
               List("Unknown2", [
                String(),
               ]),
               List("Unknown3", [
                String(),
                Float(),
                Integer(),
                Integer(),
                Float(),
                Integer(), # unused
                Integer(), # unused
                List("Unknown4", [
                 String(),
                 List("Unknown5", [
                  String(),
                  Integer(),
                  Integer(),
                 ]),
                 Integer(),
                 List("Unknown6", [
                  String(),
                  Integer(),
                  Integer(),
                 ]),
                 FloatTriplet(),
                 FloatTriplet(),
                 Float(),
                 Integer(), # unused
                 String(),
                ]),
                String(),
                StringList(),
                StringList(),
                StringList(),
                StringList(),
                StringList(),
                Integer(), # unused
                Integer(), # unused
                Flag(),
                Integer(), Integer(), Integer(),
                Integer(), Integer(), Integer(),
                Integer(), # unused
                Integer(), Integer(), Integer(),
                Integer(), Integer(), Integer(),
                Integer(), Integer(), Integer(),
                Integer(), Integer(), Integer(),
                Integer(), Integer(), Integer(),
                Integer(),
                Integer(), Integer(), # unused
                Flag(), Flag(), Flag(), Flag(),
                Flag(), Flag(), Flag(), Flag(),
                Flag(), Flag(), Flag(), Flag(),
                Flag(), Flag(), Flag(), Flag(),
                Flag(), Flag(), Flag(), Flag(),
                Flag(), Flag(), Flag(), Flag(),
                Flag(), Flag(), Flag(), Flag(),
               ]),
              ]),
  0x9f2a61e2: OptStruct("Schedules", [ # schedules.bin
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
              ]),
  0xa3374618: List("Costume", [ # costume.bin
               Name(),
               List("CostumeClass", [
                Name(),
                String(),
                List("Colors1", [
                 Array(OptFloatTriplet("Color")),
                 String(),
                ]),
                List("Colors2", [
                 Array(OptFloatTriplet("Color")),
                 String(),
                ]),
                List("Colors3", [
                 Array(OptFloatTriplet("Color")),
                 String(),
                ]),
                List("BodyPart", [
                 Name(),
                 String(),
                 String(),
                 StringList(),
                 List("Unknown2", [
                  Name(),
                  String(),
                  String(),
                  StringList(),
                  String(),
                  StringList(),
                  List("Unknown3", [
                   String(),
                   String(),
                   String(),
                   StringList(),
                   StringList(),
                   Integer(), # unused?
                   Integer(),
                   StringList(),
                   StringList(),
                   Float(),
                   Float(),
                   Float(),
                   Float(),
                   Float(),
                   Float(),
                   Integer(),
                   Integer(),
                   List("Unknown4", [
                    String(),
                    String(),
                    String(),
                    String(),
                    String(),
                    String(),
                    String(),
                    StringList(),
                    StringList(),
                    StringList(),
                    Integer(),
                    Integer(),
                    Integer(),
                    Integer(),
                    Integer(),
                    Integer(), # unused
                    Integer(),
                   ]),
                   List("Unknown5", [
                    String(),
                    String(),
                    StringList(),
                    String(),
                    Integer(), # unused
                    Integer(),
                    Integer(),
                    Integer(),
                    Integer(),
                    Integer(), # unused
                   ]),
                   Integer(), Integer(), Integer(), # unused
                   List("Shape", [
                    String(),
                    Float(), Float(), Float(),
                    Float(), Float(), Float(),
                    Float(), Float(), Float(),
                    Float(), Float(), Float(),
                    Float(), Float(), Float(),
                    Float(), Float(), Float(),
                    Float(), Float(), Float(),
                    Float(), Float(), # unused
                   ]),
                   Integer(), Integer(), # unused
                  ]),
                  Integer(),
                  Integer(),
                  Integer(),
                 ]),
                 String(),
                ]),
                List("Unknown10", [
                 Name(),
                 String(),
                 String(),
                 String(),
                 StringList(),
                 StringList(),
                ]),
                List("Unknown11", [
                 Name(),
                 String(),
                 Float(),
                 Float(),
                 Float(), # unused
                 Float(),
                 Float(), # unused
                 Float(),
                ]),
               ])
              ]),
  0xa9447224: List("ClothColInfo", [ # clothcolinfo.bin
               Name(),
               List("Unknown", [
                List("Unknown2", [
                 String(),
                 String(),
                 Integer(),
                 FloatTriplet(),
                 FloatTriplet(),
                 FloatTriplet(),
                 IntegerTriplet(), # unused
                 IntegerTriplet(), # unused
                 String(),
                 Integer(),
                 Integer(),
                ]),
               ]),
              ]),
  0xae33a047: List("Card", [ # cards.bin
               Name(),
               String(),
               String(),
               String(),
               String(),
               List("Unknown", [
                Integer(),
                String(),
                Integer(),
                Integer(),
                String(),
                String(),
                String(),
                String(),
                String(),
                String(),
               ]),
              ]),
  0xb553b8ff: List("Power", [ # powers.bin
               Name(),
               Flag(),
               String(),
               String(),
               String(),
               Integer(), # unused
               Integer(),
               Integer(), # unused
               Integer(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(),
               IntegerList(),
               StringList(),
               StringList(),
               StringList(),
               StringList(),
               StringList(),
               StringList(),
               String(),
               Float(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Float(),
               Float(),
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Integer(), # unused
               Float(),
               Float(),
               Float(),
               Float(),
               Float(),
               Float(),
               Integer(), # unused
               Integer(),
               Integer(),
               StringList(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Float(),
               Float(),
               Float(),
               Float(),
               Float(),
               Float(),
               Float(),
               Integer(),
               Integer(),
               Integer(),
               IntegerList(),
               IntegerList(),
               Integer(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               StringList(),
               List("Unknown1", [
                String(), # category?
                String(),
                String(),
                String(),
                Integer(), # unused
                Integer(),
                Integer(),
                Integer(),
                Integer(), # unused
                Integer(),
                String(), # subcategory?
                Float(),
                Integer(),
                Integer(),
                Float(),
                Float(),
                Float(),
                Integer(),
                IntegerList(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                StringList(),
                StringList(),
                StringList(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Float(),
                StringList(),
                Float(),
                StringList(),
                Float(),
                Float(),
                List("Unknown3", [
                 Integer(),
                 Integer(),
                 Integer(),
                ]),
                String(),
                IntegerList(),
                String(),
                IntegerList(),
                String(),
                String(),
                String(),
                String(),
                String(),
                String(),
                String(),
                String(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Float(),
               ]),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(), # unused
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               String(),
               Integer(), # unused
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(), # unused
               Integer(),
               IntegerList(),
               Integer(),
               Integer(),
               StringList(),
               Integer(), # unused
               Integer(),
               Integer(),
               Integer(), # unused
               Integer(),
               Float(),
               Float(),
               Integer(),
               Float(),
               Float(),
               String(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Float(),
               Integer(), # unused
               Float(),
               Integer(),
               String(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               IntegerList(),
               Integer(), # unused
               IntegerList(),
               Integer(), # unused
               IntegerList(),
               String(),
               String(),
               String(),
               String(),
               String(),
               Integer(), # unused
               String(),
               String(),
               String(),
               String(),
               String(),
               String(),
               Integer(), # unused
               String(),
               String(),
               String(),
               String(),
               String(),
               IntegerList(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Float(),
               Integer(),
               String(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               List("Unknown4", [
                String(),
                StringList(),
                String(),
                Integer(), # unused
                String(),
                IntegerList(),
                IntegerList(),
                IntegerList(),
                IntegerList(),
                IntegerList(),
                IntegerList(),
                Integer(), # unused
                IntegerList(),
                Integer(), # unused
                Integer(), # unused
                String(),
                Integer(), # unused
                String(),
                String(),
                String(),
                Integer(), # unused
                Integer(), # unused
                String(),
                String(),
                String(),
                String(),
                String(),
                String(),
                String(),
                String(),
                Integer(), # unused
                Integer(), # unused
                Integer(), # unused
                IntegerList(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Float(),
                Integer(),
                String(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                Integer(),
                String(),
               ]),
              ]),
  0xb1110b4f: List("ConversionSet", [ # conversionsets.bin
               Name(),
               Integer(),
               Integer(),
               Integer(),
              ]),
  0xbe08eb7c: Struct("PCDefNonSelectableEntity", [ # PC_Def_NonSelectableEntities.bin
               Array(Name()),
              ]),
  0xbe2cf4d1: List("BaseRecipe", [ # baserecipes,bin
               String(),
               Name(),
               String(),
               String(),
               Integer(), # unused
               String(),
               String(),
               Integer(), # unused
               StringList(),
               List("Unknown1", [
                Integer(),
                String(),
               ]),
               List("Unknown2", [
                Integer(),
                String(),
               ]),
               StringList(),
               String(),
               Integer(), # unused
               String(),
               String(),
               String(),
               String(),
               StringList(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               StringList(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               StringList(),
               StringList(),
               StringList(),
               Integer(), # unused
               String(),
               String(),
               String(),
               String(),
               String(),
               Integer(),
              ]),
  0xbf963282: List("MapStat", [ # mapstats.bin
               Name(),
               Integer(), Integer(), Integer(), Integer(),
               List("Unknown", [
                Integer(), Integer(), Integer(), Integer(),
                Integer(), Integer(), Integer(),
                List("Unknown2", [
                 String(),
                 Integer(),
                 Integer(),
                ]),
               ]),
              ]),
  0xc8048c6a: List("Anim", [ # animlists.bin
               Name(),
               StringList(),
               String(),
              ]),
  0xcd3570e4: List("VillainGroup", [ # VillainGroups.bin
               Name(),
               String(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(),
              ]),
  0xcf27aba3: List("BodyPart", [ # bodyparts.bin
               Name(),
               String(),
               Integer(), Integer(),
               String(),
               String(),
               String(),
               Integer(),
               Integer(), # unused
               Integer(),
               Integer(), # unused
               Integer(),
              ]),
  0xd11484b8: List("KBMap", [ # kb.bin
               Name(),
               String(),
               List("Unknown", [
                String(),
                String(),
               ]),
              ]),
  0xd1a68118: List("VillainCostume", [ # VillainCostume.bin
               Name(),
               String(),
               List("Unknown1", [
                String(),
                String(),
                FloatTriplet(),
                FloatTriplet(),
                FloatTriplet(),
                FloatTriplet(),
                FloatTriplet(),
                FloatTriplet(),
                FloatTriplet(),
                FloatTriplet(),
                FloatTriplet(),
                FloatTriplet(),
                IntegerTriplet(),
                Integer(),
                Integer(),
                List("Unknown2", [
                 String(),
                 String(),
                 String(),
                 String(),
                 String(),
                 String(),
                 String(),
                 String(),
                 String(),
                 Integer(), # unused
                 IntegerTriplet(),
                 IntegerTriplet(),
                 IntegerTriplet(),
                 IntegerTriplet(),
                ]),
               ]),
               String(),
              ]),
  0xdd1e01e2: List("CostumeWeaponStance", [ # costumeWeaponStances.bin
               Name(),
               Flag(),
              ]),
  0xe8361497: List("LOD", [ # lods.bin
               Name(),
               String(),
               List("Unknown", [
                FloatTriplet(),
                FloatTriplet(),
                String(),
               ]),
              ]),
  0xea743a41: List("NPC", [ # npcs_client.bin
               String(),
               Name(),
               String(),
               String(),
               Integer(), # unused
               String(),
               String(),
               Integer(), # unused
               Integer(),
               StringList(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               StringList(),
               StringList(),
               Integer(),
               Integer(),
               StringList(),
               Integer(),
               StringList(),
               String(),
               Integer(), # unused
               Integer(), # unused
              ]),
  0xed07c5bd: List("PCDefUnlockableContent", [ # PC_Def_Unlockable_Content.bin
               Name(),
               String(),
              ]),
  0xee12dab3: Struct("AuctionConfig", [ # auctionconfig.bin
               Float(),
               Float(),
               Integer(),
              ]),
  0xef0ab73c: List("PowerCustomizationMenu", [ # powercustomizationmenu.bin
               Name(),
               Integer(),
               String(),
               String(),
              ]),
  0xf0095ef2: List("SupergroupColor", [ # supergroupColors.bin
               FloatTriplet(),
              ]),
  0xf249dd6c: List("Store", [ # stores.bin
               Name(),
               List("Unknown1", [
                Integer(),
                Float(),
               ]),
               List("Unknown2", [
                Integer(),
                Float(),
               ]),
               Integer(), # unused
               Float(),
               Float(),
              ]),
  0xf6195c7d: List("Command", [ # command.bin
               Name(),
               List("Unknown", [
                Name(),
                String(),
               ]),
              ]),
  0xf81dfffb: List("PowerCostumizationCost", [ # powercustomizationcost.bin
               Integer(),
               Integer(),
               Integer(),
               Integer(),
               Integer(),
              ]),
  0xf90949fa: List("PCDefSequencerAnim", [ # PC_Def_Sequencer_Anims.bin
               StringList(),
               StringList(),
              ]),
}

class DirEntry(object):
  def __init__(self, name, tstamp):
    self.name = name
    self.tstamp = datetime.datetime.fromtimestamp(tstamp)

class StringEntry(object):
  def __init__(self, name, data, fmts):
    self.name = name
    self.data = data
    self.fmts = fmts

class StringTableDecoder(object):
  def __init__(self):
    pass
  def list_names(self, f, sz, args=None):
    for ent in f.files:
      if not is_match(ent.name, args):
        continue
      name = ent.name
      fsize = len(ent.data)
      print "%6u  %s" % (fsize, name)
  def decode(self, f, sz, pfx, args=None, options=None):
    for ent in f.files:
      if not is_match(ent.name, args):
        continue
      name = ent.name
      if not options.quiet and not options.pipe:
        print "--- %s" % name
      data = ent.data
      if options.pipe:
        sys.stdout.write(data)
        sys.stdout.flush()
      else:
        print data

class BinFile(object):
  def __init__(self, fname):
    self.fname = fname
    self.files = []
    self.strings = []
    self.fmtstrings = []
    self.slots = []
    self.is_strings = False

    self.f = open(fname, "rb")

    sig = self.f.read(8)
    if sig != "CrypticS":
      # see if it's a string table
      shdr = struct.unpack("<LL", sig)
      if shdr[0] != 0x01328e99:
        print "Not a valid BIN file!"

      self.is_strings = True
      self.fmt = shdr[0]
      hdr1 = [shdr[1], self.read_struct("<L", 4)[0]]
      pos = self.tell()
      for n in range(0, hdr1[0]):
        s = self.read_cstring()
        self.strings.append(s)

      pos += hdr1[1]
      self.seek(pos)

      hdr2 = self.read_struct("<LL", 8)
      pos = self.tell()
      for n in range(0, hdr2[0]):
        s = self.read_cstring()
        self.fmtstrings.append(s)

      pos += hdr2[1]
      self.f.seek(pos)

      thdr = self.read_struct("<L", 4)
      for n in range(0, thdr[0]):
        slen = self.read_struct("<L", 4)[0]
        name = self.f.read(slen)
        ent = self.read_struct("<LLL", 12)
        s = "\n".join(self.strings[ent[0]:ent[1]+1])
        fmts = [self.read_struct("<L", 4)[0] for x in range(0, ent[2])]
        f = [(self.fmtstrings[x], self.fmtstrings[x+1]) for x in fmts]
        self.files.append(StringEntry(name, s, f))

      self.datasize = 0
      self.decoder = StringTableDecoder()
      return

    # it's a CrypticS file, try parsing it

    self.fmt = self.read_struct("<L", 4)[0]

    s1 = self.read_string()
    s2 = self.read_string()

    flsiz = self.read_struct("<L", 4)[0]
    pos = self.tell()

    # read file list
    flnum = self.read_struct("<L", 4)[0]
    for n in range(0, flnum):
      s = self.read_string()
      x = self.read_struct("<L", 4)[0]
      self.files.append(DirEntry(s, x))

    pos += flsiz
    self.seek(pos)

    self.datasize = self.read_struct("<L", 4)[0]

    if self.fmt in decoders:
      self.decoder = decoders.get(self.fmt)
    else:
      print "Unknown format %s, using fallback decoder" % hex(self.fmt)
      self.decoder = DefaultDecoder()

  def list_sources(self, args, options):
    if not self.is_strings:
      print "    Date   Time   Name"
      print "---------- -----  ----"
      for ent in self.files:
        if not is_match(ent.name, args):
          continue
        name = ent.name
        dt = ent.tstamp.strftime("%Y-%m-%d %H:%M")
        print "%s  %s" % (dt, name)

  def list_files(self, args, options):
    print "Length  Name"
    print "------  ----"
    self.decoder.list_names(self, self.datasize, args)

  def extract_files(self, args, options):
    self.decoder.decode(self, self.datasize, "", args, options)

  def tell(self):
    return self.f.tell()

  def seek(self, pos, whence=0):
    return self.f.seek(pos, whence)

  def read(self, sz):
    return self.f.read(sz)

  def read_struct(self, format, size):
    if size is None:
      size = struct.calcsize(format)
    data = self.f.read(size)
    return struct.unpack(format, data)

  def read_string(self):
    slen = self.read_struct("<H", 2)[0]
    # .bin files need dword-aligned reads
    alen = slen + 2
    part = alen & 3
    if part != 0:
      alen += 4 - part
    data = self.f.read(alen - 2)
    return data[:slen]

  def read_cstring(self):
    s = []
    while True:
      ch = self.f.read(1)
      if ch == "\0": break
      s.append(ch)
    return "".join(s)

def main():
  usage = "usage: %prog [options] file.pigg [filenames]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option("-l", "--list",
                    action="store_true", dest="list_files",
                    help="list contents of file")
  parser.add_option("-p", "--pipe",
                    action="store_true", dest="pipe",
                    help="extract to standard output")
  parser.add_option("-s", "--source",
                    action="store_true", dest="list_sources",
                    help="list source files")
  parser.add_option("-q", "--quiet",
                    action="store_true", dest="quiet",
                    help="quiet mode")

  (options, args) = parser.parse_args()

  if len(args) < 1:
    parser.error("need a filename")

  f = BinFile(args[0])
  if options.list_files:
    f.list_files(args[1:], options)
  elif options.list_sources:
    f.list_sources(args[1:], options)
  else:
    f.extract_files(args[1:], options)

if __name__ == "__main__":
  main()

