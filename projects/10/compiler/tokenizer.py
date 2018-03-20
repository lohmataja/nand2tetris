import collections
from enum import Enum

symbols = "{}()[].,;+-*/&|<>=~"
keywords = { 'class',
             'constructor',
             'function',
             'method',
             'field',
             'static',
             'var',
             'int',
             'char',
             'boolean',
             'void',
             'true',
             'false',
             'null',
             'this',
             'let',
             'do',
             'if',
             'else',
             'while',
             'return' }

class Token(Enum):
  SYMBOL       = 1
  KEYWORD      = 2
  INT_CONSTANT = 3
  STR_CONSTANT = 4
  IDENTIFIER   = 5

def token_type_to_str(token):
  if token == Token.INT_CONSTANT:
    return "integerConstant"
  elif token == Token.STR_CONSTANT:
    return "stringConstant"
  else:
    return token.name.lower()
  
class Tokenizer:
  def __init__(self, filename):
    with open(filename, 'r') as f:
      raw_lines = f.readlines()
      lines = collections.deque()
      in_comment = False
      for line in raw_lines:
        if in_comment:
          comment_end = line.find("*/")
          if comment_end == -1:
            continue
          else:
            line = line[comment_end + 2:]
            in_comment = False
        eol_comment = line.find("//")
        if eol_comment != -1:
          line = line[:eol_comment]
        comment_begin = line.find("/*")
        if comment_begin != -1:
          comment_end = line.find("*/")
          if comment_end == -1:
            in_comment = True
            line = line[:comment_begin]
          else:
            line = line[:comment_begin] + line[comment_end + 2:]
        line = line.strip()
        if len(line) > 0:
          lines.append(line)
      self.lines = lines
      self.tokens = collections.deque()

  def has_tokens(self):
    return (len(self.lines) > 0 or len(self.tokens) > 0)

  def tokenize(self, line):
    i = 0
    while i < len(line):
      if line[i] == " ":
        i += 1
        continue
      elif line[i] in symbols:
        self.tokens.append((Token.SYMBOL, line[i]))
        i += 1
      elif line[i] == '"':
        # tokenize string literal
        i += 1
        s = ""
        while line[i] != '"':
          s += line[i]
          i += 1
        self.tokens.append((Token.STR_CONSTANT, s))
        i += 1                # skip the quote
      elif line[i].isdigit():
        s = ""
        while i < len(line) and line[i].isdigit():
          s += line[i]
          i += 1
        self.tokens.append((Token.INT_CONSTANT, s))
      else:                     # parsing keyword or identifier
        s = ""
        while i < len(line) and line[i] not in symbols and line[i] != " ":
          s += line[i]
          i += 1
        if s in keywords:
          self.tokens.append((Token.KEYWORD, s))
        else:
          self.tokens.append((Token.IDENTIFIER, s))
                     
  def advance(self):
    if len(self.tokens) == 0:
      line = self.lines.popleft()
      self.tokenize(line)
    return self.tokens.popleft()
  
