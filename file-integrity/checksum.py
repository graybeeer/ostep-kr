#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import random
from optparse import OptionParser

# to make Python2 and Python3 act the same -- how dumb
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

def print_hex(v):
    if v < 16:
        return '0x0%x' % v
    else:
        return '0x%x' % v
    
def print_bin(word):
    v = bin(word)
    o = '0b'
    o += ('0' * (10 - len(str(v))))
    o += str(v)[2:]
    return o
    

parser = OptionParser()
parser.add_option('-s', '--seed', default='0', help='난수 시드 (같은 값으로 같은 문제 재현)', action='store', type='int', dest='seed')
parser.add_option('-d', '--data_size', default='4', help='데이터의 바이트 수', action='store', type='int', dest='data_size')
parser.add_option('-D', '--data', default='', help='쉼표로 구분한 데이터 값', action='store', type='string', dest='data')
parser.add_option('-c', '--compute', help='정답과 계산 결과 표시', action='store_true', default=False, dest='solve')
(options, args) = parser.parse_args()

print('')
print('설정 난수 시드 (seed)', options.seed)
print('설정 데이터 바이트 수 (data_size)', options.data_size)
print('설정 데이터 (data)', options.data)
print('')

random_seed(options.seed)

values = []
if options.data != '':
    tmp = options.data.split(',')
    for t in tmp:
        values.append(int(t))
else:
    for t in range(int(options.data_size)):
        values.append(int(random.random() * 256))


add = 0
xor = 0
fletcher_a, fletcher_b = 0, 0

for value in values:
    add = (add + value) % 256
    xor = xor ^ value
    fletcher_a = (fletcher_a + value) % 255
    fletcher_b = (fletcher_b + fletcher_a) % 255

print('십진수:   ', end=' ')
for word in values:
    print('%10s' % str(word), end=' ')
print('')

print('16진수:   ', end=' ')
for word in values:
    print('     ', print_hex(word), end=' ')
print('')

print('이진수:   ', end=' ')
for word in values:
    print(print_bin(word), end=' ')
print('')

print('')
if options.solve:
    print('덧셈 체크섬:    ', '%3d      ' % add, '(%s)' % print_bin(add))
    print('XOR 체크섬:     ', '%3d      ' % xor, '(%s)' % print_bin(xor))
    print('Fletcher(a,b): ', '%3d,%3d  ' % (fletcher_a, fletcher_b), '(%s,%s)' % (print_bin(fletcher_a), print_bin(fletcher_b)))
else:
    print('덧셈 체크섬: ?')
    print('XOR 체크섬: ?')
    print('Fletcher 체크섬: ?')
print('')
    



# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 각 열은 같은 바이트를 십진수·16진수·이진수로 나타낸 것입니다. 표기만 다르고 값은 같습니다.
  - 덧셈 체크섬은 합을 256으로 나눈 나머지, XOR 체크섬은 바이트들의 비트별 XOR입니다.
  - Fletcher의 a는 바이트 누적합, b는 a의 누적합이며 각각 255로 나눈 나머지를 사용합니다. 데이터 변경과 순서 변경을 각각 얼마나 잘 검출하는지 보세요.
  - 체크섬이 같아도 데이터가 반드시 같다는 뜻은 아닙니다. 서로 다른 데이터가 같은 체크섬을 만들 수 있습니다.
""")
