# InPostReturnLabel

Very simple web-app to generate courier-sized labels with QR code for InPost returns (10-digit codes, usually from Allegro).

*Obviously, this is not affiliated with neither InPost nor Allegro and only exists because I'm too lazy to write codes down by hand and to get my phone to open parcel locker from the app*.

The concept is to input 10-digit code and program sends QR and code itself to label printer loaded with courier-sized labels (approx 100x150mm).

## Current limitations

- For printing, CLI assumes there's `lpr` on UNIX system. This should be handled better.
- Label template relies on Monaco font, which is not bundled. Instead, the default option is to point to macOS `/System/Library/Fonts/Monaco.ttf` and user can override that. If a font can't be bundled, there should be a discovery process or some local config file.


## What's there - work in progress

### CLI

Simple CLI to send to local printer using `lpr` or open file if no printer is provided.

#### Installation

[![PyPI: InPostReturnLabel](https://img.shields.io/pypi/v/InPostReturnLabel?style=flat-square&label=PyPI%3A%20InPostReturnLabel)](https://pypi.org/project/InPostReturnLabel/)

```bash
pipx install InPostReturnLabel
```

#### Usage

Help:

```
❯ InPostReturnLabel --help
Usage: InPostReturnLabel [OPTIONS] CODE

  InPostReturnLabel

  CODE is InPost return label code, 10 digits, e.g. 1234567890

Options:
  --version           Show the version and exit.
  -p, --printer TEXT  Local CUPS printer name; if ommited, then file will be
                      opened
  -f, --font TEXT     Path to font file, default:
                      /System/Library/Fonts/Monaco.ttf
  --help              Show this message and exit.
```

Example:

```
❯ InPostReturnLabel -f /System/Library/Fonts/Monaco.ttf -p intermec 1234567890
Label generated and stored at /var/folders/y0/xhrlswfd40gbzh5m50cbp1fxr3p32g/T/tmpi9nb7pts.png
Sending label to intermec
```

### Simple web-app - TBD

The goal is to load it on home Docker/k8s and start printing over network.

## Technical background

InPost parcel lockers accept returns by entering 10-digit code - either from keypad on device or by scanning QR code. The only tricky bit here is that parcel lockers can only read *numeric mode* and most common QR generators insist on generating them in alphanumeric mode, even when only digits 0-9 are provided.

## Example label

![](./example.png)
