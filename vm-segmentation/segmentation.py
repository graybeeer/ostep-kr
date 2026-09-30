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

def abort_if(condition, message):
    if condition:
        print('오류:', message)
        exit(1)
    return


#
# main program
#
parser = OptionParser()
parser.add_option("-s", "--seed", default=0, help='난수 시드 (같은 값으로 같은 문제 재현)', action="store", type="int", dest="seed")
parser.add_option("-A", "--addresses", default="-1", help='접근할 주소/페이지 번호 목록 (쉼표 구분, -1: 임의 생성)', action="store", type="string", dest="addresses")
parser.add_option("-a", "--asize", default="1k", help='가상 주소 공간 크기 (예: 16, 64k, 32m, 1g)', action="store", type="string", dest="asize")
parser.add_option("-p", "--physmem", default="16k", help='물리 메모리 크기 (예: 16, 64k, 32m, 1g)', action="store", type="string", dest="psize")
parser.add_option("-n", "--numaddrs", default=5, help='생성할 가상 주소 수', action="store", type="int", dest="num")
parser.add_option("-b", "--b0", default="-1", help='세그먼트 0의 베이스 레지스터 값', action="store", type="string", dest="base0")
parser.add_option("-l", "--l0", default="-1", help='세그먼트 0의 리미트 레지스터 값', action="store", type="string", dest="len0")
parser.add_option("-B", "--b1", default="-1", help='세그먼트 1의 베이스 레지스터 값', action="store", type="string", dest="base1")
parser.add_option("-L", "--l1", default="-1", help='세그먼트 1의 리미트 레지스터 값', action="store", type="string", dest="len1")
parser.add_option("-c", help='정답과 계산 결과 표시', action="store_true", default=False, dest="solve")

(options, args) = parser.parse_args()

print('설정 난수 시드 (seed)', options.seed)
print('설정 가상 주소 공간 크기 (address space size)', options.asize)
print('설정 물리 메모리 크기 (phys mem size)', options.psize)
print('')

random_seed(options.seed)
asize = convert(options.asize)
psize = convert(options.psize)
addresses = str(options.addresses)

abort_if(psize <= 4, '물리 메모리 크기를 더 크게 지정하세요')
abort_if(asize == 0, '주소 공간 크기는 0이 아니어야 합니다')
abort_if(psize <= asize, '이 시뮬레이터에서는 물리 메모리가 가상 주소 공간보다 커야 합니다')

#
# need to generate base, bounds for segment registers
#
len0 = convert(options.len0)
len1 = convert(options.len1)
base0 = convert(options.base0)
base1 = convert(options.base1)

# if randomly generating length, make it 1/4-1/2 the address space size (roughly)
if len0 == -1:
    len0 = int(asize/4.0 + (asize/4.0 * random.random()))
if len1 == -1:
    len1 = int(asize/4.0 + (asize/4.0 * random.random()))

if base0 == -1 or base1 == -1:
    # this restriction just makes it easier to place randomly-placed segments
    abort_if(psize <= 2 * asize, '베이스를 임의 생성할 때는 물리 메모리가 가상 주소 공간의 두 배보다 커야 합니다')

# if randomly generate base, have to find room for them
if base0 == -1:
    done = 0
    while done == 0:
        base0 = int(psize * random.random())
        if (base0 + len0) < psize:
            done = 1

# internally, base1 points to the lower address, and base1+len1 the higher address
# (this differs from what the user would pass in)
if base1 == -1:
    done = 0
    while done == 0:
        base1 = int(psize * random.random())
        if (base1 + len1) < psize:
            if (base1 > (base0 + len0)) or ((base1 + len1) < base0):
                done = 1
else:
    base1 = base1 - len1

abort_if(psize < base0 + len0 - 1, '세그먼트 0이 물리 메모리 범위를 벗어납니다')
abort_if(psize < base1, '세그먼트 1이 물리 메모리 범위를 벗어납니다')
    
abort_if(len0 > asize/2.0, '세그먼트 0 리미트가 주소 공간에 비해 너무 큽니다')
abort_if(len1 > asize/2.0, '세그먼트 1 리미트가 주소 공간에 비해 너무 큽니다')

print('세그먼트 레지스터 정보:')
print('')
print('  세그먼트 0 베이스 (높은 주소 방향 확장): 0x%08x (십진수 %d)' % (base0, base0))
print('  세그먼트 0 리미트                     : %d' % (len0))
print('')
print('  세그먼트 1 베이스 (낮은 주소 방향 확장): 0x%08x (십진수 %d)' % (base1+len1, base1+len1))
print('  세그먼트 1 리미트                     : %d' % (len1))
print('')

nbase1 = base1 + len1

abort_if((len0 + base0) > base1 and (base1 > base0), '물리 메모리에서 세그먼트가 겹칩니다')

addrList = []
if addresses == '-1':
    # need to generate addresses
    for i in range(0, options.num):
        n = int(asize * random.random())
        addrList.append(n)
else:
    addrList = addresses.split(',')

#
# now, need to generate virtual address trace
#
print('가상 주소 변환 목록')
i = 0
for vstr in addrList:
    vaddr = int(vstr)
    if vaddr < 0 or vaddr >= asize:
        print('오류: 가상 주소 %d은(는) 크기 %d의 주소 공간에서 생성할 수 없습니다' % (vaddr, asize))
        exit(1)
    if options.solve == False:
        print('  가상 주소 %2d: 0x%08x (십진수: %4d) --> 물리 주소는? 또는 범위 위반인가요?' % (i, vaddr, vaddr))
    else:
        paddr = 0
        if (vaddr >= (asize / 2)):
            # seg 1
            #  [base1+len1]  [negative offset]
            paddr = nbase1 + (vaddr - asize)
            if paddr < base1:
                print('  가상 주소 %2d: 0x%08x (십진수: %4d) --> 세그먼트 범위 위반 (SEG1)' % (i, vaddr, vaddr))
            else:
                print('  가상 주소 %2d: 0x%08x (십진수: %4d) --> SEG1의 유효한 물리 주소: 0x%08x (십진수: %4d)' % (i, vaddr, vaddr, paddr, paddr))
        else:
            # seg 0
            if (vaddr >= len0):
                print('  가상 주소 %2d: 0x%08x (십진수: %4d) --> 세그먼트 범위 위반 (SEG0)' % (i, vaddr, vaddr))
            else:
                paddr = vaddr + base0
                print('  가상 주소 %2d: 0x%08x (십진수: %4d) --> SEG0의 유효한 물리 주소: 0x%08x (십진수: %4d)' % (i, vaddr, vaddr, paddr, paddr))
    i += 1

print('')

if options.solve == False:
    print('각 가상 주소에 대해 변환된 물리 주소를 쓰거나,')
    print('허용 범위를 벗어났다면 세그먼트 범위 위반이라고 쓰세요.')
    print('이 문제에는 두 세그먼트가 있습니다. 가상 주소의')
    print('최상위 비트로 어느 세그먼트에 속하는지 구분합니다.')
    print('최상위 비트가 0이면 세그먼트 0, 1이면 세그먼트 1입니다.')
    print('베이스를 기준으로 확장하는 방향도 다릅니다. 세그먼트 0은')
    print('높은 주소 방향으로, 세그먼트 1은 낮은 주소 방향으로 확장합니다. ')
    print('')






# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 가상 주소의 최상위 비트가 0이면 세그먼트 0, 1이면 세그먼트 1입니다. 베이스와 리미트를 세그먼트별로 구분하세요.
  - 세그먼트 0은 높은 주소 방향으로 확장하며 물리 주소 = Base0 + VA입니다.
  - 세그먼트 1은 낮은 주소 방향으로 확장하며 물리 주소 = Base1 + (VA - 가상 주소 공간 크기)입니다. 출력된 Base1은 위쪽 경계입니다.
  - 변환 주소가 해당 세그먼트의 리미트 범위를 벗어나면 범위 위반입니다. 두 세그먼트 모두 같은 방향으로 더하면 안 됩니다.
""")
