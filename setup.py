from setuptools import setup

setup(name='plaza-twitter-service',
      version='0.0.1',
      description='Plaza service to interact with Twitter.',
      author='kenkeiras',
      author_email='kenkeiras@codigoparallevar.com',
      license='Apache License 2.0',
      packages=['plaza_twitter_service'],
      scripts=['bin/plaza-twitter-service'],
      include_package_data=True,
      install_requires = [
          'python-twitter',
          'plaza_service',
          'xdg',
      ],
      zip_safe=False)
