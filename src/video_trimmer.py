#!/usr/bin/python3

from pytube import YouTube
from pytube.helpers import safe_filename
# misc
import os
import sys
import re
# image operation
import cv2
import numpy as np

def findTextFrame(text, vid, start=None, end=None, findFirst=True):
    if start == None:
        start = 0
    if end == None:
        end = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

    if findFirst:
        for i in range(start, end):
            pass
    else:
        for i in range(end, start, -1):
            pass

def getKeyframes(inputFile, outputFile="tmp/keyframes.txt"):
    os.system("ffprobe -loglevel error -select_streams v:0 -show_entries packet=pts_time,flags -of csv=print_section=0 '{}' | awk -F',' '/K/ {print $1}' > {}".format(inputFile, outputFile))
    kf = []
    with open(file, "r") as fp:
        text = fp.readlines()
        kf  = list(map(float, text))
    return kf

def findEquivFrame(vid, refFr, start=None, end=None, findFirst=True, atol=10, matchMin=0.5, coords=(0,-1,0,716), incr=1):
    if start == None:
        start = 0
    if end == None:
        end = int(vid.get(cv2.CAP_PROP_FRAME_COUNT)) - 1

    if findFirst:
        iterRange = range(start, end, incr)
    else:
        iterRange = range(end, start, incr*(-1))

    for i in iterRange:
        vid.set(1, i)
        curr = vid.read()[1][coords[0]:coords[1], coords[2]:coords[3]]
        simArr = np.isclose(refFr, curr, atol=atol);
        if matchMin < np.count_nonzero(simArr)/simArr.size:
            return i
    return -1

def generateReferenceFrame(vidInput, coords=(0,-1,0,-1), outputFile=None, timestamp=None, frame=None):
    if timestamp is None and frame is None:
        raise ValueError("1 of timestamp and frame must be specified.")
    if timestamp is not None and frame is not None:
        raise ValueError("timestamp and frame cannot both be specified.")

    if (isinstance(vidInput, str)):
        vid = cv2.VideoCapture(vidInput)
    else:
        vid = vidInput
    fps = vid.get(cv2.CAP_PROP_FPS)
    if timestamp:
        frame = float(timestamp)
        frame *= fps
        frame = int(frame)
    if frame > vid.get(cv2.CAP_PROP_FRAME_COUNT):
        raise IndexError("Frame number {} not in the file".format(frame))
    vid.set(cv2.CAP_PROP_POS_FRAMES, frame - 1)
    result, frameImg = vid.read()
    if result:
        if outputFile:
            cv2.imwrite(outputFile, frameImg[coords[0]:coords[1], coords[2]:coords[3]])
        else:
            return frameImg


if __name__ == "__main__":
    if not len(sys.argv)>=2:
        print("Missing argument")
        sys.exit(1)

    fName = sys.argv[1]

    vid = cv2.VideoCapture(fName)
    fRate = vid.get(cv2.CAP_PROP_FPS)
    print("The framerate is {}".format(fRate))
    if ("wave" in fName): #TODO this arguments
        recapPath = "assets/waves_intro_screen.jpg"
        recapCoords=(0,-1,0,65)
        recapRangeStart = 0
        recapRangeEnd = 150
        recapDefault = 64
        nextEpPath = "assets/waves_outro_screen.jpg"
        nextEpCoords=(0,-1,530,-1)
        nextEpRangeStart = 450
        nextEpOffset = 0
        introEnd = 0 #to trim fixed length intros
        introPath = "file '../assets/waves_intro.mp4'\n"
        outroPath = "file '../assets/waves_outro.mp4'\n"
        outputName = "Waves Edited.mp4" #"Waves E{}.mp4".format(re.findall(r'EPISODE (\d+)', fName.split("/")[-1])[0])
    else: #support multiple shows in future, likely to be replaced with args
        pass

    #Find recap
    recapRef = cv2.imread(recapPath)
    recapEnd_approx = findEquivFrame(vid, recapRef, recapRangeStart, recapRangeEnd, False, incr=int(fRate), coords=recapCoords) #first do a quick pass
    recapEnd = findEquivFrame(vid, recapRef, recapRangeStart, int(recapEnd_approx + fRate*2), False, coords=recapCoords) + 2
    if recapEnd < recapRangeStart + 5: #if recap is unexpectedly low
        recapEnd = 64
        print("Recap finder defaulted")
    print("Recap ends at:  {0:.2f} s".format(recapEnd/fRate))

    #find start of next episode
    nextRef = cv2.imread(nextEpPath)
    nextStart_approx = findEquivFrame(vid, nextRef, nextEpRangeStart, incr=int(fRate), coords=nextEpCoords) #first do a quick pass
    nextStart = findEquivFrame(vid, nextRef, nextStart_approx-225, coords=nextEpCoords) + nextEpOffset
    if nextStart < recapEnd: #if nextEp not found, set to end of video
        nextStart = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))*fRate
        print("Next Ep finder defaulted")
    print("Next Ep starts at: {0:.2f} s".format(nextStart/fRate))

    # TODO: add after the break support later
    # afterBreakScan = findEquivFrame(vid, recapRef, recapEnd+15000, nextStart-15000, True, incr=250, coords=coords)
    # if afterBreakScan==-1:
    #     print("After break not found".format())
    # else:
    #     print("AFTER BREAK FOUND, PROCEED WITH CAUTION")
    #     sys.exit(0)

    # TODO: add reencode support later
    # if(reEncode):
    #     nextEndApprox = findEquivFrame(vid, recapRef, nextStart, coords=coords, findFirst=False, incr=75)
    #     nextEnd = findEquivFrame(vid, recapRef, nextStart, nextEndApprox+225, coords=coords, findFirst=False) + 25
    #     print("Next Ep ends at: {0:.2f} s".format(nextEnd/fRate))
    #     vidEnd = vid.get(cv2.CAP_PROP_FRAME_COUNT)/fRate
    #     encStr = """ffmpeg -i '{0}' -i '{1}' \
    #     -vf  "select='between(t,11.84,{7})+between(t,{2:.2f},{3:.2f})+between(t,{4:.2f},{5:.2f})', setpts=N/FRAME_RATE/TB" \
    #     -af "aselect='between(t,11.84,{7})+between(t,{2:.2f},{3:.2f})+between(t,{4:.2f},{5:.2f})', asetpts=N/SR/TB, volume=6.0" \
    #     '/media/sf_Shared/{6}'""".format(fName, fName.replace(".mp4", "_a.mp4"),recapEnd/fRate, nextStart/fRate, nextEnd/fRate, vidEnd, outputName, introEnd)
    #     print(encStr)

    #find keyframes, this will help copy most of the video rather than reencode
    kf = getKeyframes("tmp/keyframes.txt")
    recap_kf = 0
    for item in kf:
        if int(item*fRate)>recapEnd:
            recap_kf=item #- 1/fRate
            break

    muxTxt = introPath
    if (recapEnd/fRate < recap_kf):
        muxTxt += "file '../tmp/p2.mp4'\n"
        cmdStr = "ffmpeg -y -loglevel error -i '{}' -ss {:0.2f} -to {:0.2f} -avoid_negative_ts make_zero 'tmp/{}'".format(fName, recapEnd/fRate, recap_kf-1/fRate, "p2.mp4")
        print(cmdStr)
        os.system(cmdStr)
    else:
        print("Intro ends at kf, skipping p2")

    muxTxt += "file '../tmp/p3.mp4'\n"
    cmdStr = "ffmpeg -y -loglevel error -ss {:0.2f} -i '{}' -c copy -to {:0.2f} -avoid_negative_ts make_zero 'tmp/{}'".format(recap_kf, fName, nextStart/fRate - recap_kf, "p3.mp4")
    print(cmdStr)
    os.system(cmdStr)

    muxTxt += outroPath

    with open("tmp/muxlist.txt", "w") as muxF:
        muxF.write(muxTxt)
    cmdStr = "ffmpeg -loglevel error -f concat -safe 0 -i {} -c copy -avoid_negative_ts make_non_negative 'output/{}'".format("tmp/muxlist.txt", outputName) #fName.replace(".mp4", "_final.mp4").replace("tmp/", ""))
    print(cmdStr)
    os.system(cmdStr)
    #ffmpeg -f concat -safe 0 -i mylist.txt -c copy output.mp4
