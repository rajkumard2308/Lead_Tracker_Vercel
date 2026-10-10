import os
import json
import mimetypes
from urllib.parse import urlparse, unquote

from google_sheet import (
    get_leads,
    add_lead,
    update_lead,
    delete_lead,
    add_leads_bulk,
)


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

INDEX_FILE = os.path.join(
    PROJECT_ROOT,
    "index.html"
)


def application(environ, start_response):
    """
    WSGI application for Vercel Python runtime.
    """

    method = environ.get(
        "REQUEST_METHOD",
        "GET"
    )

    raw_path = environ.get(
        "PATH_INFO",
        "/"
    )

    path = urlparse(raw_path).path

    if not path:
        path = "/"

    # Decode URL safely for static files
    decoded_path = unquote(path)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def response(status_code, payload):
        """
        JSON response helper.
        """

        body = json.dumps(
            payload,
            ensure_ascii=False,
            default=str
        ).encode("utf-8")

        status_text = {
            200: "OK",
            201: "Created",
            204: "No Content",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        }.get(
            status_code,
            "OK"
        )

        headers = [
            (
                "Content-Type",
                "application/json; charset=utf-8"
            ),
            (
                "Cache-Control",
                "no-store"
            ),
            (
                "Access-Control-Allow-Origin",
                "*"
            ),
            (
                "Access-Control-Allow-Methods",
                "GET,POST,PUT,DELETE,OPTIONS"
            ),
            (
                "Access-Control-Allow-Headers",
                "Content-Type"
            ),
        ]

        if status_code != 204:
            headers.append(
                (
                    "Content-Length",
                    str(len(body))
                )
            )

        start_response(
            f"{status_code} {status_text}",
            headers
        )

        return [body]

    def static_response(file_path):
        """
        Serve a frontend/static file.
        """

        try:
            with open(file_path, "rb") as file:
                body = file.read()

            content_type, _ = mimetypes.guess_type(
                file_path
            )

            if not content_type:
                content_type = "application/octet-stream"

            headers = [
                (
                    "Content-Type",
                    content_type
                ),
                (
                    "Content-Length",
                    str(len(body))
                ),
                (
                    "Cache-Control",
                    "no-cache"
                ),
            ]

            start_response(
                "200 OK",
                headers
            )

            return [body]

        except FileNotFoundError:

            body = b"File not found"

            start_response(
                "404 Not Found",
                [
                    (
                        "Content-Type",
                        "text/plain; charset=utf-8"
                    ),
                    (
                        "Content-Length",
                        str(len(body))
                    ),
                ]
            )

            return [body]

        except Exception as exc:

            body = str(exc).encode("utf-8")

            start_response(
                "500 Internal Server Error",
                [
                    (
                        "Content-Type",
                        "text/plain; charset=utf-8"
                    ),
                    (
                        "Content-Length",
                        str(len(body))
                    ),
                ]
            )

            return [body]

    def get_body():
        """
        Read and parse JSON request body.
        """

        try:
            length = int(
                environ.get(
                    "CONTENT_LENGTH"
                ) or 0
            )

        except ValueError:
            length = 0

        if length <= 0:
            return {}

        raw = environ["wsgi.input"].read(
            length
        )

        if not raw:
            return {}

        return json.loads(
            raw.decode("utf-8")
        )

    # ---------------------------------------------------------
    # CORS preflight
    # ---------------------------------------------------------

    if method == "OPTIONS":
        return response(
            204,
            {}
        )

    # ---------------------------------------------------------
    # FRONTEND
    #
    # Vercel dev is currently sending "/" to this Python
    # function. Therefore serve index.html directly here.
    # ---------------------------------------------------------

    if method == "GET":

        # -----------------------------------------------------
        # Root page
        # -----------------------------------------------------

        if path == "/":

            if not os.path.exists(INDEX_FILE):

                body = (
                    "index.html not found at: "
                    + INDEX_FILE
                ).encode("utf-8")

                start_response(
                    "500 Internal Server Error",
                    [
                        (
                            "Content-Type",
                            "text/plain; charset=utf-8"
                        ),
                        (
                            "Content-Length",
                            str(len(body))
                        ),
                    ]
                )

                return [body]

            return static_response(
                INDEX_FILE
            )

        # -----------------------------------------------------
        # Static frontend files
        #
        # Examples:
        # /assets/logo.png
        # /assets/style.css
        # /assets/app.js
        # /favicon.ico
        # -----------------------------------------------------

        if not path.startswith("/api/") and path != "/api":

            # Prevent path traversal such as:
            # /../../some-file
            safe_relative_path = os.path.normpath(
                decoded_path.lstrip("/")
            )

            if (
                safe_relative_path.startswith("..")
                or os.path.isabs(safe_relative_path)
            ):

                return response(
                    404,
                    {
                        "error": "Not found"
                    }
                )

            static_file = os.path.join(
                PROJECT_ROOT,
                safe_relative_path
            )

            # Make sure the resolved file remains inside
            # the project directory.
            project_root_real = os.path.realpath(
                PROJECT_ROOT
            )

            static_file_real = os.path.realpath(
                static_file
            )

            if not (
                static_file_real == project_root_real
                or static_file_real.startswith(
                    project_root_real + os.sep
                )
            ):

                return response(
                    404,
                    {
                        "error": "Not found"
                    }
                )

            if os.path.isfile(static_file_real):

                return static_response(
                    static_file_real
                )

    # ---------------------------------------------------------
    # GET API
    # ---------------------------------------------------------

    if method == "GET":

        try:

            if path in (
                "/api",
                "/api/leads"
            ):

                return response(
                    200,
                    {
                        "leads": get_leads()
                    }
                )

            return response(
                404,
                {
                    "error": "Not found"
                }
            )

        except Exception as exc:

            return response(
                500,
                {
                    "error": str(exc)
                }
            )

    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    if method == "POST":

        try:

            data = get_body()

            # ---------------------------------------------
            # Add single lead
            # ---------------------------------------------

            if path == "/api/leads":

                add_lead(
                    data
                )

                return response(
                    201,
                    {
                        "success": True
                    }
                )

            # ---------------------------------------------
            # Bulk add leads
            # ---------------------------------------------

            if path == "/api/leads/bulk":

                count = add_leads_bulk(
                    data.get(
                        "leads",
                        []
                    )
                )

                return response(
                    201,
                    {
                        "success": True,
                        "count": count,
                    }
                )

            return response(
                404,
                {
                    "error": "Not found"
                }
            )

        except ValueError as exc:

            return response(
                400,
                {
                    "error": str(exc)
                }
            )

        except Exception as exc:

            return response(
                500,
                {
                    "error": str(exc)
                }
            )

    # ---------------------------------------------------------
    # PUT
    # ---------------------------------------------------------

    if method == "PUT":

        try:

            prefix = "/api/leads/"

            if not path.startswith(prefix):

                return response(
                    404,
                    {
                        "error": "Not found"
                    }
                )

            row_text = path[
                len(prefix):
            ]

            row = int(
                row_text
            )

            data = get_body()

            update_lead(
                row,
                data
            )

            return response(
                200,
                {
                    "success": True
                }
            )

        except ValueError as exc:

            return response(
                400,
                {
                    "error": str(exc)
                }
            )

        except Exception as exc:

            return response(
                500,
                {
                    "error": str(exc)
                }
            )

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    if method == "DELETE":

        try:

            prefix = "/api/leads/"

            if not path.startswith(prefix):

                return response(
                    404,
                    {
                        "error": "Not found"
                    }
                )

            row_text = path[
                len(prefix):
            ]

            row = int(
                row_text
            )

            delete_lead(
                row
            )

            return response(
                200,
                {
                    "success": True
                }
            )

        except ValueError as exc:

            return response(
                400,
                {
                    "error": str(exc)
                }
            )

        except Exception as exc:

            return response(
                500,
                {
                    "error": str(exc)
                }
            )

    # ---------------------------------------------------------
    # Unsupported method
    # ---------------------------------------------------------

    return response(
        404,
        {
            "error": "Not found"
        }
    )