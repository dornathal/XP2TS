__author__ = 'dornathal'
'''
    XP2TS Project
    Released under GPLv3 Licence or later. (see below)

    Author: Enrico Gallesio
    XP2TS Plugin Ver. 0.5 Beta released on 24 Apr 2010

    --- Description:
    XP2TS is a project aimed to allow voice automatic connection while
    flying online with X-Plane on IVAO network using a TeamSpeak client.

    Please do not be surprised for poor quality/elegance/performance of this
    project, since this is my first coding experience and I'm an absolute
    beginner. Please let me know your feedback and ideas to make it better.

    Please read README file for more details and installation info.
    For support or contacts pls refer to: http://xp2ts.sourceforge.net/


    --- GPL LICENCE NOTICE ---
    This file is part of XP2TS project

    XP2TS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    XP2TS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with XP2TS.  If not, see <http://www.gnu.org/licenses/>.
    ---
'''
import sys
import os.path
import re
import time
import subprocess
from ConfigParser import ConfigParser

from XPLMDataAccess import *
from XPLMProcessing import *
from XPLMPlugin import *


class PythonInterface:
    __MaxWhazzupAge = 3000
    __Whazz_url = "http://api.ivao.aero/getdata/whazzup/whazzup.txt"
    __ResourcePath = "/home/dornathal/.steam/steam/SteamApps/common/X-Plane 10/Resources/plugins/X-IvAp Resources/"
    __ts_server = "%s.ts.ivao.aero"

    _loopcbs = 0

    def XPluginStart(self):
        self.Name = "XP2TS"
        self.Sig = "Dornathal.Python.XP2TS"
        self.Desc = "Lets IvAp Control Teamspeak Channel Switches"

        self.xDataRef = XPLMFindDataRef("sim/cockpit/radios/com1_freq_hz")
        self.xPlaneLat = XPLMFindDataRef("sim/flightmodel/position/latitude")
        self.xPlaneLon = XPLMFindDataRef("sim/flightmodel/position/longitude")

        self.floopcb = self.loopcallback

        self._oldfreq = XPLMGetDatai(self.xDataRef)

        self.get_config()

        if not self.getwhazzup():
            return 0

        # self._loopcbs += 1
        # print("RegisterFlightLoopCallback #%i" % (++self._loopcbs))
        XPLMRegisterFlightLoopCallback(self, self.floopcb, 1.0, 0)

        return 1

    def XPluginStop(self):
        # print("UnregisterFlightLoopCallback #%i" % self._loopcbs)
        # self._loopcbs -= 1
        XPLMUnregisterFlightLoopCallback(self, self.floopcb, 0)
        pass

    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, in_fromwho, in_message, in_param):
        pass

    def loopcallback(self, elapsedcall, elapsedloop, counterin, refconin):
        # print("ping")
        newfreq = XPLMGetDatai(self.xDataRef)

        if not self._oldfreq == newfreq:
            print("New Frequency tuned in")
            print("Change TS Channel to %f !" % newfreq)
            self._oldfreq = newfreq

            Lon = XPLMGetDataf(self.xPlaneLon)
            Lat = XPLMGetDataf(self.xPlaneLat)

            print("Position: %f N, %f W" % (Lat, Lon))

            nearest_atc = self.extract_atc(newfreq)
            print(nearest_atc)
            if nearest_atc == -1:
                self.freq_conn(self.parseConfig().get("TEAMSPEAK", "SERVER").strip(), "UNICOM")
            else:
                self.freq_conn(nearest_atc[1], nearest_atc[0])

        print("pong")
        return 1

    def get_config(self):  # takes TS useful variables and fixes paths to call TS instance
        config = self.parseConfig()

        ts_pwd = config.get('ACCOUNT', 'PASSWORD').strip()
        ts_nick = config.get('ACCOUNT', 'VID').strip()
        ts_path = config.get('TEAMSPEAK',
                             'TSCONTROL').strip()  # I preferred to split TS paths for more customizable commands later

        self._ts_control_cmd = ts_path + "client_sdk/tsControl"
        if not os.path.isfile(self._ts_control_cmd):
            print(self._ts_control_cmd + "does not exists")
        self._ts_prefix_complete = self._ts_control_cmd + " CONNECT TeamSpeak://"
        self._ts_disconnect_str = self._ts_control_cmd + " DISCONNECT"
        self._ts_login = "?nickname=\"%s\"?loginname=\"%s\"?password=\"%s\"?channel=" % ("%s", ts_nick, ts_pwd)

        print("Configuration loaded")
        pass

    def parseConfig(self):
        config = ConfigParser()
        config.read(self.__ResourcePath + "X-IvAp.conf")
        config.sections()
        return config

    def freq_conn(self, ts_server, freq_chan, retry=0):  # connects TS to any server/freq.channel given
        # returns 0 if ok, 1 if a retry is needed
        # TODO exception detection
        config = self.parseConfig()
        config.set("TEAMSPEAK", "SERVER", ts_server)
        config.write(open(self.__ResourcePath + "X-IvAp.conf", 'w'))
        # try:
        ts_conn_cmd = self._ts_control_cmd + " CONNECT TeamSpeak://" + self.__ts_server % ts_server + self._ts_login % config.get(
            "ACCOUNT", "CALLSIGN") + freq_chan
        consolecmd(ts_conn_cmd, self.__ResourcePath + "ts.log", "a")  # pass command to console and log output

        print(" ")
        print("Connecting to %s ...\n" % ts_server)  # + "with command: " + ts_conn_cmd   # debug
        time.sleep(3)
        # now let's check we're connected correctly

        ts_check_cmd = self._ts_control_cmd + " GET_USER_INFO"
        stout = self.performCommand(ts_check_cmd)
        #    print stout
        if re.search(freq_chan, stout):
            print("OK! Connection should be established")
        elif re.search("NOT CONNECTED", stout):
            print(stout + "Maybe we reconnected too fast. I'll wait 5 secs now before trying again...")
            time.sleep(5)
            return 1
        elif re.search("-1001", stout):
            print(
                "ERROR: Teamspeak appears to be quit. No changes done. Please tune unicom and run TS again!")  # TODO auto-select unicom?
            # sys.exit()
        else:
            print("WARNING: Must have failed somewhere, let's try again")
            retry += 1
            return retry
        # except:
        #    print "ERROR passing console command to TS"
        return 0

    def performCommand(self, command):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout = p.stdout.read()  # this gets standard output answer
        filetolog = open(self.__ResourcePath + "ts.log", "a")
        filetolog.write(time.ctime() + ": " + stout)  # this is to log even connections
        return stout

    def extract_atc(self, com1_freq):  # parses data got from internet and chooses the proper online ATC station
        # returns a tuple with all data to connect to the choosen online ATC
        # returns -1 if no (valid) online atc is found on the selected freq

        # definitions
        lat_xplane = self.xPlaneLat
        lon_xplane = self.xPlaneLon

        atc_on_freq = 0  # atc counter
        atc_list = []
        distances_list = []
        lower_distance = 0

        print(" ")
        # debug # print "Your geographic position in X-Plane is lat: "+str(lat_xplane)+" lon: "+str(lon_xplane)


        try:
            whazzup = open(self.__ResourcePath + "whazzup.txt", "r")
        except:
            print("ERROR while opening whazzup.txt file. Is this file there?")
        # print ":"+com1_freq+":" #debug
        print(
            "Now find listening ATC on the same freq (even .xx5 freqs are considered due to 25 KHz and 8.33Hz spacing):")
        print("find for frequence: %f" % com1_freq)
        for line in whazzup:  # FOR cycle begin to parse whazzup lines
            splitted = line.split(':')
            if len(splitted) != 49:
                continue

            icao_id = splitted[0]
            [role, freq, lat, lon] = splitted[3:7]
            ts_serv = splitted[14].lower()

            if not (role == "ATC" and abs(float(freq) * 100 - com1_freq) < 1):
                continue
            print([icao_id, role, freq, lat, lon, ts_serv])

            if not re.search("OBS", icao_id) and not re.search("No Voice", ts_serv):
                distance = calculate_distance(lat_xplane, lon_xplane, float(lat),
                                              float(lon))  # computing stations distance
                distances_list.append(distance)  # creating distances list to use out of loop

                tuple_atc = icao_id, lat, lon, ts_serv, distance  # create a new tuple with these atc data

                # Creating a list to display all valid online ATCs found on the selected freq.
                # and append to atc list for further use

                atc_list.append(tuple_atc)
                print(str(atc_on_freq) + ": \t" + icao_id + " \t" + freq + " \t" + str(lat) + " \t" + str(
                    lon) + " \t\t" + ts_serv + "\t - Distance (nm): \t" + str(distance))
                atc_on_freq = atc_on_freq + 1  # counting one more valid station with com1 freq
                # print atc_on_freq
                # end for cyce

        # Now deciding what online ATC is the nearest to return
        print(" ")
        if atc_on_freq != 0:
            lower_distance = min(distances_list)  # gets the lower distances atc in the list
            nearest_station = distances_list.index(lower_distance)  # and tell us which nearest atc index number is
            print("The nearest valid station is: " + atc_list[nearest_station][0] + ", (" + str(
                atc_list[nearest_station][4]) + " nm)")
            nearest_atc_tuple = atc_list[nearest_station][0], atc_list[nearest_station][
                3]  # preparing ATC data to return
            return nearest_atc_tuple
        else:
            print(
                "WARNING: No valid ATC found in whazzup")  # TODO reload whzzup or manual connect?... ---------------- !
            return -1  # this means no atc found at all

    pass

    def getwhazzup(self):
        """ Connects to the internet and downloads the data file whazzup.txt from IVAO server only if needed
         which means not more than once every 5 mins.
        TODO Add an option to force immediate download ----!!!!
        TODO we should use another data file provided from IVAO and use a geo-loc ICAO codes list ----!!!!"""

        filename = self.__ResourcePath + "whazzup.txt"
        if os.path.exists(filename):
            try:
                if time.time() - os.path.getmtime(filename) < self.__MaxWhazzupAge:  # 3000 is for debug 300 is ok
                    print("Old network data are too young do die. I'll keep the previous by now...")
                    return 1
                    # print age_whazzup
                else:
                    print("Yes, updated network data are needed. Downloading now...")
                    os.remove(filename)
            except:
                print("ERROR retrieving whazzup file from internet. Will try with older one if present.")

        print("Downloading network data")
        os.system("wget \"%s\" -O \"%s\"" % (self.__Whazz_url, filename))
        if not os.path.exists(filename):
            print("ERROR while downloading network data (whazzup.txt)")
            print("Please check your network")
            return 0
        return 1


def consolecmd(cmd, logfile, iomode):  # excute custom commands and logs output for debug if needed
    try:  # i/o modes: r,w,a,r+, default=r
        # subprocess.Popen(cmd, shell=True, stdout=logfile, stderr=logfile)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stout = p.stdout.read()
        filetolog = open(logfile, iomode)
        filetolog.write(time.ctime() + ": " + stout)
        return stout
    except:
        print("ERROR while executing command: " + cmd)
        return 0

def calculate_distance(lat1, lon1, lat2, lon2):  # self explicative returns geographic distances
    # maths stuff
    deg_to_rad = math.pi / 180.0
    phi1 = (90.0 - lat1) * deg_to_rad
    phi2 = (90.0 - lat2) * deg_to_rad
    theta1 = lon1 * deg_to_rad
    theta2 = lon2 * deg_to_rad
    cos = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) + math.cos(phi1) * math.cos(phi2))
    arc = math.acos(cos)
    distance = arc * 3960  # nautical miles
    # distance = arc*6373 # if kilometers needed
    return distance
