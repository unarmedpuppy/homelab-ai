import Phaser from 'phaser';

// Singleton event emitter for Phaser <-> React communication
export const EventBus = new Phaser.Events.EventEmitter();
