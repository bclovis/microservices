import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  template: `
    <div class="app-container red-theme">
      <header>
        <h1>Pokemon Drafter - Red Team</h1>
      </header>
      <router-outlet></router-outlet>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #ff6b6b 0%, #c92a2a 100%);
    }
    
    header {
      background: rgba(0, 0, 0, 0.3);
      padding: 1rem;
      text-align: center;
      color: white;
    }
    
    /* dino theme hidden */
  `]
})
export class AppComponent {
  title = 'pokemon-drafter-red';
}
