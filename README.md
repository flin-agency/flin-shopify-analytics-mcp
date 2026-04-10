# flin-shopify-analytics-mcp

Read-only MCP Server fuer Shopify Analytics.

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

- Node.js 20+
- Shopify Custom App mit mindestens diesen Scopes:
- `read_orders`
- `read_customers`
- `read_products`

## Setup

1. Abhaengigkeiten installieren (nur fuer npm scripts):

```bash
npm install
```

2. Umgebungsvariablen setzen (siehe `.env.example`).

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

3. MCP Server starten:

```bash
npm start
```

## MCP Client Konfiguration (Beispiel)

### Mit CLI Args (Client Credentials)

```json
{
  "mcpServers": {
    "shopify-analytics": {
      "command": "node",
      "args": [
        "/Users/nicolasg/Antigravity/flin-shopify-analytics-mcp/src/index.js",
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

### Mit Environment Variables

```json
{
  "mcpServers": {
    "shopify-analytics": {
      "command": "node",
      "args": ["/Users/nicolasg/Antigravity/flin-shopify-analytics-mcp/src/index.js"],
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

Tests laufen mit:

```bash
npm test
```
