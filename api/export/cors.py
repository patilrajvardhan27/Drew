"""CORS for the signed Express export route.

The route is authorised by its signature alone and never reads cookies, so any origin may call it.
That avoids guessing which hosts Adobe serves add-ons from, and exposes the download name the
add-on uses as the imported document's title.
"""

from fastapi import Request, Response

PREFIX = "/api/express/"
HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Expose-Headers": "Content-Disposition",
}


async def express_cors(request: Request, call_next) -> Response:
    if not request.url.path.startswith(PREFIX):
        return await call_next(request)
    if request.method == "OPTIONS":
        response = Response(status_code=204, headers={**HEADERS, "Access-Control-Allow-Methods": "GET"})
    else:
        response = await call_next(request)
        response.headers.update(HEADERS)
    # Chrome asks before a public page calls a server on localhost, as in add-on development.
    if request.headers.get("access-control-request-private-network") == "true":
        response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response
