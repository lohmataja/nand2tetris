from .tokenizer import Tokenizer, Token, token_type_to_str
import xml.etree.ElementTree as ET

def add(tree, token_type, token):
  child = ET.SubElement(tree, token_type_to_str(token_type))
  child.text = token

class Parser:
  def __init__(self, tokenizer):
    self.tokenizer = tokenizer

  def advance(self):
    if self.tokenizer.has_tokens():
      self.token_type, self.token = self.tokenizer.advance()
      print ("Advancing: ", token_type_to_str(self.token_type), self.token)
    else:
      raise Exception("Ran out of tokens")

  def ensure_type(self, expected_type):
    if not self.token_type == expected_type:
      raise Exception("Token type mismatch. Expected" + \
                      expected_type.name + \
                      ", got: " + self.token_type.name)

  def ensure_token_is(self, expected):
    if not self.token == expected:
      raise Exception("Token mismatch. Expected: " + expected + \
             ", got: " + self.token)

  def add_current_and_advance(self, tree):
    add(tree, self.token_type, self.token)
    self.advance()

  def parse_token(self, symbol, tree):
    self.ensure_token_is(symbol)
    self.add_current_and_advance(tree)

  def current_token_is_type(self):
    return (self.token in ["int", "char", "boolean", "void"] \
            or self.token_type == Token.IDENTIFIER)

  def ensure_current_token_is_type(self):
    if not self.current_token_is_type():
      raise ("Expected type token, got " + self.token)

  # TODO: maybe split parse_type and parse_void_or_type
  def parse_type(self, tree):
    self.ensure_current_token_is_type()
    self.add_current_and_advance(tree)

  def parse_varName(self, tree):
    self.ensure_type(Token.IDENTIFIER)
    self.add_current_and_advance(tree)

  def parse_varNames(self, tree):
    self.parse_varName(tree)
    while self.token == ",":
      self.add_current_and_advance(tree) # add ","
      self.parse_varName(tree)       # add varName

  def parse_classVarDec(self, tree):
    tree = ET.SubElement(tree, "classVarDec")
    self.add_current_and_advance(tree) # static | field
    self.parse_type(tree)
    self.parse_varNames(tree)
    self.parse_token(";", tree)

  def parse_parameter(self, tree):
    self.parse_type(tree)
    self.parse_varName(tree)
  
  # 0 or 1 times
  def parse_parameter_list(self, tree):
    tree = ET.SubElement(tree, "parameterList")
    if self.current_token_is_type():
      self.parse_parameter(tree)
      while self.token == ",":
        self.add_current_and_advance(tree) # ","
        self.parse_parameter(tree)

  def parse_varDecs(self, tree):
    while self.token == "var":
      varDec = ET.SubElement(tree, "varDec")
      self.add_current_and_advance(varDec)
      self.parse_type(varDec)
      self.parse_varNames(varDec)
      self.parse_token(";", varDec)

  def parse_subroutine_call(self, tree, prev_token_type, prev_token):
    add(tree, prev_token_type, prev_token)
    if self.token == "(":
      self.add_current_and_advance(tree)
      self.parse_expression_list(tree)
      self.parse_token(")", tree)
    elif self.token == ".":
      self.add_current_and_advance(tree)
      self.parse_varName(tree)
      self.parse_token("(", tree)
      self.parse_expression_list(tree)
      self.parse_token(")", tree)
    else:
      raise Exception("Parsing subroutineCall. Expected '(' or '.', got " + self.token)

  def parse_term(self, tree, raise_if_not_a_term):
    tree = ET.SubElement(tree, "term")
    keyword_constants = { "true", "false", "null", "this" }
    unary_ops = "-~"
    print ("Parsing term. ", self.token)
    if self.token_type in [Token.INT_CONSTANT, Token.STR_CONSTANT]:
      self.add_current_and_advance(tree)
    elif self.token in keyword_constants:
      self.add_current_and_advance(tree)
    elif self.token in unary_ops:
      self.add_current_and_advance(tree)
      self.parse_term(tree, raise_if_not_a_term = True)
    elif self.token == "(":
      self.add_current_and_advance(tree)
      self.parse_expression(tree, raise_if_not_a_term = True)
      self.parse_token(")", tree)
    elif self.token_type == Token.IDENTIFIER:
      prev_token = self.token
      prev_token_type = self.token_type
      self.advance()
      if self.token == "[":          # varName [ expression ]
        add(tree, prev_token_type, prev_token)
        self.add_current_and_advance(tree)
        self.parse_expression(tree, raise_if_not_a_term = True)
        self.parse_token("]", tree)
      elif self.token in "(.":        # subroutineCall
        self.parse_subroutine_call(tree, prev_token_type, prev_token)
      else:                       # varName
        add(tree, prev_token_type, prev_token)
    else: # this was not a term
      if raise_if_not_a_term:
        raise Exception("Expected term. Got: " + self.token_type.name + " " + self.token)
    
  def parse_expression(self, tree, raise_if_not_a_term):
    tree = ET.SubElement(tree, "expression")
    self.parse_term(tree, raise_if_not_a_term)
    ops = "+-*/&|<>="
    while self.token in ops:
      self.add_current_and_advance(tree)
      self.parse_term(tree, raise_if_not_a_term = True)

  def parse_expression_list(self, tree):
    tree = ET.SubElement(tree, "expressionList")
    if self.token != ")":
      self.parse_expression(tree, raise_if_not_a_term = False)
      while self.token == ",":
        self.add_current_and_advance(tree)
        self.parse_expression(tree, raise_if_not_a_term = True)
    
  def parse_let_statement(self, tree):
    tree = ET.SubElement(tree, "letStatement")
    self.add_current_and_advance(tree)
    self.parse_varName(tree)
    if self.token == "[":
      self.add_current_and_advance(tree)
      self.parse_expression(tree, raise_if_not_a_term = True)
      self.parse_token("]", tree)
    self.parse_token("=", tree)
    self.parse_expression(tree, raise_if_not_a_term = True)
    self.parse_token(";", tree)

  def parse_if_statement(self, tree):
    tree = ET.SubElement(tree, "ifStatement")
    self.add_current_and_advance(tree)
    self.parse_token("(", tree)
    self.parse_expression(tree, raise_if_not_a_term = True)
    self.parse_token(")", tree)
    self.parse_token("{", tree)
    self.parse_statements(tree)
    self.parse_token("}", tree)
    if self.token == "else":
      self.add_current_and_advance(tree)
      self.parse_token("{", tree)
      self.parse_statements(tree)
      self.parse_token("}", tree)
      
  def parse_while_statement(self, tree):
    tree = ET.SubElement(tree, "whileStatement")
    self.add_current_and_advance(tree)
    self.parse_token("(", tree)
    self.parse_expression(tree, raise_if_not_a_term = True)
    self.parse_token(")", tree)
    self.parse_token("{", tree)
    self.parse_statements(tree)
    self.parse_token("}", tree)

  def parse_do_statement(self, tree):
    tree = ET.SubElement(tree, "doStatement")
    self.add_current_and_advance(tree)
    prev_token_type = self.token_type
    prev_token = self.token
    self.advance()
    self.parse_subroutine_call(tree, prev_token_type, prev_token)
    self.parse_token(";", tree)

  def parse_return_statement(self, tree):
    tree = ET.SubElement(tree, "returnStatement")
    self.add_current_and_advance(tree)
    if self.token != ";":
      self.parse_expression(tree, raise_if_not_a_term = True)
    self.parse_token(";", tree)
  
  def parse_statements(self, tree):
    tree = ET.SubElement(tree, "statements")
    statements = { "let"    : self.parse_let_statement,
                   "if"     : self.parse_if_statement,
                   "while"  : self.parse_while_statement,
                   "do"     : self.parse_do_statement,
                   "return" : self.parse_return_statement }
    while self.token in statements:
      statements[self.token](tree)
      
  def parse_subroutineBody(self, tree):
    tree = ET.SubElement(tree, "subroutineBody")
    self.parse_token("{", tree)
    self.parse_varDecs(tree)
    self.parse_statements(tree)
    self.parse_token("}", tree)
    
  def parse_subroutineDec(self, tree):
    tree = ET.SubElement(tree, "subroutineDec")
    self.add_current_and_advance(tree)
    self.parse_type(tree)
    self.add_current_and_advance(tree)  # subroutineName
    self.parse_token("(", tree)
    self.parse_parameter_list(tree)
    self.parse_token(")", tree)
    self.parse_subroutineBody(tree)
  
  def parse_class(self):
    if not self.tokenizer.has_tokens():
      return
    self.advance()              # get first token
    if self.token != "class":
      raise ("Excpected 'class', got " + self.token)
    tree = ET.Element("class")
    self.add_current_and_advance(tree)
    self.ensure_type(Token.IDENTIFIER) # className
    self.add_current_and_advance(tree)
    self.parse_token("{", tree)
    while self.token in ["static", "field"]:
      self.parse_classVarDec(tree)
    while self.token in ["constructor", "function", "method"]:
      self.parse_subroutineDec(tree)
    # This should end out tokens. Check invariant and avoid advancing.
    assert(self.token == "}")
    assert(not self.tokenizer.has_tokens())
    add(tree, self.token_type, self.token)
    return tree
  
def parse(input_file):
  tokenizer = Tokenizer(input_file)
  parser = Parser(tokenizer)
  return parser.parse_class()

def get_tokens(input_file):
  tokenizer = Tokenizer(input_file)
  tree = ET.Element("tokens")
  while tokenizer.has_tokens():
    token_type, token = tokenizer.advance()
    add(tree, token_type, token)
  return tree
    
