#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# from this sort of thing
# a forks b
# a forks c
# a forks d
# b forks e
# b forks f
# d forks g

# to a process tree
#a --- b --- e
#   |     |
#   |     |- f
#   |- c
#   |
#   |- d --- g


from __future__ import print_function
import random
import string
from optparse import OptionParser

#
# to make Python2 and Python3 act the same -- how dumb
# 
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

def random_randint(low, hi):
    return int(low + random.random() * (hi - low + 1))

def random_choice(L):
    return L[random_randint(0, len(L)-1)]

#
# class Forker does all the work
#
class Forker:
    def __init__(self, fork_percentage, actions, action_list, show_tree, just_final,
                 leaf_only, local_reparent, print_style, solve):
        self.fork_percentage = fork_percentage
        self.max_actions = actions
        self.action_list = action_list
        self.show_tree = show_tree
        self.just_final = just_final
        self.leaf_only = leaf_only
        self.local_reparent = local_reparent
        self.print_style = print_style
        self.solve = solve

        # root process is always this
        self.root_name = 'a'

        # process list: names of all active processes
        self.process_list = [self.root_name]

        # for each process, it's children
        self.children = {}
        self.children[self.root_name] = []

        # and track parents
        self.parents = {}

        # this is for pretty process names...
        self.name_length = 1
        self.base_names = string.ascii_lowercase + string.ascii_uppercase
        self.curr_names = self.base_names
        self.curr_index = 1

        return

    def grow_names(self):
        new_names = []
        for b1 in self.curr_names:
            for b2 in self.base_names:
                new_names.append(b1 + b2)
        self.curr_names = new_names
        self.curr_index = 0
        return

    def get_name(self):
        if self.curr_index == len(self.curr_names):
            self.grow_names()
                
        name = self.curr_names[self.curr_index]
        self.curr_index += 1
        return name

    def walk(self, p, level, pmask, is_last):
        print('                               ', end='')
        if self.print_style == 'basic':
            for i in range(level):
                print('   ', end='')
            print('%2s' % p)
            for child in self.children[p]:
                self.walk(child, level + 1, {}, False)
            return
        elif self.print_style == 'line1':
            chars = ('|', '-', '+', '|')
        elif self.print_style == 'line2':
            chars = ('|', '_', '|', '|')
        elif self.print_style == 'fancy':
            # these characters taken from 'treelib', a fun printing package for trees
            # https://github.com/caesar0301/treelib
            # chars = ('\u2502', '\u2500', '\u251c', '\u2514')
            chars = (u'\u2502', u'\u2500', u'\u251c', u'\u2514')
        else:
            print('잘못된 출력 스타일 %s' % self.print_style)
            exit(1)
            
        # print stuff before node
        if level > 0:
            # main printing
            for i in range(level-1):
                if pmask[i]:
                    # '|  '
                    print('%s   ' % chars[0], end='')
                else:
                    print('    ', end='')
            if pmask[level-1]:
                # '|__'
                if is_last:
                    print('%s%s%s ' % (chars[3], chars[1], chars[1]), end='')
                else:
                    print('%s%s%s ' % (chars[2], chars[1], chars[1]), end='')
            else:
                # '___' 
                print(' %s%s%s ' % (chars[1], chars[1], chars[1]), end='')

        # print node
        print('%s' % p)

        # undo parent verticals
        if is_last:
            pmask[level-1] = False

        # recurse
        pmask[level] = True
        for child in self.children[p][:-1]:
            self.walk(child, level + 1, pmask, False)
        for child in self.children[p][-1:]:
            self.walk(child, level + 1, pmask, True)
        return

    def print_tree(self):
        return self.walk(self.root_name, 0, {}, False)
        
    def do_fork(self, p, c):
        self.process_list.append(c)
        self.children[c] = []
        self.children[p].append(c)
        self.parents[c] = p
        return '%s forks %s' % (p, c)

    def collect_children(self, p):
        if self.children[p] == []:
            return [p]
        else:
            L = [p]
            for c in self.children[p]:
                L += self.collect_children(c)
            return L

    def do_exit(self, p):
        # remove the process from the process list
        if p == self.root_name:
            print('루트 프로세스는 종료할 수 없습니다')
            exit(1)
        exit_parent = self.parents[p]
        self.process_list.remove(p)

        # for each orphan, set its parent to exiting proc's parent or root
        if self.local_reparent:
            for orphan in self.children[p]:
                self.parents[orphan] = exit_parent
                self.children[exit_parent].append(orphan)
        else:
            # should set ALL descendants to be child of ROOT 
            descendents = self.collect_children(p)
            descendents.remove(p)
            for d in descendents:
                self.children[d] = []
                self.parents[d] = self.root_name
                self.children[self.root_name].append(d)

        # remove the entry from its parent child list
        self.children[exit_parent].remove(p)
        self.children[p] = -1 # should never be used again
        self.parents[p] = -1  # should never be used again
            
        # remove the entry for this proc from children
        return '%s EXITS' % p

    def bad_action(self, action):
        print('잘못된 동작 (%s): X+Y 또는 X- 형식이어야 합니다 (X, Y: 프로세스 이름)' % action)
        exit(1)
        return

    def check_legal(self, action):
        if '+' in action:
            tmp = action.split('+')
            if len(tmp) != 2:
                self.bad_action(action)
            return [tmp[0], tmp[1]]
        elif '-' in action:
            tmp = action.split('-')
            if len(tmp) != 2:
                self.bad_action(action)
            return [tmp[0]]
        else:
            self.bad_action(action)
        return 
    
    def run(self):
        print('                           프로세스 트리:')
        self.print_tree()
        print('')

        if self.action_list != '':
            # use specific action list
            action_list = self.action_list.split(',')
        else:
            action_list = []
            actions = 0
            temp_process_list = [self.root_name]
            level_list = {}
            level_list[self.root_name] = 1

            # this got a little yucky, too much re-doing of the work
            while actions < self.max_actions:
                if random.random() < self.fork_percentage:
                    # FORK:: pick random parent, add child to it
                    fork_choice = random_choice(temp_process_list)
                    new_child = self.get_name()
                    action_list.append('%s+%s' % (fork_choice, new_child))
                    temp_process_list.append(new_child)
                else:
                    # EXIT:: pick random child, remove it
                    #        exception: no killing root process, sorry
                    exit_choice = random_choice(temp_process_list)
                    if exit_choice == self.root_name:
                        continue
                    temp_process_list.remove(exit_choice)
                    action_list.append('%s-' % exit_choice)
                actions += 1

        for a in action_list:
            tmp = self.check_legal(a)
            if len(tmp) == 2:
                fork_choice, new_child = tmp[0], tmp[1]
                if fork_choice not in self.process_list:
                    self.bad_action(a)
                action = self.do_fork(fork_choice, new_child)
            else:
                exit_choice = tmp[0]
                if exit_choice not in self.process_list:
                    self.bad_action(a)
                if self.leaf_only and len(self.children[exit_choice]) > 0:
                    action = '%s EXITS (failed: has children)' % exit_choice
                else:
                    action = self.do_exit(exit_choice)
            
            # if we got here, we actually did an action...
            if self.show_tree:
                # SHOW TREES (guess actions)
                if self.solve:
                    print('동작:', action)
                else:
                    print('동작은?')
                # print('Process Tree:')
                if not self.just_final:
                    self.print_tree()
            else:
                # SHOW ACTIONS (guess tree)
                print('동작:', action)
                if not self.just_final:
                    if self.solve:
                        # print('Process Tree:')
                        self.print_tree()
                    else:
                        print('프로세스 트리는?')

        if self.just_final:
            if self.show_tree:
                print('\n                        최종 프로세스 트리:')
                self.print_tree()
                print('')
            else:
                if self.solve:
                    print('\n                        최종 프로세스 트리:')
                    self.print_tree()
                    print('')
                else:
                    print('\n                        최종 프로세스 트리는?\n')
            
        return


#
# main
#

parser = OptionParser()
parser.add_option('-s', '--seed', default=-1, help='난수 시드 (같은 값으로 같은 문제 재현)', action='store', type='int', dest='seed')
parser.add_option('-f', '--forks', default=0.7, help='전체 동작 중 fork(자식 생성)의 비율 (나머지는 종료)', action='store', type='float', dest='fork_percentage')
parser.add_option('-A', '--action_list', default='', help='동작을 직접 지정 (a+b,b+c,b-: a가 b 생성, b가 c 생성, b 종료)', action='store', type='string', dest='action_list')
parser.add_option('-a', '--actions', default=5, help='생성/종료 동작 수', action='store', type='int', dest='actions')
parser.add_option('-t', '--show_tree', help='동작 대신 트리를 보여 주고 동작을 문제로 제시', action='store_true', default=False, dest='show_tree')
parser.add_option('-P', '--print_style', help='트리 출력 스타일 (basic, line1, line2, fancy)', action='store', type='string', default='fancy', dest='print_style')
parser.add_option('-F', '--final_only', help='마지막 상태만 표시', action='store_true', default=False, dest='just_final')
parser.add_option('-L', '--leaf_only', help='자식 없는 말단 프로세스만 종료 허용', action='store_true', default=False, dest='leaf_only')
parser.add_option('-R', '--local_reparent', help='고아 프로세스를 가까운 조상에게 재연결', action='store_true', default=False, dest='local_reparent')
parser.add_option('-c', '--compute', help='정답과 계산 결과 표시', action='store_true', default=False, dest='solve')

(options, args) = parser.parse_args()

if options.seed != -1:
    random_seed(options.seed)

if options.fork_percentage <= 0.001:
    print('fork_percentage는 0.001보다 커야 합니다')
    exit(1)

print('')
print('설정 난수 시드 (seed)', options.seed)
print('설정 프로세스 생성 비율 (fork_percentage)', options.fork_percentage)
print('설정 동작 (actions)', options.actions)
print('설정 동작 목록 (action_list)', options.action_list)
print('설정 트리 표시 (show_tree)', options.show_tree)
print('설정 최종 상태만 표시 (just_final)', options.just_final)
print('설정 말단 프로세스만 종료 (leaf_only)', options.leaf_only)
print('설정 가까운 조상에게 재연결 (local_reparent)', options.local_reparent)
print('설정 트리 출력 스타일 (print_style)', options.print_style)
print('설정 정답 표시 (solve)', options.solve)
print('')

f = Forker(options.fork_percentage, options.actions, options.action_list, options.show_tree, options.just_final, options.leaf_only, options.local_reparent, options.print_style, options.solve)
f.run()



# Korean reading guide; simulator state is unchanged.
print("""
[각주: 출력 읽는 법]
  - 프로세스 트리: 들여쓰기는 부모-자식 관계입니다. X+Y는 X가 Y를 생성(fork), X-는 X의 종료입니다.
  - 부모가 먼저 종료되면 살아 있는 자식의 부모가 바뀝니다. leaf_only와 local_reparent 설정에 따른 트리 차이를 보세요.
  - forks는 자식 생성, EXITS는 종료, failed: has children은 자식이 남아 있어 종료할 수 없음을 뜻합니다.
""")
