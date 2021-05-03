import glob
import os
import shutil
import subprocess
import sys
import threading
import time
from random import randint

# Note: this script invokes balcon.exe and ffmpeg.exe via subprocess.Popen()
# set their paths here
# TODO: accept overrides to these by way of command line switches
balcon_path = 'L:/utils/balcon/'
balcon_executable = 'balcon.exe'
ffmpeg_path = 'L:/utils/ffmpeg/bin/'
ffmpeg_executable = 'ffmpeg.exe'


def tidy_up_before_we_begin(source_dir, working_dir, wav_file, output_mp3_file):
    # delete any old files matching the filenames we're going to use
    if os.path.exists(source_dir + output_mp3_file):
        os.remove(source_dir + output_mp3_file)
    if os.path.exists(working_dir + output_mp3_file):
        os.remove(working_dir + output_mp3_file)
    if os.path.exists(working_dir + wav_file):
        os.remove(working_dir + wav_file)


def balcon_thread(source_dir, working_dir, input_text_file, wav_file):
    # balcon.exe
    # http://www.cross-plus-a.com/bconsole.htm
    global balcon_path
    global balcon_executable
    run_balcon = subprocess.Popen(  #
        [balcon_path + balcon_executable, '-q', '-sb', '5000', '-f', source_dir + input_text_file,
         '--encoding', 'utf8', '-w', working_dir + wav_file, '-n', 'Microsoft David Desktop'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    while True:
        balcon_return_code = run_balcon.poll()
        # output = run_balcon.stdout.readline()
        # print(output)
        if balcon_return_code is not None:
            if not balcon_return_code == 0:
                print('balcon.exe error!')  # TODO: need to automatically retry balcon as necessary
                x = input("Press any key to exit")
                print('Exiting in 5 seconds...')
                time.sleep(5)
                exit(1)
            else:
                break


def convert_txt_to_wav(source_dir, working_dir, input_text_file, wav_file):
    thread = threading.Thread(target=balcon_thread, args=(source_dir, working_dir, input_text_file, wav_file,))
    thread.start()
    time.sleep(2)

    text_file_size = os.path.getsize(source_dir + input_text_file)
    target_wav_size = text_file_size * 3200
    last_percent = 0
    while True:
        if os.path.exists(working_dir + wav_file):
            cur_wav_file_size = os.path.getsize(working_dir + wav_file)
            cur_percent = int(cur_wav_file_size / target_wav_size * 100)
            if not (cur_percent == last_percent):
                print('Converting from txt to wav: {0}%'.format(min(cur_percent, 100)), end='\r')
                last_percent = cur_percent
        if not thread.is_alive():
            break
    print('Converting from txt to wav: 100%')


def ffmpeg_thread(working_dir, wav_file, output_mp3_file):
    # ffmpeg.exe
    # https://ffmpeg.org/download.html
    global ffmpeg_path
    global ffmpeg_executable
    run_ffmpeg = subprocess.Popen(
        [ffmpeg_path + ffmpeg_executable, '-hide_banner', '-y', '-loglevel', 'warning', '-stats', '-i',
         working_dir + wav_file, '-f', 'mp3', '-ab', '192000', '-vn', working_dir + output_mp3_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    while True:
        # output = run_ffmpeg.stdout.readline()
        # print(output)
        if run_ffmpeg.poll() is not None:
            break


def convert_wav_to_mp3(source_dir, working_dir, wav_file, output_mp3_file):
    thread = threading.Thread(target=ffmpeg_thread, args=(working_dir, wav_file, output_mp3_file,))
    thread.start()
    time.sleep(2)

    wav_file_size = os.path.getsize(working_dir + wav_file)
    target_mp3_size = wav_file_size / 1.6
    last_percent = 0
    while True:
        if os.path.exists(working_dir + output_mp3_file):
            cur_mp3_file_size = os.path.getsize(working_dir + output_mp3_file)
            cur_percent = int(cur_mp3_file_size / target_mp3_size * 100)
            if not (cur_percent == last_percent):
                print('Converting from wav to mp3: {0}%'.format(min(cur_percent, 100)), end='\r')
                last_percent = cur_percent
        if not thread.is_alive():
            break
    print('Converting from wav to mp3: 100%')
    print()
    shutil.move(working_dir + output_mp3_file, source_dir + output_mp3_file)


def convert_single_file(source_dir, input_text_file):
    output_mp3_file = input_text_file[0:-4] + '.mp3'
    wav_file = input_text_file[0:-4] + '.wav'

    temp_dir_number = randint(1000000000, 9999999999)
    working_dir = 'C:/temp/' + str(temp_dir_number) + '/'  # this working_dir can be customized as necessary
    if not os.path.isdir(working_dir):
        os.mkdir(working_dir)

    tidy_up_before_we_begin(source_dir, working_dir, wav_file, output_mp3_file)

    print('Input: {0}'.format(input_text_file))
    convert_txt_to_wav(source_dir, working_dir, input_text_file, wav_file)
    convert_wav_to_mp3(source_dir, working_dir, wav_file, output_mp3_file)

    # cleanup
    try:
        shutil.rmtree(working_dir)
    except OSError as e:
        print("Error deleting working_dir: %s - %s." % (e.filename, e.strerror))

    shutil.move(source_dir + input_text_file, source_dir + 'converted-text/' + input_text_file)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please specify input text file or wildcard pattern.")
        print("examples:")
        print("  python convert_txt_to_mp3.py infile.txt")
        print("  python convert_txt_to_mp3.py *.txt")
        print("  python convert_txt_to_mp3.py \"D:/files/*.txt\"")
        exit()

    full_input_path = sys.argv[1]
    path = full_input_path.split('\\')
    input_text_file = path[-1]

    if len(path) == 1:  # no full path given, just a filename or a wildcard filename pattern
        source_dir = os.getcwd() + '\\'  # a default source directory
    else:
        source_dir = full_input_path[0:(len(full_input_path) - len(input_text_file))]

    if '*' in input_text_file:
        files = glob.glob(input_text_file)
        for f in files:
            convert_single_file(source_dir, f)
    else:
        convert_single_file(source_dir, input_text_file)

    print("Pausing for 100 seconds...")
    time.sleep(100)
    exit(0)
