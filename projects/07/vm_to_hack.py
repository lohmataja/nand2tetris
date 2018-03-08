import argparse, os

parser = argparse.ArgumentParser()
parser.add_argument("input")
args = parser.parse_args()

def is_vm_file(f):
  return f.endswith(".vm")

def find_all_vm_files(path):
  if os.path.isfile(path):
    if is_vm_file(path):
      return [ path ]
  else:
    out = []
    for root, subdirs, files in os.walk(path):
      for f in files:
        if is_vm_file(f):
          out.append(os.path.join(root, f))
    return out
  
input_files = find_all_vm_files(args.input)
print ("Got files:\n  " + "\n  ".join(input_files))

def strip_comment(line):
  comment = line.find("//")
  if comment == -1:  
    line = line.strip()
  else:
    line = line[:comment].strip()
  return line
  
def parse(input_file):
  out = []
  with open(input_file, 'r') as f:
    for line in f.readlines():
      line = strip_comment(line)
      if line != "":
        out.append(line)
  return out

segments = { "local"    : "LCL",
             "argument" : "ARG",
             "this"     : "THIS",
             "that"     : "THAT",
             "pointer"  : "THIS"}

direct = { "temp" : 5,
           "pointer" : 3 }

def at_direct(segment, index):
  return ("@" + str(direct[segment] + int(index)))

def push_command(segment, index, filename):
  if segment == "constant":
    out = "@" + index + """
D=A"""
  elif segment == "static":
    out = "@" + filename + index + """
D=M"""
  elif segment in direct:
    out = at_direct(segment, index) + """
D=M"""
  else:
    out = "@" + index + """
D=A
@""" + segments[segment] + """
A=M+D
D=M"""
  # assume the value is in D now
  return(out + """
@SP
A=M
M=D
@SP
M=M+1""")

def pop_command(segment, index, filename):
  pop_to_D = """@SP
AM=M-1
D=M
"""
  follow_ptr_and_store_D = """
M=D"""
  if segment in direct:
    middle = at_direct(segment, index)
  elif segment == "static":
    middle = "@" + filename + index
  else:
    middle = """@tmp
M=D
@""" + index + """
D=A
@""" + segments[segment] + """
D=M+D
@tmp1
M=D
@tmp
D=M
@tmp1
A=M"""
  return pop_to_D + middle + follow_ptr_and_store_D

jump_counter = lambda : 1
jump_counter.cur = 0

jumps = { "eq" : "JEQ",
          "gt" : "JGT",
          "lt" : "JLT" }

def comparison(f, cur_jmp=cur_jmp):
  jmp = str(jump_counter.cur)
  jump_counter.cur += 1
  return """D=M-D
@IFTRUE""" + jmp + """
D;""" + jumps[f] + """
D=0
@CONTINUE""" + jmp + """
D;JMP
(IFTRUE""" + jmp + """)
D=-1
(CONTINUE""" + jmp + """)
@SP
A=M
M=D
@SP
M=M+1"""

simple_functions = { "add" : "+",
                     "sub" : "-",
                     "and" : "&",
                     "or"  : "|"}

def apply2(f):
  out = """@SP
AM=M-1
D=M
@SP
AM=M-1
"""
  if f in simple_functions:
    return out + "M=M" + simple_functions[f] + """D
@SP
M=M+1"""
  else:
    return out + comparison(f)

unary_functions = { "neg" : "-",
                    "not" : "!" }

def apply(f):
  return """@SP
A=M-1
M=""" + unary_functions[f] + "M"

def translate_instruction(instruction, filename):
  out = [ "// " + instruction ]
  instruction = instruction.split()
  if len(instruction) == 3:
    if instruction[0] == "push":
      out.append(push_command(instruction[1], instruction[2], filename))
    elif instruction[0] == "pop":
      out.append(pop_command(instruction[1], instruction[2], filename))
    else:
      raise(instruction[0])
  elif len(instruction) == 1:
    f = instruction[0]
    if f in unary_functions:
      out.append(apply(f))
    else:
      out.append(apply2(instruction[0]))
  return("\n".join(out) + "\n")

for input_file in input_files:
  output_file = input_file[:-2] + "asm"
  filename = os.path.basename(input_file)[:-2]
  with open(output_file, 'w') as out:
    print("Working on ", output_file)
    instructions = parse(input_file)
    for instruction in instructions:
      out.write(translate_instruction(instruction, filename))
    print("Done with ", output_file)
    
