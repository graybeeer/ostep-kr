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

parser = OptionParser()
parser.add_option('-s', '--seed', default=0, help='난수 시드 (같은 값으로 같은 문제 재현)',              action='store', type='int', dest='seed')
parser.add_option('-j', '--jobs', default=3, help='시스템의 작업 수', action='store', type='int', dest='jobs')
parser.add_option('-l', '--jlist', default='', help='실행시간:추첨권수 목록 지정 (예: 10:100,20:100은 실행 시간 10과 20, 추첨권 각 100장인 두 작업)',  action='store', type='string', dest='jlist')
parser.add_option('-m', '--maxlen',  default=10,  help='작업의 최대 실행 시간',         action='store', type='int', dest='maxlen')
parser.add_option('-T', '--maxticket', default=100, help='임의 생성 시 작업당 최대 추첨권 수',          action='store', type='int', dest='maxticket')
parser.add_option('-q', '--quantum', default=1,   help='타임 슬라이스 길이', action='store', type='int', dest='quantum')
parser.add_option('-c', '--compute', help='정답과 계산 결과 표시', action='store_true', default=False, dest='solve')

(options, args) = parser.parse_args()

random_seed(options.seed)

print('설정 작업 목록 (jlist)', options.jlist)
print('설정 작업 수 (jobs)', options.jobs)
print('설정 최대 실행 시간 (maxlen)', options.maxlen)
print('설정 최대 추첨권 수 (maxticket)', options.maxticket)
print('설정 타임 슬라이스 길이 (quantum)', options.quantum)
print('설정 난수 시드 (seed)', options.seed)
print('')

print('각 작업과 필요한 실행 시간: ')

import operator


tickTotal = 0
runTotal  = 0
joblist = []
if options.jlist == '':
    for jobnum in range(0,options.jobs):
        runtime = 0
        while runtime == 0:
            runtime = int(options.maxlen * random.random())
        tickets = 0
        while tickets == 0:
            tickets = int(options.maxticket * random.random())
        runTotal += runtime
        tickTotal += tickets
        joblist.append([jobnum, runtime, tickets])
        print('  작업 %d ( 실행 시간 = %d, 추첨권 수 = %d )' % (jobnum, runtime, tickets))
else:
    jobnum = 0
    for entry in options.jlist.split(','):
        (runtime, tickets) = entry.split(':')
        joblist.append([jobnum, int(runtime), int(tickets)])
        runTotal += int(runtime)
        tickTotal += int(tickets)
        jobnum += 1
    for job in joblist:
        print('  작업 %d ( 실행 시간 = %d, 추첨권 수 = %d )' % (job[0], job[1], job[2]))
print('\n')

if options.solve == False:
    print('추첨 계산에 사용할 난수 목록 (필요한 만큼 사용):')
    for i in range(runTotal):
        r = int(random.random() * 1000001)
        print('난수', r)

if options.solve == True:
    print('** 정답 **\n')

    jobs  = len(joblist)
    clock = 0
    for i in range(runTotal):
        r = int(random.random() * 1000001)
        winner = int(r % tickTotal)

        current = 0
        for (job, runtime, tickets) in joblist:
            current += tickets
            if current > winner:
                (wjob, wrun, wtix) = (job, runtime, tickets)
                break

        print('난수', r, '-> 당첨 추첨권 %d (전체 %d장) -> 작업 %d 실행' % (winner, tickTotal, wjob))
        # print('Winning ticket %d (of %d) -> Run %d' % (winner, tickTotal, wjob))

        print('  작업 목록:',)
        for (job, runtime, tickets) in joblist:
            if wjob == job:
                wstr = '*'
            else:
                wstr = ' '

            if runtime > 0:
                tstr = tickets
            else:
                tstr = '---'
            print(' (%s 작업:%d 남은 시간:%d 추첨권:%s ) ' % (wstr, job, runtime, tstr), end='')
        print('')

        # now do the accounting
        if wrun >= options.quantum:
            wrun -= options.quantum
        else:
            wrun = 0

        clock += options.quantum

        # job completed!
        if wrun == 0:
            print('--> 작업 %d 완료, 완료 시각 %d' % (wjob, clock))
            tickTotal -= wtix
            wtix = 0
            jobs -= 1

        # update job list
        joblist[wjob] = (wjob, wrun, wtix)

        if jobs == 0:
            print('')
            break





# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 추첨권(tickets)이 많을수록 CPU를 배정받을 확률이 높습니다. 당첨 번호는 난수를 현재 전체 추첨권 수로 나눈 나머지입니다.
  - timeleft는 남은 CPU 실행 시간입니다. 완료된 작업의 추첨권은 다음 추첨에서 제외됩니다.
  - 추첨권 비율은 장기적인 배분 비율입니다. 짧은 실행에서는 무작위 변동으로 비율이 정확히 맞지 않을 수 있습니다.
""")
