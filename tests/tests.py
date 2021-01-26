import os
import sys
import time
import cProfile, pstats, io
import pprint

from test_helpers import format_seconds

import test_regexps

import logging
logging.basicConfig(level=logging.DEBUG)
# ----

tests = {
    # Single decorator
    
    # const
    'play'                                         : 'Playing music',
    
    # const <var>
    'open slack'                                   : 'Opening Slack',
    
    # ----
    # 2 decorators
    'play nightswimming'                           : 'Playing "Nightswimming"',
    
    # const const <var>
    "play video dankest memes"                     : 'Asking Youtube to play "Dankest Memes"',
    
    # Intermixed regex
    # const <var> (const|const) <var>
    'open myfile.txt with notepad'                 : 'Asking Notepad to open "myfile.txt"',
    
    # ----
    # Default argument in function definition
    # const const <var> const <var>
    'play video help I\'m alive with vimeo'       : 'Asking Vimeo to play "Help I\'M Alive"',
    
    # Options defined in variable
    # const <var> const <var=(const|const>
    'play exposition with zune'                    : 'Asking Zune to play "Exposition"',
    'play all my friends with play music'          : 'Asking Play Music to play "All My Friends"',
    
    # ----
    # Collision handling
    
    # Constants and variables
    'play with or without you'                     : 'Playing "With Or Without You"',
    'play with or without you with play music'     : 'Asking Play Music to play "With Or Without You"',
    'play play music with play music'              : 'Asking Play Music to play "Play Music"',
    'play play music with play music with zune'    : 'Asking Zune to play "Play Music With Play Music"',
    
    # --
    # Constants take precedence over variables; 3 intents on one function
    # 4/5 consts
    'turn on the light'                            : 'Turning on the light',
    'turn on the light now'                        : 'Turning on the light',
    'turn on the light pronto'                     : 'Turning on the light',
    
    # Separate functions from above
    # [4 consts] <var>
    'turn on the light soon'                       : 'The light will turn on soon',
    
    # [5 consts] <var>
    'turn on the light at 3:00'                    : 'The light will turn on at 3:00',
    
}


# ================================
def run_tests(intentions, show_results=True, profile=False):
    passed = 0
    failed = 0
    times = []
    
    if profile:
        profiler = cProfile.Profile(timer=time.process_time)
        profiler.enable() 
    
    for i, (test, expected) in enumerate(tests.items()):
        start = time.perf_counter()
        result, match = intentions.match(test)
        
        end = time.perf_counter()
        times.append(end-start)
        
        success = result and (match == expected)
        
        if success:
            passed += 1
        else:
            failed += 1
        
        if show_results:
            pad_before = " " * max(0, (50 - len(test)))
            pad_after = " " * max(0, (60 - len(match)))
            if not success: print('--')
            print(f'{i:<4}: {test} {pad_before} => {match} {pad_after} || {"Passed" if success else "Failed **"}')
            if not success: print('--')
    
    if profile:
        profiler.disable() 
        
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
     
    if show_results:
        print(f'\n{len(tests)}/{passed} passed, {failed} failed')

    return times

    
# ================================
def get_runtime(intentions, loops):
    print(f'\nRunning time test ({len(intentions)} intents, {len(tests)} queries, {loops} iterations)...')
    
    match_times = []
    total_test_times = []
    for _ in range(loops):
        this_run = run_tests(intentions, show_results=False)
        match_times += this_run
        total_test_times.append(sum(this_run))
    
    return match_times, total_test_times

# ================================
def run_stress_test(loops, func_count=None, dec_count=None, profile=False):
    all_args  = func_count is None and dec_count is None
    all_files = os.path.isfile('stress_intents.py' and os.path.isfile('stress_tester.py'))
    
    if not (all_args and all_files):
        print('Generating random intents for stress test...')
        test_regexps.generate_random_intentions(func_count=func_count, dec_count=dec_count)

    import stress_tester
    stress_tester.run_stress_tests(loops, profile)


# ================================
def avg(iterable):
    return sum(iterable) / len(iterable)
    
    
if __name__ == '__main__':
    args = sys.argv
    
    if len(args) == 1:
        print('Valid arguments are [--base, --base-profile], --runtime, [--stress, --stress-profile]')
        sys.exit()
    
    flags = {
        'base':           '--base' in args,
        'base-profile':   '--base-profile' in args,
        'runtime':        '--runtime' in args,
        'stress':         '--stress' in args,
        'stress-profile': '--stress-profile' in args
    }
    
    start = time.perf_counter()
    intentions = test_regexps.get_intentions()
    end = time.perf_counter()
    print(f'\nIntentCollection built in {format_seconds(end - start)}')
    
    sep = '===================\n'
    
    print()
    if flags['base'] or flags['base-profile']:
        run_tests(intentions, profile=flags['base-profile'])

    if flags['runtime']:
        print(sep)
        match_times, total_test_times = get_runtime(intentions, 20000)
        
        print('\n(Match)')
        print(f'Average: {format_seconds(avg(match_times))}')
        print(f'Minimum: {format_seconds(min(match_times))}')
        print(f'Maximum: {format_seconds(max(match_times))}')
        
        print('\n(Full test set)')
        print(f'Average: {format_seconds(avg(total_test_times))}')
        print(f'Minimum: {format_seconds(min(total_test_times))}')
        print(f'Maximum: {format_seconds(max(total_test_times))}')
        print(f'Total:   {format_seconds(sum(total_test_times))}')
    
    if flags['stress'] or flags['stress-profile']:
        print('\n' + sep)
        #run_stress_test(loops=250, func_count=1000, dec_count=8, profile=flags['stress-profile'])
        run_stress_test(loops=1, func_count=10000, dec_count=8, profile=flags['stress-profile'])
        print('\n' + sep)
    
    print(f'\n{sep}Testing complete.')
    print(sep)
