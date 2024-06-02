from datetime import timedelta
import logging
import re

import click
from colorama import Fore
import dateutil.parser
#import gpxpy.geo
import gpxpy.gpx
import numpy as np
import pandas as pd
import simplekml
import gpxpy.gpx as mod_gpx

def read_gpx(gpx_filepath):
   with open(gpx_filepath, "r") as gpx_file:
       gpx = gpxpy.parse(gpx_file)

   df_segments = []
   for track in gpx.tracks:
      for segment in track.segments:
         lats, lons, times = [], [], []
         for pt in segment.points:
            # TODO get elevation ?
            lats.append(pt.latitude)
            lons.append(pt.longitude)
            times.append(pt.time)
         d = {"lat": lats, "lon": lons, "time": times}
         df = pd.DataFrame(d)
         df = df.set_index("time")
         df_segments.append(df)

   return df_segments

@click.option(
    "--debug",
    "is_debug",
    is_flag=True,
    help=("Flag to activate debug mode"),
    required=False,
)

@click.argument(
    "gpx_out_filepath",
    metavar="GPX_OUT_FILE",
    type=click.Path(resolve_path=True, dir_okay=False),
)

@click.argument(
    "gpx_filepath",
    metavar="GPX_IN_FILE",
    type=click.Path(exists=True, resolve_path=True, dir_okay=False),
)

@click.command()
def gpxaddtime(is_debug, gpx_filepath, gpx_out_filepath):
   print('--', gpx_filepath)
   print('--', gpx_out_filepath)
   gpx = read_gpx(gpx_filepath)
   #print ("gpx\n",gpx)
   #print ('lenght',len(gpx[0]))
   for sgs in gpx:
      #print (sgs)
      sgs['timestamp'] = sgs.index
      loc0 = sgs.iloc[0]
      #print ("-------Loc0-------",loc0.name)
      dist = 0
      ht0 = str(type(loc0.name)).find('NaT') != -1
      index =[]
      start_end = [0,0]
      if ht0 : index.append(start_end)
      i = 0
      for i in range(1,len(sgs)):
         ht1 = ( str(type(sgs.iloc[i].name)).find('NaT') != -1)
         if ht1 != ht0: 
            if ht1 : index.append([i,i])
            else : index[-1][1] = i
            ht0 = ht1
      print (index)
      for se in index :
         if se[0] > 0 and se[1] < len(sgs) :
            gps_before = sgs.iloc[se[0] - 1]
            distance = 0
            for i in range(se[0]-1,se[1]+1):
               gps_after = sgs.iloc[i]
               distance += gpxpy.geo.distance(gps_before["lat"],gps_before["lon"],None,gps_after["lat"],gps_after["lon"],None)
               #print ('---', distance)
               gps_before = gps_after
            dist = 0
            gps_before = sgs.iloc[se[0] - 1]
            gps = gps_before
            #print ('----gps---- ',gps,'-----\n\n')
            gps_after = sgs.iloc[se[1]]
            dtb = gps_before.name.tz_convert("utc")
            dt = gps_after.name.tz_convert("utc") - dtb
            #print ( '---dt---',dt )
            #sgs['timestamp'] = sgs['timestamp'].interpolate(method='linear')
            #print(sgs.dtypes)
            for i in range(se[0],se[1]):
               gps_after = sgs.iloc[i]
               dist += gpxpy.geo.distance(gps_before["lat"],gps_before["lon"],None,gps_after["lat"],gps_after["lon"],None)
               gps_before = gps_after
               #print( dist, distance, dist/distance)
               time = dtb + dt*dist/distance
               gps_after['timestamp'] = time
               sgs.iloc[i] = gps_after
               #print ( '-----------', (sgs.iloc[i]["timestamp"]), (gps_after)) 
            #print (sgs)
            #print (print('Created GPX:', sgs.to_xml()))


   gpx_data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
   gpx_data +='<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="TEASI ONE4 ver. 4.4.1.0 - http://www.gpstuner.com">'
   gpx_data +=  '<trk>\n' 
   for sgs in gpx:
      gpx_data +='<trkseg>\n'
      for i in range(0,len(sgs)):
         pt =  sgs.iloc[i]
         gpx_data += '<trkpt lat= "'+str(pt["lat"])+'" lon= "'+str(pt["lon"])+'">\n'
         gpx_data += '<time>'+str(pt["timestamp"])+'</time>\n'
         gpx_data += '</trkpt>\n'
      gpx_data +='</trkseg>\n'
   gpx_data +=  '</trk>\n' 
   gpx_data +=  '</gpx>\n' 
   with open(gpx_out_filepath, "w" ) as gpx_out:
      gpx_out.write(gpx_data)

if __name__ == "__main__":
   gpxaddtime()
