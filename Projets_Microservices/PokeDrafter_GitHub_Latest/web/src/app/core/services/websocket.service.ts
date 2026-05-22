import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subject, BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ChatMessage {
  author: string;
  content: string;
  is_bot: boolean;
  team?: string;
  sent_at?: string;
}

@Injectable({
  providedIn: 'root'
})
export class WebsocketService {
  private socket: WebSocket | null = null;
  private messagesSubject = new Subject<ChatMessage>();
  public messages$ = this.messagesSubject.asObservable();

  private connectedSubject = new BehaviorSubject<boolean>(false);
  public connected$ = this.connectedSubject.asObservable();

  constructor(private http: HttpClient) { }

  getHistory(): Observable<ChatMessage[]> {
    return this.http.get<ChatMessage[]>(`${environment.apiUrl}/chat/history`);
  }

  connect(team: 'red' | 'blue', username: string): void {
    if (this.socket) {
      this.socket.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    // Gateway is on port 80
    const url = `${protocol}//${host}/ws/chat/${team}?username=${encodeURIComponent(username)}`;

    console.log('WebsocketService: Connecting to', url);
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log('WebsocketService: Connection opened');
      this.connectedSubject.next(true);
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.messagesSubject.next(data);
      } catch (err) {
        console.error('WebsocketService: Failed to parse message', event.data);
      }
    };

    this.socket.onclose = (event) => {
      console.log('WebsocketService: Connection closed', event);
      this.connectedSubject.next(false);
      this.socket = null;
    };

    this.socket.onerror = (error) => {
      console.error('WebsocketService: Error', error);
      this.connectedSubject.next(false);
    };
  }

  sendMessage(content: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(content);
    } else {
      console.warn('WebsocketService: Cannot send message, socket not open');
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.connectedSubject.next(false);
    }
  }
}
