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
  - [GPS `GET /gps`](#gps-gps)
  - [Health `GET /health`](#health-health)
- [Environment](#environment)
- [Resources](#resources)
- [License](#license)

## Installation

This module is intentionally minimal.

- Python deps are defined in requirements.txt.

## Usage

To run the API:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

OR

```bash
./start.sh
```

Either command starts the API server at `http://localhost:8001`.

The API queries the SIM7600 over its AT-command serial port (commonly `/dev/ttyUSB2`).

## API Endpoints

### GPS `/gps`

- **Method**: `GET`
- **Description**: Queries `AT+CGNSINF` and returns parsed GNSS data.

Example:

```bash
curl http://localhost:8001/gps
```

Example response (fields may be `null` when there is no fix):

```json
{
  "ok": true,
  "fix": false,
  "lat": null,
  "lon": null,
  "altitude_m": null,
  "speed_kmh": null,
  "heading_deg": null,
  "utc_time": null,
  "satellites_in_view": null,
  "satellites_used": null,
  "run_status": 1,
  "fix_status": 0,
  "raw": "+CGNSINF: ...\nOK",
  "port": "/dev/ttyUSB2"
}
```

### Health `/health`

```bash
curl http://localhost:8001/health
```

## Environment

- `SIM7600_PORT`: Serial device path. If unset, the code auto-detects `/dev/ttyUSB*` and prefers common SIM7600 ports.
- `SIM7600_BAUD`: Baud rate (default `115200`).

Example:

```bash
SIM7600_PORT=/dev/ttyUSB2 SIM7600_BAUD=115200 uvicorn main:app --host 0.0.0.0 --port 8001
```

## Resources

- [SIM7600G-H 4G HAT Product Page](https://www.waveshare.com/wiki/SIM7600G-H_4G_HAT_(B))
- [SIM7600 AT Command Manual](https://www.waveshare.net/w/upload/6/68/SIM7500_SIM7600_Series_AT_Command_Manual_V2.00.pdf)

## Contributing

This fork is scoped to GPS-only behavior.

## License

MIT license

---

*Note: This module only provides GPS querying/parsing; all other modem/app features were removed.*
