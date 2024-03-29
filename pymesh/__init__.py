"""
pymesh

A mesher for 3D chromatography columns.
"""

import pathlib

def git_version():
    """ Return version with local version identifier. """
    try:
        import git
    except ImportError:
        return None

    try: 
        path = pathlib.Path(__file__).parent.resolve()
        repo = git.Repo(path, search_parent_directories=True)
        repo.git.status()
        sha = repo.head.commit.hexsha
        sha = repo.git.rev_parse(sha, short=6)
        if repo.is_dirty():
            return '{sha}.dirty'.format(sha=sha)
        else:
            return sha
    except git.InvalidGitRepositoryError: 
        return None

__version__ = "0.1"
# If run locally, return the actual git version, otherwise, return the version installed.
__git_version__ = git_version()
__author__ = 'Jayghosh Rao'
__credits__ = 'FZJ/IBG-1/ModSim'

from .configHandler import ConfigHandler
from .log           import Logger
from .bead          import Bead
from .packedBed     import PackedBed
from .container     import Container
from .genericModel  import GenericModel
from .copyMeshModel import CopyMeshModel
from .column        import Column
