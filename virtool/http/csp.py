import secrets
import aiohttp.web

CSP_CONNECT_SRC = "connect-src 'self' sentry.io"

CSP_DEFAULT_SRC = "default-src 'self'"

CSP_FONT_SRC = "font-src 'self' fonts.google.com use.fontawesome.com data:"

CSP_IMG_SRC = "img-src 'self' data:"


def generate_csp_header(nonce: str) -> str:
    """
    Put all of the CSP parts together to make a value for the Content-Security-Policy header.

    :param nonce: a nonce to add to the policy where appropriate
    :return: CSP policy value

    """
    return "; ".join([
        CSP_CONNECT_SRC,
        CSP_DEFAULT_SRC,
        CSP_FONT_SRC,
        CSP_IMG_SRC,
        generate_csp_script_src(nonce),
        generate_csp_style_src(nonce)
    ])


def generate_csp_script_src(nonce: str) -> str:
    """
    Generate script-src policy given a nonce.

    :param nonce: a nonce to add to the policy
    :return: script-src policy

    """
    return f"script-src 'self' 'nonce-{nonce}' use.fontawesome.com"


def generate_csp_style_src(nonce):
    """
    Generate style-src policy given a nonce.

    :param nonce: a nonce to add to the policy
    :return: style-src policy

    """
    return f"style-src 'self' 'nonce-{nonce}' use.fontawesome.com;"


@aiohttp.web.middleware
async def middleware(req: aiohttp.web.Request, handler):
    # Allow the nonce to be accessed from request handlers and signals. The index handler will add the nonce to the
    # index.html template.
    req["nonce"] = secrets.token_hex(20)
    return await handler(req)


async def on_prepare(req: aiohttp.web.Request, resp: aiohttp.web.Response):
    """
    Signal handler for generating CSP header and adding to response headers before the response is prepared. Accesses
    nonce generated in middleware and attached to request object.

    See https://aiohttp.readthedocs.io/en/stable/web_advanced.html#signals.

    :param req: the request object
    :param resp: the response object

    """
    nonce = req["nonce"]

    resp.headers["Content-Security-Policy"] = generate_csp_header(nonce)
    resp.headers["X-Virtool-Version"] = req.app["version"]
