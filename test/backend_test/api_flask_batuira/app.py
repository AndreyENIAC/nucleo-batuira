from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from database import init_app as init_database
from errors import register_error_handlers
from responses import success

load_dotenv()

jwt = JWTManager()


def create_app(config_object: type[Config] = Config, config_overrides: dict | None = None):
    app = Flask(__name__)
    app.config.from_object(config_object)
    if config_overrides:
        app.config.update(config_overrides)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    configured_origins = app.config["CORS_ORIGINS"]
    if isinstance(configured_origins, str) and configured_origins != "*":
        configured_origins = [item.strip() for item in configured_origins.split(",") if item.strip()]

    CORS(
        app,
        resources={r"/api/*": {"origins": configured_origins}},
        supports_credentials=False,
    )
    jwt.init_app(app)
    init_database(app)
    register_error_handlers(app)

    from routes.auth import bp as auth_bp
    from routes.usuarios import bp as usuarios_bp
    from routes.acolhidos import bp as acolhidos_bp
    from routes.clinico import bp as clinico_bp
    from routes.planos import bp as planos_bp
    from routes.documentos import bp as documentos_bp
    from routes.financeiro import bp as financeiro_bp
    from routes.organizacao import bp as organizacao_bp
    from routes.dashboard import bp as dashboard_bp

    for blueprint in (
        auth_bp,
        usuarios_bp,
        acolhidos_bp,
        clinico_bp,
        planos_bp,
        documentos_bp,
        financeiro_bp,
        organizacao_bp,
        dashboard_bp,
    ):
        app.register_blueprint(blueprint, url_prefix="/api")

    @app.get("/")
    def home():
        return success(
            {
                "aplicacao": "API Núcleo Batuíra",
                "versao": "1.0.0",
                "documentacao": "/api/rotas",
            },
            message="API funcionando.",
        )

    @app.get("/api/health")
    def health():
        return success({"status": "ok"})

    @app.get("/api/rotas")
    def list_routes():
        routes = []
        for rule in sorted(app.url_map.iter_rules(), key=lambda item: item.rule):
            if rule.rule.startswith("/api"):
                methods = sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"})
                routes.append({"rota": rule.rule, "metodos": methods})
        return success(routes)

    @jwt.unauthorized_loader
    def missing_token(reason: str):
        from responses import error

        return error("Token de acesso não informado.", status=401, details=reason)

    @jwt.invalid_token_loader
    def invalid_token(reason: str):
        from responses import error

        return error("Token de acesso inválido.", status=401, details=reason)

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        from responses import error

        return error("Sua sessão expirou. Entre novamente.", status=401)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
