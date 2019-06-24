import io, os, sys, types
import zipfile
from functools import reduce
from IPython import get_ipython
from nbformat import read, reads
from IPython.core.interactiveshell import InteractiveShell


def find_notebook(fullname, path=None):
    """find a notebook, given its fully qualified name and an optional path

    This turns "foo.bar" into "foo/bar.ipynb"
    and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar
    does not exist.
    """
    name = fullname.rsplit('.', 1)[-1]
    if not path:
        path = ['']
    for d in path:
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            return nb_path, None
        if isfile_in_zip(d, name):
            return zip_and_module(d, name)
        # let import Notebook_Name find "Notebook Name.ipynb"
        nb_path = nb_path.replace("_", " ")
        if os.path.isfile(nb_path):
            return nb_path, None
        if isfile_in_zip(d, name):
            return zip_and_module(d, name)


def zip_and_module(path, name):
    paths = path.split(os.sep)

    if len(paths) > 1:
        if paths[0].endswith(":"):  # fix path problem on windows
            paths.insert(1, "/")
        elif paths[0] == "":  # fix absolute path problem on windows
            paths.insert(0, "/")

    paths.insert(0, "")

    def split_path(zippath, module):
        if zipfile.is_zipfile(module):
            zippath = module
            return zippath, ""
        return zippath, module

    def zippath_of_tuple(x):
        if type(x) == tuple:
            return x[0]
        else:
            return ""

    def module_of_tuple(x):
        if type(x) == tuple:
            return x[1]
        else:
            return x

    zipfile_name, module = reduce(lambda x, y: split_path(zippath_of_tuple(x), os.path.join(module_of_tuple(x), y)),
                                  paths)
    notebook__name = name + ".ipynb"
    module = notebook__name if module == "" else module + "/" + notebook__name
    return (zipfile_name, module)


def isfile_in_zip(path, name):
    zipfile_name, module = zip_and_module(path, name)
    if zipfile_name == "":
        return False
    module = module.replace(os.sep, '/')
    with zipfile.ZipFile(zipfile_name, "r") as zip:
        for f in zip.namelist():
            if f == module:
                return True
    return False


class NotebookLoader(object):
    """Module Loader for Jupyter Notebooks"""

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def load_module(self, fullname):
        """import a notebook as a module"""
        path, module = find_notebook(fullname, self.path)
        is_zip = True if module else False
        if module != None:
            module = module.replace(os.sep, '/')
        print("importing Jupyter notebook from {}{}".format(path, os.sep + module if is_zip else ""))

        # load the notebook object
        if not is_zip:
            with io.open(path, 'r', encoding='utf-8') as f:
                nb = read(f, 4)
        else:
            with zipfile.ZipFile(path, "r") as zip:
                f = zip.read(module)
                nb = reads(f.decode("utf-8"), 4)

        path = path + "/" + module if is_zip else path
        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = types.ModuleType(fullname)
        mod.__file__ = path
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython
        sys.modules[fullname] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            for cell in nb.cells:
                if cell.cell_type == 'code':
                    # transform the input to executable Python
                    code = self.shell.input_transformer_manager.transform_cell(cell.source)
                    # run the code in themodule
                    exec(code, mod.__dict__)
        finally:
            self.shell.user_ns = save_user_ns
        return mod


class NotebookFinder(object):
    """Module finder that locates Jupyter Notebooks"""

    def __init__(self):
        self.loaders = {}

    def find_module(self, fullname, path=None):
        if path == None:
            path = sys.path
        nb_path = find_notebook(fullname, path)
        if not nb_path:
            return

        key = path
        if path:
            # lists aren't hashable
            key = os.path.sep.join(path)

        if key not in self.loaders:
            self.loaders[key] = NotebookLoader(path)
        return self.loaders[key]


sys.meta_path.append(NotebookFinder())
