from setuptools import setup

setup(
    name='bubbles',
    version='0.1.0',
    packages=['bubbles'],
    install_requires=[
          'bottle',
          'paste'
    ],
    url='',
    license='',
    author='',
    author_email='',
    description='',
    package_data={
        'bubbles': ['root/*', 'root/js/*']
    }
)
