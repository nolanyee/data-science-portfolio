# This program takes enrollment data and creates an exam schedule with no time conflicts using sets and graph coloring

enrollment = {}
timeslots = {0:[]}
currentstudentid = 0
lasttimeslotid = 0
courses = set()

class coursenode(): # Each course is represented by a node
    def __init__(self,name):
        global courses
        self.name = name
        self.connections = set() # Edges are created between 2 nodes if any student is taking both courses
        courses=courses.union([self])

def addstudent(*args):
    global currentstudentid
    courselist =set()
    for arg in args:
        course = arg
        if course not in [x.name for x in courses]: # New course is created if not in previous student's schedules
            course = coursenode(course)
        else:
            course = [x for x in courses if course == x.name][0]
        courselist = courselist.union([course]) # Set of all courses a student is taking
    enrollment.update({currentstudentid:courselist})
    for x in courselist: # Edges are created between all courses a student is enrolled in (if not already connected)
        x.connections = x.connections.union(courselist.difference([x]))
    currentstudentid += 1

def schedule(display=True):
    global lasttimeslotid
    for x in courses:
        for y in range(0,lasttimeslotid+1): # Assign if slot is empty or course is not connected to courses in time slot
            if timeslots[y] == [] \
                or x.connections.intersection(timeslots[y])==set():
                timeslots[y].append(x)
                break
            elif y == lasttimeslotid: # Otherwise create new time slot
                lasttimeslotid += 1
                timeslots.update({lasttimeslotid:[x]})
    if display == True: # Print schedule
        for i in timeslots:
            print('Time slot ' + str(i))
            for j in timeslots[i]:
                print(j.name)
        return len(timeslots)

from random import *
from time import *
import re
from matplotlib import pyplot as plt

def simulate(listing,students,courseload):
    global enrollment
    global timeslots
    global currentstudentid
    global lasttimeslotid
    global courses
    enrollment = {}
    timeslots = {0: []}
    currentstudentid = 0
    lasttimeslotid = 0
    courses = set()
    starttime = time()
    for i in range(0,students): # Create random student
        studentcourses = []
        for j in range(0,courseload): # Each student has a number of courses specified by courseload
            a = randint(0,listing) # Course names are random numbers from 0 to the listing value
            while a in studentcourses: # Prevents assigning the same course twice to the same student
                a = randint(0, listing)
            studentcourses.append(randint(0,listing))
        addstudent(*studentcourses)
    slots = schedule(display=True) # Calculate the schedule
    endtime = time()
    print(endtime - starttime, 'seconds to calculate.')
    return endtime - starttime, slots

def montecarlo(variable, start, steps, stepsize, coursedefault = 1000, studentdefault = 1000, loaddefault = 4):
    xaxis = [a for a in range(start,start+steps*stepsize, stepsize)]
    times = []
    slots = []
    if variable == 'courses':
        for i in range(steps):
            t, s = simulate(start+i*stepsize, studentdefault, loaddefault)
            times.append(t)
            slots.append(s)
    elif variable == 'students':
        for i in range(steps):
            t, s = simulate(coursedefault, start+i*stepsize, loaddefault)
            times.append(t)
            slots.append(s)
    elif variable == 'courseload':
        for i in range(steps):
            t, s = simulate(coursedefault, studentdefault, start+i*stepsize)
            times.append(t)
            slots.append(s)
    fig, ax = plt.subplots(1,2)
    ax[0].plot(xaxis, times)
    ax[0].set_ylabel('Time (s)')
    ax[0].set_xlabel(variable)
    ax[1].plot(xaxis, slots)
    ax[1].set_ylabel('Time Slots')
    ax[1].set_xlabel(variable)
    plt.show()

if __name__ == '__main__':
    simulation = input('Random Simulation? (yes/no): ')
    if simulation == 'yes':
        single = input('Single Simulation? (yes/no): ')
        if single == 'yes':
            listing = int(input('Number of courses:'))
            students = int(input('Number of students:'))
            courseload = int(input('Student Courseload: '))
            simulate(listing,students,courseload)
        else:
            exiting = False
            print('Monte-Carlo Simulation')
            var = input('Variable (courses, students, courseload): ')
            coursedefault = 1000
            studentdefault = 1000
            loaddefault = 4
            if var == 'courses':
                studentdefault = int(input('Number of students: '))
                loaddefault = int(input('Student Courseload: '))
            elif var == 'students':
                coursedefault = int(input('Number of courses: '))
                loaddefault = int(input('Student Courseload: '))
            elif var == 'courseload':
                coursedefault = int(input('Number of courses: '))
                studentdefault = int(input('Number of students: '))
            else:
                print('Error: Invalid Entry')
                exiting=True
            if not exiting:
                start = int(input('Start Value: '))
                steps = int(input('Steps: '))
                stepsize = int(input('Step Size: '))
                montecarlo(var,start, steps,stepsize,coursedefault, studentdefault, loaddefault)
    else:
        print('Type a comma separated list for each new student, or "done" if finished.')
        userinput= None
        while userinput != 'done' and userinput != 'Done':
            userinput = input('Student Courses:')
            if userinput == 'done' or userinput == 'Done':
                break
            else:
                addstudent(*re.split(r' *[,.] *',userinput))
        schedule()
else:
    print('Add students using addstudent(*courses) and use schedule() to calculate the schedule')
    print('or run a simulation using simulate(number of courses, number of students, courseload)')