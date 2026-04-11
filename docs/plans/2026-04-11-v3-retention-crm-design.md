# V3 Retention CRM Design

**Date:** 2026-04-11

## Goal

`v3` erweitert den Shopify MCP um Customer-Intelligence-KPIs fuer Retention und CRM Health. Der Fokus liegt auf Window-Retention, Zeit bis zum Zweitkauf und Inaktivitaetskennzahlen, nicht auf Kampagnen- oder Listenaktivierung.

## Scope

Neue read-only Tools:

- `shopify_retention_overview`
- `shopify_repeat_purchase_windows`
- `shopify_time_to_second_order`
- `shopify_inactive_customer_summary`

Nicht in `v3`:

- Winback-Listen
- VIP-/RFM-Segmente
- Cohort-Revenue-Tabellen ueber mehrere Akquisitionsmonate
- CLV-Modelle
- Attribution

## Input Model

### Cohort-based tools

Diese Tools arbeiten auf einem Erstkauf-Cohort-Fenster:

- `dateFrom` required
- `dateTo` required
- `asOfDate` optional, default = `dateTo`
- `limit` optional, default = `1000`

Bedeutung:

- `dateFrom` / `dateTo`: Zeitraum, in dem der Erstkauf eines Kunden liegen muss
- `asOfDate`: Beobachtungsstichtag fuer Wiederkaeufe

### Inactivity summary

Dieses Tool arbeitet auf einem Beobachtungsstichtag:

- `asOfDate` required
- `limit` optional, default = `1000`

## Definitions

- `tracked customer`: Kunde mit `customer.id` oder `customer.email`
- `firstOrderAt`: frueheste bekannte Order eines Kunden
- `secondOrderAt`: zweite bekannte Order eines Kunden
- `repeat customer`: Kunde mit mindestens zwei bekannten Orders
- `cohort customer`: Kunde, dessen `firstOrderAt` zwischen `dateFrom` und `dateTo` liegt
- `window repeat`: zweite Order liegt innerhalb von 30/60/90/180 Tagen nach `firstOrderAt`
- `eligible customer`: Cohort-Kunde, dessen Erstkauf weit genug vor `asOfDate` liegt, damit das Fenster voll beobachtbar ist
- `inactive 90d`: letzte bekannte Order liegt mindestens 90 Tage vor `asOfDate`

## Data Source Strategy

Die Metriken werden ausschliesslich aus Order-Historie rekonstruiert.

Fuer die Retention-Tools muessen Orders bis `asOfDate` geladen werden, nicht nur innerhalb des Cohort-Fensters. Sonst koennen Erstkauf und Zweitkauf nicht korrekt erkannt werden.

Wichtig:

- Gastbestellungen ohne stabile Kundenkennung werden fuer Customer-Intelligence-KPIs ausgeschlossen
- fuer grosse Shops bleiben die Kennzahlen von `limit` und verfuegbarer Order-Historie abhaengig
- `read_all_orders` ist fuer belastbare Langfrist-Retention empfohlen

## Internal Model

Aus Orders wird pro Customer eine History erzeugt:

- `customerId`
- `customerEmail`
- `customerName`
- `orderCount`
- `firstOrderAt`
- `secondOrderAt`
- `lastOrderAt`
- `netSalesTotal`
- `orders[]`

Abgeleitete Kennzahlen:

- `daysToSecondOrder`
- `repeatOrderCount`
- `repeatNetSales`
- `daysSinceLastOrder`

## Tool Design

### `shopify_retention_overview`

Returns:

- `cohortCustomers`
- `repeatCustomers`
- `repeatCustomerRate`
- `firstOrderNetSales`
- `repeatOrderNetSales`
- `repeatOrders`
- `averageDaysToSecondOrder`
- `medianDaysToSecondOrder`

### `shopify_repeat_purchase_windows`

Fixed windows:

- 30
- 60
- 90
- 180 days

Per window returns:

- `windowDays`
- `eligibleCustomers`
- `repeatedCustomers`
- `repeatRate`
- `ineligibleCustomers`

### `shopify_time_to_second_order`

Returns:

- `cohortCustomers`
- `customersWithSecondOrder`
- `averageDays`
- `medianDays`
- `p75Days`
- bucket counts:
  - `0-30`
  - `31-60`
  - `61-90`
  - `91-180`
  - `181+`

### `shopify_inactive_customer_summary`

Returns for fixed inactivity windows 30/60/90/180:

- `trackedCustomers`
- `inactiveCustomers`
- `inactiveRate`
- `historicalNetSales`
- `averageDaysSinceLastOrder`

## Architecture

1. `analytics.py` bekommt einen dedizierten Customer-History-Layer auf Basis der `v2`-Orderdaten
2. darauf bauen die vier Retention-KPI-Funktionen auf
3. `tools.py` expose't die vier neuen MCP Tools
4. `README.md` wird um `v3` ergaenzt

## Risks

- Wenn der MCP nicht genug historische Orders laden kann, fallen Retention-Zahlen zu optimistisch oder unvollstaendig aus
- Gast-Orders ohne Kundenkennung koennen nicht sauber in Retention gerechnet werden
- `asOfDate` muss analytisch sauber verwendet werden, sonst entstehen verzerrte Window-Rates

## Success Criteria

`v3` ist erfolgreich, wenn Claude ueber den MCP direkt antworten kann:

- Wie hoch ist die Wiederkaufrate einer Erstkauf-Cohort?
- Wie viele Kunden kaufen innerhalb von 30/60/90/180 Tagen erneut?
- Wie lange dauert es typischerweise bis zum Zweitkauf?
- Wie viele Bestandskunden sind seit 30/60/90/180 Tagen inaktiv?
