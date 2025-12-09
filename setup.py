from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='korector',
    version='1.0.4',
    author='movemin',
    author_email='your.email@example.com',
    description='A modern Python library for Korean spell checking powered by Naver',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/movemin/korector',
    project_urls={
        'Bug Reports': 'https://github.com/movemin/korector/issues',
        'Source': 'https://github.com/movemin/korector',
        'Documentation': 'https://github.com/movemin/korector#readme',
    },
    packages=find_packages(),
    py_modules=['korector'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'Natural Language :: Korean',
    ],
    python_requires='>=3.7',
    install_requires=[
        'requests>=2.25.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.950',
        ],
    },
    entry_points={
        'console_scripts': [
            'korector=korector:main',
        ],
    },
    keywords='korean spell checker naver hangul grammar 한글 맞춤법 검사',
    license='Apache License 2.0',
    zip_safe=False,
)
