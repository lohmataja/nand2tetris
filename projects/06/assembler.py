symbol_table = { "R0"  :  0,
                 "R1"  :  1,
                 "R2"  :  2,
                 "R3"  :  3,
                 "R4"  :  4,
                 "R5"  :  5,
                 "R6"  :  6,
                 "R7"  :  7,
                 "R8"  :  8,
                 "R9"  :  9,
                 "R10" : 10,
                 "R11" : 11,
                 "R12" : 12,
                 "R13" : 13,
                 "R14" : 14,
                 "R15" : 15,
                 "SP"     : 0,
                 "LCL"    : 1,
                 "ARG"    : 2,
                 "THIS"   : 3,
                 "THAT"   : 4,
                 "SCREEN" : 0x4000,
                 "KBD"    : 0x6000 }
cur_register = 16

instr_table = { "0"   : "0101010",
                "1"   : "0111111",
                "-1"  : "0111010",
                "D"   : "0001100",
                "A"   : "0110000",
                "!D"  : "0001101",
                "!A"  : "0110011",
                "-D"  : "0001111",
                "-A"  : "0110011",
                "D+1" : "0011111",
                "A+1" : "0110111",
                "D-1" : "0001110",
                "A-1" : "0110010",
                "D+A" : "0000010",
                "D-A" : "0010011",
                "A-D" : "0000111",
                "D&A" : "0000000",
                "D|A" : "0010101",

                "M"   : "1110000",
                "!M"  : "1110001",
                "-M"  : "1110011",
                "M+1" : "1110111",
                "M-1" : "1110010",
                "D+M" : "1000010",
                "D-M" : "1010011",
                "M-D" : "1000111",
                "D&M" : "1000000",
                "D|M" : "1010101" }

dest_table = { "A"   : "100",
               "M"   : "001",
               "D"   : "010",
               "AM"  : "101",
               "AD"  : "110",
               "MD"  : "011",
               "AMD" : "111"}

jump_table = { "JGT" : "001",
               "JEQ" : "010",
               "JGE" : "011",
               "JLT" : "100",
               "JNE" : "101",
               "JLE" : "110",
               "JMP" : "111" }

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("input")
args = parser.parse_args()
input_file = args.input
output_file = input_file.split(".")[0] + ".hack"
f = open(input_file, 'r')
output = open(output_file, 'w')
instructions = []

# First pass to populate symbol table and strip comments
for line in f.readlines():
    comment = line.find("//")
    if comment == -1:  
        line = line.strip()
    else:
        line = line[:comment].strip()
    if line != "":
        if line[0] == '(':
            symbol_table[line[1:-1]] = len(instructions)
        else:
            instructions.append(line)
            
# Second pass to populate the .hack file
for instruction in instructions:
    if instruction[0] == "@":
        symbol = instruction[1:]
        if symbol[0].isalpha(): # This is a symbol
            if symbol not in symbol_table:
                symbol_table[symbol] = cur_register
                cur_register += 1
            val = symbol_table[symbol]
        else:
            val = int(symbol)
        output.write("{0:{fill}16b}\n".format(val, fill='0'))
    else:
        dst_split = instruction.split("=")
        if len(dst_split) > 1:
            dst = dest_table[dst_split[0]]
            instruction = dst_split[1]
        else:
            dst = "000"
        # calculation part is always populated
        jump_split = instruction.split(";")
        if len(jump_split) > 1:
            jmp = jump_table[jump_split[1]]
            instruction = jump_split[0]
        else:
            jmp = "000"
        output.write("111" + instr_table[instruction] + dst + jmp + "\n")
            
