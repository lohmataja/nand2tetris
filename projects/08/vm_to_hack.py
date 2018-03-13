import argparse, os

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

counter = lambda : 1
counter.cur_jump = 0
counter.cur_retaddr = 0

jumps = { "eq" : "JEQ",
          "gt" : "JGT",
          "lt" : "JLT" }

def comparison(f):
  jmp = str(counter.cur_jump)
  counter.cur_jump += 1
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

def if_goto(label):
  return """@SP
AM=M-1
D=M
@""" + label + """
D;JNE"""

def function(name, num_locals):
  return "(" + name + (")" if num_locals == 0 else """)
@SP
A=M
""" + "A=A+1\n".join([ "M=0\n" ] * num_locals ) + """D=A+1
@SP
M=D""")

restore_frame = \
  "\n".join(["""// {0} = *(FRAME-{1})
@frame
AM=M-1
D=M
@{0}
M=D""".format(ptr, offset) for (ptr, offset)
             in [("THAT", "1"), \
                 ("THIS", "2"), \
                 ("ARG" , "3"), \
                 ("LCL" , "4")# , \
                 # ("RET" , "5")
             ]])

return_code = """// FRAME = LCL
@LCL
D=M
@frame
M=D
@5
D=A
@frame
A=M-D
D=M
@RET
M=D
// *ARG = pop()
@SP
AM=M-1
D=M
@ARG
A=M
M=D
// SP = ARG+1
@ARG
D=M+1
@SP
M=D
""" + restore_frame + """
// goto RET
@RET
A=M
0;JMP"""

def call(fun_name, num_args):
  ret_addr = "RETURN_ADDRESS_" + str(counter.cur_retaddr)
  counter.cur_retaddr += 1
  return ("@" + ret_addr + """
D=A
@SP
A=M
M=D
@SP
M=M+1
""" + "\n".join(["// push " + ptr + """
@""" + ptr + """
D=M
@SP
A=M
M=D
@SP
M=M+1""" for ptr in ["LCL", "ARG", "THIS", "THAT"]]) + """
// ARG = SP-n-5
@5
D=A
@""" + num_args + """
D=A+D
@SP
D=M-D
@ARG
M=D
// LCL = SP
@SP
D=M
@LCL
M=D
// goto f
@""" + fun_name + """
0;JMP
// (return-address)
(""" + ret_addr + ")")

def translate_instruction(instruction, filename):
  out = [ "// " + instruction ]
  instruction = instruction.split()
  if len(instruction) == 3:
    if instruction[0] == "push":
      out.append(push_command(instruction[1], instruction[2], filename))
    elif instruction[0] == "pop":
      out.append(pop_command(instruction[1], instruction[2], filename))
    elif instruction[0] == "function":
      out.append(function(name = instruction[1], \
                          num_locals = int(instruction[2])))
    elif instruction[0] == "call":
      out.append(call(fun_name = instruction[1], \
                      num_args = instruction[2]))
    else:
      raise(instruction[0])
  elif len(instruction) == 2:
    label = filename + instruction[1]
    if instruction[0] == "label":
      out.append("(" + label + ")")
    elif instruction[0] == "goto":
      out.append("@" + label + "\n0;JMP")
    elif instruction[0] == "if-goto":
      out.append(if_goto(label))
  elif len(instruction) == 1:
    f = instruction[0]
    if f == "return":
      out.append(return_code)
    elif f in unary_functions:
      out.append(apply(f))
    else:
      out.append(apply2(instruction[0]))
  return("\n".join(out) + "\n")

def is_vm_file(f):
  return f.endswith(".vm")

def get_filenames():
  parser = argparse.ArgumentParser()
  parser.add_argument("input")
  args = parser.parse_args()
  input_file = args.input
  print("Input (file or dir): ", input_file)
  if os.path.isfile(input_file):
    if is_vm_file(input_file):
      write_bootstrap = False
      output_file = input_file[:-2] + "asm"
      return ([input_file], output_file, write_bootstrap)
    else:
      raise("Input is not a .vm file")
  else:                         # input is a directory!
    write_bootstrap = True
    output_filename = os.path.dirname(input_file).rsplit("/")[-1] + ".asm"
    output_file = os.path.join(input_file, output_filename)
    out = []
    for f in os.listdir(input_file):
      if is_vm_file(f):
        out.append(os.path.join(input_file, f))
    return (out, output_file, write_bootstrap)
    
def main():
  vm_files, output_file, write_bootstrap = get_filenames()
  print("VM files: ", vm_files, "\nOutput file: ", output_file)
  with open(output_file, 'w') as out:
    if write_bootstrap:
      out.write("""// initialize memory
@256
D=A
@SP
M=D
""" + call(fun_name = "Sys.init", num_args = "0"))
    for input_file in vm_files:
      filename = os.path.basename(input_file)[:-2]
      print("Working on ", input_file)
      instructions = parse(input_file)
      for instruction in instructions:
        out.write(translate_instruction(instruction, filename))
      print("Done with ", input_file)
        
if __name__ == "__main__":
  main()
