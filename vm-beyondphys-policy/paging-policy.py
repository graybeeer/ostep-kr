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

def hfunc(index):
    if index == -1:
        return 'MISS'
    else:
        return 'HIT '

def vfunc(victim):
    if victim == -1:
        return '-'
    else:
        return str(victim)

#
# main program
#
parser = OptionParser()
parser.add_option('-a', '--addresses', default='-1',   help='접근할 주소/페이지 번호 목록 (쉼표 구분, -1: 임의 생성)',  action='store', type='string', dest='addresses')
parser.add_option('-f', '--addressfile', default='',   help='접근할 주소 목록을 담은 파일',                                action='store', type='string', dest='addressfile')
parser.add_option('-n', '--numaddrs', default='10',    help='-a (--addresses)가 -1일 때 생성할 주소 수',    action='store', type='string', dest='numaddrs')
parser.add_option('-p', '--policy', default='FIFO',    help='페이지 교체 정책: FIFO, LRU, OPT, UNOPT, RAND, CLOCK',                action='store', type='string', dest='policy')
parser.add_option('-b', '--clockbits', default=2,      help='CLOCK 정책의 참조 카운터 최댓값',                          action='store', type='int', dest='clockbits')
parser.add_option('-C', '--cachesize', default='3',    help='페이지 캐시 용량 (페이지 수)',                                      action='store', type='string', dest='cachesize')
parser.add_option('-m', '--maxpage', default='10',     help='임의 생성 시 페이지 번호의 상한 (이 값은 제외)',     action='store', type='string', dest='maxpage')
parser.add_option('-s', '--seed', default='0',         help='난수 시드 (같은 값으로 같은 문제 재현)',                                                    action='store', type='string', dest='seed')
parser.add_option('-N', '--notrace', default=False,    help='상세 실행 흐름 생략',                                     action='store_true', dest='notrace')
parser.add_option('-c', '--compute', default=False,    help='정답과 계산 결과 표시',                                                action='store_true', dest='solve')

(options, args) = parser.parse_args()

print('설정 주소/페이지 목록 (addresses)', options.addresses)
print('설정 주소 목록 파일 (addressfile)', options.addressfile)
print('설정 주소 수 (numaddrs)', options.numaddrs)
print('설정 정책 (policy)', options.policy)
print('설정 CLOCK 참조 카운터 한도 (clockbits)', options.clockbits)
print('설정 캐시 페이지 수 (cachesize)', options.cachesize)
print('설정 페이지 번호 상한 (maxpage)', options.maxpage)
print('설정 난수 시드 (seed)', options.seed)
print('설정 상세 흐름 생략 (notrace)', options.notrace)
print('')

addresses   = str(options.addresses)
addressFile = str(options.addressfile)
numaddrs    = int(options.numaddrs)
cachesize   = int(options.cachesize)
seed        = int(options.seed)
maxpage     = int(options.maxpage)
policy      = str(options.policy)
notrace     = options.notrace
clockbits   = int(options.clockbits)

random_seed(seed)

addrList = []
if addressFile != '':
    fd = open(addressFile)
    for line in fd:
        addrList.append(int(line))
    fd.close()
else:
    if addresses == '-1':
        # need to generate addresses
        for i in range(0,numaddrs):
            n = int(maxpage * random.random())
            addrList.append(n)
    else:
        addrList = addresses.split(',')

if options.solve == False:
    print('페이지 교체 정책이 %s이고 캐시 용량이 %d페이지일 때,' % (policy, cachesize))
    print('각 페이지 접근이 캐시에 적중하는지 실패하는지')
    print('판단하세요.\n')

    for n in addrList:
        print('접근: %d  적중/실패?  메모리 상태는?' % int(n))
    print('')

else:
    if notrace == False:
        print('정답 계산 중...\n')

    # init memory structure
    count = 0
    memory = []
    hits = 0
    miss = 0

    if policy == 'FIFO':
        leftStr = 'FirstIn'
        riteStr = 'Lastin '
    elif policy == 'LRU':
        leftStr = 'LRU'
        riteStr = 'MRU'
    elif policy == 'MRU':
        leftStr = 'LRU'
        riteStr = 'MRU'
    elif policy == 'OPT' or policy == 'RAND' or policy == 'UNOPT' or policy == 'CLOCK':
        leftStr = 'Left '
        riteStr = 'Right'
    else:
        print('정책 %s은(는) 구현되지 않았습니다' % policy)
        exit(1)

    # track reference bits for clock
    ref   = {}

    cdebug = False

    # need to generate addresses
    addrIndex = 0
    for nStr in addrList:
        # first, lookup
        n = int(nStr)
        try:
            idx = memory.index(n)
            hits = hits + 1
            if policy == 'LRU' or policy == 'MRU':
                update = memory.remove(n)
                memory.append(n) # puts it on MRU side
        except:
            idx = -1
            miss = miss + 1

        victim = -1        
        if idx == -1:
            # miss, replace?
            # print('BUG count, cachesize:', count, cachesize)
            if count == cachesize:
                # must replace
                if policy == 'FIFO' or policy == 'LRU':
                    victim = memory.pop(0)
                elif policy == 'MRU':
                    victim = memory.pop(count-1)
                elif policy == 'RAND':
                    victim = memory.pop(int(random.random() * count))
                elif policy == 'CLOCK':
                    if cdebug:
                        print('참조할 페이지', n)
                        print('메모리 ', memory)
                        print('참조 카운터 (변경 전)', ref)

                    # hack: for now, do random
                    # victim = memory.pop(int(random.random() * count))
                    victim = -1
                    while victim == -1:
                        page = memory[int(random.random() * count)]
                        if cdebug:
                            print('  검사할 페이지:', page, ref[page])
                        if ref[page] >= 1:
                            ref[page] -= 1
                        else:
                            # this is our victim
                            victim = page
                            memory.remove(page)
                            break

                    # remove old page's ref count
                    if page in memory:
                        assert('BROKEN')
                    del ref[victim]
                    if cdebug:
                        print('교체 대상', page)
                        print('길이', len(memory))
                        print('메모리', memory)
                        print('참조 카운터 (변경 후)', ref)

                elif policy == 'OPT':
                    maxReplace  = -1
                    replaceIdx  = -1
                    replacePage = -1
                    # print('OPT: access %d, memory %s' % (n, memory) )
                    # print('OPT: replace from FUTURE (%s)' % addrList[addrIndex+1:])
                    for pageIndex in range(0,count):
                        page = memory[pageIndex]
                        # now, have page 'page' at index 'pageIndex' in memory
                        whenReferenced = len(addrList)
                        # whenReferenced tells us when, in the future, this was referenced
                        for futureIdx in range(addrIndex+1,len(addrList)):
                            futurePage = int(addrList[futureIdx])
                            if page == futurePage:
                                whenReferenced = futureIdx
                                break
                        # print('OPT: page %d is referenced at %d' % (page, whenReferenced))
                        if whenReferenced >= maxReplace:
                            # print('OPT: ??? updating maxReplace (%d %d %d)' % (replaceIdx, replacePage, maxReplace))
                            replaceIdx  = pageIndex
                            replacePage = page
                            maxReplace  = whenReferenced
                            # print('OPT: --> updating maxReplace (%d %d %d)' % (replaceIdx, replacePage, maxReplace))
                    victim = memory.pop(replaceIdx)
                    # print('OPT: replacing page %d (idx:%d) because I saw it in future at %d' % (victim, replaceIdx, whenReferenced))
                elif policy == 'UNOPT':
                    minReplace  = len(addrList) + 1
                    replaceIdx  = -1
                    replacePage = -1
                    for pageIndex in range(0,count):
                        page = memory[pageIndex]
                        # now, have page 'page' at index 'pageIndex' in memory
                        whenReferenced = len(addrList)
                        # whenReferenced tells us when, in the future, this was referenced
                        for futureIdx in range(addrIndex+1,len(addrList)):
                            futurePage = int(addrList[futureIdx])
                            if page == futurePage:
                                whenReferenced = futureIdx
                                break
                        if whenReferenced < minReplace:
                            replaceIdx  = pageIndex
                            replacePage = page
                            minReplace  = whenReferenced
                    victim = memory.pop(replaceIdx)
            else:
                # miss, but no replacement needed (cache not full)
                victim = -1
                count = count + 1

            # now add to memory
            memory.append(n)
            if cdebug:
                print('길이 (변경 후)', len(memory))
            if victim != -1:
                assert(victim not in memory)

        # after miss processing, update reference bit
        if n not in ref:
            ref[n] = 1
        else:
            ref[n] += 1
            if ref[n] > clockbits:
                ref[n] = clockbits
        
        if cdebug:
            print('참조 카운터 (변경 후)', ref)

        if notrace == False:
            print('접근: %d  %s %s -> %12s <- %s 교체된 페이지:%s [적중:%d 실패:%d]' % (n, hfunc(idx), leftStr, memory, riteStr, vfunc(victim), hits, miss))
        addrIndex = addrIndex + 1
        
    print('')
    print('최종 통계: 적중 %d   실패 %d   적중률 %.2f' % (hits, miss, (100.0*float(hits))/(float(hits)+float(miss))))
    print('')



    
    
    








# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - HIT는 캐시에 이미 있는 페이지(적중), MISS는 없는 페이지(실패)입니다. 교체된 페이지가 -이면 빈 자리를 써서 내보낸 페이지가 없습니다.
  - 적중률 = 적중 수 / 전체 접근 수 × 100입니다. 캐시의 페이지 수와 접근 순서를 고정하고 정책을 비교하세요.
  - FIFO의 FirstIn/Lastin은 먼저/나중에 들어온 쪽, LRU/MRU는 가장 오래전/최근에 사용한 쪽입니다. Left/Right는 단순한 표시 방향입니다.
  - 이 시뮬레이터의 CLOCK은 후보를 무작위로 골라 참조 카운터를 줄입니다. 교재의 원형 포인터 구현과 세부 동작이 다를 수 있습니다.
""")
