from html.parser import HTMLParser

import yaml


class AssetURLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and "src" in attributes:
            self.urls.append(attributes["src"])
        elif tag == "link" and "href" in attributes:
            self.urls.append(attributes["href"])
        elif tag == "img" and "src" in attributes:
            self.urls.append(attributes["src"])


def get_schema(client):
    response = client.get("/api/schema/")
    assert response.status_code == 200
    return yaml.safe_load(response.content)


def test_openapi_schema_is_public_and_valid(client):
    schema = get_schema(client)

    assert schema["openapi"].startswith("3.")
    assert isinstance(schema["paths"], dict)
    assert schema["info"]["title"] == "Task Manager API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"]


def test_schema_contains_versioned_task_operations(client):
    schema = get_schema(client)

    expected_paths = {
        "/api/v1/auth/token/",
        "/api/v1/auth/token/refresh/",
        "/api/v1/users/",
        "/api/v1/tasks/",
        "/api/v1/tasks/{id}/",
        "/api/v1/tasks/{task_id}/completion/",
        "/api/v1/tasks/{task_id}/comments/",
    }
    assert expected_paths <= set(schema["paths"])
    assert {"get", "post"} <= set(schema["paths"]["/api/v1/tasks/"])
    assert {"get", "put", "patch", "delete"} <= set(
        schema["paths"]["/api/v1/tasks/{id}/"]
    )


def test_task_schema_documents_author_and_completion_rules(client):
    schema = get_schema(client)
    schema_text = yaml.safe_dump(schema)

    assert "server-assigned" in schema_text
    assert "dedicated completion endpoint" in schema_text


def test_swagger_and_redoc_are_available(client):
    swagger = client.get("/api/docs/swagger/")
    redoc = client.get("/api/docs/redoc/")

    assert swagger.status_code == 200
    assert "swagger-ui" in swagger.content.decode().lower()
    assert redoc.status_code == 200
    assert "redoc" in redoc.content.decode().lower()


def test_docs_assets_are_local(client):
    parser = AssetURLParser()
    content = (
        client.get("/api/docs/swagger/").content.decode()
        + client.get("/api/docs/redoc/").content.decode()
    )
    parser.feed(content)

    external_assets = [
        url for url in parser.urls if url.startswith(("http://", "https://", "//"))
    ]
    assert external_assets == []
    assert any(
        url.startswith("/static/drf_spectacular_sidecar/") for url in parser.urls
    )
