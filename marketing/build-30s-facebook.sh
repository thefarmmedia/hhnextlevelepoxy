#!/bin/bash
set -e
SRC=/home/user/hhnextlevelepoxy
SP=/tmp/claude-0/-home-user-hhnextlevelepoxy/b4db0f47-ad07-51f6-aef8-bbb682201bdd/scratchpad
SORA=$SP/fonts/Sora-ExtraBold.ttf
INTER=$SP/fonts/Inter-SemiBold.ttf
SCRIM=$SP/scrim.png
OUT=$SP/segs
mkdir -p $OUT

# 1080x1350 (4:5) from 720x1280 source: upscale 1.5x -> 1080x1920, centre-crop to 1350
BASE="scale=1080:1920:flags=lanczos,crop=1080:1350:0:285,setsar=1"
ENC="-c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -r 30 -c:a aac -b:a 128k -ar 48000 -ac 2"
AF="loudnorm=I=-18:TP=-1.5:LRA=11"

seg () { # $1=infile $2=ss $3=dur $4=drawchain $5=outname
  ffmpeg -v error -ss "$2" -t "$3" -i "$SRC/$1" -i "$SCRIM" \
    -filter_complex "[0:v]${BASE}[b];[b][1:v]overlay=0:750[s];[s]$4[v]" \
    -map "[v]" -map 0:a -af "$AF" -t "$3" $ENC "$OUT/$5.mp4" -y
}

BAR="drawbox=x=80:y=880:w=100:h=10:color=0xFF5F00@1:t=fill"
H1="fontfile=$SORA:fontcolor=white:fontsize=80:x=80:borderw=3:bordercolor=black@0.5"
SUB="fontfile=$INTER:fontcolor=white@0.92:fontsize=37:x=80"

# --- 1. PREP / grinding (same building as the reveal) ------------------- 4.0s
seg "ba266d28-e75a-4ec9-a46b-5fb4f464a15d.mp4" 0.5 4.0 \
"$BAR,drawtext=$H1:text='MOST EPOXY':y=920,\
drawtext=$H1:text='FLOORS FAIL':y=1010,\
drawtext=$SUB:text='Because the concrete was never ground.':y=1118" s1

# --- 2. APPLICATION / squeegee ----------------------------------------- 6.0s
seg "f1546f51-c0b3-4752-94c1-f0e2ca6996ae.mp4" 1.0 6.0 \
"$BAR,drawtext=$H1:text='OURS START ON':y=920,\
drawtext=$H1:text='BARE CONCRETE':y=1010,\
drawtext=$SUB:text='Diamond-ground, then coated by hand.':y=1118" s2

# --- 3. THE REVEAL / same building, two-phase copy --------------------- 7.0s
seg "6724baa2-cb57-44b7-b067-6485612f9e1a.mp4" 1.0 7.0 \
"$BAR,drawtext=$H1:text='SAME BUILDING.':y=920:enable='lt(t\,3.5)',\
drawtext=$H1:text='SEALED FOR GOOD.':y=1010:enable='lt(t\,3.5)',\
drawtext=$SUB:text='Flake broadcast, locked in with polyaspartic.':y=1118:enable='lt(t\,3.5)',\
drawtext=$H1:text='WALK ON IT IN':y=920:enable='gte(t\,3.5)',\
drawtext=$H1:text='24 HOURS.':y=1010:enable='gte(t\,3.5)',\
drawtext=$SUB:text='Drive on it in 48.':y=1118:enable='gte(t\,3.5)'" s3

# --- 4. WARRANTY over finished grey flake ------------------------------ 4.5s
seg "61358b29-b218-4a9b-aac9-472c5f52806d.mp4" 1.0 4.5 \
"$BAR,drawtext=$H1:text='15-YEAR':y=920,\
drawtext=$H1:text='WARRANTY':y=1010,\
drawtext=$SUB:text='In writing. On every install.':y=1118" s4

# --- 5. SCOPE over interior walkthrough -------------------------------- 3.5s
seg "0a5c0ff4-f2b8-40a9-928d-53950059329d.mp4" 14.0 3.5 \
"$BAR,drawtext=$H1:fontsize=72:text='GARAGES. SHOPS.':y=925,\
drawtext=$H1:fontsize=72:text='BASEMENTS.':y=1008,\
drawtext=$SUB:text='Richmond, Kearney and Kansas City.':y=1118" s5

# --- 6. END CARD -------------------------------------------------------- 5.0s
ffmpeg -v error -f lavfi -i "color=c=0x273f50:s=1080x1350:d=5:r=30" \
  -i "$SRC/logo.png" -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=48000" \
  -filter_complex "
[1:v]scale=440:-1[lg];
[0:v][lg]overlay=(W-w)/2:250[a];
[a]drawtext=fontfile=$SORA:text='15-YEAR WARRANTY':fontcolor=white:fontsize=54:x=(w-text_w)/2:y=790,
drawtext=fontfile=$SORA:text='1-DAY INSTALL':fontcolor=white:fontsize=54:x=(w-text_w)/2:y=860,
drawbox=x=(iw-110)/2:y=955:w=110:h=9:color=0xFF5F00@1:t=fill,
drawtext=fontfile=$SORA:text='(816) 419-4287':fontcolor=0xFF5F00:fontsize=82:x=(w-text_w)/2:y=1000,
drawtext=fontfile=$INTER:text='Free quote - Richmond, Kearney and Kansas City':fontcolor=white@0.80:fontsize=32:x=(w-text_w)/2:y=1115,
fade=t=out:st=4.5:d=0.5[v]" \
  -map "[v]" -map 2:a -t 5 $ENC "$OUT/s6.mp4" -y

# --- concat ------------------------------------------------------------
printf "file '%s'\n" $OUT/s1.mp4 $OUT/s2.mp4 $OUT/s3.mp4 $OUT/s4.mp4 $OUT/s5.mp4 $OUT/s6.mp4 > $OUT/list.txt
ffmpeg -v error -f concat -safe 0 -i $OUT/list.txt \
  -vf "fade=t=in:st=0:d=0.4" $ENC -movflags +faststart \
  "$SP/hh-nextlevel-epoxy-30s-facebook.mp4" -y

echo "=== BUILT ==="
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate \
  -of default=nw=1 "$SP/hh-nextlevel-epoxy-30s-facebook.mp4"
