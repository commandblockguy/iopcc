# HERE BE SPOILERS
# peruse at your own risk

import sys
import random
import ast
import io
import re
from itertools import pairwise
from ast import *
import inspect
from collections import Counter
import string
import tokenize

def punches(ebdic):
  result = 0
  num = ebdic & 0b1111
  if num > 9:
    num &= 0b111
    result |= 1 << 10
  if num:
    result |= 1 << (num + 2)
  zone = ((ebdic-1) >> 4) & 0b11
  if zone < 3:
    result |= 1 << zone
  return result

# def punches(c):
  #return ((c&15 > 9)*1024) | ((c&15 > 0) << ((c&15 - 8*(c&15>9)) + 2)) | ((((c-1) >> 4) & 3 < 3) << (((c-1) >> 4) & 3))
  # return (1024 * (9 < nums)) | ((0 < nums) << (2 + (-8*(9<nums) + nums))) | ((3 > zones) << zones)

def has_consecutive_punches(s):
  return any(bool(punches(a) & punches(b)) for a, b in pairwise(s.upper().encode('cp500')))

def gen_card(data):
  return '\n'.join(
    [
      '   +' + '-' * 81 + '+',
      *('  ' + ('/' if i else '+') + ' ' + ''.join('@' if (punches(c) >> i) & 1 else n for c in data.ljust(80).encode('cp500')) + ' \\' for i, n in enumerate('__O123456789')),
      '  +' + '-' * 82 + '+'
    ]
  )

# with open('/usr/share/dict/words') as f:
#   print(max([word[:-1] for word in f.readlines() if not has_consecutive_punches(f"'{word[:-1]}'")], key=len))

# payload function
# this is parsed and then rewritten in a form that fits on a punchcards without two consecutive binary operators
def gen_punchcard():
  from itertools import starmap, chain, cycle, repeat, batched
  from functools import partial
  from operator import and_, or_, mul, lt, lshift, add, gt, eq, getitem
  import sys
  # longest english word that does not cause a paper jam when reimported, fun coincidence
  data = (sys.argv + [" 'transliterating' "])[1]
  ebdic_bytes=data.ljust(int((len(data)-1)/80)*80+80).encode('cp500')
  zones=list(map(partial(and_, 3), map(int, map(partial(mul, 1/16), map(partial(add, -1), ebdic_bytes)))))
  nums=list(map(partial(and_, 15), ebdic_bytes))
  punchmasks=starmap(or_, zip(
    map(partial(mul, 1024),
      map(partial(lt, 9), nums)),
    starmap(or_, zip(
      starmap(lshift, zip(
        map(partial(lt, 0), nums),
        map(partial(add, 2),
          starmap(add, zip(
            map(partial(mul, -8), map(partial(lt, 9), nums)),
            nums
          ))
        )
      )),
      starmap(lshift, zip(
        map(partial(gt, 3), zones),
        zones
      ))
    ))
  ))
  format_string = chr(123)+':012b'+chr(125)
  punches=map(partial(map, partial(eq, '1')), map(reversed, map(format_string.format, punchmasks)))
  flat_punches=chain.from_iterable(punches)
  maps=cycle(map(list, cycle(zip(chain(*('_'*2),'o'.upper(),map(str, range(1,10))), repeat('@')))))
  cells=starmap(getitem, zip(maps, flat_punches))
  card_cols = batched(batched(cells, 12), 80)
  backslash = chr(92)
  newline = chr(10)
  card_rows = map(partial(map, str().join), starmap(zip, card_cols))

  return (' '+backslash+newline+'  +'+'-'*82+'+'+newline*2+'   +'+'-'*81+'+'+newline+'  + ').join([str(), *map((' '+backslash+newline+'  / ').join, card_rows), str()])[91:-93]

def desugar_imports(statements):
  """
  Rewrites a sequence of statements to use __import__ and assignments rather than import statements
  """
  for statement in statements:
    match statement:
      case Import(names):
        for alias in names:
          call = Call(func=Name(id='__import__', ctx=Load()), args=[Constant(value=alias.name)], keywords=[])
          yield Assign(targets=[Name(id=alias.asname or alias.name, ctx=Store())], value=call)
      case ImportFrom(module, names, _):
        call = Call(func=Name(id='__import__', ctx=Load()), args=[Constant(value=module)], keywords=[])
        yield Assign(targets=[Name(id=module, ctx=Store())], value=call)
        for alias in names:
          yield Assign(targets=[Name(id=alias.asname or alias.name, ctx=Store())], value=Attribute(value=Name(id=module, ctx=Load()), attr=alias.name, ctx=Load()))
      case _:
        yield statement

# function prepended to the payload prior to parsing it
def preamble():
  builtins=vars(vars()['__builtins__'])
  dict=vars(vars()['__builtins__'])['dict']
  update_vars=vars(vars()['__builtins__'])['getattr'](vars(),'update')

def get_statements(func):
  source = inspect.getsource(func)
  return ast.parse(source).body[0].body

def get_dependencies(statements):
  dependencies = {}

  class Visitor(NodeVisitor):
    def __init__(self, result):
      self.result = result

    def visit_Name(self, node):
      if node.id not in dir(__builtins__):
        self.result.add(node.id)

  for stmt in statements[:-1]:
    s = set()

    dependencies[stmt.targets[0].id] = s
    Visitor(s).visit(stmt.value)

  return dependencies

def get_used(statements):
  return {node.id for stmt in statements for node in walk(stmt) if isinstance(node, Name) and isinstance(node.ctx, Load)}

def inline(var, statements):
  try:
    stmt = next(s for s in statements if isinstance(s, Assign) and s.targets[0].id == var)
  except StopIteration:
    return statements

  statements = [s for s in statements if s != stmt]

  class Inliner(NodeTransformer):
    def visit_Name(self, node):
      if node.id == var:
        return stmt.value
      return node

  return [Inliner().visit(s) for s in statements]


def inline_single_use_vars(statements):
  use_counts = Counter(node.id for stmt in statements for node in walk(stmt) if isinstance(node, Name) and isinstance(node.ctx, Load))
  single_use = {name for name, count in use_counts.items() if count == 1}
  for var in single_use:
    statements = inline(var, statements)
  return statements

def valid_names():
  yield from string.ascii_lowercase
  for rest in valid_names():
    for last in string.ascii_lowercase:
      r = rest + last
      if not has_consecutive_punches(r[:2]):
        yield r

def rename_vars(statements):
  mappings = {}
  l = iter(valid_names())

  class Renamer(NodeTransformer):
    def visit_Name(self, node):
      if not has_consecutive_punches(node.id):
        return node
      if node.id not in mappings:
        mappings[node.id] = next(l)
      return Name(id=mappings[node.id], ctx=node.ctx)


  return [Renamer().visit(s) for s in statements], mappings

def convert_attrs(statements):
  class Deattrr(NodeTransformer):
    def visit_Attribute(self, node):
      if not has_consecutive_punches(node.attr):
        return node
      return Call(func=Name(id='getattr', ctx=Load()), args=[self.visit(node.value), Constant(value=node.attr)], keywords=[])

  return [Deattrr().visit(s) for s in statements]

def get_depths(statements):
  dependencies = get_dependencies(statements)
  depths = {}

  def get_depth(x):
    if x in depths:
      return depths[x]
    result = max(map(get_depth, dependencies[x]), default=-1)+1
    depths[x] = result
    return result

  for var in dependencies:
    get_depth(var)

  return depths

def rewrite_assignments(statements, mappings):
  depths = get_depths(statements)
  groups = [[x for x, d in depths.items() if d == i] for i in range(max(depths.values())+1)]

  definitions = {s.targets[0].id: s.value for s in statements if isinstance(s, Assign)}

  update_vars_raw = definitions[mappings['update_vars']]
  update_vars_name = Name(id=mappings['update_vars'], ctx=Load())

  dict_raw = definitions[mappings['dict']]
  dict_name = Name(id=mappings['dict'], ctx=Load())

  def assign(func, dict_func, g):
    d = Call(func=dict_func, args=[], keywords=[keyword(arg=x, value=definitions[x]) for x in g])
    return Call(func=func, args=[d], keywords=[])

  return [assign(update_vars_raw, dict_raw, groups[0])] + [assign(update_vars_name, dict_name, g) for g in groups[1:]] + statements[-1:]

def tupleize(statements):
  t = Tuple(elts=statements[:-1]+[statements[-1].value], ctx=Load())
  return Subscript(value=t, slice=Constant(value=-1), ctx=Load())

def fix_strings(statement):
  # todo: fix empty string
  class StrFixer(NodeTransformer):
    def visit_Constant(self, node):
      if not isinstance(node.value, str):
        return node
      if not has_consecutive_punches(unparse(node)):
        return node
      # todo: remove leading/trailing space if possible?
      interleaved = ' ' + ' '.join(node.value) + ' '
      c = Constant(value=interleaved)
      assert not has_consecutive_punches(unparse(c)), unparse(c)
      s = Slice(lower=Constant(value=1), step=Constant(value=2))
      return Subscript(value=c, slice=s, ctx=Load())
  return StrFixer().visit(statement)

def split_cards(stmt):
  current_card = ' '
  for _, s, *_ in tokenize.generate_tokens(io.StringIO(unparse(stmt)).readline):
    if not s:
      # ?????
      continue
    assert len(s) < 78
    new_card = current_card+(' ' if has_consecutive_punches(current_card[-1]+s[0]) else '')+s
    if len(new_card) > 79:
      assert not has_consecutive_punches(current_card), current_card
      yield current_card.ljust(80)
      current_card = ' ' + s
    else:
      current_card = new_card
  yield current_card.ljust(80)


def gen_payload(func):
  statements = get_statements(preamble) + get_statements(func)
  statements = [*desugar_imports(statements)]

  assert all(isinstance(x, Assign) for x in statements[:-1])
  assert isinstance(statements[-1], Return)

  statements = convert_attrs(statements)
  defined = {s.targets[0].id for s in statements if isinstance(s, Assign)}

  used_builtins = get_used(statements) - defined
  builtins_to_rename = {b for b in used_builtins if has_consecutive_punches(b)}

  for builtin in builtins_to_rename:
    statements.insert(1, parse(f'{builtin} = builtins["{builtin}"]', mode='exec').body[0])

  targets = [s.targets[0].id for s in statements[:-1]]
  assert len(targets) == len(set(targets))

  statements = inline_single_use_vars(statements)
  statements, mappings = rename_vars(statements)
  statements = rewrite_assignments(statements, mappings)

  statement = tupleize(statements)
  statement = fix_strings(statement)

  fix_missing_locations(statement)

  cards = split_cards(statement)
  
  return '\n\n'.join(map(gen_card, cards))

sys.argv = [None, ' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ&[.<(+!-]$*);^/ ,%_>?:#@\'="']
cards = gen_punchcard()

assert (
  cards ==
"""   +---------------------------------------------------------------------------------+
  + ___________@@@@@@@@@_________________@@@@@@@____________________________________ \\
  / ____________________@@@@@@@@@_______________@@@@@@@_____________________________ \\
  / O@OOOOOOOOOOOOOOOOOOOOOOOOOOO@@@@@@@@OOOOOOOOOOOOOO@O@@@@@OOOOOOOOOOOOOOOOOOOOOO \\
  / 11@11111111@11111111@111111111111111111111111111111@1111111111111111111111111111 \\
  / 222@22222222@22222222@2222222@22222222@222222@222222222222@222222222222222222222 \\
  / 3333@33333333@33333333@3333333@33333333@333333@333333@33333@33333333333333333333 \\
  / 44444@44444444@44444444@4444444@44444444@444444@444444@44444@4444444444444444444 \\
  / 555555@55555555@55555555@5555555@55555555@555555@555555@55555@555555555555555555 \\
  / 6666666@66666666@66666666@6666666@66666666@666666@666666@66666@66666666666666666 \\
  / 77777777@77777777@77777777@7777777@77777777@777777@777777@77777@7777777777777777 \\
  / 888888888@88888888@88888888@8888888@88@@@@@@8@@@@@@88@@@@@@@@@@@8888888888888888 \\
  / 9999999999@99999999@99999999@9999999@9999999999999999999999999999999999999999999 \\
  +----------------------------------------------------------------------------------+"""
), '\n' + cards

# cards = run_payload(payload)
# print(cards)
# ast.parse(f'(\n  {cards}\n  END\n)')

# import keyword
# for builtin in __builtins__.__dict__: # [*__builtins__.__dict__, *keyword.kwlist]:
#  if builtin != builtin.lower(): continue
#  card = gen_card(f' {builtin} ')
#  try:
#    ast.parse(f'(\n  {card}\n  END\n)')
#    assert not has_consecutive_punches(builtin), builtin+card
#    print(builtin)
#  except SyntaxError:
#   assert has_consecutive_punches(builtin), builtin+card

# for builtin in [*valid_builtins, False, True, ' ', set(), (), {}, 0]:
#   for attr in dir(builtin):
#     if not has_consecutive_punches(attr):
#       print(builtin, '.', attr)

with open('main.py', 'w') as f:
  f.write(f"from __past__ import punched_cards\n\nread(\n{gen_payload(gen_punchcard)}\n\n  DONE\n)\n")
