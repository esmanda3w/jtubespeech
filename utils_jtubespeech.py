import os
from pathlib import Path
from tqdm import tqdm
import shutil
from pydub import AudioSegment
import webvtt
import re

class RestructureFileDirectoryJtubespeech:

    def __init__(self, root_folder, dest_folder, file_type, append_lang_to_filename=None):
        self.root_folder = root_folder
        self.dest_folder = dest_folder
        self.file_type = file_type
        self.append_lang_to_filename = append_lang_to_filename

    # create new directory and ignore already created ones
    def create_new_dir(self, directory):
        try:
            os.mkdir(directory)
        except OSError as error:
            pass # directory already exists!

    # a method to make a copy of the file (vtt or wav) into another directory for restructuring
    def combine_files_to_same_directory(self):
    
        # create a new main directory for the final raw data directory
        self.create_new_dir(f'{self.root_folder}/{self.dest_folder}')
        
        # list the folder where the vtt or wav folder resides
        for subfolder in os.listdir(f'{self.root_folder}/{self.file_type}'):
            # list the files in the folder where the vtt or wav file resides
            for filename in os.listdir(f'{self.root_folder}/{self.file_type}/{subfolder}'):
                
                # create a new directory to group the vtt and wav file together
                self.create_new_dir(f'{self.root_folder}/{self.dest_folder}/{subfolder}')

                source = f'{self.root_folder}/{self.file_type}/{subfolder}/{filename}'
                destination = f'{self.root_folder}/{self.dest_folder}/{subfolder}/{filename}'

                # copy vtt or wav files
                if os.path.isfile(source):
                    shutil.copy(source, destination)

                    # differentiate between vtt files of different languages
                    if self.append_lang_to_filename != None:
                        print(destination)
                        os.rename(destination, destination[:-4] + "_" + self.append_lang_to_filename + ".vtt")
        print(f'Moved: {self.file_type}')

    def __call__(self):
        return self.combine_files_to_same_directory()


class UtilsJtubespeech:

    def __init__(self, main_data_folder, preprocessed_data_folder, audio_format):
        self.main_data_folder = main_data_folder
        self.preprocessed_data_folder = preprocessed_data_folder
        self.audio_format = audio_format

    # create new directory and ignore already created ones
    def create_new_dir(self, directory):
        try:
            os.mkdir(directory)
        except OSError as error:
            pass # directory already exists!

    # retrieve all the relevant values (start, stop, annotation) from the vtt file
    def get_vtt_values(self, filepath):
        
        # create a dictionary to store the start, end and annotation from the vtt file
        data_dict = {
            'start': [],
            'end': [],
            'annotation': []
        }

        # sample reading of vtt
        for idx,caption in enumerate(webvtt.read(filepath)):
            # time is in this format -> hh:mm:ss.xxx, split it to list and convert into float value with [hh, mm, ss.xxx] format
            time_list_start = [float(x) for x in caption.start.split(':')]
            time_list_end = [float(x) for x in caption.end.split(':')]

            # convert hh:mm:ss.xxx into ss.xxx
            time_list_start[2] += time_list_start[1]*60 + time_list_start[0]*3600
            time_list_end[2] += time_list_end[1]*60 + time_list_end[0]*3600
            time_list_start[1], time_list_start[0], time_list_end[1], time_list_end[0] = 0.0, 0.0, 0.0, 0.0

            # append the values into the dictionary 
            data_dict['start'] += [time_list_start[2]]
            data_dict['end'] += [time_list_end[2]]
            data_dict['annotation'] += [caption.text.replace('\n', ' ')]
            
        return data_dict

    # write to text file according to the librispeech format
    def write_to_txt_file(self, file_dir, data_dict):
        
        # get just the filename of the file without directory or extension
        filename = Path(file_dir).stem
        # replace the .trans with '' in the text file
        filename = filename.replace('.trans', '')

        with open(file_dir, 'w+') as f:
            for i,j in enumerate(data_dict['annotation']):
                # uppercase the alphabets
                preprocessed_text = j.upper()

                # text preprocessing using regex
                #preprocessed_text = re.sub('[^a-zA-Z0-9$%.\' ]', '', preprocessed_text)
                preprocessed_text = re.sub('[^a-zA-Z0-9$%.\' ]|(?!\d)\.(?!\d)', '', preprocessed_text)


                f.write(f'{filename}-{i:04} {preprocessed_text}\n')

    # define the preprocessed data path so that the preprocessed data can be saved in another directory later
    def get_preprocessed_dirname(self, root):
        root_split = root.split('/')
        
        # get the index that has the base data folder
        list_index = root_split.index(os.path.basename(self.main_data_folder))
        
        # modify the root folder to the preprocessed one
        root_split[list_index] = os.path.basename(self.preprocessed_data_folder)
        
        # the final preprocessed directory
        root_preprocessed = '/'.join(root_split)

        return root_preprocessed

    # slice the audio files based on the start and end timing
    def slice_audio(self, file_dir, root_preprocessed, data_dict):
        # get the audiofile
        newAudio = AudioSegment.from_wav(file_dir)
        for i, j in enumerate(data_dict['start']):

            # declare the filename to be saved
            filename = f'./{root_preprocessed}/{Path(file_dir).stem}-{i:04}.{self.audio_format}'

            # *1000 because it is in milliseconds and set frame rate to 16kHz (16000) as this is the sampling rate required
            newAudio_sliced = newAudio[data_dict['start'][i]*1000:data_dict['end'][i]*1000].set_frame_rate(16000)  
            newAudio_sliced.export(filename, format=self.audio_format)