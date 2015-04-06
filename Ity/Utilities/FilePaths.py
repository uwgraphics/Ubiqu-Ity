# coding=utf-8
__author__ = 'kohlmannj'

import os
import re
from collections import OrderedDict


def get_file_paths(
    paths=(),
    patterns=None,
    recursion_levels=8,
    valid_paths=set(),
    excluded_paths=set(),
    debug=False
):
    """
    Given a list of paths, returns two sets of file paths: one set containing
    "valid" file paths, and another set containing "excluded" file paths, which
    have failed the validation criteria or are directories (i.e. NOT files).

    "Valid" means that:

    * The files at said paths exist.
    * The path is to a file (or symlink or something), and NOT to a directory.
    * The path matches one of the regular expression patterns in path_patterns.

    For performance reasons, we do not attempt to open the files for reading,
    so functions that actually perform real work with these paths should
    perform their own checks / error handling for readability and such.

    Filtering via regular expression is disabled when path_patterns is None.

    This method is optionally recursive. The number of recursion levels (i.e.
    the number of descents into subfolders) can be controlled:

    * recursion_levels is True --> recurse ad infinitum.
    * type(recursion_levels) is int and recursion_levels > 0 -->
      recurse to a maximum of recursion_level levels.
    * Otherwise (i.e. recursion_levels is False, == 0, is None, etc.),
      recursion is disabled.

    We use 8 as the default value of recursion_levels to prevent total runaway
    recursion calls. Note that if recursion_levels equals 0 or is False, *no*
    paths represnting folders will be recursed into; the only valid paths will
    be paths to *files*.

    Note that if recursion_levels equals 1, we won't even get a folder's contents.

    Keyword arguments:
    paths            -- tuple of file system paths to folders or files.
                        (default (), an empty tuple)
    patterns         -- tuple of regular expressions to filter file paths by,
                        or None if we don't want to filter by regex pattern/s.
                        (default None)
    recursion_levels -- int or boolean indicating how many folder levels deep
                        the function should go. A positive non-zero integer
                        indicates a maximum recursion depth, True indicates
                        infinite recursion depth, and anything else (0, False,
                        None, etc.) indicates that we shouldn't recurse.
                        (default 8)
    valid_paths      -- set of strs containing the unique set of "validated"
                        file paths. Used as an argument to pass the "global"
                        set to recursive calls of the function.
                        (default set())
    excluded_paths   -- set of strs containing the unique set of file paths
                        that are "invalid" and thereby excluded from the set of
                        "valid" paths. Used as an argument to pass the "global"
                        set to recursive calls of the function.
                        (default set())
    debug            -- bool indicating whether or not we should print some
                        debug output to stdout while running the function.
                        (default False)

    """
    # Some setup for recursion_levels.
    # Prevent runaways by default.
    next_recursion_levels = False
    if recursion_levels is True:
        next_recursion_levels = True
    elif type(recursion_levels) is int:
        # Next recursion level should be one less.
        if recursion_levels > 0:
            # We'll recurse for this level and however many more levels.
            next_recursion_levels = recursion_levels - 1
            if next_recursion_levels <= 0:
                next_recursion_levels = False
            # We're definitely recursing for this level.
            recursion_levels = True
        else:
            # We'll recurse for this level, but no deeper.
            next_recursion_levels = False
    # Okay, we got garbage, so disable recursion.
    else:
        recursion_levels = False
        next_recursion_levels = False

    # Alright bus (er, function?), do your stuff!
    for path in paths:
        # Get the most absolute formulation of the path we can muster.
        path = os.path.abspath(os.path.expanduser(path))
        # Is this a duplicate path we've already validated?
        if path in valid_paths or path in excluded_paths:
            # Skip duplicate paths.
            if debug:
                print "Skipping duplicate path '%s'" % path
            continue
        # Alright, file or directory? Let's ask.
        # is the path to a *file*?
        if os.path.isfile(path):
            # Add this path, no more questions asked, if we are NOT
            # filtering by regular expression (i.e. path_patterns is None).
            if patterns is None:
                valid_paths.add(path)
            # Okay, we *are* filtering by regular expression. Get crackin'.
            else:
                for pattern in patterns:
                    # Add the path and break as soon as we get a match for
                    # any pattern.
                    match = re.search(pattern, path)
                    if match is not None:
                        valid_paths.add(path)
                        break
                # No matches found if we made it here, so add the path to
                # the excluded paths set.
                excluded_paths.add(path)
        # Is this a directory? Should we recurse into it?
        elif os.path.isdir(path) and recursion_levels is True:
            if debug:
                print "Recursively validating paths inside '%s'..." % path
            # Get this directory's contents
            child_paths = tuple([os.path.join(path, child_path) for child_path in os.listdir(path)])
            # Validate paths recursively for child_paths with whatever the
            # next level of recursion should be.
            get_file_paths(
                child_paths,
                patterns=patterns,
                recursion_levels=next_recursion_levels,
                valid_paths=valid_paths,
                excluded_paths=excluded_paths,
                debug=debug
            )
        else:
            # Can't do anything else with it, so exclude it.
            excluded_paths.add(path)
    # All done, so return both sets of valid and excluded file paths .
    return valid_paths, excluded_paths


def valid_paths(
    paths=(),
    patterns=('\.txt$',),
    recursion_levels=8,
    debug=False
):
    """
    Returns a tuple of strings that are "valid" file paths. Also corrects input
    in the case when paths is a single str instead of a list of strs.

    Please refer to the docstring for get_text_paths for more
    information about what we consider a "valid" file path.

    By default, only considers file paths ending in ".txt" to be valid.

    Keyword arguments:
    paths            -- tuple of strings representing file paths to validate.
                        We'll do The Right Thing(TM) if given a str instead,
                        though.
                        (default (), an empty tuple)
    patterns         -- tuple of regular expression patterns by which to
                        validate (i.e. filter) file paths.
                        (default ('\.txt$',), i.e. "paths ending in '.txt'")
    recursion_levels -- int or boolean indicating how many folder levels deep
                        the recursive get_file_paths() function should go.
                        A positive non-zero integer indicates a maximum
                        recursion depth, True indicates infinite recursion
                        depth, and anything else (0, False, None, etc.)
                        indicates that we shouldn't recurse.
                        (default True)

    """
    # Correct the input if path is a str.
    if type(paths) is str:
        # I've screwed up when instantiating a GramCounter by setting paths
        # to a str instead of a list. We can recover from that, of course.
        paths = (paths,)
    # Same correction for patterns value (if it's a str).
    if type(patterns) is str:
        patterns = (patterns,)
    # Finally, return only the valid paths from get_text_paths().
    return tuple(get_file_paths(paths, patterns=patterns, recursion_levels=recursion_levels, debug=debug)[0])


def get_files_in_path(path, extensions=(".txt",)):
    files = OrderedDict()
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            name, ext = os.path.splitext(filename)
            # Skip this file if its extension isn't one of the ones we're looking for.
            if (
                (extensions is not None or len(extensions) > 0)
                and ext not in extensions
            ):
                continue
            if name in files.keys():
                raise IOError("Attempting to add the same file to the data list a second time!")
            files[name] = file_path
    return files


def get_valid_path(path, relative_path_base=None, fallback_path=None):
    # Did we get a str?
    if type(path) is str:
        # Is this a relative path?
        if (
            not os.path.isabs(path) and
            type(relative_path_base) is str and
            os.path.isabs(relative_path_base)
        ):
            # Assume this relative path exists inside the corpus path (self.path).
            path = os.path.join(
                relative_path_base,
                path
            )
    # Did we get None, something that isn't a str (or None)? Then fall back.
    else:
        path = fallback_path
    # Is path still a str?
    if type(path) is str:
        # This call to os.path.abspath(), among other things, removes trailing
        # slashes from the path.
        path = os.path.abspath(path)
    return path
