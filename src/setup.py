from setuptools import setup, find_packages

setup(
    name='qisit',
    version='0.8.0_alpha',
    packages = find_packages(include=['qisit','qisit.*']),
    package_data={
        "qisit": ["LICENSE.md"],
    },
    url='https://github.com/mnowiasz/qisit',
    license='GPL 3.0',
    author='Mark Nowiasz',
    author_email='nowiasz+qisit@gmail.com',
    description='Test version',
    install_requires=[
        'babel >= 2.7.0',
        'sqlalchemy > 1.3.0',
        'pyqt5 >= 5.14',
        'pyqt5-sip'
    ],
    extras_require={
        'MySQL':  ['mysqlclient'],
        'PostgreSQL': ['psycopg2'],
        'Export': ['jinja2']
    },
    entry_points={
        'console_scripts':
            ['qisit=qisit.qt.main.qisitmain:qtmain'],
    },
    python_requires='>=3.6',
)
