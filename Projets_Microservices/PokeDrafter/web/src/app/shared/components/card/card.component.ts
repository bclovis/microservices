import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="bg-dark-card backdrop-blur-md rounded-2xl border border-white/5 shadow-xl overflow-hidden"
      [ngClass]="paddingClass"
    >
      <ng-content></ng-content>
    </div>
  `
})
export class CardComponent {
  @Input() padding: 'none' | 'sm' | 'md' | 'lg' = 'md';

  get paddingClass() {
    switch (this.padding) {
      case 'none': return '';
      case 'sm': return 'p-4';
      case 'md': return 'p-6';
      case 'lg': return 'p-8';
      default: return 'p-6';
    }
  }
}
