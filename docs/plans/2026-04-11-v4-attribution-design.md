# V4 Attribution Design

**Date:** 2026-04-11

## Goal

`v4` erweitert den Shopify MCP um Source- und UTM-basierte Attribution-Reports. Der Fokus liegt auf operativen Marketing-Reports und Datenqualitaet, nicht auf komplexer Multi-Touch-Attribution.

## Scope

Neue read-only Tools:

- `shopify_attribution_quality_summary`
- `shopify_sales_by_source`
- `shopify_sales_by_utm`
- `shopify_new_customers_by_attribution`
- `shopify_landing_page_analysis`

Nicht in `v4`:

- Multi-touch Attribution
- Last-click vs. first-click Modelle ueber mehrere Touchpoints
- Channel cost import
- ROAS / CAC aus externen Ad-Plattformen

## Data Availability Principle

Shopify-Attribution ist oft lueckenhaft. Deshalb muss jeder Report sichtbar machen, wie belastbar die zugrunde liegenden Daten sind.

Der MCP soll deshalb nicht nur Umsatz nach Quelle ausgeben, sondern auch:

- wie viele Orders Attribution-Daten haben
- wie viele Orders UTM-Werte haben
- wie viele Orders ohne Attribution sind

## Internal Attribution Model

Pro Order wird ein normalisiertes Attribution-Objekt erzeugt:

- `sourceName`
- `landingPage`
- `referringSite`
- `utm.source`
- `utm.medium`
- `utm.campaign`
- `utm.term`
- `utm.content`
- `hasAttribution`
- `hasUtm`
- `hasLandingPage`

## Source of Truth

`v4` basiert auf Order-Historie, nicht auf externen Marketingdaten.

Wenn Shopify keine oder nur teilweise Attribution liefert, reportet der MCP genau das, statt Werte zu raten.

## Inputs

Alle Attribution-Tools ausser `quality_summary` verwenden:

- `dateFrom` required
- `dateTo` required
- `limit` optional
- `query` optional

Zusatzinputs:

### `shopify_sales_by_utm`

- `groupBy`: `source|medium|campaign|source_medium|source_medium_campaign`

### `shopify_new_customers_by_attribution`

- `groupBy`: `source|campaign|landingPage`

### `shopify_landing_page_analysis`

- `sortBy`: `netSales|orders|newCustomers`

## Tool Design

### `shopify_attribution_quality_summary`

Returns:

- `orderCount`
- `ordersWithSource`
- `ordersWithLandingPage`
- `ordersWithUtm`
- `ordersWithoutAttribution`
- rates for each of the above

### `shopify_sales_by_source`

Returns grouped by normalized source:

- `source`
- `orders`
- `unitsSold`
- `grossSales`
- `netSales`
- `averageOrderValue`

### `shopify_sales_by_utm`

Returns grouped by the selected UTM dimension:

- `group`
- `orders`
- `unitsSold`
- `grossSales`
- `netSales`
- `averageOrderValue`

### `shopify_new_customers_by_attribution`

Returns:

- `group`
- `newCustomers`
- `firstOrderNetSales`
- `firstOrders`

Definition:

Ein Kunde zaehlt nur dann als `new customer` fuer eine Gruppe, wenn seine erste bekannte Order im Analysezeitraum liegt.

### `shopify_landing_page_analysis`

Returns grouped by landing page:

- `landingPage`
- `orders`
- `newCustomers`
- `grossSales`
- `netSales`
- `averageOrderValue`

## Architecture

1. `shopify_client.py` erweitert die Order-Query, falls Shopify die benoetigten Felder liefert
2. `analytics.py` bekommt Attribution-Normalizer und Aggregationsfunktionen
3. `tools.py` expose't die neuen MCP Tools
4. `README.md` dokumentiert Scope und Datenqualitaetsgrenzen

## Query Strategy

Wir nutzen nur Felder, die aus Shopify-Orders direkt ableitbar sind. Wenn `landingPage` oder `referringSite` im Schema nicht vorhanden oder nicht stabil verfuegbar sind, bleibt `v4` minimal auf `sourceName` plus UTM aus Landing URLs bzw. vorhandenen Order-Feldern.

## Risks

- fehlende oder inkonsistente UTM-Daten
- `sourceName` ist oft grob und kanalisiert nicht fein genug
- Landing-Page-Felder sind je nach Shop/Checkout-Setup nicht immer verlaesslich

## Success Criteria

`v4` ist erfolgreich, wenn Claude direkt beantworten kann:

- Wie verteilt sich Umsatz nach Source?
- Welche UTM-Kampagnen erzeugen Umsatz?
- Welche Quellen bringen Neukunden?
- Welche Landing Pages performen?
- Wie gut ist die Attribution-Datenbasis ueberhaupt?
