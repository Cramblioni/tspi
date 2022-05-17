
# token scanner pseudocode interpreter
# tspi [pronounced as "taspie"]
# written in python 3.10, may not be compatible with
# version lower than 3.8, though fully compatible with
# 3.9

## general structure
## input buffer
## output buffer
## current frame
## frame stack

## a frame is just ( inputbuffer,
##                   outputbuffer,
##                   instructions,
##                   instruction pointer)

## when an error is raised then the interpreter pops a
## frame from the frame stack, If it fails then it
## then it reraises the error, else the frame popped is
## used as the new current frame

## instructions
# consume :
#     takes a character from the input buffer and adds
#     it to the output buffer

# omit :
#     takes a character from the input buffer and throws
#     it out

# push [body] :
#     pushes a copy of the current frame onto the stack
#     but with the code in it's body

# pop :
#     pops a frame from the stack

# assert [charset]:
#     if the front of the input buffer isn't in charset
#     then raise an error

# finish :
#     halts execution and makes the program return the
#     output buffer

# select :
#     body only contains case statements, If the front of
#     the input buffer doesn't satisfy a case then it
#     raises an error in a similar fashion to assert

# case [charset] :
#     Only appears in the body of a "select" instruction
#     and defines each case the instruction can match

## A program MUST terminate with a `finish` instruction,
## if it does not then an error is raised.

## this language uses significant whitespace for code
## bodies

import sys

from dataclasses import dataclass
from enum import Enum,auto
from io import StringIO

class _TokenType(Enum):
  """
An enumerator for keeping track of what type a token is. I would've had each
token type as a dataclass, but since there's only two and both would just be
the same structure wise, It's easier to have them as a tuple with the type
and the actual token itself. Less lines too.
  """
  WORD = auto()
  CHRSET = auto()
  
def _chunk(text : str) -> list:
  """
Takes the text and splits it into a list of lines, each line is annotated
with what line number it is and what lines belong to it. The
contents of the line is also stripped and scanned, tspi has two token types
one of which is a word, the other is a charset.

lines are structured using tuples as
    (line_number : int, tokens : tuple, body : tuple)

word Tokens will be structured using a tuple as
    (_TokenType.WORD, word : str)
    
chrset Tokens will be structured using a tuple as
    (_TokenType.CHRSET, chars : str)
with the chars being put through a `set` first to ensure each option appears
once
  """
  
  
  # I'm annotating the three variables below because they'll change throughout
  # the runtime of the loop just below them, If i don't annotate a variable
  # then it's safe to assume I'll be trying to keep it constant
  indent_stack : list = [0] 
  line_stack : list = [[]] # index 0 is the output
  current_line : list = line_stack[0]
  
  for lnum, line in enumerate(text.split("\n")):
    if line == "":
      # skips empty lines, this also makes the whole indenting system more
      # stable, this doesn't disrupt line counting due to the `enumerate`
      # statement above
      continue
    line_stripped = line.lstrip()
    indent = len(line) - len(line_stripped)
    
    if indent > indent_stack[-1]:
      # preps a new line list and pushes a new indent onto the stack
      current_line = []
      line_stack.append(current_line)
      indent_stack.append(indent)
      
    elif indent < indent_stack[-1]:
      # pop indents off the stack until you reach the correct indent level
      # this also moves pops a line list off the line stack and tuples it up
      # putting it in the body slot of the last line in the previous indent
      # level
      while indent_stack[-1] != indent:
        indent_stack.pop()
        body = tuple(line_stack.pop())
        current_line = line_stack[-1]
        current_line[-1] = (current_line[-1][0],current_line[-1][1],body)
        if indent_stack[-1] < indent:
          # If we've missed the the indent, then syntax error
          raise SyntaxError(f"mismatch indent on line {lnum}")
    # now we go scanning/ lexing
    # This should be easy enough, whitespace is skipped, if a token starts
    # with a letter then it is treated as a word. If it starts with `(`
    # then it is treated as a charset.

    # words will satisfy /[a-zA-Z]+/
    # and charsets satisfy /\(.*\)/
    # where . matches all non whitespace characters also \ is an escape character

    # I won't be using the `re` library because this is too simple to need that

    tokens : list = [] # we will convert this to a tuple later
    cur_ind : int = 0
    max_len = len(line)
    while cur_ind  < max_len:
      # part of this loop was machine generated
      cur_char = line[cur_ind]
      
      if cur_char == " ":
        #skipping space
        cur_ind += 1
      if cur_char == ";":
        # breaking if the rest of the line is a comment
        break
      elif cur_char == "(":
        # handling charset
        buff : str = ""
        cur_ind += 1
        while cur_ind  < max_len and line[cur_ind] != ")":
          if line[cur_ind] == "\\":
            cur_ind += 1
          buff += line[cur_ind]
          cur_ind += 1
        cur_ind += 1
        tokens.append((_TokenType.CHRSET,"".join(set(buff))))
      elif cur_char.isalpha():
        # handling words
        buff : str = ""
        while cur_ind < max_len and line[cur_ind].isalpha():
          buff += line[cur_ind]
          cur_ind += 1
        tokens.append((_TokenType.WORD, buff))
      else:
        # raise error [eventually]
        pass
    if tokens:
      current_line.append((lnum, tuple(tokens),()))

  # finally de-indent until you get back to the base indent
  while len(line_stack) > 1:
    body = tuple(line_stack.pop())
    current_line = line_stack[-1]
    current_line[-1] = (current_line[-1][0],current_line[-1][1],body)


  # reduntant comment but we've finished chunking and scanning/lexing
  return line_stack.pop()

# below are the dataclasses `_parse` will use in it's output and `_interpret`
# will interpret. This will also be the only scenario where I'll be using
# inheritance / deriving, But I'll just be doing that manually and not letting
# python do it, because it's simpler

# all of these dataclasses will be frozen, This is because any mutation is an
# error in the interpreter step, So i want there to be an exception if they do
# mutate.

# each class has an attribute called `.lineref`, This is going to be the line
# which generated the instruction

@dataclass(frozen=True)
class _instMove:
  """
Instructs the interpreter to move a character from the input buffer to the
output buffer, Or just drop the character if `.drop` is true
  """
  lineref : tuple
  drop    : bool

@dataclass(frozen=True)
class _instFinish:
  """
Instructs the interpreter to halt execution and return the current output
buffer.
  """
  lineref : tuple

@dataclass(frozen=True)
class _instAssert:
  """
Checks if the front of the input buffer is in `.charset`, if it is not then it
raises an error
  """
  lineref : tuple
  charset : str

@dataclass(frozen=True)
class _instSelect:
  """
Checks the front of the input buffer, If it's in `.cases` then it'll execute
the code associated with it. If the front of the input buffer isn't in `.cases`
then it behaves like "assert" and raises an error
  """
  lineref : tuple
  cases   : dict

@dataclass(frozen=True)
class _instStack:
  """
If `.pop` is True, Then it pops from the frame stack. If `.pop` is False then
it pushes `.frame` onto the frame stack
  """
  lineref : tuple
  pop     : bool
  frame   : tuple # this is just the code to run



def _parse(chunks : list) -> list:
  """
Takes the mess of an output from `_chunk` and parses it into a list of simple
instructions which can be fed to `_interpret`

most of these instructions are just dataclasses, This is to use runtime type-
checking to simplify interpreting, Since We want that to be as stable as possible.
  """

  # I'll be using nested functions, Sorry in advance for those who dispise these

  def _parse_line(single : tuple) -> object:
    "parses a single line"
    # unpacking the line
    lnum,((inst_type,inst),*tokens),body = single
    # instructions follow a [instruction, *arguments] structure
    # hence the weird multiple assignment above. Sorry.
    if inst_type is not _TokenType.WORD:
      raise SyntaxError(f"Expected command on line {lnum}")
    elif inst == "push":
      body = _parse_many(body)
      return _instStack(single,False,body)
    elif inst == "pop":
      return _instStack(single,True,None)
    elif inst == "assert":
      arg_t,arg = tokens[0]
      if arg_t is not _TokenType.CHRSET:
        raise SyntaxError(f"Expected charset after assert on line {lnum}")
      return _instAssert(single,arg)
    elif inst == "select":
      # this is going to be the hardest one to write since it has the
      # "case" statement
      cases : dict = {}
      for slnum,((stmt_t,stmt),*stokens),sbody in body:
        if stmt_t is not _TokenType.WORD:
          raise SyntaxError(f"expected case on line {slnum}")
        if stmt != "case":
          raise SyntaxError(f"expected case on line {slnum} not {stmt!r}")
        (arg_t,arg) = stokens[0]
        if arg_t is not _TokenType.CHRSET:
          raise SyntaxError(f"expected charset after case on line {slnum}")
        cases[arg] = _parse_many(sbody)
      return _instSelect(single,cases)
    elif inst == "consume":
      return _instMove(single,False)
    elif inst == "omit":
      return _instMove(single,True)
    elif inst == "finish":
      return _instFinish(single)
    else:
      raise SyntaxError(f"Unrecognised instruction \"{inst}\" on line {lnum}")
    

  def _parse_many(many : tuple) -> tuple:
    "parses many lines" # hence the name
    return tuple(map(_parse_line,many))

  return _parse_many(chunks)

# Before we get to the interpreter, Here's a function to print "disassemble"
# the output from the parser into a reperisentation of the possible input
# string

def _disassemble(program : tuple) -> None:
  # this uses a technique of creating a list of lines and indent
  # changes before zipping them up into text and printing

  # Also uses nested function, impure nested function
  
  buffer : list = []

  def _dis_single(single):
    nonlocal buffer
    if isinstance(single,_instFinish):
      buffer.append("finish")
    elif isinstance(single,_instMove):
      buffer.append("omit" if single.drop else "consume")
    elif isinstance(single,_instStack):
      if single.pop:
        buffer.append("pop")
      else:
        buffer.append("push")
        buffer.append(1) # indent
        _dis_many(single.frame)
        buffer.append(-1) # dedent
    elif isinstance(single,_instAssert):
      buffer.append(f"assert ({single.charset})")
    elif isinstance(single,_instSelect):
      buffer.append("select")
      buffer.append(1)
      for case,body in single.cases.items():
        buffer.append(f"case ({case})")
        buffer.append(1)
        _dis_many(body)
        buffer.append(-1)
      buffer.append(-1)

  def _dis_many(many):
    for single in many: _dis_single(single)

  _dis_many(program)

  indwidth = len(str(len((*filter(lambda x:isinstance(x,str),buffer),)))) + 2
  
  current_indent : int = 0
  text : str = ""
  ln = 0
  for step in buffer:
    if isinstance(step,int):
      current_indent += step
    elif isinstance(step,str):
      ln += 1
      text += "%s | %s%s\n"%(str(ln).rjust(indwidth), "    " * current_indent, step)
  print(text)

@dataclass()
class _intrpFrame:
  """
This is used to help manage interpreting the program.
  """
  input_pointer       : 0
  output_pointer      : 0
  instruction_pointer : int
  instructions        : tuple

  def getInstruction(self) -> object:
    "gets the next instruction, or return None if instructions exhausted"
    if self.instruction_pointer == len(self.instructions):
      return None
    else:
      ret = self.instructions[self.instruction_pointer]
      self.instruction_pointer += 1
      return ret

class IASSERT(BaseException): pass
  
def _interpret(program : tuple, input_buffer : StringIO):
  """
Interprets the instruction stream produced by `_parse` and then returns the
output buffer.
  """
  if not isinstance(input_buffer,StringIO):
    raise TypeError("Expected StringIO but got %s instead" %\
                    repr(type(input_buffer)))

  # these two funtions handle interpreting without error
  def _exc_push(code : tuple):
    prev = exc_stack[-1]
    exc_stack.append(_intrpFrame(prev.input_pointer,prev.output_pointer,
                                 0,code))

  def _exc_pop():
    prev = exc_stack.pop()
    if not exc_stack:
      raise IASSERT
    exc_stack[-1].output_pointer = prev.output_pointer
    exc_stack[-1].input_pointer = prev.input_pointer
    input_buffer.seek(prev.input_pointer)

  # these two handles reading / writing to the buffers
  def _read():
    ret = input_buffer.read(1)
    exc_stack[-1].input_pointer = input_buffer.tell()
    return ret

  def _write(value):
    output_buffer.write(value)
    exc_stack[-1].output_pointer = output_buffer.tell()

  # this is for testing the 'front' of the input buffer
  def _peek():
    return input_buffer.getvalue()[input_buffer.tell()] if input_buffer.tell()\
           < len(input_buffer.getvalue()) else ""

  
  # this will be annotated and commented later
  with StringIO() as output_buffer:
    exc_stack : list = [_intrpFrame(input_buffer.tell(),0,0,program)]
    err_stack : list = []
    Running   : bool = True

    while Running:
      try:
        instr = exc_stack[-1].getInstruction()
        if instr == None:
          _exc_pop()
  ######
        elif isinstance(instr,_instMove):
          temp = _read()
          if not instr.drop:
            _write(temp)
        elif isinstance(instr,_instFinish):
          Running = False
        elif isinstance(instr,_instAssert):
          test = _peek()
          if test and test not in instr.charset:
            raise IASSERT
        elif isinstance(instr,_instStack):
          if instr.pop:
            err_stack.pop()
          else:
            err_stack.append((len(exc_stack),
                              _intrpFrame(exc_stack[-1].input_pointer,
                                          exc_stack[-1].output_pointer,
                                          0, instr.frame)))
        elif isinstance(instr,_instSelect):
          test = _peek()
          if not test:
            raise IASSERT
          for case,body in instr.cases.items():
            if test in case:
              _exc_push(body)
              break
          else:
            raise IASSERT
  ######
          
      except IASSERT as err:
        if err_stack:
          # this overwrites our progress back to the "push" instruction
          depth,frame = err_stack.pop()
          while len(exc_stack) >= depth:
            exc_stack.pop()
          exc_stack.append(frame)
          output_buffer.seek(frame.output_pointer)
          output_buffer.truncate()
          input_buffer.seek(frame.input_pointer)
        else:
          raise err
    return output_buffer.getvalue()

def parse(text):
  return _parse(_chunk(text))

def interp(prog,text):
  """
Runs the provided program on the text included until it has scanned
all of the text, or an error is encountered
  """
  source = StringIO(text)
  out = []
  try:
    while source.tell() < len(text):
      out.append(_interpret(prog,source))
  except IASSERT:
    pass
  return out
