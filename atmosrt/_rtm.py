"""
    Copyright (c) 2012 Philip Schliehauf (uniphil@gmail.com) and the
    Queen's University Applied Sustainability Centre
    
    This project is hosted on github; for up-to-date code and contacts:
    https://github.com/Queens-Applied-Sustainability/PyRTM
    
    This file is part of PyRTM.

    PyRTM is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PyRTM is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PyRTM.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import pickle
import re
import shutil
import subprocess
import tempfile

from atmosrt import settings


class RTMError(Exception): pass


MAX_FILE_CHARS = 42
CACHE_DIR = 'cached'
PRIMARY = ['description']
SECONDARY = ['year', 'month', 'day']

_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, 'data', path)


def _vars_to_file(vars):
    """Return a safe string to be used as a file or directory name"""
    clean_vars = [re.sub('[^a-zA-Z0-9_:-]', '.', str(v)) for v in vars]
    clean_string = '-'.join(clean_vars)
    if clean_string.startswith('.'):
        clean_string = 'c' + clean_string
    if len(clean_string) > MAX_FILE_CHARS:
        # name was too long; use hash instead hash instead.
        return str(clean_string.__hash__())
    return clean_string


class Model():
    """The parent of what you probably need to use"""

    def __init__(self, userconfig=None, target='.', cleanup=True, **kwargs):
        required = ['description']
        self.config = {k: v for k, v in settings.defaults.items() if k in required}
        if userconfig:
            self.config.update(userconfig)
        self.config.update(kwargs)

        self.target = target
        self.cleanup = cleanup

    def __hash__(self):
        return hash(str(self.config) + str(self.__class__))

class Working(object):
    """work with the executables"""

    def __init__(self, model):

        # set up the directory variables
        primary = _vars_to_file(model.config[v] for v in PRIMARY)
        secondary = _vars_to_file(getattr(model.config['time'], v) for v in SECONDARY) if model.config.get('time') else 'notime'
        rundir = _vars_to_file([str(hash(model))])

        self.cleanup = model.cleanup
        self.cache = ~model.cleanup

        if self.cleanup:
            path = os.path.join(model.target, "-".join([primary, secondary, rundir]))
        else:
            path = os.path.join(model.target, primary, secondary, rundir)

        try:
            state = model._working_state[hash(model)]
        except AttributeError:
            model._workings_state = {}
        except KeyError:
            pass
        finally:
            state = {'dir_created': False}

        if not state['dir_created']:
            try:
                os.makedirs(path)
            except OSError as err:
                if err.errno != 17:
                    raise

            state['dir_created'] = True

        self.model = model
        self.path = path
        self.state = state

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        """save state back to model"""

        if self.cleanup:
            for f in os.listdir(self.path):
                if f[0] != ".":
                    os.unlink(os.path.join(self.path, f))
            os.rmdir(self.path)

        # try:
        #     self.model._workings_state[hash(self.model)].update(self.state)
        # except KeyError:
        #     self.model._workings_state[hash(self.model)] = self.state

    def __str__(self):
        return "<Working: %s>" % self.path

    def link(self, resources, path=""):
        """link some stuff in"""
        if type(resources) == str:
            resources = [resources]
        try:
            for resource in resources:
                os.symlink(os.path.join(path, resource), os.path.join(self.path, resource))
        except OSError as err:
            if err.errno != 17:
                raise

    def write(self, file_name, content):
        if file_name in self.state.get('writes', []):
            return
        else:
            file_path = os.path.join(self.path, file_name)
            with open(file_path, 'w') as to_write:
                to_write.write(content)

        if not self.state.get('writes'):
            self.state['writes'] = [file_name]
        else:
            self.state['writes'].append(file_name)

    def run(self, cmd, outfile, errfile=None):

        try:
            # first try to get the local cache
            run_out = self.state['outfile'][cmd]
        except KeyError:
            self.state['outfile'] = {}

        if self.cache:
            # no local cache, check for a pickle
            safe_cmd = _vars_to_file([cmd])
            errfile = errfile or 'err-%s' % outfile
            picklename = 'run %s.pickle' % safe_cmd
            picklepath = os.path.join(self.path, picklename)

            try:
                with open(picklepath, 'rb') as pfile:
                    run_out = pickle.load(pfile)
                self.state['outfile'][cmd] = run_out
                return run_out
            except IOError:
                pass

        # no pickle, so now actually run the command
        cmd += ' 2> %s' % errfile
        p = subprocess.Popen(cmd, cwd=self.path, shell=True)
        p.wait()
        with open(os.path.join(self.path, errfile)) as errfile:
            err = errfile.read()

        run_out = [p.returncode, err, self.model]
        self.state['outfile'][cmd] = run_out

        if self.cache:
            with open(picklepath, 'wb') as cache_pickle:
                pickle.dump(run_out, cache_pickle)

        return run_out

    def get(self, file_name, mode='r'):
        """all these files should be closed before finishing with Working"""
        return open(os.path.join(self.path, file_name), mode, encoding='latin_1')

