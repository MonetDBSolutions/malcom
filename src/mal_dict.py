import random
import json
from utils import Utils
from functools import reduce
from mal_instr import MalInstruction
from mal_dataflow import Dataflow
#TODO add method find closest instruction

class MalDictionary:
    """
    @arg mal_dict: dict<List<MalInstruction>>
    @arg q_tags  : list<int> //list of the unique query tags
    @arg varflow: dic<tag,dic<var,table>>
    """
    def __init__(self, mal_dict, q_tags, varflow):
        self.mal_dict   = mal_dict
        self.query_tags = q_tags
        self.varflow    = varflow

    """
    @arg mfile    : json file containing mal execution info (link??)
    @arg blacklist: list of black listed mal instructions
    """
    @staticmethod
    def fromJsonFile(mfile, blacklist):
        with open(mfile) as f:
            maldict    = {}
            startd     = {}
            query_tags = set()
            varflow    = Dataflow()

            while 1: #while not EOF
                jobj = Utils.read_json_object(f)
                if jobj is None:
                    break
                fname,args ,ret  = Utils.extract_fname(jobj["short"])

                if not Utils.is_blacklisted(blacklist,fname):
                    new_mals = MalInstruction.fromJsonObj(jobj)

                    if jobj["state"] == "start":
                        startd[jobj["pc"]] = jobj["clk"]
                    elif jobj["state"] == "done":
                        assert jobj["pc"] in startd
                        new_mals.time  = float(jobj["clk"]) - float(startd[jobj["pc"]])
                        maldict[fname] = maldict.get(fname,[]) + [new_mals]
                        query_tags.add(int(jobj["tag"]))

                        if fname == "bind": #or fname == "bind_idxbat":
                            varflow.add(new_mals.tag, ret, (args[2].strip(), args[3].strip()))
                        elif fname == "tid":
                            varflow.add(new_mals.tag, ret, args[2].strip())

        return MalDictionary(maldict,list(query_tags),varflow)

    """
    @arg mals: MalInstruction
    @ret: List<MalInstriction> //list of all exact matches
    """
    def findInstr(self, mals):
        dic = self.mal_dict
        return [x for x in dic[mals.fname] if x == mals]

    def getInsList(self):
        ilist = []
        for l in self.mal_dict.values():
            ilist.extend(l)
        return ilist

    """
    @arg mals: string //method name
    @arg nags: int    //nof arguments
    @ret: list<MalInstruction>
    """
    def findMethod(self, fname, nargs=None):
        dic = self.mal_dict
        if nargs == None:
            return dic[fname]

        return [x for x in dic[fname] if len(x.arg_list) == nargs]


    def findClosestSize(self, target):
        mlist     = self.mal_dict[target.fname]
        dist_list = [abs(i.arg_size-tsize) for x in mlist]
        nn_index  = dist_list.index(min(dist_list))
        return mlist[nn_index]

    #@arg
    def kNN(self, ins, k):
        mlist     = self.mal_dict[ins.fname]
        l         = len(ins.arg_list)
        dist_list = list(filter(lambda ins: len(ins.arg_list) == l, mlist))
        dist_list.sort( key = lambda i: ins.argDist(i) )
        return dist_list[0:k]

        #@arg
    def predictMem(self, ins, default=None):
        try:
            nn1 = self.kNN(ins,1)[0].mem_fprint
        except Exception as e:
            if default != None:
                nn1 =  default
            else:
                raise e
        return nn1

    def predict(self, ins, default=None):
        try:
            nn1 = self.kNN(ins,1)[0]
        except Exception as e:
            if default != None:
                nn1 =  default
            else:
                raise e
        return nn1
    # def preditMem(self,ins)

    #TODO too custom, needs rewritting
    def printAll(self, method, nargs):
        dic = self.mal_dict
        for s in dic[method]:
            if s.fname == method and nargs == len(s.arg_list):
                a2val = s.arg_list[2].aval
                a1val = s.arg_list[1].aval
                a1_t  = s.arg_list[1].atype
                print("mal: {}, args: {} {} {} size: {}, time: {}".format(method,a2val,a1_t, a1val,s.size,s.time))

    """ @arg other: MalDictionary"""
    def printDiff(self, other):
        for l in other.mal_dict.values():
            for m1 in l:
                assert len(self.findInstr(m1)) == 1
                try:
                    m   = self.findInstr(m1)[0]
                    ins = m.fname
                    td  = abs(m1.time-m.time)
                    sd  = abs(m1.mem_fprint-m.mem_fprint)
                    fs  = "q: {:<25s} tdiff: {:8.0f}/{:<8.0f} sdiff {:5d}/{:<5d}"
                    print(fs.format(ins,td,m.time,sd,m.mem_fprint))
                except IndexError:
                    print("Index Error: {}".format(m1.short))

    def getAll(self, method, nargs):
        d = self.mal_dict
        return filter(
            lambda s: s.fname == method and len(s.arg_list) == nargs, d[method]
        )

    """
    @arg f: lamdba k: MalInstruction
    """
    def getTopN(self, f, n):
        mal_list = Utils.flatten(self.mal_dict)
        mal_list.sort(key = f)
        return mal_list[0:n]




    """
    @desc splits the dictionary in two based on the query tags
    @arg: list<int>
    """
    def splitTag(self, train_tags, test_tags):
        s1,s2 = {},{}

        for (k,l) in self.mal_dict.items():
            for mali in l:
                if mali.tag in train_tags:
                    s1[k] = s1.get(k,[]) + [mali]
                if mali.tag in test_tags:
                    # assert not mali.tag in train_tags
                    s2[k] = s2.get(k,[]) + [mali]

        return (MalDictionary(s1,train_tags,self.varflow), MalDictionary(s2,test_tags,self.varflow))

    """
    @desc splits the dictionary in two based on the query id
    @arg: list<int>
    @arg tag2query: dict<int,int>
    """
    def splitQuery(self, train_q, test_q, tag2query):
        s1,s2 = {},{}
        s1_tags, s2_tags = set(), set()

        for (k,l) in self.mal_dict.items():
            for mali in l:
                if tag2query[mali.tag] in train_q:
                    s1[k] = s1.get(k,[]) + [mali]
                    s1_tags.add(mali.tag)
                if tag2query[mali.tag] in test_q:
                    s2[k] = s2.get(k,[]) + [mali]
                    s2_tags.add(mali.tag)

        return (MalDictionary(s1,list(s1_tags),self.varflow), MalDictionary(s2,list(s2_tags),self.varflow))

    """
    @desc splits the dictionary in two based on the query tags
    @arg: list<int>
    """
    def splitRandom(self, trainp, testp):
        assert trainp + testp == 1.0
        s1,s2 = {}, {}
        s1_tags, s2_tags = set(), set()

        for (k,l) in self.mal_dict.items():
            for mali in l:
                r = random.random()
                if r < trainp:
                    s1[k] = s1.get(k,[]) + [mali]
                    s1_tags.add(mali.tag)
                else:
                    assert r + testp >= 1
                    s2[k] = s2.get(k,[]) + [mali]
                    s2_tags.add(mali.tag)
        return (MalDictionary(s1,list(s1_tags),self.varflow), MalDictionary(s2,list(s2_tags),self.varflow))

    def printPredictions(self, test_dict):
        for ins in test_dict.getInsList():
            try:
                mpred = self.predictMem(ins)
                mem   = ins.mem_fprint
                if mem != 0:
                    print("method: {:20} nargs: {:2d} actual: {:10d} pred: {:10d} perc: {:10.0f}".format(ins.fname,ins.nargs, mem,mpred,abs(100*mpred/mem)))
                else:
                    print("method: {:20} nargs: {:2d} actual: {:10d} pred: {:10d}".format(ins.fname, ins.nargs, mem,mpred))
            except Exception as err:
                # print("Exception: {}".format(err))
                print("method: {:20} nargs: {:2d}  NOT FOUND".format(ins.fname,ins.nargs))
                pass

    def printPredictionsVerbose(self, test_dict):
        for ins in test_dict.getInsList():
            # try:
                ipred = self.predict(ins)
                mpred = ipred.mem_fprint
                mem   = ins.mem_fprint
                if mem != 0: # and mpred / mem > 2:
                    # print("method: {:15} actual: {:10d} pred: {:10d} perc: {:10.0f} ".format(ins.fname, mem,mpred,abs(100*mpred/mem)))
                    print("INS SHORT {:80}".format(ins.short))
                    print("KNN SHORT {:80}".format(ipred.short))

                    # for a in ins.getArgVars():
                    #     if a.name.startswith("X"):
                    #         print("{} {}".format(a.name, self.xvar_d[a.name]))
                    #     else:
                    #         print("{} {}".format(a.name, self.xvar_d[a.name]))

                    print("real: {:10d} pred: {:10d}\nINS: {} \nKNN: {}\n".format(mem,mpred, ins.argListStr(), ipred.argListStr()))
                # else:
                    # print("method: {:20} nargs: {:2d} actual: {:10d} pred: {:10d}".format(ins.fname, ins.nargs, mem,mpred))
            # except Exception as err:
            #     print("Exception: {}".format(err))
            #     # print("method: {:20} nargs: {:2d}  NOT FOUND".format(ins.fname,ins.nargs))
            #     pass

    def avgDeviance(self, test_dict):
        suml  = lambda x,y: x+y
        diff  = sum( map(lambda ins: abs(ins.mem_fprint-self.predictMem(ins,0)),test_dict.getInsList()) )
        total = sum( map(lambda ins: ins.mem_fprint,test_dict.getInsList()) )
        # print("dev")
        return 100 * diff / total
