#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
from optparse import OptionParser
import random
import math

def mustbepowerof2(bits, size, msg):
    if math.pow(2,bits) != size:
        print('실행 옵션 오류: %s' % msg)
        sys.exit(1)

def mustbemultipleof(bignum, num, msg):
    if (int(float(bignum)/float(num)) != (int(bignum) / int(num))):
        print('실행 옵션 오류: %s' % msg)
        sys.exit(1)

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
parser.add_option('-A', '--addresses', default='-1',
                  help='접근할 주소/페이지 번호 목록 (쉼표 구분, -1: 임의 생성)',
                  action='store', type='string', dest='addresses')
parser.add_option('-s', '--seed',    default=0,     help='난수 시드 (같은 값으로 같은 문제 재현)',                               action='store', type='int', dest='seed')
parser.add_option('-a', '--asize',   default='16k', help='가상 주소 공간 크기 (예: 16, 64k, 32m, 1g)',   action='store', type='string', dest='asize')
parser.add_option('-p', '--physmem', default='64k', help='물리 메모리 크기 (예: 16, 64k, 32m, 1g)', action='store', type='string', dest='psize')
parser.add_option('-P', '--pagesize', default='4k', help='페이지 크기 (예: 4k, 8k)',            action='store', type='string', dest='pagesize')
parser.add_option('-n', '--numaddrs',  default=5,  help='생성할 가상 주소 수',       action='store', type='int', dest='num')
parser.add_option('-u', '--used',       default=50, help='사용 중인 가상 주소 공간의 비율 (백분율)', action='store', type='int', dest='used')
parser.add_option('-v',                             help='상세 정보 표시',                                  action='store_true', default=False, dest='verbose')
parser.add_option('-c',                             help='정답과 계산 결과 표시',                        action='store_true', default=False, dest='solve')


(options, args) = parser.parse_args()

print('설정 난수 시드 (seed)',               options.seed)
print('설정 가상 주소 공간 크기 (address space size)', options.asize)
print('설정 물리 메모리 크기 (phys mem size)',      options.psize)
print('설정 페이지 크기 (page size)',          options.pagesize)
print('설정 상세 정보 표시 (verbose)',            options.verbose)
print('설정 주소/페이지 목록 (addresses)',          options.addresses)
print('')

random.seed(options.seed)

asize    = convert(options.asize)
psize    = convert(options.psize)
pagesize = convert(options.pagesize)
addresses = str(options.addresses)

if psize <= 1:
    print('오류: 물리 메모리 크기는 1보다 커야 합니다.')
    exit(1)

if asize < 1:
    print('오류: 주소 공간 크기는 0이 아니어야 합니다.')
    exit(1)

if psize <= asize:
    print('오류: 이 시뮬레이터에서는 물리 메모리가 가상 주소 공간보다 커야 합니다')
    exit(1)

if psize >= convert('1g') or asize >= convert('1g'):
    print('오류: 이 시뮬레이터에서는 1 GB보다 작은 크기를 사용하세요.')
    exit(1)

mustbemultipleof(asize, pagesize, 'address space must be a multiple of the pagesize')
mustbemultipleof(psize, pagesize, 'physical memory must be a multiple of the pagesize')

# print some useful info, like the darn page table 
pages = int(psize / pagesize);
import array
used = array.array('i')
pt   = array.array('i')
for i in range(0,pages):
    used.insert(i,0)
vpages = int(asize / pagesize)

# now, assign some pages of the VA
vabits   = int(math.log(float(asize))/math.log(2.0))
mustbepowerof2(vabits, asize, 'address space must be a power of 2')
pagebits = int(math.log(float(pagesize))/math.log(2.0))
mustbepowerof2(pagebits, pagesize, 'page size must be a power of 2')
vpnbits  = vabits - pagebits
pagemask = (1 << pagebits) - 1

# import ctypes
# vpnmask  = ctypes.c_uint32(~pagemask).value
vpnmask = 0xFFFFFFFF & ~pagemask
#if vpnmask2 != vpnmask:
#    print 'ERROR'
#    exit(1)
# print 'va:%d page:%d vpn:%d -- %08x %08x' % (vabits, pagebits, vpnbits, vpnmask, pagemask)

print('')
print('페이지 테이블 항목을 읽는 방법:')
print('가장 왼쪽의 최상위 비트는 유효(VALID) 비트입니다.')
print('  이 비트가 1이면 나머지 비트는 물리 페이지 프레임 번호(PFN)입니다.')
print('  이 비트가 0이면 유효하지 않은 페이지입니다.')
print('각 항목의 가상 페이지 번호(VPN)도 보려면')
print('상세 모드(-v)를 사용하세요.')
print('')

print('페이지 테이블 (0번 항목부터 순서대로)')
for v in range(0,vpages):
    done = 0
    while done == 0:
        if ((random.random() * 100.0) > (100.0 - float(options.used))):
            u = int(pages * random.random())
            if used[u] == 0:
                used[u] = 1
                done = 1
                # print('%8d - %d' % (v, u))
                if options.verbose == True:
                    print('  [%8d]  ' % v, end='')
                else:
                    print('  ', end='')
                print('0x%08x' % (0x80000000 | u))
                pt.insert(v,u)
        else:
            # print('%8d - not valid' % v)
            if options.verbose == True:
                print('  [%8d]  ' % v, end='')
            else:
                print('  ', end='')
            print('0x%08x' % 0)
            pt.insert(v,-1)
            done = 1
print(''            )


#
# now, need to generate virtual address trace
#

addrList = []
if addresses == '-1':
    # need to generate addresses
    for i in range(0, options.num):
        n = int(asize * random.random())
        addrList.append(n)
else:
    addrList = addresses.split(',')


print('가상 주소 변환 목록')
for vStr in addrList:
    # vaddr = int(asize * random.random())
    vaddr = int(vStr)
    if options.solve == False:
        print('  가상 주소 0x%08x (십진수: %8d) --> 물리 주소는? 또는 유효하지 않은 주소인가요?' % (vaddr, vaddr))
    else:
        paddr = 0
        # split vaddr into VPN | offset
        vpn = (vaddr & vpnmask) >> pagebits
        if pt[vpn] < 0:
            print('  가상 주소 0x%08x (십진수: %8d) --> 유효하지 않음 (VPN %d이(가) 무효)' % (vaddr, vaddr, vpn))
        else:
            pfn    = pt[vpn]
            offset = vaddr & pagemask
            paddr  = (pfn << pagebits) | offset
            print('  가상 주소 0x%08x (십진수: %8d) --> 물리 주소 %08x (십진수 %8d) [VPN %d]' % (vaddr, vaddr, paddr, paddr, vpn))
print('')

if options.solve == False:
    print('각 가상 주소가 변환되는 물리 주소를 쓰세요.')
    print('유효하지 않은 주소라면 주소 오류(예: segfault)라고 쓰세요.')
    print('')








# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - VPN은 가상 페이지 번호, PFN은 물리 페이지 프레임 번호입니다. 가상 주소를 페이지 번호와 페이지 내부 오프셋으로 나누세요.
  - 유효 비트가 1일 때 물리 주소 = PFN × 페이지 크기 + 오프셋입니다. 주소 변환 전후에 페이지 내부 오프셋은 같습니다.
  - 유효 비트가 0이면 이 문제에서는 유효하지 않은 가상 페이지입니다. 자동으로 디스크에서 읽어 온다고 가정하지 마세요.
""")
