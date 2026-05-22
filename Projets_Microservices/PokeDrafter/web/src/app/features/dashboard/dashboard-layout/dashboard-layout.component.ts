import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SidebarComponent } from '../components/sidebar/sidebar.component';
import { ChatSidebarComponent } from '../components/chat-sidebar/chat-sidebar.component';

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, SidebarComponent, ChatSidebarComponent],
  template: `
    <div class="flex h-screen w-full bg-[#f8faff] overflow-hidden">
      <!-- Left Sidebar -->
      <app-sidebar class="flex-shrink-0"></app-sidebar>

      <!-- Main Content Area -->
      <main class="flex-1 relative overflow-y-auto overflow-x-hidden p-8">
            <router-outlet></router-outlet>
      </main>

      <!-- Right Chat Sidebar -->
      <app-chat-sidebar class="flex-shrink-0"></app-chat-sidebar>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100vh;
    }
  `]
})
export class DashboardLayoutComponent { }
