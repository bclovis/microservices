import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
    selector: 'app-nav-link',
    standalone: true,
    imports: [CommonModule, RouterModule],
    template: `
    <a 
      [routerLink]="route" 
      routerLinkActive="bg-blue-50 text-poke-blue" 
      class="flex items-center gap-4 px-6 py-4 rounded-2xl text-gray-500 hover:bg-gray-50 hover:text-poke-blue transition-all duration-200 group"
    >
      <svg 
        viewBox="0 0 14 14" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg" 
        class="w-5 h-5 fill-current transition-colors"
      >
        <path [attr.d]="svgPath" [attr.fill-rule]="fillRule" [attr.clip-rule]="clipRule" stroke-width="1"></path>
      </svg>
      <span class="text-xl font-medium">{{ label }}</span>
    </a>
  `,
    styles: []
})
export class NavLinkComponent {
    @Input() route: string = '';
    @Input() label: string = '';
    @Input() svgPath: string = '';
    @Input() fillRule: string = 'evenodd';
    @Input() clipRule: string = 'evenodd';
}
