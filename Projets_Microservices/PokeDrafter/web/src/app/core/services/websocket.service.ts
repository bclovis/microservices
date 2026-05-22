import { Injectable } from '@angular/core';
import { Subject, Observable, EMPTY } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ChatMessage {
  author: string;
  content: string;
  is_bot: boolean;
  team?: string;
}

@Injectable({
  providedIn: 'root'
})
export class WebsocketService {
  private socket: WebSocket | null = null;
  private messagesSubject = new Subject<ChatMessage>();
  public messages$ = this.messagesSubject.asObservable();

  constructor() { }

  connect(team: 'red' | 'blue', username: string): void {
    if (this.socket) {
      this.socket.close();
    }

    // Use absolute URL for WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = 'localhost'; // Or environment.apiUrl host
    const url = `${protocol}//${host}/ws/chat/${team}?username=${encodeURIComponent(username)}`;

    this.socket = new WebSocket(url);

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messagesSubject.next(data);
    };

    this.socket.onclose = (event) => {
      console.log('WebSocket connection closed', event);
      this.socket = null;
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error', error);
    };
  }

  sendMessage(content: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(content);
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
