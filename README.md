# flin-shopify-analytics-mcp

Read-only MCP server for Shopify analytics.

Der Server ist dafür gedacht, Shopify-Shop-Daten in Claude oder anderen MCP-Clients lesend abzufragen, zum Beispiel:

- Welche Kunden haben bestellt?
- Welche Produkte wurden gekauft?
- Wie viele Einheiten wurden gekauft?
- Wie viel Umsatz hat ein Kunde erzeugt?

## Was dieser MCP kann

Der Server stellt diese Tools bereit:

- Basisdaten:
- `shopify_list_orders`
- `shopify_list_customers`
- `shopify_list_products`
- `shopify_customer_purchase_summary`
- `shopify_sales_by_customer_product`

- Reporting Core (`v2`, auf `main`):
- `shopify_sales_overview`
- `shopify_sales_timeseries`
- `shopify_top_products`
- `shopify_top_customers`
- `shopify_discount_analysis`

- Retention / CRM Health (`v3`, auf `main`):
- `shopify_retention_overview`
- `shopify_repeat_purchase_windows`
- `shopify_time_to_second_order`
- `shopify_inactive_customer_summary`

Write-Operationen sind nicht erlaubt. GraphQL-Mutationen werden blockiert.

## Wichtig: Ohne Shopify-App funktioniert dieser MCP nicht

Du brauchst für den Ziel-Shop immer eine installierte Shopify-App mit Admin-API-Rechten.

Je nach App-Typ bekommst du unterschiedliche Credentials:

- Neue Apps ab 2026: `Client ID` + `Client Secret`
- Bestehende Legacy-Custom-Apps: `Admin API access token` (`shpat_...`)

Ohne installierte App und passende Scopes kann der MCP keine Orders, Kunden oder Produkte lesen.

## Voraussetzungen

- Python 3.10+
- `uv` oder `uvx`
- Zugriff auf den Shopify-Store
- Berechtigung, eine App für den Store zu erstellen und zu installieren

## Shopify-App erstellen

### Empfohlen: Dev Dashboard App mit Client Credentials

Das ist der richtige Weg für neue Shopify-Apps.

1. Öffne den Shopify Dev Dashboard Bereich für deine App.
2. Erstelle eine App für den Ziel-Store.
3. Konfiguriere die Admin-API-Scopes.
4. Release die App-Version mit diesen Scopes.
5. Installiere die App auf dem Store.
6. Öffne in der App `Settings` und kopiere:
   - `Client ID`
   - `Client secret`

Für diesen MCP brauchst du mindestens diese Scopes:

- `read_products`
- `read_customers`
- `read_orders`

Optional:

- `read_all_orders`

`read_all_orders` ist sinnvoll, wenn du nicht nur die normalen Standard-Zeiträume von Shopify auslesen willst.
Für `v3` Retention-KPIs ist `read_all_orders` faktisch empfohlen, weil Wiederkauf- und Inaktivitätskennzahlen sonst auf unvollständiger Historie basieren können.

### Legacy: Bestehende Custom App im Shopify Admin

Nur für bereits existierende Admin-Custom-Apps.

1. Öffne die bestehende Custom App im Shopify Admin.
2. Stelle sicher, dass die App installiert ist.
3. Prüfe die Admin-API-Scopes.
4. Kopiere den `Admin API access token`.

Auch hier brauchst du mindestens:

- `read_products`
- `read_customers`
- `read_orders`

## Welche Credentials du eintragen musst

### Option A: Dev Dashboard App

Verwende diese Variablen:

```bash
SHOPIFY_STORE_DOMAIN="your-store.myshopify.com"
SHOPIFY_CLIENT_ID="your_client_id"
SHOPIFY_CLIENT_SECRET="your_client_secret"
SHOPIFY_API_VERSION="2026-04"
```

Der MCP holt das Access Token automatisch über den Client-Credentials-Flow und erneuert es selbst.

### Option B: Legacy Custom App

Verwende diese Variablen:

```bash
SHOPIFY_STORE_DOMAIN="your-store.myshopify.com"
SHOPIFY_ADMIN_ACCESS_TOKEN="shpat_xxx"
SHOPIFY_API_VERSION="2026-04"
```

Wenn `SHOPIFY_ADMIN_ACCESS_TOKEN` gesetzt ist, verwendet der MCP den statischen Token-Modus.

## Claude Desktop Konfiguration

### Variante 1: Über PyPI mit `uvx`

Die Beispiele unten sind auf die letzte veröffentlichte PyPI-Version gepinnt. `main` kann bereits zusätzliche, noch nicht veröffentlichte Tools enthalten.

```json
{
  "mcpServers": {
    "flin-shopify-analytics-mcp": {
      "command": "uvx",
      "args": [
        "--refresh",
        "-q",
        "flin-shopify-analytics-mcp@0.2.6"
      ],
      "env": {
        "SHOPIFY_STORE_DOMAIN": "your-store.myshopify.com",
        "SHOPIFY_CLIENT_ID": "your_client_id",
        "SHOPIFY_CLIENT_SECRET": "your_client_secret",
        "SHOPIFY_API_VERSION": "2026-04"
      }
    }
  }
}
```

### Variante 2: Lokal aus dem Repo

Das ist die stabilste Variante für Entwicklung und Debugging.

```json
{
  "mcpServers": {
    "flin-shopify-analytics-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--quiet",
        "--directory",
        "/Users/nicolasg/Antigravity/flin-shopify-analytics-mcp",
        "flin-shopify-analytics-mcp"
      ],
      "env": {
        "SHOPIFY_STORE_DOMAIN": "your-store.myshopify.com",
        "SHOPIFY_CLIENT_ID": "your_client_id",
        "SHOPIFY_CLIENT_SECRET": "your_client_secret",
        "SHOPIFY_API_VERSION": "2026-04"
      }
    }
  }
}
```

## Lokaler Start ohne Claude

### Mit Client ID / Client Secret

```bash
uvx --refresh -q flin-shopify-analytics-mcp@0.2.6 \
  --domain your-store.myshopify.com \
  --clientId your_client_id \
  --clientSecret your_client_secret \
  --apiVersion 2026-04
```

### Mit statischem Admin-Token

```bash
uvx --refresh -q flin-shopify-analytics-mcp@0.2.6 \
  --domain your-store.myshopify.com \
  --accessToken shpat_xxx \
  --apiVersion 2026-04
```

## TLS / SSL

Der MCP verwendet standardmäßig das `certifi`-CA-Bundle.

Falls deine Umgebung einen Firmen-Proxy oder eigene Root-Zertifikate benutzt, kannst du zusätzlich setzen:

```bash
SHOPIFY_CA_BUNDLE="/path/to/ca-bundle.pem"
```

Alternativ funktioniert auch:

```bash
SSL_CERT_FILE="/path/to/ca-bundle.pem"
```

## Troubleshooting

### `SSL: CERTIFICATE_VERIFY_FAILED`

Dann kann die Python-Umgebung die Zertifikatskette nicht verifizieren.

Prüfe in dieser Reihenfolge:

1. Ob du auf `0.2.6` oder neuer bist
2. Ob ein Firmen-Proxy oder eigenes Root-CA im Spiel ist
3. Ob `SHOPIFY_CA_BUNDLE` oder `SSL_CERT_FILE` gesetzt werden muss

### `no version of flin-shopify-analytics-mcp == ...`

Dann hängt `uvx` meistens noch auf einem alten Index-Stand.

Hilfreich:

```bash
uv cache clean flin-shopify-analytics-mcp
```

Und in der Claude-Konfiguration:

```json
"args": ["--refresh", "-q", "flin-shopify-analytics-mcp@0.2.6"]
```

## Entwicklung

Tests:

```bash
python -m unittest discover -s py_tests -v
```

Build:

```bash
uv build
```

## Release

1. Version in `pyproject.toml`, `flin_shopify_analytics_mcp/__init__.py` und `flin_shopify_analytics_mcp/mcp_server.py` anheben
2. Commit erstellen
3. Tag `vX.Y.Z` pushen
4. GitHub Actions Workflow `.github/workflows/release.yml` veröffentlicht auf PyPI

## Offizielle Shopify-Doku

- Dev Dashboard App und Client Credentials: https://shopify.dev/docs/apps/build/dev-dashboard/get-api-access-tokens
- Legacy Custom Apps im Shopify Admin: https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/generate-app-access-tokens-admin
