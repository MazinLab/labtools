import sys
import pstats
import cProfile


def profile_this_function(sort="time", restrictions=()):
    """
    This function can be used as a decorator on any function to provide detailed
    profiling information.

    Args:
        sort: Sort the output using this kwarg
            From https://docs.python.org/3/library/profile.html#pstats.Stats:
            'calls'	        call count
            'cumulative'	cumulative time
            'cumtime'	    cumulative time
            'file'	        file name
            'filename'	    file name
            'module'	    file name
            'ncalls'	    call count
            'pcalls'	    primitive call count
            'line'	        line number
            'name'	        function name
            'nfl'	        name/file/line
            'stdname'	    standard name
            'time'	        internal time
            'tottime'       internal time

        restrictions: Arguements for the print_stats function.
            From https://docs.python.org/3/library/profile.html#pstats.Stats.print_stats:
            The arguments provided (if any) can be used to limit the list down to the
            significant entries. Initially, the list is taken to be the complete set of
            profiled functions. Each restriction is either an integer (to select a count
            of lines), or a decimal fraction between 0.0 and 1.0 inclusive (to select a
            percentage of lines), or a string that will interpreted as a regular
            expression (to pattern match the standard name that is printed). If several
            restrictions are provided, then they are applied sequentially.
    Example:
        Profile slow_function and sort the results by cumulative time, showing 10% of the
        output.

        @profile_this_function(sort='cumtime', restrictions=(0.1,))
        def slow_function(args):
            ** slow stuff here **
    """
    def decorator(func):
        def profiled_function(*args, **kwargs):
            profile = cProfile.Profile()
            try:
                profile.enable()
                result = func(*args, **kwargs)
                profile.disable()
                return result
            finally:
                stats = pstats.Stats(profile, stream=sys.stderr).sort_stats(sort)
                stats.print_stats(*restrictions)
        return profiled_function
    return decorator
