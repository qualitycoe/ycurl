# ycurl

A curl-like Python utility that performs HTTP requests based on a YAML file.

## Features

- Supports GET, POST, PUT, DELETE, etc.
- Custom headers, body (JSON or raw)
- Query parameters
- Auth (Basic, Bearer)
- SSL/TLS certs with `cert`, `key`, `verify`
- Timeout and custom CA bundles

## Usage

```bash
python cli.py request.yaml
