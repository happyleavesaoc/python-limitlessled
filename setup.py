from setuptools import setup

setup(
    name='limitlessled',
    version='1.1.3',
    description='Control LimitlessLED products.',
    url='https://github.com/happyleavesaoc/python-limitlessled/',
    license='MIT',
    author='happyleaves',
    author_email='happyleaves.tfr@gmail.com',
    packages=['limitlessled', 'limitlessled.group', 'limitlessled.group.commands'],
    install_requires=[],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ]
)
