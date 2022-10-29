# Notification-System
<!-- PROJECT LOGO -->
<div align="center"><br />
<p align="center" style="width: 100%">

<h2 align="center">Notification System</h2>
</p>
</div>


Notification System. Base from FastAPI

## I. Requirements:
    - Python >= 3.9
    - Redis
    - MongoDB

## II. Setup environment:
- How to set up environment:
    1. Install [redis](https://redis.io/docs/getting-started/installation/install-redis-on-linux/)
    2. Setup Python virtual environment:
        For Linux:
        ```sh
        cd notification_system
        virtualenv env -p python3
        source env/bin/activate
        pip install -r requirements.txt
        ```

        For Windows:
        ```powershell
        cd notification_system
        virtualenv env -p py3
        env/Scripts/activate
        pip install -r requirements_windows.txt
        ```

        Lưu ý: một số package trên linux và windows khác nhau nên chú ý file requirements tương ứng OS.

    4. In folder `notification_system`
        - Copy a content of file `.env.example` to `.env` file and config some parameters in it if necessary (`already configured`).
        - CHANGE `DEBUG=False` FOR PRODUCTION: This should be set to `False`.

    5. Run
        - For local development:
        ```sh
        uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
        ```

    6. Documentation
        - Swagger: `http://127.0.0.1:8000/docs/`
        - Redoc: `http://127.0.0.1:8000/redoc/`


## III. Note for developers:
- Install `pre-commit`:
    ```sh
    pre-commit install
    ```
