import { Component, OnDestroy, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WebsocketService, ChatMessage } from '../../../../core/services/websocket.service';
import { AuthService, User } from '../../../../core/services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-chat-sidebar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="h-full w-80 bg-white border-l border-gray-100 flex flex-col shadow-[-4px_0_24px_rgba(0,0,0,0.02)]">
      <!-- Header -->
      <div class="p-6 border-b border-gray-50 flex justify-between items-center bg-white/80 backdrop-blur-md sticky top-0 z-10">
        <div>
          <h3 class="font-black text-gray-900 uppercase tracking-tight text-sm">Battle Chat</h3>
          <p class="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-0.5">Live Updates</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[8px] font-black uppercase tracking-widest" [class.text-green-500]="wsConnected" [class.text-red-400]="!wsConnected">
            {{ wsConnected ? 'Online' : 'Offline' }}
          </span>
          <span class="w-2 h-2 rounded-full shadow-sm" [class.bg-green-500]="wsConnected" [class.bg-red-400]="!wsConnected" [class.animate-pulse]="wsConnected"></span>
        </div>
      </div>
      
      <!-- Messages Area -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth" #scrollContainer>
        <div *ngFor="let m of messages" 
             [class.items-end]="m.author === currentUser?.username"
             class="flex flex-col gap-1 animate-in fade-in slide-in-from-bottom-2 duration-300">
          
          <div class="flex items-center gap-2 px-1">
            <span class="text-[9px] font-black uppercase tracking-wider" 
                  [class.text-poke-blue]="m.author !== 'bot' && m.author === currentUser?.username"
                  [class.text-gray-400]="m.author === 'bot'"
                  [class.text-red-500]="m.author !== 'bot' && m.author !== currentUser?.username">
              {{ m.author }}
            </span>
          </div>

          <div [class.bg-poke-blue]="m.author === currentUser?.username"
               [class.text-white]="m.author === currentUser?.username"
               [class.bg-gray-50]="m.author !== currentUser?.username && !m.is_bot"
               [class.text-gray-700]="m.author !== currentUser?.username && !m.is_bot"
               [class.bg-yellow-50]="m.is_bot"
               [class.text-yellow-800]="m.is_bot"
               [class.border-yellow-100]="m.is_bot"
               [class.border]="m.is_bot"
               [class.rounded-tr-none]="m.author === currentUser?.username"
               [class.rounded-tl-none]="m.author !== currentUser?.username"
               class="px-4 py-3 rounded-2xl max-w-[95%] w-fit text-base leading-relaxed shadow-sm transition-all hover:shadow-md font-medium break-words whitespace-pre-wrap">
            {{ m.content }}
          </div>
        </div>

        <div *ngIf="messages.length === 0" class="h-full flex flex-col items-center justify-center opacity-20 p-8 text-center">
            <svg class="w-12 h-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
            <p class="text-xs font-bold uppercase tracking-widest">No activity yet</p>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-6 bg-white border-t border-gray-50">
        <div class="relative group">
          <input 
            [(ngModel)]="chatInput" 
            (keyup.enter)="sendChat()"
            placeholder="Broadcast message..." 
            class="w-full bg-gray-50 border-none rounded-2xl pl-4 pr-12 py-4 text-sm focus:ring-2 focus:ring-poke-blue outline-none transition-all placeholder:text-gray-400 font-medium">
          <button 
            (click)="sendChat()" 
            class="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-poke-blue text-white rounded-xl flex items-center justify-center hover:bg-poke-blue-dark transition-all shadow-lg shadow-poke-blue/20 active:scale-90">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100%; }
    .scroll-smooth { scroll-behavior: smooth; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #f1f1f1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #e5e7eb; }
  `]
})
export class ChatSidebarComponent implements OnInit, OnDestroy {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  currentUser: User | null = null;
  messages: ChatMessage[] = [];
  chatInput = '';
  wsConnected = false;
  private subs = new Subscription();

  constructor(
    private authService: AuthService,
    private wsService: WebsocketService
  ) {}

  ngOnInit() {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      console.log('ChatSidebar: User changed', user);
      if (user) {
        // Load history first
        this.wsService.getHistory().subscribe({
          next: (history) => {
            this.messages = history;
            this.scrollToBottom();
          },
          error: (err) => console.error('Failed to load chat history', err)
        });

        const team = user.color === 'RED' ? 'red' : 'blue';
        console.log(`ChatSidebar: Connecting to team ${team} as ${user.username}`);
        this.wsService.connect(team, user.username);
      }
    });

    this.subs.add(
      this.wsService.connected$.subscribe(connected => {
        this.wsConnected = connected;
      })
    );

    this.subs.add(
      this.wsService.messages$.subscribe(msg => {
        console.log('ChatSidebar: Message received', msg);
        this.messages.push(msg);
        this.scrollToBottom();
      })
    );
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
    this.wsService.disconnect();
  }

  sendChat() {
    if (!this.chatInput.trim()) return;
    this.wsService.sendMessage(this.chatInput);
    this.chatInput = '';
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.scrollContainer) {
        this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }
}
