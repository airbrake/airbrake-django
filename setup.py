from setuptools import setup, find_packages


setup(
    name='django-airbrake',
    version='0.0.3',
    description='A Django app for submitting exceptions to Airbrake.io.',
    long_description='',
    keywords='django, airbrake',
    author='Joseph C. Stump',
    author_email='joe@stu.mp',
    url='https://github.com/joestump/django-airbrake',
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    install_requires=['decorator', 'lxml', 'six'],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Environment :: Web Environment",
    ]
)
