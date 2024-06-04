# macbak
iCloud backup via a Mac, with optional source control


## Introduction

macbak is a collection of tools for providing an independent backup and
optional source control for Apple iCloud based resources. These work by
converting each resource to HTML and copying it to your Mac for both
safekeeping and as a way to allow line-based source control such as git if
desired. The icdrivebak tool doesn't convert but forces all iCloud Drive files
to be copied to the Mac. Together these allow normal Mac backup of these files.

Tools:

- notes2html — Back up Apple Notes to HTML files
- icdrivebak — Force all iCloud Drive files to be downloaded, for backup


## Getting Started

To install, first clone the repository:

```
git clone https://github.com/forbes3100/macbak.git
cd macbak
```

Then install dependencies:

```
pip3 install coverage pyemoji pillow_heif ui
```

## Running the tests

The following command should run all tests, ending with "OK".

```
./test_msg2html.py
```

## Usage

### notes2html

Notes backup is done whenever macbak is scheduled to run.

It will create the folder notes_icloud_bak in Documents if it doesn't exist, and write each note to a .html file there in subfolders matching the folder hierarchy in Notes. The file names have spaces changed to underscores to ease use with Unix.

When run again only updated notes will be written.


### icdrivebak

The following command should start the iCloud download of any files that have
yet to be downloaded to this Mac, listing those files. The files are stored
locally in ~/Library/Mobile Documents, allowing Time Machine, etc. to back
them up.

```
./icdrivebak.py
```


## Contributing

Please read [CONTRIBUTING.md](https://github.com/forbes3100/macbak.git/blob/master/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

* **Scott Forbes** - *Initial work* - [forbes3100](https://github.com/forbes3100)

See also the list of [contributors](https://github.com/forbes3100/macbak.git/graphs/contributors) who participated in this project.

## License

This project is licensed under the GNU General Public License.
