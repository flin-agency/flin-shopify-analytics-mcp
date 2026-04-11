# V2 Reporting Core Design

**Date:** 2026-04-11

## Goal

`v2` erweitert den Shopify MCP von einfachen Listenabfragen zu belastbarem Sales-Reporting. Der Fokus liegt auf operativen KPI-Antworten fuer einen Zeitraum, nicht auf vollstaendiger Finanzbuchhaltung.

## Scope

Neue read-only Tools:

- `shopify_sales_overview`
- `shopify_sales_timeseries`
- `shopify_top_products`
- `shopify_top_customers`
- `shopify_discount_analysis`

Nicht in `v2`:

- Cohorts
- CLV
- RFM
- UTM/Source Attribution
- vollstaendige Finance-Metriken inklusive Margin

## KPI Definitions

Der MCP soll fuer `v2` eine konsistente, dokumentierte Definition verwenden:

- `grossSales`: Summe der Line-Item-Preise vor Discounts und vor Refunds
- `discountAmount`: Summe der Discounts auf Order-Ebene und Line-Item-Ebene
- `refundedAmount`: Summe der Refunds
- `netSales`: `grossSales - discountAmount - refundedAmount`
- `orders`: Anzahl Orders im Zeitraum
- `unitsSold`: aktuelle verkaufte Einheiten nach Refunds/Removals
- `averageOrderValue`: `netSales / orders`

Wichtig: `v2` liefert Sales Reporting, kein buchhalterisch vollstaendiges P&L-Modell.

## Data Model

Die bestehende Order-Repräsentation wird erweitert und dient gleichzeitig als normalisierte Analytics-Basis.

Pro Order werden zusaetzlich benoetigt:

- `subtotalAmount`
- `discountAmount`
- `refundedAmount`
- `grossSales`
- `netSales`
- `unitsSold`
- `discountCodes`
- `sourceName`
- `customer.numberOfOrders`

Pro Line Item werden zusaetzlich benoetigt:

- `variantId`
- `variantTitle`
- `vendor`
- `quantity`
- `currentQuantity`
- `unitPrice`
- `discountedUnitPrice`
- `grossSales`
- `netSales`
- `discountAmount`

## Shopify Fields

Die Implementierung erweitert die Order-GraphQL-Query auf Basis von Shopify Admin GraphQL 2026-04.

Verwendete Order-Felder:

- `subtotalPriceSet`
- `totalDiscountsSet`
- `totalRefundedSet`
- `discountCodes`
- `currentSubtotalLineItemsQuantity`
- `sourceName`
- `customer.numberOfOrders`

Verwendete Line-Item-Felder:

- `quantity`
- `currentQuantity`
- `originalUnitPriceSet`
- `discountedUnitPriceAfterAllDiscountsSet`
- `originalTotalSet`
- `totalDiscountSet`
- `variant { id title sku }`
- `product { id title }`
- `vendor`

## Tool Design

### `shopify_sales_overview`

Inputs:

- `dateFrom` required
- `dateTo` required
- `query` optional
- `comparePreviousPeriod` optional

Returns:

- KPI block for current period
- optional KPI block for previous period
- delta block for main metrics

### `shopify_sales_timeseries`

Inputs:

- `dateFrom` required
- `dateTo` required
- `interval`: `day|week|month`
- `query` optional
- `comparePreviousPeriod` optional

Returns:

- ordered buckets with `label`, `orders`, `unitsSold`, `grossSales`, `discountAmount`, `refundedAmount`, `netSales`, `averageOrderValue`
- optional previous-period buckets

### `shopify_top_products`

Inputs:

- `dateFrom` required
- `dateTo` required
- `limit` optional
- `query` optional
- `sortBy`: `netSales|grossSales|unitsSold|orders`
- `groupBy`: `product|variant`

Returns:

- ranked rows with product/variant identifiers and KPI totals

### `shopify_top_customers`

Inputs:

- `dateFrom` required
- `dateTo` required
- `limit` optional
- `query` optional
- `sortBy`: `netSales|grossSales|unitsSold|orders`
- `customerType`: `all|new|returning`

Returns:

- ranked customer rows with KPI totals and customer metadata

### `shopify_discount_analysis`

Inputs:

- `dateFrom` required
- `dateTo` required
- `limit` optional for top codes
- `query` optional

Returns:

- `discountAmountTotal`
- `discountedOrders`
- `discountedOrderRate`
- `averageDiscountPerDiscountedOrder`
- top discount codes

## Architecture

Die Umsetzung bleibt bewusst einfach und erweiterbar:

1. `shopify_client.py` erweitert die GraphQL Order Query und das Order Mapping
2. `analytics.py` erhaelt neue Aggregationsfunktionen fuer Overview, Timeseries, Product Ranking, Customer Ranking und Discount Analysis
3. `tools.py` registriert und dispatcht die neuen MCP Tools
4. Tests decken sowohl Analytics-Berechnung als auch MCP-Tool-Exposure ab

## Risks

- Shopify Order-Daten sind nicht Finance-Accounting. Werte muessen klar als Sales KPIs kommuniziert werden.
- `new` vs. `returning` basiert in `v2` auf `customer.numberOfOrders`; fuer spaetere Lifecycle-Analysen ist ein eigener Customer-Intelligence-Layer sauberer.
- Line-Item Revenue bleibt fuer v2 Reporting ausreichend genau, aber nicht als perfekte Finanzallokation zu verstehen.

## Success Criteria

`v2` ist erfolgreich, wenn Claude mit dem MCP diese Fragen direkt beantworten kann:

- Wie hoch waren Umsatz, Orders, Units, Discounts und Refunds in einem Zeitraum?
- Wie entwickelt sich der Shop ueber Tage, Wochen oder Monate?
- Welche Produkte und Kunden treiben den Umsatz?
- Welche Discount Codes haben den groessten Effekt?
