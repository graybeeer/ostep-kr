#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import random
from optparse import OptionParser
import string

# to make Python2 and Python3 act the same -- how dumb
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

def tprint(str):
    print(str)

def dprint(str):
    return

def dospace(howmuch):
    for i in range(howmuch + 1):
        print('%28s' % ' ', end='')

# given list, pick random element and return it
def pickrand(tlist):
    n = int(random.random() * len(tlist))
    p = tlist[n]
    return p

# given number, conclude if nth bit is set
def isset(num, index):
    mask = 1 << index
    return (num & mask) > 0

# useful instead of assert
def zassert(cond, str):
    if cond == False:
        print('중단::', str)
        exit(1)

#
# Which files are used in the simulation
# 
# Not representing a realistic piece of anything
# but rather just for convenience when generating
# random traces ...
#
# Files are named 'a', 'b', etc. for ease of use
# Could probably add a numeric aspect to allow
# for more than 26 files but who cares
#

class files:
    def __init__(self, numfiles):
        self.numfiles = numfiles
        self.value    = 0
        self.filelist = list(string.ascii_lowercase)[0:numfiles]

    def getfiles(self):
        return self.filelist

    def getvalue(self):
        rc = self.value
        self.value += 1
        return rc

#
# Models the actions of the AFS server
# 
# The only real interactions are get/put
# get() causes the server to track which files cache what;
# put() may cause callbacks to invalidate client caches
#
class server:
    def __init__(self, files, solve, detail):
        self.files  = files
        self.solve  = solve
        self.detail = detail
        
        flist = self.files.getfiles()
        self.contents = {}
        for f in flist:
            v = self.files.getvalue()
            self.contents[f] = v
        self.getcnt, self.putcnt = 0, 0

    def stats(self):
        print('서버     -- 가져오기:%d 저장:%d' % (self.getcnt, self.putcnt))

    def filestats(self, printcontents):
        for fname in self.contents:
            if printcontents:
                print('파일:%s 내용:%d' % (fname, self.contents[fname]))
            else:
                print('파일:%s 내용:?' % fname)
            

    def setclients(self, clients):
        # need list of clients 
        self.clients = clients

        # per client callback list
        self.cache = {}
        for c in self.clients:
            self.cache[c.getname()] = []

    def get(self, client, fname):
        zassert(fname in self.contents, '서버 가져오기 -- 파일:%s이(가) 서버에 없습니다' % fname)
        self.getcnt += 1
        if self.solve and isset(self.detail, 0):
            print('파일 가져오기:%s 클라이언트:%s [%d]' % (fname, client, self.contents[fname]))
        if fname not in self.cache[client]:
            self.cache[client].append(fname)
            # dprint('  -> List for client %s' % client, ' is ', self.cache[client])
        return self.contents[fname]

    def put(self, client, fname, value):
        zassert(fname in self.contents, '서버 저장 -- 파일:%s이(가) 서버에 없습니다' % fname)
        self.putcnt += 1
        self.contents[fname] = value
        if self.solve and isset(self.detail, 0):
            print('파일 저장:%s 클라이언트:%s [%s]' % (fname, client, self.contents[fname]))
        # scan others for callback
        for c in self.clients:
            cname = c.getname()
            if fname in self.cache[cname] and cname != client:
                if self.solve and isset(self.detail, 1):
                    print('콜백: 클라이언트:%s 파일:%s' % (cname, fname))
                c.invalidate(fname)
                # XXX - this is not right ...
                # self.cache[cname].remove(fname)

#
# Per-client file descriptors
#
# Would be useful if the simulation allowed more
# than one active file open() at a time; it kind
# of does but this isn't really utilized
#
class filedesc:
    def __init__(self, max=1024):
        self.max = max
        self.fd  = {}
        for i in range(self.max):
            self.fd[i] = ''

    def alloc(self, fname, sfd=-1):
        if sfd != -1:
            zassert(self.fd[sfd] == '', '파일 디스크립터 할당 -- fd:%d은(는) 이미 사용 중입니다' % sfd)
            self.fd[sfd] = fname
            return sfd
        else:
            for i in range(self.max):
                if self.fd[i] == '':
                    self.fd[i] = fname
                    return i
            return -1

    def lookup(self, sfd):
        zassert(i >= 0 and i < self.max, '파일 디스크립터 조회 -- 유효 범위 초과 (%d은(는) 0~%d 범위가 아님)' % (sfd, self.max))
        zassert(self.fd[sfd] != '',      '파일 디스크립터 조회 -- fd:%d은(는) 사용 중이 아니어서 조회할 수 없습니다' % sfd)
        return self.fd[sfd]

    def free(self, i):
        zassert(i >= 0 and i < self.max, '파일 디스크립터 해제 -- 유효 범위 초과 (%d은(는) 0~%d 범위가 아님)' % (sfd, self.max))
        zassert(self.fd[sfd] != '',      '파일 디스크립터 해제 -- fd:%d은(는) 사용 중이 아니어서 해제할 수 없습니다' % sfd)
        self.fd[i] = ''

#
# The client cache
#
# Just models what files are cached.
# When a file is opened, its contents are fetched
# from the server and put in the cache. At that point,
# the cache contents are VALID, DIRTY/NOT (depending
# on whether this is for reading or writing), and the
# REFERENCE COUNT is set to 1. If multiple open's take
# place on this file, REFERENCE COUNT will be updated
# accordingly. VALID gets set to 0 if the cache is
# invalidated by a callback; however, the contents
# still might be used by a given client if the file
# is already open. Note that a callback does NOT
# prevent a client from overwriting an already opened file.
#
class cache:
    def __init__(self, name, num, solve, detail):
        self.name       = name
        self.num        = num
        self.solve      = solve
        self.detail     = detail

        self.cache      = {}

        self.hitcnt     = 0
        self.misscnt    = 0
        self.invalidcnt = 0

    def stats(self):
        print('   캐시 -- 적중:%d 실패:%d 무효화:%d' % (self.hitcnt, self.misscnt, self.invalidcnt))

    def put(self, fname, data, dirty, refcnt):
        self.cache[fname] = dict(data=data, dirty=dirty, refcnt=refcnt, valid=True)
            
    def update(self, fname, data):
        self.cache[fname] = dict(data=data, dirty=True, refcnt=self.cache[fname]['refcnt'], valid=self.cache[fname]['valid'])

    def invalidate(self, fname):
        dospace(self.num)
        print('파일 무효화:%s' % fname, '캐시:', self.cache)
        # zassert(fname in self.cache, 'cache:invalidate() -- cannot invalidate file not in cache (%s)' % fname)
        if fname not in self.cache:
            return
        self.invalidcnt += 1
        self.cache[fname] = dict(data=self.cache[fname]['data'], dirty=self.cache[fname]['dirty'],
                                 refcnt=self.cache[fname]['refcnt'], valid=False)
        if self.solve and isset(self.detail, 1):
            dospace(self.num)
            if isset(self.detail,3):
                print('%2s 무효화 %s' % (self.name, fname))
            else:
                print('무효화 %s' % (fname))
            self.printstate(self.num)

    def checkvalid(self, fname):
        zassert(fname in self.cache, '캐시 유효성 검사 -- 캐시에 없는 파일은 검사할 수 없습니다 (%s)' % fname)
        if self.cache[fname]['valid'] == False and self.cache[fname]['refcnt'] == 0:
            del self.cache[fname]

    def printstate(self, fname):
        for fname in self.cache:
            data   = self.cache[fname]['data']
            dirty  = self.cache[fname]['dirty']
            refcnt = self.cache[fname]['refcnt']
            valid  = self.cache[fname]['valid']
            if valid == True:
                validPrint = 1
            else:
                validPrint = 0
            if dirty == True:
                dirtyPrint = 1
            else:
                dirtyPrint = 0

            if self.solve and isset(self.detail, 2):
                dospace(self.num)
                if isset(self.detail, 3):
                    print('%s [%s:%2d (v=%d,d=%d,r=%d)]' % (self.name, fname, data, validPrint, dirtyPrint, refcnt))
                else:
                    print('[%s:%2d (v=%d,d=%d,r=%d)]' % (fname, data, validPrint, dirtyPrint, refcnt))

    def checkget(self, fname):
        if fname in self.cache:
            self.cache[fname] = dict(data=self.cache[fname]['data'], dirty=self.cache[fname]['dirty'],
                                     refcnt=self.cache[fname]['refcnt'], valid=self.cache[fname]['valid'])
            self.hitcnt += 1
            return (True, self.cache[fname])
        self.misscnt += 1
        return (False, -1)

    def get(self, fname):
        assert(fname in self.cache)
        return (True, self.cache[fname])

    def incref(self, fname):
        assert(fname in self.cache)
        self.cache[fname] = dict(data=self.cache[fname]['data'], dirty=self.cache[fname]['dirty'],
                                 refcnt=self.cache[fname]['refcnt'] + 1, valid=self.cache[fname]['valid'])
        
    def decref(self, fname):
        assert(fname in self.cache)
        self.cache[fname] = dict(data=self.cache[fname]['data'], dirty=self.cache[fname]['dirty'],
                                 refcnt=self.cache[fname]['refcnt'] - 1, valid=self.cache[fname]['valid'])
        
    def setdirty(self, fname, dirty):
        assert(fname in self.cache)
        self.cache[fname] = dict(data=self.cache[fname]['data'], dirty=dirty,
                                 refcnt=self.cache[fname]['refcnt'], valid=self.cache[fname]['valid'])

    def setclean(self, fname):
        assert(fname in self.cache)
        self.cache[fname] = dict(data=self.cache[fname]['data'], dirty=False,
                                 refcnt=self.cache[fname]['refcnt'], valid=self.cache[fname]['valid'])
            
    def isdirty(self, fname):
        assert(fname in self.cache)
        return (self.cache[fname]['dirty'] == True)

    def setvalid(self, fname):
        assert(fname in self.cache)
        self.cache[fname] = dict(data=self.cache[fname]['data'], dirty=self.cache[fname]['dirty'],
                                 refcnt=self.cache[fname]['refcnt'], valid=True)
            
        
# actions
MICRO_OPEN      = 1
MICRO_READ      = 2
MICRO_WRITE     = 3
MICRO_CLOSE     = 4

def op2name(op):
    if op == MICRO_OPEN:
        return 'MICRO_OPEN'
    elif op == MICRO_READ:
        return 'MICRO_READ'
    elif op == MICRO_WRITE:
        return 'MICRO_WRITE'
    elif op == MICRO_CLOSE:
        return 'MICRO_CLOSE'
    else:
        abort('오류: 잘못된 동작 -> ' + op)

#
# Client class
#
# Models the behavior of each client in the system.
#
# 
#
class client:
    def __init__(self, name, cid, server, files, bias, numsteps, actions, solve, detail):
        self.name    = name      # readable name of client
        self.cid     = cid       # client ID
        self.server  = server    # server object
        self.files   = files     # files object
        self.bias    = bias      # bias
        self.actions = actions   # schedule exactly?
        self.solve   = solve     # show answers?
        self.detail  = detail    # how much of an answer to show

        # cache
        self.cache   = cache(self.name, self.cid, self.solve, self.detail)

        # file desc
        self.fd      = filedesc()

        # stats
        self.readcnt  = 0
        self.writecnt = 0

        # init actions
        self.done    = False     # track state
        self.acnt    = 0         # this is used when running
        self.acts    = []        # this just tracks the opcodes

        if self.actions == '':
            # in case with no specific actions, generate one...
            for i in range(numsteps):
                fname = pickrand(self.files.getfiles())
                r = random.random()
                fd = self.fd.alloc(fname)
                zassert(fd >= 0, '클라이언트 초기화 -- 파일 디스크립터가 부족합니다!')
                if r < self.bias[0]:
                    # FILE_READ
                    self.acts.append((MICRO_OPEN,  fname, fd))
                    self.acts.append((MICRO_READ,  fd))
                    self.acts.append((MICRO_CLOSE, fd))
                else:
                    # FILE_WRITE
                    self.acts.append((MICRO_OPEN,  fname, fd))
                    self.acts.append((MICRO_WRITE, fd))
                    self.acts.append((MICRO_CLOSE, fd))
        else:
            # in this case, unpack actions and make it happen
            # should look like this: "oa1:r1:c1" (open 'a' for reading with file desc 1, read from fd:1, close fd:1)
            # yes the file descriptor and file name are redundant for read/write and close
            for a in self.actions.split(':'):
                act = a[0]
                if act == 'o':
                    zassert(len(a) == 3, '클라이언트 초기화 -- 잘못된 열기 동작 (%s), oa1과 같은 형식을 사용하세요' % a)
                    fname, fd = a[1], int(a[2])
                    self.fd.alloc(fname, fd)
                    assert(fd >= 0)
                    self.acts.append((MICRO_OPEN,  fname, fd))
                elif act == 'r':
                    zassert(len(a) == 2, '클라이언트 초기화 -- 잘못된 읽기 동작 (%s), r1과 같은 형식을 사용하세요' % a)
                    fd = int(a[1])
                    self.acts.append((MICRO_READ,  fd))
                elif act == 'w':
                    zassert(len(a) == 2, '클라이언트 초기화 -- 잘못된 쓰기 동작 (%s), w1과 같은 형식을 사용하세요' % a)
                    fd = int(a[1])
                    self.acts.append((MICRO_WRITE, fd))
                elif act == 'c':
                    zassert(len(a) == 2, '클라이언트 초기화 -- 잘못된 닫기 동작 (%s), c1과 같은 형식을 사용하세요' % a)
                    fd = int(a[1])
                    self.acts.append((MICRO_CLOSE, fd))
                else:
                    print('알 수 없는 명령: %s (입력 %s)' % (act, a))
                    exit(1)
        print(self.acts)
        return

    def getname(self):
        return self.name

    def stats(self):
        print('%s       -- 읽기:%d 쓰기:%d' % (self.name, self.readcnt, self.writecnt))
        self.cache.stats()
            
    def getfile(self, fname):
        (in_cache, item) = self.cache.checkget(fname)
        if in_cache == True and item['valid'] == 1:
            dprint('  -> CLIENT %s:: HAS LOCAL COPY of %s' % (self.name, fname))
            # self.cache.setdirty(fname, dirty)
        else:
            data = self.server.get(self.name, fname)
            self.cache.put(fname, data, False, 0)
        self.cache.incref(fname)
        return

    def putfile(self, fname, value):
        self.server.put(self.name, fname, value)
        self.cache.setclean(fname)
        self.cache.setvalid(fname)
        return

    def invalidate(self, fname):
        self.cache.invalidate(fname)
        return

    def step(self, space):
        if self.done == True:
            return -1
        if self.acnt == len(self.acts):
            self.done = True
            return 0

        # now figure out what to do and do it
        # action, fname, fd = self.acts[self.acnt]
        action = self.acts[self.acnt][0]

        # print ''
        # print '*************************'
        # print '%s ACTION -> %s' % (self.name, op2name(action))
        # print '*************************'

        # first, do spacing for command (below)
        dospace(space)

        if isset(self.detail, 3) == True:
            print(self.name, end=' ')

        # now handle the action
        if action == MICRO_OPEN:
            fname, fd = self.acts[self.acnt][1], self.acts[self.acnt][2]
            tprint('open:%s [fd:%d]' % (fname, fd))
            # self.getfile(fname, dirty=False)
            self.getfile(fname)
        elif action == MICRO_READ:
            fd    = self.acts[self.acnt][1]
            fname = self.fd.lookup(fd)
            self.readcnt += 1
            in_cache, contents = self.cache.get(fname)
            assert(in_cache == True)
            if self.solve:
                tprint('read:%d -> %d' % (fd, contents['data']))
            else:
                tprint('read:%d -> value?' % (fd))
        elif action == MICRO_WRITE:
            fd    = self.acts[self.acnt][1]
            fname = self.fd.lookup(fd)
            self.writecnt += 1
            in_cache, contents = self.cache.get(fname)
            assert(in_cache == True)
            v = self.files.getvalue()
            self.cache.update(fname, v)
            if self.solve:
                tprint('write:%d %d -> %d' % (fd, contents['data'], v))
            else:
                tprint('write:%d value? -> %d' % (fd, v))
        elif action == MICRO_CLOSE:
            fd    = self.acts[self.acnt][1]
            fname = self.fd.lookup(fd)
            in_cache, contents = self.cache.get(fname)
            assert(in_cache == True)
            tprint('close:%d' % (fd))
            if self.cache.isdirty(fname):
                self.putfile(fname, contents['data'])
            self.cache.decref(fname)
            self.cache.checkvalid(fname)

        # useful to see
        self.cache.printstate(self.name)

        if self.solve and self.detail > 0:
            print('')

        # return that there is more left to do
        self.acnt += 1
        return 1


#
# main program
#
parser = OptionParser()
parser.add_option('-s', '--seed',      default=0,      help='난수 시드 (같은 값으로 같은 문제 재현)',           action='store', type='int', dest='seed')
parser.add_option('-C', '--clients',   default=2,      help='클라이언트 수',         action='store', type='int', dest='numclients')
parser.add_option('-n', '--numsteps',  default=2,      help='클라이언트별 동작 수',   action='store', type='int', dest='numsteps')
parser.add_option('-f', '--numfiles',  default=1,      help='서버의 파일 수', action='store', type='int', dest='numfiles')
parser.add_option('-r', '--readratio', default=0.5,    help='읽기 비율 (나머지는 쓰기)',     action='store', type='float', dest='readratio')
parser.add_option('-A', '--actions',   default='',     help='클라이언트 동작 직접 지정 (oa1:r1:c1,oa1:w1:c1: 두 클라이언트가 파일 a를 열고, 각각 읽기/쓰기를 한 뒤 닫음)', action='store', type='string', dest='actions')
parser.add_option('-S', '--schedule',  default='',     help='실행 순서 지정 (01: 클라이언트 0과 1을 번갈아 실행, 생략하면 무작위)', action='store', type='string', dest='schedule')
parser.add_option('-p', '--printstats', default=False, help='추가 통계 표시',      action='store_true', dest='printstats')
parser.add_option('-c', '--compute',    default=False, help='정답과 계산 결과 표시', action='store_true', dest='solve')
parser.add_option('-d', '--detail',     default=0,     help='정답 상세 수준 (1: 서버 동작, 2: 무효화, 4: 클라이언트 캐시, 8: 추가 이름표; 비트 OR로 조합)', action='store', type='int', dest='detail')
(options, args) = parser.parse_args()

print('설정 난수 시드 (seed)',       options.seed)
print('설정 클라이언트 수 (numclients)', options.numclients)
print('설정 클라이언트별 동작 수 (numsteps)',   options.numsteps)
print('설정 파일 수 (numfiles)',   options.numfiles)
print('설정 읽기 비율 (readratio)',  options.readratio)
print('설정 동작 (actions)',    options.actions)
print('설정 실행 순서 (schedule)',   options.schedule)
print('설정 상세 수준 (detail)',     options.detail)
print('')

seed       = int(options.seed)
numclients = int(options.numclients)
numsteps   = int(options.numsteps)
numfiles   = int(options.numfiles)
readratio  = float(options.readratio)
actions    = options.actions
schedule   = options.schedule
printstats = options.printstats
solve      = options.solve
detail     = options.detail

# with specific schedule, files are all specified by a single letter in specific actions list
# but we ignore this for now...

zassert(numfiles > 0 and numfiles <= 26, '파일은 26개까지만 시뮬레이션할 수 있습니다')
zassert(readratio >= 0.0 and readratio <= 1.0, '읽기 비율은 0 이상 1 이하여야 합니다')

# start it
random_seed(seed)

# files in server to begin with
f = files(numfiles)

# make server
s = server(f, solve, detail)

clients = []

if actions != '':
    # if specific actions are specified, figure some stuff out now
    # e.g., oa1:ra1:ca1,oa1:ra1:ca1 which is list of 0's actions, then 1's, then...
    cactions = actions.split(',')
    if numclients != len(cactions):
        numclients = len(cactions)
    i = 0
    for clist in cactions:
        clients.append(client('c%d' % i, i, s, f, [], len(clist), clist, solve, detail))
        i += 1
else:
    # else, make random clients
    for i in range(numclients):
        clients.append(client('c%d' % i, i, s, f, [readratio, 1.0], numsteps, '', solve, detail))

# tell server about these clients
s.setclients(clients)

# init print out for clients
print('%12s' % '서버', '%12s' % ' ', end=' ')
for c in clients:
    print('%13s' % c.getname(), '%13s' % ' ', end=' ')
print('')

# main loop
#
# over time, pick a random client
# have it do one thing, show what happens
# move on to next and so forth

s.filestats(True)

# for use with specific schedule
schedcurr = 0

# check for legal schedule (must include all clients)
if schedule != '':
    for i in range(len(clients)):
        cnt = 0
        for j in range(len(schedule)):
            curr = schedule[j]
            if int(curr) == i:
                cnt += 1
        zassert(cnt != 0, '클라이언트 %d이(가) 실행 순서:%s에 없어 종료할 수 없습니다' % (i, schedule))
            
# RUN the schedule (either random or specified by user)
numrunning = len(clients)
while numrunning > 0:
    if schedule == '':
        c = pickrand(clients)
    else:
        idx = int(schedule[schedcurr])
        # print 'SCHEDULE DEBUG:: schedule:', schedule, 'schedcurr', schedcurr, 'index', idx
        c = clients[idx]
        schedcurr += 1
        if schedcurr == len(schedule):
            schedcurr = 0
    rc = c.step(clients.index(c))
    if rc == 0:
        numrunning -= 1


s.filestats(solve)

if printstats:
    s.stats()
    for c in clients:
        c.stats()


# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 서버 가져오기(Get)/저장(Put)은 서버와의 파일 전송 횟수, 캐시 적중/실패는 로컬 복사본 사용 가능 여부입니다.
  - open/read/write/close는 열기/읽기/쓰기/닫기입니다. 클라이언트의 변경이 서버에 언제 전달되고 다른 클라이언트의 캐시가 언제 무효화되는지 보세요.
  - 캐시의 v는 유효 여부, d는 수정 여부(dirty), r은 열고 있는 참조 수입니다. 콜백은 서버가 캐시 무효화를 알리는 동작입니다.
""")
