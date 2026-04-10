function normalizeMoney(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : 0;
}

function customerKey(customer) {
  if (customer?.id) {
    return customer.id;
  }
  if (customer?.email) {
    return `email:${customer.email}`;
  }
  return "guest";
}

export function aggregateByCustomerProduct(orders) {
  const customers = new Map();

  for (const order of orders) {
    const key = customerKey(order.customer);
    if (!customers.has(key)) {
      customers.set(key, {
        customerId: order.customer?.id ?? null,
        customerName: order.customer?.name ?? "Guest",
        customerEmail: order.customer?.email ?? null,
        totalOrders: 0,
        totalSpent: 0,
        currencyCode: order.currencyCode ?? null,
        products: new Map()
      });
    }

    const customer = customers.get(key);
    customer.totalOrders += 1;
    customer.totalSpent += normalizeMoney(order.totalAmount);
    if (!customer.currencyCode && order.currencyCode) {
      customer.currencyCode = order.currencyCode;
    }

    for (const item of order.items || []) {
      const productKey = item.productId || `${item.title}:${item.sku || ""}`;
      if (!customer.products.has(productKey)) {
        customer.products.set(productKey, {
          productId: item.productId ?? null,
          title: item.title ?? "Unknown product",
          sku: item.sku ?? null,
          quantity: 0
        });
      }
      customer.products.get(productKey).quantity += Number(item.quantity || 0);
    }
  }

  const customerList = [...customers.values()]
    .map((entry) => ({
      customerId: entry.customerId,
      customerName: entry.customerName,
      customerEmail: entry.customerEmail,
      totalOrders: entry.totalOrders,
      totalSpent: Number(entry.totalSpent.toFixed(2)),
      currencyCode: entry.currencyCode,
      products: [...entry.products.values()].sort((a, b) => b.quantity - a.quantity)
    }))
    .sort((a, b) => b.totalSpent - a.totalSpent);

  return {
    orderCount: orders.length,
    customerCount: customerList.length,
    customers: customerList
  };
}
