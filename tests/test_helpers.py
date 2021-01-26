def format_seconds(t, places=8):
    sec, d = f'{t:.{places}f}'.split('.')
    
    milli = d[:3].lstrip('0')

    micro = d[3:places].rstrip('0')
    if len(micro) > 3:
        micro = (micro[:3] + '.' + micro[3:])
    micro = micro.lstrip('0')
    
    sec_str   = f'{sec} second{"s" if sec not in ["0", "1"] else ""}'          if sec != '0' else ''
    milli_str = f'{milli} millisecond{"s" if milli not in ["0", "1"] else ""}' if milli != '' else ''
    micro_str = f'{micro} microsecond{"s" if micro not in ["0", "1"] else ""}' if micro != '' else ''
    
    round_time = f'{t:.{places}f}'
    
    return ', '.join((p for p in (sec_str, milli_str, micro_str, f'({round_time}s)') if p != ''))
