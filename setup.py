from setuptools import setup, find_packages

setup(
    name='fiteanalytics',
    description='FinX API SDK',
    version='0.0.3',
    author='Fite Analytics LLC',
    author_email='info@fiteanalytics.com',
    classifiers=['License :: OSI Approved :: GNU Affero General Public License v3',],
    license='APGL3',
    packages=find_packages(exclude=('*.tests',)),
    url='https://github.com/FiteAnalytics/sdk',
    install_requires=[
        'PyYAML',
        'python-dotenv',
        'aiohttp',
    ],
    # include_package_data is needed to reference MANIFEST.in
    include_package_data=True,
)