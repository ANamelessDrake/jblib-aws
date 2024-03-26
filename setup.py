import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='jblibaws',
                version='1.2.72',
                description='JustBard\'s Python based AWS Utilities',
                long_description=long_description,
                long_description_content_type="text/markdown",
                author='Justin Bard',
                author_email='JustinBard@gmail.com',
                url='https://justbardtech.com',
                packages=setuptools.find_packages(),
                classifiers=[
                    "Programming Language :: Python :: 3",
                    "License :: OSI Approved :: MIT License",
                    "Operating System :: POSIX :: Linux",
                ],
                )
