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

def roundup(size):
    value = 1.0
    while value < size:
        value = value * 2.0
    return value

    
class OS:
    def __init__(self):
        # 4k phys memory (128 pages)
        self.pageSize  = 32
        self.physPages = 128
        self.physMem   = self.pageSize * self.physPages
        self.vaPages   = 1024
        self.vaSize    = self.pageSize * self.vaPages
        self.pteSize   = 1
        self.pageBits  = 5 # log of page size

        # os tracks
        self.usedPages      = []
        self.usedPagesCount = 0
        self.maxPageCount   = int(self.physMem / self.pageSize)

        # no pages used (yet)
        for i in range(0, self.maxPageCount):
            self.usedPages.append(0)

        # set contents of memory to 0, too
        self.memory = []
        for i in range(0, self.physMem):
            self.memory.append(0)

        # associative array of pdbr's (indexed by PID)
        self.pdbr = {}

        # mask is 11111 00000 00000 --> 0111 1100 0000 0000 
        self.PDE_MASK    = 0x7c00
        self.PDE_SHIFT   = 10

        # 00000 11111 00000 -> 000 0011 1110 0000
        self.PTE_MASK    = 0x03e0
        self.PTE_SHIFT   = 5

        self.VPN_MASK    = self.PDE_MASK | self.PTE_MASK
        self.VPN_SHIFT   = self.PTE_SHIFT

        # grabs the last five bits of a virtual address
        self.OFFSET_MASK = 0x1f

    def findFree(self):
        assert(self.usedPagesCount < self.maxPageCount)
        look = int(random.random() * self.maxPageCount)
        while self.usedPages[look] == 1:
            look = int(random.random() * self.maxPageCount)
        self.usedPagesCount = self.usedPagesCount + 1
        self.usedPages[look] = 1
        return look

    def initPageDir(self, whichPage):
        whichByte = whichPage << self.pageBits
        for i in range(whichByte, whichByte + self.pageSize):
            self.memory[i] = 0x7f

    def initPageTablePage(self, whichPage):
        self.initPageDir(whichPage)

    def getPageTableEntry(self, virtualAddr, ptePage, printStuff):
        pteBits = (virtualAddr & self.PTE_MASK) >> self.PTE_SHIFT
        pteAddr = (ptePage << self.pageBits) | pteBits
        pte     = self.memory[pteAddr]
        valid   = (pte & 0x80) >> 7
        pfn     = (pte & 0x7f)
        if printStuff == True:
            print('    --> PTE 인덱스:0x%x [십진수 %d] 항목 값:0x%x (유효 비트 %d, PFN 0x%02x [십진수 %d])' % (pteBits, pteBits, pte, valid, pfn, pfn))
        return (valid, pfn, pteAddr)

    def getPageDirEntry(self, pid, virtualAddr, printStuff):
        pageDir = self.pdbr[pid]
        pdeBits = (virtualAddr & self.PDE_MASK) >> self.PDE_SHIFT
        pdeAddr = (pageDir << self.pageBits) | pdeBits
        pde     = self.memory[pdeAddr]
        valid   = (pde & 0x80) >> 7
        ptPtr   = (pde & 0x7f)
        if printStuff == True:
            print('  --> PDE 인덱스:0x%x [십진수 %d] 항목 값:0x%x (유효 비트 %d, PFN 0x%02x [십진수 %d])' % (pdeBits, pdeBits, pde, valid, ptPtr, ptPtr))
        return (valid, ptPtr, pdeAddr)

    def setPageTableEntry(self, pteAddr, physicalPage):
        self.memory[pteAddr] = 0x80 | physicalPage

    def setPageDirEntry(self, pdeAddr, physicalPage):
        self.memory[pdeAddr] = 0x80 | physicalPage
        
    def allocVirtualPage(self, pid, virtualPage, physicalPage):
        # make it into a virtual address, as everything uses this (and not VPN)
        virtualAddr = virtualPage << self.pageBits
        (valid, ptPtr, pdeAddr) = self.getPageDirEntry(pid, virtualAddr, False)
        if valid == 0:
            # must allocate a page of the page table now, and have the PD point to it
            assert(ptPtr == 127)
            ptePage = self.findFree()
            self.setPageDirEntry(pdeAddr, ptePage)
            self.initPageTablePage(ptePage)
        else:
            # otherwise, just extract page number of page table page
            ptePage = ptPtr
        # now, look up page table entry too, and mark it valid and fill in translation
        (valid, pfn, pteAddr) = self.getPageTableEntry(virtualAddr, ptePage, False)
        assert(valid == 0)
        assert(pfn == 127)
        self.setPageTableEntry(pteAddr, physicalPage)

    # -2 -> PTE fault, -1 means PDE fault
    def translate(self, pid, virtualAddr):
        (valid, ptPtr, pdeAddr) = self.getPageDirEntry(pid, virtualAddr, True)
        if valid == 1:
            ptePage = ptPtr
            (valid, pfn, pteAddr) = self.getPageTableEntry(virtualAddr, ptePage, True)
            if valid == 1:
                offset = (virtualAddr & self.OFFSET_MASK)
                paddr  = (pfn << self.pageBits) | offset
		# print('     --> pfn: %02x  offset: %x' % (pfn, offset))
                return paddr
            else:
                return -2
        return -1

    def fillPage(self, whichPage):
        for j in range(0, self.pageSize):
            self.memory[(whichPage * self.pageSize) + j] = int(random.random() * 31)

    def procAlloc(self, pid, numPages):
        # need a PDBR: find one somewhere in memory
        pageDir = self.findFree()
        # print('**ALLOCATE** page dir', pageDir)
        self.pdbr[pid] = pageDir
        self.initPageDir(pageDir)

        used = {}
        for vp in range(0, self.vaPages):
            used[vp] = 0
        allocatedVPs = []
        
        for vp in range(0, numPages):
            vp = int(random.random() * self.vaPages)
            while used[vp] == 1:
                vp = int(random.random() * self.vaPages)
            assert(used[vp] == 0)
            used[vp] = 1
            allocatedVPs.append(vp)
            pp = self.findFree()
            # print('**ALLOCATE** page', pp)
            # print('  trying to map vp:%08x to pp:%08x' % (vp, pp))
            self.allocVirtualPage(pid, vp, pp)
            self.fillPage(pp)
        return allocatedVPs

    def dumpPage(self, whichPage):
        i = whichPage
        for j in range(0, self.pageSize):
            print(self.memory[(i * self.pageSize) + j], end='')
        print('')

    def memoryDump(self):
        for i in range(0, int(self.physMem / self.pageSize)):
            print('페이지 %3d:' %  i, end='')
            for j in range(0, self.pageSize):
                print('%02x' % self.memory[(i * self.pageSize) + j], end='')
            print('')

    def getPDBR(self, pid):
        return self.pdbr[pid]

    def getValue(self, addr):
        return self.memory[addr]

# allocate some processes in memory
# allocate some multi-level page tables in memory
# make a bit of a mystery:
# can examine PDBR (PFN of current proc's page directory)
# can examine contents of any page
# fill pages with values too
# ask: when given
#   LOAD VA, R1
# what will final value will be loaded into R1?

#
# main program
#
parser = OptionParser()
parser.add_option('-s', '--seed', default=0, help='난수 시드 (같은 값으로 같은 문제 재현)', action='store', type='int', dest='seed')
parser.add_option('-a', '--allocated', default=64, help='할당할 가상 페이지 수',
                  action='store', type='int', dest='allocated')
parser.add_option('-n', '--addresses', default=10, help='생성할 가상 주소 수',
                  action='store', type='int', dest='num')
parser.add_option('-c', '--solve', help='정답과 계산 결과 표시', action='store_true', default=False, dest='solve')


(options, args) = parser.parse_args()

print("""
[각주: 출력 읽는 법]
  - PDBR은 페이지 디렉터리가 놓인 물리 페이지 번호입니다. PDE는 디렉터리 항목, PTE는 페이지 테이블 항목입니다.
  - 가상 주소를 디렉터리 인덱스·테이블 인덱스·오프셋으로 나누고 PDBR → PDE → PTE → 데이터 순서로 따라가세요.
  - valid는 유효 비트, PFN은 다음 단계의 물리 페이지 번호입니다. 어느 단계든 유효 비트가 0이면 이 문제에서는 주소 변환 실패입니다.
  - 마지막 값(Value)은 물리 주소 자체가 아니라 그 주소에 저장된 데이터입니다. 이 시뮬레이터의 페이지 크기는 32바이트입니다.
""")

print('설정 난수 시드 (seed)', options.seed)
print('설정 할당할 가상 페이지 수 (allocated)',  options.allocated)
print('설정 생성할 주소 수 (num)',  options.num)
print('')

random_seed(options.seed)

# do the work now
os = OS()
used = os.procAlloc(1, options.allocated)

os.memoryDump()

print('\n페이지 디렉터리 기준 레지스터(PDBR):', os.getPDBR(1), ' (십진수) [페이지 디렉터리가 저장된 물리 페이지 번호]\n')

for i in range(0, options.num):
    if (random.random() * 100) > 50.0 or i >= len(used):
        vaddr = int(random.random() * 1024 * 32)
    else:
        vaddr = (used[i] << 5) | int(random.random() * 32)
    if options.solve == True:
        print('가상 주소 0x%04x:' % vaddr)
        r = os.translate(1, vaddr)
        if r > -1:
            print('      --> 물리 주소 0x%03x로 변환 --> 저장된 값: 0x%02x' % (r, os.getValue(r)))
        elif r == -1:
            print('      --> 주소 변환 실패 (페이지 디렉터리 항목이 유효하지 않음)')
        else:
            print('      --> 주소 변환 실패 (페이지 테이블 항목이 유효하지 않음)')
    else:
        print('가상 주소 %04x: 물리 주소와 저장된 값은? 또는 주소 변환 실패인가요?' % vaddr)

print('')

exit(0)





