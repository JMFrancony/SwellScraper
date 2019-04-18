# !/usr/bin/env python
# -*- coding: utf-8 -*-

''' used for scheduling activities
'''

import datetime
import json
import itertools
import re

from CfgReader import CfgFileParser
from FileLogger import FileLogger

CONFIGFILE = 'WebPageCollector.cfg'

# ============================================================================================================
class Event():
    def __init__(self, Time, EvtInfo):
        self.Period = -1
        self.Ticks = 0
        self.TimeIn = Time
        self.Run = EvtInfo['run']
        if 'period' in EvtInfo:
            self.Period, self.Ticks = self.converTime(EvtInfo['period'])

    def converTime(self, duration):
        DayTime = [0, 0, 0, 0]
        Ticks = 0
        if 'd' in duration:
            DayTime = [int(duration[:-1]), 0, 0, 0]
            Ticks = int(duration[:-1]) * 86400
        elif 'h' in duration:
            hours = int(duration[:-1])
            days, hours = divmod(hours,24)
            DayTime = [days, hours, 0, 0]
            Ticks = days * 86400 + hours * 3600
        elif 'm' in duration:
            minutes = int(duration[:-1])
            if minutes < 1440:
                hours, minutes = divmod(minutes, 60)
                DayTime = [0, hours, minutes, 0]
                Ticks = hours * 3600 + minutes*60
        elif 's' in duration:
            seconds = int(duration[:-1])
            if seconds < 86400:
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                DayTime = [0, hours, minutes, seconds]
                Ticks = hours * 3600 + minutes*60 + seconds
        return DayTime, Ticks

# ============================================================================================================
class Agenda():
    def __init__(self):
        self.file_logger = FileLogger()
        cfg_parser = CfgFileParser()
        self.Config = cfg_parser.file_reader(CONFIGFILE)
        self.Agenda = []
        self.Pace = self.Config['Agenda']['pace']
        Date = self.Config['Agenda']['begin']
        self.Begin = datetime.datetime.strptime(Date.strip(), '%Y-%m-%d %H:%M:%S')
        Date = self.Config['Agenda']['end']
        self.End = datetime.datetime.strptime(Date.strip(), '%Y-%m-%d %H:%M:%S')
        self.CycledAgenda = itertools.cycle(self.Agenda)
        
    def nextEvent(self):
        return next(self.CycledAgenda)

    def CurrentEvent(self, Now):
        Event = self.nextEvent()
        Day = Now.weekday()
        Time = Now.time()
        Ticks = Time.hour * 3600 + Time.minute * 60 + Time.second
        DayIn = Event.TimeIn[0]
        TicksIn = Event.TimeIn[1] * 3600 + Event.TimeIn[2] * 60 + Event.TimeIn[3]
        DayOut = Event.TimeOut[0]
        TicksOut = Event.TimeOut[1] * 3600 + Event.TimeOut[2] * 60 + Event.TimeOut[3]
        while (TicksIn > Ticks or Ticks >= TicksOut) and (DayIn > Day or Day >= DayOut):
            Event = self.nextEvent()
            TicksIn = Event.TimeIn[1] * 3600 + Event.TimeIn[2] * 60 + Event.TimeIn[3]
            DayIn = Event.TimeIn[0]
            TicksOut = Event.TimeOut[1] * 3600 + Event.TimeOut[2] * 60 + Event.TimeOut[3]
            DayOut = Event.TimeOut[0]
        return Event

    def Delay(self, Now):
        Event = self.CurrentEvent(Now)
        if Event.Run:
            delay = Event.Ticks
        else:
            Day = Now.weekday()
            DeltaDay = Event.TimeOut[0] - Day
            if DeltaDay < 0:
                DeltaDay += 7
            EndDay = datetime.datetime(Now.year, Now.month, Now.day, Event.TimeOut[1], Event.TimeOut[2], Event.TimeOut[3])
            EndDay += datetime.timedelta(days=DeltaDay)
            Delta = EndDay-Now
            delay = Delta.seconds
            if Delta.days > 0:
                delay += Delta.days * 86400
        return delay

    def Prettify(self):
        print()
        print('\tbegin\t', self.Begin.date())
        print('\tend\t', self.End.date())
        Now = self.CurrentEvent(datetime.datetime.now())
        for Evt in self.Agenda:
            print('------')
            if Now == Evt :
                print('\tACTUAL')
            if type(Evt.Period) == int:
                print('\tperiod undefined')
            else:
                print('\tperiod', datetime.time(Evt.Period[1], Evt.Period[2], Evt.Period[3]).isoformat())
            print('\tTicks',Evt.Ticks)
            if Evt.TimeIn[0] > -1:
                print('\ttimeIn\t', str(Evt.TimeIn[0])+'\t', datetime.time(Evt.TimeIn[1], Evt.TimeIn[2], Evt.TimeIn[3]).isoformat())
            else:
                print('\ttimeIn\t', 'daily\t', datetime.time(Evt.TimeIn[1], Evt.TimeIn[2], Evt.TimeIn[3]).isoformat())
            if Evt.TimeOut[0] > -1:
                print('\ttimeOut\t', str(Evt.TimeOut[0])+'\t', datetime.time(Evt.TimeOut[1], Evt.TimeOut[2], Evt.TimeOut[3]).isoformat())
            else:
                print('\ttimeOut\t', 'daily\t', datetime.time(Evt.TimeOut[1], Evt.TimeOut[2], Evt.TimeOut[3]).isoformat())
            print('\trunning', Evt.Run)

# ============================================================================================================
class DailyAgenda(Agenda):
    def __init__(self):
        super(DailyAgenda, self).__init__()
        nb_evt = int(self.Config[self.Pace]['nbevt'])
        for Idx in range(nb_evt):
            evt_line = self.Config[self.Pace][str(Idx + 1)]
            evt_line = evt_line.strip()
            evt_line = re.sub(r'\s+', ' ', evt_line)
            Infos = evt_line.split('|')
            EvtInfo = json.loads(Infos[1])
            H, M, S = Infos[0].strip().split(':')
            TimeIn = [-1, int(H), int(M), int(S)]
            if [-1, 0, 0, 0] != TimeIn and Idx == 0:
                new_event = Event([-1, 0, 0, 0], {'run': False})
                self.Agenda.append(new_event)
            new_event = Event(TimeIn, EvtInfo)
            self.Agenda.append(new_event)
        self.Agenda.sort(key=lambda x: x.TimeIn[1])
        Prev = self.Agenda[0]
        for Evt in self.Agenda[1:]:
            Prev.TimeOut = Evt.TimeIn
            Prev = Evt
        self.Agenda[-1].TimeOut = [-1, 23, 59, 59]
        self.CycledAgenda = itertools.cycle(self.Agenda)
        self.file_logger.csv_log('AGENDA', 'A Daily agenda is set up')

# ============================================================================================================
class WeeklyAgenda(Agenda):
    def __init__(self):
        super(WeeklyAgenda, self).__init__()
        self.Pace = 'weekly'
        nb_evt = int(self.Config[self.Pace]['nbevt'])
        for Idx in range(nb_evt):
            evt_line = self.Config[self.Pace][str(Idx + 1)]
            evt_line = evt_line.strip()
            evt_line = re.sub(r'\s+', ' ', evt_line)
            Infos = evt_line.split('|')
            EvtInfo = json.loads(Infos[1])
            D, H, M, S = Infos[0].strip().split(':')
            DatIn = [int(D), int(H), int(M), int(S)]
            if [0, 0, 0, 0] != DatIn and Idx == 0:
                new_event = Event([0, 0, 0, 0], {'run': False})
                self.Agenda.append(new_event)
            new_event = Event(DatIn, EvtInfo)
            self.Agenda.append(new_event)
        self.Agenda.sort(key=lambda x: x.TimeIn[0])
        Prev = self.Agenda[0]
        for Evt in self.Agenda[1:]:
            Prev.TimeOut = Evt.TimeIn
            Prev = Evt
        self.Agenda[-1].TimeOut = [6, 23, 59, 59]
        self.CycledAgenda = itertools.cycle(self.Agenda)
        self.file_logger.csv_log('AGENDA', 'A Weekly agenda is set up')

# ============================================================================================================
if __name__ == '__main__':
    Test = DailyAgenda()
    Test.Prettify()