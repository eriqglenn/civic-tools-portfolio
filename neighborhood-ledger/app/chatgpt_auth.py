"""App-owned ChatGPT OAuth for the local Windows Ledger. Never reads other apps' tokens."""
import base64
import hashlib
import html
import json
from pathlib import Path
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt

ISSUER = 'https://auth.openai.com'
RESOURCE = 'https://api.openai.com/v1'
SCOPES = 'openid profile email offline_access resource.invoke chatgpt.tokens.use.direct'

def opener():
    from ledger_ai import NoRedirect
    return urllib.request.build_opener(NoRedirect())

def remote_json(url, form=None, token=None):
    headers = {'Accept': 'application/json'}
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    if token: headers['Authorization'] = 'Bearer ' + token
    try:
        with opener().open(urllib.request.Request(url, data=data, headers=headers), timeout=20) as response:
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000: raise ValueError('OpenAI returned an oversized connection response.')
        value = json.loads(raw) if raw else {}
        if not isinstance(value, dict): raise ValueError('ChatGPT returned an unexpected connection response.')
        return value
    except urllib.error.HTTPError as error:
        if error.code in (400, 401): raise ValueError('ChatGPT could not authorize this connection. Sign in again; your account must support plan sharing.') from None
        if error.code == 429: raise ValueError('ChatGPT reports a usage limit. Check Manage usage, then retry.') from None
        raise ValueError('ChatGPT could not complete this connection. Check account access and try again.') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError('Could not reach ChatGPT. Check your connection or City network restrictions, then retry.') from None
    except (json.JSONDecodeError, UnicodeError): raise ValueError('ChatGPT returned an unreadable connection response.') from None

def discovery():
    value = remote_json(ISSUER + '/.well-known/openid-configuration')
    if value.get('issuer') != ISSUER: raise ValueError('ChatGPT identity configuration could not be verified.')
    for field in ('authorization_endpoint', 'token_endpoint', 'jwks_uri', 'revocation_endpoint'):
        p = urllib.parse.urlsplit(value.get(field, ''))
        if p.scheme != 'https' or p.netloc != 'auth.openai.com' or p.username or p.fragment:
            raise ValueError('ChatGPT identity endpoints could not be verified.')
    return value

def verify_identity(encoded, client, nonce=None, subject=None, metadata=None):
    try:
        metadata = metadata or discovery()
        header = jwt.get_unverified_header(encoded)
        if header.get('alg') not in ('RS256', 'ES256'): raise ValueError()
        keys = jwt.PyJWKSet.from_dict(remote_json(metadata['jwks_uri']))
        key = keys[header['kid']]
        claims = jwt.decode(encoded, key.key, algorithms=[header['alg']], audience=client,
                            issuer=ISSUER, leeway=5, options={'require': ['exp', 'iat', 'iss', 'aud', 'sub']})
        if not isinstance(claims['sub'], str) or not claims['sub']: raise ValueError()
        if nonce is not None and not secrets.compare_digest(str(claims.get('nonce', '')), nonce): raise ValueError()
        if subject is not None and claims['sub'] != subject: raise ValueError()
        return claims
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise ValueError('ChatGPT identity could not be verified. Please start sign-in again.') from None

class ChatGPTConnection:
    def __init__(self, root, activate=lambda: None):
        self.root = Path(root); self.path = self.root / 'chatgpt-connection.enc'
        self.lock = threading.RLock(); self.pending = None; self.phase = 'idle'; self.message = ''
        self.activate = activate

    def read(self):
        from ledger_ai import protect
        if not self.path.exists(): return {}
        try: return json.loads(protect(self.path.read_bytes(), True))
        except (OSError, ValueError):
            raise ValueError('This ChatGPT connection cannot be unlocked. Sign in again on this Windows account.') from None

    def write(self, value):
        from ledger_ai import protect
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp'); tmp.write_bytes(protect(json.dumps(value).encode()))
        tmp.replace(self.path)

    def host_id(self):
        from ledger_ai import protect
        path = self.root / 'chatgpt-host.enc'
        try: return protect(path.read_bytes(), True).decode()
        except (OSError, ValueError):
            value = 'urn:uuid:' + str(uuid.uuid4())
            self.root.mkdir(parents=True, exist_ok=True); path.write_bytes(protect(value.encode()))
            return value

    def status(self):
        with self.lock:
            try: c = self.read()
            except ValueError: c = {}
            return {'connected': bool(c.get('refresh_token')), 'ready': bool(c.get('refresh_token') and c.get('models')),
                    'account': c.get('email') or ('ChatGPT account' if c.get('sub') else ''),
                    'model': c.get('model', ''), 'models': c.get('models', []), 'phase': self.phase,
                    'message': self.message, 'welcomeNeeded': bool(c.get('refresh_token') and c.get('sub') not in c.get('welcomed_subjects', []))}

    def cancel(self):
        with self.lock:
            pending = self.pending; self.pending = None
            if pending:
                pending['timer'].cancel()
                self.message = 'Sign-in canceled. Choose Continue with ChatGPT whenever you are ready.'
                threading.Thread(target=lambda: (pending['server'].shutdown(), pending['server'].server_close()), daemon=True).start()
            self.phase = 'idle'

    def start(self, new_account=False):
        self.cancel()
        metadata = discovery()
        with self.lock:
            try: saved = {} if new_account else self.read()
            except ValueError: saved = {}
            owner = self
            class Callback(BaseHTTPRequestHandler):
                def log_message(self, *args): pass  # OAuth URLs contain one-time secrets.
                def do_GET(self):
                    parsed = urllib.parse.urlsplit(self.path)
                    if self.headers.get('Host') != '127.0.0.1:' + str(self.server.server_port) or parsed.path != '/auth/callback':
                        self.send_error(404); return
                    ok, message = owner.finish(urllib.parse.parse_qs(parsed.query, keep_blank_values=True))
                    page = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                            '<title>Neighborhood Ledger</title><h1>Neighborhood Ledger</h1><p>' + html.escape(message) + '</p>').encode()
                    self.send_response(200 if ok else 400); self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Cache-Control', 'no-store'); self.send_header('Referrer-Policy', 'no-referrer')
                    self.send_header('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'")
                    self.send_header('Content-Length', str(len(page))); self.end_headers(); self.wfile.write(page)
            server = ThreadingHTTPServer(('127.0.0.1', 0), Callback)
            verifier = secrets.token_urlsafe(48)
            redirect = f'http://127.0.0.1:{server.server_port}/auth/callback'
            pending = {'state': secrets.token_urlsafe(32), 'nonce': secrets.token_urlsafe(32), 'verifier': verifier,
                       'redirect': redirect, 'client': saved.get('client_id'), 'subject': saved.get('sub'),
                       'host': self.host_id(), 'server': server, 'metadata': metadata, 'deadline': time.monotonic()+300}
            def expire():
                with self.lock:
                    if self.pending is pending:
                        self.cancel(); self.phase = 'error'; self.message = 'Sign-in expired. Choose Continue with ChatGPT to try again.'
            pending['timer'] = threading.Timer(300, expire); pending['timer'].daemon = True
            self.pending = pending; self.phase = 'waiting'; self.message = 'Finish signing in in your browser, then return here.'
            params = {'client_id': pending['client'] or 'dynamic_agent_client', 'ext_agent_host_id': pending['host'],
                      'response_type': 'code', 'redirect_uri': redirect, 'scope': SCOPES, 'resource': RESOURCE,
                      'state': pending['state'], 'nonce': pending['nonce'], 'code_challenge_method': 'S256',
                      'code_challenge': base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')}
            if not pending['client']: params['agent_name_hint'] = 'Neighborhood Ledger MLS'
            url = metadata['authorization_endpoint'] + '?' + urllib.parse.urlencode(params)
            threading.Thread(target=server.serve_forever, daemon=True).start(); pending['timer'].start()
        webbrowser.open(url)
        return {'authorizationUrl': url, **self.status()}

    def finish(self, params):
        with self.lock:
            p = self.pending
            if not p or time.monotonic() > p['deadline'] or any(len(v) != 1 for v in params.values()) or not secrets.compare_digest(params.get('state', [''])[0], p['state']):
                return False, 'This sign-in attempt is invalid or expired. Return to Ledger and start again.'
            self.cancel()  # Consume the callback before any exchange; replay cannot replace credentials.
            try:
                if params.get('error'): raise ValueError('ChatGPT sign-in was not completed. You can try again in Ledger.')
                client = params.get('client_id', [p['client']])[0]
                if not client or client == 'dynamic_agent_client' or (p['client'] and client != p['client']):
                    raise ValueError('ChatGPT did not return the expected app registration. Start sign-in again.')
                code = params.get('code', [''])[0]
                if not code: raise ValueError('ChatGPT did not return an authorization code. Start sign-in again.')
                tokens = remote_json(p['metadata']['token_endpoint'], {'grant_type': 'authorization_code', 'client_id': client,
                          'code': code, 'code_verifier': p['verifier'], 'redirect_uri': p['redirect'], 'resource': RESOURCE})
                claims = verify_identity(tokens.get('id_token', ''), client, p['nonce'], p['subject'], p['metadata'])
                try: previous = self.read()
                except ValueError: previous = {}
                c = {'client_id': client, 'sub': claims['sub'], 'email': claims.get('email', ''), 'host_id': p['host'],
                     'welcomed_subjects': previous.get('welcomed_subjects', [])}
                self.merge_tokens(c, tokens, initial=True)
                self.write(c); self.phase = 'connected'; self.message = 'Signed in. Choose Test connection to check plan access.'
                try: self.load_models()
                except ValueError as error: self.message = str(error) + ' Choose Refresh models to retry.'
                self.activate()
                return True, 'You are signed in. Return to Neighborhood Ledger to test your connection. You can close this tab.'
            except ValueError as error:
                self.phase = 'error'; self.message = str(error); return False, self.message

    @staticmethod
    def merge_tokens(c, tokens, initial=False):
        if str(tokens.get('token_type', 'Bearer')).lower() != 'bearer':
            raise ValueError('ChatGPT returned an unsupported connection token.')
        scopes = tokens.get('scope', '' if initial else c.get('scope', ''))
        if not isinstance(scopes, str) or not {'resource.invoke', 'chatgpt.tokens.use.direct'} <= set(scopes.split()):
            raise ValueError('Your ChatGPT account did not grant plan sharing. Try another eligible account or use an API key.')
        if not tokens.get('access_token') or (initial and not tokens.get('refresh_token')):
            raise ValueError('ChatGPT did not provide a renewable connection. Sign in again.')
        try: lifetime = float(tokens['expires_in'])
        except (KeyError, TypeError, ValueError): raise ValueError('ChatGPT did not provide a valid session lifetime.') from None
        if not 0 < lifetime < 31_536_000: raise ValueError('ChatGPT returned an invalid session lifetime.')
        for key in ('access_token', 'refresh_token', 'id_token'):
            if tokens.get(key): c[key] = tokens[key]
        c.update(scope=scopes, expires_at=time.time()+lifetime)

    def credentials(self):
        with self.lock:
            c = self.read()
            if not c.get('refresh_token'): raise ValueError('Continue with ChatGPT in AI settings first.')
            if c.get('expires_at', 0) < time.time()+60:
                metadata = discovery()
                tokens = remote_json(metadata['token_endpoint'], {'grant_type': 'refresh_token', 'client_id': c['client_id'],
                                     'refresh_token': c['refresh_token'], 'resource': RESOURCE})
                if tokens.get('id_token'): verify_identity(tokens['id_token'], c['client_id'], subject=c['sub'], metadata=metadata)
                self.merge_tokens(c, tokens); self.write(c)
            return c['access_token'], c.get('model', '')

    def load_models(self):
        with self.lock:
            token, _ = self.credentials(); data = remote_json(RESOURCE+'/models', token=token)
            models = [{'slug': m['slug'], 'name': m.get('display_name') or m['slug']} for m in data.get('models', [])
                      if isinstance(m, dict) and m.get('visibility') == 'list' and isinstance(m.get('slug'), str)]
            if not models: raise ValueError('No eligible ChatGPT models were returned for this account.')
            c = self.read(); c['models'] = models
            if c.get('model') not in [m['slug'] for m in models]: c['model'] = models[0]['slug']
            self.write(c); self.message = 'Signed in. Choose Test connection to check plan access.'
            return self.status()

    def select_model(self, model):
        with self.lock:
            c = self.read()
            if model not in [m['slug'] for m in c.get('models', [])]: raise ValueError('Choose a model available to this ChatGPT account.')
            c['model'] = model; self.write(c)
            return self.status()

    def welcome(self):
        with self.lock:
            c = self.read()
            if c.get('sub'): c['welcomed_subjects'] = list(set(c.get('welcomed_subjects', [])+[c['sub']]))
            self.write(c)
        return self.status()

    def signout(self):
        with self.lock:
            self.cancel()
            try: c = self.read()
            except ValueError: c = {}
            message = 'Signed out of ChatGPT on this computer.'
            try:
                if c.get('refresh_token'):
                    metadata = discovery()
                    remote_json(metadata['revocation_endpoint'], {'token': c['refresh_token'], 'token_type_hint': 'refresh_token', 'client_id': c['client_id']})
            except ValueError:
                message += ' Remote disconnection could not be confirmed. Remove Ledger’s connection in ChatGPT settings.'
            self.write({k: c[k] for k in ('client_id', 'sub', 'email', 'host_id', 'welcomed_subjects') if k in c})
            self.message = message
            return self.status()

def request_chatgpt(token, payload, raw_response=False):
    from ledger_ai import response_text
    body = {k: v for k, v in payload.items() if k != 'max_output_tokens'}
    if isinstance(body.get('input'), str): body['input'] = [{'role': 'user', 'content': body['input']}]
    body.update(store=False, stream=True)
    req = urllib.request.Request(RESOURCE+'/responses', data=json.dumps(body).encode(),
          headers={'Authorization': 'Bearer '+token, 'Content-Type': 'application/json', 'Accept': 'text/event-stream'})
    completed_items = {}
    def event(lines):
        try: data = json.loads('\n'.join(lines))
        except ValueError: raise ValueError('ChatGPT returned an unreadable stream. Please retry.') from None
        kind = data.get('type')
        if kind == 'response.output_item.done':
            index, item = data.get('output_index'), data.get('item')
            if isinstance(index, int) and index >= 0 and isinstance(item, dict):
                completed_items[index] = item
        if kind == 'response.completed':
            result=data.get('response', {})
            # Some streams emit the finished items separately and end with an empty output list.
            if not result.get('output') and completed_items:
                result = {**result, 'output':[completed_items[i] for i in sorted(completed_items)]}
            if raw_response:
                if result.get('status')!='completed':raise ValueError('The ChatGPT response did not finish. Please retry.')
                return result,result.get('usage',{})
            return response_text(result)
        if kind in ('error', 'response.failed', 'response.incomplete'):
            error = data.get('error') or data.get('response', {}).get('error') or data
            if str(error.get('code', '')).startswith('subscription_sharing_'):
                raise ValueError('ChatGPT plan sharing is unavailable or has reached its limit. Check Manage usage in AI settings.')
            raise ValueError('The ChatGPT answer did not finish. Check plan access or try a shorter question.')
    try:
        with opener().open(req, timeout=65) as response:
            total = 0; lines = []; started = time.monotonic()
            while True:
                raw = response.readline(256001); total += len(raw)
                if total > 2_000_000 or len(raw) > 256000 or time.monotonic()-started > 90:
                    raise ValueError('The ChatGPT answer exceeded the local response limit. Ask a shorter question.')
                if not raw: break
                line = raw.decode('utf-8').rstrip('\r\n')
                if line.startswith('data:'): lines.append(line[5:].lstrip(' '))
                elif not line and lines:
                    result = event(lines); lines = []
                    if result is not None: return result
            if lines:
                result = event(lines)
                if result is not None: return result
        raise ValueError('The ChatGPT stream ended before the answer finished. Please retry.')
    except urllib.error.HTTPError as error:
        if error.code == 401: raise ValueError('ChatGPT did not accept this session. Sign in again in AI settings.') from None
        if error.code in (403, 429): raise ValueError('ChatGPT plan access is unavailable or limited. Check Manage usage in AI settings.') from None
        raise ValueError('ChatGPT could not accept this request. Try another available model or reconnect.') from None
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeError):
        raise ValueError('The ChatGPT connection was interrupted. Check your connection, then retry.') from None
