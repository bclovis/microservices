import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-pokemon-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card-container" (click)="toggleFlip()" [class.is-flipped]="isFlipped">
      <div class="card-inner">
        <!-- Front of Card -->
        <div class="card-front" [style.background]="getGradient()">
          <div class="card-shine"></div>
          
          <!-- Top Section -->
          <div class="top-section">
            <div class="id-number">#{{ number | number:'3.0-0' }}</div>
            <h3 class="pokemon-name" [class.long-name]="name.length > 12">{{ name }}</h3>
            
            <!-- Type Tooltip / Badges -->
            <div class="type-badge-container">
              <span *ngFor="let type of types" 
                    class="type-pill" 
                    [style.backgroundColor]="getTypeColor(type)">
                {{ type }}
              </span>
            </div>
          </div>

          <!-- Middle: Pokemon Artwork (Auto-scaling) -->
          <div class="artwork-container">
            <div class="orb-backdrop"></div>
            <img [src]="spriteUrl" [alt]="name" class="pokemon-sprite">
          </div>

          <!-- Bottom: Points (Pinned to bottom) -->
          <div class="card-footer">
            <div class="points-badge">
              <span class="pts-value">{{ points }}</span>
              <span class="pts-label">pts</span>
            </div>
          </div>
        </div>

        <!-- Back of Card -->
        <div class="card-back">
          <div class="back-bg"></div>
          <div class="back-logo-container">
             <img src="assets/logo.png" alt="PokeDrafter" class="back-logo">
          </div>
          <div class="back-footer">
             <span class="legal">© 2026 POKEDRAFTER</span>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      width: 280px;
      height: 400px;
      font-family: 'CyGrotesk', sans-serif;
    }

    .card-container {
      width: 100%;
      height: 100%;
      perspective: 1500px;
      cursor: pointer;
    }

    .card-inner {
      position: relative;
      width: 100%;
      height: 100%;
      transition: transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      transform-style: preserve-3d;
      border-radius: 20px;
    }

    .card-container.is-flipped .card-inner {
      transform: rotateY(180deg);
    }

    .card-front, .card-back {
      position: absolute;
      width: 100%;
      height: 100%;
      backface-visibility: hidden;
      border-radius: 20px;
      border: 8px solid #fff;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
      overflow: hidden;
    }

    /* FRONT SIDE */
    .card-front {
      padding: 18px; /* Reduced padding to save space */
      display: flex;
      flex-direction: column;
      justify-content: space-between; /* Balance items vertically */
      z-index: 2;
    }

    .card-shine {
      position: absolute;
      top: -100%; left: -100%; width: 300%; height: 300%;
      background: linear-gradient(135deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0) 100%);
      transform: rotate(45deg);
      pointer-events: none;
    }

    .card-container:hover .card-shine {
      animation: shine 1.5s ease-in-out;
    }

    @keyframes shine {
      0% { top: -100%; left: -100%; }
      100% { top: 100%; left: 100%; }
    }

    .top-section {
      z-index: 10;
      flex-shrink: 0;
    }

    .id-number {
      font-size: 14px;
      font-weight: 500;
      color: rgba(255,255,255,0.8);
      margin-bottom: -2px;
    }

    .pokemon-name {
      font-size: 26px;
      font-weight: 700;
      color: #fff;
      text-transform: capitalize;
      margin: 0 0 8px 0;
      text-shadow: 0 2px 4px rgba(0,0,0,0.1);
      line-height: 1;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .pokemon-name.long-name {
      font-size: 22px; /* Shrink font for long names */
    }

    .type-badge-container {
      display: flex;
      gap: 6px;
      z-index: 10;
    }

    .type-pill {
      font-size: 9px;
      font-weight: 700;
      color: white;
      text-transform: uppercase;
      padding: 2px 8px;
      border-radius: 20px;
      background: rgba(0,0,0,0.2);
      backdrop-filter: blur(5px);
      letter-spacing: 0.5px;
    }

    .artwork-container {
      position: relative;
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 0;
      margin: 5px 0;
      z-index: 5;
    }

    .orb-backdrop {
      position: absolute;
      width: 190px;
      height: 190px;
      background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%);
      border-radius: 50%;
      opacity: 0.3;
      animation: pulse 4s infinite;
    }

    @keyframes pulse {
      0% { transform: scale(0.95); opacity: 0.2; }
      50% { transform: scale(1.05); opacity: 0.4; }
      100% { transform: scale(0.95); opacity: 0.2; }
    }

    .pokemon-sprite {
      width: 120%;
      height: 120%;
      max-width: 250px;
      max-height: 250px;
      object-fit: contain;
      z-index: 10;
      filter: drop-shadow(0 10px 20px rgba(0,0,0,0.25));
      transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .card-container:hover .pokemon-sprite {
      transform: scale(1.15) translateY(-5px);
    }

    .card-footer {
      z-index: 10;
      flex-shrink: 0;
      padding-top: 5px;
      display: flex;
      justify-content: flex-start;
      align-items: flex-end;
    }

    .points-badge {
      display: flex;
      flex-direction: column;
      line-height: 0.9;
    }

    .pts-value {
      font-size: 34px;
      font-weight: 700;
      color: #fff;
    }

    .pts-label {
      font-size: 12px;
      font-weight: 500;
      color: rgba(255,255,255,0.9);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    /* BACK SIDE */
    .card-back {
      transform: rotateY(180deg);
      background: #f8faff;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 0;
      border: 10px solid #fff;
    }

    .back-bg {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: linear-gradient(135deg, #f8faff 0%, #eef2f3 100%);
    }

    .back-logo-container {
      z-index: 10;
      width: 85%;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .back-logo {
      width: 100%;
      height: auto;
      object-fit: contain;
    }

    .back-footer {
      position: absolute;
      bottom: 20px;
      z-index: 10;
    }

    .legal {
      font-size: 8px;
      color: #cbd5e0;
      font-weight: 600;
      letter-spacing: 2px;
      text-transform: uppercase;
    }
  `]
})
export class PokemonCardComponent {
  @Input() number: number = 25;
  @Input() name: string = 'Pikachu';
  @Input() points: number = 2999;
  @Input() spriteUrl: string = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png';
  @Input() types: string[] = ['Electric'];

  isFlipped = false;

  toggleFlip() {
    this.isFlipped = !this.isFlipped;
  }

  getTypeColor(type: string): string {
    const typeColors: { [key: string]: string } = {
      fire: '#F08030',
      water: '#6890F0',
      grass: '#78C850',
      electric: '#F8D030',
      psychic: '#F85888',
      ice: '#98D8D8',
      dragon: '#7038F8',
      dark: '#705848',
      fairy: '#EE99AC',
      normal: '#A8A878',
      fighting: '#C03028',
      flying: '#A890F0',
      poison: '#A040A0',
      ground: '#E0C068',
      rock: '#B8A038',
      bug: '#A8B820',
      ghost: '#705898',
      steel: '#B8B8D0'
    };
    return typeColors[type.toLowerCase()] || '#A8A878';
  }

  getGradient(): string {
    const type = this.types[0]?.toLowerCase() || 'normal';
    const gradients: { [key: string]: string[] } = {
      fire: ['#FF512F', '#DD2476'],
      water: ['#4facfe', '#00f2fe'],
      grass: ['#00b09b', '#96c93d'],
      electric: ['#f8d030', '#f7971e'],
      psychic: ['#f85888', '#d04ed6'],
      ice: ['#acb6e5', '#86fde8'],
      dragon: ['#4b6cb7', '#182848'],
      dark: ['#232526', '#414345'],
      fairy: ['#ff9a9e', '#fecfef'],
      normal: ['#bdc3c7', '#2c3e50'],
      fighting: ['#8e2de2', '#4a00e0'],
      flying: ['#4ca1af', '#c4e0e5'],
      poison: ['#7f00ff', '#e100ff'],
      ground: ['#ba8b02', '#181818'],
      rock: ['#757f9a', '#d7dde8'],
      bug: ['#02aab0', '#00cdac'],
      ghost: ['#30e8bf', '#ff8235'],
      steel: ['#000428', '#004e92']
    };

    const colors = gradients[type] || gradients['normal'];
    return `linear-gradient(135deg, ${colors[0]}, ${colors[1]})`;
  }
}
