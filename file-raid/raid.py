#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import math
import random
from optparse import OptionParser

# to make Python2 and Python3 act the same -- how dumb
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

# minimum unit of transfer to RAID
BLOCKSIZE = 4096

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

class disk:
    def __init__(self, seekTime=10, xferTime=0.1, queueLen=8):
        # these are both in milliseconds
        # seek is the time to seek (simple constant amount)
        # transfer is the time to read one block
        self.seekTime = seekTime
        self.xferTime = xferTime

        # length of scheduling queue
        self.queueLen = queueLen

        # current location: make it negative so that whatever
        # the first read is, it causes a seek 
        self.currAddr = -10000

        # queue
        self.queue    = []

        # disk geometry
        self.numTracks      = 100
        self.blocksPerTrack = 100
        self.blocksPerDisk  = self.numTracks * self.blocksPerTrack

        # stats
        self.countIO   = 0
        self.countSeq  = 0
        self.countNseq = 0
        self.countRand = 0
        self.utilTime  = 0

    def stats(self):
        return (self.countIO, self.countSeq, self.countNseq, self.countRand, self.utilTime)

    def enqueue(self, addr):
        assert(addr < self.blocksPerDisk)
        self.countIO += 1

        # check if this is on the same track, or a different one
        currTrack = int(self.currAddr / self.numTracks)
        newTrack  = int(addr / self.numTracks)

        # absolute diff
        diff = addr - self.currAddr
        if diff < 0:
            diff = -diff

        # if on the same track...
        if currTrack == newTrack or diff < self.blocksPerTrack:
            if diff == 1:
                self.countSeq += 1
            else:
                self.countNseq += 1
            self.utilTime += (diff * self.xferTime)
        else:
            self.countRand += 1
            self.utilTime += (self.seekTime + self.xferTime)
        self.currAddr = addr

    def go(self):
        return self.utilTime

class raid:
    def __init__(self, chunkSize='4k', numDisks=4, level=0, timing=False, reverse=False, solve=False, raid5type='LS'):
        chunkSize      = int(convert(chunkSize))
        self.chunkSize = int(chunkSize / BLOCKSIZE)
        self.numDisks  = numDisks
        self.raidLevel = level
        self.timing    = timing
        self.reverse   = reverse
        self.solve     = solve
        self.raid5type = raid5type

        if (chunkSize % BLOCKSIZE) != 0:
            print('청크 크기 (%d)는 블록 크기 (%d)의 배수여야 합니다: %d' % (chunkSize, BLOCKSIZE, self.chunkSize % BLOCKSIZE))
            exit(1)
        if self.raidLevel == 1 and numDisks % 2 != 0:
            print('RAID 1: 디스크 수 (%d)는 짝수여야 합니다' % numDisks)
            exit(1)

        if self.raidLevel == 4:
            self.blocksInStripe = (self.numDisks - 1) * self.chunkSize
            self.pdisk = self.numDisks - 1
        if self.raidLevel == 5:
            self.blocksInStripe = (self.numDisks - 1) * self.chunkSize
            self.pdisk = -1

        self.disks = []
        for i in range(self.numDisks):
            self.disks.append(disk())

    # print per-disk stats
    def stats(self, totalTime):
        for d in range(self.numDisks):
            s = self.disks[d].stats()
            if totalTime > 0.0:
                util = (100.0*float(s[4])/totalTime)
            else:
                util = 0.0
            if s[4] == totalTime:
                print('디스크:%d  사용률: %.2f  I/O 수: %5d (순차:%d 인접:%d 무작위:%d)' % (d, util, s[0], s[1], s[2], s[3]))
            elif s[4] == 0:
                print('디스크:%d  사용률:   %.2f  I/O 수: %5d (순차:%d 인접:%d 무작위:%d)' % (d, util, s[0], s[1], s[2], s[3]))
            else:
                print('디스크:%d  사용률:  %.2f  I/O 수: %5d (순차:%d 인접:%d 무작위:%d)' % (d, util, s[0], s[1], s[2], s[3]))

    # global enqueue function
    def enqueue(self, addr, size, isWrite):
        # should we print out the logical operation?
        if self.timing == False:
            if self.solve or self.reverse==False:
                if isWrite:
                    print('논리 쓰기  주소:%d 크기:%d' % (addr, size * BLOCKSIZE))
                else:
                    print('논리 읽기  주소:%d 크기:%d' % (addr, size * BLOCKSIZE))
                if self.solve == False:
                    print('  어떤 물리 읽기/쓰기가 필요한가요?\n')
            else:
                print('이에 해당하는 논리 동작은?')

        # should we print out the physical operations?
        if self.timing == False and (self.solve or self.reverse==True):
            self.printPhysical = True
        else:
            self.printPhysical = False

        if self.raidLevel == 0:
            self.enqueue0(addr, size, isWrite)
        elif self.raidLevel == 1:
            self.enqueue1(addr, size, isWrite)
        elif self.raidLevel == 4 or self.raidLevel == 5:
            self.enqueue45(addr, size, isWrite)

    # process disk workloads one at a time, returning final completion time
    def go(self):
        tmax = 0
        for d in range(self.numDisks):
            t = self.disks[d].go()
            if t > tmax:
                tmax = t
        return tmax

    # helper functions
    def doSingleRead(self, disk, off, doNewline=False):
        if self.printPhysical:
            print('  읽기  [디스크 %d, 오프셋 %d]  ' % (disk, off), end='')
            if doNewline:
                print('')
        self.disks[disk].enqueue(off)

    def doSingleWrite(self, disk, off, doNewline=False):
        if self.printPhysical:
            print('  쓰기  [디스크 %d, 오프셋 %d]  ' % (disk, off), end='')
            if doNewline:
                print('')
        self.disks[disk].enqueue(off)

    # 
    # mapping for RAID 0 (striping)
    #
    def bmap0(self, bnum):
        cnum = int(bnum / self.chunkSize)
        coff = bnum % self.chunkSize
        return (cnum % self.numDisks, int(int(cnum / self.numDisks) * self.chunkSize + coff))

    def enqueue0(self, addr, size, isWrite):
        # can ignore isWrite, as I/O pattern is the same for striping
        for b in range(addr, addr+size):
            (disk, off) = self.bmap0(b)
            if isWrite:
                self.doSingleWrite(disk, off, True)
            else:
                self.doSingleRead(disk, off, True)
        if self.timing == False and self.printPhysical:
            print('')

    #
    # mapping for RAID 1 (mirroring)
    # 
    def bmap1(self, bnum):
        cnum = int(bnum / self.chunkSize)
        coff = bnum % self.chunkSize
        disk = int(2 * (cnum % int(self.numDisks / 2)))
        return (disk, disk + 1, int(int(cnum / int(self.numDisks / 2))) * self.chunkSize + coff)

    def enqueue1(self, addr, size, isWrite):
        for b in range(addr, addr+size):
            (disk1, disk2, off) = self.bmap1(b)
            # print 'enqueue:', addr, size, '-->', m
            if isWrite:
                self.doSingleWrite(disk1, off, False)
                self.doSingleWrite(disk2, off, True)
            else:
                # the raid-1 read balancing algorithm is here;
                # could be something more intelligent -- 
                # instead, it is just based on the disk offset
                # to produce something easily reproducible
                if off % 2 == 0:
                    self.doSingleRead(disk1, off, True)
                else:
                    self.doSingleRead(disk2, off, True)
        if self.timing == False and self.printPhysical:
            print('')

    # 
    # mapping for RAID 4 (parity disk)
    # 
    # assumes (for now) that there is just one parity disk
    #
    def bmap4(self, bnum):
        cnum = int(bnum / self.chunkSize)
        coff = bnum % self.chunkSize
        return (cnum % (self.numDisks - 1), int(cnum / (self.numDisks - 1)) * self.chunkSize + coff)

    def pmap4(self, snum):
        return self.pdisk

    # 
    # mapping for RAID 5 (rotated parity)
    #
    def __bmap5(self, bnum):
        cnum = int(bnum / self.chunkSize)
        coff = bnum % self.chunkSize
        ddsk = int(cnum / (self.numDisks - 1))
        doff = (ddsk * self.chunkSize) + coff
        disk = cnum % (self.numDisks - 1)
        col = (ddsk % self.numDisks)
        pdisk = (self.numDisks - 1) - col

        # supports left-asymmetric and left-symmetric layouts
        if self.raid5type == 'LA':
            if disk >= pdisk:
                disk += 1
        elif self.raid5type == 'LS':
            disk = (disk - col) % (self.numDisks)
        else:
            print('오류: 지원하지 않는 RAID 방식')
            exit(1)
        assert(disk != pdisk)
        return (disk, pdisk, doff)

    # yes this is lame (redundant call to __bmap5 is serious programmer laziness)
    def bmap5(self, bnum):
        (disk, pdisk, off) = self.__bmap5(bnum)
        return (disk, off)

    # this too is lame (redundant call to __bmap5 is serious programmer laziness)
    def pmap5(self, snum):
        (disk, pdisk, off) = self.__bmap5(snum * self.blocksInStripe)
        return pdisk

    # RAID 4/5 helper routine to write out some blocks in a stripe
    def doPartialWrite(self, stripe, begin, end, bmap, pmap):
        numWrites = end - begin
        pdisk     = pmap(stripe)
        if (numWrites + 1) <= (self.blocksInStripe - numWrites):
            # SUBTRACTIVE PARITY
            # print 'SUBTRACTIVE'
            offList = []
            for voff in range(begin, end):
                (disk, off) = bmap(voff)
                self.doSingleRead(disk, off)
                if off not in offList:
                    offList.append(off)
            for i in range(len(offList)):
                self.doSingleRead(pdisk, offList[i], i == (len(offList) - 1))
        else:
            # ADDITIVE PARITY 
            # print 'ADDITIVE'
            stripeBegin = stripe * self.blocksInStripe
            stripeEnd   = stripeBegin + self.blocksInStripe
            for voff in range(stripeBegin, begin):
                (disk, off) = bmap(voff)
                self.doSingleRead(disk, off, (voff == (begin - 1)) and (end == stripeEnd))
            for voff in range(end, stripeEnd):
                (disk, off) = bmap(voff)
                self.doSingleRead(disk, off, voff == (stripeEnd - 1))

        # WRITES: same for additive or subtractive parity
        offList = []
        for voff in range(begin, end):
            (disk, off) = bmap(voff)
            self.doSingleWrite(disk, off)
            if off not in offList:
                offList.append(off)
        for i in range(len(offList)):
            self.doSingleWrite(pdisk, offList[i], i == (len(offList) - 1))

    # RAID 4/5 enqueue routine
    def enqueue45(self, addr, size, isWrite):
        if self.raidLevel == 4:
            (bmap, pmap) = (self.bmap4, self.pmap4)
        elif self.raidLevel == 5:
            (bmap, pmap) = (self.bmap5, self.pmap5)

        if isWrite == False:
            for b in range(addr, addr+size):
                (disk, off) = bmap(b)
                self.doSingleRead(disk, off)
        else:
            # process the write request, one stripe at a time
            initStripe     = int((addr)            / self.blocksInStripe)
            finalStripe    = int((addr + size - 1) / self.blocksInStripe)

            left  = size
            begin = addr
            for stripe in range(initStripe, finalStripe + 1):
                endOfStripe = (stripe * self.blocksInStripe) + self.blocksInStripe

                if left >= self.blocksInStripe:
                    end = begin + self.blocksInStripe
                else:
                    end = begin + left

                if end >= endOfStripe:
                    end = endOfStripe
                        
                self.doPartialWrite(stripe, begin, end, bmap, pmap)

                left -= (end - begin)
                begin = end
                    
        # for all cases, print this for pretty-ness in mapping mode
        if self.timing == False and self.printPhysical:
            print('')

#
# main program
#
parser = OptionParser()

parser.add_option('-s', '--seed',        default=0,      help='난수 시드 (같은 값으로 같은 문제 재현)',                                action='store',       type='int',    dest='seed')
parser.add_option('-D', '--numDisks',    default=4,      help='RAID의 디스크 수',                        action='store',       type='int',    dest='numDisks')
parser.add_option('-C', '--chunkSize',   default='4k',   help='RAID 청크 크기',                         action='store',       type='string', dest='chunkSize')
parser.add_option('-n', '--numRequests', default=10,     help='시뮬레이션할 요청 수',                 action='store',       type='int',    dest='numRequests')
parser.add_option('-S', '--reqSize',     default='4k',   help='요청 크기',                               action='store',       type='string', dest='size')
parser.add_option('-W', '--workload',    default='rand', help='작업 부하 유형: rand (무작위), seq (순차)',               action='store',       type='string', dest='workload')
parser.add_option('-w', '--writeFrac',   default=0,      help='쓰기 비율 (100: 모두 쓰기, 0: 모두 읽기)', action='store',       type='int',    dest='writeFrac')
parser.add_option('-R', '--randRange',   default=10000,  help='무작위 작업 부하에서 요청 주소 범위', action='store',       type='int',    dest='range')
parser.add_option('-L', '--level',       default=0,      help='RAID 수준 (0, 1, 4, 5)',                        action='store',       type='int',    dest='level')
parser.add_option('-5', '--raid5',       default='LS',   help='RAID 5 배치: LS (좌측 대칭), LA (좌측 비대칭)',   action='store',       type='string', dest='raid5type')
parser.add_option('-r', '--reverse',     default=False,  help='논리 동작 대신 물리 동작을 보여 주고 논리 동작을 문제로 제시',  action='store_true',                 dest='reverse')
parser.add_option('-t', '--timing',      default=False,  help='주소 매핑 대신 소요 시간 계산 모드 사용',       action='store_true',                 dest='timing')
parser.add_option('-c', '--compute',     default=False,  help='정답과 계산 결과 표시',                         action='store_true',                 dest='solve')

(options, args) = parser.parse_args()

print("""
[각주: 출력 읽는 법]
  - 논리 주소는 사용자가 보는 주소, 물리 위치는 실제 디스크 번호와 그 디스크 내부 오프셋입니다. 주소·오프셋은 블록 단위, 논리 요청의 크기는 바이트 단위입니다.
  - 요청 앞에 이름 없이 나오는 두 숫자는 시작 블록 번호와 요청 블록 수입니다.
  - RAID 0은 분산 저장, RAID 1은 복제, RAID 4/5는 패리티를 사용합니다. 논리 쓰기 하나가 여러 물리 읽기/쓰기로 바뀔 수 있습니다.
  - 시간 모드의 사용률은 전체 소요 시간 대비 각 디스크가 바빴던 비율(%)입니다. 병렬 동작하므로 디스크별 시간을 단순히 더하면 전체 시간이 되지 않습니다.
""")

print('설정 블록 크기 (blockSize)',   BLOCKSIZE)
print('설정 난수 시드 (seed)',        options.seed)
print('설정 디스크 수 (numDisks)',    options.numDisks)
print('설정 청크 크기 (chunkSize)',   options.chunkSize)
print('설정 요청 수 (numRequests)', options.numRequests)
print('설정 요청 크기 (reqSize)',     options.size)
print('설정 작업 부하 유형 (workload)',    options.workload)
print('설정 쓰기 비율 (writeFrac)',   options.writeFrac)
print('설정 무작위 요청 범위 (randRange)',   options.range)
print('설정 RAID 수준 (level)',       options.level)
print('설정 RAID 5 배치 방식 (raid5)',       options.raid5type)
print('설정 문제와 정답의 표시 방향 반전 (reverse)',     options.reverse)
print('설정 소요 시간 모드 (timing)',      options.timing)
print('')

writeFrac = float(options.writeFrac) / 100.0
assert(writeFrac >= 0.0 and writeFrac <= 1.0)

random_seed(options.seed)

size = convert(options.size)
if size % BLOCKSIZE != 0:
    print('오류: 요청 크기 (%d)는 블록 크기 (%d)의 배수여야 합니다' % (size, BLOCKSIZE))
    exit(1)
size = int(size / BLOCKSIZE)

if options.workload == 'seq' or options.workload == 's' or options.workload == 'sequential':
    workloadIsSequential = True
elif options.workload == 'rand' or options.workload == 'r' or options.workload == 'random':
    workloadIsSequential = False
else:
    print('오류: 작업 부하는 r/rand/random 또는 s/seq/sequential이어야 합니다')
    exit(1)

assert(options.level == 0 or options.level == 1 or options.level == 4 or options.level == 5)
if options.level != 0 and options.numDisks < 2:
    print('RAID 4와 RAID 5는 디스크가 2개 이상 필요합니다')
    exit(1)

if options.level == 5 and options.raid5type != 'LA' and options.raid5type != 'LS':
    print('RAID 5는 좌측 비대칭(LA)과 좌측 대칭(LS)만 지원합니다 (%s은(는) 지원하지 않음)' % options.raid5type)
    exit(1)

# instantiate RAID
r = raid(chunkSize=options.chunkSize, numDisks=options.numDisks, level=options.level, timing=options.timing,
         reverse=options.reverse, solve=options.solve, raid5type=options.raid5type)

# generate requests
off = 0
for i in range(options.numRequests):
    if workloadIsSequential == True:
        blk = off
        off += size
    else:
        blk = int(random.random() * options.range)
    if random.random() < writeFrac:
        print(blk, size)
        r.enqueue(blk, size, True)
    else:
        print(blk, size)
        r.enqueue(blk, size, False)

# process requests
t = r.go()

# print out some final info, if needed
if options.timing == False:
    print('')
    exit(0)

if options.solve:
    print('')
    r.stats(t)
    print('')
    print('통계: 전체 소요 시간', t)
    print('')
else:
    print('')
    print('작업 부하가 완료되기까지 걸리는 시간을 추정하세요.')
    print('- 각 디스크는 대략 몇 개의 요청을 받나요?')
    print('- 무작위 요청과 순차 요청은 각각 몇 개인가요?')
    print('')
