# Seadu

Seadu is a command-line tool used for uploading and downloading files from specific Seafile library.

# Usage

1. Install

```bash
apt install -y pipx && pipx install seadu
```

2. Initial

You need to add the library API Token manually. The configuration file will be saved in `~/.seadu/config.json`.

```bash
seadu init -s YOUT_SERVER -t YOUR_TOKEN
```

The `-s` option should be entered as a full URL containing `http://`/`https://` without a slash at the end, e.g. https://cloud.seafile.com

3. Download/Upload

```bash
seadu down DIR_TO_STORE
seadu up DIR_TO_UPLOAD
```
