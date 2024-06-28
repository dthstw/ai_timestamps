from pytube import YouTube
import os
import certifi

url_chapters = {}

url_chapters["pFssgtp1ckQ"] = "\n0:00 Why Use A Vest?\n2:18 Day 1: Finding Projects\n3:50 Day 2: Showing Crew & Projects\n10:40 Day 3: An Unexpected Turn Of Events\n13:13 Day 4: Volume Session\n13:52 Day 5: Getting Tired\n15:10 Day 6: Exhausted\n17:05 The Problems With Training Too Much\n18:06 Pros & Cons"
url_chapters["PvRbGuSeI3o"] = "\n00:00- intro \n00:20- turkey salad with poppyseed dressing\n04:08- beef meatloaf\n07:49- chicken and fried rice\n12:19- spaghetti squash (vegetarian option)\n17:23- taste testing\n20:34- let me know\n21:03- the end"

os.environ['SSL_CERT_FILE'] = certifi.where()

#for i, (key, value) in enumerate(url_chapters.items()):
#    print(f"{key}:{key}")
keys_list = list(url_chapters.keys())
#print("http://youtube.com/watch?v="+keys_list[0])
url_first = "http://youtube.com/watch?v="
yt = YouTube(url=url_first+keys_list[0])

print(yt.title)

