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

# process switch behavior
SCHED_SWITCH_ON_IO = 'SWITCH_ON_IO'
SCHED_SWITCH_ON_END = 'SWITCH_ON_END'

# io finished behavior
IO_RUN_LATER = 'IO_RUN_LATER'
IO_RUN_IMMEDIATE = 'IO_RUN_IMMEDIATE'

# process states
STATE_RUNNING = 'RUNNING'
STATE_READY = 'READY'
STATE_DONE = 'DONE'
STATE_WAIT = 'BLOCKED'

# members of process structure
PROC_CODE = 'code_'
PROC_PC = 'pc_'
PROC_ID = 'pid_'
PROC_STATE = 'proc_state_'

# things a process can do
DO_COMPUTE = 'cpu'
DO_IO = 'io'
DO_IO_DONE = 'io_done'


class scheduler:
    def __init__(self, process_switch_behavior, io_done_behavior, io_length):
        # keep set of instructions for each of the processes
        self.proc_info = {}
        self.process_switch_behavior = process_switch_behavior
        self.io_done_behavior = io_done_behavior
        self.io_length = io_length
        return

    def new_process(self):
        proc_id = len(self.proc_info)
        self.proc_info[proc_id] = {}
        self.proc_info[proc_id][PROC_PC] = 0
        self.proc_info[proc_id][PROC_ID] = proc_id
        self.proc_info[proc_id][PROC_CODE] = []
        self.proc_info[proc_id][PROC_STATE] = STATE_READY
        return proc_id

    # program looks like this:
    #   c7,i,c1,i
    # which means
    #   compute for 7, then i/o, then compute for 1, then i/o
    def load_program(self, program):
        proc_id = self.new_process()
        for line in program.split(','):
            opcode = line[0]
            if opcode == 'c': # compute
                num = int(line[1:])
                for i in range(num):
                    self.proc_info[proc_id][PROC_CODE].append(DO_COMPUTE)
            elif opcode == 'i':
                self.proc_info[proc_id][PROC_CODE].append(DO_IO)
                # add one compute to HANDLE the I/O completion
                self.proc_info[proc_id][PROC_CODE].append(DO_IO_DONE)
            else:
                print('잘못된 명령 %s (c 또는 i여야 함)' % opcode)
                exit(1)
        return

    def load(self, program_description):
        proc_id = self.new_process()
        tmp = program_description.split(':')
        if len(tmp) != 2:
            print('잘못된 설정 (%s): 숫자 <x:y> 형식이어야 합니다' % program_description)
            print('  X는 명령어 수입니다')
            print('  Y는 명령어가 I/O 대신 CPU를 사용하는 확률(백분율)입니다')
            exit(1)

        num_instructions, chance_cpu = int(tmp[0]), float(tmp[1])/100.0
        for i in range(num_instructions):
            if random.random() < chance_cpu:
                self.proc_info[proc_id][PROC_CODE].append(DO_COMPUTE)
            else:
                self.proc_info[proc_id][PROC_CODE].append(DO_IO)
                # add one compute to HANDLE the I/O completion
                self.proc_info[proc_id][PROC_CODE].append(DO_IO_DONE)
        return

    def move_to_ready(self, expected, pid=-1):
        if pid == -1:
            pid = self.curr_proc
        assert(self.proc_info[pid][PROC_STATE] == expected)
        self.proc_info[pid][PROC_STATE] = STATE_READY
        return

    def move_to_wait(self, expected):
        assert(self.proc_info[self.curr_proc][PROC_STATE] == expected)
        self.proc_info[self.curr_proc][PROC_STATE] = STATE_WAIT
        return

    def move_to_running(self, expected):
        assert(self.proc_info[self.curr_proc][PROC_STATE] == expected)
        self.proc_info[self.curr_proc][PROC_STATE] = STATE_RUNNING
        return

    def move_to_done(self, expected):
        assert(self.proc_info[self.curr_proc][PROC_STATE] == expected)
        self.proc_info[self.curr_proc][PROC_STATE] = STATE_DONE
        return

    def next_proc(self, pid=-1):
        if pid != -1:
            self.curr_proc = pid
            self.move_to_running(STATE_READY)
            return
        for pid in range(self.curr_proc + 1, len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] == STATE_READY:
                self.curr_proc = pid
                self.move_to_running(STATE_READY)
                return
        for pid in range(0, self.curr_proc + 1):
            if self.proc_info[pid][PROC_STATE] == STATE_READY:
                self.curr_proc = pid
                self.move_to_running(STATE_READY)
                return
        return

    def get_num_processes(self):
        return len(self.proc_info)

    def get_num_instructions(self, pid):
        return len(self.proc_info[pid][PROC_CODE])

    def get_instruction(self, pid, index):
        return self.proc_info[pid][PROC_CODE][index]

    def get_num_active(self):
        num_active = 0
        for pid in range(len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] != STATE_DONE:
                num_active += 1
        return num_active

    def get_num_runnable(self):
        num_active = 0
        for pid in range(len(self.proc_info)):
            if self.proc_info[pid][PROC_STATE] == STATE_READY or \
                   self.proc_info[pid][PROC_STATE] == STATE_RUNNING:
                num_active += 1
        return num_active

    def get_ios_in_flight(self, current_time):
        num_in_flight = 0
        for pid in range(len(self.proc_info)):
            for t in self.io_finish_times[pid]:
                if t > current_time:
                    num_in_flight += 1
        return num_in_flight

    def check_for_switch(self):
        return

    def space(self, num_columns):
        for i in range(num_columns):
            print('%10s' % ' ', end='')

    def check_if_done(self):
        if len(self.proc_info[self.curr_proc][PROC_CODE]) == 0:
            if self.proc_info[self.curr_proc][PROC_STATE] == STATE_RUNNING:
                self.move_to_done(STATE_RUNNING)
                self.next_proc()
        return

    def run(self):
        clock_tick = 0

        if len(self.proc_info) == 0:
            return

        # track outstanding IOs, per process
        self.io_finish_times = {}
        for pid in range(len(self.proc_info)):
            self.io_finish_times[pid] = []

        # make first one active
        self.curr_proc = 0
        self.move_to_running(STATE_READY)

        # OUTPUT: headers for each column
        print('%s' % '시각', end='')
        for pid in range(len(self.proc_info)):
            print('%14s' % ('PID:%2d' % (pid)), end='')
        print('%14s' % 'CPU', end='')
        print('%14s' % 'I/O', end='')
        print('')

        # init statistics
        io_busy = 0
        cpu_busy = 0

        while self.get_num_active() > 0:
            clock_tick += 1

            # check for io finish
            io_done = False
            for pid in range(len(self.proc_info)):
                if clock_tick in self.io_finish_times[pid]:
                    io_done = True
                    self.move_to_ready(STATE_WAIT, pid)
                    if self.io_done_behavior == IO_RUN_IMMEDIATE:
                        # IO_RUN_IMMEDIATE
                        if self.curr_proc != pid:
                            if self.proc_info[self.curr_proc][PROC_STATE] == STATE_RUNNING:
                                self.move_to_ready(STATE_RUNNING)
                        self.next_proc(pid)
                    else:
                        # IO_RUN_LATER
                        if self.process_switch_behavior == SCHED_SWITCH_ON_END and self.get_num_runnable() > 1:
                            # this means the process that issued the io should be run
                            self.next_proc(pid)
                        if self.get_num_runnable() == 1:
                            # this is the only thing to run: so run it
                            self.next_proc(pid)
                    self.check_if_done()
            
            # if current proc is RUNNING and has an instruction, execute it
            instruction_to_execute = ''
            if self.proc_info[self.curr_proc][PROC_STATE] == STATE_RUNNING and \
                   len(self.proc_info[self.curr_proc][PROC_CODE]) > 0:
                instruction_to_execute = self.proc_info[self.curr_proc][PROC_CODE].pop(0)
                cpu_busy += 1

            # OUTPUT: print what everyone is up to
            if io_done:
                print('%3d*' % clock_tick, end='')
            else:
                print('%3d ' % clock_tick, end='')
            for pid in range(len(self.proc_info)):
                if pid == self.curr_proc and instruction_to_execute != '':
                    print('%14s' % ('RUN:'+instruction_to_execute), end='')
                else:
                    print('%14s' % (self.proc_info[pid][PROC_STATE]), end='')

            # CPU output here: if no instruction executes, output a space, otherwise a 1 
            if instruction_to_execute == '':
                print('%14s' % ' ', end='')
            else:
                print('%14s' % '1', end='')

            # IO output here:
            num_outstanding = self.get_ios_in_flight(clock_tick)
            if num_outstanding > 0:
                print('%14s' % str(num_outstanding), end='')
                io_busy += 1
            else:
                print('%10s' % ' ', end='')
            print('')

            # if this is an IO start instruction, switch to waiting state
            # and add an io completion in the future
            if instruction_to_execute == DO_IO:
                self.move_to_wait(STATE_RUNNING)
                self.io_finish_times[self.curr_proc].append(clock_tick + self.io_length + 1)
                if self.process_switch_behavior == SCHED_SWITCH_ON_IO:
                    self.next_proc()

            # ENDCASE: check if currently running thing is out of instructions
            self.check_if_done()
        return (cpu_busy, io_busy, clock_tick)
        
#
# PARSE ARGUMENTS
#

parser = OptionParser()
parser.add_option('-s', '--seed', default=0, help='난수 시드 (같은 값으로 같은 문제 재현)', action='store', type='int', dest='seed')
parser.add_option('-P', '--program', default='', help='프로그램 명령을 직접 지정 (예: c5,i)', action='store', type='string', dest='program')
parser.add_option('-l', '--processlist', default='', help='프로세스 목록 X1:Y1,X2:Y2,... (X: 명령어 수, Y: CPU 명령 확률 0~100. 100이면 CPU만, 0이면 I/O만 사용)', action='store', type='string', dest='process_list')
parser.add_option('-L', '--iolength', default=5, help='I/O 완료에 걸리는 시간', action='store', type='int', dest='io_length')
parser.add_option('-S', '--switch', default='SWITCH_ON_IO', help='프로세스 전환 시점: SWITCH_ON_IO (I/O 시작 시), SWITCH_ON_END (종료 시)', action='store', type='string', dest='process_switch_behavior')
parser.add_option('-I', '--iodone', default='IO_RUN_LATER', help='I/O 완료 후 실행: IO_RUN_LATER (차례를 기다림), IO_RUN_IMMEDIATE (즉시 실행)', action='store', type='string', dest='io_done_behavior')
parser.add_option('-c', help='정답과 계산 결과 표시', action='store_true', default=False, dest='solve')
parser.add_option('-p', '--printstats', help='끝에 통계 표시 (-c와 함께 사용해야 표시됨)', action='store_true', default=False, dest='print_stats')
(options, args) = parser.parse_args()

print("""
[각주: 출력 읽는 법]
  - PID는 프로세스 번호입니다. RUN은 실행, READY는 실행 대기, BLOCKED은 I/O 대기, DONE은 종료 상태입니다.
  - 시각 옆 *는 I/O 완료 시점입니다. CPU 열과 I/O 열은 해당 시각의 사용 여부/진행 중인 I/O 수를 보여 줍니다.
  - CPU 사용률 = CPU 사용 시간 / 전체 경과 시간 × 100입니다. 한 프로세스가 I/O를 기다리는 동안 다른 프로세스가 CPU를 쓰는지 보세요.
""")

random_seed(options.seed)

assert(options.process_switch_behavior == SCHED_SWITCH_ON_IO or options.process_switch_behavior == SCHED_SWITCH_ON_END)
assert(options.io_done_behavior == IO_RUN_IMMEDIATE or options.io_done_behavior == IO_RUN_LATER)

s = scheduler(options.process_switch_behavior, options.io_done_behavior, options.io_length)

if options.program != '':
    for p in options.program.split(':'):
        s.load_program(p)
else:
    # example process description (10:100,10:100)
    for p in options.process_list.split(','):
        s.load(p)

assert(options.io_length >= 0)

if options.solve == False:
    print('다음 프로세스를 실행할 때의 실행 흐름을 작성하세요:')
    for pid in range(s.get_num_processes()):
        print('프로세스 %d' % pid)
        for inst in range(s.get_num_instructions(pid)):
            print('  %s' % s.get_instruction(pid, inst))
        print('')
    print('확인할 동작:')
    print('  프로세스 전환 조건: ', end='')
    if options.process_switch_behavior == SCHED_SWITCH_ON_IO:
        print('현재 프로세스가 종료되거나 I/O를 요청할 때')
    else:
        print('현재 프로세스가 종료될 때')
    print('  I/O 완료 후 요청한 프로세스는 ', end='')
    if options.io_done_behavior == IO_RUN_IMMEDIATE:
        print('즉시 실행됩니다')
    else:
        print('자신의 차례가 오면 실행됩니다')
    print('')
    exit(0)

(cpu_busy, io_busy, clock_tick) = s.run()

if options.print_stats:
    print('')
    print('통계: 전체 경과 시간 %d' % clock_tick)
    print('통계: CPU 사용 시간 %d (%.2f%%)' % (cpu_busy, 100.0 * float(cpu_busy)/clock_tick))
    print('통계: I/O 처리 중인 시간 %d (%.2f%%)' % (io_busy, 100.0 * float(io_busy)/clock_tick))
    print('')
