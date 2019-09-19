import unittest
import ephem
import math
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import cv2
import numpy as np
import os
from os.path import isfile, join
from tqdm import tqdm
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
cmap = plt.cm.get_cmap('Greys')


def dd_dms(lat,lon):
   latstr = "%6.1f" % abs(round(lat, 1))
   if lat < 0:
       latstr += "ºS"
   else:
       latstr += "ºN"
   lonstr = "%6.1f" % round(lat, 1)
   if lon < 0:
       lonstr += "W"
   else:
       lonstr += "E"
   return (f"{latstr}")
   return (f"{latstr} {lonstr}")

def plotonmap(obs, sun_lat, sun_lon,
              city_lat, city_lon, city,
              projection='ortho',
              redraw=True,
              bluemarble=False):
    filename ="images/%s/plot_%s.png" % (city, obs.date.datetime().strftime("%Y%m%d"))

    if not redraw and os.path.exists(filename):
        pass
    else:
        plt.style.use('dark_background')
        plt.figure(figsize=(16, 9))
        img = plt.imread("milkyway.jpg")
        plt.imshow(img, zorder=0, extent=[-100, 8.0, 1.0, 7.0])

        print (f"sunlon {sun_lon} sunlat {sun_lat}")
        m = Basemap(projection=projection, resolution='c', lat_0=20, lon_0=city_lon)
        if bluemarble:
            m.bluemarble(scale=0.5);
        else:
            water=cmap(0.8)
            land=cmap(0.6)
            m.fillcontinents(color=land, lake_color=water)
            m.drawmapboundary(fill_color=water)
            # m.drawcoastlines(color=water)

        citydot(m, city_lat, city_lon, 'white')
        sundot(m, sun_lat, sun_lon, 'y', label='subsolar')
        draw_parallel(m, sun_lat, city_lon, color='yellow')

        # draw terminator
        _ = m.nightshade(obs.date.datetime(), delta=0.6, alpha=0.6,)
        draw_parallel(m, 23.5, city_lon, color='ivory', label="Tropic of\nCancer")
        draw_parallel(m, -23.5, city_lon, color='ivory', label="Tropic of\nCapricorn")
        draw_parallel(m, 0, city_lon, color='ivory', label='Equator')

        datestring = obs.date.datetime().strftime("%Y-%m-%d")
        plt.annotate(datestring, xy=(10, 10), fontsize=20, textcoords='data', color='w')

        plt.savefig(filename)
        plt.close()


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
    pathOut = '%s.mp4' % city
    size=None
    fps = 10.0
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
        height, width, layers = img.shape
        size = (width, height)

        # inserting the frames into an image array
        frame_array.append(img)
    if size is None:
        print ("no frames found")
    else:
        out = cv2.VideoWriter(pathOut, fourcc, fps, size)
        for i in range(len(frame_array)):
            # writing to a image array
            out.write(frame_array[i])
        out.release()
        import subprocess
        subprocess.call(['open', pathOut])

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


def runitall(city_lat, city_lon, city):
    import shutil
    obs = ephem.Observer()
    obs.lat = str(city_lat)
    obs.lon = str(city_lon)
    # obs.desc = city
    obs.date = ephem.date('2019/06/20 12:00')
    try:
        shutil.rmtree('images/%s' % city)
    except:
        os.makedirs('images/%s' % city )
    if not os.path.exists('images/%s' % city):
        os.makedirs('images/%s' % city)
    for x in tqdm(range(0, 30)):
        obs.date = obs.next_rising(ephem.Sun())
        sun_lon, sun_lat = subsolarpoint(obs)
        print (obs.lat, obs.lon)
        plotonmap(obs, sun_lat, sun_lon, city_lat, city_lon, city,
                  projection='ortho', bluemarble=True)
    makemovie(city)

class MyTestCase(unittest.TestCase):
    def test_images(self):
        lat = 35.7796
        lon = -78.6382
        city = "Raleigh"
        runitall(lat, lon, city)

    def test_map(self):
        # 35.7796
        obs = ephem.Observer()
        obs.lat = "35.7796"
        obs.lon = "-78.6382"
        obs.date = ephem.date('2019/06/21 12:00')
        obs.date = obs.next_rising(ephem.Sun())
        print (obs.date)
        sun_lon, sun_lat = subsolarpoint(obs)
        a = plotonmap(obs, sun_lat, sun_lon, 35.7796, -78.6382, 'TEST', projection='ortho', bluemarble=True)




    def test_movie(self):
        makemovie()



if __name__ == '__main__':
    unittest.main()
