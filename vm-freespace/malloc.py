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

class malloc:
    def __init__(self, size, start, headerSize, policy, order, coalesce, align):
        # size of space
        self.size        = size
        
        # info about pretend headers
        self.headerSize  = headerSize

        # init free list
        self.freelist    = []
        self.freelist.append((start, size))

        # keep track of ptr to size mappings
        self.sizemap     = {}

        # policy
        self.policy       = policy
        assert(self.policy in ['FIRST', 'BEST', 'WORST'])

        # list ordering
        self.returnPolicy = order
        assert(self.returnPolicy in ['ADDRSORT', 'SIZESORT+', 'SIZESORT-', 'INSERT-FRONT', 'INSERT-BACK'])

        # this does a ridiculous full-list coalesce, but that is ok
        self.coalesce     = coalesce

        # alignment (-1 if no alignment)
        self.align        = align
        assert(self.align == -1 or self.align > 0)

    def addToMap(self, addr, size):
        assert(addr not in self.sizemap)
        self.sizemap[addr] = size
        # print('adding', addr, 'to map of size', size)
        
    def malloc(self, size):
        if self.align != -1:
            left = size % self.align
            if left != 0:
                diff = self.align - left
            else:
                diff = 0
            # print('aligning: adding %d to %d' % (diff, size))
            size += diff

        size += self.headerSize

        bestIdx  = -1
        if self.policy == 'BEST':
            bestSize = self.size + 1
        elif self.policy == 'WORST' or self.policy == 'FIRST':
            bestSize = -1

        count = 0
            
        for i in range(len(self.freelist)):
            eaddr, esize = self.freelist[i][0], self.freelist[i][1]
            count   += 1
            if esize >= size and ((self.policy == 'BEST'  and esize < bestSize) or
                                  (self.policy == 'WORST' and esize > bestSize) or
                                  (self.policy == 'FIRST')):
                bestAddr = eaddr
                bestSize = esize
                bestIdx  = i
                if self.policy == 'FIRST':
                    break

        if bestIdx != -1:
            if bestSize > size:
                # print('SPLIT', bestAddr, size)
                self.freelist[bestIdx] = (bestAddr + size, bestSize - size)
                self.addToMap(bestAddr, size)
            elif bestSize == size:
                # print('PERFECT MATCH (no split)', bestAddr, size)
                self.freelist.pop(bestIdx)
                self.addToMap(bestAddr, size)
            else:
                abort('도달하면 안 되는 내부 상태입니다')
            return (bestAddr, count)

        # print('*** FAILED TO FIND A SPOT', size)
        return (-1, count)

    def free(self, addr):
        # simple back on end of list, no coalesce
        if addr not in self.sizemap:
            return -1
            
        size = self.sizemap[addr]
        if self.returnPolicy == 'INSERT-BACK':
            self.freelist.append((addr, size))
        elif self.returnPolicy == 'INSERT-FRONT':
            self.freelist.insert(0, (addr, size))
        elif self.returnPolicy == 'ADDRSORT':
            self.freelist.append((addr, size))
            self.freelist = sorted(self.freelist, key=lambda e: e[0])
        elif self.returnPolicy == 'SIZESORT+':
            self.freelist.append((addr, size))
            self.freelist = sorted(self.freelist, key=lambda e: e[1], reverse=False)
        elif self.returnPolicy == 'SIZESORT-':
            self.freelist.append((addr, size))
            self.freelist = sorted(self.freelist, key=lambda e: e[1], reverse=True)

        # not meant to be an efficient or realistic coalescing...
        if self.coalesce == True:
            self.newlist = []
            self.curr    = self.freelist[0]
            for i in range(1, len(self.freelist)):
                eaddr, esize = self.freelist[i]
                if eaddr == (self.curr[0] + self.curr[1]):
                    self.curr = (self.curr[0], self.curr[1] + esize)
                else:
                    self.newlist.append(self.curr)
                    self.curr = eaddr, esize
            self.newlist.append(self.curr)
            self.freelist = self.newlist
            
        del self.sizemap[addr]
        return 0

    def dump(self):
        print('빈 공간 목록 [ 항목 수 %d ]: ' % len(self.freelist), end='')
        for e in self.freelist:
            print('[ 시작 주소:%d 크기:%d ]' % (e[0], e[1]), end='')
        print('')


#
# main program
#
parser = OptionParser()

parser.add_option('-s', '--seed',        default=0,          help='난수 시드 (같은 값으로 같은 문제 재현)',                             action='store', type='int',    dest='seed')
parser.add_option('-S', '--size',        default=100,        help='힙 크기',                            action='store', type='int',    dest='heapSize')
parser.add_option('-b', '--baseAddr',    default=1000,       help='힙의 시작 주소',                        action='store', type='int',    dest='baseAddr')
parser.add_option('-H', '--headerSize',  default=0,          help='할당 블록의 헤더 크기',                          action='store', type='int',    dest='headerSize')
parser.add_option('-a', '--alignment',   default=-1,         help='할당 크기의 정렬 단위 (-1: 정렬하지 않음)', action='store', type='int',    dest='alignment')
parser.add_option('-p', '--policy',      default='BEST',     help='빈 공간 탐색 정책 (BEST: 가장 작은 적합 공간, WORST: 가장 큰 공간, FIRST: 첫 적합 공간)',            action='store', type='string', dest='policy')
parser.add_option('-l', '--listOrder',   default='ADDRSORT', help='빈 공간 목록 순서 (ADDRSORT: 주소순, SIZESORT+/-: 크기 오름/내림차순, INSERT-FRONT/BACK: 앞/뒤 삽입)', action='store', type='string', dest='order')
parser.add_option('-C', '--coalesce',    default=False,      help='목록에서 연속한 인접 빈 공간 병합',                     action='store_true',           dest='coalesce')
parser.add_option('-n', '--numOps',      default=10,         help='임의 생성할 동작 수',            action='store', type='int',    dest='opsNum')
parser.add_option('-r', '--range',       default=10,         help='최대 할당 크기',                              action='store', type='int',    dest='opsRange')
parser.add_option('-P', '--percentAlloc',default=50,         help='전체 동작 중 할당의 비율',              action='store', type='int',    dest='opsPAlloc')
parser.add_option('-A', '--allocList',   default='',         help='동작 직접 지정 (+10: 크기 10 할당, -0: 첫 할당 해제)', action='store', type='string', dest='opsList')
parser.add_option('-c', '--compute',     default=False,      help='정답과 계산 결과 표시',                      action='store_true',           dest='solve')

(options, args) = parser.parse_args()

m = malloc(int(options.heapSize), int(options.baseAddr), int(options.headerSize),
           options.policy, options.order, options.coalesce, options.alignment)

print('난수 시드', options.seed)
print('크기', options.heapSize)
print('시작 주소', options.baseAddr)
print('헤더 크기', options.headerSize)
print('정렬 단위', options.alignment)
print('정책', options.policy)
print('목록 순서', options.order)
print('인접 공간 병합', options.coalesce)
print('동작 수', options.opsNum)
print('할당 크기 범위', options.opsRange)
print('할당 비율', options.opsPAlloc)
print('동작 목록', options.opsList)
print('정답 표시', options.solve)
print('')

percent = int(options.opsPAlloc) / 100.0

random_seed(int(options.seed))
p = {}
L = []
assert(percent > 0)

if options.opsList == '':
    c = 0
    j = 0
    while j < int(options.opsNum):
        pr = False
        if random.random() < percent:
            size     = int(random.random() * int(options.opsRange)) + 1
            ptr, cnt = m.malloc(size)
            if ptr != -1:
                p[c] = ptr
                L.append(c)
            print('ptr[%d] = 할당(%d)' % (c, size), end='')
            if options.solve == True:
                print(' 반환값 %d (탐색한 항목 %d개)' % (ptr + options.headerSize, cnt))
            else:
                print(' 반환값 ?')
            c += 1
            j += 1
            pr = True
        else:
            if len(p) > 0:
                # pick random one to delete
                d = int(random.random() * len(L))
                rc = m.free(p[L[d]])
                print('해제(ptr[%d])' % L[d], )
                if options.solve == True:
                    print('반환값 %d' % rc)
                else:
                    print('반환값 ?')
                del p[L[d]]
                del L[d]
                # print('DEBUG p', p)
                # print('DEBUG L', L)
                pr = True
                j += 1
        if pr:
            if options.solve == True:
                m.dump()
            else:
                print('빈 공간 목록은? ')
            print('')
else:
    c = 0
    for op in options.opsList.split(','):
        if op[0] == '+':
            # allocation!
            size     = int(op.split('+')[1])
            ptr, cnt = m.malloc(size)
            if ptr != -1:
                p[c] = ptr
            print('ptr[%d] = 할당(%d)' % (c, size), end='')
            if options.solve == True:
                print(' 반환값 %d (탐색한 항목 %d개)' % (ptr, cnt))
            else:
                print(' 반환값 ?')
            c += 1
        elif op[0] == '-':
            # free
            index = int(op.split('-')[1])
            if index >= len(p):
                print('잘못된 해제 요청: 건너뜁니다')
                continue
            print('해제(ptr[%d])' % index, )
            rc = m.free(p[index])
            if options.solve == True:
                print('반환값 %d' % rc)
            else:
                print('반환값 ?')
        else:
            abort('잘못된 피연산자: +크기 또는 -인덱스 형식이어야 합니다')
        if options.solve == True:
            m.dump()
        else:
            print('빈 공간 목록은?')
        print('')

# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 빈 공간 목록의 항목 수는 빈 구간 개수이며 남은 바이트 수가 아닙니다. 각 항목은 시작 주소와 연속한 빈 공간 크기를 나타냅니다.
  - 내부 할당 결과 -1은 실패입니다. 동작 목록을 직접 지정한 모드(-A)는 이 값 또는 할당 블록 시작 주소를 표시합니다.
  - 원본의 임의 생성 모드는 표시할 때 헤더 크기를 더합니다. 따라서 헤더가 0이 아니면 성공 시 데이터 시작 주소, 실패 시에도 (-1 + 헤더 크기)가 표시됩니다.
  - 해제 반환값은 0이면 성공, -1이면 실패입니다. 탐색한 항목 수는 할당 위치를 찾기 위해 확인한 빈 구간 수입니다.
  - 총 빈 공간이 충분해도 큰 연속 공간이 없으면 할당에 실패할 수 있습니다(외부 단편화). 헤더·정렬로 요청 크기보다 더 많은 공간을 쓸 수 있습니다.
""")
