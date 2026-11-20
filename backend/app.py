"""
API de autenticação via LDAP.

Fluxo do login:
  1. A API se conecta ao LDAP com uma conta de serviço (bind administrativo)
     e procura o DN do usuário pelo uid informado.
  2. Tenta um novo bind usando o DN encontrado e a senha digitada.
     Se o LDAP aceitar, a senha está correta.
  3. Busca os grupos (groupOfNames) dos quais o usuário é membro.
  4. Emite um token JWT com uid, nome, e-mail e grupos.
As rotas protegidas exigem o cabeçalho  Authorization: Bearer <token>.
"""
import os
import logging
import datetime as dt
from functools import wraps

import jwt
from flask import Flask, jsonify, request, g
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPBindError, LDAPException
from ldap3.utils.conv import escape_filter_chars

LDAP_URL = os.getenv("LDAP_URL", "ldap://ldap:389")
LDAP_USERS_OU = os.getenv("LDAP_USERS_OU", "ou=usuarios,dc=uva,dc=local")
LDAP_GROUPS_OU = os.getenv("LDAP_GROUPS_OU", "ou=grupos,dc=uva,dc=local")
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN", "cn=admin,dc=uva,dc=local")
LDAP_BIND_PASSWORD = os.getenv("LDAP_BIND_PASSWORD", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
if len(JWT_SECRET) < 32:
    raise RuntimeError("Configure JWT_SECRET com pelo menos 32 caracteres antes de iniciar a API")
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
ldap_server = Server(LDAP_URL, get_info=ALL, connect_timeout=5)


def service_connection():
    """Conexão com a conta de serviço, usada apenas para buscas."""
    return Connection(ldap_server, LDAP_BIND_DN, LDAP_BIND_PASSWORD, auto_bind=True)


def find_user(conn, username):
    """Retorna a entrada LDAP do usuário ou None."""
    # escape_filter_chars impede LDAP injection (ex.: usuário "*")
    filtro = f"(&(objectClass=inetOrgPerson)(uid={escape_filter_chars(username)}))"
    conn.search(LDAP_USERS_OU, filtro, SUBTREE, attributes=["uid", "cn", "mail"])
    return conn.entries[0] if len(conn.entries) == 1 else None


def find_groups(conn, user_dn):
    filtro = f"(&(objectClass=groupOfNames)(member={escape_filter_chars(user_dn)}))"
    conn.search(LDAP_GROUPS_OU, filtro, SUBTREE, attributes=["cn"])
    return [str(e.cn) for e in conn.entries]


def authenticate(username, password):
    """Valida usuário e senha no LDAP. Retorna dict com dados ou None."""
    # Senha vazia faria um "unauthenticated bind", que o LDAP aceita: bloquear.
    if not username or not password:
        return None
    with service_connection() as conn:
        entry = find_user(conn, username)
        if entry is None:
            return None
        user_dn = entry.entry_dn
        try:
            # O próprio LDAP confere a senha: o bind só funciona se ela estiver certa
            Connection(ldap_server, user_dn, password, auto_bind=True).unbind()
        except LDAPBindError:
            return None
        return {
            "uid": str(entry.uid),
            "nome": str(entry.cn),
            "email": str(entry.mail) if entry.mail else "",
            "grupos": find_groups(conn, user_dn),
        }


def token_required(grupo=None):
    """Decorator: exige JWT válido e, opcionalmente, um grupo específico."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify(erro="Token ausente"), 401
            try:
                g.user = jwt.decode(auth[7:], JWT_SECRET, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return jsonify(erro="Token expirado"), 401
            except jwt.InvalidTokenError:
                return jsonify(erro="Token inválido"), 401
            if grupo and grupo not in g.user.get("grupos", []):
                return jsonify(erro=f"Acesso restrito ao grupo '{grupo}'"), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.get("/api/health")
def health():
    try:
        with service_connection():
            ldap_ok = True
    except LDAPException:
        ldap_ok = False
    return jsonify(status="ok", ldap="conectado" if ldap_ok else "indisponivel"), (200 if ldap_ok else 503)


@app.post("/api/login")
def login():
    dados = request.get_json(silent=True) or {}
    try:
        user = authenticate(dados.get("username", "").strip(), dados.get("password", ""))
    except LDAPException as e:
        app.logger.error("Erro LDAP: %s", e)
        return jsonify(erro="Servidor LDAP indisponível"), 503
    if user is None:
        app.logger.info("Login negado para %s", dados.get("username"))
        return jsonify(erro="Usuário ou senha inválidos"), 401

    agora = dt.datetime.now(dt.timezone.utc)
    payload = {**user, "sub": user["uid"], "iat": agora,
               "exp": agora + dt.timedelta(minutes=JWT_EXP_MINUTES)}
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    app.logger.info("Login OK para %s (grupos: %s)", user["uid"], user["grupos"])
    return jsonify(token=token, usuario=user)


@app.get("/api/me")
@token_required()
def me():
    return jsonify(usuario={k: g.user[k] for k in ("uid", "nome", "email", "grupos")})


@app.get("/api/admin")
@token_required(grupo="admins")
def admin_area():
    with service_connection() as conn:
        conn.search(LDAP_USERS_OU, "(objectClass=inetOrgPerson)", SUBTREE,
                    attributes=["uid", "cn", "mail"])
        usuarios = [{"uid": str(e.uid), "nome": str(e.cn), "email": str(e.mail)}
                    for e in conn.entries]
    return jsonify(mensagem=f"Bem-vindo à área administrativa, {g.user['nome']}!",
                   usuarios_no_diretorio=usuarios)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
