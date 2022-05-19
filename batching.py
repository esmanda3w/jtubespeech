# a python module that removes the data where the column 'sub' == False obtained from retrieve_subtitle_exists.py 
# since it will not be used in the download_video.py
# it will also split the csv into batches for easier parallel run when downloading the videos later

import pandas as pd
import os
import sys
import argparse

def parse_args():
  parser = argparse.ArgumentParser(
    description="Retrieving whether subtitles exists or not.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
  )
  parser.add_argument("--language_list",    type=str, help="delimited (_) list of target language codes (ISO 639-1) (ja, en, ...)")
  parser.add_argument("--raw_csv",          type=str, help="filepath of the raw csv that is yet to be splitted")  
  parser.add_argument("--entries",          type=int, default=50, help="number of entries per csv file")
  
  return parser.parse_args(sys.argv[1:])

class DataframePruningAndBatching():
    def __init__(self, lang_codes, source_csv_path, dest_dir, entries_per_csv):
        self.lang_codes = lang_codes
        self.source_csv_path = source_csv_path
        self.dest_dir = dest_dir
        self.entries_per_csv = entries_per_csv

    def remove_unwanted_row(self):
        # reads the csv generated from retrieve_subtitle_exists.py
        df_ = pd.read_csv(self.source_csv_path)

        # creates new dataframe with only column 'sub' == True
        df = df_.copy()
        for lang in self.lang_codes:
            df = df[df[f"sub_{lang}"] == True]

        # reoder the dataframe by the 'auto' column
        # df = df.sort_values(by=['auto'], ascending=True)

        # split the csv files into batches of csv files
        self.split_into_batches(df)

    # split the csv files into batches of csv files
    def split_into_batches(self, df):
        for batch in range((len(df)-1) // self.entries_per_csv + 1):
            if batch != (len(df)-1) // self.entries_per_csv + 1:
                df_batch = df.iloc[batch*self.entries_per_csv: (batch+1)*self.entries_per_csv]
            else:
                df_batch = df.iloc[batch*self.entries_per_csv:]

            #df_batch.to_csv(f'{os.path.dirname(self.source_csv_path)}/batch_{batch+1}.csv', index=False)
            df_batch.to_csv(f'{self.dest_dir}/{os.path.basename(self.dest_dir)}_batch_{batch+1}.csv', index=False)
            print(f'Batch {batch+1}: Done')
        print('Done!')

    def __call__(self):
        return self.remove_unwanted_row()

if __name__ == '__main__':

    # passing arguments
    args = parse_args()
  
    df_batching = DataframePruningAndBatching(lang_codes=args.language_list.split("_"), 
                                              source_csv_path=args.raw_csv, 
                                              dest_dir=os.path.dirname(args.raw_csv), 
                                              entries_per_csv=args.entries)

    df_batching()