from setuptools import setup

setup(
    name='korector',
    version='1.0.6.3',
    author='ovin',
    description='Korean spell checker using Naver API (Linux/macOS/Windows)',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/movemin03/korector',
    packages=['korector'],
    py_modules=['cli'],
    install_requires=[
        'requests>=2.25.0',  # 모든 플랫폼 지원
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: Microsoft :: Windows :: Windows 11',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing :: Linguistic',
    ],
    entry_points={
        'console_scripts': [
            'korector=cli:main',
        ],
    },
)
