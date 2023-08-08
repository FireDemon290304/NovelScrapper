import time


def timeme(method):
    """
    A decorator that measures the execution time of a function and prints it out.

    Parameters:\n
    - method: the function to be decorated\n

    Optional parameters:\n
    - threshold: the time threshold in seconds (default: 10)\n
    - time_format: the output format ('hmsr' for hours, minutes, seconds, and milliseconds, 's' for seconds rounded to five decimal places; default: 'hmsr')\n
    - verbose: print execution time. Default is true
    """

    def wrapper(*args, **kw):
        verbose = kw.get('verbose', True)  # Get the 'verbose' flag, default is True
        threshold = kw.get('threshold', 10)
        time_format = kw.get('output_format', 'hmsr')

        start_time = time.time()
        try:
            result = method(*args, **kw)
        except Exception as e:
            if verbose:
                print(f'{method.__name__} raised an exception: {e}.')
            raise
        else:
            end_time = time.time()

        if verbose:  # If 'verbose' flag is True, print the execution time
            elapsed_time = round(end_time - start_time, 4)
            if elapsed_time > threshold:
                if time_format == 'hmsr':
                    hours, remainder = divmod(elapsed_time, 3600)
                    minutes, remainder = divmod(remainder, 60)
                    seconds, milliseconds = divmod(remainder, 1)
                    milliseconds = int(milliseconds * 1000)
                    time_str = f'{hours:.0f}:{minutes:02.0f}:{seconds:02.0f}:{milliseconds:03d}'
                elif time_format == 's':
                    time_str = f'{elapsed_time:.5f}'
                else:
                    raise ValueError(f'Invalid output format: {time_format}')
            else:
                time_str = f'{elapsed_time:.5f}'

            class_name = type(args[0]).__name__ if args else ''
            print(f'{class_name + "." if class_name else ""}{method.__name__} ran for {time_str} seconds.')

        return result
    return wrapper
