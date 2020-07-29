from setuptools import setup

VERSION='1.0.2'

def get_requirements():
    with open('requirements.txt') as requirements:
        for req in requirements:
            req = req.strip()
            if req and not req.startswith('#') and not 'git+' in req:
                yield req

def get_dependency_links():
    with open('requirements.txt') as requirements:
        for req in requirements:
            req = req.strip()
            if req and not req.startswith('#') and 'git+' in req:
                yield req

def get_readme():
    with open('README.md') as readme:
            return readme.read()

setup(
    name='lastpass-python-cli',
    version=VERSION,
    description='Lastpass Python CLI',
    long_description=get_readme(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    keywords=['lastpass','cli'],
    author='Karthik Kumar Viswanathan',
    author_email='karthikkumar@gmail.com',
    url='https://github.com/guilt/lastpass-python-cli',
    license='MIT',
    install_requires=list(get_requirements()),
    dependency_links=list(get_dependency_links()),
    include_package_data=True,
    zip_safe=False,
    scripts=['scripts/lpass'],
)
