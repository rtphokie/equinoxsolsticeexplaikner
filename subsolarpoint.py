import unittest
import ephem
import math
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.basemap import Basemap
import cv2
import numpy as np
import configparser
import shutil
import sys
import os, time
import warnings
warnings.filterwarnings("ignore", module="matplotlib")


import unittest
from os.path import isfile, join
from tqdm import tqdm
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
cmap = plt.cm.get_cmap('Greys')

class Config():
    def __init__(self, future_events=False):
        self.type = type
        self.datestring = "%Y-%m-%d %H:%M"
        self.filename = "astroreport.ini"
        self.future_events = future_events
        try:
            self.read_opts = ConfigParser.ConfigParser()
        except:
            self.read_opts = configparser.ConfigParser()
        self.config = self.read_config()

    def read_config(self, parse=True):
        matrix = dict()
        self.read_opts.read(self.filename)
        for section in self.read_opts.sections():
            matrix[section] = dict()
            for p, v in self.read_opts. items(section):
                matrix[section][p] = v
        return matrix

def read_config():
    thing = Config()
    config = thing.read_config()
    return config

def plotonmap(obs, sun_lat, sun_lon,
              city_lat, city_lon, city,
              projection='ortho',
              redraw=False,
              bluemarble=False):
    if os.path.exists("movies/%s.mp4" % city):
        return

    filename ="images/%s/plot_%s_00.png" % (city, obs.date.datetime().strftime("%Y%m%d"))

    if not redraw and os.path.exists(filename):
        return
    else:
        plt.style.use('dark_background')
        plt.figure(figsize=(19.2, 10.80))
        m = Basemap(projection=projection, resolution='l', lat_0=20, lon_0=city_lon)
        m.bluemarble()

        # draw terminator
        _ = m.nightshade(obs.date.datetime(), delta=0.7, alpha=0.5,)

        # draw tropics and equator
        draw_parallel(m, 23.5, city_lon, color='ivory', label="Tropic of\nCancer")
        draw_parallel(m, -23.5, city_lon, color='ivory', label="Tropic of\nCapricorn")
        draw_parallel(m, 0, city_lon, color='ivory', label='Equator')

        # mark city
        citydot(m, city_lat, city_lon, 'white')

        # mark sun position
        sundot(m, sun_lat, sun_lon, 'y', label='subsolar')
        draw_parallel(m, sun_lat, city_lon, color='yellow')

        datestring = obs.date.datetime().strftime("%Y-%m-%d")
        frames = 1
        if '6-21' in datestring or '12-21' in datestring or '6-.8020' in datestring:
            datestring += " Solstice"
            frames=20
        if '3-19' in datestring or '9-23' in datestring:
            datestring += " Equinox"
            frames = 40
        plt.annotate(datestring, xy=(10, 10), fontsize=20, textcoords='data', color='w')
        plt.savefig(filename, transparent=True)
        plt.close()
        from PIL import Image
        fg = Image.open(filename, 'r')
        bg = Image.open('starfield.png', 'r')
        text_img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        text_img.paste(bg, (0, 0))
        text_img.paste(fg, (0, 0), mask=fg)
        text_img.save(filename, format="png")

        for x in range(1,frames):
            filename2 = "images/%s/plot_%s_%02d.png" % (city,
                                                        obs.date.datetime().strftime("%Y%m%d"),
                                                        x
                                                        )
            shutil.copyfile(filename, filename2 )




def citydot(m, lat, lon, color, label="", labellon=-98, markersize=16):
    xpt, ypt = m(lon, lat)
    m.plot([xpt], [ypt], "*", color=color, markersize=markersize, alpha=0.7)

def sundot(m, lat, lon, color, label="", labellon=-98, markersize=24):
    xpt, ypt = m(lon-130, lat)
    m.plot([xpt], [ypt], "o", color=color, markersize=markersize, alpha=0.7)

def draw_parallel(m, lat, lon, color='yellow', label=None, fontsize=18, labellon=-160):
    if lat >= 0:
        lonextension = 85
    else:
        lonextension = 80
    lons = np.linspace(round(lon)-lonextension, round(lon)+lonextension)
    lats = np.linspace(lat, lat)
    x, y = m(lons, lats)
    m.plot(x, y, linewidth=6, color=color, linestyle='-', alpha=0.3)
    if label is not None:
        xrpt, ypt = m(round(lon)-lonextension, lat+2)
        plt.annotate(label, xy=(xrpt, ypt), textcoords='data', ha = 'center',
                     fontsize=fontsize,
                     weight='bold', color=color, family="Arial")

def makemovie(city):
    pathIn = './images/%s/' % city
    pathOut = 'movies/%s.mp4' % city
    smallPathOut = 'movies_small/%s.mp4' % city
    size=None
    fps = 25.0
    frame_array = []
    files = [f for f in os.listdir(pathIn) if isfile(join(pathIn, f))]
    # for sorting the file names properly
    files.sort(key=lambda x: x[5:-4])
    files.sort()
    frame_array = []
    files = [f for f in os.listdir(pathIn) if isfile(join(pathIn, f))]
    # for sorting the file names properly
    files.sort(key=lambda x: x[5:-4])
    for i in range(len(files)):
        filename = pathIn + files[i]
        # reading each files
        img = cv2.imread(filename)
        print (filename)
        try:
            height, width, layers = img.shape
            size = (width, height)
        except:
            print(f"error in {filename}")
            return
        frame_array.append(img)
    if len(frame_array) <= 1:
        print (f"no frames found for {city}")
    else:
        out = cv2.VideoWriter(pathOut, fourcc, fps, size)
        for i in range(len(frame_array)):
            # writing to a image array
            out.write(frame_array[i])
        out.release()
        import subprocess
        subprocess.call(['ffmpeg', '-y', '-i', pathOut, '-crf', '35', smallPathOut])
        subprocess.call(['open', smallPathOut])

def subsolarpoint(obs, body=None):
    if body is None:
        body = ephem.Sun(obs)
    body.compute(obs.date)

    body_lon = math.degrees(body.ra-obs.sidereal_time() )
    if body_lon< -180.0:
      body_lon = 360.0 + body_lon
    elif body_lon > 180.0 :
      body_lon = body_lon - 360.0
    body_lat = math.degrees(body.dec)
    return body_lon, body_lat

def runitall(city_lat, city_lon, city, flush=False):
    os.environ['export OBJC_DISABLE_INITIALIZE_FORK_SAFETY']='YES'
    import shutil
    obs = ephem.Observer()
    obs.lat = str(city_lat)
    obs.lon = str(city_lon)
    # obs.desc = city
    obs.date = ephem.date('2019/06/20 12:00')
    if flush:
        shutil.rmtree('images/%s' % city)
        os.makedirs('images/%s' % city )
    if not os.path.exists('images/%s' % city):
        os.makedirs('images/%s' % city)
    child_pids = set()
    concurency = 12
    # for x in tqdm(range(0, 365), unit='day'):
    for x in tqdm(range(0,366), unit='day'):
        obs.date = obs.next_rising(ephem.Sun())
        obs.date += ephem.minute*15
        sun_lon, sun_lat = subsolarpoint(obs)
        while len(child_pids) >= concurency:
            for pid in child_pids:
                try:
                    os.waitpid(pid, 0)
                except:
                    pass
            child_pids = set()  # all subprocesses are done
        child_pid = os.fork()
        if child_pid == 0:
            #child
            plotonmap(obs, sun_lat, sun_lon, city_lat, city_lon, city)
            os._exit(0)
        else:
            child_pids.add(child_pid)
    makemovie(city)

class MyTestCase(unittest.TestCase):
    def test_images(self):
        foo = read_config()
        for k, v in foo.items():
            runitall(float(v['lat']), float(v['lon']), v['city'])

    def test_map(self):
        # 35.7796
        obs = ephem.Observer()
        obs.lat = "35.7796"
        obs.lon = "-78.6382"
        obs.date = ephem.date('2019/12/21 0:00')
        obs.date = obs.next_rising(ephem.Sun())
        sun_lon, sun_lat = subsolarpoint(obs)
        a = plotonmap(obs, sun_lat, sun_lon, 35.7796, -78.6382, 'TEST', redraw=True)

    def test_movie(self):
        makemovie()

    def test_subp(self):
        from threading import Thread

    def test_c(self):
        foo = read_config()
        for k, v in foo.items():
            print (k, v['city'], float(v['lat']), float(v['lon']))

if __name__ == '__main__':
    foo = read_config()
    for k, v in tqdm(sorted(foo.items()), unit='city'):
        print (v['city'])
        runitall(float(v['lat']), float(v['lon']), v['city'])

    #https://www.ps2pdf.com/compress-mp4
