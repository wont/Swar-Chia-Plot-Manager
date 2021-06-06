import os
import time
import psutil
import shutil


def health_check(healths, running_work, to_kill_elapsed):

    for rw in running_work:
        w = running_work[rw]
        line_count = w.line_count
        progress = float(w.progress.strip('%'))
        temp_folder = w.job.temporary_directory[0]
        name = w.job.name  

        print(f'health check for {name} / {rw}： ({progress}%): ')
        to_print = ''
        if not rw in healths:
            h = {}
            h['line_count'] = line_count
            h['progress'] = progress
            h['earliest_time'] = time.time()
            h['current_time'] = time.time()
            h['elapsed'] = 0  # in seconds
            h['work_start'] = w.time_start
            h['start'] = time.time()
            h['init_progress'] = progress
            h['plot_id'] = w.plot_id
            healths[rw] = h
            est_seconds = 100 * \
                (time.time()-h['work_start']) / \
                progress - (h['start']-w.time_start)
            to_finish = f'{est_seconds/3600:.0f} H {est_seconds%3600:.0f} Sec'
            to_print = f'\t every thing seems OK. current line count: {line_count}, est. {to_finish} to finish. pid: {rw}, temp_folder: {temp_folder}'

        elif line_count > 10 and progress > 0.1 and progress < 98:
            h = healths[rw]
            if h['line_count'] == line_count and abs(h['progress'] -
                                                     progress) < 0.001:
                # to kill if stuck in {to_kill_elapsed} seconds
                elapsed = int(time.time() - h['earliest_time'])
                plot_id = h['plot_id']
                if elapsed > to_kill_elapsed:
                    # kill
                    to_print = f'\t to kill process {rw}, it has stucked for {elapsed} seconds'
                    p = psutil.Process(rw)
                    p.terminate()
                    # clear temp folder
                    remove_temp_folder(temp_folder,plot_id=plot_id)
                else:

                    to_print = f'\t the process {rw} has stucked for {elapsed} seconds in log line: {line_count}. it will be killed after stucked for more {to_kill_elapsed-elapsed} seconds.'
                    to_print += f'\n\t the plot id is {plot_id}.'

            else:
                last_line_count = h['line_count']
                est_seconds = (100-progress)*(time.time() -
                                              h['start'])/(progress-h['init_progress'])
                #est_seconds = 100*(time.time()-h['start'])/progress
                to_finish = f'{est_seconds/3600:.0f} H {est_seconds%3600:.0f} Sec'
                h['line_count'] = line_count
                h['progress'] = progress
                h['earliest_time'] = time.time()
                h['current_time'] = time.time()

                to_print = f'\t it seems OK. last log count: {last_line_count}, current: {line_count}; est. {to_finish} to finish. pid: {rw}, temp: {temp_folder}'
        print(to_print)
    return healths


def remove_temp_folder(folder, plot_id='USE_THE_ID_TO_FILTER'):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if plot_id not in file_path:
            continue
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
