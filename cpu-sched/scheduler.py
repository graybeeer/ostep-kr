#! /usr/bin/env python3
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

parser = OptionParser()
parser.add_option("-s", "--seed", default=0, help='난수 시드 (같은 값으로 같은 문제 재현)', action="store", type="int", dest="seed")
parser.add_option("-j", "--jobs", default=3, help='시스템의 작업 수', action="store", type="int", dest="jobs")
parser.add_option("-l", "--jlist", default="", help='임의 생성 대신 실행 시간 목록을 쉼표로 구분하여 지정', action="store", type="string", dest="jlist")
parser.add_option("-m", "--maxlen", default=10, help='작업의 최대 실행 시간', action="store", type="int", dest="maxlen")
parser.add_option("-p", "--policy", default="FIFO", help='스케줄링 정책: SJF (짧은 작업 우선), FIFO (입력 순서), RR (순환 실행)', action="store", type="string", dest="policy")
parser.add_option("-q", "--quantum", help='RR 정책의 타임 슬라이스 길이', default=1, action="store", type="int", dest="quantum")
parser.add_option("-c", help='정답과 계산 결과 표시', action="store_true", default=False, dest="solve")

(options, args) = parser.parse_args()

random_seed(options.seed)

print('설정 정책 (policy)', options.policy)
if options.jlist == '':
    print('설정 작업 수 (jobs)', options.jobs)
    print('설정 최대 실행 시간 (maxlen)', options.maxlen)
    print('설정 난수 시드 (seed)', options.seed)
else:
    print('설정 작업 목록 (jlist)', options.jlist)
print('')

print('각 작업과 필요한 실행 시간: ')

import operator

joblist = []
if options.jlist == '':
    for jobnum in range(0,options.jobs):
        runtime = int(options.maxlen * random.random()) + 1
        joblist.append([jobnum, runtime])
        print('  작업', jobnum, '( 실행 시간 = ' + str(runtime) + ' )')
else:
    jobnum = 0
    for runtime in options.jlist.split(','):
        joblist.append([jobnum, float(runtime)])
        jobnum += 1
    for job in joblist:
        print('  작업', job[0], '( 실행 시간 = ' + str(job[1]) + ' )')
print('\n')

if options.solve == True:
    print('** 정답 **\n')
    if options.policy == 'SJF':
        joblist = sorted(joblist, key=operator.itemgetter(1))
        options.policy = 'FIFO'
    
    if options.policy == 'FIFO':
        thetime = 0
        print('실행 흐름:')
        for job in joblist:
            print('  [ 시각 %3d ] 작업 %d: %.2f초 실행 ( 완료 시각 %.2f )' % (thetime, job[0], job[1], thetime + job[1]))
            thetime += job[1]

        print('\n최종 통계:')
        t     = 0.0
        count = 0
        turnaroundSum = 0.0
        waitSum       = 0.0
        responseSum   = 0.0
        for tmp in joblist:
            jobnum  = tmp[0]
            runtime = tmp[1]
            
            response   = t
            turnaround = t + runtime
            wait       = t
            print('  작업 %3d -- 응답 시간: %3.2f  반환 시간: %3.2f  대기 시간: %3.2f' % (jobnum, response, turnaround, wait))
            responseSum   += response
            turnaroundSum += turnaround
            waitSum       += wait
            t += runtime
            count = count + 1
        print('\n  평균 -- 응답 시간: %3.2f  반환 시간: %3.2f  대기 시간: %3.2f\n' % (responseSum/count, turnaroundSum/count, waitSum/count))
                     
    if options.policy == 'RR':
        print('실행 흐름:')
        turnaround = {}
        response = {}
        lastran = {}
        wait = {}
        quantum  = float(options.quantum)
        jobcount = len(joblist)
        for i in range(0,jobcount):
            lastran[i] = 0.0
            wait[i] = 0.0
            turnaround[i] = 0.0
            response[i] = -1

        runlist = []
        for e in joblist:
            runlist.append(e)

        thetime  = 0.0
        while jobcount > 0:
            job = runlist.pop(0)
            jobnum  = job[0]
            runtime = float(job[1])
            if response[jobnum] == -1:
                response[jobnum] = thetime
            currwait = thetime - lastran[jobnum]
            wait[jobnum] += currwait
            if runtime > quantum:
                runtime -= quantum
                ranfor = quantum
                print('  [ 시각 %3d ] 작업 %3d: %.2f초 실행' % (thetime, jobnum, ranfor))
                runlist.append([jobnum, runtime])
            else:
                ranfor = runtime;
                print('  [ 시각 %3d ] 작업 %3d: %.2f초 실행 ( 완료 시각 %.2f )' % (thetime, jobnum, ranfor, thetime + ranfor))
                turnaround[jobnum] = thetime + ranfor
                jobcount -= 1
            thetime += ranfor
            lastran[jobnum] = thetime

        print('\n최종 통계:')
        turnaroundSum = 0.0
        waitSum       = 0.0
        responseSum   = 0.0
        for i in range(0,len(joblist)):
            turnaroundSum += turnaround[i]
            responseSum += response[i]
            waitSum += wait[i]
            print('  작업 %3d -- 응답 시간: %3.2f  반환 시간: %3.2f  대기 시간: %3.2f' % (i, response[i], turnaround[i], wait[i]))
        count = len(joblist)
        
        print('\n  평균 -- 응답 시간: %3.2f  반환 시간: %3.2f  대기 시간: %3.2f\n' % (responseSum/count, turnaroundSum/count, waitSum/count))

    if options.policy != 'FIFO' and options.policy != 'SJF' and options.policy != 'RR': 
        print('오류: 스케줄링 정책', options.policy, '은(는) 지원하지 않습니다.')
        sys.exit(0)
else:
    print('각 작업의 반환 시간, 응답 시간, 대기 시간을 계산하세요.')
    print('계산한 다음 같은 실행 옵션에 -c를 추가하여 다시 실행하면')
    print('정답을 확인할 수 있습니다. 다른 문제를 만들려면')
    print('-s <정수>로 시드를 바꾸거나 실행 시간 목록(예: -l 10,15,20)을')
    print('직접 지정하세요.')
    print('')

# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 응답 시간(Response): 도착부터 CPU에서 처음 실행되기까지의 시간입니다.
  - 반환 시간(Turnaround): 도착부터 완료까지의 시간입니다. 대기 시간(Wait): 실행 준비 상태로 CPU를 기다린 시간의 합입니다.
  - 이 시뮬레이터의 작업은 모두 시각 0에 도착합니다. 같은 작업 목록에서 정책별 평균과 각 작업의 대기 시간을 비교하세요.
  - FIFO는 입력 순서, SJF는 짧은 작업 우선, RR은 정해진 퀀텀만큼 돌아가며 실행합니다. 퀀텀이 짧다고 모든 지표가 좋아지는 것은 아닙니다.
""")
