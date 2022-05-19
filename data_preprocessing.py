import os
import tarfile
import sys
import argparse
import shutil
from tqdm import tqdm
from pathlib import Path
from utils_jtubespeech import RestructureFileDirectoryJtubespeech, UtilsJtubespeech

def parse_args():
    parser = argparse.ArgumentParser(
        description="To preprocess the scraped jtubespeech data into a more standardized format.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--root_folder",                type=str, help="the folder where the raw vtt and wav16k folder resides")
    parser.add_argument("--dest_folder_name",           type=str, help="the directory name created to store the restructured data for the preprocessing task")
    parser.add_argument("--file_type_vtt",              type=str, help="delimited (&) file type(s) of the folder name needed to extract the transcript")
    parser.add_argument("--file_type_wav",              type=str, help="file type of the folder name needed to extract the raw audio")
    parser.add_argument("--main_data_folder",           type=str, help="main data folder with all the raw data that is to be processed")
    parser.add_argument("--preprocessed_data_folder",   type=str, help="new directory name for the preprocessed data")
    parser.add_argument("--audio_format",               type=str, help="the audio format of the exported preprocessed audio")
    
    return parser.parse_args(sys.argv[1:])

class DataPreprocessingJtubespeech:
    
    def __init__(self, main_data_folder, preprocessed_data_folder, audio_format, vtt_files):
        self.main_data_folder = main_data_folder
        self.preprocessed_data_folder = preprocessed_data_folder
        self.audio_format = audio_format
        self.vtt_files = vtt_files

    def data_preprocessing(self):
        # walk and find all .wav and .vtt file
        for root, dirs, files in tqdm(os.walk(self.main_data_folder)):

            # calling the class object
            preprocess = UtilsJtubespeech(main_data_folder=self.main_data_folder,
                                          preprocessed_data_folder=self.preprocessed_data_folder,
                                          audio_format=self.audio_format)

            # function call to define the preprocessed directory for the processed data (text and audio)
            root_preprocessed = preprocess.get_preprocessed_dirname(root)
            
            # create the preprocessed data directory
            preprocess.create_new_dir(f'./{root_preprocessed}/')

            for file in files:
                # join the root and the filepath to access the textgrid data
                file_access = os.path.join(root, file)
                
                # check for files with .vtt extension
                if file.endswith('.vtt'):
                    data_dict = preprocess.get_vtt_values(file_access)
                    preprocess.write_to_txt_file(f'{root_preprocessed}/{Path(file_access).stem}.trans.txt', data_dict)
                    
                elif file.endswith('.wav'):
                    # get the first vtt filename and extension since timestamps are the same for all vtt files
                    # same filename for .wav and .vtt but with the language appended to the back for vtt
                    file_access_vtt = file_access.split('.') 
                    file_name_vtt = file_access_vtt[0] + "_" + vtt_files[0][4:]
                    
                    # extract the required data (in a dictionary) from the .vtt file
                    data_dict = preprocess.get_vtt_values(filepath=f'{file_name_vtt}.vtt')
                    
                    # slice the audio files based on the start and end timing
                    preprocess.slice_audio(file_access, root_preprocessed, data_dict)
        
        print('Done: Preprocessing')

    def make_tarfile(self, output_name, src_dir):
        with tarfile.open(output_name,"w:gz") as tar:
            tar.add(src_dir,arcname=os.path.basename(src_dir))
        
        print('Done: Compressing')

    def __call__(self):
        return self.data_preprocessing()


if __name__ == '__main__':
    
    args = parse_args()

    ## RESTRUCTURING THE JTUBESPEECH DATA FILE DIRECTORY
    vtt_files = args.file_type_vtt.split("&")
    for vtt_file in vtt_files:
        file_combine_vtt = RestructureFileDirectoryJtubespeech(root_folder=args.root_folder, 
                                                               dest_folder=args.dest_folder_name, 
                                                               file_type=vtt_file,
                                                               append_lang_to_filename=vtt_file[4:])
        file_combine_vtt()

    file_combine_wav = RestructureFileDirectoryJtubespeech(root_folder=args.root_folder, 
                                                           dest_folder=args.dest_folder_name,
                                                           file_type=args.file_type_wav)

    file_combine_wav()

    ## DATA PREPROCESSING OF THE JTUBESPEECH DATA TO THE LIBRISPEECH FORMAT
    preprocess = DataPreprocessingJtubespeech(main_data_folder = args.main_data_folder,
                                              preprocessed_data_folder = args.preprocessed_data_folder,
                                              audio_format = args.audio_format,
                                              vtt_files = vtt_files)

    preprocess()

    # delete the raw data folder after preprocessing is done
    shutil.rmtree(args.main_data_folder)

    ## MAKE IT INTO A .tar.gz compressed folder
    #preprocess.make_tarfile(f'./{config["preprocessed_data_folder"]}.tar.gz', f'./{config["preprocessed_data_folder"]}')
