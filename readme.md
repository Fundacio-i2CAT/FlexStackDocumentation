# Read The Docs Webpage for FlexStack

This repo stores the readthedocs webpage for the FlexStack project.

## Install dependencies

It's recommended to use a python virtual environment to install the dependencies.

```bash
pip install -r requirements.txt
```

## Build the webpage

To build the webpage, run the following command:

```bash
make html
```

The webpage will be generated in the `build/html` directory.

## Serve the webpage

To serve the webpage, run the following command (in the `build/html` directory):

```bash
python -m http.server
```

