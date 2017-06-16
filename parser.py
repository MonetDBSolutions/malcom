#!/usr/bin/python3
import json
import sys
from statement import MalStatement
from pprint import pprint

def print_usage():
    print("Usage: ./parser.py <trainset> <testset>")

#TODO error checking
#readline until you reach '}' or EOF
def read_json_object(f):
    lines = []
    rbrace = False
    while rbrace == False:
        line = f.readline()
        if line == '': #no more lines to read
            return None
        lines += line
        if line == '}\n':
            rbrace = True
    return ''.join(lines)



def get_top_N(mal_list, n):
    mal_list.sort(key = lambda k:  -k.time)
    return mal_list[0:n] #ignore the first 2(dataflow, user function)

def flatten(mal_dict):
    l = []
    for v in mal_dict.values():
        l.extend(v)
    return l


def parse_dataset(dfile):
    with open(dfile) as f:
        maldict = {}
        startd  = {}
        while 1: #while not EOF
            jsons = read_json_object(f)
            if jsons is None:
                break
            jobj     = json.loads(jsons)
            new_mals = MalStatement.fromJsonObj(jobj)
            if new_mals.stype != 'dataflow' and not "function user" in new_mals.stype:
                if jobj["state"] == "start":
                    startd[jobj["pc"]] = jobj["clk"]
                if jobj["state"] == "done":
                    assert jobj["pc"] in startd
                    new_mals.time = float(jobj["clk"]) - float(startd[jobj["pc"]])
                    maldict[new_mals.stype] = maldict.get(new_mals.stype,[]) + [new_mals]

    return maldict

def print_method(dic, method, nargs):
    for s in dic[method]:
        if s.stype == method and nargs == len(s.arg_list):
            print("method {} found, args: {} {} {} {} size: {}, time: {}".format(method,s.stype, s.arg_list[2].aval, s.arg_list[1].atype, s.arg_list[1].aval,s.size, s.time))

def get_all_method(dic, method, nargs):
    ret = []
    for s in dic[method]:
        if s.stype == method and nargs == len(s.arg_list):
            ret.append(s)
    return ret

def find_instr(dic, mals):
    return [x for x in dic[mals.stype] if x == mals]


if __name__ == '__main__':
    trainset = sys.argv[1]
    testset  = sys.argv[2]

    print("Using dataset {} as train set".format(trainset))
    print("Using dataset {} as test set".format(testset))
    
    traind   = parse_dataset(trainset)
    print_method(traind, "thetaselect", 3)
    print("--------------------------------------------------------------------------------------")
    testd    = parse_dataset(testset)
    print_method(testd,"thetaselect", 3)

    m1 = get_all_method(traind, "thetaselect", 3)[2]
    m1.print_stmt()
    m  = find_instr(testd,m1)[0]
    print("JUST TESTING")
    m.print_stmt()
    print("time diff: {} size diff {}".format(m1.time-m.time,m1.size-m.size))
    # testd    = parse_dataset(testset)
    # with open(trainset) as f:
    #     maldict = {}
    #     inslist = []
    #     while 1:
    #         jsons = parse_single(f)
    #         if jsons is None:
    #             break
    #         jobj    = json.loads(jsons)
    #         # (comm,_)          = parse_stmt(jobj["short"]) #for debugging
    #         # refd[comm]    = refd.get(comm, 0) + 1
    #         new_mals = MalStatement.fromJsonObj(jobj)
    #         if new_mals.stype != 'dataflow' and not "function user" in new_mals.stype:
    #             inslist.append(new_mals)
    #             maldict[new_mals.stype] = maldict.get(new_mals.stype,[]) + [new_mals]

    mlist  = flatten(traind)
    smlist = get_top_N(mlist,15)
#     print("-----------------------------TOP 15-------------------------------------------")
#     for e in smlist:
#         print("time:{} instr: {}".format(e.time,e.stype))
#         print("nargs: {}".format(len(e.arg_list)))

# #asserts
#     for ins in mlist:
#         if ins not in traind[ins.stype]:
#             print("Ins not found {}".format(ins.stype))

# if len(e.arg_list) > 0:
    # pprint(e.arg_list[0])
# print("---------------------------------------------------------------------x")
# for k in refd.keys():
#     print("{}: {}".format(k,refd[k]))
