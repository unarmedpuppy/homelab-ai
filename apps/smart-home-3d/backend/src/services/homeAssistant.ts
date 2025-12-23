import { EventEmitter } from 'events';

interface HAState {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
}

interface HAEvent {
  event_type: string;
  data: {
    entity_id: string;
    new_state: HAState;
    old_state: HAState;
  };
}

export class HomeAssistantService extends EventEmitter {
  private ws: WebSocket | null = null;
  private messageId = 1;
  private isConnected = false;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pendingRequests = new Map<number, { resolve: (value: unknown) => void; reject: (error: Error) => void }>();

  constructor(
    private readonly url: string,
    private readonly token: string
  ) {
    super();
  }

  async connect(): Promise<void> {
    if (!this.token) {
      console.log('No HA token - skipping connection');
      return;
    }

    return new Promise((resolve, reject) => {
      const wsUrl = this.url.replace(/^http/, 'ws') + '/api/websocket';

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected to Home Assistant');
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(JSON.parse(event.data as string), resolve);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(new Error('WebSocket connection failed'));
        };

        this.ws.onclose = () => {
          this.isConnected = false;
          this.scheduleReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: Record<string, unknown>, connectResolve?: (value: unknown) => void): void {
    const type = message.type as string;

    switch (type) {
      case 'auth_required':
        this.authenticate();
        break;

      case 'auth_ok':
        this.isConnected = true;
        console.log('Authenticated with Home Assistant');
        this.subscribeToEvents();
        connectResolve?.({});
        break;

      case 'auth_invalid':
        console.error('Invalid Home Assistant token');
        break;

      case 'result':
        this.handleResult(message);
        break;

      case 'event':
        this.handleEvent(message as unknown as { event: HAEvent });
        break;
    }
  }

  private authenticate(): void {
    this.send({
      type: 'auth',
      access_token: this.token,
    });
  }

  private subscribeToEvents(): void {
    this.sendCommand({
      type: 'subscribe_events',
      event_type: 'state_changed',
    });
  }

  private handleResult(message: Record<string, unknown>): void {
    const id = message.id as number;
    const pending = this.pendingRequests.get(id);

    if (pending) {
      if (message.success) {
        pending.resolve(message.result);
      } else {
        pending.reject(new Error((message.error as { message: string })?.message || 'Unknown error'));
      }
      this.pendingRequests.delete(id);
    }
  }

  private handleEvent(message: { event: HAEvent }): void {
    const { event } = message;

    if (event.event_type === 'state_changed') {
      this.emit('state_changed', {
        entityId: event.data.entity_id,
        newState: event.data.new_state,
        oldState: event.data.old_state,
      });
    }
  }

  private send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private sendCommand<T>(command: Record<string, unknown>): Promise<T> {
    return new Promise((resolve, reject) => {
      const id = this.messageId++;
      this.pendingRequests.set(id, { resolve: resolve as (value: unknown) => void, reject });

      this.send({
        ...command,
        id,
      });

      // Timeout after 10 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      console.log('Attempting to reconnect to Home Assistant...');
      this.connect().catch(console.error);
    }, 5000);
  }

  async getStates(): Promise<HAState[]> {
    if (!this.isConnected) {
      throw new Error('Not connected to Home Assistant');
    }

    return this.sendCommand<HAState[]>({
      type: 'get_states',
    });
  }

  async callService(
    domain: string,
    service: string,
    entityId: string,
    data: Record<string, unknown> = {}
  ): Promise<void> {
    if (!this.isConnected) {
      throw new Error('Not connected to Home Assistant');
    }

    await this.sendCommand({
      type: 'call_service',
      domain,
      service,
      service_data: {
        entity_id: entityId,
        ...data,
      },
    });
  }

  async turnOn(entityId: string, options: Record<string, unknown> = {}): Promise<void> {
    const [domain] = entityId.split('.');
    await this.callService(domain, 'turn_on', entityId, options);
  }

  async turnOff(entityId: string): Promise<void> {
    const [domain] = entityId.split('.');
    await this.callService(domain, 'turn_off', entityId);
  }

  async toggle(entityId: string): Promise<void> {
    const [domain] = entityId.split('.');
    await this.callService(domain, 'toggle', entityId);
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }
}
