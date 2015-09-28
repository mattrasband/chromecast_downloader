from distutils.core import setup

setup(
    name='chromecast_downloader',
    version='1.0',
    author='Matt Rasband',
    author_email='matt.rasband@gmail.com',
    py_modules=['chromecast_downloader'],
    install_requires=['requests', 'appdirs'],
    license='MIT',
    keywords='chromecast background wallpaper',
    entry_points={
        'console_scripts': ['chromecast-downloader=chromecast_downloader:main']
    }
)