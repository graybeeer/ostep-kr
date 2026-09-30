#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
from optparse import OptionParser
import random

# to make Python2 and Python3 act the same -- how dumb
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

# finds the highest nonempty queue
# -1 if they are all empty
def FindQueue():
    q = hiQueue
    while q > 0:
        if len(queue[q]) > 0:
            return q
        q -= 1
    if len(queue[0]) > 0:
        return 0
    return -1

def Abort(str):
    sys.stderr.write(str + '\n')
    exit(1)


#
# PARSE ARGUMENTS
#

parser = OptionParser()
parser.add_option('-s', '--seed', help='난수 시드 (같은 값으로 같은 문제 재현)',
                  default=0, action='store', type='int', dest='seed')
parser.add_option('-n', '--numQueues',
                  help='MLFQ 큐 개수 (-Q를 사용하지 않을 때)',
                  default=3, action='store', type='int', dest='numQueues')
parser.add_option('-q', '--quantum', help='타임 슬라이스 길이 (-Q를 사용하지 않을 때)',
                  default=10, action='store', type='int', dest='quantum')
parser.add_option('-a', '--allotment', help='우선순위별 허용 타임 슬라이스 수 (-A를 사용하지 않을 때)',
                  default=1, action='store', type='int', dest='allotment')
parser.add_option('-Q', '--quantumList',
                  help='큐별 타임 슬라이스 길이: ' + \
                  'x,y,z,... (x는 최고 우선순위 큐의 길이, ' + \
                  'y는 그다음 큐의 값, 이하 같은 순서)',
                  default='', action='store', type='string', dest='quantumList')
parser.add_option('-A', '--allotmentList',
                  help='큐별 허용 타임 슬라이스 수: ' + \
                  'x,y,z,... (x는 최고 우선순위 큐의 허용 횟수, ' + \
                  'y는 그다음 큐의 값, 이하 같은 순서)',
                  default='', action='store', type='string', dest='allotmentList')
parser.add_option('-j', '--numJobs', default=3, help='시스템의 작업 수',
                  action='store', type='int', dest='numJobs')
parser.add_option('-m', '--maxlen', default=100, help='작업의 최대 실행 시간 ' +
                  '(임의 생성 시)', action='store', type='int',
                  dest='maxlen')
parser.add_option('-M', '--maxio', default=10,
                  help='임의 생성 작업의 최대 I/O 요청 간격',
                  action='store', type='int', dest='maxio')
parser.add_option('-B', '--boost', default=0,
                  help='모든 작업의 우선순위를 올리는 주기: ' +
                  '최고 우선순위로 복귀', action='store', type='int', dest='boost')
parser.add_option('-i', '--iotime', default=5,
                  help='I/O 하나에 걸리는 고정 시간',
                  action='store', type='int', dest='ioTime')
parser.add_option('-S', '--stay', default=False,
                  help='I/O 요청 시 할당량을 초기화하고 현재 우선순위 유지',
                  action='store_true', dest='stay')
parser.add_option('-I', '--iobump', default=False,
                  help='I/O 완료 작업을 즉시 이동: ' + \
                  '현재 큐의 맨 앞에 배치',
                  action='store_true', dest='iobump')
parser.add_option('-l', '--jlist', default='',
                  help='작업 목록 형식: ' + \
                  'x1,y1,z1:x2,y2,z2:... (x는 도착 시각, y는 CPU 실행 ' + \
                  '시간, z는 I/O 요청 간격)',
                  action='store', type='string', dest='jlist')
parser.add_option('-c', help='정답과 계산 결과 표시', action='store_true',
                  default=False, dest='solve')

(options, args) = parser.parse_args()

random.seed(options.seed)

# MLFQ: How Many Queues
numQueues = options.numQueues

quantum = {}
if options.quantumList != '':
    # instead, extract number of queues and their time slic
    quantumLengths = options.quantumList.split(',')
    numQueues = len(quantumLengths)
    qc = numQueues - 1
    for i in range(numQueues):
        quantum[qc] = int(quantumLengths[i])
        qc -= 1
else:
    for i in range(numQueues):
        quantum[i] = int(options.quantum)

allotment = {}
if options.allotmentList != '':
    allotmentLengths = options.allotmentList.split(',')
    if numQueues != len(allotmentLengths):
        print('할당량 개수와 타임 슬라이스 개수가 같아야 합니다')
        exit(1)
    qc = numQueues - 1
    for i in range(numQueues):
        allotment[qc] = int(allotmentLengths[i])
        if qc != 0 and allotment[qc] <= 0:
            print('할당량은 양의 정수여야 합니다')
            exit(1)
        qc -= 1
else:
    for i in range(numQueues):
        allotment[i] = int(options.allotment)

hiQueue = numQueues - 1

# MLFQ: I/O Model
# the time for each IO: not great to have a single fixed time but...
ioTime = int(options.ioTime)

# This tracks when IOs and other interrupts are complete
ioDone = {}

# This stores all info about the jobs
job = {}

# seed the random generator
random_seed(options.seed)

# jlist 'startTime,runTime,ioFreq:startTime,runTime,ioFreq:...'
jobCnt = 0
if options.jlist != '':
    allJobs = options.jlist.split(':')
    for j in allJobs:
        jobInfo = j.split(',')
        if len(jobInfo) != 3:
            print('작업 형식 오류: x1,y1,z1:x2,y2,z2:... 형식을 사용하세요')
            print('x는 도착 시각, y는 CPU 실행 시간, z는 I/O 요청 간격입니다.')
            exit(1)
        assert(len(jobInfo) == 3)
        startTime = int(jobInfo[0])
        runTime   = int(jobInfo[1])
        ioFreq    = int(jobInfo[2])
        job[jobCnt] = {'currPri':hiQueue, 'ticksLeft':quantum[hiQueue],
                       'allotLeft':allotment[hiQueue], 'startTime':startTime,
                       'runTime':runTime, 'timeLeft':runTime, 'ioFreq':ioFreq, 'doingIO':False,
                       'firstRun':-1}
        if startTime not in ioDone:
            ioDone[startTime] = []
        ioDone[startTime].append((jobCnt, 'JOB BEGINS'))
        jobCnt += 1
else:
    # do something random
    for j in range(options.numJobs):
        startTime = 0
        runTime   = int(random.random() * (options.maxlen - 1) + 1)
        ioFreq    = int(random.random() * (options.maxio - 1) + 1)
        
        job[jobCnt] = {'currPri':hiQueue, 'ticksLeft':quantum[hiQueue],
                       'allotLeft':allotment[hiQueue], 'startTime':startTime,
                       'runTime':runTime, 'timeLeft':runTime, 'ioFreq':ioFreq, 'doingIO':False,
                       'firstRun':-1}
        if startTime not in ioDone:
            ioDone[startTime] = []
        ioDone[startTime].append((jobCnt, 'JOB BEGINS'))
        jobCnt += 1


numJobs = len(job)

print('입력 설정:')
print('설정 작업 수 (jobs)',            numJobs)
print('설정 큐 수 (queues)',          numQueues)
for i in range(len(quantum)-1,-1,-1):
    print('설정: 큐 %2d의 허용 타임 슬라이스 수 %3d' % (i, allotment[i]))
    print('설정: 큐 %2d의 타임 슬라이스 길이 %3d' % (i, quantum[i]))
print('설정 우선순위 상향 주기 (boost)',           options.boost)
print('설정 I/O 소요 시간 (ioTime)',          options.ioTime)
print('설정 I/O 후 우선순위 유지 (stayAfterIO)',     options.stay)
print('설정 I/O 완료 후 큐 맨 앞으로 이동 (iobump)',          options.iobump)

print('\n')
print('각 작업에는 다음 세 가지 값이 주어집니다:')
print('  도착 시각(startTime): 작업이 시스템에 들어오는 시각')
print('  실행 시간(runTime): 완료까지 필요한 CPU 시간의 합')
print('  I/O 간격(ioFreq): 이만큼 CPU를 사용하면 I/O 요청')
print('              (각 I/O는 ioTime만큼 걸립니다)\n')

print('작업 목록:')
for i in range(numJobs):
    print('  작업 %2d: 도착 시각 %3d - 실행 시간 %3d - I/O 간격 %3d' % (i, job[i]['startTime'], job[i]['runTime'], job[i]['ioFreq']))
print('')

print("""
[각주: 출력 읽는 법]
  - 큐 번호가 클수록 우선순위가 높습니다. 남은 퀀텀(TICKS)은 현재 타임 슬라이스의 남은 시간입니다.
  - 할당량(ALLOT)은 현재 우선순위에서 쓸 수 있는 남은 타임 슬라이스 수입니다. 남은 실행(TIME)은 작업이 더 사용해야 하는 CPU 시간입니다.
  - JOB BEGINS는 작업 도착, IO_DONE은 I/O 완료입니다. 별도 시각 없이 나오는 I/O 완료 예약 문구는 미래 완료 이벤트를 등록했다는 뜻입니다.
  - 응답 시간은 첫 실행 시각 - 도착 시각, 반환 시간은 완료 시각 - 도착 시각입니다. I/O 대기와 우선순위 상향이 이 값에 미치는 영향을 보세요.
""")

if options.solve == False:
    print('주어진 작업들의 실행 흐름을 계산하세요.')
    print('각 작업의 응답 시간과 반환 시간도')
    print('함께 계산해 보세요.')
    print('')
    print('계산 후 -c 옵션으로 정답을 확인하세요.\n')
    exit(0)

# initialize the MLFQ queues
queue = {}
for q in range(numQueues):
    queue[q] = []

# TIME IS CENTRAL
currTime = 0

# use these to know when we're finished
totalJobs    = len(job)
finishedJobs = 0

print('\n실행 흐름:\n')

while finishedJobs < totalJobs:
    # find highest priority job
    # run it until either
    # (a) the job uses up its time quantum
    # (b) the job performs an I/O

    # check for priority boost
    if options.boost > 0 and currTime != 0:
        if currTime % options.boost == 0:
            print('[ 시각 %d ] 우선순위 상향 ( 주기 %d )' % (currTime, options.boost))
            # remove all jobs from queues (except high queue) and put them in high queue
            for q in range(numQueues-1):
                for j in queue[q]:
                    if job[j]['doingIO'] == False:
                        queue[hiQueue].append(j)
                queue[q] = []

            # change priority to high priority
            # reset number of ticks left for all jobs (just for lower jobs?)
            # add to highest run queue (if not doing I/O)
            for j in range(numJobs):
                # print('-> Boost %d (timeLeft %d)' % (j, job[j]['timeLeft']))
                if job[j]['timeLeft'] > 0:
                    # print('-> FinalBoost %d (timeLeft %d)' % (j, job[j]['timeLeft']))
                    job[j]['currPri']   = hiQueue
                    job[j]['ticksLeft'] = quantum[hiQueue]
                    job[j]['allotLeft'] = allotment[hiQueue]
                    # print('  BOOST', j, ' ticks:', job[j]['ticksLeft'], ' allot:', job[j]['allotLeft'])
            # print('BOOST END: QUEUES look like:', queue)

    # check for any I/Os done
    if currTime in ioDone:
        for (j, type) in ioDone[currTime]:
            q = job[j]['currPri']
            job[j]['doingIO'] = False
            print('[ 시각 %d ] %s, 작업 %d' % (currTime, type, j))
            if options.iobump == False or type == 'JOB BEGINS':
                queue[q].append(j)
            else:
                queue[q].insert(0, j)

    # now find the highest priority job
    currQueue = FindQueue()
    if currQueue == -1:
        print('[ 시각 %d ] 유휴 (실행할 작업 없음)' % (currTime))
        currTime += 1
        continue
            
    # there was at least one runnable job, and hence ...
    currJob = queue[currQueue][0]
    if job[currJob]['currPri'] != currQueue:
        Abort('현재 우선순위[%d]와 현재 큐[%d]가 일치하지 않습니다' % (job[currJob]['currPri'], currQueue))

    job[currJob]['timeLeft']  -= 1
    job[currJob]['ticksLeft'] -= 1

    if job[currJob]['firstRun'] == -1:
        job[currJob]['firstRun'] = currTime

    runTime   = job[currJob]['runTime']
    ioFreq    = job[currJob]['ioFreq']
    ticksLeft = job[currJob]['ticksLeft']
    allotLeft = job[currJob]['allotLeft']
    timeLeft  = job[currJob]['timeLeft']

    print('[ 시각 %d ] 작업 %d 실행, 우선순위 %d [ 남은 퀀텀 %d 할당량 %d 남은 실행 %d (전체 %d) ]' % \
          (currTime, currJob, currQueue, ticksLeft, allotLeft, timeLeft, runTime))

    if timeLeft < 0:
        Abort('오류: 남은 실행 시간은 0보다 작을 수 없습니다')


    # UPDATE TIME
    currTime += 1

    # CHECK FOR JOB ENDING
    if timeLeft == 0:
        print('[ 시각 %d ] 작업 %d 완료' % (currTime, currJob))
        finishedJobs += 1
        job[currJob]['endTime'] = currTime
        # print('BEFORE POP', queue)
        done = queue[currQueue].pop(0)
        # print('AFTER POP', queue)
        assert(done == currJob)
        continue

    # CHECK FOR IO
    issuedIO = False
    if ioFreq > 0 and (((runTime - timeLeft) % ioFreq) == 0):
        # time for an IO!
        print('[ 시각 %d ] 작업 %d의 I/O 시작' % (currTime, currJob))
        issuedIO = True
        desched = queue[currQueue].pop(0)
        assert(desched == currJob)
        job[currJob]['doingIO'] = True
        # this does the bad rule -- reset your time at this level if you do I/O
        if options.stay == True:
            job[currJob]['ticksLeft'] = quantum[currQueue]
            job[currJob]['allotLeft'] = allotment[currQueue]
        # add to IO Queue: but which queue?
        futureTime = currTime + ioTime
        if futureTime not in ioDone:
            ioDone[futureTime] = []
        print('I/O 완료 예약')
        ioDone[futureTime].append((currJob, 'IO_DONE'))
        
    # CHECK FOR QUANTUM ENDING AT THIS LEVEL (BUT REMEMBER, THERE STILL MAY BE ALLOTMENT LEFT)
    if ticksLeft == 0:
        if issuedIO == False:
            # IO HAS NOT BEEN ISSUED (therefor pop from queue)'
            desched = queue[currQueue].pop(0)
        assert(desched == currJob)

        job[currJob]['allotLeft'] = job[currJob]['allotLeft'] - 1

        if job[currJob]['allotLeft'] == 0:
            # this job is DONE at this level, so move on
            if currQueue > 0:
                # in this case, have to change the priority of the job
                job[currJob]['currPri']   = currQueue - 1
                job[currJob]['ticksLeft'] = quantum[currQueue-1]
                job[currJob]['allotLeft'] = allotment[currQueue-1]
                if issuedIO == False:
                    queue[currQueue-1].append(currJob)
            else:
                job[currJob]['ticksLeft'] = quantum[currQueue]
                job[currJob]['allotLeft'] = allotment[currQueue]
                if issuedIO == False:
                    queue[currQueue].append(currJob)
        else:
            # this job has more time at this level, so just push it to end
            job[currJob]['ticksLeft'] = quantum[currQueue]
            if issuedIO == False:
                queue[currQueue].append(currJob)

        


# print out statistics
print('')
print('최종 통계:')
responseSum   = 0
turnaroundSum = 0
for i in range(numJobs):
    response   = job[i]['firstRun'] - job[i]['startTime']
    turnaround = job[i]['endTime'] - job[i]['startTime']
    print('  작업 %2d: 도착 시각 %3d - 응답 시간 %3d - 반환 시간 %3d' % (i, job[i]['startTime'], response, turnaround))
    responseSum   += response
    turnaroundSum += turnaround

print('\n  평균 (%2d개): 도착 시각 해당 없음 - 응답 시간 %.2f - 반환 시간 %.2f' % (i, float(responseSum)/numJobs, float(turnaroundSum)/numJobs))
print('\n')
