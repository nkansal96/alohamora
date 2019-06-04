""" Define the setup instructions for this package """
import os
import setuptools


def version():
    """ Returns the version from blaze.__version__ """
    from blaze.__version__ import __version__ as blaze_version
    return blaze_version


def long_description():
    """ Returns the README as the long descripion for this package """
    with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
        return '\n' + f.read()


def requirements():
    """ Returns the requirements.txt file as the install_requires for this package """
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        return list(map(lambda line: line.strip(), f))


setuptools.setup(
    name='blaze',
    version=version(),
    description='Automated push policy generation via reinforcement learning',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    author='Nikhil Kansal',
    author_email='nkansal96@gmail.com',
    requires_python='>=3.6.0',
    url='https://github.com/nkansal96/blaze',
    packages=setuptools.find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
    install_requires=requirements(),
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: System :: Distributed Computing',
        'Typing :: Typed',
    ],
    scripts=[
        'bin/blaze',
    ],
)
