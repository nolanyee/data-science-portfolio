'''
This program enables creation of simplified hypothetical Bayesian networks, for situations where little is known
about the joint probability distributions or even the true structure of the network.

Joint probability distributions are limited to a few different intuitive types, which enable simpler calculations.
1. Main Node: True only if any parent is True
2. Interaction Node: True only if all parents are True
3. Exclusion Node: True only if one parent is True
4. Inverted Node: True only if any parent is False
5. Inverted Interaction Node: True only if all parents are False

For a child node, the effective probability of parents being True is the probability p of the parents being True
multiplied by a weight w. The effective probability of the parents being False is therefore 1 - pw. It is recommended
that 0 <= w <= 1, but it is not enforced. For probabilities that are expected to be small, w > 1 may be used, but with
caution, as long as pw never exceeds 1. Never assign w < 0.

The graphs update in two modes. Bayesian mode recalculates the probability of each node given the all the evidence.
However if the evidence is contradictory, it will display an error. Investigation mode recalculates probabilities based
only on their parents (not their children) and optimizes priors of the Eves (parentless nodes) using gradient descent.
This allows flagging of contradictory nodes (with parents given precedence over children). It also uses gradient
descent to optimize all the w's to resolve contradictions (the result is output as a change in the color of the edge
and the original w values are restored). The constraint 0 <= w <= 1 is not enforced during gradient descent unless
'Constrained' is selected.

Investigation mode can be run optimizing priors using only the shallowest evidence nodes, and using only the
contradictory nodes to optimize w's. Alternatively if 'Use All Evidence' is selected, all the evidence is used for
optimization of priors and w's.
'''


# Global Variables and Lists
NodeList = [] # Current global list of all nodes
CalcNodeList = [] # Temporary list of nodes whose probabilities have already been calculated during update()
EvidenceList = [] # List of all user set evidence
LineList =[] # List of edges, associated nodes, weight, and a copy of weight to restore weights after gradient descent
NodeID = 0 # Running count of number of nodes created, for symbol assignment
WeightID = 0 # Running count of number of edges created, for symbol assignment
wSymbolDict = {} # Dictionary of weight symbols (keys) and associated weight objects
pSymbolDict = {} # Dictionary of node symbols (keys) and associated node objects
SymbolList = [] # A list of all symbols compiled from pSymbolDict and wSymbolDict during update()
CalcList = [] # A list storing nodes yet to be calculated during update calculations, to avoid repeat calculations
ActiveList = [] # A list with currently calculating nodes for during update calculations, to avoid repeat calculations
TypeColor = {'Main':'black', 'Interaction':'blue', 'Exclusion':'green',
             'Inverted':'red', 'Inverted Interaction':'magenta'} # Node label color assignment for node type
                                                                 # update if new node type is added

EdgeEnds = [] # List of nodes used for edge creation
EdgeEnds2 =[] # List of nodes used for edge deletion

# Imported Libraries
from tkinter import *
from tkinter.ttk import * # Overrides basic Tk widgets
from symengine import * # Run time is ~10x faster compared with sympy
from random import *
import re
from itertools import *
import pickle
import cProfile

# Main Window Widget Creation
root = Tk(className = ' Investigator ')

sheet = Canvas(root, width=850, height=600)
sheet.pack(fill=BOTH, expand=True )

testbutton1 = Button(root,text='Clear Evidence', command=lambda:clearevidence())
testbutton2 = Button(root,text='Clear Highlights', command=lambda:clearlinecolor())
testbutton3 = Button(root,text='Reset Priors', command=lambda:clearpriors())
testbutton4 = Button(root,text='UPDATE', command=lambda:updatebutton())

allevidencevar = IntVar()
allevidence = Checkbutton(root, text='Use All Evidence',variable=allevidencevar)

wtonlyvar = IntVar()
wtonly = Checkbutton(root, text='Constrained', variable=wtonlyvar)

modevar = IntVar()
Radio1 = Radiobutton(root,text='Bayesian',variable=modevar,value=1, command=lambda:disable())
Radio2 = Radiobutton(root,text='Investigation',variable=modevar,value=2, command=lambda:enable())

message = Label(root,text='Press Ctrl-h for instructions',justify=CENTER)

# Widget Packing
testbutton1.pack(side=RIGHT)
testbutton2.pack(side=RIGHT)
testbutton3.pack(side=RIGHT)
Radio1.pack(side=LEFT)
Radio2.pack(side=LEFT)
allevidence.pack(side=LEFT)
wtonly.pack(side=LEFT)
testbutton4.pack(side=LEFT)
message.pack(side=LEFT,fill=BOTH,expand=True)

# Set Default Update Mode to Investigation
modevar.set(2)

# Disable options for investigation mode if Bayesian mode is chosen
def disable():
    allevidence.config(state=DISABLED)
    wtonly.config(state=DISABLED)

def enable():
    allevidence.config(state=NORMAL)
    wtonly.config(state=NORMAL)

# Node Class
class NodeFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.header = Frame(self,relief=SUNKEN,borderwidth=1)
        self.subframe=Frame(self, relief=SUNKEN, width=400, height=22, borderwidth=1)
        self.header.pack(side=TOP,fill='x')

        # Data Attributes
        self.var = IntVar() # Enabling for the node frame to collapse
        self.tvar = IntVar() # Marking the node as True (evidence)
        self.fvar = IntVar() # Marking the node as False (evidence)
        self.auxvar = IntVar() # Marking the node as auxiliary
        self.nodetype = StringVar() # Type of node
        self.probability = 0.5 # Probability of node being True
        self.eveprior = 0.5 # Prior probability (only used if the node is an Eve)
        self.parents = [] # List of the node's parents and associated weight label object and symbol
        self.nodevar = None # The symbol of the node's probability
        self.theoretical = None # The theoretical probability (applicable when the node is set as evidence)
        self.equation = None # The equation of the probability (variable, depending on which calculation is used)
        self.baseequation = None # Probability equation expressed in terms of parents only
        self.condensedequation = None # Probability equation after substitution of current evidence(Bayesian mode)
        self.fullequation = None # Probability equation in terms of Eve probability
        self.evidenceequation = None # Probability equation after substitution of all user set evidence (Investigation)
        self.wtlist =[] # List of weight symbols associated with the node
        self.evelist = [] # List of probability symbols of the node's Eves
        self.eveslist = [] # List of the node's Eves (as node objects)
        self.ancestorlist = [] # List of all ancestor nodes
        self.evidenceancestorlist = [] # List of ancestors that are in the set of evidence nodes
        self.contradiction = False # True if a child contradicts its parent/ancestor
        self.tracker = -1 # For cycle detection
        # Although many attributes may be calculated from other ones, they are used many times and it is faster to
        # store them rather than generate them repeatedly

        # Widget Creation
        self.label=Label(self.header, text='{:.2f}'.format(self.probability), anchor=CENTER)
        self.togglebutton=Checkbutton(self.header,width=2,text='+',variable =self.var,
                                      style='Toolbutton',command=self.toggle)
        self.entry = Entry(self.header, width =10)
        self.NodeDropdown = Combobox(self.subframe, textvariable=self.nodetype)
        self.NodeDropdown['values'] = ('Main', 'Interaction', 'Exclusion', 'Inverted', 'Inverted Interaction')# May add
        self.ForceTrue = Checkbutton(self.subframe, text='True',variable=self.tvar, command=self.Tbold)
        self.ForceFalse = Checkbutton(self.subframe, text='False',variable=self.fvar, command=self.Fbold)
        self.DeleteButton = Button(self.subframe,text='Delete',command=self.deletenode)
        self.ForceAux = Checkbutton(self.subframe, text='Auxiliary',variable=self.auxvar, command=self.auxiliary)

        # Widget Packing
        self.label.pack(side=BOTTOM, fill='x')
        self.togglebutton.pack(side=LEFT)
        self.entry.pack(side=RIGHT, pady=2, anchor='e', fill='x', expand=True)
        self.subframe.pack(side=TOP, fill=BOTH, expand=True)
        self.NodeDropdown.pack(side=TOP)
        self.ForceTrue.pack(side=LEFT)
        self.ForceFalse.pack(side=LEFT)
        self.DeleteButton.pack(side=BOTTOM)
        self.ForceAux.pack(side=BOTTOM)

        # Event Binding
        self.label.bind('<ButtonPress-1>', self.StartMove)
        self.label.bind('<ButtonRelease-1>', self.StopMove)
        self.label.bind('<B1-Motion>',self.OnMotion)
        self.label.bind('<Shift-Button-1>', self.storeedge)
        self.label.bind('<Shift-B1-Motion>', self.nothing)
        self.label.bind('<Alt-Button-1>', self.removeedge)
        self.label.bind('<Alt-B1-Motion>', self.nothing)
        self.NodeDropdown.bind('<<ComboboxSelected>>',self.typelabel)

        # Initial State
        self.toggle(False)
        self.nodetype.set('Main')

    # Probability Calculation based on Parents
    def calcprob(self,fast=False):
        global CalcNodeList
        if self not in CalcNodeList: # CalcNodeList stores already calculated nodes to prevent repeat calculation
            for i in self.parents: # Ensures that parents are always calculated before children
                if i[0].probability == -1:
                    i[0].calcprob()
                    CalcNodeList.append(i)
            n = len(self.parents)
            def expandcalc(): # Function used to expand and evaluate equations
                counter = 0 # Count actual evidence (input evidence is removed and restored stepwise during update)
                for x in NodeList:
                    if x.tvar.get() == True or x.fvar.get == True:
                        counter += 1
                if counter == 0 and EvidenceList != [] and modevar.get() == 2:  # Equation using full input evidence
                    calculating2 = self.equation
                    for x in self.parents:
                        if x[0] not in list(zip(*EvidenceList))[0]:
                            calculating2 = calculating2.subs(x[0].nodevar, x[0].evidenceequation)
                        else:
                            if list(zip(*EvidenceList))[1][list(zip(*EvidenceList))[0].index(x[0])] == 'T':
                                calculating2 = calculating2.subs(x[0].nodevar, 1)
                            else:
                                calculating2 = calculating2.subs(x[0].nodevar, 0)
                    self.evidenceequation = removeexponent(calculating2)
                if EvidenceList != [] and modevar.get() == 1:  # Calculate equation based on temporary current evidence
                    self.condensedequation = self.equation
                    for x in self.parents:
                        self.condensedequation = self.condensedequation.subs(x[0].nodevar, x[0].condensedequation)
                    self.condensedequation = removeexponent(self.condensedequation)

                # Expresses equation in terms parentless nodes (Eves) and removes all exponents
                self.equation = self.equation.subs({x[0].nodevar : x[0].equation for x in self.parents})
                self.equation = removeexponent(self.equation)
                if counter == 0 and fast == False:  # Calculates full equation and populates list of terms
                    self.evelist = []
                    self.eveslist = []
                    self.wtlist = []
                    self.ancestorlist = []
                    self.fullequation = self.equation
                    fullterms = re.split('\W+', str(self.fullequation).strip())
                    fullterms = filter(lambda a: ('p' in a) or ('w' in a), fullterms)
                    fullterms = list(set(fullterms))
                    for x in fullterms:
                        if 'p' in x:
                            self.evelist.append(x)
                            self.eveslist.append(pSymbolDict[x])
                        elif 'w' in x:
                            self.wtlist.append(x)
                    for wt in self.wtlist:
                        self.ancestorlist.append([a[1] for a in LineList if a[3] == wSymbolDict[wt]][0])
                self.probability = evaluateequation(self.equation) # Sets probability to calculated result
            if self.tvar.get() != 0: # For nodes set to True
                self.probability = 1
                self.equation = symbols(self.nodevar)
                self.condensedequation = 1 # For nodes set to False
            elif self.fvar.get() != 0:
                self.probability = 0
                self.equation = symbols(self.nodevar)
                self.condensedequation = 0
            elif self.parents == []: # For parentless nodes (Eves)
                self.probability = self.eveprior
                self.equation = symbols(self.nodevar)
                self.fullequation = self.equation
                self.evidenceequation = self.equation
                self.condensedequation = self.equation
            else: # Calculations for all the different types of nodes
                if fast == True:
                    self.equation = self.baseequation
                    expandcalc()
                elif fast == False:
                    if self.nodetype.get() == 'Main':
                        equationstr = ''
                        for i in range(1, n + 1):
                            terms = list(combinations([str(x[0].nodevar + '*' + x[2]) for x in self.parents], i))
                            termlist = []
                            for a in terms:
                                termlist.append('*'.join(list(a)))
                            sumi = '{:+}'.format((-1) ** (i + 1)) + '*(' + '+'.join(termlist) + ')'
                            equationstr = equationstr + sumi
                        self.equation = sympify(equationstr)
                    elif self.nodetype.get() == 'Interaction':
                        terms = '*'.join([str(x[0].nodevar + '*' + x[2]) for x in self.parents])
                        self.equation = sympify(terms)
                    elif self.nodetype.get() == 'Exclusion':
                        equationstr = ''
                        for i in range(1, n + 1):
                            terms = list(combinations([str(x[0].nodevar + '*' + x[2]) for x in self.parents], i))
                            termlist = []
                            for a in terms:
                                termlist.append('*'.join(list(a)))
                            sumi = '{:+}'.format(i * (-1) ** (i + 1)) + '*(' + '+'.join(termlist) + ')'
                            equationstr = equationstr + sumi
                        self.equation = sympify(equationstr)
                    elif self.nodetype.get() == 'Inverted':
                        terms = '1-' + '*'.join([str(x[0].nodevar + '*' + x[2]) for x in self.parents])
                        self.equation = sympify(terms)
                    elif self.nodetype.get() == 'Inverted Interaction':
                        equationstr = ''
                        for i in range(1, n + 1):
                            terms = list(combinations([str(x[0].nodevar + '*' + x[2]) for x in self.parents], i))
                            termlist = []
                            for a in terms:
                                termlist.append('*'.join(list(a)))
                            sumi = '{:+}'.format((-1) ** (i + 1)) + '*(' + '+'.join(termlist) + ')'
                            equationstr = equationstr + sumi
                        equationstr = '1-(' + equationstr + ')'
                        self.equation = sympify(equationstr)
                    # For new node types, add elif blocks here for calculation
                    self.baseequation = self.equation
                    expandcalc()

    # Toggle button shows or hides the subframe with node information
    def toggle(self, show=None):
        show = self.var.get() if show is None else show
        if show:
            self.subframe.pack(side=TOP,fill='x', expand=True)
            self.togglebutton.configure(text='-')
        else:
            self.subframe.forget()
            self.togglebutton.configure(text='+')

    # Links the probability text color to the node type
    def typelabel(self,event):
        self.label.config(foreground=TypeColor[self.nodetype.get()])

    # Enables dragging of nodes and updating of the edge positions
    def StartMove(self,event):
        self.x ,self.y= (event.x, event.y)

    def StopMove(self, event):
        self.x, self.y = (None, None)

    def OnMotion(self,event):
        dx, dy = (event.x - self.x,event.y - self.y)
        x, y = self.winfo_x() + dx, self.winfo_y() + dy
        self.place(x=x,y=y)
        LineStart = [x for x in LineList if x[1]==self]
        LineEnd =[x for x in LineList if x[2]==self]
        for i in LineStart: # Calculations to ensure the end of the arrow is at the closest of 8 positions on the frame
            c = x + 44
            d = y + 23
            e = i[2].winfo_x()
            f= i[2].winfo_y()
            corners1 = [[e, f, (c - e) ** 2 + (d - f) ** 2],
                        [e + 88, f, (c - e - 88) ** 2 + (d - f) ** 2],
                        [e, f + 47, (c - e) ** 2 + (d - f - 47) ** 2],
                        [e + 88, f + 47, (c - e - 88) ** 2 + (d - f - 47) ** 2],
                        [e + 44, f, (c - e - 44) ** 2 + (d - f) ** 2],
                        [e + 88, f + 23, (c - e - 88) ** 2 + (d - f - 23) ** 2],
                        [e + 44, f + 47, (c - e - 44) ** 2 + (d - f - 47) ** 2],
                        [e, f + 23, (c - e) ** 2 + (d - f - 23) ** 2]]
            closest1 = min(corners1,key=lambda x:x[2])
            sheet.coords(i[0],c, d, closest1[0], closest1[1])
            LineStart[LineStart.index(i)][3].place(x=(c+closest1[0])/2, y=(d+closest1[1])/2)
        for i in LineEnd:
            a = i[1].winfo_x()+44
            b = i[1].winfo_y()+23
            corners2 = [[x, y, (a - x) ** 2 + (b - y) ** 2],
                        [x + 88, y, (a - x - 88) ** 2 + (b - y) ** 2],
                        [x, y + 47, (a - x) ** 2 + (b - y - 47) ** 2],
                        [x + 88, y + 47, (a - x - 88) ** 2 + (b - y - 47) ** 2],
                        [x + 44, y, (a - x - 44) ** 2 + (b - y) ** 2],
                        [x + 44, y + 47, (a - x - 44) ** 2 + (b - y - 47) ** 2],
                        [x + 88, y + 23, (a - x - 88) ** 2 + (b - y - 23) ** 2],
                        [x, y + 23, (a - x) ** 2 + (b - y - 23) ** 2]]
            closest2 = min(corners2,key=lambda x:x[2])
            sheet.coords(i[0],a,b, closest2[0], closest2[1])
            LineEnd[LineEnd.index(i)][3].place(x=(a+closest2[0])/2, y=(b+closest2[1])/2)

    # Commands associated with setting a node to True or False
    def Tbold(self):
        if self.fvar.get() != 0 and self.tvar.get() != 0:
            self.fvar.set(False)
            EvidenceList.remove([self, 'F'])
            EvidenceList.append([self, 'T'])
        elif self.tvar.get() == 0 and self.fvar.get() == 0:
            self.label.config(font='Helvetica 8')
            EvidenceList.remove([self, 'T'])
        else:
            self.label.config(font='Helvetica 12 bold')
            EvidenceList.append([self, 'T'])
        self.probability = 1
        self.label.configure(text='{:.2f}'.format(self.probability))

    def Fbold(self):
        if self.fvar.get() != 0 and self.tvar.get() != 0:
            self.tvar.set(False)
            EvidenceList.remove([self, 'T'])
            EvidenceList.append([self, 'F'])
        elif self.tvar.get() == 0 and self.fvar.get() == 0:
            self.label.config(font='Helvetica 8')
            EvidenceList.remove([self, 'F'])
        else:
            self.label.config(font='Helvetica 12 bold')
            EvidenceList.append([self, 'F'])
        self.probability = 0
        self.label.configure(text='{:.2f}'.format(self.probability))

    # Creation of Edges and updating of all relevant global lists and dictionaries
    def storeedge(self,event):
        global EdgeEnds
        global LineList
        global WeightID
        if len(EdgeEnds) < 2:
            EdgeEnds.append(self)
            if len(EdgeEnds) == 2:
                LineListCopy = []
                for x in LineList:
                    LineListCopy.append(tuple(x))
                LineStart = set(x for x in LineListCopy if x[1] == EdgeEnds[0])
                LineEnd = set(x for x in LineListCopy if x[2] == EdgeEnds[1])
                if LineList == [] or LineStart.intersection(LineEnd) == set():
                    a = EdgeEnds[0].winfo_x()+44
                    b = EdgeEnds[0].winfo_y()+23
                    c = EdgeEnds[1].winfo_x()
                    d = EdgeEnds[1].winfo_y()
                    corners = [[c, d, (a - c) ** 2 + (b - d) ** 2],
                               [c + 88, d, (a - c - 88) ** 2 + (b - d) ** 2],
                               [c, d + 47, (a - c) ** 2 + (b - d - 47) ** 2],
                               [c + 88, d + 47, (a - c - 88) ** 2 + (b - d - 47) ** 2],
                               [c + 44, d, (a - c - 44) ** 2 + (b - d) ** 2],
                               [c + 88, d + 23, (a - c - 88) ** 2 + (b - d - 23) ** 2],
                               [c + 44, d + 47, (a - c - 44) ** 2 + (b - d - 47) ** 2],
                               [c, d + 23, (a - c) ** 2 + (b - d - 23) ** 2]]
                    LineID = sheet.create_line(a,b,min(corners,key=lambda x:x[2])[0],
                                           min(corners,key=lambda x:x[2])[1], arrow=LAST)
                    Weight = Entry(sheet,width=3)
                    Weight.place(x=(a+min(corners,key=lambda x:x[2])[0])/2,y=(b+min(corners,key=lambda x:x[2])[1])/2)
                    Weight.insert(0,1)
                    wtcopy = float(Weight.get())
                    LineNodes = [LineID, EdgeEnds[0],EdgeEnds[1], Weight, wtcopy]
                    LineList.append(LineNodes)
                    wSymbolDict.update({'w' + str(WeightID):Weight})
                    globals().update({'w' + str(WeightID): symbols('w' + str(WeightID))})
                    self.parents.append([EdgeEnds[0],Weight,'w' + str(WeightID)])
                    WeightID +=1
        else:
            EdgeEnds = [self]

    # Removal of edges and updating of all relevant global lists and dictionaries
    def removeedge(self,event):
        global EdgeEnds2
        global LineList
        if len(EdgeEnds2) < 2:
            EdgeEnds2.append(self)
            if len(EdgeEnds2) == 2:
                LineListCopy = []
                for x in LineList:
                    LineListCopy.append(tuple(x))
                LineStart = set(x for x in LineListCopy if x[1] == EdgeEnds2[0])
                LineEnd = set(x for x in LineListCopy if x[2] == EdgeEnds2[1])
                if LineStart.intersection(LineEnd) != set():
                    self.parents.remove([x for x in self.parents if x[0] == EdgeEnds2[0]][0])
                    if [x for x in wSymbolDict if wSymbolDict[x] ==
                        list(LineStart.intersection(LineEnd))[0][3]][0] in self.wtlist:
                        self.wtlist.remove([x for x in wSymbolDict if wSymbolDict[x] ==
                                        list(LineStart.intersection(LineEnd))[0][3]][0])
                    del wSymbolDict[[x for x in wSymbolDict if wSymbolDict[x]==
                                     list(LineStart.intersection(LineEnd))[0][3]][0]]
                    sheet.delete(list(LineStart.intersection(LineEnd))[0][0])
                    list(LineStart.intersection(LineEnd))[0][3].forget()
                    list(LineStart.intersection(LineEnd))[0][3].destroy()
                    LineList.remove(list(list(LineStart.intersection(LineEnd))[0]))
        else:
            EdgeEnds2 = [self]

    def nothing(self,event):
        pass

    def auxiliary(self):
        if self.auxvar.get() == True:
            self.header.config(relief=RAISED)
            for a in [x[3] for x in LineList if x[2]==self]:
                a.delete(0,END)
                a.insert(0,1)
            for y in LineList:
                if y[2]==self:
                    y[4]=1
            for z in self.parents:
                z.append(z[2])
                z[2]=str(1)
        else:
            self.header.config(relief=SUNKEN)
            for z in self.parents:
                z[2]=z[3]
                del z[3]

    # Node Deletion and updating of all relevant global lists and dictionaries
    def deletenode(self):
        for x in NodeList:
            Children = [x for x in filter(lambda x: x.parents!=[],NodeList) if self in list(zip(*x.parents))[0]]
        if Children != []:
            for i in Children:
                i.parents.remove([a for a in i.parents if a[0]==self][0])
        AffectedLines = [x for x in LineList if x[1] == self]+[x for x in LineList if x[2] == self]
        for i in AffectedLines:
            del wSymbolDict[[x for x in wSymbolDict if wSymbolDict[x] == i[3]][0]]
            sheet.delete(i[0])
            LineList.remove(i)
            i[3].forget()
            i[3].destroy()
        del pSymbolDict[self.nodevar]
        NodeList.remove(self)
        if EvidenceList != [] and self in list(zip(*EvidenceList))[0]:
            EvidenceList.remove(EvidenceList[list(zip(*EvidenceList))[0].index(self)])
        self.forget()
        self.destroy()

def createnode(event): # Node creation and updating of all relevant global lists and dictionaries
    global NodeID
    NewNode = NodeFrame(sheet)
    NewNode.place(x=event.x, y=event.y)
    NodeList.append(NewNode)
    pSymbolDict.update({'p'+str(NodeID):NewNode})
    globals().update({'p'+str(NodeID):symbols('p'+str(NodeID))})
    NewNode.nodevar ='p'+str(NodeID)
    NodeID += 1
    message.config(text='')

def removeevidence(): # Used for evidence removal during updating, original input evidence is stored in EvidenceList
    for x in NodeList:
        x.tvar.set(False)
        x.fvar.set(False)
    update()

def clearevidence(): # For the user to clear evidence. EvidenceList is also cleared.
    global EvidenceList
    for x in NodeList:
        x.tvar.set(False)
        x.fvar.set(False)
        EvidenceList = []
        x.label.config(font='Helvetica 8')
    update()

def clearpriors(): # Clearing of priors for Eves (reset to default 0.5)
    for x in NodeList:
        x.eveprior = 0.5
    update()

def clearlinecolor(): # Clearing of line colors, back to black
    for x in LineList:
        sheet.itemconfig(x[0], fill='black')

def cycledetect(): # using Depth First Search
    cycles = 0
    for x in NodeList:
        x.tracker = -1
    def cyclesub(y):
        nonlocal templist
        nonlocal cycles
        y.tracker = 0
        templist.append(y)
        if y.parents != [] and set(templist).intersection(list(zip(*y.parents))[0])!= set():
            cycles +=1
        if y.parents != []:
            for z in list(zip(*y.parents))[0]:
                if z.tracker == -1:
                    cyclesub(z)
        y.tracker = 1
        templist.pop()
    for x in NodeList:
        if x.tracker == -1:
            templist = [] # This is a stack storing the current path being explored
            cyclesub(x)
    return cycles

def update(fast=False): # Update procedure called during probability updating
    global CalcNodeList
    global SymbolList
    sortnode = sorted(NodeList, key=lambda x: len(x.wtlist))
    if fast == True: # Calculate only nodes affected by nodes in ActiveList and nodes that affect nodes in CalcList
        CalcNodeList = [x for x in NodeList
                        if (set(ActiveList).intersection(set(x.ancestorlist)) == set()
                            and x not in ActiveList and x not in CalcList)
                        or (x not in set().union(*[y.ancestorlist for y in CalcList])
                            and x not in CalcList and x not in ActiveList)]
    else:
        CalcNodeList = []
    SymbolList = sorted(pSymbolDict)+sorted(wSymbolDict)
    for i in set(NodeList).difference(set(CalcNodeList)):
        i.probability = -1
    if fast == True:
        for i in sortnode:
            i.calcprob(fast=True)
            i.label.configure(text='{:.2f}'.format(float(i.probability)))
    else:
        for i in NodeList:
            i.calcprob()
            i.label.configure(text='{:.2f}'.format(float(i.probability)))

def updatebutton(): # Radiobutton allows choice of update algorithm
    c = cycledetect()
    if c != 0:
        message.configure(text='Error: Cycles detected')
    elif modevar.get() == 1:
        bayes()
    else:
        forward()

def removeexponent(eq): # Removes exponents from equations
    if ('*' not in str(eq)) and ('+' not in str(eq)) and ('-' not in str(eq)):
        eq = sympify(re.sub(r'\*\*.(\d)?', '', str(eq)))
    else:
        eq = sympify(re.sub(r'\*\*.(\d)?', '', str(eq.expand()))) #This is most time consuming step
    return eq

def evaluateequation(eq,bayes=False): # Evaluates equations with current probability and weight values
    if eq == 0:
        return 0
    else:
        fullterms = re.split('\W+', str(eq).strip())
        fullterms = filter(lambda a: ('p' in a) or ('w' in a), fullterms)
        fullterms = list(set(fullterms))
        relevantsymbolsstr = [x for x in SymbolList if x in fullterms]
        relevantsymbols = [symbols(x) for x in relevantsymbolsstr]
        relevantvalues = [float(pSymbolDict[x].probability) for x in relevantsymbolsstr if 'p' in x] \
                         + [float(wSymbolDict[x].get()) for x in relevantsymbolsstr if 'w' in x]
        f = Lambdify(relevantsymbols, eq)
        eq = f(relevantvalues)[0] # Note syntax for Lambdify is specific to symengine, which outputs array
        return eq

def bayes(): # Bayesian updating of network
    global message
    global CalcList
    global ActiveList
    message.configure(text='')
    for x in NodeList: # Reset node attributes that are changed during previous updates
        x.evidenceancestorlist = []
        x.contradiction = False
        x.label.config(relief='flat')
    if EvidenceList == []: # If no evidence, updating is done in the forward direction using update()
        update()
    else:
        sortnode = sorted(NodeList,key=lambda x : len(x.wtlist))
        sortevidence = list(filter(lambda a: a in list(zip(*EvidenceList))[0],sortnode))
        sortnotevidence = list(filter(lambda a: a not in list(zip(*EvidenceList))[0],sortnode))
        updatedprob =[]
        evidenceprob = sympify(1)
        removeevidence()

        for x in sortnode: # This creates an evidence ancestor list for all nodes
            for w in x.wtlist:
                wt = wSymbolDict[w]
                parent = list(filter(lambda a: a[3]==wt, LineList))[0][1]
                if parent in list(zip(*EvidenceList))[0]:
                    x.evidenceancestorlist.append(parent)

        # Calculation of the probability of the evidence as product of probabilities as evidence is added stepwise
        CalcList = sortevidence[:] # CalcList and ActiveList are used to prevent unnecessary repeat calculations
        ActiveList = []
        EvidenceCombo = [] # EvidenceCombo and ComboEquations are used for memoization
        ComboEquations = []

        for x in sortevidence: # Calculation of probability of evidence Eves first, then update after setting
            if x.evidenceancestorlist == []:
                if EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'T':
                    evidenceprob = evidenceprob * x.condensedequation
                    x.tvar.set(True)
                elif EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'F':
                    evidenceprob = evidenceprob * (1-x.condensedequation)
                    x.fvar.set(True)
                ActiveList.append(x)
                CalcList.remove(x)
                EvidenceCombo.append(x)
                ComboEquations.append([EvidenceCombo[:],evidenceprob])
        update(fast=True)

        for x in sortevidence: # Calculation of probability of remaining evidence nodes
            if x.evidenceancestorlist != []:
                if EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'T':
                    evidenceprob = evidenceprob * x.condensedequation
                    x.tvar.set(True)
                elif EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'F':
                    evidenceprob = evidenceprob * (1 - x.condensedequation)
                    x.fvar.set(True)
                ActiveList = [x]
                CalcList.remove(x)
                EvidenceCombo.append(x)
                ComboEquations.append([EvidenceCombo[:], evidenceprob])
                update(fast=True)
        evidenceprob = removeexponent(evidenceprob)
        evidenceprob = evaluateequation(evidenceprob)
        if evidenceprob == 0 or evidenceprob < 0:
            message.configure(text='Error: Contradictory Evidence')

        else: # Calculation of the joint probability of each node and the evidence
            for x in sortnotevidence :
                nodeevidenceprob = 1
                removeevidence()
                combined = sortevidence[:]
                combined.append(x)
                cumulativelist = []
                firsttime = 1
                CalcList = list(filter(lambda a: a in combined,sortnode))
                ActiveList = []
                for y in list(filter(lambda a: a in combined,sortnode)):
                    cumulativelist.append(y)
                    if set(cumulativelist).difference(set(sortevidence))== set(): # Memoization
                        nodeevidenceprob = [a[1] for a in ComboEquations if a[0]==cumulativelist][0]
                        if EvidenceList[list(zip(*EvidenceList))[0].index(y)][1] == 'T':
                            y.tvar.set(True)
                        elif EvidenceList[list(zip(*EvidenceList))[0].index(y)][1] == 'F':
                            y.fvar.set(True)
                        ActiveList.append(y)
                        CalcList.remove(y)
                    else:
                        if firsttime == 1:
                            update(fast=True)
                            firsttime = 0
                        if y in list(zip(*EvidenceList))[0]:
                            if EvidenceList[list(zip(*EvidenceList))[0].index(y)][1] == 'T':
                                nodeevidenceprob = nodeevidenceprob * y.condensedequation
                                y.tvar.set(True)
                            elif EvidenceList[list(zip(*EvidenceList))[0].index(y)][1] == 'F':
                                nodeevidenceprob = nodeevidenceprob * (1 - y.condensedequation)
                                y.fvar.set(True)
                            ActiveList=[y]
                            CalcList.remove(y)
                            update(fast=True)
                        else:
                            nodeevidenceprob = nodeevidenceprob * y.condensedequation
                            y.tvar.set(True)
                            ActiveList = [y]
                            CalcList.remove(y)
                            update(fast=True)
                x.tvar.set(False)
                if x.parents == []:
                    x.probability = x.eveprior
                nodeevidenceprob = removeexponent(nodeevidenceprob)
                nodeevidenceprob = evaluateequation(nodeevidenceprob)
                updatedprob.append([x,nodeevidenceprob/evidenceprob])
            update()
            for x in sortnotevidence:
                x.probability = list(filter(lambda a: a[0]==x, updatedprob))[0][1]
                x.label.config(text='{:.2f}'.format(float(x.probability)))
                if x.evelist == []:
                    x.eveprior = x.probability


def forward(): # Uses gradient descent to optimize Eve probabilities and weights to investigate contradictory evidence
    global message
    global CalcList
    global ActiveList
    message.configure(text='')
    global LineList
    if EvidenceList == []:
        update()
    else:
        for x in NodeList: # Reset evidence ancestor list
            x.evidenceancestorlist = []
            x.contradiction = False
            x.label.config(relief='flat')

        removeevidence() # This forces an update that generates the equations and populates the Eve lists

        sortnode = sorted(NodeList, key=lambda x: len(x.wtlist))
        sortevidence = list(filter(lambda a: a in list(zip(*EvidenceList))[0], sortnode))
        tempevelist = []
        subtempevelist = []
        evidenceevelist = []

        for x in sortnode: # This creates an evidence ancestor list for all nodes
            for w in x.wtlist:
                wt = wSymbolDict[w]
                parent = list(filter(lambda a: a[3]==wt, LineList))[0][1]
                if parent in list(zip(*EvidenceList))[0]:
                    x.evidenceancestorlist.append(parent)

        uniqueeves = set() # This creates an evidence Eve list
        for x in sortevidence:
            if x.evidenceancestorlist == []:
                evidenceevelist.append(x)
            if set(x.eveslist).difference(uniqueeves) != set():
                uniqueeves = uniqueeves.union(set(x.eveslist))
                if x not in evidenceevelist:
                    evidenceevelist.append(x)

        for x in sortevidence: # Creates a list of all Eves of evidence nodes
            for y in x.eveslist:
                tempevelist.append(y)
        tempevelist = list(set(tempevelist).difference(set(sortevidence)))

        for x in evidenceevelist: # Creates a list of all Eves of evidence Eve nodes
            for y in x.eveslist:
                subtempevelist.append(y)
        subtempevelist = list(set(subtempevelist).difference(set(evidenceevelist)))

        # Gradient Descent is used first to optimize prior probabilities
        if allevidencevar.get() == False: # Gradient Descent to match evidence Eves only
            evidences = evidenceevelist
            eves = subtempevelist
        else: # Gradient Descent to match all evidence
           evidences = sortevidence
           eves = tempevelist
        # Calculating the gradient equation
        if eves != []:
            loss = sympify(0)
            for x in evidences:
                if [a[1] for a in EvidenceList if a[0]==x][0] == 'T':
                    p = 1
                else:
                    p = 0
                if allevidencevar.get() == False:
                    equation = x.evidenceequation
                else:
                    equation = x.fullequation
                loss = loss + (equation -p)**2 # Least Squares
            grad = []
            for x in eves:
                grad.append(diff(loss,symbols(x.nodevar)))
            norm = 1 # Gradient Descent Procedure
            randcount = -1
            while norm > 0.00001 or randcount < 1: # Threshold for gradient norm
                calculatedgrad = []
                for x in grad:
                    calculating = evaluateequation(x)
                    if randcount < 0:
                        calculatedgrad.append(calculating+0.1*(random()-0.5))# May increase magnitude of random step
                    else:
                        calculatedgrad.append(calculating)
                norm = sum(map(lambda a :a**2, calculatedgrad))
                change = 0
                for x in eves: # Enforces that probability is between 0 and 1
                    init = x.probability
                    x.probability -= 0.25*calculatedgrad[eves.index(x)] # Step size may be changed
                    if x.probability < 0:
                        x.probability = 0
                    if x.probability >1:
                        x.probability = 1
                    final = x.probability
                    change += (final-init)**2
                if change < 0.000001: # Threshold for size of variable change after a step
                    break
                randcount +=1
                if randcount > 100000: # Maximum steps
                    break
            for x in eves:
                x.eveprior = x.probability


        update() # Update again after optimizing priors

        CalcList = []
        ActiveList = sortevidence[:]

        # This procedure avoids recalculation of evidence nodes that are independent of other evidence nodes
        for x in sortevidence: # Restores evidence and tests for contradictions in evidence with no evidence ancestors
            if x.evidenceancestorlist == []:
                x.theoretical = x.probability
                if EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'T':
                    x.tvar.set(True)
                    if x.theoretical < 0.1: # May make threshold larger to increase sensitivity to contradictions
                        x.contradiction = True
                        x.label.config(relief='sunken')
                elif EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'F':
                    x.fvar.set(True)
                    if (1 - x.theoretical) < 0.1: # May make threshold larger to increase sensitivity to contradictions
                        x.contradiction = True
                        x.label.config(relief='sunken')
            else:
                if EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'T':
                    x.tvar.set(True)
                elif EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'F':
                    x.fvar.set(True)

        for x in sortevidence: # Determines if each evidence node is in contradiction with all others
            if x.evidenceancestorlist != []:
                if EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'T':
                    x.tvar.set(False)
                    ActiveList.remove(x)
                    CalcList = [x]
                    update(fast=True)
                    ActiveList.append(x)
                    x.theoretical = x.probability
                    x.tvar.set(True)
                    if x.theoretical < 0.05:
                        x.contradiction = True
                        x.label.config(relief='sunken')
                elif EvidenceList[list(zip(*EvidenceList))[0].index(x)][1] == 'F':
                    x.fvar.set(False)
                    ActiveList.remove(x)
                    CalcList = [x]
                    update(fast=True)
                    ActiveList.append(x)
                    x.theoretical = x.probability
                    x.fvar.set(True)
                    if (1 - x.theoretical) < 0.05:
                        x.contradiction = True
                        x.label.config(relief='sunken')

        update() # Update again after restoring evidence, equations not affected

        for x in sortnode:
            x.label.config(text='{:.2f}'.format(float(x.probability)))
        contradictlist = []
        for x in sortevidence:
            if x.contradiction == True:
                contradictlist.append(x)

        # Gradient Descent on weights to diagnose network
        if allevidencevar.get() == False: # Gradient Descent to match contradictions only
            evidences = contradictlist
        else: # Gradient Descent to match all evidence
           evidences = sortevidence
        if contradictlist != [] or allevidencevar.get() == True:
            loss = sympify(0)
            for x in evidences:
                if x.tvar.get() == True:
                    p = 1
                else:
                    p = 0
                if allevidencevar.get() == False:
                    equation = x.evidenceequation
                else:
                    equation = x.fullequation
                loss = loss + (equation - p) ** 2 # Least Squares
            grad = []
            combinedwt = []
            for x in evidences:
                for y in x.wtlist:
                    combinedwt.append(y)
            combinedwt = list(set(combinedwt))
            for w in combinedwt:
                wt = wSymbolDict[w]
                LineList[LineList.index(list(filter(lambda a:a[3]==wt, LineList))[0])][4]=float(wt.get())
            for w in combinedwt:
                grad.append(diff(loss,symbols(w)))
            norm = 1 # Gradient Descent Procedure
            randcount = -1
            while norm > 0.00001 or randcount < 1: # Threshold for gradient
                calculatedgrad = []
                for x in grad:
                    calculating = evaluateequation(x)
                    if randcount < 0:
                        calculatedgrad.append(calculating+0.1*(random()-0.5)) # May increase magnitude of random step
                    else:
                        calculatedgrad.append(calculating)
                norm = sum(map(lambda a :a**2, calculatedgrad))
                change = 0
                for w in combinedwt:
                    wt = wSymbolDict[w]
                    init = float(wt.get())
                    wt.delete(0,END)
                    wt.insert(0,float(init) - 0.25*calculatedgrad[combinedwt.index(w)]) # Step size may be changed
                    if wtonlyvar.get() == 1:
                        if float(wt.get()) < 0:
                            wt.delete(0, END)
                            wt.insert(0,0)
                        if float(wt.get()) >1:
                            wt.delete(0, END)
                            wt.insert(0, 1)
                    final = float(wt.get())
                    change += (final-init)**2
                if change < 0.000001: # Threshold for change after step
                    break
                randcount += 1
                if randcount > 100000: # Threshold for number of steps
                    break
            ActiveList = [y[0] for y in EvidenceList if y[0].probability == 0]
            NegativeList = [y for y in NodeList if y.nodetype.get() == 'Inverted'
                            or y.nodetype.get() == 'Inverted Interaction']
            NegEvidenceList = list(set().union(*[[z for z in y.evidenceancestorlist if z.probability ==0]
                                                 for y in NegativeList]))
            NegRelatedList = [y for y in NodeList
                                 if (set(NegEvidenceList).intersection(set(y.ancestorlist)) != set()
                                     or y in NegEvidenceList or y in NegativeList)
                                 and (y in set().union(*[z.ancestorlist for z in NegativeList])
                                      or y in NegativeList or y in NegEvidenceList)]
            NegRelatedWt = [a for a in combinedwt if
                                    list(filter(lambda z: z[3]==wSymbolDict[a], LineList))[0][1] in NegRelatedList and
                                    list(filter(lambda z: z[3]==wSymbolDict[a], LineList))[0][2] in NegRelatedList]
            for w in combinedwt: # Colors are used to show if the weights need to be increased or decreased
                wt = wSymbolDict[w]
                line = LineList[LineList.index(list(filter(lambda a:a[3]==wt, LineList))[0])][0]
                original = LineList[LineList.index(list(filter(lambda a: a[3] == wt, LineList))[0])][4]
                final = float(wt.get())
                delta = final-float(original)
                if -0.05 < delta < 0.05:
                    flagged = []
                    for x in evidences:
                        if x.tvar.get() == True and x.theoretical == 0:
                            if x.nodetype.get() == 'Main' or (x.nodetype.get() =='Exclusion'\
                            and sum([y.probability for y in x.parents])<0.1*len(x.parents))\
                            or x.nodetype.get() == 'Interaction':
                                CalcList = [y[0] for y in x.parents if y[0].probability < 0.1]
                                RelevantNodes = [y for y in NodeList
                                 if (set(ActiveList).intersection(set(y.ancestorlist)) != set()
                                     or y in ActiveList or y in CalcList)
                                 and (y in set().union(*[z.ancestorlist for z in CalcList])
                                      or y in CalcList or y in ActiveList)]
                                RelevantNodes.append(x)
                                flagged.append([a for a in x.wtlist if
                                    list(filter(lambda z: z[3]==wSymbolDict[a], LineList))[0][1] in RelevantNodes and
                                    list(filter(lambda z: z[3]==wSymbolDict[a], LineList))[0][2] in RelevantNodes and
                                    a not in NegRelatedWt])
                    # For evidence = True, but theoretical = 0 due to ancestors being 0.
                    if w in set().union(*flagged) and wtonlyvar.get() != 1:
                        color = '#0000ff'
                    else:
                        color = '#000000'
                elif delta < 0 :
                    R = int(min((original-max(final,0))*150+max(-1*final,0)*150+100,255))
                    if -1*final > 0:
                        G = int(min(-1*final*150+100,255))
                    else:
                        G = 0
                    color = RGBtoHex([R,G,0])
                elif delta > 0:
                    G = int(min((min(1, final)-original) *150+100,255))
                    if final -1 >0:
                        B = int(min((final - 1)*150+100,255))
                    else:
                        B = 0
                    color = RGBtoHex([0,G,B])
                else:
                    color = '#000000'
                sheet.itemconfig(line, fill=color)
                tempstorage = float(wt.get())
                wt.delete(0, END)
                wt.insert(0, original)
                LineList[LineList.index(list(filter(lambda a: a[3] == wt, LineList))[0])][4]=tempstorage

def RGBtoHex(x): # Convert RGB color to Hex
    hexcolor = '#'
    for i in x:
        if len(hex(i))==3:
            hexcolor = hexcolor + '0'
        hexcolor = hexcolor + hex(i)[2:]
    return hexcolor

def save(event): # Save network as text file
    NodeData =[]
    LineData = []
    for x in NodeList:
        x.update_idletasks()
        NodeData.append([NodeList.index(x),x.entry.get(),x.tvar.get(),x.fvar.get(),
                         x.winfo_x(),x.winfo_y(),x.nodetype.get(),x.eveprior,x.auxvar.get()])
    for x in LineList:
        LineData.append([LineList.index(x),NodeList.index(x[1]),NodeList.index(x[2]),x[3].get()])
    FullData = [NodeData,LineData]
    file = input('Enter Filepath and Name: ')
    print('saving')
    with open(file,'wb') as f:
        pickle.dump(FullData,f)
    print('done')

def reload(event): # Load by recreating nodes and edges from information in text file
    global NodeID
    global EdgeEnds
    global EdgeEnds2
    global LineList
    global WeightID
    TempNodeList = NodeList[:]
    for x in TempNodeList:
        x.deletenode()
    file = input('Enter Filepath and Name: ')
    NodeID = 0
    WeightID = 0
    EdgeEnds = []
    EdgeEnds2 = []
    LineList = []
    with open(file, 'rb') as f:
        FullData=pickle.load(f)
    NodeData = FullData[0]
    LineData = FullData[1]
    for x in NodeData:
        NewNode = NodeFrame(sheet)
        NewNode.place(x=int(x[4]), y=int(x[5]))
        NewNode.entry.insert(0,x[1])
        NewNode.tvar.set(x[2])
        NewNode.fvar.set(x[3])
        NewNode.nodetype.set(x[6])
        NewNode.eveprior = x[7]
        NewNode.auxvar.set(x[8])
        NewNode.label.config(foreground=TypeColor[NewNode.nodetype.get()])
        if NewNode.tvar.get() != 0:
            NewNode.label.config(font='Helvetica 12 bold')
            EvidenceList.append([NewNode, 'T'])
        elif NewNode.fvar.get() != 0:
            EvidenceList.append([NewNode, 'F'])
            NewNode.label.config(font='Helvetica 12 bold')
        NodeList.append(NewNode)
        pSymbolDict.update({'p' + str(NodeID): NewNode})
        globals().update({'p'+str(NodeID):symbols('p'+str(NodeID))})
        NewNode.nodevar ='p'+str(NodeID)
        NodeID += 1
    for x in LineData:
        EdgeEnds.append(NodeList[x[1]])
        EdgeEnds.append(NodeList[x[2]])
        EdgeEnds[0].update_idletasks()
        EdgeEnds[1].update_idletasks()
        a = EdgeEnds[0].winfo_x() + 44
        b = EdgeEnds[0].winfo_y() + 23
        c = EdgeEnds[1].winfo_x()
        d = EdgeEnds[1].winfo_y()
        corners = [[c, d, (a - c) ** 2 + (b - d) ** 2],
                   [c + 88, d, (a - c - 88) ** 2 + (b - d) ** 2],
                   [c, d + 47, (a - c) ** 2 + (b - d - 47) ** 2],
                   [c + 88, d + 47, (a - c - 88) ** 2 + (b - d - 47) ** 2],
                   [c + 44, d, (a - c - 44) ** 2 + (b - d) ** 2],
                   [c + 88, d + 23, (a - c - 88) ** 2 + (b - d - 23) ** 2],
                   [c + 44, d + 47, (a - c - 44) ** 2 + (b - d - 47) ** 2],
                   [c, d + 23, (a - c) ** 2 + (b - d - 23) ** 2]]
        LineID = sheet.create_line(a, b, min(corners, key=lambda x: x[2])[0],
                                   min(corners, key=lambda x: x[2])[1], arrow=LAST)
        Weight = Entry(sheet, width=3)
        Weight.place(x=(a + min(corners, key=lambda x: x[2])[0]) / 2,
                     y=(b + min(corners, key=lambda x: x[2])[1]) / 2)
        Weight.insert(0, x[3])
        wtcopy = float(Weight.get())
        LineNodes = [LineID, EdgeEnds[0], EdgeEnds[1], Weight, wtcopy]
        LineList.append(LineNodes)
        wSymbolDict.update({'w' + str(WeightID): Weight})
        globals().update({'w' + str(WeightID): symbols('w' + str(WeightID))})
        EdgeEnds[1].parents.append([EdgeEnds[0], Weight, 'w' + str(WeightID)])
        WeightID += 1
        EdgeEnds =[]
    for i in NodeList:
        if i.auxvar.get() == True:
            i.header.config(relief=RAISED)
            for a in [x[3] for x in LineList if x[2]==i]:
                a.delete(0,END)
                a.insert(0,1)
            for y in LineList:
                if y[2]==i:
                    y[4]=1
            for z in i.parents:
                z.append(z[2])
                z[2]=str(1)
    update()

def help(event): # Displays help
    print('Instructions:\nRight-Click = Create node\nLeft-Click Hold = Drag node\n'
          'Shift-Left-Click = Create edge connecting parent to child node\n'
          'Alt-Left-Click = Delete edge (same order as to create edge)\n'
          'Click on + to expand node, set evidence, select node type, or delete node\n'
          'Contol-b = Set prior\nControl-s = Save as text file\n'
          'Control-o = Load text file\nControl-h = Help\n'
          'Control-p = profile the update() function (for developers)')

def profileupdate(event): # Used for optimization
    cProfile.run('update()')

def biasprior(event):
    activenode = None
    while activenode == None:
        nodename = input('Enter name of node: ')
        for x in NodeList:
            if x.entry.get() == nodename:
                activenode = x
        if activenode == None:
            print('Invalid Name')
    newprior = None
    while newprior == None:
        enterprior = input('Enter prior: ')
        if not re.match('(\d)*(.)?(\d)+',enterprior):
            print('Invalid Entry. Must be numerical.')
        else:
            newprior = float(enterprior)
    activenode.eveprior = newprior


sheet.bind('<Button-3>', createnode)
root.bind('<Control-s>', save)
root.bind('<Control-o>', reload)
root.bind('<Control-h>', help)
root.bind('<Control-p>',profileupdate)
root.bind('<Control-b>',biasprior)

mainloop()

