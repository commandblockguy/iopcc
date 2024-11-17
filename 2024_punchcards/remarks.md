# Remarks

A tremendous amount of engineering effort has been put into dragging languages like C and JavaScript kicking and screaming into the 21st century.
For reasons I do not fully comprehend, substantially less work has been put into bringing more modern languages like Python into the past by a few decades.
With this submission, I hope to rectify this, and demonstrate a Python truly suited to the 1950s.

## Author
commandz (commandz@commandblockguy.xyz)

## Usage

e.g. `python main.py 0123456789`

### Arguments

`main.py` takes a single command-line argument. If no argument is provided, it defaults to ` 'transliterating' `.

### Compatibility

Requires Python version 3.12 or above.
Should not require any particular OS, external libraries, or platform-dependent APIs.
Tested on Python 3.12.4 on Arch Linux.

## Other Remarks

`generate.py` (the script which generates `main.py`) is provided for reference purposes, and is not part of the submission proper.
As such, it contains spoilers, including (but not limited to) 2-3 lines resembling actual documentation.

The syntax I used here imposed a fun set of restrictions on the payload.
In particular, I was prevented from using `for` and `lambda` and the characters `{}`, and restricted to only the following builtins:

- any
- iter
- max
- min
- vars
- int
- map
- set
- quit
- exit

I originally used the lookalike characters "OIᒿЗᏎ𑢻б𑣆𐌚Ꝯ" and the + operator, which eliminated that restriction, but it turns out that Ubuntu doesn't actually display those as fixed-width by default and it was completely unrecognizable.