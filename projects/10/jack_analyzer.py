#!/usr/bin/env python3
import argparse, os
from compiler.parser import parse, get_tokens
import xml.etree.ElementTree as ET

def is_jack_file(filename):
  return (filename.endswith("jack"))

def output_filenames(input_file):
  tokens_file = input_file[:-5] + "T2.xml"
  compiled_file = input_file[:-5] + "2.xml"
  return (tokens_file, compiled_file)

def get_filenames():
  parser = argparse.ArgumentParser()
  parser.add_argument("input")
  args = parser.parse_args()
  input_file = args.input
  print("Input (file or dir): ", input_file)
  if os.path.isfile(input_file):
    if is_jack_file(input_file):
      tokens_file, compiled_file = output_filenames(input_file)
      return (input_file, tokens_file, compiled_file)
    else:
      raise("Input is not a .jack file")
  else:                         # input is a directory!
    input_dir = input_file
    out = []
    for input_file in os.listdir(input_dir):
      if is_jack_file(input_file):
        in_file = os.path.join(input_dir, input_file)
        tokens_file, compiled_file = output_filenames(in_file)
        out.append((in_file, tokens_file, compiled_file))
      else:
        print('Not a .jack file: ', input_file)
    return out

def to_pretty_string(tree, prefix):
  children = list(tree)
  if len(children) == 0 and tree.text != None:
    return (prefix + ET.tostring(tree, \
                                 encoding = "unicode", \
                                 short_empty_elements = False))
  else:
    return (prefix + "<" + tree.tag + ">\n" + \
            "\n".join(map(lambda c : to_pretty_string(c, prefix + "  "), \
                          children)) + \
            ("\n" if children else "") + prefix + "</" + tree.tag + ">")
  
def pretty_dump(tree, out):
  with open(out, 'w') as out:
    out.write(to_pretty_string(tree, ""))
  
def main():
  files = get_filenames()
  for (input_file, tokens_file, compiled_file) in files:
    print("Parsing ", input_file, "into tokens file ", tokens_file, "and compiled file", compiled_file)
    tokens = get_tokens(input_file)
    ast = parse(input_file)
    pretty_dump(tokens, tokens_file)
    pretty_dump(ast, compiled_file)
  
if __name__ == "__main__":
  main()
