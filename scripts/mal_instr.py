from utils import Utils
from functools import reduce

#TODO Utils
def parse_stmt(stmt):
    # print(stmt)
    args = []
    if ":=" in stmt:
        fname = stmt.split(':=')[1].split("(")[0]
        args  = stmt.split(':=')[1].split("(")[1].split(")")[0].strip().split(" ") #TODO remove
    elif "(" in stmt:
        fname = stmt.split("(")[0]
        args  = stmt.split("(")[1].split(")")[0].strip().split(" ")
    else:
        fname = stmt

    return (fname.strip(),args)


    """ MalInstruction Class:
@arg type(string)   : type of statement(assign, thetaselect etc)
@arg time(float)    : how much time did the statement last
@arg size(int)      : memory footprint
@arg list(List<Arg>): the arguments of the query (list for now TODO change)
@arg short(string)  : the short mal statement, str representation
@var metric(Metric) : var that can define a distance between two queries
    """
class MalInstruction:
    def __init__(self, short, stype, size, ret_size, usec, alist):
        self.stype    = stype
        self.time     = 0
        self.size     = size
        self.ret_size = ret_size
        self.usec     = usec
        self.arg_list = alist
        self.short    = short
        self.tot_size = self.size + self.ret_size
        self.metric   = Metric.fromMalInstruction(self.stype,self.arg_list)#TODO rethink

    def distance(self,other):
        return self.metric.distance(other.metric) #TODO fix this

    @staticmethod
    def fromJsonObj(jobj):
        # time          = float(jobj["usec"])
        size          = int(jobj["size"])
        short         = jobj["short"]
        (stype,_)     = parse_stmt(jobj["short"])
        usec          = jobj["usec"]
        
        rv            = [rv.get("size",0) for rv in jobj["ret"]]
        ret_size      = reduce(lambda x,y: x+y, rv, 0)#total size of return vals
        
        if "arg" in jobj:
            alist = [Arg.fromJsonObj(e) for e in jobj["arg"]]
            # alist = parse_stmt_args(jobj["arg"])
        else:
            alist = []
        return MalInstruction(short, stype, size, ret_size, usec, alist)

    def print_stmt(self):
        print("Instr: {} args: {} time: {} size: {}".format(self.stype,len(self.arg_list),self.time, self.size))

    def __eq__(self, other):
        if(self.stype == other.stype and Utils.cmp_arg_list(self.arg_list,other.arg_list) == True):
            return True
        else:
            return False

    def __ne__(self, other):
        return self.__ne__(other)

    
""" Arg class """
#@attr atype: String
#@attr aval : Object
class Arg:
    def __init__(self, name, atype, val, size):
        self.name   = name
        self.atype  = atype
        self.aval   = val
        self.size   = size
    @staticmethod
    def fromJsonObj(jobj):
        # pprint(jobj)
        name  = jobj['name']
        atype = jobj['type']
        aval  = jobj.get('value',None)
        size  = jobj.get('size',0)
        return Arg(name,atype,aval,size)

    def __eq__(self, other):
        if (self.name  == other.name  and
            self.atype == other.atype and
            self.aval  == other.aval  and
            self.size  == other.size):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

#TODO rename Metric, wtf name is this ?
#TODO maybe input output operator: Arg format ???
"""
@arg itype: intstuction type: String
@arg value:
@arg op: type of operator(e.g thetaselect)
@arg vtype: type of value(short, int, boolean, date...)
"""
class Metric:
    def __init__(self, itype, op, vtype, value):
        self.itype = itype #maybe remove??
        self.op    = op
        self.vtype = vtype
        self.value = value

    def distance(self, other):
        if( self.itype == other.itype and
            self.op == other.op and
            self.vtype == other.vtype):
            if(self.vtype == "int"):
                return float((other.value-self.value) ** 2)
        else:
            return float("inf")

    @staticmethod
    def fromMalInstruction(sname, arg_list):
        if(sname == 'thetaselect'):
            if(len(arg_list) == 4):
                return None
            elif len(arg_list) == 3:
                # print("thetaselect found {} {} {} {}".format(sname, arg_list[2].aval, arg_list[1].atype, arg_list[1].aval))
                return Metric(sname, arg_list[2].aval, arg_list[1].atype, arg_list[1].aval)
            else:
                print("wtf")
                return None
        else:
            return None
