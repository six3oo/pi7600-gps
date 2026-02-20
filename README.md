# Pi7600: GPS-only SIM7600 client

[GitHub Repository](https://github.com/dazemc/pi7600)

## Overview

This submodule has been intentionally stripped down to one purpose: query and return
GNSS/GPS information from a Waveshare SIM7600 HAT using AT commands.

## Features

- **GPS Data**: Parse `AT+CGNSINF` into a clean JSON payload.
- **REST API**: Minimal FastAPI app exposing `GET /gps`.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
  - [Modem Status `/`](#modem-status-)
  - [Host Information `/info`](#host-information-info)
  - [SMS Management `/sms`](#sms-management-sms)
    - [Read SMS `GET /sms`](#read-sms-get-sms)
    - [Send SMS `POST /sms`](#send-sms-post-sms)
    - [Delete SMS `DELETE /sms/delete/{msg_idx}`](#delete-sms-delete-smsdelete-msg_idx)
  - [AT Command Interface `/at`](#at-command-interface-at)
  - [API Documentation `/docs` and `/redoc`](#api-documentation-docs-and-redoc)
- [Resources](#resources)
- [Contributing](#contributing)
- [License](#license)

## Installation

*Detailed installation instructions will be provided in the future once the project reaches a stable release.*

## Usage

To run the API:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

This starts the API server at `http://localhost:8000`.

## API Endpoints

### GPS `/gps`

- **Method**: `GET`
- **Description**: Queries `AT+CGNSINF` and returns parsed GNSS data.

Example:

```bash
curl http://localhost:8001/gps
```

### Health `/health`

```bash
curl http://localhost:8001/health
```

## Resources

- [SIM7600G-H 4G HAT Product Page](https://www.waveshare.com/wiki/SIM7600G-H_4G_HAT_(B))
- [SIM7600 AT Command Manual](https://www.waveshare.net/w/upload/6/68/SIM7500_SIM7600_Series_AT_Command_Manual_V2.00.pdf)

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request if you have suggestions or improvements.

## License

MIT license

---

*Note: This project is under active development, and documentation will be updated as features are added.*
