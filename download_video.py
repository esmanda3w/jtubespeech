import time
import argparse
import sys
import subprocess
import shutil

import pydub
from pathlib import Path
from util import make_video_url, make_basename, vtt2txt, autovtt2txt
import pandas as pd
from tqdm import tqdm
import os

def parse_args():
    parser = argparse.ArgumentParser(
        description="Downloading videos with subtitle.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--language_list",   type=str, help="delimited (_) language code (ISO 639-1) (ja, en, ...)")
    parser.add_argument("--sublist",         type=str, help="batched csv file with a list of video IDs with subtitles")
    parser.add_argument("--outdir",          type=str, default="video", help="dirname to save videos")
    parser.add_argument("--keeporg",         action='store_true', default=False, help="keep original audio file.")

    return parser.parse_args(sys.argv[1:])

def download_video(lang_list, fn_sub, outdir="video", wait_sec=10, keep_org=False):
    """
    Tips:
      If you want to download automatic subtitles instead of manual subtitles, please change as follows.
        1. replace "sub[sub["sub"]==True]" of for-loop with "sub[sub["auto"]==True]"
        2. replace "--write-sub" option of youtube-dl with "--write-auto-sub"
        3. replace vtt2txt() with autovtt2txt()
        4 (optional). change fn["vtt"] (path to save subtitle) to another. 
    """
    lang_dir = "_".join(lang_list)

    # parse args to take in the language code
    args = parse_args()

    sub = pd.read_csv(fn_sub)

    # initialise number of successful scrape
    success_count = 0

    # for videoid in tqdm(sub[sub[f"sub_{lang}"] == True]["videoid"]):  # manual subtitle only
    for videoid in tqdm(sub["videoid"]):
        file_formats = ["wav", "wav16k"]
        # append language to vtt and txt files (subtitle files)
        for lang in lang_list:
            file_formats.append(f"vtt_{lang}")
            file_formats.append(f"txt_{lang}")

        fn = {}
        for k in file_formats:
            fn[k] = Path(outdir) / lang_dir / k / \
                (make_basename(videoid) + "." + k[:3])
            fn[k].parent.mkdir(parents=True, exist_ok=True)

        if not fn["wav16k"].exists():
            print(videoid)

            # download
            url = make_video_url(videoid)
            base = fn["wav"].parent.joinpath(fn["wav"].stem)
            languages = ",".join(lang_list)
            cp = subprocess.run(
                f"youtube-dl --sub-lang {languages} --extract-audio --audio-format wav --write-sub {url} -o {base}.\%\(ext\)s", shell=True, universal_newlines=True)
            if cp.returncode != 0:
                print(f"Failed to download the video: url = {url}")
                continue
            try:
                for lang in lang_list:
                    shutil.move(f"{base}.{lang}.vtt", fn[f"vtt_{lang}"])
            except Exception as e:
                print(
                    f"Failed to rename subtitle file. The download may have failed: url = {url}, filename = {base}.{lang}.vtt, error = {e}")
                continue

            # vtt -> txt (reformatting)
            try:
                for lang in lang_list:
                    txt = vtt2txt(open(fn[f"vtt_{lang}"], "r").readlines())
                    with open(fn[f"txt_{lang}"], "w") as f:
                        f.writelines(
                            [f"{t[0]:1.3f}\t{t[1]:1.3f}\t\"{t[2]}\"\n" for t in txt])
            except Exception as e:
                print(
                    f"Falied to convert subtitle file to txt file: url = {url}, filename = {fn[f'vtt_{lang}']}, error = {e}")
                continue

            # wav -> wav16k (resampling to 16kHz, 1ch)
            try:
                wav = pydub.AudioSegment.from_file(fn["wav"], format="wav")
                wav = pydub.effects.normalize(
                    wav, 5.0).set_frame_rate(16000).set_channels(1)
                wav.export(fn["wav16k"], format="wav", bitrate="16k")
            except Exception as e:
                print(
                    f"Failed to normalize or resample downloaded audio: url = {url}, filename = {fn['wav']}, error = {e}")
                continue

            # remove original wav
            if not keep_org:
                fn["wav"].unlink()

            # wait
            if wait_sec > 0.01:
                time.sleep(wait_sec)
        
        success_count += 1

    print('\n---------------------------------\n')
    print(f'Number of successful scrape in this batch: {success_count}/{len(sub["videoid"])}')
    print('\n---------------------------------\n')
    return Path(outdir) / lang_dir


if __name__ == "__main__":
    args = parse_args()

    dirname = download_video(lang_list=args.language_list.split("_"), 
                             fn_sub=args.sublist, 
                             outdir=args.outdir)

    print(f"save {args.language_list.upper()} videos to {dirname}.")