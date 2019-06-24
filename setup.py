from setuptools import setup
setup(name='jupyter_importer',
    version='0.2',
    description='Enable to import .ipynb in jupyter',
    url='https://github.com/nilday/jupyter_importer',
    author='nilday',
    author_email='nilday.lee@gmail.com',
    license='Apache License 2',
    install_requires=[
      'notebook',
    ],
    py_modules=['jupyter_importer'],
    zip_safe=False)
