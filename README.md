# flin-shopify-analytics-mcp

Read-only MCP Server fuer Shopify Analytics, verteilbar ueber PyPI.

Ziel: alle wichtigen Shop-Daten abfragen und insbesondere beantworten koennen:
- wer gekauft hat
- was gekauft wurde
- wie viel gekauft wurde
- wie viel Umsatz je Kunde entstanden ist

## Features (v1, nur read)

- `shopify_list_orders`: Orders mit Kunde, Betrag und Line-Items
- `shopify_list_customers`: Kunden mit Bestellanzahl und Amount Spent
- `shopify_list_products`: Produkte/Varianten mit SKU, Preis, Bestand
- `shopify_customer_purchase_summary`: Zusammenfassung pro Kunde
- `shopify_sales_by_customer_product`: Aggregation "wer hat was wie viel gekauft"

Der Server blockiert GraphQL `mutation`-Operationen explizit.

## Voraussetzungen

- Python 3.10+
- `uv` (empfohlen fuer `uvx`) oder `pip`
- Shopify App mit mindestens diesen Scopes:
  - `read_orders`
  - `read_customers`
  - `read_products`

## Nutzung

### Option A: Direkt ueber PyPI mit uvx (empfohlen)

```bash
uvx --from flin-shopify-analytics-mcp shopify-mcp \
  --domain your-store.myshopify.com \
  --clientId your_client_id \
  --clientSecret your_client_secret \
  --apiVersion 2025-01
```

### Option B: Lokal entwickeln

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
shopify-mcp --domain your-store.myshopify.com --clientId your_client_id --clientSecret your_client_secret
```

## Auth-Optionen

Option 1: Client Credentials (neue Dev Dashboard Apps)

```bash
export SHOPIFY_STORE_DOMAIN="your-store.myshopify.com"
export SHOPIFY_CLIENT_ID="your_client_id"
export SHOPIFY_CLIENT_SECRET="your_client_secret"
export SHOPIFY_API_VERSION="2025-01"
```

Option 2: Legacy Static Access Token

```bash
export SHOPIFY_STORE_DOMAIN="your-store.myshopify.com"
export SHOPIFY_ADMIN_ACCESS_TOKEN="shpat_xxx"
export SHOPIFY_API_VERSION="2025-01"
```

Hinweis:
- Bei `client_credentials` wird das Access Token automatisch angefordert und kurz vor Ablauf erneuert.
- Wenn sowohl `SHOPIFY_ADMIN_ACCESS_TOKEN` als auch `SHOPIFY_CLIENT_ID/SHOPIFY_CLIENT_SECRET` gesetzt sind, gewinnt der statische Token-Modus.

## MCP Client Konfiguration (Beispiel)

### Claude Desktop mit uvx

```json
{
  "mcpServers": {
    "shopify-analytics": {
      "command": "uvx",
      "args": [
        "--from",
        "flin-shopify-analytics-mcp",
        "shopify-mcp",
        "--domain",
        "your-store.myshopify.com",
        "--clientId",
        "your_client_id",
        "--clientSecret",
        "your_client_secret",
        "--apiVersion",
        "2025-01"
      ]
    }
  }
}
```

### Alternative mit ENV

```json
{
  "mcpServers": {
    "shopify-analytics": {
      "command": "uvx",
      "args": ["--from", "flin-shopify-analytics-mcp", "shopify-mcp"],
      "env": {
        "SHOPIFY_STORE_DOMAIN": "your-store.myshopify.com",
        "SHOPIFY_CLIENT_ID": "your_client_id",
        "SHOPIFY_CLIENT_SECRET": "your_client_secret",
        "SHOPIFY_API_VERSION": "2025-01"
      }
    }
  }
}
```

## Entwicklung

Python Tests:

```bash
python -m unittest discover -s py_tests -v
```

## Release auf PyPI

1. Version in `pyproject.toml` und `flin_shopify_analytics_mcp/__init__.py` hochziehen.
2. Commit + Push nach `main`.
3. GitHub Release mit Tag `vX.Y.Z` erstellen.
4. Workflow `.github/workflows/release.yml` published automatisch auf PyPI (Trusted Publisher oder `PYPI_API_TOKEN`).

Hinweis:
- Fuer Trusted Publishing muss das PyPI-Projekt einmalig mit diesem GitHub-Repo/Workflow verknuepft sein.
