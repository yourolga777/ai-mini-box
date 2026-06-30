export function formatPrice(kopecks: number): string {
  return `${(kopecks / 100).toLocaleString("ru-RU", { minimumFractionDigits: 2 })} ₽`;
}

export function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    new: "Новый",
    processing: "В обработке",
    completed: "Выполнен",
    cancelled: "Отменён",
  };
  return labels[status] ?? status;
}
