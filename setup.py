from setuptools import setup

setup(name='programaker-twitter-service',
      version='0.0.1',
      description='Programaker service to interact with Twitter.',
      author='kenkeiras',
      author_email='kenkeiras@codigoparallevar.com',
      license='Apache License 2.0',
      packages=['programaker_twitter_service'],
      scripts=['bin/programaker-twitter-service'],
      include_package_data=True,
      install_requires = [
          'python-twitter',
          'programaker_bridge',
          'xdg',
      ],
      zip_safe=False)
