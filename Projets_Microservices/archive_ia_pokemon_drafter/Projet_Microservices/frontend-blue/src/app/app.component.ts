import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  template: `
    <div class="app-container blue-theme">
      <header>
        <h1>Pokemon Drafter - Blue Team</h1>
      </header>
      <router-outlet></router-outlet>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #4dabf7 0%, #1971c2 100%);
    }
    
    header {
      background: rgba(0, 0, 0, 0.3);
      padding: 1rem;
      text-align: center;
      color: white;
    }
    
    /* dino reference concealed */
  `]
})
export class AppComponent {
  title = 'pokemon-drafter-blue';
}
