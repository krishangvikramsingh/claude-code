import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from errors import (AccountLocked, DuplicateAccount, DuplicateReport, InvalidCollegeEmail,
                    InvalidCredentials, InvalidReview, NotAuthorised, NotFound, NotVerified, PlatformError)
from seed import build_sample_platform

STATUS = {
    DuplicateAccount: 409,
    InvalidCollegeEmail: 422,
    InvalidCredentials: 401,
    AccountLocked: 423,
    NotVerified: 403,
    NotAuthorised: 403,
    InvalidReview: 422,
    DuplicateReport: 409,
    NotFound: 404,
}

platform, sample_college = build_sample_platform()
sessions = {}


def rec_json(item):
    rec = item["rec"]
    return {"id": rec.rec_id, "name": rec.name, "category": rec.category.value, "rating": rec.average_rating,
            "price_level": rec.price_level, "distance_km": item["distance_km"]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def reply(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def payload(self):
        size = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(size) or b"{}")

    def current_user(self):
        token = self.headers.get("Authorization", "").replace("Bearer ", "")
        return sessions.get(token)

    def dispatch(self, method):
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if method == "GET" and parts == ["health"]:
                return self.reply(200, {"status": "ok"})
            if method == "GET" and parts == ["colleges"]:
                return self.reply(200, [{"id": c.college_id, "name": c.name} for c in platform.colleges.values()])
            if method == "POST" and parts == ["register"]:
                body = self.payload()
                user = platform.register(body["name"], body["email"], body["password"], body["college_id"])
                return self.reply(201, {"user_id": user.user_id, "verified": user.verified})
            if method == "POST" and parts == ["login"]:
                body = self.payload()
                user = platform.login(body["email"], body["password"])
                token = secrets.token_hex(16)
                sessions[token] = user.user_id
                return self.reply(200, {"token": token, "role": user.role})
            if method == "GET" and parts == ["search"]:
                outcome = platform.search(query["category"], float(query["lat"]), float(query["lon"]),
                                          float(query.get("radius", 5)))
                return self.reply(200, {"results": [rec_json(i) for i in outcome["results"]],
                                        "message": outcome["message"]})
            user_id = self.current_user()
            if user_id is None:
                return self.reply(401, {"error": "login required"})
            if method == "POST" and parts == ["reviews"]:
                body = self.payload()
                review = platform.submit_review(user_id, body["rec_id"], body["rating"], body.get("comment", ""))
                return self.reply(201, {"review_id": review.review_id, "status": review.status.value})
            if method == "POST" and len(parts) == 3 and parts[0] == "reviews" and parts[2] == "validate":
                body = self.payload()
                review = platform.validate_review(user_id, parts[1], bool(body.get("approve")))
                return self.reply(200, {"review_id": review.review_id, "status": review.status.value})
            return self.reply(404, {"error": "unknown route"})
        except PlatformError as exc:
            return self.reply(STATUS.get(type(exc), 400), {"error": type(exc).__name__})
        except (KeyError, ValueError, json.JSONDecodeError):
            return self.reply(400, {"error": "bad request"})

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")


def run(host="127.0.0.1", port=8000):
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run()
