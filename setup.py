import setuptools
setuptools.setup(
     name='gfilter',  
     version='0.1',
     entry_points={
         'console_scripts': ['gfilter=gfilter.gfilter:main'],
     },
     author='Daniel Margolis',
     author_email='dan@af0.net.',
     description='Create Gmail filters in Python',
     long_description=open('README.md', 'r').read(),
     long_description_content_type='text/markdown',
     url='https://github.com/danmarg/pygfilter',
     packages=setuptools.find_packages(
         include=['gfilter', 'gfilter.*'],
     ),
     classifiers=[
         'Programming Language :: Python :: 3',
         'License :: OSI Approved :: MIT License',
         'Operating System :: OS Independent',
     ],
     install_requires=[
         'google-api-python-client',
         'google-auth-httplib2',
         'google-auth-oauthlib',
         'retry',
    ],
 )
