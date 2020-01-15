from setuptools import setup


setup(
    name='cldfbench_dryerorder',
    py_modules=['cldfbench_dryerorder'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'dryerorder=cldfbench_dryerorder:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
