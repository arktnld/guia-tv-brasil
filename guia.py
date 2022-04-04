#!/usr/bin/python

# needs install natsort package
from natsort import natsorted
import requests, sys, getopt
from bs4 import BeautifulSoup
from time import localtime, strftime
from colorama import Fore, Style

tv = [ 'Globo', 'SBT', 'Record', 'Band', 'RedeTV', 'HBO-Signature', 'Syfy', 'Universal-Channel', 'Warner-Channel', 'AXN', 'TNT-Series' ]
doc = [ 'AE', 'Animal-Planet', 'Arte-1', 'Discovery-Channel', 'Discovery-Civilization', 'Discovery-Home-and-Health', 'Discovery-Kids', 'Discovery-Science', 'Discovery-Theater', 'Discovery-Turbo', 'Discovery-World', 'Investigacao-Discovery-ID', 'NatGeo-Wild-HD', 'National-Geographic', 'The-History-Channel', 'TLC', 'Food-Network', 'truTV' ]
sport = [ 'Band-Sports', 'Combate', 'ESPN-Brasil', 'SporTV', 'SporTV2', 'SporTV3' ]
movie = [ 'AMC', 'Cinemax', 'FX',  'Megapix', 'Paramount', 'Sony', 'Space',  'Lifetime', 'HBO', 'HBO-Plus',  'HBO2', 'HBO-Family', 'Max-Prime', 'Max-e', 'Max-HD', 'Telecine-Action', 'Telecine-Cult', 'Telecine-Fun', 'Telecine-Pipoca', 'Telecine-Premium', 'Telecine-Touch', 'Fox', 'Fox-Life', 'TNT' ]
# favorite = [ 'Warner-Channel', 'Tooncast' ]

time = strftime("%H:%M", localtime())
# time = "03:00"

class Program(): # Class with hour and name of a tv program
    def __init__(self, hour, name):
        self.hour = hour
        self.name = name

    def __str__(self):
        return  self.hour + " " + self.name

class Channel(): # Class with channel name and all programs schedule
    def __init__(self, name):
        self.name = name
        self.programs = []

    def __str__(self):
        return self.programs

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i < len(self.programs):
            h = self.programs[self.i].hour
            p = self.programs[self.i].name
            self.i = self.i + 1
            return h, p
        else:
            raise StopIteration

    def __add__(self, obj):
        return self.programs + obj.programs

    def __len__(self) -> int:
        return len(self.programs)

    def update(self, obj):
        for hour, name in obj:
            program = Program(hour, name)
            self.programs.append(program)

    def setProgram(self, h, p):
        program = Program(h, p)
        self.programs.append(program)

    def getProgram(self, n):
        return self.programs[n]

def usage():
    print("Usage:")
    print("\tguia [options]")
    print("\tguia -n [options]")
    print("\tguia -e [channel]")
    print()
    print("Output Options:")
    print("\t-n, --watch-now          Show now and next programs to watch")
    print("\t-e, --specific CHANNEL   Show programs of specific channel")
    print()
    print("Search Lists:")
    print("\t-t, --tv-show            Tv's and series channel list")
    print("\t-d, --doc                Documentary channel list")
    print("\t-m, --movie              Movie channel list")
    print("\t-s, --sport              Sport channel list")

def getChannelPrograms(name): # Create object channel with name and list of programs
    url = 'https://www.tvmap.com.br/' + name
    r = requests.get(url)
    html = BeautifulSoup(r.text, 'html.parser')

    channel = Channel(name)
    for l1, l2 in zip(html.findAll("div", class_="timelineheader"), html.findAll("div", class_="hourbox")):
        program = l1.b.string
        hours = l2.span.string.replace(' h', '')
        channel.setProgram(hours, program)

    return channel

def getPMPrograms(channel): # get post noon programs
    pm = Channel(channel.name)
    for hour, name in channel:
        if hour > "11:59" and hour <= "24:59":
            pm.setProgram(hour, name)
    return pm

def getAMPrograms(channel): # get after noon programs
    am = Channel(channel.name)
    for hour, name in sorted(channel):
        if hour >= "00:00" and hour < "12:00":
            am.setProgram(hour, name)

    return am

def getCurrentProgramPosition(pm, am): # get position of current program by time
    pos = ''
    if time > "11:59" and time < "24:00": # get current position program if pm
        first = am.programs[0]
        for n, program in enumerate(pm):
            if time <= first.hour: # check if now time is less then first pm program
                pos = len(pm) + len(am) - 2 # set current position to last am program
                break
            elif time <= program[0]: # check if now time is less then first pm program
                if n == 0: # if n less then zero get last am position
                    pos = len(pm) + len(am) - 2
                    break
                else: # set current position if program time is more than now time
                    pos = n - 2
                    break
        if pos == '': # if any programs match time, get last pm program position
            pos = len(pm) - 2
    else:
        first = am.programs[0]
        for n, program in enumerate(am): # get current position program if am
            if time <= first.hour: # check if now time is less then first am program
                pos = 0 # set current position to last pm program
                break
            elif time <= program[0]: # check if now time is less then first pm program
                pos = n # set current position if program time is more than now time
                break
        if pos == '': # if any programs match time, get last am program position
            pos = len(am)
        pos = int(pos + len(pm) - 2) # add pm lenght to am position

    return pos

def getProgramsOrder(channel, pos): # set current program to fisrt position in channel list
    afterChannelPrograms = Channel(channel.name)
    beforeChannelPrograms = Channel(channel.name)
    for n, program in enumerate(channel):
        hour = program[0]
        name = program[1]
        if int(pos) < n:
            afterChannelPrograms.setProgram(hour, name)
        else:
            beforeChannelPrograms.setProgram(hour, name)
    afterChannelPrograms.update(beforeChannelPrograms)

    return afterChannelPrograms

def getListChannels(channels): # get list of channels
    listChannelsOrderedPrograms = []
    for canal in channels:
        channel = getChannelPrograms(canal)
        channelPM = getPMPrograms(channel)
        channelAM = getAMPrograms(channel)
        pos = getCurrentProgramPosition(channelPM, channelAM)
        channelPM.update(channelAM)
        orderedChannel = getProgramsOrder(channelPM, pos)

        listChannelsOrderedPrograms.append(orderedChannel)
    return listChannelsOrderedPrograms

def getSpecificChannel(specific): # get list of program to a specific channel
        listChannels= getListChannels(specific)
        for channel in listChannels:
            print(Fore.GREEN + channel.name + Fore.RESET)
            for hour, name in channel:
                print(name + Fore.BLUE + " " + hour + Fore.RESET)
        return

def getListPrograms(channels): # get list of programs by position
        listChannels= getListChannels(channels)
        def getProgramByPos(pos):
            results = []
            for channel in listChannels:
                channel.name = checkChannelName(channel.name)
                h = channel.programs[pos].hour
                p = channel.programs[pos].name
                results.append(h + " " + p + " " + channel.name)

            orderAfter00 = []
            checkAfter00 = False
            for line in natsorted(results):
                time, *program, channel = str(line).split()
                if time >= "00:00" and time < "00:59" or checkAfter00:
                    # If hour is "00:00" put all time before the time less than "00:00"
                    checkAfter00 = False if time > "20:00" else True
                    if checkAfter00: orderAfter00.append(line)
                else:
                    print(Fore.BLUE + str(time) + Fore.RESET + " " + " ".join(program) + " " + Fore.GREEN  + channel + Fore.RESET)

            for line in natsorted(orderAfter00):
                time, *program, channel = str(line).split()
                print(Fore.BLUE + str(time) + Fore.RESET + " " + " ".join(program) + " " + Fore.GREEN  + channel + Fore.RESET)

        getProgramByPos(0)
        print(Fore.YELLOW + " ----------- Watch Now at " + time + " ------------ " + Fore.RESET)
        getProgramByPos(1)

def getSummaryChannels(channels): # get current and next channels programs list
        listChannels = getListChannels(channels)
        for channel in listChannels:
            channel.name = checkChannelName(channel.name)
            program0 = channel.programs[0]
            program1 = channel.programs[1]
            print(Fore.GREEN + channel.name + Fore.RESET)
            print(Style.BRIGHT + program0.name + " " + program0.hour + Style.NORMAL)
            print(program1.name + " " + program1.hour)
            print()

def getGuide(channels, now, specific):
    print("Fetching channels, please wait...")
    if specific:
        getSpecificChannel(specific)
    elif now:
        getListPrograms(channels)
    else:
        getSummaryChannels(channels)

#
# Actual script
#

def checkChannelName(name):
    if name == "Max-Prime":
        name = "HBO-Xtreme"
    elif name == "Max-e":
        name = "HBO-Mundi"
    elif name == "Max-HD":
        name = "HBO-Pop"
    elif name == "Fox":
        name = "Star"
    elif name == "Fox-Life":
        name = "Star-Life"

    return name

try:
    opts, args = getopt.getopt(sys.argv[1:], 'entdms', ['specific', 'watch-now', 'tv-show', 'doc', 'movie', 'serie', 'sport' ])
except getopt.GetoptError:
    print("ERROR: Option not found\n")
    usage()
    sys.exit(2)

listOfChannels = list()
now, specific = False, False
for opt, arg in opts:
    if opt in ('-t', '--tv-show'):
        listOfChannels = listOfChannels + tv
    elif opt in ('-d', '--doc'):
        listOfChannels = listOfChannels + doc
    elif opt in ('-m', '--movie'):
        listOfChannels = listOfChannels + movie
    elif opt in ('-s', '--sport'):
        listOfChannels = listOfChannels + sport
    elif opt in ('-n', '--watch-now'):
        now = True
    elif opt in ('-e', '--specific'):
        # if args:
        specific = args
        # else:
        #     print("ERROR: Option -e/--specific needs [channel] name arg\n")
        #     usage()
        #     sys.exit(2)
    # elif opt in ('-f', '--fav'):
        # listOfChannels = listOfChannels + favorite

if not listOfChannels and not specific:
    print("ERROR: You need to specify a channel category to search\n")
    usage()
    sys.exit(2)

getGuide(listOfChannels, now, specific)
