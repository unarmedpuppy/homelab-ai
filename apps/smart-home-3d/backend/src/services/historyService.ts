// In-memory history for now - will be replaced with Prisma/PostgreSQL
interface HistoryRecord {
  id: string;
  deviceId: string;
  timestamp: Date;
  property: string;
  oldValue: unknown;
  newValue: unknown;
}

interface DeviceEvent {
  deviceId: string;
  timestamp: Date;
  property: string;
  oldValue: unknown;
  newValue: unknown;
}

export class HistoryService {
  private records: HistoryRecord[] = [];
  private maxRecords = 10000;

  async recordEvent(event: DeviceEvent): Promise<void> {
    const record: HistoryRecord = {
      id: `${event.deviceId}-${event.timestamp.getTime()}`,
      ...event,
    };

    this.records.push(record);

    // Trim old records
    if (this.records.length > this.maxRecords) {
      this.records = this.records.slice(-this.maxRecords);
    }
  }

  async getDeviceHistory(
    deviceId: string,
    startDate?: Date,
    endDate?: Date,
    limit = 1000
  ): Promise<HistoryRecord[]> {
    let filtered = this.records.filter((r) => r.deviceId === deviceId);

    if (startDate) {
      filtered = filtered.filter((r) => r.timestamp >= startDate);
    }

    if (endDate) {
      filtered = filtered.filter((r) => r.timestamp <= endDate);
    }

    return filtered.slice(-limit).reverse();
  }

  async getDevicePropertyHistory(
    deviceId: string,
    property: string,
    startDate?: Date,
    endDate?: Date
  ): Promise<{ timestamp: Date; value: unknown }[]> {
    let filtered = this.records.filter(
      (r) => r.deviceId === deviceId && r.property === property
    );

    if (startDate) {
      filtered = filtered.filter((r) => r.timestamp >= startDate);
    }

    if (endDate) {
      filtered = filtered.filter((r) => r.timestamp <= endDate);
    }

    return filtered.map((r) => ({
      timestamp: r.timestamp,
      value: r.newValue,
    }));
  }

  async getAggregatedHistory(
    deviceId: string,
    property: string,
    interval: 'hour' | 'day' | 'week' | 'month',
    startDate: Date,
    endDate: Date
  ): Promise<{ bucket: Date; avgValue: number; minValue: number; maxValue: number; count: number }[]> {
    const history = await this.getDevicePropertyHistory(deviceId, property, startDate, endDate);

    // Group by interval
    const buckets = new Map<string, { values: number[]; timestamp: Date }>();

    for (const record of history) {
      const bucketKey = this.getBucketKey(record.timestamp, interval);
      if (!buckets.has(bucketKey)) {
        buckets.set(bucketKey, { values: [], timestamp: this.getBucketStart(record.timestamp, interval) });
      }

      const value = typeof record.value === 'number' ? record.value : parseFloat(String(record.value));
      if (!isNaN(value)) {
        buckets.get(bucketKey)!.values.push(value);
      }
    }

    // Calculate aggregates
    return Array.from(buckets.values())
      .map(({ values, timestamp }) => ({
        bucket: timestamp,
        avgValue: values.reduce((a, b) => a + b, 0) / values.length,
        minValue: Math.min(...values),
        maxValue: Math.max(...values),
        count: values.length,
      }))
      .sort((a, b) => a.bucket.getTime() - b.bucket.getTime());
  }

  private getBucketKey(date: Date, interval: 'hour' | 'day' | 'week' | 'month'): string {
    const d = new Date(date);

    switch (interval) {
      case 'hour':
        return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}-${d.getHours()}`;
      case 'day':
        return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      case 'week':
        const weekNum = Math.floor(d.getDate() / 7);
        return `${d.getFullYear()}-${d.getMonth()}-${weekNum}`;
      case 'month':
        return `${d.getFullYear()}-${d.getMonth()}`;
    }
  }

  private getBucketStart(date: Date, interval: 'hour' | 'day' | 'week' | 'month'): Date {
    const d = new Date(date);

    switch (interval) {
      case 'hour':
        d.setMinutes(0, 0, 0);
        break;
      case 'day':
        d.setHours(0, 0, 0, 0);
        break;
      case 'week':
        d.setHours(0, 0, 0, 0);
        d.setDate(d.getDate() - d.getDay());
        break;
      case 'month':
        d.setHours(0, 0, 0, 0);
        d.setDate(1);
        break;
    }

    return d;
  }

  async cleanupOldHistory(retentionDays: number = 90): Promise<number> {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - retentionDays);

    const before = this.records.length;
    this.records = this.records.filter((r) => r.timestamp >= cutoff);

    return before - this.records.length;
  }

  async exportHistory(
    deviceId: string,
    startDate: Date,
    endDate: Date
  ): Promise<string> {
    const history = await this.getDeviceHistory(deviceId, startDate, endDate);

    const headers = ['timestamp', 'property', 'old_value', 'new_value'];
    const rows = history.map((h) => [
      h.timestamp.toISOString(),
      h.property,
      JSON.stringify(h.oldValue),
      JSON.stringify(h.newValue),
    ]);

    return [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
  }
}
