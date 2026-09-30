#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
from optparse import OptionParser
import random
import math

# to make Python2 and Python3 act the same -- how dumb
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

def convert(size):
    length = len(size)
    lastchar = size[length-1]
    if (lastchar == 'k') or (lastchar == 'K'):
        m = 1024
        nsize = int(size[0:length-1]) * m
    elif (lastchar == 'm') or (lastchar == 'M'):
        m = 1024*1024
        nsize = int(size[0:length-1]) * m
    elif (lastchar == 'g') or (lastchar == 'G'):
        m = 1024*1024*1024
        nsize = int(size[0:length-1]) * m
    else:
        nsize = int(size)
    return nsize


#
# main program
#
parser = OptionParser()
parser.add_option('-s', '--seed',      default=0,     help='난수 시드 (같은 값으로 같은 문제 재현)',                                action='store', type='int', dest='seed')
parser.add_option('-a', '--asize',     default='1k',  help='가상 주소 공간 크기 (예: 16, 64k, 32m, 1g)',    action='store', type='string', dest='asize')
parser.add_option('-p', '--physmem',   default='16k', help='물리 메모리 크기 (예: 16, 64k, 32m, 1g)',  action='store', type='string', dest='psize')
parser.add_option('-n', '--addresses', default=5,     help='생성할 가상 주소 수',        action='store', type='int', dest='num')
parser.add_option('-b', '--b',         default='-1',  help='베이스 레지스터 값 (물리 시작 주소)',                         action='store', type='string', dest='base')
parser.add_option('-l', '--l',         default='-1',  help='리미트 레지스터 값 (허용 범위 크기)',                        action='store', type='string', dest='limit')
parser.add_option('-c', '--compute',   default=False, help='정답과 계산 결과 표시',                         action='store_true', dest='solve')


(options, args) = parser.parse_args()

print('')
print('설정 난수 시드 (seed)', options.seed)
print('설정 가상 주소 공간 크기 (address space size)', options.asize)
print('설정 물리 메모리 크기 (phys mem size)', options.psize)
print('')

random_seed(options.seed)
asize = convert(options.asize)
psize = convert(options.psize)

if psize <= 1:
    print('오류: 물리 메모리 크기는 1보다 커야 합니다.')
    exit(1)

if asize == 0:
    print('오류: 주소 공간 크기는 0이 아니어야 합니다.')
    exit(1)

if psize <= asize:
    print('오류: 이 시뮬레이터에서는 물리 메모리가 가상 주소 공간보다 커야 합니다')
    exit(1)

#
# need to generate base, bounds for segment registers
#
limit = convert(options.limit)
base  = convert(options.base)

if limit == -1:
    limit = int(asize/4.0 + (asize/4.0 * random.random()))

# now have to find room for them
if base == -1:
    done = 0
    while done == 0:
        base = int(psize * random.random())
        if (base + limit) < psize:
            done = 1

print('베이스/리미트 레지스터 정보:')
print('')
print('  베이스(Base): 0x%08x (십진수 %d)' % (base, base))
print('  리미트(Limit): %d' % (limit))
print('')

if base + limit > psize:
    print('오류: 지정한 베이스/리미트로는 주소 공간이 물리 메모리에 들어가지 않습니다.')
    print('베이스 + 리미트:', base + limit, '  물리 메모리 크기:', psize)
    exit(1)

#
# now, need to generate virtual address trace
#
print('가상 주소 변환 목록')
for i in range(0,options.num):
    vaddr = int(asize * random.random())
    if options.solve == False:
        print('  가상 주소 %2d: 0x%08x (십진수: %4d) --> 물리 주소는? 또는 범위 위반인가요?' % (i, vaddr, vaddr))
    else:
        paddr = 0
        if (vaddr >= limit):
            print('  가상 주소 %2d: 0x%08x (십진수: %4d) --> 세그먼트 범위 위반' % (i, vaddr, vaddr))
        else:
            paddr = vaddr + base
            print('  가상 주소 %2d: 0x%08x (십진수: %4d) --> 유효한 물리 주소: 0x%08x (십진수: %4d)' % (i, vaddr, vaddr, paddr, paddr))

print('')

if options.solve == False:
    print('각 가상 주소에 대해 변환된 물리 주소를 쓰거나,')
    print('허용 범위를 벗어났다면 세그먼트 범위 위반이라고 쓰세요.')
    print('이 문제에서는 주어진 크기의 단순한 가상 주소 공간을 가정합니다.')
    print('')






# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 가상 주소(VA)는 프로세스가 사용하는 주소, 물리 주소(PA)는 실제 메모리 위치입니다.
  - 베이스(Base)는 물리 시작 주소, 리미트(Limit)는 허용 범위의 크기입니다. VA < Limit이면 PA = Base + VA, 아니면 범위 위반입니다.
  - 리미트는 마지막 물리 주소가 아닙니다. 0x 표기는 16진수이고 괄호 안 십진수는 같은 값입니다.
""")
