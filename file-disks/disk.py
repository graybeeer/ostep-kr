#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
try:
    from Tkinter import *
except:
    from tkinter import *
from types import *
import math, random, time, sys, os
from optparse import OptionParser

# to make Python2 and Python3 act the same -- how dumb
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

MAXTRACKS = 1000

# states that a request/disk go through
STATE_NULL   = 0
STATE_SEEK   = 1
STATE_ROTATE = 2
STATE_XFER   = 3
STATE_DONE   = 4

#
# TODO
# XXX transfer time
# XXX satf 
# XXX skew
# XXX scheduling window
# XXX sstf
# XXX specify requests vs. random requests in range
# XXX add new requests as old ones complete (starvation)
# XXX run in non-graphical mode
# XXX better graphical display (show key, long lists of requests, more timings on screen)
# XXX be able to do "pure" sequential
# XXX add more blocks around outer tracks (zoning)
# XXX simple flag to make scheduling window a fairness window (-F)
#     new algs to scan and c-scan the disk?
#

class Disk:
    def __init__(self, addr, addrDesc, lateAddr, lateAddrDesc,
                 policy, seekSpeed, rotateSpeed, skew, window, compute,
                 graphics, zoning):
        self.addr              = addr
        self.addrDesc          = addrDesc
        self.lateAddr          = lateAddr
        self.lateAddrDesc      = lateAddrDesc
        self.policy            = policy
        self.seekSpeed         = seekSpeed
        self.rotateSpeed       = rotateSpeed
        self.skew              = skew
        self.window            = window
        self.compute           = compute
        self.graphics          = graphics
        self.zoning            = zoning

        # figure out zones first, to figure out the max possible request
        self.InitBlockLayout()
        
        # figure out requests
        random_seed(options.seed)
        self.requests     = self.MakeRequests(self.addr, self.addrDesc)
        self.lateRequests = self.MakeRequests(self.lateAddr, self.lateAddrDesc)

        # graphical startup
        self.width = 500
        if self.graphics:
            self.root = Tk()
            tmpLen = len(self.requests)
            if len(self.lateRequests) > 0:
                tmpLen += len(self.lateRequests)
            self.canvas = Canvas(self.root, width=410, height=460 + ((tmpLen / 20.0) * 20))
            self.canvas.pack()

        # fairness stuff
        if self.policy == 'BSATF' and self.window != -1:
            self.fairWindow = self.window
        else:
            self.fairWindow = -1

        print('요청 목록', self.requests)
        print('')

        # for late requests
        self.lateCount = 0
        if len(self.lateRequests) > 0:
            print('나중에 도착하는 요청', self.lateRequests)
            print('')

        if self.compute == False:
            print('')
            print('위 요청들의 탐색 시간, 회전 대기 시간, 전송 시간을 계산하세요.')
            print('-c 또는 그래픽 모드(-G)로 정답을 확인하세요.')
            print('')

        # BINDINGS
        if self.graphics:
            self.root.bind('s', self.Start)
            self.root.bind('p', self.Pause)
            self.root.bind('q', self.Exit)

        # TRACK INFO
        self.tracks = {}
        self.trackWidth =  40
        self.tracks[0]  = 140
        self.tracks[1]  = self.tracks[0] - self.trackWidth
        self.tracks[2]  = self.tracks[1] - self.trackWidth

        if (self.seekSpeed > 1 and self.trackWidth % self.seekSpeed != 0):
            print('탐색 속도 (%d)는 트랙 폭 (%d)을 나누어떨어지게 해야 합니다' % (self.seekSpeed, self.trackWidth))
            sys.exit(1)
        if self.seekSpeed < 1:
            x = self.trackWidth / self.seekSpeed
            y = int(float(self.trackWidth) / float(self.seekSpeed))
            if float(x) != float(y):
                print('탐색 속도 (%f)는 트랙 폭 (%d)을 나누어떨어지게 해야 합니다' % (self.seekSpeed, self.trackWidth))
                sys.exit(1)

        # DISK SURFACE
        self.cx = self.width / 2.0
        self.cy = self.width / 2.0
        if self.graphics:
            self.canvas.create_rectangle(self.cx-175, 30, self.cx - 20, 80, fill='gray', outline='black')
        self.platterSize = 320
        ps2 = self.platterSize / 2.0
        if self.graphics:
            self.canvas.create_oval(self.cx-ps2, self.cy-ps2, self.cx+ps2, self.cy + ps2, fill='darkgray', outline='black')
        for i in range(len(self.tracks)):
            t = self.tracks[i] - (self.trackWidth / 2.0)
            if self.graphics:
                self.canvas.create_oval(self.cx - t, self.cy - t, self.cx + t, self.cy + t, fill='', outline='black', width=1.0)

        # SPINDLE
        self.spindleX  = self.cx
        self.spindleY  = self.cy
        if self.graphics:
            self.spindleID = self.canvas.create_oval(self.spindleX-3, self.spindleY-3, self.spindleX+3, self.spindleY+3, fill='orange', outline='black')

        # DISK ARM
        self.armTrack     = 0
        self.armSpeedBase = float(seekSpeed)
        self.armSpeed     = float(seekSpeed)

        distFromSpindle   = self.tracks[self.armTrack]
        self.armWidth     = 20
        self.headWidth    = 10

        self.armX         = self.spindleX - (distFromSpindle * math.cos(math.radians(0)))
        self.armX1        = self.armX - self.armWidth
        self.armX2        = self.armX + self.armWidth
        self.armY1        = 50.0
        self.armY2        = self.width / 2.0

        self.headX1       = self.armX - self.headWidth
        self.headX2       = self.armX + self.headWidth
        self.headY1       = (self.width / 2.0) - self.headWidth
        self.headY2       = (self.width / 2.0) + self.headWidth

        if self.graphics:
            self.armID        = self.canvas.create_rectangle(self.armX1, self.armY1, self.armX2, self.armY2, fill='gray', outline='black')
            self.headID       = self.canvas.create_rectangle(self.headX1, self.headY1, self.headX2, self.headY2, fill='gray', outline='black')

        self.targetSize   = 10.0
        if self.graphics:
            sz                = self.targetSize
            self.targetID     = self.canvas.create_oval(self.armX1-sz, self.armY1-sz, self.armX1+sz, self.armY1+sz, fill='orange', outline='')

        # IO QUEUE
        self.queueX       = 20
        self.queueY       = 450
        
        self.requestCount = 0
        self.requestQueue = []
        self.requestState = []
        self.queueBoxSize = 20
        self.queueBoxID   = {}
        self.queueTxtID   = {}

        # draw each box
        for index in range(len(self.requests)):
            self.AddQueueEntry(int(self.requests[index]), index)
        if self.graphics:
            self.canvas.create_text(self.queueX - 5, self.queueY - 20, anchor='w', text='Queue:')

        # scheduling window
        self.currWindow = self.window

        # draw current limits of queue
        if self.graphics:
            self.windowID = -1
            self.DrawWindow()

        # initial scheduling info
        self.currentIndex = -1
        self.currentBlock = -1

        # initial state of disk (vs seeking, rotating, transferring)
        self.state = STATE_NULL

        # DRAW BLOCKS on the TRACKS
        for bid in range(len(self.blockInfoList)):
            (track, angle, name) = self.blockInfoList[bid]
            if self.graphics:
                distFromSpindle = self.tracks[track]
                xc = self.spindleX + (distFromSpindle * math.cos(math.radians(angle)))
                yc = self.spindleY + (distFromSpindle * math.sin(math.radians(angle)))
                cid = self.canvas.create_text(xc, yc, text=name, anchor='center')
            else:
                cid = -1
            self.blockInfoList[bid] = (track, angle, name, cid)

        # angle of rotation
        self.angle = 0.0

        # TIME INFO
        if self.graphics:
            self.timeID = self.canvas.create_text(10, 10, text='Time: 0.00', anchor='w')
            self.canvas.create_rectangle(95,0,200,18, fill='orange', outline='orange')
            self.seekID = self.canvas.create_text(100, 10, text='Seek: 0.00', anchor='w')
            self.canvas.create_rectangle(195,0,300,18, fill='lightblue', outline='lightblue')
            self.rotID  = self.canvas.create_text(200, 10, text='Rotate: 0.00', anchor='w')
            self.canvas.create_rectangle(295,0,400,18, fill='green', outline='green')
            self.xferID = self.canvas.create_text(300, 10, text='Transfer: 0.00', anchor='w')
            self.canvas.create_text(320, 40, text='"s" to start', anchor='w')
            self.canvas.create_text(320, 60, text='"p" to pause', anchor='w')
            self.canvas.create_text(320, 80, text='"q" to quit', anchor='w')
        self.timer = 0

        # STATS
        self.seekTotal   = 0.0
        self.rotTotal    = 0.0
        self.xferTotal   = 0.0

        # set up animation loop
        if self.graphics:
            self.doAnimate = True
        else:
            self.doAnimate = False
        self.isDone = False

    # call this to start simulation
    def Go(self):
        if options.graphics:
            self.root.mainloop()
        else:
            self.GetNextIO()
            while self.isDone == False:
                self.Animate()

    # crappy error message
    def PrintAddrDescMessage(self, value):
        print('잘못된 주소 생성 설정 (%s)' % value)
        print('주소 생성 설정은 공백 없이 쉼표로 구분한 세 값이어야 합니다.')
        print('예: "10,100,0"은 주소 10개를 생성하며,')
        print('최댓값은 100, 최솟값은 0입니다. 최댓값 -1은')
        print('사용 가능한 최대 주소를 뜻합니다.')
        sys.exit(1)
    
    #
    # ZONES AND BLOCK LAYOUT
    #
    def InitBlockLayout(self):
        self.blockInfoList    = []
        self.blockToTrackMap  = {}
        self.blockToAngleMap  = {}
        self.tracksBeginEnd   = {}
        self.blockAngleOffset = []

        zones = self.zoning.split(',')
        assert(len(zones) == 3)
        for i in range(len(zones)):
            print('트랙별 블록 간 각도', i, zones[i])
            self.blockAngleOffset.append(int(zones[i]) // 2)

        track        = 0 # outer track
        angleOffset  = 2 * self.blockAngleOffset[track]
        for angle in range(0, 360, angleOffset):
            block = angle // angleOffset
            print(track, angleOffset, block)
            self.blockToTrackMap[block] = track
            self.blockToAngleMap[block] = angle
            self.blockInfoList.append((track, angle, block))
        self.tracksBeginEnd[track] = (0, block)
        pblock                     = block + 1

        track                      = 1 # middle track
        skew                       = self.skew
        angleOffset                = 2 * self.blockAngleOffset[track]
        for angle in range(0, 360, angleOffset):
            block = (angle // angleOffset) + pblock 
            print(track, skew, angleOffset, block)
            self.blockToTrackMap[block] = track
            self.blockToAngleMap[block] = angle + (angleOffset * skew)
            self.blockInfoList.append((track, angle + (angleOffset * skew), block))
        self.tracksBeginEnd[track] = (pblock, block)
        pblock                     = block + 1

        track                      = 2 # inner track
        skew                       = 2 * self.skew
        angleOffset                = 2 * self.blockAngleOffset[track]
        for angle in range(0, 360, angleOffset):
            block = (angle // angleOffset) + pblock
            print(track, skew, angleOffset, block)
            self.blockToTrackMap[block] = track
            self.blockToAngleMap[block] = angle + (angleOffset * skew)
            self.blockInfoList.append((track, angle + (angleOffset * skew), block))
        self.tracksBeginEnd[track] = (pblock, block)
        self.maxBlock              = pblock
        # print 'MAX BLOCK:', self.maxBlock

        # adjust angle to starting position relative 
        for i in self.blockToAngleMap:
            self.blockToAngleMap[i] = (self.blockToAngleMap[i] + 180) % 360

        # print 'btoa map', self.blockToAngleMap
        # print 'btot map', self.blockToTrackMap
        # print 'bao', self.blockAngleOffset

    def MakeRequests(self, addr, addrDesc):
        (numRequests, maxRequest, minRequest) = (0, 0, 0)
        if addr == '-1':
            # first extract values from descriptor
            desc = addrDesc.split(',')
            if len(desc) != 3:
                self.PrintAddrDescMessage(addrDesc)
            (numRequests, maxRequest, minRequest) = (int(desc[0]), int(desc[1]), int(desc[2]))
            if maxRequest == -1:
                maxRequest = self.maxBlock
            # now make list 
            tmpList = []
            for i in range(numRequests):
                tmpList.append(int(random.random() * maxRequest) + minRequest)
            return tmpList
        else:
            tmpList = []
            for x in addr.split(','):
                tmpList.append(int(x))
            return tmpList

    #
    # BUTTONS
    #
    def Start(self, event):
        self.GetNextIO()
        self.doAnimate = True
        self.Animate()

    def Pause(self, event):
        if self.doAnimate == False:
            self.doAnimate = True
        else:
            self.doAnimate = False

    def Exit(self, event):
        sys.exit(0)

    #
    # CORE SIMULATION and ANIMATION
    #
    def UpdateTime(self):
        if self.graphics:
            self.canvas.itemconfig(self.timeID, text='Time: ' + str(self.timer))
            self.canvas.itemconfig(self.seekID, text='Seek: ' + str(self.seekTotal))
            self.canvas.itemconfig(self.rotID,  text='Rotate: ' + str(self.rotTotal))
            self.canvas.itemconfig(self.xferID, text='Transfer: ' + str(self.xferTotal))

    def AddRequest(self, block):
        self.AddQueueEntry(block, len(self.requestQueue))

    def QueueMap(self, index):
        numPerRow = 400 // self.queueBoxSize
        return (index % numPerRow, index // numPerRow)

    def DrawWindow(self):
        if self.window == -1:
            return
        (col, row) = self.QueueMap(self.currWindow)
        if col == 0:
            (col, row) = (20, row - 1)
        if self.windowID != -1:
            self.canvas.delete(self.windowID)
        self.windowID = self.canvas.create_line(self.queueX + (col * 20) - 10, self.queueY - 13 + (row * 20),
                                                self.queueX + (col * 20) - 10, self.queueY + 13 + (row * 20), width=2)

    def AddQueueEntry(self, block, index):
        self.requestQueue.append((block, index))
        self.requestState.append(STATE_NULL)
        if self.graphics:
            (col, row) = self.QueueMap(index)
            sizeHalf   = self.queueBoxSize / 2.0
            (cx, cy)   = (self.queueX + (col * self.queueBoxSize), self.queueY + (row * self.queueBoxSize))
            self.queueBoxID[index] = self.canvas.create_rectangle(cx - sizeHalf, cy - sizeHalf, cx + sizeHalf, cy + sizeHalf, fill='white')
            self.queueTxtID[index] = self.canvas.create_text(cx, cy, anchor='center', text=str(block))
    
    def SwitchColors(self, c):
        if self.graphics:
            self.canvas.itemconfig(self.queueBoxID[self.currentIndex], fill=c)
            self.canvas.itemconfig(self.targetID, fill=c)

    def SwitchState(self, newState):
        self.state                           = newState
        self.requestState[self.currentIndex] = newState

    def RadiallyCloseTo(self, a1, a2):
        if a1 > a2:
            v = a1 - a2
        else:
            v = a2 - a1
        if v < self.rotateSpeed:
            return True
        return False

    def DoneWithTransfer(self):
        angleOffset = self.blockAngleOffset[self.armTrack]
        # if int(self.angle) == (self.blockToAngleMap[self.currentBlock] + angleOffset) % 360:
        if self.RadiallyCloseTo(self.angle, float((self.blockToAngleMap[self.currentBlock] + angleOffset) % 360)):
            # print 'END TRANSFER', self.angle, self.timer
            self.SwitchState(STATE_DONE)
            self.requestCount += 1
            return True
        return False

    def DoneWithRotation(self):
        angleOffset = self.blockAngleOffset[self.armTrack]
        # XXX there is a weird bug in here
        # print self.timer, 'ROTATE:: ', self.currentBlock, 'currangle: ', self.angle, ' - mapangle: ', self.blockToAngleMap[self.currentBlock]
        # print '  angleOffset  ', angleOffset
        # print '  blockMap     ', (self.blockToAngleMap[self.currentBlock] - angleOffset) % 360
        # print '  self.angle   ', self.angle, int(self.angle)
        # if int(self.angle) == (self.blockToAngleMap[self.currentBlock] - angleOffset) % 360:
        if self.RadiallyCloseTo(self.angle, float((self.blockToAngleMap[self.currentBlock] - angleOffset) % 360)):
            self.SwitchState(STATE_XFER)
            # print ' --> DONE WITH ROTATION!', self.timer
            return True
        return False
        
    def PlanSeek(self, track):
        self.seekBegin = self.timer
        self.SwitchColors('orange')
        self.SwitchState(STATE_SEEK)
        if track == self.armTrack:
            self.rotBegin = self.timer
            self.SwitchColors('lightblue')
            self.SwitchState(STATE_ROTATE)
            return
        self.armTarget   = track
        self.armTargetX1 = self.spindleX - self.tracks[track] - (self.trackWidth / 2.0)
        if track >= self.armTrack:
            self.armSpeed = self.armSpeedBase
        else:
            self.armSpeed = - self.armSpeedBase

    def DoneWithSeek(self):
        # move the disk arm
        self.armX1  += self.armSpeed
        self.armX2  += self.armSpeed
        self.headX1 += self.armSpeed
        self.headX2 += self.armSpeed
        # update it on screen
        if self.graphics:
            self.canvas.coords(self.armID,  self.armX1,  self.armY1,  self.armX2,  self.armY2)
            self.canvas.coords(self.headID, self.headX1, self.headY1, self.headX2, self.headY2)
        # check if done
        if (self.armSpeed > 0.0 and self.armX1 >= self.armTargetX1) or (self.armSpeed < 0.0 and self.armX1 <= self.armTargetX1):
            self.armTrack = self.armTarget
            return True
        return False

    def DoSATF(self, rList):
        minBlock = -1
        minIndex = -1
        minEst   = -1

        # print '**** DoSATF ****', rList
        for (block, index) in rList:
            if self.requestState[index] == STATE_DONE:
                # print '  Skip', index
                continue
            track = self.blockToTrackMap[block]
            angle = self.blockToAngleMap[block]
            # print '  track', track, 'angle', angle

            # estimate seek time
            dist = int(math.fabs(self.armTrack - track))
            seekEst  = (self.trackWidth / self.armSpeedBase) * dist
            # print('  dist', dist)
            # print('  seekEst', seekEst)

            # estimate rotate time
            angleOffset = self.blockAngleOffset[track]
            # print '  angleOffset', angleOffset
            # print '  self.angle', self.angle
            angleAtArrival = (self.angle + (seekEst * self.rotateSpeed))
            while angleAtArrival > 360.0:
                angleAtArrival -= 360.0
            # print 'self.rotateSpeed', self.rotateSpeed
            # print 'angleAtArrival', angleAtArrival
            rotDist = ((angle - angleOffset) - angleAtArrival)
            while rotDist > 360.0:
                rotDist -= 360.0
            while rotDist < 0.0:
                rotDist += 360.0
            rotEst = rotDist / self.rotateSpeed
            # print '  rotEst', rotDist, self.rotateSpeed, ' -> ', rotEst

            # finally, transfer
            xferEst = (angleOffset * 2.0) / self.rotateSpeed

            # print '  xferEst', xferEst

            totalEst = seekEst + rotEst + xferEst
            # print '  totalEst', seekEst, rotEst, xferEst, ' -> ', totalEst

            # print '  --> block:%d seek:%d rotate:%d xfer:%d est:%d' % (block, seekEst, rotEst, xferEst, totalEst)

            # should probably pick one on same track in case of a TIE
            if minEst == -1 or totalEst < minEst:
                minEst   = totalEst
                minBlock = block
                minIndex = index
                # print '  UPDATE new minBlock', minBlock, minIndex
            # print ''
            # END loop

        # when done
        self.totalEst = minEst
        assert(minBlock != -1)
        assert(minIndex != -1)
        return (minBlock, minIndex)

    # 
    # actually doesn't quite do SSTF
    # just finds all the blocks on the nearest track
    # (whatever that may be) and returns it as a list
    # 
    def DoSSTF(self, rList):
        minDist   = MAXTRACKS
        minBlock  = -1
        trackList = []  # all the blocks on a track

        for (block, index) in rList:
            if self.requestState[index] == STATE_DONE:
                continue
            track = self.blockToTrackMap[block]
            dist  = int(math.fabs(self.armTrack - track))
            if dist < minDist:
                trackList = []
                trackList.append((block, index))
                minDist = dist
            elif dist == minDist:
                trackList.append((block, index))
        assert(trackList != [])
        return trackList

    def UpdateWindow(self):
        if self.fairWindow == -1 and self.currWindow > 0 and self.currWindow < len(self.requestQueue):
            self.currWindow += 1
            if self.graphics:
                self.DrawWindow()

    # warning: doesn't just GET the window, but may update it as well
    # (when it is time to do so)
    def GetWindow(self):
        if self.currWindow <= -1:
            return len(self.requestQueue)
        else:
            if self.fairWindow != -1:
                # a WINDOW is in place - 
                # print '  curr window', self.currWindow, '  FAIR window', self.fairWindow, ' request count', self.requestCount
                if self.requestCount > 0 and (self.requestCount % self.fairWindow == 0):
                    self.currWindow = self.currWindow + self.fairWindow
                    # print '  -> UPDATING current window', self.currWindow
                    if self.graphics:
                        self.DrawWindow()
                return self.currWindow
            else:
                return self.currWindow

    def GetNextIO(self):
        # check if done: if so, print stats and end animation
        if self.requestCount == len(self.requestQueue):
            self.UpdateTime()
            self.PrintStats()
            self.doAnimate = False
            self.isDone = True
            return

        # do policy: should set currentBlock, 
        if self.policy == 'FIFO':
            (self.currentBlock, self.currentIndex) = self.requestQueue[self.requestCount]
            self.DoSATF(self.requestQueue[self.requestCount:self.requestCount+1])
        elif self.policy == 'SATF' or self.policy == 'BSATF':
            endIndex = self.GetWindow()
            # print '  GetWindow():', endIndex
            if endIndex > len(self.requestQueue):
                endIndex = len(self.requestQueue)
            (self.currentBlock, self.currentIndex) = self.DoSATF(self.requestQueue[0:endIndex])
        elif self.policy == 'SSTF':
            # first, find all the blocks on a given track (given window constraints)
            trackList = self.DoSSTF(self.requestQueue[0:self.GetWindow()])
            # then, do SATF on those blocks (otherwise, will not do them in obvious order)
            (self.currentBlock, self.currentIndex) = self.DoSATF(trackList)
        else:
            print('정책 (%s)은 구현되지 않았습니다' % self.policy)
            sys.exit(1)

        # once best block is decided, go ahead and do the seek
        self.PlanSeek(self.blockToTrackMap[self.currentBlock])

        # add another block?
        if len(self.lateRequests) > 0 and self.lateCount < len(self.lateRequests):
            self.AddRequest(self.lateRequests[self.lateCount])
            self.lateCount += 1

    def Animate(self):
        if self.graphics == True and self.doAnimate == False:
            self.root.after(20, self.Animate)
            return

        # timer
        self.timer += 1
        self.UpdateTime()

        # see which blocks are rotating on the disk
        # print('SELF ANGLE', self.angle)
        self.angle = self.angle + self.rotateSpeed
        if self.angle >= 360.0:
            self.angle = 0.0

        # move the blocks
        if self.graphics:
            for (track, angle, name, cid) in self.blockInfoList:
                distFromSpindle = self.tracks[track]
                na = angle - self.angle
                xc = self.spindleX + (distFromSpindle * math.cos(math.radians(na)))
                yc = self.spindleY + (distFromSpindle * math.sin(math.radians(na)))
                if self.graphics:
                    self.canvas.coords(cid, xc, yc)
                    if self.currentBlock == name:
                        sz = self.targetSize
                        self.canvas.coords(self.targetID, xc-sz, yc-sz, xc+sz, yc+sz)

        # move the arm OR wait for a rotational delay
        if self.state == STATE_SEEK:
            if self.DoneWithSeek():
                self.rotBegin   = self.timer
                self.SwitchState(STATE_ROTATE)
                self.SwitchColors('lightblue')
        if self.state == STATE_ROTATE:
            # check for read (disk arm must be settled)
            if self.DoneWithRotation():
                self.xferBegin = self.timer
                self.SwitchState(STATE_XFER)
                self.SwitchColors('green')
        if self.state == STATE_XFER:
            if self.DoneWithTransfer():
                self.DoRequestStats()
                self.SwitchState(STATE_DONE)
                self.SwitchColors('red')
                self.UpdateWindow()
                currentBlock = self.currentBlock
                self.GetNextIO()
                nextBlock = self.currentBlock
                if self.blockToTrackMap[currentBlock] == self.blockToTrackMap[nextBlock]:
                    if (currentBlock == self.tracksBeginEnd[self.armTrack][1] and nextBlock == self.tracksBeginEnd[self.armTrack][0]) or (currentBlock + 1 == nextBlock):
                        # need a special case here: to handle when we stay in transfer mode
                        (self.rotBegin, self.seekBegin, self.xferBegin) = (self.timer, self.timer, self.timer)
                        self.SwitchState(STATE_XFER)
                        self.SwitchColors('green')
                        
                        
        
        # make sure to keep the animation going!
        if self.graphics:
            self.root.after(20, self.Animate)

    def DoRequestStats(self):
        seekTime  = self.rotBegin  - self.seekBegin
        rotTime   = self.xferBegin - self.rotBegin
        xferTime  = self.timer     - self.xferBegin
        totalTime = self.timer     - self.seekBegin

        if self.compute == True:
            print('블록: %3d  탐색:%3d  회전 대기:%3d  전송:%3d  합계:%4d' % (self.currentBlock, seekTime, rotTime, xferTime, totalTime))

        # if int(totalTime) != int(self.totalEst):
        #     print 'INTERNAL ERROR: estimate was', self.totalEst, 'whereas actual time to access block was', totalTime
        #     print 'Please report this bug and as much information as possible so as to make it easy to recreate. Thanks!'

        # update stats
        self.seekTotal += seekTime
        self.rotTotal  += rotTime
        self.xferTotal += xferTime

        

    def PrintStats(self):
        if self.compute == True:
            print('\n총합        탐색:%3d  회전 대기:%3d  전송:%3d  합계:%4d\n' % (self.seekTotal, self.rotTotal, self.xferTotal, self.timer))
        
# END: class Disk


    
#
# MAIN SIMULATOR
#
parser = OptionParser()
parser.add_option('-s', '--seed',            default='0',         help='난수 시드 (같은 값으로 같은 문제 재현)',                                             action='store', type='int',    dest='seed')
parser.add_option('-a', '--addr',            default='-1',        help='요청 목록 (쉼표로 구분, -1이면 addrDesc로 생성)',     action='store', type='string', dest='addr')
parser.add_option('-A', '--addrDesc',        default='5,-1,0',    help='요청 수, 최대 요청 주소(-1: 전체 범위), 최소 요청 주소',        action='store', type='string', dest='addrDesc')
parser.add_option('-S', '--seekSpeed',       default='1',         help='헤드 탐색 속도',                                           action='store', type='string', dest='seekSpeed')
parser.add_option('-R', '--rotSpeed',        default='1',         help='디스크 회전 속도',                                       action='store', type='string', dest='rotateSpeed')
parser.add_option('-p', '--policy',          default='FIFO',      help='스케줄링 정책 (FIFO, SSTF, SATF, BSATF)',             action='store', type='string', dest='policy')
parser.add_option('-w', '--schedWindow',     default=-1,          help='스케줄링 시 살펴볼 요청 범위 (-1: 전체)',                   action='store', type='int',    dest='window')
parser.add_option('-o', '--skewOffset',      default=0,           help='트랙 간 시작 위치 차이 (블록 단위)',                              action='store', type='int',    dest='skew')
parser.add_option('-z', '--zoning',          default='30,30,30',  help='바깥/중간/안쪽 트랙의 블록 사이 각도',      action='store', type='string', dest='zoning')
parser.add_option('-G', '--graphics',        default=False,       help='그래픽 화면 표시',                                        action='store_true',           dest='graphics')
parser.add_option('-l', '--lateAddr',        default='-1',        help='나중에 도착하는 요청 목록 (쉼표 구분, -1: 임의 생성)',     action='store', type='string', dest='lateAddr')
parser.add_option('-L', '--lateAddrDesc',    default='0,-1,0',    help='요청 수, 최대 요청 주소(-1: 전체 범위), 최소 요청 주소',        action='store', type='string', dest='lateAddrDesc')
parser.add_option('-c', '--compute',         default=False,       help='정답과 계산 결과 표시',                                     action='store_true',           dest='compute')
(options, args) = parser.parse_args()

print('설정 난수 시드 (seed)', options.seed)
print('설정 요청 주소 (addr)', options.addr)
print('설정 요청 생성 설정 (addrDesc)', options.addrDesc)
print('설정 탐색 속도 (seekSpeed)', options.seekSpeed)
print('설정 회전 속도 (rotateSpeed)', options.rotateSpeed)
print('설정 트랙 간 시작 위치 차이 (skew)', options.skew)
print('설정 스케줄링 요청 범위 (window)', options.window)
print('설정 정책 (policy)', options.policy)
print('설정 정답 표시 (compute)', options.compute)
print('설정 그래픽 표시 (graphics)', options.graphics)
print('설정 트랙별 블록 간 각도 (zoning)', options.zoning)
print('설정 나중에 도착할 요청 (lateAddr)', options.lateAddr)
print('설정 추가 요청 생성 설정 (lateAddrDesc)', options.lateAddrDesc)
print('')

if options.window == 0:
    print('스케줄링 범위 (%d)는 양수 또는 -1(전체)이어야 합니다' % options.window)
    sys.exit(1)

if options.graphics and options.compute == False:
    print('\n알림: 그래픽 모드에서는 정답 계산이 자동으로 켜집니다\n')
    options.compute = True

# set up simulator info
d = Disk(addr=options.addr, addrDesc=options.addrDesc, lateAddr=options.lateAddr, lateAddrDesc=options.lateAddrDesc,
         policy=options.policy, seekSpeed=float(options.seekSpeed), rotateSpeed=float(options.rotateSpeed),
         skew=options.skew, window=options.window, compute=options.compute, graphics=options.graphics, zoning=options.zoning)

# run simulation
d.Go()

# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 탐색(Seek)은 헤드가 목표 트랙으로 움직이는 시간, 회전 대기(Rotate)는 목표 블록이 헤드 아래로 올 때까지의 시간입니다.
  - 전송(Transfer)은 블록을 읽거나 쓰는 시간이며, 요청별 합계는 이 세 시간의 합입니다. 블록 번호는 데이터의 위치를 나타냅니다.
  - FIFO는 요청 순서, SSTF는 가까운 트랙 우선, SATF는 접근 시간이 짧은 요청 우선입니다. 탐색만 줄이는 것과 전체 시간을 줄이는 것은 다릅니다.
  - 초기 배치에서 이름 없이 나오는 세 숫자는 트랙 번호·블록 간 각도·블록 번호입니다. 네 숫자이면 트랙 번호 뒤에 시작 위치 차이(skew)가 포함됩니다.
""")
