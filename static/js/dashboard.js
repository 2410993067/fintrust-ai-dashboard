let subscriptionChartInstance = null;

function formatCurrency(value) {
  return `$${Number(value || 0).toFixed(2)}`;
}

function renderSubscriptions(subscriptions) {
  const chartSection = document.getElementById('chartSection');
  const tableSection = document.getElementById('tableSection');
  const emptyStateSection = document.getElementById('emptyStateSection');
  const tableBody = document.getElementById('subscriptionTableBody');

  tableBody.innerHTML = '';

  if (!subscriptions || !subscriptions.length) {
    chartSection.classList.add('d-none');
    tableSection.classList.add('d-none');
    emptyStateSection.classList.remove('d-none');
    return;
  }

  emptyStateSection.classList.add('d-none');
  chartSection.classList.remove('d-none');
  tableSection.classList.remove('d-none');

  subscriptions.forEach((item) => {
    const row = document.createElement('tr');
    const typeLabel = String(item.subscription_type || '')
      .replaceAll('_', ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());

    row.innerHTML = `
      <td>${item.merchant || ''}</td>
      <td><span class="pill">${item.category || 'Uncategorized'}</span></td>
      <td>${formatCurrency(item.avg_amount)}</td>
      <td>${Number(item.avg_interval || 0).toFixed(1)} days</td>
      <td>${Number(item.confidence_score || 0).toFixed(2)}</td>
      <td><span class="pill">${typeLabel}</span></td>
    `;
    tableBody.appendChild(row);
  });
}

function renderChart(labels, values) {
  const ctx = document.getElementById('subscriptionChart');
  if (subscriptionChartInstance) {
    subscriptionChartInstance.destroy();
    subscriptionChartInstance = null;
  }

  if (!ctx || !labels.length) {
    return;
  }

  subscriptionChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Monthly Cost',
        data: values,
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Cost ($)' },
        },
        x: {
          title: { display: true, text: 'Merchant' },
        },
      },
    },
  });
}

async function loadDashboard() {
  const errorBanner = document.getElementById('dashboardError');
  errorBanner.classList.add('d-none');

  try {
    const response = await fetch('/api/dashboard');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    document.getElementById('totalTransactions').textContent = data.total_transactions ?? 0;
    document.getElementById('totalSpending').textContent = formatCurrency(data.total_spending);
    document.getElementById('monthlySubscriptionCost').textContent = formatCurrency(data.monthly_subscription_cost);
    document.getElementById('healthScore').textContent = data.health_score ?? 100;
    document.getElementById('healthLabel').textContent = data.health_label || 'Excellent';

    renderSubscriptions(data.subscriptions || []);
    renderChart(data.chart_labels || [], data.chart_values || []);
  } catch (error) {
    errorBanner.classList.remove('d-none');
    console.error('Dashboard load failed:', error);
  }
}

loadDashboard();
