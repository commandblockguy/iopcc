import sys                         ,                                                                                                                                 builtins
f                                  :                                                                                                                 0=sys._getframe().f_back
while'port'in f.f_code.co_filename :                                                                                                                               f=f.f_back
class P(str)                       :                                                                                                                                        #
 __neg__=__pos__=lambda s          :                                                                                                                                        s
 def     __add__(s,o)              :                                                                                                                    return[s]+[o]*bool(o)
 def    __radd__(o,s)              :                                                                                                                     return s+[o]*bool(o)
 def  __matmul__(s,o)              :                                                                                                                     return P(f'{s} {o}')
 def __truediv__(s,o)              :                                                                                                                     return P(f'{s}~{o}')
def o(i:(punched_cards:=P))        :                        c=i[3:].count(' ');p=i[3:].find(' ')+1;return p*(c>0)|[(i[2]<'!')*128,128,8][c]|((i[:3].find(' ')+(c<1))&3)<<4|64
def g(m:(d:=f.f_locals))           : print(eval(bytes(o(''.join(l))for c in m for l in zip(*c.split('~'))).decode('cp500').lower().replace(*'÷/'),{'__builtins__':builtins}))
d|=dict(DONE=P(),read=g)|{c*i      :                                                                                                P(c*i)for i in range(1, 81)for c in '_O'}
