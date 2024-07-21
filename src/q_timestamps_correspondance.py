import re
import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv


def extract_timestamps_from_description(description):
    # Updated pattern to match timestamps like `0:00` or `00:00` or `00:00:00`
    pattern = re.compile(r'^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]?\s*(.*)', re.MULTILINE)
    matches = pattern.findall(description)
    print(f"Matches found: {matches}")  # Debug print
    timestamps = [(time, " ".join(text.split()).strip()) for time, text in matches if text.strip()]
    return timestamps


description = """
Join me in this exciting video as I team up with the incredibly talented and dynamic climber, Antoine, also known as "The Flying Frenchman" at our gym. Despite having only four years of climbing experience, Antoine's skills are nothing short of extraordinary.
In this episode, we visit Klatreverket Åssiden, a boulder gym that's new to me, where we climb some fun boulders together. With Antoine's expert tips and guidance, I learned new techniques I can use in my own bouldering training, and I hope that you will too!
Don't miss out on Antoine's amazing insights—be sure to follow him on Instagram @eatingtroll for more climbing inspiration and tips.

Chapters:
0:34 Intro 
1:23 Intro Kristine
3:55 Intro Antoine 
5:19 Warm Up
6:03 Boulder 1
7:03 Boulder 2 
8:09 Boulder 3
9:05 Boulder 4
10:20 Antoine's Project 
14:22 Boulder 6: Real cool
18:56 Boulder 7: Hard core
21:18 Campusing 
25:48 Kristine's return to the green jumpy one
27:15 Next Episode teaser


Music by: Sakura Girl 
"""

extract_timestamps_from_description(description=description)



#description = """
#It's Genuary 2024! Watch as I attempt to build a falling sand simulation in p5.js using a grid of pixels and simple rules. Code: https://thecodingtrain.com/challenges...
#
#🚀 Watch this video ad-free on Nebula https://nebula.tv/videos/codingtrain-...
#
#p5.js Web Editor Sketches:
#🕹️ Falling Sand: https://editor.p5js.org/codingtrain/s...
#🕹️ Falling Sand with Gravity: https://editor.p5js.org/codingtrain/s...
#
#🎥 Previous:    • Coding Challenge 179: Elementary Cell...
#🎥 All:    • Coding Challenges
#
#References:
#🔗 Genuary: https://genuary.art/
#🔗 Sandspiel by Max Bittker: https://sandspiel.club/
#🔗 Making a falling sand simulator: https://jason.today/falling-sand
#📕 The Nature of Code by Daniel Shiffman: https://natureofcode.com/
#
#Videos:
#🎥 Noita 1.0 Launch Trailer by Nolla Games:    • Noita 1.0 Launch Trailer
#🚂 Wolfram CA:    • Coding Challenge 179: Elementary Cell...
#🚂 The Game of Life:    • Coding Challenge #85: The Game of Life
#
#Related Coding Challenges:
#🚂 179 Wolfram CA:    • Coding Challenge 179: Elementary Cell...
#🚂 85 The Game of Life:    • Coding Challenge #85: The Game of Life
#🚂 107 Sandpiles:    • Coding Challenge #107: Sandpiles
#🚂 132 Fluid Simulation:    • Coding Challenge #132: Fluid Simulation
#🚂 102 2D Water Ripple:    • Coding Challenge 102: 2D Water Ripple
#
#Timestamps:
#0:00 Introduction and references
#2:10 About cellular automata
#2:47 The rules for a sand simulation
#3:36 Code! Creating a grid
#5:04 Animating a falling grain of sand
#7:32 About matrix columns and rows
#8:04 Let's account for the bottom edge
#9:09 Adding mouse interaction
#9:42 More sophisticated sand behavior
#10:43 Oops! Some errors to fix
#11:30 Adding randomness
#12:26 Handling left and right edges
#14:00 Checking if mouse is within the canvas
#14:40 Making it more efficient
#14:56 More space and more sand
#16:55 Adding some color!
#18:54 Challenge complete! Let's do some refactoring
#20:58 How could we add gravity?
#21:57 Wrapping up
#
#Editing by Mathieu Blanchette
#Animations by Jason Heglund
#Music from Epidemic Sound
#
#🚂 Website: https://thecodingtrain.com/
#👾 Share Your Creation! https://thecodingtrain.com/guides/pas...
#🚩 Suggest Topics: https://github.com/CodingTrain/Sugges...
#💡 GitHub: https://github.com/CodingTrain
#💬 Discord: https://thecodingtrain.com/discord
#💖 Membership: http://youtube.com/thecodingtrain/join
#🛒 Store: https://standard.tv/codingtrain
#🖋️ Twitter:   / thecodingtrain
#📸 Instagram:   / the.coding.train
#"""
#
#def extract_timestamps_from_description(description):
#    lines = description.strip().split('\n')
#    timestamps = []
#    current_time = None
#    current_text = []
#
#    time_pattern = re.compile(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]?\s*(.*)')
#
#    i = 0
#    while i < len(lines):
#        line = lines[i].strip()
#        match = time_pattern.match(line)
#        if i + 2 < len(lines):               
#            lines[i + 1]
#            lines[i + 2]
#        
#       if match:
#           current_time = match.group(1)
#           current_text = [match.group(2)]
#           if line[i + 1] < len(lines):
#               match = time_pattern.match(line[i + 1])
#               #if it is a match, than it means that the following line is a separate timestamp and we add it to our timestamps list
#               if match:
#                   timestamps.append((current_time, ' '.join(current_text).strip()))
#                   current_time = match.group(1)
#                   current_text = [match.group(2)]
#               #if it is not a match, than we should check conditions for the third consequent line, for now we will add this second line to current text
#               else:
#                   current_text_2 = (current_text, ' '.join(line[i + 1]).strip())
#               #checking the third line
#               if line[i + 2] <= len(lines):
#                   match = time_pattern.match(line[i + 2])
#                   #if it is a match, than we can append tuple current_time and appended current text to our timestamps, because matching shows that third line is a new timestamp
#                   if match:
#                       timestamps.append((current_time, ' '.join(current_text_2).strip()))
#                       #update of current_time and current_text
#                       current_time = match.group(1)
#                       current_text = [match.group(2)]
#                   #if it is not a match, than it means that timestamps are over and we will not use current_text_2 and just append only first separate timestamp
#                   else:
#                       timestamps.append((current_time, ' '.join(current_text).strip())
#               else:
#                   break
#           else:
#               break
#           i += 1