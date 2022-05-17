
# tspi
 a fun little project where I wrote an interpreter for some pseudocode I was writing

### what is tspi

tspi, standing for `Token Scanner Pseudocode Interpreter` or "taspie" for short, Is an interpreter for some pseudocode I wrote when figuring out how to take a set of different tokens and compiling them into a set of instructions of how to get any of those tokens and only those tokens. Poor explaination, I Know.
It works on scanning being based on moving characters from one buffer to another buffer, selectively omitting some characters. It also achieves branching with assertions, error handling, and selection. tspi is a very simple language, it is pseudocode after all. Below is an example snippet;
```
; this script scans and caputeres the below sequences
;    note : characters in square brackets are caputered
;           and the ones outside are not
; [+-]
; [!-]
; [-+]
; [-+*]
; [+]e[-]
push
    switch
        case (+!)
            consume
            assert (-)
            consume
        case (-)
			consume
			assert (+)
			consume
			push
			assert (*)
			pop
			consume
	finish
assert (+)
consume
assert (e)
omit
assert (-)
consume
pop
finish
```
<sup>fig 1.1</sup>
As you can see, These programs are nice and readable. They're a tad on the verbose side but ultimately thats because it's one instruction per line and mostly just keywords. Infact, the only part of the program that isn't keywords is the character sets (the `()` with text between them). Why is this, because I hand wrote several tens of lines of this stuff by hand and it's easier to write than to draw.

###  more details

This language has a simple structure, There are no variables, but there are two buffers and a stack. You can read from the input buffer and write the value to the output buffer, or you can read from the input buffer and just drop the value (`consume` and `omit` respectively), and conditionals are done by changing the path of the program or by rolling back earlier into the program and running different code.
The whole rolling back the program happens on any error, If the error goes uncaught then the program is rolled back to before it started and an exception is raised. To catch an error you use the `push` statement to push the response to the next error onto the stack. When an error is caught then it's rolled back to the most recent `push` statement which then redifines what code will run then continues from that point. To handle error catching properly you will use the `pop` keyword to remove these error catching responses from the stack, this removes any unwanted error catching and allows some level of consistency in what is probably the messiest way of handling control.
Syntax wise, many keywords (push, pop, consume, omit, assert, select, case, finish) each does it's own thing. Each keyword is explained in the Python script in the comment block at the top. It is below this paragraph. As you probably saw in the snippet<sup>fig 1.1</sup> above, tspi Uses significant whitespace, and it's *too*  annoying. If a statement/instruction that is meant to have a body doesn't then it's treated as empty. You don't have to include `pass` like you would in python. Infact, in the snippet<sup>fig 1.1</sup> above you can see push being used as a bodyless statement, which is allowed, and makes dropping out of a body on an error really easy to do. Anway, below is the comment block explaining what each statement does.
```py
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
```
That warning at the end is important. Even if you write your own interpreter or modify a fork of this, Keep this in mind. If the program terminates due to running out of instructions, that's a sign you didn't quite scan the text properly.