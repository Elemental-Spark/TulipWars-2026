import json
import tulip

IS_WEB = tulip.board() in ("WEB", "AMYBOARD_WEB")

if IS_WEB:
    import js
    requests = None
else:
    try:
        import tuliprequests as requests
    except Exception:
        try:
            import requests
        except Exception:
            requests = None


class NetworkError(Exception):
    pass


class Client:
    def __init__(self, server_url, device_id, callsign, version):
        self.server_url = server_url
        self.device_id = device_id
        self.callsign = callsign
        self.version = version
        self.async_mode = IS_WEB

    def configured(self):
        return self.server_url.startswith("http") and "YOURDOMAIN" not in self.server_url

    def _body(self, action, payload=None):
        body = {
            "action": action,
            "device_id": self.device_id,
            "callsign": self.callsign,
            "version": self.version,
        }
        if payload:
            for key in payload:
                body[key] = payload[key]
        return body

    def _validate(self, data):
        if not isinstance(data, dict):
            raise NetworkError("Relay returned invalid JSON")
        if not data.get("ok", False):
            raise NetworkError(data.get("error", "Server rejected request"))
        return data

    def _post_sync(self, action, payload=None):
        if requests is None:
            raise NetworkError("No HTTP requests module is available")
        if not self.configured():
            raise NetworkError("Configure the TulipWars relay URL")
        try:
            response = requests.post(self.server_url, json=self._body(action, payload))
            status = getattr(response, "status_code", 200)
            if status < 200 or status >= 300:
                raise NetworkError("Server returned HTTP %d" % status)
            return self._validate(response.json())
        except NetworkError:
            raise
        except Exception as exc:
            raise NetworkError("Connection failed: %s" % exc)

    def _post_web(self, action, payload=None, done=None, fail=None):
        if not self.configured():
            error = NetworkError("Configure the TulipWars relay URL")
            if fail is not None:
                fail(error)
                return None
            raise error

        body = json.dumps(self._body(action, payload))
        options = js.JSON.parse(json.dumps({
            "method": "POST",
            "headers": {"content-type": "application/json"},
            "body": body,
        }))

        def decoded(text):
            try:
                data = self._validate(json.loads(str(text)))
                if done is not None:
                    done(data)
                return data
            except Exception as exc:
                return failed(exc)

        def failed(exc):
            error = exc if isinstance(exc, NetworkError) else NetworkError("Connection failed: %s" % exc)
            if fail is not None:
                fail(error)
                return None
            print(error)
            return None

        return js.fetch(self.server_url, options).then(
            lambda response: response.text()
        ).then(decoded).catch(failed)

    def _request(self, action, payload=None, done=None, fail=None):
        if self.async_mode:
            return self._post_web(action, payload, done, fail)
        try:
            data = self._post_sync(action, payload)
            if done is not None:
                done(data)
            return data
        except Exception as exc:
            if fail is not None:
                fail(exc)
                return None
            raise

    def hello(self, done=None, fail=None):
        return self._request("hello", done=done, fail=fail)

    def status(self, done=None, fail=None):
        return self._request("status", done=done, fail=fail)

    def heartbeat(self, done=None, fail=None):
        return self._request("heartbeat", done=done, fail=fail)

    def travel(self, system_id, done=None, fail=None):
        return self._request("travel", {"destination": system_id}, done, fail)

    def market(self, done=None, fail=None):
        return self._request("market", done=done, fail=fail)

    def trade(self, commodity, side, quantity=1, done=None, fail=None):
        return self._request("trade", {
            "commodity": commodity,
            "side": side,
            "quantity": quantity,
        }, done, fail)

    def scan(self, done=None, fail=None):
        return self._request("scan", done=done, fail=fail)

    def combat(self, command, done=None, fail=None):
        return self._request("combat", {"command": command}, done, fail)

    def chat_list(self, done=None, fail=None):
        return self._request("chat_list", done=done, fail=fail)

    def chat_post(self, message, done=None, fail=None):
        return self._request("chat_post", {"message": message}, done, fail)
